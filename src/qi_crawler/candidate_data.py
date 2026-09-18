from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
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


def _read_documents(database: Path) -> tuple[_DocumentRecord, ...]:
    uri = database.as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        connection.execute("PRAGMA query_only = ON")
        rows = connection.execute(
            "SELECT id, stored_path, sha256 FROM documents ORDER BY id"
        ).fetchall()
    return tuple(
        _DocumentRecord(int(row[0]), Path(str(row[1])).resolve(strict=False), str(row[2]).lower())
        for row in rows
    )


def _schema_revision(database: Path) -> str:
    uri = database.as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        connection.execute("PRAGMA query_only = ON")
        row = connection.execute("SELECT version_num FROM alembic_version").fetchone()
    if row is None or not row[0]:
        raise CandidateDataError("SOURCE_SCHEMA_NOT_VERIFIED")
    return str(row[0])


def _snapshot_sqlite(source_db: Path, candidate_db: Path) -> None:
    candidate_db.parent.mkdir(parents=True, exist_ok=True)
    source_uri = source_db.as_uri() + "?mode=ro"
    with sqlite3.connect(source_uri, uri=True) as source_connection:
        source_connection.execute("PRAGMA query_only = ON")
        with sqlite3.connect(candidate_db) as candidate_connection:
            source_connection.backup(candidate_connection)


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
    source_db = _sqlite_path(str(raw["storage"].get("database_url", "")))
    source_documents = Path(str(raw["storage"].get("document_dir", ""))).resolve(strict=True)
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
        db_hash_before = _sha256(source_db)
        records = _read_documents(source_db)
        document_hashes_before: dict[int, str] = {}
        for record in records:
            if not record.stored_path.is_file():
                raise CandidateDataError(f"MANAGED_SOURCE_MISSING: {record.stored_path}")
            document_hashes_before[record.document_id] = _sha256(record.stored_path)
        schema = _schema_revision(source_db)

        _snapshot_sqlite(source_db, candidate_db)
        candidate_records = _read_documents(candidate_db)
        if len(candidate_records) != len(records):
            raise CandidateDataError("DOCUMENT_IDENTITY_MISMATCH: document count")

        copied_targets: set[Path] = set()
        with sqlite3.connect(candidate_db) as candidate_connection:
            for source_record, candidate_record in zip(records, candidate_records, strict=True):
                if not source_record.stored_path.is_relative_to(source_documents):
                    raise CandidateDataError(f"MANAGED_SOURCE_ESCAPE: {source_record.stored_path}")
                _guard_no_reparse(source_record.stored_path)
                relative = source_record.stored_path.relative_to(source_documents)
                target = (roots["candidate_document_root"] / relative).resolve(strict=False)
                if not target.is_relative_to(roots["candidate_document_root"].resolve()):
                    raise CandidateDataError(f"CANDIDATE_PATH_ESCAPE: {target}")
                if target in copied_targets:
                    raise CandidateDataError(f"DESTINATION_COLLISION: {target}")
                _copy_verified_document(source_record.stored_path, target, source_record.sha256)
                copied_targets.add(target)
                _rebase_document(candidate_connection, source_record, candidate_record, target)

        for record in records:
            if _sha256(record.stored_path) != document_hashes_before[record.document_id]:
                raise CandidateDataError(
                    f"SOURCE_DOCUMENT_CHANGED_DURING_CAPTURE: {record.document_id}"
                )
        if _sha256(source_db) != db_hash_before:
            raise CandidateDataError("SOURCE_DB_CHANGED_DURING_CAPTURE")

        candidate_paths = _read_documents(candidate_db)
        if any(not record.stored_path.is_relative_to(destination) for record in candidate_paths):
            raise CandidateDataError("FAIL_CANDIDATE_ISOLATION")

        candidate_config = _isolated_config(raw, roots, candidate_db)
        (destination / "config.yaml").write_text(
            yaml.safe_dump(candidate_config, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        keyword_groups = source / "keyword-groups.yaml"
        if keyword_groups.is_file():
            shutil.copyfile(keyword_groups, destination / "keyword-groups.yaml")

        digest_payload = "\n".join(sorted({record.sha256 for record in records})).encode()
        complete: dict[str, Any] = {
            **incomplete,
            "status": "COMPLETE",
            "source_db_identity": {"path": str(source_db), "sha256": db_hash_before},
            "candidate_db_identity": {
                "path": str(candidate_db.resolve()),
                "sha256": _sha256(candidate_db),
            },
            "source_schema": schema,
            "document_count": len(records),
            "document_sha_set_digest": hashlib.sha256(digest_payload).hexdigest(),
            "rebase_count": len(records),
            **{key: str(path.resolve()) for key, path in roots.items()},
        }
        _write_receipt(destination, complete)
        return complete
    except Exception as exc:
        incomplete["error"] = str(exc)
        _write_receipt(destination, incomplete)
        raise


def validate_candidate_receipt(destination_root: Path | str) -> dict[str, Any]:
    destination = Path(destination_root).resolve(strict=True)
    receipt_path = destination / _RECEIPT_NAME
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CandidateDataError("CANDIDATE_RECEIPT_INVALID") from exc
    if receipt.get("status") != "COMPLETE":
        raise CandidateDataError("CANDIDATE_RECEIPT_INCOMPLETE")
    if Path(str(receipt.get("destination_root", ""))).resolve() != destination:
        raise CandidateDataError("CANDIDATE_RECEIPT_DESTINATION_MISMATCH")
    return receipt
