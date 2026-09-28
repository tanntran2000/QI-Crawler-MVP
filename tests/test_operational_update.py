from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import stat
import subprocess
import sys
import time
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from qi_crawler import operational_release, operational_update
from qi_crawler.db import CURRENT_SCHEMA_REVISION
from qi_crawler.operational_release import OperationalPaths, operational_paths
from qi_crawler.operational_update import (
    JOURNAL_SCHEMA,
    MARKER_SCHEMA,
    RECEIPT_SCHEMA,
    _database_paths,
    classify_operational_update_state,
)
from qi_crawler.update_transaction import MaintenanceBusy

UPDATE_ID = "update-01"
OLD_PATHS = {"1": "documents/old-a.pdf", "2": "documents/old-b.pdf"}
NEW_PATHS = {"1": "documents/new-a.pdf", "2": "documents/new-b.pdf"}


class _SyntheticHardInterruption(BaseException):
    """Model process loss that bypasses ordinary exception recovery."""


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _write_db(path: Path, stored_paths: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("CREATE TABLE documents (id INTEGER PRIMARY KEY, stored_path TEXT)")
        connection.executemany(
            "INSERT INTO documents(id, stored_path) VALUES (?, ?)",
            [(int(key), value) for key, value in stored_paths.items()],
        )
        connection.commit()


def _write_update_bundle(root: Path, *, source_sha: str, executable_bytes: bytes) -> None:
    root.mkdir(parents=True, exist_ok=True)
    executable = root / "QI-Crawler.exe"
    executable.write_bytes(executable_bytes)
    manifest = {
        "metadata_schema_version": "qi-crawler-installed-release-v1",
        "product": "QI-Crawler",
        "version": operational_release.__version__,
        "source_git_sha": source_sha,
        "source_branch": "codex/single-installation-legacy-root-retirement-01",
        "build_timestamp_utc": "2026-09-28T00:00:00Z",
        "alembic_head": CURRENT_SCHEMA_REVISION,
        "release_channel": operational_release.OPERATIONAL_RELEASE_CHANNEL,
        "portable_exe_sha256": _sha(executable),
    }
    _write_json(root / "release_manifest.json", manifest)
    (root / "BUILD_INFO.txt").write_text(
        "\n".join(f"{key}={value}" for key, value in manifest.items()) + "\n",
        encoding="utf-8",
    )
    (root / "runtime").mkdir()


def _app_update_fixture(root: Path) -> tuple[OperationalPaths, Path]:
    paths = operational_paths(root)
    paths.application_root.mkdir(parents=True)
    paths.data_root.mkdir(parents=True)
    paths.control_root.mkdir(parents=True)
    for directory in paths.data_directories:
        directory.mkdir(parents=True, exist_ok=True)
    paths.config_path.write_text("storage: {}\n", encoding="utf-8")
    _write_update_bundle(
        paths.application_root,
        source_sha="a" * 40,
        executable_bytes=b"synthetic old application",
    )
    operational_release._rewrite_operational_config(paths.config_path, paths)
    paths.database_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(paths.database_path)) as connection:
        connection.execute("CREATE TABLE alembic_version (version_num TEXT NOT NULL)")
        connection.execute("INSERT INTO alembic_version VALUES (?)", (CURRENT_SCHEMA_REVISION,))
        for table in (
            "notices",
            "attachments",
            "documents",
            "document_extractions",
            "document_evidence",
            "tender_cases",
            "tender_releases",
            "tender_document_memberships",
            "tender_operational_revision_events",
            "tender_recovery_events",
        ):
            connection.execute(f"CREATE TABLE {table} (id INTEGER PRIMARY KEY)")
        connection.commit()
    migration = {
        "receipt_schema_version": operational_release.OPERATIONAL_MIGRATION_RECEIPT_SCHEMA_VERSION,
        "status": "PASS",
        "source_git_sha": "a" * 40,
        "from_revision": operational_release.SOURCE_SCHEMA_REVISION,
        "to_revision": CURRENT_SCHEMA_REVISION,
        "output_db_sha256": _sha(paths.database_path).lower(),
    }
    _write_json(paths.migration_receipt_path, migration)
    old_bundle = operational_release._bundle_identity(paths.application_root)
    _write_json(
        paths.acceptance_path,
        operational_release._operational_acceptance_payload(paths, old_bundle, migration),
    )
    new_bundle = root.parent / "new-bundle"
    _write_update_bundle(
        new_bundle,
        source_sha="b" * 40,
        executable_bytes=b"synthetic new application",
    )
    return paths, new_bundle


def _install_uncheckpointed_wal(paths: OperationalPaths) -> None:
    wal_path = Path(f"{paths.database_path}-wal")
    shm_path = Path(f"{paths.database_path}-shm")
    with closing(sqlite3.connect(paths.database_path)) as connection:
        assert connection.execute("PRAGMA journal_mode = WAL").fetchone() == ("wal",)
        connection.execute("PRAGMA wal_autocheckpoint = 0")
        connection.execute("INSERT INTO notices (id) VALUES (99)")
        connection.commit()
        assert wal_path.is_file() and wal_path.stat().st_size > 32
        assert shm_path.is_file()
        active_files = {
            paths.database_path: paths.database_path.read_bytes(),
            wal_path: wal_path.read_bytes(),
            shm_path: shm_path.read_bytes(),
        }
    for path, content in active_files.items():
        path.write_bytes(content)


def _replace_db(path: Path, stored_paths: dict[str, str]) -> None:
    path.unlink()
    _write_db(path, stored_paths)


def _fixture(tmp_path: Path, *, phase: str = "EARLY_ACTIVE") -> tuple[OperationalPaths, dict]:
    paths = operational_paths(tmp_path / "operational")
    paths.application_root.mkdir(parents=True)
    paths.executable.write_bytes(b"old application")
    paths.config_path.parent.mkdir(parents=True)
    paths.config_path.write_bytes(b"old config")
    _write_db(paths.database_path, OLD_PATHS)
    paths.control_root.mkdir(parents=True)

    marker = {
        "schema_version": MARKER_SCHEMA,
        "update_id": UPDATE_ID,
        "journal": "update_journal.json",
    }
    journal = {
        "schema_version": JOURNAL_SCHEMA,
        "update_id": UPDATE_ID,
        "phase": phase,
        "application": {
            "old_sha256": _sha(paths.executable),
            "new_sha256": hashlib.sha256(b"new application").hexdigest().upper(),
        },
        "config": {
            "old_sha256": _sha(paths.config_path),
            "new_sha256": hashlib.sha256(b"new config").hexdigest().upper(),
        },
        "database": {"old_paths": OLD_PATHS, "new_paths": NEW_PATHS},
        "backup": {
            "path": "backups/preupdate.db",
            "sha256": "",
            "baseline_paths": OLD_PATHS,
        },
    }
    _write_json(paths.control_root / "active_update.json", marker)
    _write_json(paths.control_root / "update_journal.json", journal)
    return paths, journal


def _write_journal(paths: OperationalPaths, journal: dict) -> None:
    _write_json(paths.control_root / "update_journal.json", journal)


def _install_backup(paths: OperationalPaths, journal: dict) -> Path:
    backup = paths.control_root / journal["backup"]["path"]
    _write_db(backup, OLD_PATHS)
    journal["backup"]["sha256"] = _sha(backup)
    _write_journal(paths, journal)
    return backup


def _install_new_identity(paths: OperationalPaths) -> None:
    paths.executable.write_bytes(b"new application")
    paths.config_path.write_bytes(b"new config")


def _write_receipt(paths: OperationalPaths, journal: dict, **overrides: object) -> None:
    receipt = {
        "schema_version": RECEIPT_SCHEMA,
        "update_id": UPDATE_ID,
        "application_sha256": journal["application"]["new_sha256"],
        "config_sha256": journal["config"]["new_sha256"],
        "database_state": "NEW",
    }
    receipt.update(overrides)
    _write_json(paths.control_root / "update_receipt.json", receipt)


def _classify(paths: OperationalPaths):
    before = _tree_identity(paths.root)
    result = classify_operational_update_state(paths)
    assert _tree_identity(paths.root) == before
    return result


def test_idle_absence_is_phase_valid_and_result_has_no_action_authority(tmp_path: Path) -> None:
    paths, _ = _fixture(tmp_path)
    (paths.control_root / "active_update.json").unlink()
    (paths.control_root / "update_journal.json").unlink()

    result = _classify(paths)

    assert result.classification == "NO_ACTIVE_UPDATE"
    assert result.observed_phase == "IDLE"
    assert result.input_stable is True
    assert result.artifact_states["marker"] == "PHASE_VALID_ABSENCE"
    assert not ({"action", "delete", "restore", "overwrite", "continue"} & set(result.__dataclass_fields__))


def test_startup_guard_fails_closed_for_marker_without_authoritative_journal(
    tmp_path: Path,
) -> None:
    assert callable(getattr(operational_update, "assert_operational_startup_allowed", None))
    paths = operational_paths(tmp_path / "operational")
    update_id = "a" * 32
    _write_json(
        paths.control_root / "update_marker.json",
        {
            "schema_version": "qi-crawler-update-pointer-v1",
            "update_id": update_id,
            "journal": f"updates/{update_id}/state.json",
        },
    )

    with pytest.raises(operational_update.OperationalUpdateError, match="UPDATE_JOURNAL_REQUIRED"):
        operational_update.assert_operational_startup_allowed(paths)


def test_startup_guard_fails_closed_for_attempt_directory_without_bootstrap_journal(
    tmp_path: Path,
) -> None:
    paths = operational_paths(tmp_path / "operational")
    (paths.control_root / "updates" / ("b" * 32)).mkdir(parents=True)

    with pytest.raises(operational_update.OperationalUpdateError, match="UPDATE_JOURNAL_REQUIRED"):
        operational_update.assert_operational_startup_allowed(paths)


def test_update_transition_journal_retains_ordered_intent_and_confirmation(
    tmp_path: Path,
) -> None:
    assert callable(getattr(operational_update, "_append_update_transition", None))
    paths, _bundle = _app_update_fixture(tmp_path / "operational")
    update_id = "c" * 32
    journal_path = paths.control_root / "updates" / update_id / "state.json"
    data_candidates = (
        paths.config_path,
        paths.database_path,
        Path(f"{paths.database_path}-wal"),
        Path(f"{paths.database_path}-shm"),
    )
    _write_json(
        journal_path,
        {
            "schema_version": operational_update.UPDATE_STATE_SCHEMA,
            "update_id": update_id,
            "phase": "PREPARING",
            "result": None,
            "first_mutation_at": None,
            "pending_action": None,
            "transitions": [],
            "application": {
                "old": operational_update._update_tree_identity(paths.application_root),
                "new": {"sha256": "new"},
                "active_path": paths.application_root.relative_to(paths.root).as_posix(),
                "old_path": f".update/{update_id}/old",
                "stage_path": f".update/{update_id}/stage",
                "failed_path": f".update/{update_id}/failed",
            },
            "acceptance": {
                "old_sha256": operational_update._update_file_identity(paths.acceptance_path)["sha256"],
                "snapshot_path": f"control/updates/{update_id}/acceptance.before.json",
            },
            "source_data_before": {
                str(path): operational_update._data_file_identity(path)
                for path in data_candidates
            },
            "lkg_manifest_path": f"control/updates/{update_id}/last_known_good.json",
        },
    )

    operational_update._append_update_transition(
        journal_path,
        kind="INTENT",
        action="ROTATE_ACTIVE_TO_OLD",
        before={"active": "old-sha"},
        expected={"old": "old-sha"},
    )
    operational_update._append_update_transition(
        journal_path,
        kind="CONFIRMED",
        action="ROTATE_ACTIVE_TO_OLD",
        before={"active": "old-sha"},
        expected={"old": "old-sha"},
        observed={"old": "old-sha"},
    )

    state = json.loads(journal_path.read_text(encoding="utf-8"))
    assert [entry["sequence"] for entry in state["transitions"]] == [1, 2]
    assert [entry["kind"] for entry in state["transitions"]] == ["INTENT", "CONFIRMED"]
    assert [entry["action"] for entry in state["transitions"]] == [
        "ROTATE_ACTIVE_TO_OLD",
        "ROTATE_ACTIVE_TO_OLD",
    ]
    assert state["pending_action"] is None
    assert state["first_mutation_at"] is not None


def test_synthetic_app_update_preserves_data_and_acceptance_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert callable(getattr(operational_update, "apply_operational_application_update", None))
    paths, bundle = _app_update_fixture(tmp_path / "operational")
    old_generation_identity = operational_update._update_tree_identity(paths.application_root)
    db_before = paths.database_path.read_bytes()
    config_before = paths.config_path.read_bytes()
    migration_before = paths.migration_receipt_path.read_bytes()
    db_sidecars_before = {
        suffix: Path(f"{paths.database_path}{suffix}").exists()
        for suffix in ("-wal", "-shm")
    }
    monkeypatch.setattr(operational_update, "_assert_no_old_runtime_holders", lambda *_args: None)

    result = operational_update.apply_operational_application_update(
        paths, bundle, confirmed=True
    )

    acceptance = json.loads(paths.acceptance_path.read_text(encoding="utf-8"))
    assert result["result"] == "COMPLETE"
    assert paths.executable.read_bytes() == b"synthetic new application"
    assert paths.database_path.read_bytes() == db_before
    assert paths.config_path.read_bytes() == config_before
    assert paths.migration_receipt_path.read_bytes() == migration_before
    assert {
        suffix: Path(f"{paths.database_path}{suffix}").exists()
        for suffix in ("-wal", "-shm")
    } == db_sidecars_before
    assert acceptance["source_git_sha"] == "b" * 40
    assert acceptance["migration_source_sha"] == "a" * 40
    assert acceptance["database_sha256"] == json.loads(migration_before)["output_db_sha256"]
    journal = json.loads(Path(result["journal_path"]).read_text(encoding="utf-8"))
    assert [entry["sequence"] for entry in journal["transitions"]] == list(
        range(1, len(journal["transitions"]) + 1)
    )
    assert journal["result"] == "COMPLETE"
    lkg = json.loads(Path(result["lkg_manifest_path"]).read_text(encoding="utf-8"))
    assert lkg["runtime_verification_reference"] == "NOT_PERFORMED"
    assert lkg["application_generation"] == {
        "path": Path(result["old_generation_path"]).relative_to(paths.root).as_posix(),
        "identity": old_generation_identity,
    }
    assert lkg["database_snapshot"]["sha256"] == _sha(paths.database_path)
    snapshot_root = paths.root / "Data" / "data" / "backups" / result["update_id"]
    snapshot_db = snapshot_root / "egp.db"
    snapshot_config = snapshot_root / "config.yaml"
    expected_artifacts = {
        path.relative_to(paths.root).as_posix(): operational_update._update_file_identity(path)
        for path in (snapshot_db, snapshot_config)
    }
    assert lkg["snapshot_artifacts"] == expected_artifacts
    assert lkg["database_snapshot"]["sidecars"] == {}


def test_synthetic_app_update_preserves_uncheckpointed_wal_data_and_seals_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, bundle = _app_update_fixture(tmp_path / "operational")
    _install_uncheckpointed_wal(paths)
    data_paths = (
        paths.config_path,
        paths.database_path,
        Path(f"{paths.database_path}-wal"),
        Path(f"{paths.database_path}-shm"),
    )
    data_before = {
        str(path): operational_update._data_file_identity(path) for path in data_paths
    }
    assert data_before[str(Path(f"{paths.database_path}-wal"))]["exists"] is True
    assert data_before[str(Path(f"{paths.database_path}-shm"))]["exists"] is True
    monkeypatch.setattr(operational_update, "_assert_no_old_runtime_holders", lambda *_args: None)

    result = operational_update.apply_operational_application_update(
        paths, bundle, confirmed=True
    )

    assert result["result"] == "COMPLETE"
    assert {
        str(path): operational_update._data_file_identity(path) for path in data_paths
    } == data_before
    manifest = json.loads(Path(result["lkg_manifest_path"]).read_text(encoding="utf-8"))
    assert manifest["database_snapshot"]["verification"]["aggregate_row_counts"]["notices"] == 1
    snapshot_artifacts = manifest["snapshot_artifacts"]
    assert (
        paths.data_dir / "backups" / result["update_id"] / "egp.db"
    ).relative_to(paths.root).as_posix() in snapshot_artifacts
    assert (
        paths.data_dir / "backups" / result["update_id"] / "config.yaml"
    ).relative_to(paths.root).as_posix() in snapshot_artifacts
    assert all(
        operational_update._update_file_identity(paths.root / relative) == identity
        for relative, identity in snapshot_artifacts.items()
    )
    snapshot_sidecars = manifest["database_snapshot"]["sidecars"]
    assert {name for name in snapshot_sidecars if name in {"-wal", "-shm"}} == {
        path.name[len("egp.db") :]
        for path in (
            paths.data_dir / "backups" / result["update_id"] / "egp.db-wal",
            paths.data_dir / "backups" / result["update_id"] / "egp.db-shm",
        )
        if path.exists()
    }


def test_recovery_rolls_back_exact_old_generation_after_rotation_interruption(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, bundle = _app_update_fixture(tmp_path / "operational")
    old_bytes = paths.executable.read_bytes()
    old_acceptance = paths.acceptance_path.read_bytes()
    monkeypatch.setattr(operational_update, "_assert_no_old_runtime_holders", lambda *_args: None)
    original_replace = os.replace
    interrupted = False

    def replace_then_interrupt(source: Path, destination: Path) -> None:
        nonlocal interrupted
        original_replace(source, destination)
        if Path(source) == paths.application_root and not interrupted:
            interrupted = True
            raise OSError("injected failure after first app mutation")

    monkeypatch.setattr(operational_update.os, "replace", replace_then_interrupt)
    with pytest.raises(operational_update.OperationalUpdateError, match="UPDATE_FAILED"):
        operational_update.apply_operational_application_update(
            paths, bundle, confirmed=True
        )

    state_path = next((paths.control_root / "updates").glob("*/state.json"))
    state = json.loads(state_path.read_text(encoding="utf-8"))
    old_path = paths.root / state["application"]["old_path"]
    assert state["result"] == "RECOVERY_REQUIRED"
    assert state["pending_action"] == "ROTATE_ACTIVE_TO_OLD"
    assert not paths.application_root.exists()
    assert operational_update._update_tree_identity(old_path) == state["application"]["old"]
    assert paths.acceptance_path.read_bytes() == old_acceptance

    monkeypatch.setattr(operational_update.os, "replace", original_replace)
    result = operational_update.recover_operational_application_update(paths)

    recovered = json.loads(state_path.read_text(encoding="utf-8"))
    assert result["result"] == "ROLLED_BACK"
    assert paths.executable.read_bytes() == old_bytes
    assert paths.acceptance_path.read_bytes() == old_acceptance
    assert not old_path.exists()
    assert recovered["result"] == "ROLLED_BACK"
    assert recovered["pending_action"] is None
    assert [entry["sequence"] for entry in recovered["transitions"]] == list(
        range(1, len(recovered["transitions"]) + 1)
    )
    assert any(entry["kind"] == "RECOVERY_INTENT" for entry in recovered["transitions"])
    assert any(entry["kind"] == "RECOVERY_CONFIRMED" for entry in recovered["transitions"])
    assert recovered["first_mutation_at"] is not None
    assert operational_update._update_tree_identity(
        paths.root / recovered["application"]["stage_path"]
    ) == recovered["application"]["new"]


def test_sharing_violation_before_first_app_mutation_is_failed_no_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, bundle = _app_update_fixture(tmp_path / "operational")
    old_application = operational_update._update_tree_identity(paths.application_root)
    acceptance_before = paths.acceptance_path.read_bytes()
    data_paths = (
        paths.config_path,
        paths.database_path,
        Path(f"{paths.database_path}-wal"),
        Path(f"{paths.database_path}-shm"),
    )
    data_before = {str(path): operational_update._update_file_identity(path) for path in data_paths}
    monkeypatch.setattr(operational_update, "_assert_no_old_runtime_holders", lambda *_args: None)
    original_replace = os.replace

    def reject_active_rotation(source: Path, destination: Path) -> None:
        if Path(source) == paths.application_root:
            raise PermissionError("injected Windows sharing violation")
        original_replace(source, destination)

    monkeypatch.setattr(operational_update.os, "replace", reject_active_rotation)
    with pytest.raises(operational_update.OperationalUpdateError, match="UPDATE_FAILED"):
        operational_update.apply_operational_application_update(paths, bundle, confirmed=True)

    state_path = next((paths.control_root / "updates").glob("*/state.json"))
    state = json.loads(state_path.read_text(encoding="utf-8"))
    rotation_history = [
        entry
        for entry in state["transitions"]
        if entry["action"] == "ROTATE_ACTIVE_TO_OLD"
    ]
    assert state["result"] == "FAILED_NO_MUTATION"
    assert state["first_mutation_at"] is None
    assert state["pending_action"] is None
    assert [entry["kind"] for entry in rotation_history] == [
        "INTENT",
        "ATTEMPT_FAILED_RECOVERED",
    ]
    assert rotation_history[-1]["observed"]["actual"] == {
        "active": old_application,
        "old": {"exists": False},
    }
    assert operational_update._update_tree_identity(paths.application_root) == old_application
    assert paths.acceptance_path.read_bytes() == acceptance_before
    assert {str(path): operational_update._update_file_identity(path) for path in data_paths} == data_before
    assert not (paths.control_root / "update_marker.json").exists()


@pytest.mark.parametrize("tamper_old_generation", [False, True])
def test_recovery_requires_exact_old_generation_binding_after_postcheck_interruption(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tamper_old_generation: bool,
) -> None:
    paths, bundle = _app_update_fixture(tmp_path / "operational")
    monkeypatch.setattr(operational_update, "_assert_no_old_runtime_holders", lambda *_args: None)
    original_validate = operational_release.validate_operational_acceptance
    calls = 0

    def fail_once_after_acceptance(executable: Path, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise operational_release.OperationalReleaseError("injected postcheck interruption")
        return original_validate(executable, **kwargs)

    monkeypatch.setattr(
        operational_release, "validate_operational_acceptance", fail_once_after_acceptance
    )
    with pytest.raises(
        operational_update.OperationalUpdateError, match="UPDATE_POSTCHECK_ACCEPTANCE_FAILED"
    ):
        operational_update.apply_operational_application_update(paths, bundle, confirmed=True)

    state_path = next((paths.control_root / "updates").glob("*/state.json"))
    interrupted = json.loads(state_path.read_text(encoding="utf-8"))
    assert interrupted["result"] == "RECOVERY_REQUIRED"
    assert interrupted["first_mutation_at"] is not None

    old_path = paths.root / interrupted["application"]["old_path"]
    if tamper_old_generation:
        (old_path / "QI-Crawler.exe").write_bytes(b"ambiguous retained old generation")
        active_before = operational_update._generation_identity(paths.application_root)
        old_before = operational_update._generation_identity(old_path)
        acceptance_before = paths.acceptance_path.read_bytes()
        with pytest.raises(operational_update.OperationalUpdateError, match="UPDATE_RECOVERY_AMBIGUOUS"):
            operational_update.recover_operational_application_update(paths)
        held = json.loads(state_path.read_text(encoding="utf-8"))
        assert held["result"] == "RECOVERY_REQUIRED"
        assert operational_update._generation_identity(paths.application_root) == active_before
        assert operational_update._generation_identity(old_path) == old_before
        assert paths.acceptance_path.read_bytes() == acceptance_before
        return

    monkeypatch.setattr(operational_release, "validate_operational_acceptance", original_validate)
    result = operational_update.recover_operational_application_update(paths)

    recovered = json.loads(state_path.read_text(encoding="utf-8"))
    acceptance = json.loads(paths.acceptance_path.read_text(encoding="utf-8"))
    assert result["result"] == "RECOVERY_COMPLETE"
    assert recovered["result"] == "RECOVERY_COMPLETE"
    assert acceptance["source_git_sha"] == "b" * 40
    assert recovered["pending_action"] is None


def test_forward_recovery_requires_no_holders_and_immutable_data_recheck(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, bundle = _app_update_fixture(tmp_path / "operational")
    _install_uncheckpointed_wal(paths)
    monkeypatch.setattr(operational_update, "_assert_no_old_runtime_holders", lambda *_args: None)
    original_validate = operational_release.validate_operational_acceptance
    validation_calls = 0

    def interrupt_after_acceptance(executable: Path, **kwargs):
        nonlocal validation_calls
        validation_calls += 1
        if validation_calls == 2:
            raise operational_release.OperationalReleaseError("injected recovery fixture hold")
        return original_validate(executable, **kwargs)

    monkeypatch.setattr(
        operational_release, "validate_operational_acceptance", interrupt_after_acceptance
    )
    with pytest.raises(
        operational_update.OperationalUpdateError, match="UPDATE_POSTCHECK_ACCEPTANCE_FAILED"
    ):
        operational_update.apply_operational_application_update(paths, bundle, confirmed=True)

    state_path = next((paths.control_root / "updates").glob("*/state.json"))
    state_before = json.loads(state_path.read_text(encoding="utf-8"))
    active_before = operational_update._generation_identity(paths.application_root)
    old_path = paths.root / state_before["application"]["old_path"]
    old_before = operational_update._generation_identity(old_path)
    acceptance_before = paths.acceptance_path.read_bytes()
    marker_path = paths.control_root / "update_marker.json"
    marker_before = marker_path.read_bytes()
    data_paths = (
        paths.config_path,
        paths.database_path,
        Path(f"{paths.database_path}-wal"),
        Path(f"{paths.database_path}-shm"),
    )
    data_before = {str(path): operational_update._data_file_identity(path) for path in data_paths}
    history_before = state_before["transitions"]
    holder_calls: list[tuple[Path, ...]] = []
    validation_options: list[dict[str, object]] = []

    def reject_old_holder(
        _paths: OperationalPaths, additional_executables: tuple[Path, ...] = ()
    ) -> None:
        holder_calls.append(additional_executables)
        raise operational_update.OperationalUpdateError("UPDATE_RUNTIME_RESOURCE_HELD")

    def record_validation(executable: Path, **kwargs):
        validation_options.append(dict(kwargs))
        return original_validate(executable, **kwargs)

    monkeypatch.setattr(operational_update, "_assert_no_old_runtime_holders", reject_old_holder)
    monkeypatch.setattr(operational_release, "validate_operational_acceptance", record_validation)
    with pytest.raises(
        operational_update.OperationalUpdateError, match="UPDATE_RUNTIME_RESOURCE_HELD"
    ):
        operational_update.recover_operational_application_update(paths)

    held = json.loads(state_path.read_text(encoding="utf-8"))
    assert holder_calls == [(old_path / "QI-Crawler.exe",)]
    assert validation_options == [{"immutable_database": True}]
    assert held["result"] == "RECOVERY_REQUIRED"
    assert held["pending_action"] is None
    assert held["transitions"] == history_before
    assert operational_update._generation_identity(paths.application_root) == active_before
    assert operational_update._generation_identity(old_path) == old_before
    assert paths.acceptance_path.read_bytes() == acceptance_before
    assert marker_path.read_bytes() == marker_before
    assert {str(path): operational_update._data_file_identity(path) for path in data_paths} == data_before


def test_recovery_confirms_terminal_marker_removal_after_interruption(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, bundle = _app_update_fixture(tmp_path / "operational")
    monkeypatch.setattr(operational_update, "_assert_no_old_runtime_holders", lambda *_args: None)
    original_unlink = Path.unlink
    interrupted = False

    def unlink_then_interrupt(path: Path, *args, **kwargs) -> None:
        nonlocal interrupted
        original_unlink(path, *args, **kwargs)
        if path == paths.control_root / "update_marker.json" and not interrupted:
            interrupted = True
            raise OSError("injected after marker unlink")

    monkeypatch.setattr(Path, "unlink", unlink_then_interrupt)
    with pytest.raises(operational_update.OperationalUpdateError, match="UPDATE_FAILED"):
        operational_update.apply_operational_application_update(paths, bundle, confirmed=True)
    assert not (paths.control_root / "update_marker.json").exists()
    monkeypatch.setattr(Path, "unlink", original_unlink)

    state_path = next((paths.control_root / "updates").glob("*/state.json"))
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["result"] == "COMPLETE"
    assert state["pending_action"] == "CLEAR_ACTIVE_MARKER"

    result = operational_update.recover_operational_application_update(paths)

    recovered = json.loads(state_path.read_text(encoding="utf-8"))
    assert result["result"] == "COMPLETE"
    assert recovered["pending_action"] is None
    assert recovered["transitions"][-1]["action"] == "CLEAR_ACTIVE_MARKER"
    assert recovered["transitions"][-1]["kind"] == "CONFIRMED"


@pytest.mark.parametrize(
    ("action", "timing", "expected_result"),
    (
        ("COMMIT_ACCEPTANCE", "before", "ROLLED_BACK"),
        ("COMMIT_ACCEPTANCE", "after", "RECOVERY_COMPLETE"),
        ("SET_ACTIVE_MARKER", "before", "FAILED_NO_MUTATION"),
        ("SET_ACTIVE_MARKER", "after", "FAILED_NO_MUTATION"),
        ("CLEAR_ACTIVE_MARKER", "before", "COMPLETE"),
    ),
)
def test_hard_interruption_reconciles_acceptance_and_marker_intents(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    action: str,
    timing: str,
    expected_result: str,
) -> None:
    paths, bundle = _app_update_fixture(tmp_path / "operational")
    monkeypatch.setattr(operational_update, "_assert_no_old_runtime_holders", lambda *_args: None)
    marker_path = paths.control_root / "update_marker.json"
    data_paths = (
        paths.config_path,
        paths.database_path,
        Path(f"{paths.database_path}-wal"),
        Path(f"{paths.database_path}-shm"),
    )
    data_before = {str(path): operational_update._data_file_identity(path) for path in data_paths}
    old_application = operational_update._generation_identity(paths.application_root)
    old_acceptance = paths.acceptance_path.read_bytes()

    original_write = operational_update._write_json_durable
    original_unlink = Path.unlink

    def interrupted_write(path: Path, payload: object) -> None:
        if (
            action in {"COMMIT_ACCEPTANCE", "SET_ACTIVE_MARKER"}
            and path == (paths.acceptance_path if action == "COMMIT_ACCEPTANCE" else marker_path)
        ):
            if timing == "after":
                original_write(path, payload)
            raise _SyntheticHardInterruption(action)
        original_write(path, payload)

    def interrupted_unlink(path: Path, *args, **kwargs) -> None:
        if action == "CLEAR_ACTIVE_MARKER" and path == marker_path:
            if timing == "after":
                original_unlink(path, *args, **kwargs)
            raise _SyntheticHardInterruption(action)
        original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(operational_update, "_write_json_durable", interrupted_write)
    monkeypatch.setattr(Path, "unlink", interrupted_unlink)
    with pytest.raises(_SyntheticHardInterruption):
        operational_update.apply_operational_application_update(paths, bundle, confirmed=True)

    state_path = next((paths.control_root / "updates").glob("*/state.json"))
    interrupted = json.loads(state_path.read_text(encoding="utf-8"))
    transitions_before = list(interrupted["transitions"])
    assert interrupted["pending_action"] == action
    assert transitions_before[-1]["kind"] in {"INTENT", "RECOVERY_INTENT"}
    assert transitions_before[-1]["action"] == action
    assert not any(
        entry["action"] == action and entry["kind"] in {"CONFIRMED", "RECOVERY_CONFIRMED"}
        for entry in transitions_before
    )
    if action == "COMMIT_ACCEPTANCE":
        assert interrupted["result"] not in operational_update._UPDATE_TERMINAL_RESULTS
        if timing == "before":
            assert paths.acceptance_path.read_bytes() == old_acceptance
        else:
            acceptance_bytes = paths.acceptance_path.read_bytes()
            assert acceptance_bytes != old_acceptance
            assert hashlib.sha256(acceptance_bytes).hexdigest().upper() == transitions_before[-1][
                "expected"
            ]["acceptance"]["sha256"]
    if action == "SET_ACTIVE_MARKER" and timing == "after":
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        assert marker["update_id"] == interrupted["update_id"]
    if action == "CLEAR_ACTIVE_MARKER":
        assert interrupted["result"] == "COMPLETE"
        assert marker_path.is_file()

    monkeypatch.setattr(operational_update, "_write_json_durable", original_write)
    monkeypatch.setattr(Path, "unlink", original_unlink)
    result = operational_update.recover_operational_application_update(paths)
    recovered = json.loads(state_path.read_text(encoding="utf-8"))

    assert result["result"] == expected_result
    assert recovered["result"] == expected_result
    assert recovered["pending_action"] is None
    assert [entry["sequence"] for entry in recovered["transitions"]] == list(
        range(1, len(recovered["transitions"]) + 1)
    )
    assert recovered["transitions"][: len(transitions_before)] == transitions_before
    assert {str(path): operational_update._data_file_identity(path) for path in data_paths} == data_before
    assert not marker_path.exists()
    if action == "SET_ACTIVE_MARKER" or (action == "COMMIT_ACCEPTANCE" and timing == "before"):
        assert operational_update._generation_identity(paths.application_root) == old_application
        assert paths.acceptance_path.read_bytes() == old_acceptance


def test_normal_confirmation_cannot_close_recovery_intent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, state_path, _state = _interrupted_update_for_path_test(tmp_path, monkeypatch)
    marker_path = paths.control_root / "update_marker.json"
    before = {"marker": operational_update._data_file_identity(marker_path)}
    expected = {"marker": {"exists": False}}
    operational_update._append_update_transition(
        state_path,
        kind="RECOVERY_INTENT",
        action="RECOVERY_CLEAR_ACTIVE_MARKER",
        before=before,
        expected=expected,
    )
    intent_bytes = state_path.read_bytes()

    with pytest.raises(
        operational_update.OperationalUpdateError,
        match="UPDATE_TRANSITION_INTENT_MISMATCH",
    ):
        operational_update._append_update_transition(
            state_path,
            kind="CONFIRMED",
            action="RECOVERY_CLEAR_ACTIVE_MARKER",
            before=before,
            expected=expected,
            observed=expected,
        )

    assert state_path.read_bytes() == intent_bytes
    retained = json.loads(state_path.read_text(encoding="utf-8"))
    assert retained["pending_action"] == "RECOVERY_CLEAR_ACTIVE_MARKER"
    assert retained["transitions"][-1]["kind"] == "RECOVERY_INTENT"


@pytest.mark.parametrize(
    "path_name",
    (
        "acceptance",
        "migration_receipt",
        "data_root",
        "data_dir",
        "config",
        "database",
        "wal",
        "shm",
    ),
)
def test_reparse_data_or_acceptance_path_is_rejected_before_attempt_creation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    path_name: str,
) -> None:
    paths, bundle = _app_update_fixture(tmp_path / "operational")
    target = {
        "acceptance": paths.acceptance_path,
        "migration_receipt": paths.migration_receipt_path,
        "data_root": paths.data_root,
        "data_dir": paths.data_dir,
        "config": paths.config_path,
        "database": paths.database_path,
        "wal": Path(f"{paths.database_path}-wal"),
        "shm": Path(f"{paths.database_path}-shm"),
    }[path_name]
    if path_name in {"wal", "shm"}:
        target.write_bytes(b"synthetic sidecar")
    original_lstat = Path.lstat

    def mark_target_as_reparse(path: Path):
        if path == target:
            mode = stat.S_IFREG if path.is_file() else stat.S_IFDIR
            return SimpleNamespace(st_mode=mode, st_file_attributes=0x400)
        return original_lstat(path)

    monkeypatch.setattr(Path, "lstat", mark_target_as_reparse)
    monkeypatch.setattr(operational_update, "_assert_no_old_runtime_holders", lambda *_args: None)
    with pytest.raises(operational_update.OperationalUpdateError, match="UPDATE_.*PATH_UNSAFE"):
        operational_update.apply_operational_application_update(paths, bundle, confirmed=True)

    assert not (paths.control_root / "updates").exists()
    assert not (paths.control_root / "update_marker.json").exists()
    assert not (paths.root / ".update").exists()


def test_recovery_rejects_data_identity_paths_outside_operational_set(
    tmp_path: Path,
) -> None:
    paths = operational_paths(tmp_path / "operational")

    with pytest.raises(
        operational_update.OperationalUpdateError,
        match="UPDATE_DATA_IDENTITY_PATHS_INVALID",
    ):
        operational_update._verify_update_data_unchanged(
            paths, {"source_data_before": {"C:/outside/unknown.db": {"exists": False}}}
        )


def _interrupted_update_for_path_test(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[OperationalPaths, Path, dict[str, object]]:
    paths, bundle = _app_update_fixture(tmp_path / "operational")
    monkeypatch.setattr(operational_update, "_assert_no_old_runtime_holders", lambda *_args: None)
    original_validate = operational_release.validate_operational_acceptance
    calls = 0

    def fail_once_after_acceptance(executable: Path, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise operational_release.OperationalReleaseError("injected recovery fixture hold")
        return original_validate(executable, **kwargs)

    monkeypatch.setattr(
        operational_release, "validate_operational_acceptance", fail_once_after_acceptance
    )
    with pytest.raises(
        operational_update.OperationalUpdateError, match="UPDATE_POSTCHECK_ACCEPTANCE_FAILED"
    ):
        operational_update.apply_operational_application_update(paths, bundle, confirmed=True)
    state_path = next((paths.control_root / "updates").glob("*/state.json"))
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["result"] == "RECOVERY_REQUIRED"
    assert state["first_mutation_at"] is not None
    return paths, state_path, state


@pytest.mark.parametrize(
    "redirect",
    ("old_stage", "acceptance_snapshot", "lkg_manifest", "snapshot_family"),
)
def test_recovery_rejects_paths_redirected_outside_exact_attempt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, redirect: str
) -> None:
    paths, state_path, state = _interrupted_update_for_path_test(tmp_path, monkeypatch)
    outside = paths.root.parent / "outside-attempt"
    outside.mkdir()
    sentinel = outside / "sentinel.txt"
    sentinel.write_bytes(b"must remain unchanged")

    if redirect == "old_stage":
        outside_old = outside / "old"
        outside_old.mkdir()
        (outside_old / "sentinel.txt").write_bytes(b"old generation must not be moved")
        state["application"]["old_path"] = "../outside-attempt/old"
        state["application"]["stage_path"] = "../outside-attempt/stage"
    elif redirect == "acceptance_snapshot":
        original = paths.root / state["acceptance"]["snapshot_path"]
        redirected = outside / "acceptance.before.json"
        redirected.write_bytes(original.read_bytes())
        state["acceptance"]["snapshot_path"] = os.path.relpath(redirected, paths.root)
    elif redirect == "lkg_manifest":
        original = paths.root / state["lkg_manifest_path"]
        redirected = outside / "last_known_good.json"
        redirected.write_bytes(original.read_bytes())
        state["lkg_manifest_path"] = os.path.relpath(redirected, paths.root)
    else:
        manifest_path = paths.root / state["lkg_manifest_path"]
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        redirected_root = paths.data_dir / "backups" / "another-attempt"
        redirected_artifacts: dict[str, dict[str, object]] = {}
        redirected_paths: dict[str, str] = {}
        for relative, identity in manifest["snapshot_artifacts"].items():
            source = paths.root / relative
            destination = redirected_root / source.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read_bytes())
            redirected_relative = destination.relative_to(paths.root).as_posix()
            redirected_artifacts[redirected_relative] = identity
            redirected_paths[source.name] = redirected_relative
        manifest["snapshot_artifacts"] = redirected_artifacts
        manifest["database_snapshot"]["path"] = redirected_paths["egp.db"]
        manifest["config_snapshot"]["path"] = redirected_paths["config.yaml"]
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    state_path.write_text(json.dumps(state), encoding="utf-8")
    sentinel_before = sentinel.read_bytes()
    active_before = operational_update._generation_identity(paths.application_root)
    acceptance_before = paths.acceptance_path.read_bytes()
    with pytest.raises(
        operational_update.OperationalUpdateError, match="UPDATE_.*PATH_UNSAFE"
    ):
        operational_update.recover_operational_application_update(paths)
    assert sentinel.read_bytes() == sentinel_before
    assert operational_update._generation_identity(paths.application_root) == active_before
    assert paths.acceptance_path.read_bytes() == acceptance_before
    assert (paths.control_root / "update_marker.json").is_file()
    assert json.loads(state_path.read_text(encoding="utf-8"))["result"] == "RECOVERY_REQUIRED"


@pytest.mark.parametrize("marker_present", [False, True])
def test_recovery_rejects_non_uuid_attempt_id_with_or_without_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, marker_present: bool
) -> None:
    paths, state_path, state = _interrupted_update_for_path_test(tmp_path, monkeypatch)
    updates_root = paths.control_root / "updates"
    invalid_id = "not-a-uuid"
    if marker_present:
        redirected_state = dict(state)
        redirected_state["update_id"] = invalid_id
        invalid_directory = updates_root / invalid_id
        invalid_directory.mkdir()
        invalid_state_path = invalid_directory / "state.json"
        invalid_state_path.write_text(json.dumps(redirected_state), encoding="utf-8")
        marker = {
            "schema_version": operational_update.UPDATE_POINTER_SCHEMA,
            "update_id": invalid_id,
            "journal": f"updates/{invalid_id}/state.json",
        }
        (paths.control_root / "update_marker.json").write_text(
            json.dumps(marker), encoding="utf-8"
        )
    else:
        invalid_directory = updates_root / invalid_id
        state_path.parent.rename(invalid_directory)
        invalid_state_path = invalid_directory / "state.json"
        state["update_id"] = invalid_id
        invalid_state_path.write_text(json.dumps(state), encoding="utf-8")
        (paths.control_root / "update_marker.json").unlink()

    with pytest.raises(operational_update.OperationalUpdateError, match="UPDATE_ID_INVALID"):
        operational_update.recover_operational_application_update(paths)


def test_unsafe_path_rejects_reparse_root_before_tree_hashing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "operational"
    target = root / "Current" / "QI-Crawler"
    target.mkdir(parents=True)
    original_lstat = Path.lstat

    def reparse_root_lstat(path: Path):
        if path == target:
            return SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400)
        return original_lstat(path)

    monkeypatch.setattr(Path, "lstat", reparse_root_lstat)
    assert operational_update._unsafe_path(target, root) is True
    with pytest.raises(operational_update.OperationalUpdateError, match="UPDATE_PATH_UNSAFE"):
        operational_update._update_tree_identity(target)


@pytest.mark.parametrize("operation", ["apply", "recover"])
def test_app_update_lock_contention_is_normalized(operation: str, tmp_path: Path, monkeypatch):
    paths = operational_paths(tmp_path / "operational")
    paths.root.mkdir(parents=True)
    paths.control_root.mkdir()

    def raise_busy(_lock) -> None:
        raise MaintenanceBusy("synthetic existing owner")

    monkeypatch.setattr(operational_update._ExclusiveFileLock, "acquire", raise_busy)
    with pytest.raises(operational_update.OperationalUpdateError, match="UPDATE_SINGLETON_BUSY"):
        if operation == "apply":
            operational_update.apply_operational_application_update(
                paths, tmp_path / "unused-bundle", confirmed=True
            )
        else:
            operational_update.recover_operational_application_update(paths)


@pytest.mark.parametrize("operation", ["apply", "recover"])
def test_app_update_does_not_hide_unexpected_lock_errors(operation: str, tmp_path: Path, monkeypatch):
    paths = operational_paths(tmp_path / "operational")
    paths.root.mkdir(parents=True)
    paths.control_root.mkdir()

    def raise_programming_error(_lock) -> None:
        raise ValueError("synthetic lock programming error")

    monkeypatch.setattr(operational_update._ExclusiveFileLock, "acquire", raise_programming_error)
    with pytest.raises(ValueError, match="synthetic lock programming error"):
        if operation == "apply":
            operational_update.apply_operational_application_update(
                paths, tmp_path / "unused-bundle", confirmed=True
            )
        else:
            operational_update.recover_operational_application_update(paths)


@pytest.mark.parametrize(
    ("appearance", "expected_error"),
    [
        ("unknown", "UPDATE_PROCESS_PATH_AUTHORITY_UNKNOWN"),
        ("before", "UPDATE_OLD_PROCESS_PRESENT"),
        ("between_censuses", "UPDATE_OLD_PROCESS_PRESENT"),
        ("restart_manager", "UPDATE_RUNTIME_RESOURCE_HELD"),
        ("exclusive_data_handle", "UPDATE_DATA_RESOURCE_HELD"),
    ],
)
def test_non_cooperative_old_binary_census_fails_before_app_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    appearance: str,
    expected_error: str,
) -> None:
    paths, bundle = _app_update_fixture(tmp_path / "operational")
    old_generation = operational_update._update_tree_identity(paths.application_root)
    db_before = paths.database_path.read_bytes()
    config_before = paths.config_path.read_bytes()
    acceptance_before = paths.acceptance_path.read_bytes()
    census_calls = 0

    def census_result():
        nonlocal census_calls
        census_calls += 1
        if appearance == "unknown":
            return [{"ExecutablePath": None}]
        if appearance == "before" or (
            appearance == "between_censuses" and census_calls >= 2
        ):
            return [{"ExecutablePath": str(paths.executable)}]
        return []

    monkeypatch.setattr(
        operational_release,
        "_cim_process_census",
        list if appearance == "restart_manager" else census_result,
    )
    monkeypatch.setattr(
        operational_update,
        "_restart_manager_resource_holders",
        (lambda *_args: ((123, "synthetic holder"),))
        if appearance == "restart_manager"
        else (lambda *_args: ()),
    )
    if appearance == "exclusive_data_handle":
        monkeypatch.setattr(
            operational_update, "_assert_no_old_runtime_holders", lambda *_args: None
        )
        original_open = operational_update._open_exclusive_database_file
        open_calls = 0

        def fail_data_barrier(path: Path):
            nonlocal open_calls
            open_calls += 1
            if open_calls == 3 and path == paths.config_path:
                raise PermissionError("injected exclusive config handle denial")
            return original_open(path)

        monkeypatch.setattr(
            operational_update, "_open_exclusive_database_file", fail_data_barrier
        )
    with pytest.raises(operational_update.OperationalUpdateError, match=expected_error):
        operational_update.apply_operational_application_update(paths, bundle, confirmed=True)

    state_path = next((paths.control_root / "updates").glob("*/state.json"))
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["result"] == "FAILED_NO_MUTATION"
    assert state["first_mutation_at"] is None
    assert operational_update._update_tree_identity(paths.application_root) == old_generation
    assert paths.database_path.read_bytes() == db_before
    assert paths.config_path.read_bytes() == config_before
    assert paths.acceptance_path.read_bytes() == acceptance_before
    assert not (paths.control_root / "update_marker.json").exists()


def test_resource_holder_after_app_rotation_blocks_acceptance_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, bundle = _app_update_fixture(tmp_path / "operational")
    old_acceptance = paths.acceptance_path.read_bytes()
    data_paths = (
        paths.config_path,
        paths.database_path,
        Path(f"{paths.database_path}-wal"),
        Path(f"{paths.database_path}-shm"),
    )
    data_before = {
        str(path): operational_update._update_file_identity(path) for path in data_paths
    }
    rm_calls = 0

    def holders_after_rotation(resources: tuple[Path, ...]):
        nonlocal rm_calls
        rm_calls += 1
        return ((123, "synthetic old-generation holder"),) if rm_calls == 3 else ()

    monkeypatch.setattr(operational_release, "_cim_process_census", list)
    monkeypatch.setattr(
        operational_update, "_restart_manager_resource_holders", holders_after_rotation
    )
    with pytest.raises(
        operational_update.OperationalUpdateError, match="UPDATE_RUNTIME_RESOURCE_HELD"
    ):
        operational_update.apply_operational_application_update(paths, bundle, confirmed=True)

    state_path = next((paths.control_root / "updates").glob("*/state.json"))
    state = json.loads(state_path.read_text(encoding="utf-8"))
    old_generation = paths.root / state["application"]["old_path"]
    assert rm_calls == 3
    assert state["result"] == "RECOVERY_REQUIRED"
    assert state["first_mutation_at"] is not None
    assert state["pending_action"] is None
    assert not any(
        entry["action"] == "COMMIT_ACCEPTANCE" for entry in state["transitions"]
    )
    assert operational_update._update_tree_identity(paths.application_root) == state[
        "application"
    ]["new"]
    assert operational_update._update_tree_identity(old_generation) == state["application"]["old"]
    assert paths.acceptance_path.read_bytes() == old_acceptance
    assert {
        str(path): operational_update._update_file_identity(path) for path in data_paths
    } == data_before


@pytest.mark.skipif(os.name != "nt", reason="positive active capture requires Windows exclusive file-sharing semantics")
@pytest.mark.parametrize(
    ("phase", "db_state", "receipt", "expected"),
    [
        ("EARLY_ACTIVE", "OLD", False, "EARLY_ACTIVE_PHASE"),
        ("BACKUP_REQUIRED", "OLD", False, "BACKUP_VALID"),
        ("PRECOMMIT", "OLD", False, "PRECOMMIT_OLD_DB"),
        ("DB_COMMIT_INTENT", "OLD", False, "PRECOMMIT_OLD_DB"),
        ("DB_COMMITTED", "NEW", False, "DB_COMMITTED_JOURNAL_LAG"),
        ("RECEIPT_WRITTEN", "NEW", True, "RECEIPT_PRESENT_VALID"),
        ("TERMINAL", "NEW", True, "TERMINAL_CONSISTENT"),
    ],
)
def test_positive_phase_matrix(
    tmp_path: Path, phase: str, db_state: str, receipt: bool, expected: str
) -> None:
    paths, journal = _fixture(tmp_path, phase=phase)
    if phase != "EARLY_ACTIVE":
        _install_backup(paths, journal)
    if db_state == "NEW":
        _replace_db(paths.database_path, NEW_PATHS)
        _install_new_identity(paths)
    if receipt:
        _write_receipt(paths, journal)

    result = _classify(paths)

    assert result.classification == expected
    assert result.observed_phase == phase
    assert result.input_stable is True


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ("journal_missing", "JOURNAL_REQUIRED"),
        ("journal_corrupt", "JOURNAL_INVALID"),
        ("journal_id_mismatch", "UPDATE_ID_MISMATCH"),
        ("journal_schema", "JOURNAL_SCHEMA_UNSUPPORTED"),
        ("journal_phase", "PHASE_UNSUPPORTED"),
    ],
)
def test_marker_and_journal_ambiguity_fails_closed(
    tmp_path: Path, mutation: str, reason: str
) -> None:
    paths, journal = _fixture(tmp_path)
    journal_path = paths.control_root / "update_journal.json"
    if mutation == "journal_missing":
        journal_path.unlink()
    elif mutation == "journal_corrupt":
        journal_path.write_text("{", encoding="utf-8")
    elif mutation == "journal_id_mismatch":
        journal["update_id"] = "other"
        _write_journal(paths, journal)
    elif mutation == "journal_schema":
        journal["schema_version"] = "future"
        _write_journal(paths, journal)
    else:
        journal["phase"] = "FUTURE_PHASE"
        _write_journal(paths, journal)

    result = _classify(paths)

    assert result.classification == "RECOVERY_REQUIRED_AMBIGUOUS"
    assert reason in result.reasons


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ("missing", "BACKUP_REQUIRED"),
        ("wrong_hash", "BACKUP_IDENTITY_MISMATCH"),
        ("wrong_baseline", "BACKUP_BASELINE_MISMATCH"),
    ],
)
def test_required_backup_is_validated(tmp_path: Path, mutation: str, reason: str) -> None:
    paths, journal = _fixture(tmp_path, phase="BACKUP_REQUIRED")
    if mutation == "missing":
        journal["backup"]["sha256"] = "0" * 64
        _write_journal(paths, journal)
    else:
        _install_backup(paths, journal)
        if mutation == "wrong_hash":
            journal["backup"]["sha256"] = "0" * 64
        else:
            journal["backup"]["baseline_paths"] = {"1": "wrong"}
        _write_journal(paths, journal)

    result = _classify(paths)

    assert result.classification == "RECOVERY_REQUIRED_AMBIGUOUS"
    assert reason in result.reasons


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ("missing", "RECEIPT_REQUIRED"),
        ("corrupt", "RECEIPT_INVALID"),
        ("app_mismatch", "RECEIPT_APPLICATION_MISMATCH"),
    ],
)
def test_required_receipt_is_validated(tmp_path: Path, mutation: str, reason: str) -> None:
    paths, journal = _fixture(tmp_path, phase="RECEIPT_WRITTEN")
    _install_backup(paths, journal)
    _replace_db(paths.database_path, NEW_PATHS)
    _install_new_identity(paths)
    receipt_path = paths.control_root / "update_receipt.json"
    if mutation == "corrupt":
        receipt_path.write_text("{", encoding="utf-8")
    elif mutation == "app_mismatch":
        _write_receipt(paths, journal, application_sha256="0" * 64)

    result = _classify(paths)

    assert result.classification == "RECOVERY_REQUIRED_AMBIGUOUS"
    assert reason in result.reasons


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ("mixed_db", "DATABASE_STATE_MIXED_OR_UNKNOWN"),
        ("config", "CONFIG_IDENTITY_MISMATCH"),
        ("application", "APPLICATION_IDENTITY_MISMATCH"),
    ],
)
def test_identity_ambiguity_fails_closed(tmp_path: Path, mutation: str, reason: str) -> None:
    paths, journal = _fixture(tmp_path, phase="DB_COMMITTED")
    _install_backup(paths, journal)
    _replace_db(paths.database_path, NEW_PATHS)
    _install_new_identity(paths)
    if mutation == "mixed_db":
        _replace_db(paths.database_path, {"1": OLD_PATHS["1"], "2": NEW_PATHS["2"]})
    elif mutation == "config":
        paths.config_path.write_bytes(b"unknown config")
    else:
        paths.executable.write_bytes(b"unknown application")

    result = _classify(paths)

    assert result.classification == "RECOVERY_REQUIRED_AMBIGUOUS"
    assert reason in result.reasons


def test_backup_path_escape_fails_closed(tmp_path: Path) -> None:
    paths, journal = _fixture(tmp_path, phase="BACKUP_REQUIRED")
    journal["backup"]["path"] = "../../outside.db"
    journal["backup"]["sha256"] = "0" * 64
    _write_journal(paths, journal)

    result = _classify(paths)

    assert result.classification == "RECOVERY_REQUIRED_AMBIGUOUS"
    assert "BACKUP_PATH_UNSAFE" in result.reasons


def test_journal_read_error_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths, _ = _fixture(tmp_path)
    journal_path = paths.control_root / "update_journal.json"
    original = Path.read_bytes
    before = _tree_identity(paths.root)

    def denied(path: Path) -> bytes:
        if path == journal_path:
            raise PermissionError("synthetic access denial")
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", denied)

    result = classify_operational_update_state(paths)
    monkeypatch.undo()

    assert result.classification == "RECOVERY_REQUIRED_AMBIGUOUS"
    assert "JOURNAL_INVALID" in result.reasons
    assert _tree_identity(paths.root) == before


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
def test_reparse_or_symlink_artifact_fails_closed(tmp_path: Path) -> None:
    paths, journal = _fixture(tmp_path, phase="BACKUP_REQUIRED")
    outside = tmp_path / "outside.db"
    _write_db(outside, OLD_PATHS)
    backup = paths.control_root / journal["backup"]["path"]
    backup.parent.mkdir(parents=True)
    try:
        backup.symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation unavailable")
    journal["backup"]["sha256"] = _sha(outside)
    _write_journal(paths, journal)

    result = _classify(paths)

    assert result.classification == "RECOVERY_REQUIRED_AMBIGUOUS"
    assert "BACKUP_PATH_UNSAFE" in result.reasons


def test_observation_rejects_ambiguous_sidecars_without_opening_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, journal = _fixture(tmp_path, phase="BACKUP_REQUIRED")
    _install_backup(paths, journal)
    wal = Path(f"{paths.database_path}-wal")
    shm = Path(f"{paths.database_path}-shm")
    wal.write_bytes(b"pre-existing wal evidence")
    shm.write_bytes(b"pre-existing shm evidence")

    source_uri = paths.database_path.resolve(strict=False).as_uri() + "?mode=ro"
    original_connect = sqlite3.connect
    source_opens: list[str] = []

    def reject_source_open(database_name, *args, **kwargs):
        if str(database_name) == source_uri:
            source_opens.append(str(database_name))
        return original_connect(database_name, *args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", reject_source_open)
    before = _tree_identity(paths.root)
    result = _classify(paths)
    after = _tree_identity(paths.root)

    assert result.classification == "RECOVERY_REQUIRED_AMBIGUOUS"
    expected_reason = (
        "DATABASE_CAPTURE_UNSUPPORTED" if os.name != "nt" else "DATABASE_CAPTURE_UNPROVEN"
    )
    assert expected_reason in result.reasons
    assert source_opens == []
    assert after == before


@pytest.mark.skipif(os.name != "nt", reason="capture barrier requires Windows file-sharing semantics")
def test_stable_rollback_source_reads_only_hash_matched_private_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _ = _fixture(tmp_path)
    database = paths.database_path
    before = (database.stat().st_size, _sha(database))
    assert database.read_bytes()[18:20] == b"\x01\x01"
    assert not Path(f"{database}-wal").exists()
    assert not Path(f"{database}-shm").exists()
    assert not Path(f"{database}-journal").exists()

    source_uri = database.resolve(strict=False).as_uri() + "?mode=ro"
    original_connect = sqlite3.connect
    source_opens: list[str] = []
    original_copy = operational_update._copy_database
    copy_states: list[tuple[int, str]] = []

    def track_source_open(database_name, *args, **kwargs):
        if str(database_name) == source_uri:
            source_opens.append(str(database_name))
        return original_connect(database_name, *args, **kwargs)

    def record_private_copy(source, destination, deadline, *args, **kwargs) -> None:
        original_copy(source, destination, deadline, *args, **kwargs)
        copy_states.append((destination.stat().st_size, _sha(destination)))

    monkeypatch.setattr(sqlite3, "connect", track_source_open)
    monkeypatch.setattr(operational_update, "_copy_database", record_private_copy)
    rows, error = _database_paths(database, active_wal=True)
    after = (database.stat().st_size, _sha(database))

    assert rows == OLD_PATHS
    assert error is None
    assert source_opens == []
    assert copy_states == [(before[0], before[1])]
    assert after == before
    assert not Path(f"{database}-wal").exists()
    assert not Path(f"{database}-shm").exists()
    assert not Path(f"{database}-journal").exists()


@pytest.mark.skipif(os.name != "nt", reason="requires Windows file-sharing semantics")
def test_valid_uncheckpointed_wal_without_capture_barrier_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, journal = _fixture(tmp_path, phase="DB_COMMITTED")
    _install_backup(paths, journal)
    _install_new_identity(paths)

    source_uri = paths.database_path.resolve(strict=False).as_uri() + "?mode=ro"
    original_connect = sqlite3.connect
    source_opens: list[str] = []

    def reject_source_open(database_name, *args, **kwargs):
        if str(database_name) == source_uri:
            source_opens.append(str(database_name))
        return original_connect(database_name, *args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", reject_source_open)
    with closing(sqlite3.connect(paths.database_path)) as writer:
        assert writer.execute("PRAGMA journal_mode = WAL").fetchone() == ("wal",)
        writer.execute("PRAGMA wal_autocheckpoint = 0")
        writer.executemany(
            "UPDATE documents SET stored_path = ? WHERE id = ?",
            [(value, int(key)) for key, value in NEW_PATHS.items()],
        )
        writer.commit()

        wal = Path(f"{paths.database_path}-wal")
        shm = Path(f"{paths.database_path}-shm")
        assert wal.is_file() and wal.stat().st_size > 32
        assert shm.is_file()
        before = tuple(
            (suffix, path.read_bytes() if path.exists() else None)
            for suffix, path in (("", paths.database_path), ("-wal", wal), ("-shm", shm))
        )
        result = _classify(paths)
        after = tuple(
            (suffix, path.read_bytes() if path.exists() else None)
            for suffix, path in (("", paths.database_path), ("-wal", wal), ("-shm", shm))
        )

        assert result.classification == "RECOVERY_REQUIRED_AMBIGUOUS"
        assert "DATABASE_CAPTURE_BUSY" in result.reasons
        assert source_opens == []
        assert after == before


@pytest.mark.skipif(os.name != "nt", reason="requires Windows file-sharing semantics")
def test_wal_header_without_sidecars_is_not_eligible_for_capture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _ = _fixture(tmp_path)
    database = paths.database_path
    with closing(sqlite3.connect(database)) as writer:
        assert writer.execute("PRAGMA journal_mode = WAL").fetchone() == ("wal",)
        writer.execute("UPDATE documents SET stored_path = ? WHERE id = 1", (NEW_PATHS["1"],))
        writer.commit()
        assert writer.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()[0] == 0
    wal = Path(f"{database}-wal")
    shm = Path(f"{database}-shm")
    journal = Path(f"{database}-journal")
    assert not wal.exists()
    assert not shm.exists()
    assert not journal.exists()
    assert database.read_bytes()[18:20] == b"\x02\x02"
    before = tuple(
        (suffix, path.read_bytes() if path.exists() else None)
        for suffix, path in (("", database), ("-wal", wal), ("-shm", shm))
    )

    source_uri = database.resolve(strict=False).as_uri() + "?mode=ro"
    original_connect = sqlite3.connect
    source_opens: list[str] = []

    def track_source_open(database_name, *args, **kwargs):
        if str(database_name) == source_uri:
            source_opens.append(str(database_name))
        return original_connect(database_name, *args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", track_source_open)
    rows, error = _database_paths(database, active_wal=True)
    after = tuple(
        (suffix, path.read_bytes() if path.exists() else None)
        for suffix, path in (("", database), ("-wal", wal), ("-shm", shm))
    )

    assert rows is None
    assert error == "DATABASE_CAPTURE_UNPROVEN"
    assert source_opens == []
    assert after == before


@pytest.mark.skipif(os.name != "nt", reason="requires Windows file-sharing semantics")
def test_open_sqlite_writer_prevents_capture_before_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _ = _fixture(tmp_path)
    database = paths.database_path
    database.unlink()
    initial = {
        str(row_id): f"initial/{row_id:04d}/" + "x" * 500
        for row_id in range(1, 3001)
    }
    generation_one = {**initial, "1": "generation-1/first.pdf"}
    generation_two = {**generation_one, "3000": "generation-2/last.pdf"}

    with closing(sqlite3.connect(database)) as setup:
        setup.execute("CREATE TABLE documents (id INTEGER PRIMARY KEY, stored_path TEXT)")
        setup.executemany(
            "INSERT INTO documents(id, stored_path) VALUES (?, ?)",
            [(int(key), value) for key, value in initial.items()],
        )
        setup.commit()
        assert setup.execute("PRAGMA page_count").fetchone()[0] > 128

    def source_sqlite_files() -> tuple[tuple[str, bytes | None], ...]:
        return tuple(
            (suffix, path.read_bytes() if path.exists() else None)
            for suffix in ("", "-wal", "-shm")
            for path in (Path(f"{database}{suffix}"),)
        )

    def read_main_only(path: Path) -> dict[str, str]:
        uri = path.as_uri() + "?mode=ro&immutable=1"
        with closing(sqlite3.connect(uri, uri=True)) as connection:
            rows = connection.execute("SELECT id, stored_path FROM documents ORDER BY id")
            return {str(row[0]): str(row[1]) for row in rows.fetchall()}

    with closing(sqlite3.connect(database)) as writer:
        writer.execute(
            "UPDATE documents SET stored_path = ? WHERE id = 1",
            (generation_one["1"],),
        )
        writer.commit()
        assert not Path(f"{database}-wal").exists()
        assert not Path(f"{database}-shm").exists()
        assert not Path(f"{database}-journal").exists()
        assert read_main_only(database) == generation_one

        source_before_capture = source_sqlite_files()
        source_after_interleaving: list[tuple[tuple[str, bytes | None], ...]] = []
        copied_generations: list[tuple[str, str]] = []

        def copy_with_writer_interleaving(
            source: Path, destination: Path, deadline: float
        ) -> None:
            size = source.stat().st_size
            with source.open("rb") as input_stream, destination.open("wb") as output_stream:
                output_stream.write(input_stream.read(size // 2))
                output_stream.flush()
                writer.execute(
                    "UPDATE documents SET stored_path = ? WHERE id = 3000",
                    (generation_two["3000"],),
                )
                writer.commit()
                source_after_interleaving.append(source_sqlite_files())
                output_stream.write(input_stream.read())
            captured = read_main_only(destination)
            copied_generations.append((captured["1"], captured["3000"]))

        monkeypatch.setattr(
            operational_update, "_copy_database", copy_with_writer_interleaving
        )
        rows, error = _database_paths(database, active_wal=True)
        source_after_capture = source_sqlite_files()

    assert copied_generations == []
    assert source_after_interleaving == []
    assert source_before_capture == source_after_capture
    assert rows is None
    assert error == "DATABASE_CAPTURE_BUSY"


@pytest.mark.skipif(os.name != "nt", reason="requires Windows file-sharing semantics")
def test_copied_database_exclusive_lock_returns_unreadable_within_finite_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _ = _fixture(tmp_path)
    database = paths.database_path
    locked_copied_databases: list[Path] = []
    original_reader = operational_update._read_database_paths

    def lock_backup_database(path: Path, **kwargs):
        if path.resolve() != database.resolve():
            blocker = sqlite3.connect(path, timeout=0.1)
            blocker.execute("BEGIN EXCLUSIVE")
            locked_copied_databases.append(path)
            try:
                return original_reader(path, **kwargs)
            finally:
                blocker.close()
        return original_reader(path, **kwargs)

    monkeypatch.setattr(operational_update, "_read_database_paths", lock_backup_database)

    started = time.monotonic()
    rows, error = _database_paths(database, active_wal=True)
    elapsed = time.monotonic() - started

    assert locked_copied_databases
    assert rows is None
    assert error == "DATABASE_UNREADABLE"
    assert elapsed < 10.0


@pytest.mark.skipif(os.name != "nt", reason="requires Windows file-sharing semantics")
def test_active_wal_without_capture_barrier_is_rejected_before_source_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _ = _fixture(tmp_path)
    database = paths.database_path
    wal_path = Path(f"{database}-wal")
    shm_path = Path(f"{database}-shm")

    def source_sqlite_files() -> tuple[tuple[str, bytes | None], ...]:
        return tuple(
            (suffix, path.read_bytes() if path.exists() else None)
            for suffix, path in (
                ("", database),
                ("-wal", wal_path),
                ("-shm", shm_path),
            )
        )

    original_connect = sqlite3.connect
    source_uri = database.resolve(strict=False).as_uri() + "?mode=ro"
    source_opens: list[str] = []

    def reject_source_open(database_name, *args, **kwargs):
        if str(database_name) == source_uri:
            source_opens.append(str(database_name))
        return original_connect(database_name, *args, **kwargs)

    with closing(original_connect(database, timeout=0.1)) as blocker:
        assert blocker.execute("PRAGMA locking_mode=EXCLUSIVE").fetchone() == (
            "exclusive",
        )
        assert blocker.execute("PRAGMA journal_mode = WAL").fetchone() == ("wal",)
        blocker.execute("PRAGMA wal_autocheckpoint = 0")
        blocker.execute(
            "UPDATE documents SET stored_path = ? WHERE id = 1",
            (NEW_PATHS["1"],),
        )
        blocker.commit()
        assert wal_path.is_file() and wal_path.stat().st_size > 32
        assert not shm_path.exists()
        before = source_sqlite_files()
        monkeypatch.setattr(sqlite3, "connect", reject_source_open)

        started = time.monotonic()
        rows, error = _database_paths(database, active_wal=True)
        elapsed = time.monotonic() - started
        after = source_sqlite_files()

    assert source_opens == []
    assert after == before
    assert rows is None
    assert error == "DATABASE_CAPTURE_UNPROVEN"
    assert elapsed < 1.0


@pytest.mark.skipif(os.name != "nt", reason="requires Windows file-sharing semantics")
def test_existing_sqlite_reader_prevents_capture_barrier(
    tmp_path: Path,
) -> None:
    paths, _ = _fixture(tmp_path)
    database = paths.database_path
    sidecars = (Path(f"{database}-wal"), Path(f"{database}-shm"))

    def source_files() -> tuple[tuple[str, bytes | None], ...]:
        return tuple(
            (suffix, path.read_bytes() if path.exists() else None)
            for suffix, path in (("", database), ("-wal", sidecars[0]), ("-shm", sidecars[1]))
        )

    before = source_files()
    with closing(sqlite3.connect(database, timeout=0.1)) as reader:
        assert reader.execute("SELECT stored_path FROM documents ORDER BY id").fetchall()
        started = time.monotonic()
        rows, error = _database_paths(database, active_wal=True)
        elapsed = time.monotonic() - started

    after = source_files()
    assert after == before
    assert elapsed < 1.0
    assert rows is None
    assert error == "DATABASE_CAPTURE_BUSY"


@pytest.mark.skipif(os.name != "nt", reason="requires Windows file-sharing semantics")
def test_stable_uncheckpointed_wal_is_captured_without_source_sqlite_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _ = _fixture(tmp_path)
    database = paths.database_path
    wal_path = Path(f"{database}-wal")
    shm_path = Path(f"{database}-shm")
    crash_writer = """
import os, sqlite3, sys
connection = sqlite3.connect(sys.argv[1], timeout=0.1)
connection.execute("PRAGMA journal_mode = WAL")
connection.execute("PRAGMA wal_autocheckpoint = 0")
connection.execute("UPDATE documents SET stored_path = ? WHERE id = 1", (sys.argv[2],))
connection.commit()
print("COMMITTED", flush=True)
os._exit(0)
"""
    setup = subprocess.run(
        [sys.executable, "-c", crash_writer, str(database), NEW_PATHS["1"]],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert setup.returncode == 0, setup.stderr
    assert setup.stdout.strip() == "COMMITTED"
    assert wal_path.is_file() and shm_path.is_file()

    def source_files() -> tuple[tuple[str, bytes | None], ...]:
        return tuple(
            (suffix, path.read_bytes() if path.exists() else None)
            for suffix, path in (("", database), ("-wal", wal_path), ("-shm", shm_path))
        )

    before = source_files()
    source_uri = database.resolve(strict=False).as_uri() + "?mode=ro"
    original_connect = sqlite3.connect
    source_opens: list[str] = []
    locked_source_attempts: list[tuple[int, str]] = []
    probe_source_handles = """
import sys
for name in sys.argv[1:]:
    try:
        with open(name, "rb") as source:
            source.read(1)
    except OSError as error:
        print("BLOCKED:" + str(error))
    else:
        print("OPENED")
"""
    original_copy = operational_update._copy_database

    def track_source_open(database_name, *args, **kwargs):
        if str(database_name) == source_uri:
            source_opens.append(str(database_name))
        return original_connect(database_name, *args, **kwargs)

    def copy_with_lock_probe(source, destination, deadline, *args, **kwargs) -> None:
        if source == database:
            probe = subprocess.run(
                [sys.executable, "-c", probe_source_handles, str(database), str(wal_path), str(shm_path)],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            locked_source_attempts.append((probe.returncode, probe.stdout.strip()))
        original_copy(source, destination, deadline, *args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", track_source_open)
    monkeypatch.setattr(operational_update, "_copy_database", copy_with_lock_probe)
    rows, error = _database_paths(database, active_wal=True)
    after = source_files()

    assert after == before
    assert source_opens == []
    assert len(locked_source_attempts) == 1
    assert locked_source_attempts[0][0] == 0
    probe_lines = locked_source_attempts[0][1].splitlines()
    assert len(probe_lines) == 3
    assert all(line.startswith("BLOCKED:") for line in probe_lines)
    assert rows == {**OLD_PATHS, "1": NEW_PATHS["1"]}
    assert error is None


@pytest.mark.skipif(os.name != "nt", reason="requires Windows file-sharing semantics")
def test_sqlite_writer_started_during_capture_is_blocked_and_source_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _ = _fixture(tmp_path)
    database = paths.database_path
    original_copy = operational_update._copy_database
    writer_attempts: list[tuple[int, str]] = []
    writer = """
import sqlite3, sys
try:
    connection = sqlite3.connect(sys.argv[1], timeout=0.2)
    connection.execute("UPDATE documents SET stored_path = ? WHERE id = 1", (sys.argv[2],))
    connection.commit()
    connection.close()
    print("WRITE_SUCCEEDED")
except sqlite3.Error as error:
    print("BLOCKED:" + str(error))
"""

    def source_files() -> tuple[tuple[str, bytes | None], ...]:
        return tuple(
            (suffix, path.read_bytes() if path.exists() else None)
            for suffix in ("", "-wal", "-shm")
            for path in (Path(f"{database}{suffix}"),)
        )

    def copy_with_writer_attempt(source, destination, deadline, *args, **kwargs) -> None:
        attempt = subprocess.run(
            [sys.executable, "-c", writer, str(database), NEW_PATHS["1"]],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        writer_attempts.append((attempt.returncode, attempt.stdout.strip()))
        original_copy(source, destination, deadline, *args, **kwargs)

    before = source_files()
    monkeypatch.setattr(operational_update, "_copy_database", copy_with_writer_attempt)
    rows, error = _database_paths(database, active_wal=True)
    after = source_files()

    assert after == before, f"source changed while writer attempt ran: {writer_attempts}"
    assert writer_attempts and all(
        returncode == 0 and output.startswith("BLOCKED:")
        for returncode, output in writer_attempts
    )
    assert rows == OLD_PATHS
    assert error is None


@pytest.mark.skipif(os.name != "nt", reason="requires Windows file-sharing semantics")
def test_sidecar_added_during_copy_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _ = _fixture(tmp_path)
    database = paths.database_path
    wal_path = Path(f"{database}-wal")
    original_copy = operational_update._copy_database
    injected_wal = b"persistent injected sidecar"
    copy_calls: list[Path] = []

    def copy_then_add_sidecar(source, destination, deadline, *args, **kwargs) -> None:
        original_copy(source, destination, deadline, *args, **kwargs)
        if source == database:
            copy_calls.append(source)
            wal_path.write_bytes(injected_wal)

    monkeypatch.setattr(operational_update, "_copy_database", copy_then_add_sidecar)
    rows, error = _database_paths(database, active_wal=True)

    assert copy_calls == [database]
    assert rows is None
    assert error == "DATABASE_CHANGED_DURING_SNAPSHOT"
    assert wal_path.read_bytes() == injected_wal


def _seed_uncheckpointed_wal(database: Path) -> tuple[Path, Path, bytes, bytes]:
    writer = """
import os, sqlite3, sys
connection = sqlite3.connect(sys.argv[1], timeout=0.1)
connection.execute("PRAGMA journal_mode = WAL")
connection.execute("PRAGMA wal_autocheckpoint = 0")
connection.execute("UPDATE documents SET stored_path = ? WHERE id = 1", (sys.argv[2],))
connection.commit()
print("COMMITTED", flush=True)
os._exit(0)
"""
    setup = subprocess.run(
        [sys.executable, "-c", writer, str(database), NEW_PATHS["1"]],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert setup.returncode == 0, setup.stderr
    assert setup.stdout.strip() == "COMMITTED"

    wal_path = Path(f"{database}-wal")
    shm_path = Path(f"{database}-shm")
    assert wal_path.is_file() and shm_path.is_file()
    wal_bytes = wal_path.read_bytes()
    shm_bytes = shm_path.read_bytes()
    page_size = int.from_bytes(wal_bytes[8:12], "big")
    frame_size = 24 + page_size
    assert wal_bytes[:4] in (b"\x37\x7f\x06\x82", b"\x37\x7f\x06\x83")
    assert int.from_bytes(wal_bytes[4:8], "big") == 3007000
    assert page_size >= 512 and page_size <= 65536 and page_size & (page_size - 1) == 0
    database_page_size = int.from_bytes(database.read_bytes()[16:18], "big")
    assert page_size == (65536 if database_page_size == 1 else database_page_size)
    assert len(wal_bytes) >= 32 + frame_size
    assert (len(wal_bytes) - 32) % frame_size == 0
    assert len(shm_bytes) >= 32768 and len(shm_bytes) % 32768 == 0
    return wal_path, shm_path, wal_bytes, shm_bytes


def _assert_partial_sidecar_rejected_before_private_verification(
    database: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_paths = tuple(
        Path(f"{database}{suffix}") for suffix in ("", "-wal", "-shm")
    )

    def source_state() -> tuple[tuple[bool, bytes | None], ...]:
        return tuple(
            (path.is_file(), path.read_bytes() if path.is_file() else None)
            for path in source_paths
        )

    before = source_state()
    private_verification_paths: list[Path] = []
    original_read = operational_update._read_database_paths

    def observe_private_verification(path: Path, *args, **kwargs):
        if kwargs.get("immutable") is False:
            private_verification_paths.append(path)
        return original_read(path, *args, **kwargs)

    monkeypatch.setattr(operational_update, "_read_database_paths", observe_private_verification)
    rows, error = _database_paths(database, active_wal=True)
    after = source_state()

    assert after == before
    assert not private_verification_paths, (
        f"invalid source sidecar reached private SQLite: rows={rows!r}, error={error!r}"
    )
    assert rows is None
    assert error == "DATABASE_CAPTURE_UNPROVEN"


@pytest.mark.skipif(os.name != "nt", reason="requires Windows file-sharing semantics")
def test_capture_rejects_wal_header_without_complete_frame(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _ = _fixture(tmp_path)
    wal_path, _shm_path, valid_wal, _valid_shm = _seed_uncheckpointed_wal(
        paths.database_path
    )
    wal_path.write_bytes(valid_wal[:32])

    _assert_partial_sidecar_rejected_before_private_verification(
        paths.database_path, monkeypatch
    )


@pytest.mark.skipif(os.name != "nt", reason="requires Windows file-sharing semantics")
def test_capture_rejects_misaligned_wal_frame_tail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _ = _fixture(tmp_path)
    wal_path, _shm_path, valid_wal, _valid_shm = _seed_uncheckpointed_wal(
        paths.database_path
    )
    wal_path.write_bytes(valid_wal + b"\x00")

    _assert_partial_sidecar_rejected_before_private_verification(
        paths.database_path, monkeypatch
    )


@pytest.mark.skipif(os.name != "nt", reason="requires Windows file-sharing semantics")
@pytest.mark.parametrize(
    ("field_offset", "invalid_value"),
    [(8, 1000), (4, 0)],
    ids=("invalid-page-size", "unsupported-format-version"),
)
def test_capture_rejects_untrusted_wal_header_fields(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field_offset: int,
    invalid_value: int,
) -> None:
    paths, _ = _fixture(tmp_path)
    wal_path, _shm_path, valid_wal, _valid_shm = _seed_uncheckpointed_wal(
        paths.database_path
    )
    invalid_wal = bytearray(valid_wal)
    invalid_wal[field_offset : field_offset + 4] = invalid_value.to_bytes(4, "big")
    wal_path.write_bytes(invalid_wal)

    _assert_partial_sidecar_rejected_before_private_verification(
        paths.database_path, monkeypatch
    )


@pytest.mark.skipif(os.name != "nt", reason="requires Windows file-sharing semantics")
def test_capture_rejects_shm_truncated_below_region(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _ = _fixture(tmp_path)
    _wal_path, shm_path, _valid_wal, valid_shm = _seed_uncheckpointed_wal(
        paths.database_path
    )
    shm_path.write_bytes(valid_shm[: len(valid_shm) // 2])

    _assert_partial_sidecar_rejected_before_private_verification(
        paths.database_path, monkeypatch
    )


@pytest.mark.skipif(os.name != "nt", reason="requires Windows file-sharing semantics")
def test_capture_rejects_misaligned_shm_region(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _ = _fixture(tmp_path)
    _wal_path, shm_path, _valid_wal, valid_shm = _seed_uncheckpointed_wal(
        paths.database_path
    )
    shm_path.write_bytes(valid_shm + b"\x00")

    _assert_partial_sidecar_rejected_before_private_verification(
        paths.database_path, monkeypatch
    )


@pytest.mark.skipif(os.name == "nt", reason="only verifies unsupported non-Windows behavior")
def test_active_capture_fails_closed_off_windows_without_source_sqlite_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _ = _fixture(tmp_path)
    database = paths.database_path
    source_uri = database.resolve(strict=False).as_uri() + "?mode=ro"
    original_connect = sqlite3.connect
    source_opens: list[str] = []

    def track_source_open(database_name, *args, **kwargs):
        if str(database_name) == source_uri:
            source_opens.append(str(database_name))
        return original_connect(database_name, *args, **kwargs)

    before = database.read_bytes()
    monkeypatch.setattr(sqlite3, "connect", track_source_open)
    rows, error = _database_paths(database, active_wal=True)

    assert rows is None
    assert error == "DATABASE_CAPTURE_UNSUPPORTED"
    assert source_opens == []
    assert database.read_bytes() == before


def test_changed_input_during_observation_is_reported_unstable(tmp_path: Path) -> None:
    paths, _ = _fixture(tmp_path)

    def mutate_after_read(stage: str) -> None:
        if stage == "after_read":
            paths.config_path.write_bytes(b"external concurrent change")

    result = classify_operational_update_state(paths, observation_hook=mutate_after_read)

    assert result.classification == "OBSERVATION_UNSTABLE"
    assert result.input_stable is False
    assert "INPUT_CHANGED_DURING_OBSERVATION" in result.reasons


def _tree_identity(root: Path) -> tuple[tuple[str, str, int, str], ...]:
    rows = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            rows.append((relative, "link", 0, os.readlink(path)))
        elif path.is_dir():
            rows.append((relative, "directory", 0, ""))
        else:
            rows.append((relative, "file", path.stat().st_size, _sha(path)))
    return tuple(rows)


@pytest.mark.parametrize(
    "corruption",
    (
        "unsupported_phase",
        "unsupported_result",
        "unsupported_action",
        "terminal_phase_result_mismatch",
        "malformed_transition",
        "transition_sequence_gap",
        "pending_action_mismatch",
        "missing_active_path",
        "missing_acceptance_path",
    ),
)
@pytest.mark.parametrize("entrypoint", ("startup", "recovery", "append"))
def test_malformed_update_journal_is_rejected_before_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    corruption: str,
    entrypoint: str,
) -> None:
    paths, state_path, state = _interrupted_update_for_path_test(tmp_path, monkeypatch)
    if corruption == "unsupported_phase":
        state["phase"] = "UNKNOWN_PHASE"
    elif corruption == "unsupported_result":
        state["result"] = "UNKNOWN_RESULT"
    elif corruption == "unsupported_action":
        state["transitions"][-1]["action"] = "ARBITRARY_FILESYSTEM_ACTION"
    elif corruption == "terminal_phase_result_mismatch":
        state["phase"] = "TERMINAL"
        state["result"] = "RECOVERY_REQUIRED"
    elif corruption == "malformed_transition":
        state["transitions"][-1] = "not-a-transition"
    elif corruption == "transition_sequence_gap":
        state["transitions"][-1]["sequence"] = len(state["transitions"]) + 7
    elif corruption == "pending_action_mismatch":
        state["pending_action"] = "ACTION_WITHOUT_LAST_INTENT"
    elif corruption == "missing_active_path":
        del state["application"]["active_path"]
    elif corruption == "missing_acceptance_path":
        del state["acceptance"]["snapshot_path"]
    state_path.write_text(json.dumps(state), encoding="utf-8")

    state_before = state_path.read_bytes()
    app_before = operational_update._generation_identity(paths.application_root)
    acceptance_before = paths.acceptance_path.read_bytes()
    marker_path = paths.control_root / "update_marker.json"
    marker_before = marker_path.read_bytes()
    with pytest.raises(operational_update.OperationalUpdateError):
        if entrypoint == "startup":
            operational_update.assert_operational_startup_allowed(paths)
        elif entrypoint == "recovery":
            operational_update.recover_operational_application_update(paths)
        else:
            operational_update._append_update_transition(
                state_path,
                kind="RECOVERY_INTENT",
                action="SYNTHETIC_VALIDATION_PROBE",
                before={},
                expected={},
            )

    assert state_path.read_bytes() == state_before
    assert operational_update._generation_identity(paths.application_root) == app_before
    assert paths.acceptance_path.read_bytes() == acceptance_before
    assert marker_path.read_bytes() == marker_before


@pytest.mark.parametrize("projected_length", (240, 241))
def test_update_tree_identity_enforces_projected_windows_path_boundary(
    tmp_path: Path, projected_length: int
) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "payload.bin").write_bytes(b"payload")
    filename = "payload.bin"
    drive_root = Path("C:/")
    component_length = projected_length - len(str(drive_root)) - 1 - len(filename)
    projected_root = drive_root / ("p" * component_length)
    projected_file = projected_root / filename
    assert len(str(projected_file)) == projected_length

    if projected_length == 240:
        assert operational_update._update_tree_identity(
            bundle, projected_roots=(projected_root,)
        )["files"] == 1
    else:
        with pytest.raises(operational_update.OperationalUpdateError, match="UPDATE_PATH_TOO_LONG"):
            operational_update._update_tree_identity(
                bundle, projected_roots=(projected_root,)
            )


@pytest.mark.parametrize("projected_length", (240, 241))
def test_update_tree_identity_checks_projected_empty_directory_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    projected_length: int,
) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    projected_root = Path("C:/") / "projection"
    directory_name = "d" * (projected_length - len(str(projected_root)) - 1)
    directory = bundle / directory_name
    projected_path = projected_root / directory_name
    assert len(str(projected_path)) == projected_length
    monkeypatch.setattr(
        operational_update.os,
        "walk",
        lambda _root, followlinks: [(str(bundle), [directory_name], [])],
    )
    original_lstat = Path.lstat

    def synthetic_directory_lstat(path: Path):
        if path == directory:
            return SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0)
        return original_lstat(path)

    monkeypatch.setattr(Path, "lstat", synthetic_directory_lstat)

    if projected_length == 240:
        assert operational_update._update_tree_identity(
            bundle, projected_roots=(projected_root,)
        )["files"] == 0
    else:
        with pytest.raises(
            operational_update.OperationalUpdateError, match="UPDATE_PATH_TOO_LONG"
        ):
            operational_update._update_tree_identity(
                bundle, projected_roots=(projected_root,)
            )


@pytest.mark.parametrize("projected_length", (240, 241))
def test_update_preflight_budgets_durable_json_temporary_names(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    projected_length: int,
) -> None:
    paths, bundle = _app_update_fixture(tmp_path / "operational")
    update_id = "a" * 32
    temp_path = Path("C:/") / ("t" * (projected_length - len("C:/")))
    assert len(str(temp_path)) == projected_length
    monkeypatch.setattr(
        operational_update, "_durable_json_temp_path", lambda _path: temp_path
    )

    if projected_length == 240:
        operational_update._preflight_update_generation(paths, bundle, update_id)
    else:
        with pytest.raises(
            operational_update.OperationalUpdateError, match="UPDATE_PATH_TOO_LONG"
        ):
            operational_update._preflight_update_generation(paths, bundle, update_id)
        assert not (paths.control_root / "updates" / update_id).exists()
        assert not (paths.root / ".update" / update_id).exists()
        assert not (paths.data_dir / "backups" / update_id).exists()


@pytest.mark.parametrize(
    "redirect",
    (
        "database_path",
        "config_path",
        "artifact_root",
        "artifact_key",
        "unsupported_sidecar",
        "database_type",
    ),
)
def test_lkg_manifest_rejects_snapshot_path_or_artifact_redirection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    redirect: str,
) -> None:
    paths, state_path, state = _interrupted_update_for_path_test(tmp_path, monkeypatch)
    manifest_path = paths.root / state["lkg_manifest_path"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    database = manifest["database_snapshot"]
    config = manifest["config_snapshot"]
    artifacts = manifest["snapshot_artifacts"]

    if redirect == "database_path":
        database["path"] = "Data/data/backups/other/egp.db"
    elif redirect == "config_path":
        config["path"] = "Data/data/backups/other/config.yaml"
    elif redirect == "artifact_root":
        old_path = next(iter(artifacts))
        artifacts[old_path.replace(state["update_id"], "b" * 32)] = artifacts.pop(old_path)
    elif redirect == "artifact_key":
        artifacts["Data/data/backups/other/egp.db"] = artifacts.pop(database["path"])
    elif redirect == "unsupported_sidecar":
        database["sidecars"]["-journal"] = {"exists": True}
    else:
        manifest["database_snapshot"] = ["malformed"]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(operational_update.OperationalUpdateError):
        operational_update._verify_lkg_binding(
            paths,
            state,
            state["update_id"],
            paths.root / state["application"]["old_path"],
        )
    assert state_path.is_file()


def test_recovery_rejects_other_unresolved_attempt_when_marker_is_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _state_path, state = _interrupted_update_for_path_test(tmp_path, monkeypatch)
    other_id = "b" * 32
    other = json.loads(json.dumps(state))
    expected = operational_update._expected_update_paths(paths, other_id)
    other["update_id"] = other_id
    other["application"]["active_path"] = expected["active"].relative_to(paths.root).as_posix()
    other["application"]["old_path"] = expected["old"].relative_to(paths.root).as_posix()
    other["application"]["stage_path"] = expected["stage"].relative_to(paths.root).as_posix()
    other["application"]["failed_path"] = expected["failed"].relative_to(paths.root).as_posix()
    other["acceptance"]["snapshot_path"] = expected[
        "acceptance_snapshot"
    ].relative_to(paths.root).as_posix()
    other["lkg_manifest_path"] = expected["lkg_manifest"].relative_to(paths.root).as_posix()
    other_journal = expected["journal"]
    other_journal.parent.mkdir(parents=True)
    other_journal.write_text(json.dumps(other), encoding="utf-8")
    active_before = operational_update._generation_identity(paths.application_root)
    acceptance_before = paths.acceptance_path.read_bytes()
    marker_before = (paths.control_root / "update_marker.json").read_bytes()

    with pytest.raises(operational_update.OperationalUpdateError, match="UPDATE_JOURNAL_ORPHAN"):
        operational_update.recover_operational_application_update(paths)

    assert operational_update._generation_identity(paths.application_root) == active_before
    assert paths.acceptance_path.read_bytes() == acceptance_before
    assert (paths.control_root / "update_marker.json").read_bytes() == marker_before


@pytest.mark.parametrize("entrypoint", ("startup", "recovery"))
def test_orphan_attempt_directory_without_state_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    entrypoint: str,
) -> None:
    paths, _state_path, _state = _interrupted_update_for_path_test(tmp_path, monkeypatch)
    (paths.control_root / "update_marker.json").unlink()
    orphan = paths.control_root / "updates" / ("c" * 32)
    orphan.mkdir()
    active_before = operational_update._generation_identity(paths.application_root)
    acceptance_before = paths.acceptance_path.read_bytes()

    with pytest.raises(operational_update.OperationalUpdateError, match="UPDATE_JOURNAL_REQUIRED"):
        if entrypoint == "startup":
            operational_update.assert_operational_startup_allowed(paths)
        else:
            operational_update.recover_operational_application_update(paths)

    assert operational_update._generation_identity(paths.application_root) == active_before
    assert paths.acceptance_path.read_bytes() == acceptance_before
    assert not (paths.control_root / "update_marker.json").exists()


def test_update_path_safety_preflight_runs_before_control_lock_creation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, bundle = _app_update_fixture(tmp_path / "operational")
    original = Path.lstat

    def mark_root_as_reparse(path: Path):
        if path == paths.root:
            return SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400)
        return original(path)

    monkeypatch.setattr(Path, "lstat", mark_root_as_reparse)
    with pytest.raises(operational_update.OperationalUpdateError, match="UPDATE_ROOT_PATH_UNSAFE"):
        operational_update.apply_operational_application_update(paths, bundle, confirmed=True)
    assert not (paths.control_root / "update.lock").exists()
    assert not (paths.control_root / "updates").exists()
    assert not (paths.root / ".update").exists()


def test_update_path_safety_rejects_control_escape_before_lock_creation(
    tmp_path: Path,
) -> None:
    paths, bundle = _app_update_fixture(tmp_path / "operational")
    escaped = replace(paths, control_root=paths.root.parent / "outside-control")
    with pytest.raises(operational_update.OperationalUpdateError, match="UPDATE_CONTROL_PATH_UNSAFE"):
        operational_update.apply_operational_application_update(escaped, bundle, confirmed=True)
    assert not (paths.control_root / "update.lock").exists()
    assert not (escaped.control_root / "update.lock").exists()
    assert not (paths.control_root / "updates").exists()


def test_update_path_preflight_rejects_overlong_bundle_before_attempt_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, bundle = _app_update_fixture(tmp_path / "operational")
    extra_name = "p" * 110 + ".bin"
    (bundle / extra_name).write_bytes(b"synthetic payload")
    active_before = operational_update._generation_identity(paths.application_root)
    acceptance_before = paths.acceptance_path.read_bytes()
    monkeypatch.setattr(operational_update, "_assert_no_old_runtime_holders", lambda *_args: None)

    with pytest.raises(operational_update.OperationalUpdateError, match="UPDATE_PATH_TOO_LONG"):
        operational_update.apply_operational_application_update(paths, bundle, confirmed=True)

    assert operational_update._generation_identity(paths.application_root) == active_before
    assert paths.acceptance_path.read_bytes() == acceptance_before
    assert not (paths.control_root / "updates").exists()
    assert not (paths.control_root / "update_marker.json").exists()
    assert not (paths.root / ".update").exists()


def test_update_preflight_rejects_same_volume_mismatch_before_attempt_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, bundle = _app_update_fixture(tmp_path / "operational")
    monkeypatch.setattr(operational_update, "_assert_no_old_runtime_holders", lambda *_args: None)
    original_stat = Path.stat

    def different_active_volume(path: Path, *args, **kwargs):
        result = original_stat(path, *args, **kwargs)
        if path == paths.application_root:
            return SimpleNamespace(st_dev=result.st_dev + 1, st_mode=result.st_mode)
        return result

    monkeypatch.setattr(Path, "stat", different_active_volume)
    with pytest.raises(
        operational_update.OperationalUpdateError, match="UPDATE_ROTATION_VOLUME_MISMATCH"
    ):
        operational_update.apply_operational_application_update(paths, bundle, confirmed=True)
    assert not (paths.control_root / "updates").exists()
    assert not (paths.root / ".update").exists()


@pytest.mark.parametrize("reparse_target", ("current", "bundle", "transient"))
def test_update_preflight_rejects_reparse_paths_before_attempt_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    reparse_target: str,
) -> None:
    paths, bundle = _app_update_fixture(tmp_path / "operational")
    monkeypatch.setattr(operational_update, "_assert_no_old_runtime_holders", lambda *_args: None)
    transient = paths.root / ".update"
    if reparse_target == "transient":
        transient.mkdir()
    target = {
        "current": paths.application_root,
        "bundle": bundle,
        "transient": transient,
    }[reparse_target]
    original_lstat = Path.lstat

    def mark_target_as_reparse(path: Path):
        if path == target:
            return SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400)
        return original_lstat(path)

    monkeypatch.setattr(Path, "lstat", mark_target_as_reparse)
    with pytest.raises(operational_update.OperationalUpdateError, match="UPDATE_.*PATH_UNSAFE"):
        operational_update.apply_operational_application_update(paths, bundle, confirmed=True)
    assert not (paths.control_root / "updates").exists()
    assert not (paths.root / ".update" / ("1" * 32)).exists()


def test_update_attempt_collision_fails_before_attempt_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, bundle = _app_update_fixture(tmp_path / "operational")
    update_id = "a" * 32
    monkeypatch.setattr(operational_update, "uuid4", lambda: SimpleNamespace(hex=update_id))
    collision = paths.root / ".update" / update_id
    collision.mkdir(parents=True)
    sentinel = collision / "preserve.txt"
    sentinel.write_bytes(b"existing transient generation")
    monkeypatch.setattr(operational_update, "_assert_no_old_runtime_holders", lambda *_args: None)

    with pytest.raises(
        operational_update.OperationalUpdateError, match="UPDATE_ID_COLLISION_OR_UNSAFE"
    ):
        operational_update._preflight_update_generation(paths, bundle, update_id)
    assert sentinel.read_bytes() == b"existing transient generation"
    assert not (paths.control_root / "updates" / update_id).exists()
