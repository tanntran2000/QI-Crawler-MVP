from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from qi_crawler import operational_release, standalone
from qi_crawler.db import CURRENT_SCHEMA_REVISION
from qi_crawler.migrations import upgrade_database
from qi_crawler.operational_release import (
    OPERATIONAL_ACCEPTANCE_SCHEMA_VERSION,
    OPERATIONAL_MIGRATION_RECEIPT_SCHEMA_VERSION,
    OperationalReleaseError,
    operational_paths,
    promote_live_operational_root,
    promote_synthetic_operational_root,
    validate_operational_acceptance,
)
from scripts import promote_operational_release as promotion_cli

SOURCE_SHA = "a" * 40
VERIFIED_MAIN_SHA = "b" * 40
OLD_PREMERGE_SHA = "166c96d5c530d72f2cb7b8703c89f940fd9a939f"
SOURCE_REVISION = "0020_add_tender_operational_revision_events"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _write_schema_marker(path: Path, revision: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        connection.execute("CREATE TABLE alembic_version (version_num TEXT NOT NULL)")
        connection.execute("INSERT INTO alembic_version VALUES (?)", (revision,))
        connection.commit()
    finally:
        connection.close()


def _create_database_at_0020(path: Path, root: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    upgrade_database(f"sqlite:///{path.as_posix()}", backup_dir=root / "backups")
    connection = sqlite3.connect(path)
    try:
        connection.execute(
            "UPDATE alembic_version SET version_num = ?",
            (SOURCE_REVISION,),
        )
        connection.commit()
    finally:
        connection.close()


def _write_metadata(
    bundle: Path,
    *,
    channel: str = "INTERNAL_PILOT",
    source_sha: str = SOURCE_SHA,
    source_branch: str = "release/v0.10-b09-operational-rebind-01",
) -> dict[str, str]:
    executable = bundle / "QI-Crawler.exe"
    executable.write_bytes(b"synthetic-operational-executable")
    portable_hash = _sha256(executable)
    manifest = {
        "metadata_schema_version": "qi-crawler-installed-release-v1",
        "product": "QI-Crawler",
        "version": "0.10.0",
        "source_git_sha": source_sha,
        "source_branch": source_branch,
        "build_timestamp_utc": "2026-09-22T00:00:00Z",
        "alembic_head": CURRENT_SCHEMA_REVISION,
        "release_channel": channel,
        "portable_exe_sha256": portable_hash,
    }
    (bundle / "release_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    (bundle / "BUILD_INFO.txt").write_text(
        "\n".join(f"{key}={value}" for key, value in manifest.items()) + "\n",
        encoding="utf-8",
    )
    (bundle / "runtime").mkdir()
    return manifest


def _write_operational_fixture(
    root: Path,
    *,
    acceptance: bool = True,
    wrong_root: Path | None = None,
    database_path: Path | None = None,
    channel: str = "INTERNAL_PILOT",
) -> tuple[Path, Path]:
    paths = operational_paths(root)
    paths.application_root.mkdir(parents=True)
    paths.data_root.mkdir(parents=True)
    paths.config_path.write_text("storage: {}\n", encoding="utf-8")
    operational_release._rewrite_operational_config(paths.config_path, paths)
    for directory in paths.data_directories:
        directory.mkdir(parents=True, exist_ok=True)
    paths.control_root.mkdir(parents=True, exist_ok=True)
    database = database_path or paths.database_path
    _write_schema_marker(database, CURRENT_SCHEMA_REVISION)
    manifest = _write_metadata(paths.application_root, channel=channel)
    paths.migration_receipt_path.write_text(
        json.dumps(
            {
                "receipt_schema_version": OPERATIONAL_MIGRATION_RECEIPT_SCHEMA_VERSION,
                "status": "PASS",
                "source_git_sha": SOURCE_SHA,
                "from_revision": SOURCE_REVISION,
                "to_revision": CURRENT_SCHEMA_REVISION,
                "output_db_sha256": _sha256(database),
            }
        )
        + "\n",
        encoding="utf-8",
    )
    if acceptance:
        bound_root = (wrong_root or root).resolve()
        receipt = {
            "acceptance_schema_version": OPERATIONAL_ACCEPTANCE_SCHEMA_VERSION,
            "status": "ACCEPTED",
            "operational_root": str(bound_root),
            "application_root": str((bound_root / "Current" / "QI-Crawler").resolve()),
            "executable": str((bound_root / "Current" / "QI-Crawler" / "QI-Crawler.exe").resolve()),
            "data_root": str((bound_root / "Data").resolve()),
            "config_path": str((bound_root / "Data" / "config.yaml").resolve()),
            "database_path": str(database.resolve()),
            "product": manifest["product"],
            "version": manifest["version"],
            "source_git_sha": SOURCE_SHA,
            "source_branch": manifest["source_branch"],
            "build_timestamp_utc": manifest["build_timestamp_utc"],
            "release_channel": manifest["release_channel"],
            "portable_exe_sha256": manifest["portable_exe_sha256"],
            "release_manifest_sha256": _sha256(paths.release_manifest_path),
            "build_info_sha256": _sha256(paths.build_info_path),
            "schema_revision": CURRENT_SCHEMA_REVISION,
            "migration_receipt_sha256": _sha256(paths.migration_receipt_path),
            "migration_source_sha": SOURCE_SHA,
            "migration_from_revision": SOURCE_REVISION,
            "migration_to_revision": CURRENT_SCHEMA_REVISION,
            "database_sha256": _sha256(database),
            "created_at": "2026-09-22T00:00:00Z",
        }
        paths.acceptance_path.write_text(
            json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
        )
    return paths.executable, paths.database_path


def test_internal_pilot_requires_operational_acceptance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    executable, _ = _write_operational_fixture(tmp_path / "operational", acceptance=False)
    monkeypatch.setattr(operational_release, "OPERATIONAL_ROOT", (tmp_path / "operational"))
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(executable))
    with pytest.raises(OperationalReleaseError, match="OPERATIONAL_ACCEPTANCE_REQUIRED"):
        standalone.authorize_frozen_runtime([])


def test_valid_operational_binding_precedes_database_initialization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "operational"
    executable, database = _write_operational_fixture(root)
    monkeypatch.setattr(operational_release, "OPERATIONAL_ROOT", root)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(executable))
    keys = ("QI_CRAWLER_DATA_DIR", "QI_CRAWLER_CONFIG_PATH", "QI_CRAWLER_DATABASE_URL")
    previous = {key: os.environ.get(key) for key in keys}
    try:
        assert standalone.authorize_frozen_runtime([]) == "ACCEPTED_OPERATIONAL"
        assert Path(os.environ["QI_CRAWLER_DATA_DIR"]) == root / "Data"
        assert Path(os.environ["QI_CRAWLER_CONFIG_PATH"]) == root / "Data" / "config.yaml"
        assert os.environ["QI_CRAWLER_DATABASE_URL"] == f"sqlite:///{database.as_posix()}"
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def test_operational_acceptance_wrong_root_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "operational"
    executable, _ = _write_operational_fixture(root, wrong_root=tmp_path / "other")
    with pytest.raises(OperationalReleaseError, match="OPERATIONAL_ROOT_MISMATCH"):
        validate_operational_acceptance(executable)


def test_operational_database_outside_data_root_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "operational"
    external_db = tmp_path / "outside.db"
    executable, _ = _write_operational_fixture(root, database_path=external_db)
    with pytest.raises(OperationalReleaseError, match="OPERATIONAL_DATABASE_PATH_INVALID"):
        validate_operational_acceptance(executable)


def test_candidate_receipt_cannot_substitute_operational_receipt(tmp_path: Path) -> None:
    root = tmp_path / "operational"
    executable, _ = _write_operational_fixture(root, acceptance=False)
    paths = operational_paths(root)
    (paths.control_root / "pre_start_acceptance.json").write_text("{}", encoding="utf-8")
    with pytest.raises(OperationalReleaseError, match="OPERATIONAL_ACCEPTANCE_REQUIRED"):
        validate_operational_acceptance(executable)


def test_unexpected_operational_layout_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bundle = tmp_path / "unexpected" / "QI-Crawler"
    bundle.mkdir(parents=True)
    executable = bundle / "QI-Crawler.exe"
    executable.write_bytes(b"wrong-layout")
    _write_metadata(bundle)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(executable))
    with pytest.raises(standalone.StandaloneResourceError, match="OPERATIONAL_LAYOUT_INVALID"):
        standalone.authorize_frozen_runtime([])


def test_synthetic_promotion_migrates_copy_without_mutating_source(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source_bundle = source / "app" / "QI-Crawler"
    source_bundle.mkdir(parents=True)
    _write_metadata(source_bundle)
    source_data = source / "data"
    source_db = source_data / "data" / "database" / "egp.db"
    _create_database_at_0020(source_db, source_data)
    (source_data / "config.yaml").write_text("storage: {}\n", encoding="utf-8")
    before = _sha256(source_db)
    result = promote_synthetic_operational_root(
        source_bundle,
        source_data,
        tmp_path / "operational",
        source_git_sha=SOURCE_SHA,
    )
    assert result["status"] == "PROMOTED_SYNTHETIC"
    assert _sha256(source_db) == before
    final = operational_paths(tmp_path / "operational")
    assert validate_operational_acceptance(final.executable)["schema_revision"] == CURRENT_SCHEMA_REVISION


def test_synthetic_promotion_rejects_overlapping_roots(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source_bundle = source / "app" / "QI-Crawler"
    source_bundle.mkdir(parents=True)
    _write_metadata(source_bundle)
    source_data = source / "data"
    _create_database_at_0020(source_data / "data" / "database" / "egp.db", source_data)
    (source_data / "config.yaml").write_text("storage: {}\n", encoding="utf-8")

    with pytest.raises(OperationalReleaseError, match="SYNTHETIC_ROOT_OVERLAP"):
        promote_synthetic_operational_root(
            source_bundle,
            source_data,
            source,
            source_git_sha=SOURCE_SHA,
        )


def _promotion_inputs(tmp_path: Path) -> tuple[Path, Path, Path, str]:
    source = tmp_path / "source"
    bundle = source / "app" / "QI-Crawler"
    bundle.mkdir(parents=True)
    _write_metadata(bundle)
    data = source / "data"
    _create_database_at_0020(data / "data" / "database" / "egp.db", data)
    (data / "config.yaml").write_text("storage: {}\n", encoding="utf-8")
    destination = tmp_path / "operational"
    destination.mkdir()
    (destination / "old.txt").write_text("old", encoding="utf-8")
    return bundle, data, destination, SOURCE_SHA


def test_promotion_failure_before_cutover_preserves_original_root(tmp_path: Path) -> None:
    bundle, data, destination, source_sha = _promotion_inputs(tmp_path)
    before = (destination / "old.txt").read_text(encoding="utf-8")
    with pytest.raises(OperationalReleaseError, match="PROMOTION_FAILED_BEFORE_CUTOVER"):
        promote_synthetic_operational_root(
            bundle, data, destination, source_git_sha=source_sha, fail_stage="before_cutover"
        )
    assert (destination / "old.txt").read_text(encoding="utf-8") == before
    assert not (destination / "Current").exists()


def test_promotion_failure_after_rotation_rolls_back(tmp_path: Path) -> None:
    bundle, data, destination, source_sha = _promotion_inputs(tmp_path)
    with pytest.raises(OperationalReleaseError, match="PROMOTION_FAILED_AFTER_ROTATION"):
        promote_synthetic_operational_root(
            bundle, data, destination, source_git_sha=source_sha, fail_stage="after_rotation"
        )
    assert (destination / "old.txt").read_text(encoding="utf-8") == "old"
    assert not (destination / "control").exists()


def test_successful_synthetic_promotion_is_internally_coherent(tmp_path: Path) -> None:
    bundle, data, destination, source_sha = _promotion_inputs(tmp_path)
    result = promote_synthetic_operational_root(bundle, data, destination, source_git_sha=source_sha)
    paths = operational_paths(destination)
    assert result["status"] == "PROMOTED_SYNTHETIC"
    assert paths.executable.is_file()
    assert paths.config_path.is_file()
    assert paths.acceptance_path.is_file()
    assert paths.database_path.is_file()
    acceptance = validate_operational_acceptance(paths.executable)
    assert acceptance["operational_root"] == str(destination.resolve())
    migration = json.loads(paths.migration_receipt_path.read_text(encoding="utf-8"))
    assert acceptance["database_sha256"] == migration["output_db_sha256"]
    storage = yaml.safe_load(paths.config_path.read_text(encoding="utf-8"))["storage"]
    assert storage == {
        "database_url": f"sqlite:///{paths.database_path.as_posix()}",
        "document_dir": str(paths.data_dir / "documents"),
        "download_dir": str(paths.data_dir / "downloads"),
        "discovery_dir": str(paths.data_dir / "discovery"),
        "raw_dir": str(paths.data_dir / "raw"),
        "rejects_dir": str(paths.data_dir / "rejects"),
        "report_dir": str(paths.data_dir / "reports"),
    }


def test_operational_startup_accepts_legitimate_database_write_after_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "operational"
    executable, database = _write_operational_fixture(root)
    monkeypatch.setattr(operational_release, "OPERATIONAL_ROOT", root)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(executable))
    for key in ("QI_CRAWLER_DATA_DIR", "QI_CRAWLER_CONFIG_PATH", "QI_CRAWLER_DATABASE_URL"):
        monkeypatch.setenv(key, "before-test")

    assert standalone.authorize_frozen_runtime([]) == "ACCEPTED_OPERATIONAL"
    original_sha = _sha256(database)
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE operational_note (value TEXT NOT NULL)")
        connection.execute("INSERT INTO operational_note VALUES ('saved')")
    assert _sha256(database) != original_sha

    assert standalone.authorize_frozen_runtime([]) == "ACCEPTED_OPERATIONAL"
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT value FROM operational_note").fetchone() == ("saved",)
    paths = operational_paths(root)
    acceptance = json.loads(paths.acceptance_path.read_text(encoding="utf-8"))
    migration = json.loads(paths.migration_receipt_path.read_text(encoding="utf-8"))
    assert acceptance["database_sha256"].lower() == migration["output_db_sha256"].lower()
    assert _sha256(database).lower() != acceptance["database_sha256"].lower()


def test_pre_cutover_config_is_rebound_only_after_stage_acceptance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle, data, destination, source_sha = _promotion_inputs(tmp_path)
    original_validate = operational_release.validate_operational_acceptance
    original_replace = operational_release._atomic_directory_replace
    stage_validated = False
    prebound = False

    def validate(executable: Path, *, expected_version: str = "0.10.0") -> dict[str, object]:
        nonlocal stage_validated
        if ".stage-" in str(executable):
            stage_paths = operational_paths(executable.parent.parent.parent)
            storage = yaml.safe_load(stage_paths.config_path.read_text(encoding="utf-8"))["storage"]
            assert storage["database_url"] == f"sqlite:///{stage_paths.database_path.as_posix()}"
            stage_validated = True
        return original_validate(executable, expected_version=expected_version)

    def replace(source: Path, target: Path) -> None:
        nonlocal prebound
        if target == destination.parent / "operational.rollback":
            assert stage_validated
            # The staged config must point to the future destination before old-root rotation.
            staged = next(destination.parent.glob(f".{destination.name}.stage-*"))
            storage = yaml.safe_load((staged / "Data" / "config.yaml").read_text(encoding="utf-8"))["storage"]
            assert storage["database_url"] == f"sqlite:///{operational_paths(destination).database_path.as_posix()}"
            prebound = True
        original_replace(source, target)

    monkeypatch.setattr(operational_release, "validate_operational_acceptance", validate)
    monkeypatch.setattr(operational_release, "_atomic_directory_replace", replace)
    promote_synthetic_operational_root(bundle, data, destination, source_git_sha=source_sha)
    assert stage_validated and prebound


@pytest.mark.parametrize(
    "bad_config",
    [
        pytest.param("storage: [bad]\n", id="wrong-storage-type"),
        pytest.param("other: value\n", id="missing-storage"),
        pytest.param("storage: {database_url: sqlite:///missing.db}\n", id="missing-directories"),
        pytest.param("storage: {database_url: 7}\n", id="wrong-database-url-type"),
        pytest.param("storage: [\n", id="malformed-yaml"),
        pytest.param("[]\n", id="wrong-root-type"),
    ],
)
def test_operational_acceptance_rejects_invalid_persisted_config(
    tmp_path: Path, bad_config: str
) -> None:
    executable, _ = _write_operational_fixture(tmp_path / "operational")
    operational_paths(tmp_path / "operational").config_path.write_text(bad_config, encoding="utf-8")
    with pytest.raises(OperationalReleaseError, match="OPERATIONAL_CONFIG_BINDING_INVALID"):
        validate_operational_acceptance(executable)


@pytest.mark.parametrize("key", ["database_url", "document_dir", "download_dir", "discovery_dir", "raw_dir", "rejects_dir", "report_dir"])
def test_operational_acceptance_rejects_missing_storage_key(tmp_path: Path, key: str) -> None:
    executable, _ = _write_operational_fixture(tmp_path / "operational")
    config_path = operational_paths(tmp_path / "operational").config_path
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    del config["storage"][key]
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    with pytest.raises(OperationalReleaseError, match="OPERATIONAL_CONFIG_BINDING_INVALID"):
        validate_operational_acceptance(executable)


@pytest.mark.parametrize("key", ["database_url", "document_dir", "download_dir", "discovery_dir", "raw_dir", "rejects_dir", "report_dir"])
@pytest.mark.parametrize("escaped_root", [".operational.stage-old", "rollback", "AppData", "candidate"])
def test_operational_acceptance_rejects_stale_storage_path(
    tmp_path: Path, key: str, escaped_root: str
) -> None:
    executable, _ = _write_operational_fixture(tmp_path / "operational")
    config_path = operational_paths(tmp_path / "operational").config_path
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    escaped = tmp_path / escaped_root / "Data" / "data" / "documents"
    config["storage"][key] = f"sqlite:///{escaped.as_posix()}" if key == "database_url" else str(escaped)
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    with pytest.raises(OperationalReleaseError, match="OPERATIONAL_CONFIG_BINDING_INVALID"):
        validate_operational_acceptance(executable)
    assert not escaped.parent.exists()


@pytest.mark.parametrize("url", ["sqlite:///:memory:", "postgresql:///egp.db", "sqlite://user:pass@localhost/egp.db", "sqlite:///egp.db?mode=ro"])
def test_operational_acceptance_rejects_invalid_database_url(tmp_path: Path, url: str) -> None:
    executable, _ = _write_operational_fixture(tmp_path / "operational")
    config_path = operational_paths(tmp_path / "operational").config_path
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["storage"]["database_url"] = url
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    with pytest.raises(OperationalReleaseError, match="OPERATIONAL_CONFIG_BINDING_INVALID"):
        validate_operational_acceptance(executable)


def test_operational_acceptance_rejects_configured_symlink_escape(tmp_path: Path) -> None:
    executable, _ = _write_operational_fixture(tmp_path / "operational")
    paths = operational_paths(tmp_path / "operational")
    outside = tmp_path / "outside"
    outside.mkdir()
    document_dir = paths.data_dir / "documents"
    document_dir.rmdir()
    try:
        document_dir.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("directory symlinks unavailable on this host")
    with pytest.raises(OperationalReleaseError, match="OPERATIONAL_CONFIG_BINDING_INVALID"):
        validate_operational_acceptance(executable)


def test_operational_acceptance_rejects_config_file_symlink_escape(tmp_path: Path) -> None:
    executable, _ = _write_operational_fixture(tmp_path / "operational")
    config_path = operational_paths(tmp_path / "operational").config_path
    outside = tmp_path / "outside-config.yaml"
    outside.write_bytes(config_path.read_bytes())
    config_path.unlink()
    try:
        config_path.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("file symlinks unavailable on this host")
    with pytest.raises(OperationalReleaseError, match="OPERATIONAL_CONFIG_BINDING_INVALID"):
        validate_operational_acceptance(executable)


def test_operational_acceptance_rejects_wrong_schema_after_database_write(tmp_path: Path) -> None:
    executable, database = _write_operational_fixture(tmp_path / "operational")
    with sqlite3.connect(database) as connection:
        connection.execute("UPDATE alembic_version SET version_num = 'wrong'")
    with pytest.raises(OperationalReleaseError, match="OPERATIONAL_SCHEMA_MISMATCH"):
        validate_operational_acceptance(executable)


def test_operational_acceptance_rejects_unusable_database(tmp_path: Path) -> None:
    executable, database = _write_operational_fixture(tmp_path / "operational")
    database.write_bytes(b"not a SQLite database")
    with pytest.raises(OperationalReleaseError, match="OPERATIONAL_DATABASE_INVALID"):
        validate_operational_acceptance(executable)


def test_operational_acceptance_rejects_tampered_migration_baseline(tmp_path: Path) -> None:
    executable, _ = _write_operational_fixture(tmp_path / "operational")
    paths = operational_paths(tmp_path / "operational")
    migration = json.loads(paths.migration_receipt_path.read_text(encoding="utf-8"))
    migration["output_db_sha256"] = "0" * 64
    paths.migration_receipt_path.write_text(json.dumps(migration), encoding="utf-8")
    acceptance = json.loads(paths.acceptance_path.read_text(encoding="utf-8"))
    acceptance["migration_receipt_sha256"] = _sha256(paths.migration_receipt_path)
    paths.acceptance_path.write_text(json.dumps(acceptance), encoding="utf-8")
    with pytest.raises(OperationalReleaseError, match="OPERATIONAL_DATABASE_BASELINE_MISMATCH"):
        validate_operational_acceptance(executable)


def test_operational_acceptance_rejects_tampered_acceptance_baseline(tmp_path: Path) -> None:
    executable, _ = _write_operational_fixture(tmp_path / "operational")
    paths = operational_paths(tmp_path / "operational")
    acceptance = json.loads(paths.acceptance_path.read_text(encoding="utf-8"))
    acceptance["database_sha256"] = "0" * 64
    paths.acceptance_path.write_text(json.dumps(acceptance), encoding="utf-8")
    with pytest.raises(OperationalReleaseError, match="OPERATIONAL_DATABASE_BASELINE_MISMATCH"):
        validate_operational_acceptance(executable)


def _live_promotion_inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    source_sha: str = VERIFIED_MAIN_SHA,
) -> tuple[Path, Path, Path, str]:
    source_bundle = tmp_path / "candidate" / "app" / "QI-Crawler"
    source_bundle.mkdir(parents=True)
    _write_metadata(source_bundle, source_sha=source_sha, source_branch="main")
    source_data = tmp_path / "appdata" / "QI-Crawler"
    _create_database_at_0020(source_data / "data" / "database" / "egp.db", source_data)
    (source_data / "config.yaml").write_text("storage: {}\n", encoding="utf-8")
    destination = tmp_path / "live"
    destination.mkdir()
    (destination / "old.txt").write_text("old", encoding="utf-8")
    rollback_parent = tmp_path / "rollback"
    monkeypatch.setattr(operational_release, "OPERATIONAL_ROOT", destination)
    monkeypatch.setattr(operational_release, "LIVE_SOURCE_DATA_ROOT", source_data)
    monkeypatch.setattr(operational_release, "LIVE_ROLLBACK_ROOT_PARENT", rollback_parent)
    monkeypatch.setattr(operational_release, "LIVE_OPERATIONAL_VOLUME", destination.drive)
    monkeypatch.setattr(operational_release, "LIVE_SOURCE_VOLUME", source_data.drive)
    monkeypatch.setattr(
        operational_release,
        "_active_qi_crawler_processes",
        lambda: {
            "method": "CIM",
            "processes": [],
            "path_authority": "NOT_APPLICABLE",
        },
    )
    monkeypatch.setattr(
        operational_release,
        "_disk_usage",
        lambda path: SimpleNamespace(free=16 * 1024**3),
    )
    monkeypatch.setattr(
        operational_release,
        "_verified_main_checkout_head",
        lambda root: source_sha,
    )
    return source_bundle, source_data, destination, source_sha


def test_live_promotion_rejects_premerge_sha_against_verified_main_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle, _, _, _ = _live_promotion_inputs(
        tmp_path,
        monkeypatch,
        source_sha=OLD_PREMERGE_SHA,
    )
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    monkeypatch.setattr(
        operational_release,
        "_verified_main_checkout_head",
        lambda root: VERIFIED_MAIN_SHA,
        raising=False,
    )

    with pytest.raises(OperationalReleaseError, match="OPERATIONAL_SOURCE_SHA_MISMATCH"):
        promote_live_operational_root(bundle, source_checkout_root=checkout)


def test_live_source_checkout_rejects_non_main_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    responses = {
        ("rev-parse", "--show-toplevel"): str(checkout),
        ("rev-parse", "HEAD"): VERIFIED_MAIN_SHA,
        ("branch", "--show-current"): "feature/not-main",
        ("status", "--porcelain", "--untracked-files=no"): "",
    }
    monkeypatch.setattr(
        operational_release,
        "_git_output",
        lambda root, *args: responses[args],
        raising=False,
    )

    with pytest.raises(OperationalReleaseError, match="LIVE_SOURCE_BRANCH_MISMATCH"):
        operational_release._verified_main_checkout_head(checkout)


def test_live_source_checkout_rejects_dirty_tracked_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    responses = {
        ("rev-parse", "--show-toplevel"): str(checkout),
        ("rev-parse", "HEAD"): VERIFIED_MAIN_SHA,
        ("branch", "--show-current"): "main",
        ("status", "--porcelain", "--untracked-files=no"): " M src/qi_crawler/example.py",
    }
    monkeypatch.setattr(
        operational_release,
        "_git_output",
        lambda root, *args: responses[args],
        raising=False,
    )

    with pytest.raises(OperationalReleaseError, match="LIVE_SOURCE_TREE_DIRTY"):
        operational_release._verified_main_checkout_head(checkout)


def test_live_source_checkout_rejects_head_change_during_verification(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    heads = iter((VERIFIED_MAIN_SHA, "c" * 40))

    def git_output(root: Path, *args: str) -> str:
        if args == ("rev-parse", "--show-toplevel"):
            return str(checkout)
        if args == ("rev-parse", "HEAD"):
            return next(heads)
        if args == ("branch", "--show-current"):
            return "main"
        if args == ("status", "--porcelain", "--untracked-files=no"):
            return ""
        raise AssertionError(args)

    monkeypatch.setattr(operational_release, "_git_output", git_output, raising=False)

    with pytest.raises(OperationalReleaseError, match="LIVE_SOURCE_HEAD_CHANGED"):
        operational_release._verified_main_checkout_head(checkout)


def test_live_promotion_cli_binds_checkout_root(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: dict[str, object] = {}

    def fake_promote(bundle_root: Path, **kwargs: object) -> dict[str, str]:
        observed.update(kwargs)
        return {"status": "PREFLIGHT_PASS"}

    monkeypatch.setattr(promotion_cli, "promote_live_operational_root", fake_promote)

    assert promotion_cli.main(["--bundle-root", "bundle"]) == 0
    assert observed["source_checkout_root"] == promotion_cli.ROOT


def test_live_promotion_source_has_no_hardcoded_release_sha() -> None:
    source = Path(operational_release.__file__).read_text(encoding="utf-8")
    assert "LIVE_SOURCE_GIT_SHA" not in source


def test_live_promotion_without_execute_flag_is_zero_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle, source_data, destination, _ = _live_promotion_inputs(tmp_path, monkeypatch)
    before_source = operational_release._tree_snapshot(source_data)
    before_destination = sorted(path.relative_to(destination).as_posix() for path in destination.rglob("*"))
    result = promote_live_operational_root(bundle, source_checkout_root=tmp_path)
    assert result["status"] == "PREFLIGHT_PASS"
    assert result["process_census_method"] == "CIM"
    assert result["process_count"] == 0
    assert result["path_authority"] == "NOT_APPLICABLE"
    assert operational_release._tree_snapshot(source_data) == before_source
    assert sorted(path.relative_to(destination).as_posix() for path in destination.rglob("*")) == before_destination
    assert not (tmp_path / "rollback").exists()


def test_live_promotion_rejects_wrong_operational_root_before_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle, _, _, source_sha = _live_promotion_inputs(tmp_path, monkeypatch)
    with pytest.raises(OperationalReleaseError, match="LIVE_OPERATIONAL_ROOT_MISMATCH"):
        operational_release._live_preflight(
            bundle,
            source_git_sha=source_sha,
            expected_version=operational_release.LIVE_VERSION,
            execute=False,
            operational_root=tmp_path / "wrong-live",
        )


def test_live_promotion_rejects_wrong_source_root_before_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle, _, _, source_sha = _live_promotion_inputs(tmp_path, monkeypatch)
    with pytest.raises(OperationalReleaseError, match="LIVE_SOURCE_ROOT_MISMATCH"):
        operational_release._live_preflight(
            bundle,
            source_git_sha=source_sha,
            expected_version=operational_release.LIVE_VERSION,
            execute=False,
            source_data_root=tmp_path / "wrong-source",
        )


def test_live_promotion_rejects_wrong_source_sha(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bundle, _, _, _ = _live_promotion_inputs(tmp_path, monkeypatch)
    monkeypatch.setattr(
        operational_release,
        "_verified_main_checkout_head",
        lambda root: "c" * 40,
    )
    with pytest.raises(OperationalReleaseError, match="OPERATIONAL_SOURCE_SHA_MISMATCH"):
        promote_live_operational_root(bundle, source_checkout_root=tmp_path)


def test_live_promotion_rejects_internal_candidate_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle, _, _, _ = _live_promotion_inputs(tmp_path, monkeypatch)
    manifest = json.loads((bundle / "release_manifest.json").read_text(encoding="utf-8"))
    manifest["release_channel"] = "INTERNAL_CANDIDATE"
    (bundle / "release_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    (bundle / "BUILD_INFO.txt").write_text(
        "\n".join(f"{key}={value}" for key, value in manifest.items()) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(OperationalReleaseError, match="OPERATIONAL_RELEASE_CHANNEL_INVALID"):
        promote_live_operational_root(bundle, source_checkout_root=tmp_path)


def test_live_promotion_rejects_executable_hash_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle, _, _, _ = _live_promotion_inputs(tmp_path, monkeypatch)
    (bundle / "QI-Crawler.exe").write_bytes(b"tampered")

    with pytest.raises(OperationalReleaseError, match="OPERATIONAL_EXECUTABLE_SHA_MISMATCH"):
        promote_live_operational_root(bundle, source_checkout_root=tmp_path)


def test_live_promotion_rejects_unexpected_source_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle, source_data, _, _ = _live_promotion_inputs(tmp_path, monkeypatch)
    connection = sqlite3.connect(source_data / "data" / "database" / "egp.db")
    try:
        connection.execute("UPDATE alembic_version SET version_num = ?", (CURRENT_SCHEMA_REVISION,))
        connection.commit()
    finally:
        connection.close()
    with pytest.raises(OperationalReleaseError, match="PROMOTION_SOURCE_SCHEMA_UNEXPECTED"):
        promote_live_operational_root(bundle, source_checkout_root=tmp_path)


def test_live_promotion_rejects_insufficient_storage_reserve(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle, _, _, _ = _live_promotion_inputs(tmp_path, monkeypatch)
    monkeypatch.setattr(operational_release, "_disk_usage", lambda path: SimpleNamespace(free=1))
    with pytest.raises(OperationalReleaseError, match="LIVE_STORAGE_RESERVE_UNAVAILABLE"):
        promote_live_operational_root(bundle, source_checkout_root=tmp_path)


def test_live_promotion_rejects_rollback_collision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle, _, _, _ = _live_promotion_inputs(tmp_path, monkeypatch)
    fixed = datetime(2026, 9, 22, tzinfo=UTC)
    monkeypatch.setattr(operational_release, "_utc_now", lambda: fixed)
    rollback = tmp_path / "rollback" / "v0.9-20260922T000000Z"
    rollback.mkdir(parents=True)
    with pytest.raises(OperationalReleaseError, match="LIVE_ROLLBACK_ROOT_EXISTS"):
        promote_live_operational_root(bundle, source_checkout_root=tmp_path)


def test_live_promotion_rejects_active_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle, _, _, _ = _live_promotion_inputs(tmp_path, monkeypatch)
    monkeypatch.setattr(
        operational_release,
        "_active_qi_crawler_processes",
        lambda: {
            "method": "CIM",
            "processes": [
                {
                    "ProcessId": "42",
                    "ExecutablePath": str(
                        operational_release.OPERATIONAL_ROOT
                        / "Current"
                        / "QI-Crawler"
                        / "QI-Crawler.exe"
                    ),
                }
            ],
            "path_authority": "EXACT",
        },
    )
    with pytest.raises(OperationalReleaseError, match="LIVE_ACTIVE_PROCESS_PRESENT"):
        promote_live_operational_root(bundle, source_checkout_root=tmp_path)


def test_windows_process_census_prefers_successful_cim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(operational_release, "_cim_process_census", list, raising=False)
    monkeypatch.setattr(
        operational_release,
        "_tasklist_process_census",
        lambda: pytest.fail("fallback must not run after successful CIM"),
        raising=False,
    )

    assert operational_release._windows_process_census() == {
        "method": "CIM",
        "processes": [],
        "path_authority": "NOT_APPLICABLE",
    }


def test_windows_process_census_uses_tasklist_after_cim_denied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def denied() -> list[dict[str, str | None]]:
        raise OperationalReleaseError("LIVE_PROCESS_CENSUS_FAILED")

    monkeypatch.setattr(operational_release, "_cim_process_census", denied, raising=False)
    monkeypatch.setattr(operational_release, "_tasklist_process_census", list, raising=False)

    assert operational_release._windows_process_census() == {
        "method": "TASKLIST_FALLBACK",
        "processes": [],
        "path_authority": "NOT_APPLICABLE",
    }


def test_live_promotion_blocks_tasklist_match_with_unknown_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle, _, _, _ = _live_promotion_inputs(tmp_path, monkeypatch)
    monkeypatch.setattr(
        operational_release,
        "_active_qi_crawler_processes",
        lambda: {
            "method": "TASKLIST_FALLBACK",
            "processes": [
                {
                    "ImageName": "QI-Crawler.exe",
                    "ProcessId": "42",
                    "ExecutablePath": None,
                }
            ],
            "path_authority": "UNKNOWN",
        },
    )

    with pytest.raises(OperationalReleaseError, match="LIVE_ACTIVE_PROCESS_PRESENT"):
        promote_live_operational_root(bundle, source_checkout_root=tmp_path)


def test_live_promotion_allows_cim_process_outside_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle, _, _, _ = _live_promotion_inputs(tmp_path, monkeypatch)
    monkeypatch.setattr(
        operational_release,
        "_active_qi_crawler_processes",
        lambda: {
            "method": "CIM",
            "processes": [
                {
                    "ProcessId": "42",
                    "ExecutablePath": str(tmp_path / "other" / "QI-Crawler.exe"),
                }
            ],
            "path_authority": "EXACT",
        },
    )

    result = promote_live_operational_root(bundle, source_checkout_root=tmp_path)

    assert result["status"] == "PREFLIGHT_PASS"
    assert result["process_census_method"] == "CIM"
    assert result["process_count"] == 1
    assert result["path_authority"] == "EXACT"


def test_windows_process_census_fails_when_both_methods_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def failed() -> list[dict[str, str | None]]:
        raise OperationalReleaseError("LIVE_PROCESS_CENSUS_FAILED")

    monkeypatch.setattr(operational_release, "_cim_process_census", failed, raising=False)
    monkeypatch.setattr(operational_release, "_tasklist_process_census", failed, raising=False)

    with pytest.raises(OperationalReleaseError, match="LIVE_PROCESS_CENSUS_FAILED"):
        operational_release._windows_process_census()


def test_tasklist_census_rejects_malformed_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(operational_release, "_windows_system_executable", lambda name: name)
    monkeypatch.setattr(
        operational_release.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(stdout="malformed tasklist output"),
    )

    with pytest.raises(OperationalReleaseError, match="LIVE_PROCESS_CENSUS_FAILED"):
        operational_release._tasklist_process_census()


def test_tasklist_census_ignores_unrelated_exact_image_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(operational_release, "_windows_system_executable", lambda name: name)
    monkeypatch.setattr(
        operational_release.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            stdout='"not-QI-Crawler.exe","42","Console","1","1,024 K"\n'
        ),
    )

    assert operational_release._tasklist_process_census() == []


def test_tasklist_census_recognizes_exact_qi_crawler_image(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(operational_release, "_windows_system_executable", lambda name: name)
    monkeypatch.setattr(
        operational_release.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            stdout='"QI-Crawler.exe","42","Console","1","1,024 K"\n'
        ),
    )

    assert operational_release._tasklist_process_census() == [
        {
            "ImageName": "QI-Crawler.exe",
            "ProcessId": "42",
            "ExecutablePath": None,
        }
    ]


def test_tasklist_census_uses_non_elevated_argument_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(operational_release, "_windows_system_executable", lambda name: name)
    observed: dict[str, object] = {}

    def run(args: list[str], **kwargs: object) -> SimpleNamespace:
        observed["args"] = args
        observed.update(kwargs)
        return SimpleNamespace(stdout="INFO: No tasks are running which match the specified criteria.\n")

    monkeypatch.setattr(operational_release.subprocess, "run", run)

    assert operational_release._tasklist_process_census() == []
    assert observed["args"] == [
        "tasklist.exe",
        "/FI",
        "IMAGENAME eq QI-Crawler.exe",
        "/FO",
        "CSV",
        "/NH",
    ]
    assert "shell" not in observed
    assert "runas" not in " ".join(observed["args"]).casefold()


def test_windows_system_executable_is_bound_to_system32(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    system_root = tmp_path / "Windows"
    executable = system_root / "System32" / "tasklist.exe"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"system tasklist")
    monkeypatch.setenv("SystemRoot", str(system_root))

    assert operational_release._windows_system_executable("tasklist.exe") == str(
        executable.resolve()
    )


def test_live_promotion_staging_failure_preserves_old_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle, _, destination, _ = _live_promotion_inputs(tmp_path, monkeypatch)
    with pytest.raises(OperationalReleaseError, match="PROMOTION_FAILED_BEFORE_CUTOVER"):
        promote_live_operational_root(
            bundle,
            source_checkout_root=tmp_path,
            execute=True,
            fail_stage="before_cutover",
        )
    assert (destination / "old.txt").read_text(encoding="utf-8") == "old"
    assert not (destination / "Current").exists()


def test_live_promotion_after_rotation_restores_rollback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle, _, destination, _ = _live_promotion_inputs(tmp_path, monkeypatch)
    with pytest.raises(OperationalReleaseError, match="PROMOTION_FAILED_AFTER_ROTATION"):
        promote_live_operational_root(
            bundle,
            source_checkout_root=tmp_path,
            execute=True,
            fail_stage="after_rotation",
        )
    assert (destination / "old.txt").read_text(encoding="utf-8") == "old"
    assert not (destination / "control").exists()


def test_live_promotion_final_validation_failure_restores_rollback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle, _, destination, _ = _live_promotion_inputs(tmp_path, monkeypatch)
    original = operational_release.validate_operational_acceptance
    calls = 0

    def fail_final(executable: Path, *, expected_version: str = operational_release.__version__) -> dict[str, object]:
        nonlocal calls
        calls += 1
        if calls >= 2:
            raise OperationalReleaseError("FINAL_VALIDATION_FORCED")
        return original(executable, expected_version=expected_version)

    monkeypatch.setattr(operational_release, "validate_operational_acceptance", fail_final)
    with pytest.raises(OperationalReleaseError, match="FINAL_VALIDATION_FORCED"):
        promote_live_operational_root(
            bundle,
            source_checkout_root=tmp_path,
            execute=True,
        )
    assert (destination / "old.txt").read_text(encoding="utf-8") == "old"
    assert not (destination / "control").exists()


def test_live_promotion_success_is_coherent_and_preserves_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle, source_data, destination, _ = _live_promotion_inputs(tmp_path, monkeypatch)
    before_bundle = operational_release._tree_snapshot(bundle)
    before_data = operational_release._tree_snapshot(source_data)
    result = promote_live_operational_root(
        bundle,
        source_checkout_root=tmp_path,
        execute=True,
    )
    assert result["status"] == "PROMOTED_LIVE"
    assert validate_operational_acceptance(operational_paths(destination).executable)["operational_root"] == str(destination.resolve())
    assert Path(result["rollback_root"]).is_dir()
    assert operational_release._tree_snapshot(bundle) == before_bundle
    assert operational_release._tree_snapshot(source_data) == before_data
