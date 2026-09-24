from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from qi_crawler.operational_release import OperationalPaths, operational_paths
from qi_crawler.operational_update import (
    JOURNAL_SCHEMA,
    MARKER_SCHEMA,
    RECEIPT_SCHEMA,
    classify_operational_update_state,
)

UPDATE_ID = "update-01"
OLD_PATHS = {"1": "documents/old-a.pdf", "2": "documents/old-b.pdf"}
NEW_PATHS = {"1": "documents/new-a.pdf", "2": "documents/new-b.pdf"}


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


def test_observation_is_read_only_and_preserves_tree_identity(tmp_path: Path) -> None:
    paths, journal = _fixture(tmp_path, phase="BACKUP_REQUIRED")
    _install_backup(paths, journal)
    wal = Path(f"{paths.database_path}-wal")
    shm = Path(f"{paths.database_path}-shm")
    wal.write_bytes(b"pre-existing wal evidence")
    shm.write_bytes(b"pre-existing shm evidence")

    before = _tree_identity(paths.root)
    result = _classify(paths)
    after = _tree_identity(paths.root)

    assert result.classification == "BACKUP_VALID"
    assert after == before


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
