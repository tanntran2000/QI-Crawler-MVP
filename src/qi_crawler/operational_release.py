"""Fail-closed binding and synthetic promotion for the operational bundle."""

from __future__ import annotations

import gc
import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
import time
from collections.abc import MutableMapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml
from sqlalchemy.engine import make_url

from . import __version__
from .db import CURRENT_SCHEMA_REVISION
from .migrations import upgrade_database

OPERATIONAL_RELEASE_CHANNEL = "INTERNAL_PILOT"
OPERATIONAL_ACCEPTANCE_SCHEMA_VERSION = "qi-crawler-operational-acceptance-v1"
OPERATIONAL_MIGRATION_RECEIPT_SCHEMA_VERSION = "qi-crawler-operational-migration-v1"
OPERATIONAL_ACCEPTANCE_NAME = "operational_acceptance.json"
OPERATIONAL_MIGRATION_RECEIPT_NAME = "operational_migration_receipt.json"
SOURCE_SCHEMA_REVISION = "0020_add_tender_operational_revision_events"
OPERATIONAL_ROOT = Path(r"D:\QI-Crawler")
_SHA40 = set("0123456789abcdefABCDEF")
_SHA64 = set("0123456789abcdefABCDEF")


class OperationalReleaseError(RuntimeError):
    """An operational release or promotion invariant failed closed."""


@dataclass(frozen=True, slots=True)
class OperationalPaths:
    root: Path
    application_root: Path
    executable: Path
    runtime_root: Path
    build_info_path: Path
    release_manifest_path: Path
    data_root: Path
    config_path: Path
    data_dir: Path
    database_path: Path
    logs_root: Path
    control_root: Path
    acceptance_path: Path
    migration_receipt_path: Path

    @property
    def data_directories(self) -> tuple[Path, ...]:
        return (
            self.data_dir / "database",
            self.data_dir / "documents",
            self.data_dir / "downloads",
            self.data_dir / "discovery",
            self.data_dir / "raw",
            self.data_dir / "rejects",
            self.data_dir / "reports",
            self.data_dir / "sessions",
            self.data_dir / "backups",
            self.logs_root,
        )


def operational_paths(root: Path | str) -> OperationalPaths:
    stable_root = Path(root).expanduser().resolve(strict=False)
    application = stable_root / "Current" / "QI-Crawler"
    data_root = stable_root / "Data"
    data_dir = data_root / "data"
    control = stable_root / "control"
    return OperationalPaths(
        root=stable_root,
        application_root=application,
        executable=application / "QI-Crawler.exe",
        runtime_root=application / "runtime",
        build_info_path=application / "BUILD_INFO.txt",
        release_manifest_path=application / "release_manifest.json",
        data_root=data_root,
        config_path=data_root / "config.yaml",
        data_dir=data_dir,
        database_path=data_dir / "database" / "egp.db",
        logs_root=data_root / "logs",
        control_root=control,
        acceptance_path=control / OPERATIONAL_ACCEPTANCE_NAME,
        migration_receipt_path=control / OPERATIONAL_MIGRATION_RECEIPT_NAME,
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _read_json(path: Path, error: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OperationalReleaseError(error) from exc
    if not isinstance(value, dict):
        raise OperationalReleaseError(error)
    return value


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _parse_build_info(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise OperationalReleaseError("OPERATIONAL_BUILD_INFO_INVALID") from exc
    fields: dict[str, str] = {}
    for line in lines:
        if not line or "=" not in line:
            raise OperationalReleaseError("OPERATIONAL_BUILD_INFO_INVALID")
        key, value = line.split("=", 1)
        if not key or not value or key in fields:
            raise OperationalReleaseError("OPERATIONAL_BUILD_INFO_INVALID")
        fields[key] = value
    return fields


def _schema_revision(database: Path) -> str:
    if not database.is_file():
        raise OperationalReleaseError("OPERATIONAL_DATABASE_REQUIRED")
    try:
        uri = database.as_uri() + "?mode=ro"
        with sqlite3.connect(uri, uri=True) as connection:
            connection.execute("PRAGMA query_only = ON")
            row = connection.execute("SELECT version_num FROM alembic_version").fetchone()
    except sqlite3.Error as exc:
        raise OperationalReleaseError("OPERATIONAL_DATABASE_INVALID") from exc
    if row is None or not row[0]:
        raise OperationalReleaseError("OPERATIONAL_SCHEMA_NOT_VERIFIED")
    return str(row[0])


def _path_is_inside(path: Path, root: Path) -> bool:
    return path == root or path.is_relative_to(root)


def _bundle_identity(bundle: Path, *, expected_source_sha: str | None = None) -> dict[str, Any]:
    executable = bundle / "QI-Crawler.exe"
    manifest_path = bundle / "release_manifest.json"
    build_info_path = bundle / "BUILD_INFO.txt"
    if not executable.is_file() or not manifest_path.is_file() or not build_info_path.is_file():
        raise OperationalReleaseError("OPERATIONAL_RELEASE_METADATA_REQUIRED")
    manifest = _read_json(manifest_path, "OPERATIONAL_RELEASE_MANIFEST_INVALID")
    required = {
        "metadata_schema_version",
        "product",
        "version",
        "source_git_sha",
        "source_branch",
        "build_timestamp_utc",
        "alembic_head",
        "release_channel",
        "portable_exe_sha256",
    }
    if set(manifest) != required:
        raise OperationalReleaseError("OPERATIONAL_RELEASE_MANIFEST_FIELDS_INVALID")
    if manifest.get("metadata_schema_version") != "qi-crawler-installed-release-v1":
        raise OperationalReleaseError("OPERATIONAL_RELEASE_MANIFEST_SCHEMA_UNSUPPORTED")
    if manifest.get("product") != "QI-Crawler":
        raise OperationalReleaseError("OPERATIONAL_RELEASE_PRODUCT_INVALID")
    if manifest.get("release_channel") != OPERATIONAL_RELEASE_CHANNEL:
        raise OperationalReleaseError("OPERATIONAL_RELEASE_CHANNEL_INVALID")
    source_sha = str(manifest.get("source_git_sha", ""))
    if len(source_sha) != 40 or set(source_sha) - _SHA40:
        raise OperationalReleaseError("OPERATIONAL_SOURCE_SHA_INVALID")
    if expected_source_sha is not None and source_sha.lower() != expected_source_sha.lower():
        raise OperationalReleaseError("OPERATIONAL_SOURCE_SHA_MISMATCH")
    if manifest.get("alembic_head") != CURRENT_SCHEMA_REVISION:
        raise OperationalReleaseError("OPERATIONAL_BUILD_SCHEMA_MISMATCH")
    expected_executable_sha = str(manifest.get("portable_exe_sha256", ""))
    if len(expected_executable_sha) != 64 or set(expected_executable_sha) - _SHA64:
        raise OperationalReleaseError("OPERATIONAL_EXECUTABLE_SHA_INVALID")
    if _sha256(executable) != expected_executable_sha.upper():
        raise OperationalReleaseError("OPERATIONAL_EXECUTABLE_SHA_MISMATCH")
    build_info = _parse_build_info(build_info_path)
    if build_info != {key: str(value) for key, value in manifest.items()}:
        raise OperationalReleaseError("OPERATIONAL_BUILD_INFO_MANIFEST_MISMATCH")
    return {
        **manifest,
        "bundle_root": str(bundle.resolve(strict=True)),
        "executable": str(executable.resolve(strict=True)),
        "portable_exe_sha256": expected_executable_sha.lower(),
        "release_manifest_sha256": _sha256(manifest_path).lower(),
        "build_info_sha256": _sha256(build_info_path).lower(),
    }


def validate_operational_acceptance(
    executable: Path | str,
    *,
    expected_version: str = __version__,
) -> dict[str, Any]:
    """Validate the separate operational receipt before config or DB creation."""
    try:
        actual_executable = Path(executable).expanduser().resolve(strict=True)
    except OSError as exc:
        raise OperationalReleaseError("OPERATIONAL_LAYOUT_INVALID") from exc
    if (
        actual_executable.name != "QI-Crawler.exe"
        or actual_executable.parent.name != "QI-Crawler"
        or actual_executable.parent.parent.name != "Current"
    ):
        raise OperationalReleaseError("OPERATIONAL_LAYOUT_INVALID")
    root = actual_executable.parent.parent.parent.resolve(strict=False)
    paths = operational_paths(root)
    if actual_executable != paths.executable:
        raise OperationalReleaseError("OPERATIONAL_LAYOUT_INVALID")
    if not paths.runtime_root.is_dir():
        raise OperationalReleaseError("OPERATIONAL_RUNTIME_REQUIRED")
    bundle = _bundle_identity(paths.application_root)
    if bundle["version"] != expected_version:
        raise OperationalReleaseError("OPERATIONAL_VERSION_MISMATCH")
    if not paths.acceptance_path.is_file():
        raise OperationalReleaseError("OPERATIONAL_ACCEPTANCE_REQUIRED")
    receipt = _read_json(paths.acceptance_path, "OPERATIONAL_ACCEPTANCE_INVALID")
    required = {
        "acceptance_schema_version",
        "status",
        "operational_root",
        "application_root",
        "executable",
        "data_root",
        "config_path",
        "database_path",
        "product",
        "version",
        "source_git_sha",
        "source_branch",
        "build_timestamp_utc",
        "release_channel",
        "portable_exe_sha256",
        "release_manifest_sha256",
        "build_info_sha256",
        "schema_revision",
        "migration_receipt_sha256",
        "migration_source_sha",
        "migration_from_revision",
        "migration_to_revision",
        "database_sha256",
        "created_at",
    }
    if set(receipt) != required:
        raise OperationalReleaseError("OPERATIONAL_ACCEPTANCE_FIELDS_INVALID")
    if (
        receipt["acceptance_schema_version"] != OPERATIONAL_ACCEPTANCE_SCHEMA_VERSION
        or receipt["status"] != "ACCEPTED"
    ):
        raise OperationalReleaseError("OPERATIONAL_ACCEPTANCE_INVALID")
    expected_paths = {
        "operational_root": paths.root,
        "application_root": paths.application_root,
        "executable": paths.executable,
        "data_root": paths.data_root,
        "config_path": paths.config_path,
        "database_path": paths.database_path,
    }
    for field, expected in expected_paths.items():
        if Path(str(receipt[field])).resolve(strict=False) != expected.resolve(strict=False):
            if field == "operational_root":
                error = "OPERATIONAL_ROOT_MISMATCH"
            elif field == "database_path":
                error = "OPERATIONAL_DATABASE_PATH_INVALID"
            else:
                error = "OPERATIONAL_PATH_MISMATCH"
            raise OperationalReleaseError(error)
    if not _path_is_inside(paths.application_root, paths.root) or not _path_is_inside(
        paths.data_root, paths.root
    ) or _path_is_inside(paths.data_root, paths.application_root):
        raise OperationalReleaseError("OPERATIONAL_LAYOUT_INVALID")
    if not _path_is_inside(paths.database_path, paths.data_root):
        raise OperationalReleaseError("OPERATIONAL_DATABASE_PATH_INVALID")
    if not paths.control_root.is_dir() or any(
        not directory.is_dir() for directory in paths.data_directories
    ):
        raise OperationalReleaseError("OPERATIONAL_LAYOUT_INVALID")
    for key in (
        "product",
        "version",
        "source_git_sha",
        "source_branch",
        "build_timestamp_utc",
        "release_channel",
        "portable_exe_sha256",
        "release_manifest_sha256",
        "build_info_sha256",
    ):
        left = str(receipt[key])
        right = str(bundle[key])
        if key.endswith("sha256") or key == "portable_exe_sha256":
            left, right = left.lower(), right.lower()
        if left != right:
            raise OperationalReleaseError("OPERATIONAL_BUILD_IDENTITY_MISMATCH")
    if receipt["release_channel"] != OPERATIONAL_RELEASE_CHANNEL:
        raise OperationalReleaseError("OPERATIONAL_RELEASE_CHANNEL_INVALID")
    if receipt["schema_revision"] != CURRENT_SCHEMA_REVISION:
        raise OperationalReleaseError("OPERATIONAL_SCHEMA_MISMATCH")
    if receipt["migration_to_revision"] != CURRENT_SCHEMA_REVISION:
        raise OperationalReleaseError("OPERATIONAL_MIGRATION_MISMATCH")
    if receipt["migration_from_revision"] != SOURCE_SCHEMA_REVISION:
        raise OperationalReleaseError("OPERATIONAL_MIGRATION_MISMATCH")
    if str(receipt["migration_source_sha"]).lower() != str(receipt["source_git_sha"]).lower():
        raise OperationalReleaseError("OPERATIONAL_MIGRATION_PROVENANCE_MISMATCH")
    if _sha256(paths.release_manifest_path).lower() != str(receipt["release_manifest_sha256"]).lower():
        raise OperationalReleaseError("OPERATIONAL_MANIFEST_SHA_MISMATCH")
    if _sha256(paths.build_info_path).lower() != str(receipt["build_info_sha256"]).lower():
        raise OperationalReleaseError("OPERATIONAL_BUILD_INFO_SHA_MISMATCH")
    migration = _read_json(paths.migration_receipt_path, "OPERATIONAL_MIGRATION_RECEIPT_INVALID")
    if (
        migration.get("receipt_schema_version") != OPERATIONAL_MIGRATION_RECEIPT_SCHEMA_VERSION
        or migration.get("status") != "PASS"
        or migration.get("source_git_sha") != receipt["migration_source_sha"]
        or migration.get("from_revision") != receipt["migration_from_revision"]
        or migration.get("to_revision") != receipt["migration_to_revision"]
    ):
        raise OperationalReleaseError("OPERATIONAL_MIGRATION_PROVENANCE_MISMATCH")
    if _sha256(paths.migration_receipt_path).lower() != str(receipt["migration_receipt_sha256"]).lower():
        raise OperationalReleaseError("OPERATIONAL_MIGRATION_RECEIPT_SHA_MISMATCH")
    if not paths.config_path.is_file():
        raise OperationalReleaseError("OPERATIONAL_CONFIG_REQUIRED")
    if _schema_revision(paths.database_path) != CURRENT_SCHEMA_REVISION:
        raise OperationalReleaseError("OPERATIONAL_SCHEMA_MISMATCH")
    if _sha256(paths.database_path).lower() != str(receipt["database_sha256"]).lower():
        raise OperationalReleaseError("OPERATIONAL_DATABASE_SHA_MISMATCH")
    return receipt


def bind_operational_runtime_environment(
    executable: Path | str,
    environment: MutableMapping[str, str] | None = None,
) -> dict[str, Any]:
    receipt = validate_operational_acceptance(executable)
    target = os.environ if environment is None else environment
    target["QI_CRAWLER_DATA_DIR"] = str(Path(str(receipt["data_root"])).resolve(strict=False))
    target["QI_CRAWLER_CONFIG_PATH"] = str(Path(str(receipt["config_path"])).resolve(strict=False))
    target["QI_CRAWLER_DATABASE_URL"] = (
        f"sqlite:///{Path(str(receipt['database_path'])).resolve(strict=False).as_posix()}"
    )
    return receipt


def validate_operational_database_target(database_url: str, paths: OperationalPaths) -> Path:
    try:
        parsed = make_url(database_url)
        if (
            parsed.get_backend_name() != "sqlite"
            or not parsed.database
            or parsed.database == ":memory:"
            or parsed.username is not None
            or parsed.password is not None
            or parsed.host is not None
            or parsed.port is not None
            or parsed.query
        ):
            raise ValueError
        actual = Path(parsed.database).expanduser().resolve(strict=False)
    except Exception as exc:
        raise OperationalReleaseError("OPERATIONAL_DATABASE_PATH_INVALID") from exc
    expected = paths.database_path.resolve(strict=False)
    if actual != expected or not _path_is_inside(actual, paths.data_root.resolve(strict=False)):
        raise OperationalReleaseError("OPERATIONAL_DATABASE_PATH_INVALID")
    return actual


def _assert_synthetic_roots(*roots: Path) -> None:
    temp_root = Path(tempfile.gettempdir()).resolve(strict=False)
    repository_temp_root = Path(__file__).resolve().parents[2] / ".tmp"
    allowed = (temp_root, repository_temp_root.resolve(strict=False))
    protected = [Path(r"D:\QI-Crawler").resolve(strict=False)]
    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        protected.append((Path(local_app_data) / "QI-Crawler").resolve(strict=False))
    for root in roots:
        if not any(_path_is_inside(root, allowed_root) for allowed_root in allowed):
            raise OperationalReleaseError("SYNTHETIC_ROOT_REQUIRED")
        if any(_path_is_inside(root, item) or _path_is_inside(item, root) for item in protected):
            raise OperationalReleaseError("PROTECTED_OPERATIONAL_ROOT_FORBIDDEN")


def _consistent_sqlite_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with sqlite3.connect(source.as_uri() + "?mode=ro", uri=True) as source_connection:
            source_connection.execute("PRAGMA query_only = ON")
            with sqlite3.connect(destination) as destination_connection:
                source_connection.backup(destination_connection)
    except sqlite3.Error as exc:
        destination.unlink(missing_ok=True)
        raise OperationalReleaseError("SYNTHETIC_SOURCE_COPY_FAILED") from exc


def _atomic_directory_replace(source: Path, destination: Path) -> None:
    try:
        os.replace(source, destination)
    except PermissionError:
        # Windows scanners can briefly retain a just-written receipt handle.
        gc.collect()
        time.sleep(0.2)
        os.replace(source, destination)


def _rewrite_operational_config(config_path: Path, paths: OperationalPaths) -> None:
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raw = {}
    storage = raw.setdefault("storage", {})
    if not isinstance(storage, dict):
        raise OperationalReleaseError("OPERATIONAL_CONFIG_INVALID")
    storage.update(
        {
            "database_url": f"sqlite:///{paths.database_path.as_posix()}",
            "document_dir": str(paths.data_dir / "documents"),
            "download_dir": str(paths.data_dir / "downloads"),
            "discovery_dir": str(paths.data_dir / "discovery"),
            "raw_dir": str(paths.data_dir / "raw"),
            "rejects_dir": str(paths.data_dir / "rejects"),
            "report_dir": str(paths.data_dir / "reports"),
        }
    )
    config_path.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")


def _operational_acceptance_payload(
    paths: OperationalPaths,
    bundle: dict[str, Any],
    migration_receipt: dict[str, Any],
) -> dict[str, Any]:
    return {
        "acceptance_schema_version": OPERATIONAL_ACCEPTANCE_SCHEMA_VERSION,
        "status": "ACCEPTED",
        "operational_root": str(paths.root),
        "application_root": str(paths.application_root),
        "executable": str(paths.executable),
        "data_root": str(paths.data_root),
        "config_path": str(paths.config_path),
        "database_path": str(paths.database_path),
        "product": bundle["product"],
        "version": bundle["version"],
        "source_git_sha": bundle["source_git_sha"],
        "source_branch": bundle["source_branch"],
        "build_timestamp_utc": bundle["build_timestamp_utc"],
        "release_channel": OPERATIONAL_RELEASE_CHANNEL,
        "portable_exe_sha256": bundle["portable_exe_sha256"],
        "release_manifest_sha256": bundle["release_manifest_sha256"],
        "build_info_sha256": bundle["build_info_sha256"],
        "schema_revision": CURRENT_SCHEMA_REVISION,
        "migration_receipt_sha256": _sha256(paths.migration_receipt_path).lower(),
        "migration_source_sha": migration_receipt["source_git_sha"],
        "migration_from_revision": migration_receipt["from_revision"],
        "migration_to_revision": migration_receipt["to_revision"],
        "database_sha256": _sha256(paths.database_path).lower(),
        "created_at": datetime.now(UTC).isoformat(),
    }


def promote_synthetic_operational_root(
    source_bundle_root: Path | str,
    source_data_root: Path | str,
    operational_root: Path | str,
    *,
    source_git_sha: str,
    expected_version: str = __version__,
    fail_stage: str | None = None,
) -> dict[str, Any]:
    """Promote only temp fixtures with copy, migration, validation and rollback."""
    source_bundle = Path(source_bundle_root).expanduser().resolve(strict=True)
    source_data = Path(source_data_root).expanduser().resolve(strict=True)
    destination = Path(operational_root).expanduser().resolve(strict=False)
    _assert_synthetic_roots(source_bundle, source_data, destination)
    if fail_stage not in {None, "before_cutover", "after_rotation"}:
        raise OperationalReleaseError("PROMOTION_FAILURE_STAGE_INVALID")
    bundle = _bundle_identity(source_bundle, expected_source_sha=source_git_sha)
    if bundle["version"] != expected_version:
        raise OperationalReleaseError("OPERATIONAL_VERSION_MISMATCH")
    source_database = source_data / "data" / "database" / "egp.db"
    if _schema_revision(source_database) != SOURCE_SCHEMA_REVISION:
        raise OperationalReleaseError("PROMOTION_SOURCE_SCHEMA_UNEXPECTED")
    if destination.exists() and not destination.is_dir():
        raise OperationalReleaseError("PROMOTION_DESTINATION_INVALID")
    rollback_root = destination.parent / f"{destination.name}.rollback"
    if rollback_root.exists():
        raise OperationalReleaseError("PROMOTION_ROLLBACK_ROOT_EXISTS")
    stage = destination.parent / f".{destination.name}.stage-{uuid4().hex[:8]}"
    rotated = False
    try:
        stage_paths = operational_paths(stage)
        stage_paths.application_root.mkdir(parents=True)
        shutil.copytree(source_bundle, stage_paths.application_root, dirs_exist_ok=True)
        shutil.copytree(source_data, stage_paths.data_root, dirs_exist_ok=True)
        stage_paths.database_path.unlink(missing_ok=True)
        Path(f"{stage_paths.database_path}-wal").unlink(missing_ok=True)
        Path(f"{stage_paths.database_path}-shm").unlink(missing_ok=True)
        _consistent_sqlite_copy(source_database, stage_paths.database_path)
        _rewrite_operational_config(stage_paths.config_path, stage_paths)
        for directory in stage_paths.data_directories:
            directory.mkdir(parents=True, exist_ok=True)
        input_db_sha256 = _sha256(stage_paths.database_path).lower()
        migration_result = upgrade_database(
            f"sqlite:///{stage_paths.database_path.as_posix()}",
            backup_dir=stage_paths.data_dir / "backups",
        )
        migration = {
            "receipt_schema_version": OPERATIONAL_MIGRATION_RECEIPT_SCHEMA_VERSION,
            "status": "PASS",
            "source_git_sha": source_git_sha.lower(),
            "from_revision": SOURCE_SCHEMA_REVISION,
            "to_revision": migration_result.revision,
            "input_db_sha256": input_db_sha256,
            "output_db_sha256": _sha256(stage_paths.database_path).lower(),
            "created_at": datetime.now(UTC).isoformat(),
        }
        if migration_result.revision != CURRENT_SCHEMA_REVISION:
            raise OperationalReleaseError("PROMOTION_SCHEMA_MISMATCH")
        _write_json(stage_paths.migration_receipt_path, migration)
        _write_json(
            stage_paths.acceptance_path,
            _operational_acceptance_payload(stage_paths, bundle, migration),
        )
        validate_operational_acceptance(stage_paths.executable, expected_version=expected_version)
        if fail_stage == "before_cutover":
            raise OperationalReleaseError("PROMOTION_FAILED_BEFORE_CUTOVER")
        if destination.exists():
            _atomic_directory_replace(destination, rollback_root)
            rotated = True
        _atomic_directory_replace(stage, destination)
        if fail_stage == "after_rotation":
            raise OperationalReleaseError("PROMOTION_FAILED_AFTER_ROTATION")
        final_paths = operational_paths(destination)
        final_receipt = _read_json(final_paths.acceptance_path, "OPERATIONAL_ACCEPTANCE_INVALID")
        final_receipt.update(
            {
                "operational_root": str(final_paths.root),
                "application_root": str(final_paths.application_root),
                "executable": str(final_paths.executable),
                "data_root": str(final_paths.data_root),
                "config_path": str(final_paths.config_path),
                "database_path": str(final_paths.database_path),
            }
        )
        _write_json(final_paths.acceptance_path, final_receipt)
        validated = validate_operational_acceptance(final_paths.executable, expected_version=expected_version)
        return {
            "status": "PROMOTED_SYNTHETIC",
            "operational_root": str(final_paths.root),
            "rollback_root": str(rollback_root) if rollback_root.exists() else None,
            "acceptance": validated,
        }
    except Exception as exc:
        if rotated:
            shutil.rmtree(destination, ignore_errors=True)
            _atomic_directory_replace(rollback_root, destination)
        if isinstance(exc, OperationalReleaseError):
            raise
        raise OperationalReleaseError(f"PROMOTION_FAILED_BEFORE_CUTOVER: {exc}") from exc
    finally:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
