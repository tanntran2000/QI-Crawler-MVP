from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
from pathlib import Path

import pytest

from qi_crawler import operational_release, standalone
from qi_crawler.db import CURRENT_SCHEMA_REVISION
from qi_crawler.migrations import upgrade_database
from qi_crawler.operational_release import (
    OPERATIONAL_ACCEPTANCE_SCHEMA_VERSION,
    OPERATIONAL_MIGRATION_RECEIPT_SCHEMA_VERSION,
    OperationalReleaseError,
    operational_paths,
    promote_synthetic_operational_root,
    validate_operational_acceptance,
)

SOURCE_SHA = "a" * 40
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


def _write_metadata(bundle: Path, *, channel: str = "INTERNAL_PILOT") -> dict[str, str]:
    executable = bundle / "QI-Crawler.exe"
    executable.write_bytes(b"synthetic-operational-executable")
    portable_hash = _sha256(executable)
    manifest = {
        "metadata_schema_version": "qi-crawler-installed-release-v1",
        "product": "QI-Crawler",
        "version": "0.10.0",
        "source_git_sha": SOURCE_SHA,
        "source_branch": "release/v0.10-b09-operational-rebind-01",
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
    paths.config_path.write_text("storage:\n  database_url: sqlite:///placeholder.db\n", encoding="utf-8")
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
    assert validate_operational_acceptance(paths.executable)["operational_root"] == str(destination.resolve())
