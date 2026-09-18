from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml


class CandidateDataError(RuntimeError):
    """Fail-closed candidate-data preparation error."""


@dataclass(frozen=True, slots=True)
class _DocumentRecord:
    document_id: int
    stored_path: Path
    sha256: str


_REPARSE_POINT = 0x400
_RECEIPT_NAME = "candidate_data_receipt.json"
CLONE_RECEIPT_SCHEMA_VERSION = "qi-crawler-candidate-clone-v1"
MAX_BACKUP_SECONDS = 30.0
_BACKUP_PAGES = 128
_SQLITE_BUSY_TIMEOUT_MS = 1_000
_monotonic = time.monotonic


def _capture_hook(_phase: str) -> None:
    """Stable no-op phase seam for deterministic capture-race regressions."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_receipt(destination: Path, payload: dict[str, Any]) -> None:
    target = destination / _RECEIPT_NAME
    temporary = destination / f"{_RECEIPT_NAME}.tmp"
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)


def _is_reparse_or_symlink(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except OSError:
        return False
    return bool(attributes & _REPARSE_POINT)


def _guard_no_reparse(path: Path) -> None:
    current = path.absolute()
    while True:
        if current.exists() and _is_reparse_or_symlink(current):
            raise CandidateDataError(f"REPARSE_OR_SYMLINK: {current}")
        if current.parent == current:
            return
        current = current.parent


def _guard_roots(source: Path, destination: Path) -> tuple[Path, Path]:
    _guard_no_reparse(source)
    _guard_no_reparse(destination)
    source_resolved = source.resolve(strict=True)
    destination_resolved = destination.resolve(strict=False)
    if (
        source_resolved == destination_resolved
        or destination_resolved.is_relative_to(source_resolved)
        or source_resolved.is_relative_to(destination_resolved)
    ):
        raise CandidateDataError("PATH_OVERLAP: source and destination must be disjoint")
    if destination.exists() and any(destination.iterdir()):
        raise CandidateDataError("DESTINATION_NOT_EMPTY: destination must be absent or empty")
    return source_resolved, destination_resolved


def _sqlite_path(database_url: str) -> Path:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise CandidateDataError("SOURCE_DATABASE_NOT_SQLITE")
    return Path(database_url[len(prefix) :]).expanduser().resolve(strict=True)


def _resolve_source_document_root(
    source_root: Path,
    storage: dict[str, Any],
) -> tuple[Path, str, bool]:
    declared = "document_dir" in storage
    if not declared:
        document_root = source_root / "data" / "documents"
        basis = "LEGACY_STANDALONE_DEFAULT"
    else:
        raw_document_root = storage["document_dir"]
        if not isinstance(raw_document_root, (str, os.PathLike)) or not str(
            raw_document_root
        ).strip():
            raise CandidateDataError("SOURCE_DOCUMENT_DIR_INVALID")
        document_root = Path(raw_document_root).expanduser()
        if not document_root.is_absolute():
            document_root = source_root / document_root
        basis = "CONFIG_EXPLICIT"

    _guard_no_reparse(document_root)
    resolved = document_root.resolve(strict=False)
    if not resolved.is_relative_to(source_root):
        raise CandidateDataError("SOURCE_CONFIG_ESCAPE")
    return resolved, basis, declared


def _read_documents_from_connection(
    connection: sqlite3.Connection,
) -> tuple[_DocumentRecord, ...]:
    rows = connection.execute(
        "SELECT id, stored_path, sha256 FROM documents ORDER BY id"
    ).fetchall()
    return tuple(
        _DocumentRecord(int(row[0]), Path(str(row[1])).resolve(strict=False), str(row[2]).lower())
        for row in rows
    )


def _schema_revision_from_connection(connection: sqlite3.Connection) -> str:
    row = connection.execute("SELECT version_num FROM alembic_version").fetchone()
    if row is None or not row[0]:
        raise CandidateDataError("SOURCE_SCHEMA_NOT_VERIFIED")
    return str(row[0])


def _read_documents(database: Path) -> tuple[_DocumentRecord, ...]:
    uri = database.as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        connection.execute("PRAGMA query_only = ON")
        return _read_documents_from_connection(connection)


def _schema_revision(database: Path) -> str:
    uri = database.as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        connection.execute("PRAGMA query_only = ON")
        return _schema_revision_from_connection(connection)


def _file_observation(path: Path, *, include_sha256: bool) -> dict[str, Any]:
    try:
        stat = path.stat()
    except FileNotFoundError:
        return {"exists": False}
    observation: dict[str, Any] = {"exists": True, "size": stat.st_size}
    if include_sha256:
        try:
            observation["sha256"] = _sha256(path)
        except FileNotFoundError:
            return {"exists": False, "changed_during_observation": True}
    return observation


def _sqlite_file_observation(source_db: Path) -> dict[str, Any]:
    return {
        "main_db": _file_observation(source_db, include_sha256=True),
        "wal": _file_observation(Path(f"{source_db}-wal"), include_sha256=True),
        "shm": _file_observation(Path(f"{source_db}-shm"), include_sha256=False),
    }


def _snapshot_sqlite(source_connection: sqlite3.Connection, candidate_db: Path) -> None:
    candidate_db.parent.mkdir(parents=True, exist_ok=True)
    started = _monotonic()

    def enforce_deadline(_status: int, _remaining: int, _total: int) -> None:
        if _monotonic() - started > MAX_BACKUP_SECONDS:
            raise CandidateDataError("SOURCE_BACKUP_TIMEOUT")

    with sqlite3.connect(candidate_db, timeout=1.0) as candidate_connection:
        candidate_connection.execute(f"PRAGMA busy_timeout = {_SQLITE_BUSY_TIMEOUT_MS}")
        source_connection.backup(
            candidate_connection,
            pages=_BACKUP_PAGES,
            progress=enforce_deadline,
            sleep=0.05,
        )
    if _monotonic() - started > MAX_BACKUP_SECONDS:
        raise CandidateDataError("SOURCE_BACKUP_TIMEOUT")


def _copy_verified_document(source: Path, destination: Path, expected_sha256: str) -> None:
    if not source.is_file():
        raise CandidateDataError(f"MANAGED_SOURCE_MISSING: {source}")
    if _sha256(source) != expected_sha256:
        raise CandidateDataError(f"MANAGED_SOURCE_SHA_MISMATCH: {source}")
    if destination.exists():
        raise CandidateDataError(f"DESTINATION_COLLISION: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    if _sha256(destination) != expected_sha256:
        raise CandidateDataError(f"MANAGED_DESTINATION_SHA_MISMATCH: {destination}")
    try:
        if os.path.samefile(source, destination):
            raise CandidateDataError(f"SAME_FILE_ALIAS: {destination}")
    except FileNotFoundError:
        raise CandidateDataError(f"MANAGED_DESTINATION_MISSING: {destination}") from None


def _rebase_document(
    connection: sqlite3.Connection,
    source_record: _DocumentRecord,
    candidate_record: _DocumentRecord,
    destination: Path,
) -> None:
    if candidate_record != source_record:
        raise CandidateDataError(
            f"DOCUMENT_IDENTITY_MISMATCH: document_id={source_record.document_id}"
        )
    cursor = connection.execute(
        "UPDATE documents SET stored_path = ? "
        "WHERE id = ? AND stored_path = ? AND lower(sha256) = ?",
        (
            str(destination.resolve()),
            source_record.document_id,
            str(source_record.stored_path),
            source_record.sha256,
        ),
    )
    if cursor.rowcount != 1:
        raise CandidateDataError(
            f"DOCUMENT_IDENTITY_MISMATCH: document_id={source_record.document_id}"
        )


def _candidate_roots(destination: Path) -> dict[str, Path]:
    data = destination / "data"
    return {
        "candidate_database_root": data / "database",
        "candidate_document_root": data / "documents",
        "candidate_download_root": data / "downloads",
        "candidate_discovery_root": data / "discovery",
        "candidate_raw_root": data / "raw",
        "candidate_reject_root": data / "rejects",
        "candidate_report_root": data / "reports",
        "candidate_log_root": destination / "logs",
        "candidate_session_root": data / "sessions",
        "candidate_backup_root": data / "backups",
        "candidate_config_root": destination,
    }


def managed_document_mapping_identity(
    destination_root: Path | str,
    database: Path | str,
) -> dict[str, Any]:
    """Return a canonical, mapping-sensitive identity for managed documents."""
    destination = Path(destination_root).resolve(strict=True)
    document_root = (destination / "data" / "documents").resolve(strict=True)
    records = _read_documents(Path(database).resolve(strict=True))
    entries: list[list[Any]] = []
    observed_paths: set[Path] = set()
    for record in records:
        stored_path = record.stored_path.resolve(strict=True)
        if not stored_path.is_relative_to(document_root):
            raise CandidateDataError(f"MANAGED_DOCUMENT_PATH_ESCAPE: {stored_path}")
        if stored_path in observed_paths:
            raise CandidateDataError(f"MANAGED_DOCUMENT_PATH_COLLISION: {stored_path}")
        observed_paths.add(stored_path)
        if _sha256(stored_path).lower() != record.sha256:
            raise CandidateDataError(f"MANAGED_DOCUMENT_SHA_MISMATCH: {record.document_id}")
        relative = stored_path.relative_to(document_root).as_posix()
        entries.append([record.document_id, relative, record.sha256])
    entries.sort(key=lambda item: (item[0], item[1], item[2]))
    canonical = json.dumps(
        {"document_count": len(entries), "documents": entries},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return {
        "document_count": len(entries),
        "managed_document_mapping_digest": hashlib.sha256(canonical).hexdigest(),
    }


def _isolated_config(raw: dict[str, Any], roots: dict[str, Path], database: Path) -> dict[str, Any]:
    copied = json.loads(json.dumps(raw))
    storage = copied.setdefault("storage", {})
    storage.update(
        {
            "database_url": f"sqlite:///{database.resolve().as_posix()}",
            "document_dir": str(roots["candidate_document_root"].resolve()),
            "download_dir": str(roots["candidate_download_root"].resolve()),
            "discovery_dir": str(roots["candidate_discovery_root"].resolve()),
            "raw_dir": str(roots["candidate_raw_root"].resolve()),
            "rejects_dir": str(roots["candidate_reject_root"].resolve()),
            "report_dir": str(roots["candidate_report_root"].resolve()),
        }
    )
    copied["candidate_isolation"] = {key: str(value.resolve()) for key, value in roots.items()}
    return copied


def prepare_candidate_data(source_root: Path | str, destination_root: Path | str) -> dict[str, Any]:
    source, destination = _guard_roots(Path(source_root), Path(destination_root))
    source_config = source / "config.yaml"
    if not source_config.is_file():
        raise CandidateDataError(f"SOURCE_CONFIG_MISSING: {source_config}")
    raw = yaml.safe_load(source_config.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict) or not isinstance(raw.get("storage"), dict):
        raise CandidateDataError("SOURCE_CONFIG_INVALID")
    storage = raw["storage"]
    source_db = _sqlite_path(str(storage.get("database_url", "")))
    source_documents, source_document_root_basis, source_document_dir_declared = (
        _resolve_source_document_root(source, storage)
    )
    if not source_db.is_relative_to(source) or not source_documents.is_relative_to(source):
        raise CandidateDataError("SOURCE_CONFIG_ESCAPE")
    _guard_no_reparse(source_db)
    _guard_no_reparse(source_documents)

    destination.mkdir(parents=True, exist_ok=True)
    incomplete: dict[str, Any] = {
        "status": "INCOMPLETE",
        "source_root": str(source),
        "destination_root": str(destination),
        "created_at": datetime.now(UTC).isoformat(),
    }
    _write_receipt(destination, incomplete)
    try:
        roots = _candidate_roots(destination)
        for path in roots.values():
            path.mkdir(parents=True, exist_ok=True)
        candidate_db = roots["candidate_database_root"] / "egp.db"
        pre_open_observation = _sqlite_file_observation(source_db)
        db_hash_before = str(pre_open_observation["main_db"]["sha256"])
        source_uri = source_db.as_uri() + "?mode=ro"
        with sqlite3.connect(
            source_uri,
            uri=True,
            isolation_level=None,
            timeout=1.0,
        ) as source_connection:
            source_connection.execute("PRAGMA query_only = ON")
            source_connection.execute(f"PRAGMA busy_timeout = {_SQLITE_BUSY_TIMEOUT_MS}")
            journal_mode = str(source_connection.execute("PRAGMA journal_mode").fetchone()[0])
            data_version_start = int(
                source_connection.execute("PRAGMA data_version").fetchone()[0]
            )
            source_connection.execute("BEGIN")
            try:
                schema = _schema_revision_from_connection(source_connection)
                records = _read_documents_from_connection(source_connection)
                document_hashes_before: dict[int, str] = {}
                for record in records:
                    if not record.stored_path.is_file():
                        raise CandidateDataError(f"MANAGED_SOURCE_MISSING: {record.stored_path}")
                    document_hashes_before[record.document_id] = _sha256(record.stored_path)
                _capture_hook("AFTER_SOURCE_METADATA_READ")

                _snapshot_sqlite(source_connection, candidate_db)
                candidate_records = _read_documents(candidate_db)
                candidate_schema = _schema_revision(candidate_db)
                if candidate_schema != schema:
                    raise CandidateDataError("FAIL_CANDIDATE_SCHEMA_MISMATCH")
                if candidate_records != records:
                    raise CandidateDataError("DOCUMENT_IDENTITY_MISMATCH")
                _capture_hook("AFTER_SQLITE_BACKUP")

                copied_targets: set[Path] = set()
                with sqlite3.connect(candidate_db) as candidate_connection:
                    for source_record, candidate_record in zip(
                        records, candidate_records, strict=True
                    ):
                        if not source_record.stored_path.is_relative_to(source_documents):
                            raise CandidateDataError(
                                f"MANAGED_SOURCE_ESCAPE: {source_record.stored_path}"
                            )
                        _guard_no_reparse(source_record.stored_path)
                        relative = source_record.stored_path.relative_to(source_documents)
                        target = (roots["candidate_document_root"] / relative).resolve(strict=False)
                        if not target.is_relative_to(roots["candidate_document_root"].resolve()):
                            raise CandidateDataError(f"CANDIDATE_PATH_ESCAPE: {target}")
                        if target in copied_targets:
                            raise CandidateDataError(f"DESTINATION_COLLISION: {target}")
                        _copy_verified_document(
                            source_record.stored_path, target, source_record.sha256
                        )
                        copied_targets.add(target)
                        _rebase_document(
                            candidate_connection, source_record, candidate_record, target
                        )

                for record in records:
                    if _sha256(record.stored_path) != document_hashes_before[record.document_id]:
                        raise CandidateDataError(
                            f"SOURCE_DOCUMENT_CHANGED_DURING_CAPTURE: {record.document_id}"
                        )
            finally:
                source_connection.rollback()
            data_version_end = int(
                source_connection.execute("PRAGMA data_version").fetchone()[0]
            )
            if data_version_end != data_version_start:
                raise CandidateDataError("SOURCE_DB_CHANGED_DURING_CAPTURE")
        final_observation = _sqlite_file_observation(source_db)
        sidecar_activity = (
            "OBSERVED"
            if (
                pre_open_observation["wal"] != final_observation["wal"]
                or pre_open_observation["shm"] != final_observation["shm"]
            )
            else "NONE"
        )

        candidate_paths = _read_documents(candidate_db)
        if any(not record.stored_path.is_relative_to(destination) for record in candidate_paths):
            raise CandidateDataError("FAIL_CANDIDATE_ISOLATION")

        candidate_config = _isolated_config(raw, roots, candidate_db)
        candidate_config_path = destination / "config.yaml"
        candidate_config_path.write_text(
            yaml.safe_dump(candidate_config, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        keyword_groups = source / "keyword-groups.yaml"
        if keyword_groups.is_file():
            shutil.copyfile(keyword_groups, destination / "keyword-groups.yaml")

        mapping_identity = managed_document_mapping_identity(destination, candidate_db)
        complete: dict[str, Any] = {
            **incomplete,
            "receipt_schema_version": CLONE_RECEIPT_SCHEMA_VERSION,
            "status": "COMPLETE",
            "source_db_identity": {"path": str(source_db), "sha256": db_hash_before},
            "source_sqlite_observation": {
                "journal_mode": journal_mode,
                "data_version_start": data_version_start,
                "data_version_end": data_version_end,
                "pre_open": pre_open_observation,
                "final": final_observation,
                "coordination_sidecar_activity": sidecar_activity,
            },
            "candidate_db_identity": {
                "path": str(candidate_db.resolve()),
                "sha256": _sha256(candidate_db),
            },
            "source_schema": schema,
            "source_document_root": str(source_documents),
            "source_document_root_basis": source_document_root_basis,
            "source_document_dir_declared": source_document_dir_declared,
            **mapping_identity,
            "rebase_count": len(records),
            "candidate_config_path": str(candidate_config_path.resolve()),
            **{key: str(path.resolve()) for key, path in roots.items()},
        }
        _write_receipt(destination, complete)
        return complete
    except Exception as exc:
        incomplete["error"] = str(exc)
        _write_receipt(destination, incomplete)
        raise


def _validate_candidate_config(
    destination: Path,
    receipt: dict[str, Any],
) -> None:
    config_path = Path(str(receipt.get("candidate_config_path", ""))).resolve(strict=True)
    if config_path != (destination / "config.yaml").resolve(strict=True):
        raise CandidateDataError("CANDIDATE_CONFIG_PATH_MISMATCH")
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict) or not isinstance(raw.get("storage"), dict):
        raise CandidateDataError("CANDIDATE_CONFIG_INVALID")
    isolation = raw.get("candidate_isolation")
    if not isinstance(isolation, dict):
        raise CandidateDataError("CANDIDATE_CONFIG_ISOLATION_MISSING")
    root_keys = tuple(_candidate_roots(destination))
    for key in root_keys:
        configured = Path(str(isolation.get(key, ""))).resolve(strict=False)
        recorded = Path(str(receipt.get(key, ""))).resolve(strict=False)
        if (
            configured != recorded
            or not configured.is_relative_to(destination)
            or not configured.is_dir()
        ):
            raise CandidateDataError(f"CANDIDATE_CONFIG_ESCAPE: {key}")
    storage = raw["storage"]
    expected_storage = {
        "database_url": f"sqlite:///{(destination / 'data' / 'database' / 'egp.db').resolve().as_posix()}",
        "document_dir": str((destination / "data" / "documents").resolve()),
        "download_dir": str((destination / "data" / "downloads").resolve()),
        "discovery_dir": str((destination / "data" / "discovery").resolve()),
        "raw_dir": str((destination / "data" / "raw").resolve()),
        "rejects_dir": str((destination / "data" / "rejects").resolve()),
        "report_dir": str((destination / "data" / "reports").resolve()),
    }
    for key, expected in expected_storage.items():
        if storage.get(key) != expected:
            raise CandidateDataError(f"CANDIDATE_CONFIG_ESCAPE: {key}")


def validate_candidate_receipt(
    destination_root: Path | str,
    *,
    require_pre_migration_db_identity: bool = True,
) -> dict[str, Any]:
    destination = Path(destination_root).resolve(strict=True)
    _guard_no_reparse(destination)
    receipt_path = destination / _RECEIPT_NAME
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CandidateDataError("CANDIDATE_RECEIPT_INVALID") from exc
    if receipt.get("status") != "COMPLETE":
        raise CandidateDataError("CANDIDATE_RECEIPT_INCOMPLETE")
    if receipt.get("receipt_schema_version") != CLONE_RECEIPT_SCHEMA_VERSION:
        raise CandidateDataError("CANDIDATE_RECEIPT_SCHEMA_UNSUPPORTED")
    if Path(str(receipt.get("destination_root", ""))).resolve() != destination:
        raise CandidateDataError("CANDIDATE_RECEIPT_DESTINATION_MISMATCH")
    candidate_db = Path(
        str((receipt.get("candidate_db_identity") or {}).get("path", ""))
    ).resolve(strict=True)
    expected_db = (destination / "data" / "database" / "egp.db").resolve(strict=True)
    if candidate_db != expected_db or not candidate_db.is_relative_to(destination):
        raise CandidateDataError("CANDIDATE_DB_PATH_MISMATCH")
    if require_pre_migration_db_identity:
        expected_sha = str((receipt.get("candidate_db_identity") or {}).get("sha256", ""))
        if _sha256(candidate_db) != expected_sha:
            raise CandidateDataError("CANDIDATE_DB_IDENTITY_MISMATCH")
        if _schema_revision(candidate_db) != receipt.get("source_schema"):
            raise CandidateDataError("CANDIDATE_SCHEMA_IDENTITY_MISMATCH")
    current_mapping = managed_document_mapping_identity(destination, candidate_db)
    if current_mapping != {
        "document_count": receipt.get("document_count"),
        "managed_document_mapping_digest": receipt.get("managed_document_mapping_digest"),
    }:
        raise CandidateDataError("MANAGED_DOCUMENT_MAPPING_MISMATCH")
    _validate_candidate_config(destination, receipt)
    return receipt
