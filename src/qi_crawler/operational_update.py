"""Read-only observation and fail-closed classification of operational updates."""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import re
import shutil
import sqlite3
import stat
import tempfile
import time
from collections.abc import Callable, Mapping
from contextlib import ExitStack, closing, nullcontext
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any
from uuid import uuid4

from .operational_release import OperationalPaths, operational_paths
from .update_transaction import MaintenanceBusy, _ExclusiveFileLock, _write_json_durable

MARKER_SCHEMA = "qi-crawler-operational-update-marker-v1"
JOURNAL_SCHEMA = "qi-crawler-operational-update-journal-v1"
RECEIPT_SCHEMA = "qi-crawler-operational-update-receipt-v1"
UPDATE_POINTER_SCHEMA = "qi-crawler-update-pointer-v1"
UPDATE_STATE_SCHEMA = "qi-crawler-app-update-state-v1"
_WAL_HEADER_SIZE = 32
_WAL_FRAME_HEADER_SIZE = 24
_WAL_FORMAT_VERSION = 3_007_000
_SHM_REGION_SIZE = 32_768

_PHASES = {
    "EARLY_ACTIVE",
    "BACKUP_REQUIRED",
    "PRECOMMIT",
    "DB_COMMIT_INTENT",
    "DB_COMMITTED",
    "RECEIPT_WRITTEN",
    "TERMINAL",
}
_BACKUP_PHASES = _PHASES - {"EARLY_ACTIVE"}
_NEW_IDENTITY_PHASES = {"DB_COMMITTED", "RECEIPT_WRITTEN", "TERMINAL"}
_RECEIPT_PHASES = {"RECEIPT_WRITTEN", "TERMINAL"}
_CLASSIFICATIONS = {
    "EARLY_ACTIVE": "EARLY_ACTIVE_PHASE",
    "BACKUP_REQUIRED": "BACKUP_VALID",
    "PRECOMMIT": "PRECOMMIT_OLD_DB",
    "DB_COMMIT_INTENT": "PRECOMMIT_OLD_DB",
    "DB_COMMITTED": "DB_COMMITTED_JOURNAL_LAG",
    "RECEIPT_WRITTEN": "RECEIPT_PRESENT_VALID",
    "TERMINAL": "TERMINAL_CONSISTENT",
}

_UPDATE_TERMINAL_RESULTS = {
    "COMPLETE",
    "FAILED_NO_MUTATION",
    "ROLLED_BACK",
    "RECOVERY_COMPLETE",
}
_UPDATE_PHASES = {"PREPARING", "STAGED", "NEW_APP_ACTIVE", "RECOVERY_REQUIRED", "TERMINAL"}
_UPDATE_TRANSITION_KINDS = {
    "INTENT",
    "CONFIRMED",
    "RECOVERY_INTENT",
    "RECOVERY_CONFIRMED",
    "ATTEMPT_FAILED_RECOVERED",
}
_UPDATE_ACTIONS = {
    "CAPTURE_ACCEPTANCE_SNAPSHOT",
    "SET_ACTIVE_MARKER",
    "CAPTURE_LKG_SNAPSHOT",
    "COPY_BUNDLE_TO_STAGE",
    "ROTATE_ACTIVE_TO_OLD",
    "ROTATE_STAGE_TO_ACTIVE",
    "COMMIT_ACCEPTANCE",
    "CLEAR_ACTIVE_MARKER",
    "RECOVERY_MOVE_ACTIVE_TO_FAILED",
    "RECOVERY_RESTORE_OLD_ACTIVE",
    "RECOVERY_RESTORE_ACCEPTANCE",
    "RECOVERY_CLEAR_ACTIVE_MARKER",
    "FINALIZE_UPDATE",
}
_UPDATE_ID_PATTERN = re.compile(r"[0-9a-f]{32}\Z")
_MAX_UPDATE_PATH_LENGTH = 240
_DATA_SENTINEL_TABLES = (
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
)
_DATA_SENTINEL_COUNT_TABLES = (
    "notices",
    "documents",
    "tender_cases",
    "tender_releases",
    "tender_document_memberships",
    "tender_recovery_events",
)


class OperationalUpdateError(RuntimeError):
    """An operational application update cannot be classified safely."""


def _safe_update_id(value: object) -> bool:
    return isinstance(value, str) and _UPDATE_ID_PATTERN.fullmatch(value) is not None


def _expected_update_paths(paths: OperationalPaths, update_id: str) -> dict[str, Path]:
    attempt_root = paths.root / ".update" / update_id
    journal_root = paths.control_root / "updates" / update_id
    return {
        "active": paths.application_root,
        "old": attempt_root / "old",
        "stage": attempt_root / "stage",
        "failed": attempt_root / "failed",
        "acceptance_snapshot": journal_root / "acceptance.before.json",
        "journal": journal_root / "state.json",
        "lkg_manifest": journal_root / "last_known_good.json",
        "snapshot_root": paths.data_dir / "backups" / update_id,
    }


def _strict_relative_path(paths: OperationalPaths, value: object, expected: Path) -> bool:
    if not isinstance(value, str) or not value or "\x00" in value:
        return False
    components = re.split(r"[\\/]", value)
    if any(component in {"", ".", ".."} for component in components):
        return False
    candidate = Path(value)
    if candidate.is_absolute() or candidate.drive or candidate.root:
        return False
    try:
        return paths.root / candidate == expected
    except (TypeError, ValueError):
        return False


def _validate_update_journal(
    paths: OperationalPaths,
    state: object,
    update_id: object,
    *,
    journal_path: Path | None = None,
) -> dict[str, Any]:
    """Validate the shared durable journal contract before reads drive mutation."""
    if not _safe_update_id(update_id) or not isinstance(state, dict):
        raise OperationalUpdateError("UPDATE_JOURNAL_CONTRACT_INVALID")
    if (
        state.get("schema_version") != UPDATE_STATE_SCHEMA
        or state.get("update_id") != update_id
        or state.get("phase") not in _UPDATE_PHASES
    ):
        raise OperationalUpdateError("UPDATE_JOURNAL_CONTRACT_INVALID")

    phase = state.get("phase")
    result = state.get("result")
    if result not in ({None, "RECOVERY_REQUIRED"} | _UPDATE_TERMINAL_RESULTS):
        raise OperationalUpdateError("UPDATE_JOURNAL_CONTRACT_INVALID")
    if (phase == "TERMINAL") != (result in _UPDATE_TERMINAL_RESULTS):
        raise OperationalUpdateError("UPDATE_JOURNAL_TERMINAL_STATE_INVALID")
    if result == "RECOVERY_REQUIRED" and phase != "RECOVERY_REQUIRED":
        raise OperationalUpdateError("UPDATE_JOURNAL_TERMINAL_STATE_INVALID")
    if state.get("first_mutation_at") is not None and not isinstance(
        state.get("first_mutation_at"), str
    ):
        raise OperationalUpdateError("UPDATE_JOURNAL_CONTRACT_INVALID")

    expected = _expected_update_paths(paths, update_id)
    application = state.get("application")
    acceptance = state.get("acceptance")
    if (
        not isinstance(application, dict)
        or not isinstance(application.get("old"), dict)
        or not isinstance(application.get("new"), dict)
        or not isinstance(acceptance, dict)
        or not isinstance(acceptance.get("old_sha256"), str)
        or not _strict_relative_path(paths, application.get("active_path"), expected["active"])
        or not _strict_relative_path(paths, application.get("old_path"), expected["old"])
        or not _strict_relative_path(paths, application.get("stage_path"), expected["stage"])
        or not _strict_relative_path(paths, application.get("failed_path"), expected["failed"])
        or not _strict_relative_path(
            paths, acceptance.get("snapshot_path"), expected["acceptance_snapshot"]
        )
        or not _strict_relative_path(paths, state.get("lkg_manifest_path"), expected["lkg_manifest"])
    ):
        raise OperationalUpdateError("UPDATE_JOURNAL_PATH_UNSAFE")
    source_data_before = state.get("source_data_before")
    expected_data_paths = {
        str(candidate)
        for candidate in (
            paths.config_path,
            paths.database_path,
            Path(f"{paths.database_path}-wal"),
            Path(f"{paths.database_path}-shm"),
        )
    }
    if not isinstance(source_data_before, dict) or set(source_data_before) != expected_data_paths:
        raise OperationalUpdateError("UPDATE_DATA_IDENTITY_PATHS_INVALID")
    if journal_path is not None and journal_path != expected["journal"]:
        raise OperationalUpdateError("UPDATE_JOURNAL_PATH_UNSAFE")

    transitions = state.get("transitions")
    if not isinstance(transitions, list):
        raise OperationalUpdateError("UPDATE_TRANSITION_HISTORY_INVALID")
    pending: dict[str, Any] | None = None
    for sequence, transition in enumerate(transitions, start=1):
        if (
            not isinstance(transition, dict)
            or type(transition.get("sequence")) is not int
            or transition.get("sequence") != sequence
            or transition.get("kind") not in _UPDATE_TRANSITION_KINDS
            or transition.get("action") not in _UPDATE_ACTIONS
            or not isinstance(transition.get("action"), str)
            or not transition.get("action")
            or not isinstance(transition.get("at_utc"), str)
            or not isinstance(transition.get("before"), dict)
            or not isinstance(transition.get("expected"), dict)
        ):
            raise OperationalUpdateError("UPDATE_TRANSITION_HISTORY_INVALID")
        kind = transition["kind"]
        if kind in {"INTENT", "RECOVERY_INTENT"}:
            if pending is not None:
                raise OperationalUpdateError("UPDATE_TRANSITION_HISTORY_INVALID")
            pending = transition
        elif kind in {"CONFIRMED", "RECOVERY_CONFIRMED", "ATTEMPT_FAILED_RECOVERED"}:
            if (
                pending is None
                or pending.get("action") != transition.get("action")
                or pending.get("before") != transition.get("before")
                or pending.get("expected") != transition.get("expected")
                or (
                    kind == "CONFIRMED"
                    and pending.get("kind") != "INTENT"
                )
                or (kind == "RECOVERY_CONFIRMED" and pending.get("kind") != "RECOVERY_INTENT")
                or not isinstance(transition.get("observed"), dict)
            ):
                raise OperationalUpdateError("UPDATE_TRANSITION_HISTORY_INVALID")
            pending = None

    pending_action = state.get("pending_action")
    if pending is None:
        if pending_action is not None:
            raise OperationalUpdateError("UPDATE_TRANSITION_PENDING_ACTION_INVALID")
    elif pending_action != pending.get("action") or transitions[-1] is not pending:
        raise OperationalUpdateError("UPDATE_TRANSITION_PENDING_ACTION_INVALID")
    return state


def _load_update_journals(paths: OperationalPaths) -> dict[str, dict[str, Any]]:
    """Enumerate every attempt directory so orphan state cannot be ignored."""
    updates_root = paths.control_root / "updates"
    if _unsafe_path(updates_root, paths.root):
        raise OperationalUpdateError("UPDATE_CONTROL_PATH_UNSAFE")
    if not updates_root.exists():
        return {}
    if not updates_root.is_dir():
        raise OperationalUpdateError("UPDATE_CONTROL_PATH_UNSAFE")
    try:
        entries = tuple(sorted(updates_root.iterdir(), key=lambda item: item.name))
    except OSError as exc:
        raise OperationalUpdateError("UPDATE_JOURNAL_DIRECTORY_UNKNOWN") from exc

    states: dict[str, dict[str, Any]] = {}
    for entry in entries:
        update_id = entry.name
        if not _safe_update_id(update_id):
            raise OperationalUpdateError("UPDATE_ID_INVALID")
        if (
            not entry.is_dir()
            or entry.is_symlink()
            or _unsafe_path(entry, paths.root)
        ):
            raise OperationalUpdateError("UPDATE_ATTEMPT_DIRECTORY_UNSAFE")
        journal_path = entry / "state.json"
        if _unsafe_path(journal_path, paths.root):
            raise OperationalUpdateError("UPDATE_JOURNAL_PATH_UNSAFE")
        if not journal_path.is_file():
            raise OperationalUpdateError("UPDATE_JOURNAL_REQUIRED")
        state, error = _json(journal_path)
        if error or state is None:
            raise OperationalUpdateError("UPDATE_JOURNAL_INVALID")
        states[update_id] = _validate_update_journal(
            paths, state, update_id, journal_path=journal_path
        )
    return states


def _journal_paths(paths: OperationalPaths, journal_path: Path) -> None:
    expected_parent = paths.control_root / "updates"
    if (
        journal_path.name != "state.json"
        or journal_path.parent.parent != expected_parent
        or not _safe_update_id(journal_path.parent.name)
    ):
        raise OperationalUpdateError("UPDATE_JOURNAL_PATH_UNSAFE")


def _paths_for_journal(journal_path: Path) -> OperationalPaths:
    if journal_path.name != "state.json":
        raise OperationalUpdateError("UPDATE_JOURNAL_PATH_UNSAFE")
    root = journal_path.parent.parent.parent.parent
    paths = operational_paths(root)
    _journal_paths(paths, journal_path)
    return paths


def _append_update_transition(
    journal_path: Path,
    *,
    kind: str,
    action: str,
    before: dict[str, Any],
    expected: dict[str, Any],
    observed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Durably append one sequenced transition without dropping prior evidence."""
    state, error = _json(journal_path)
    if error or state is None:
        raise OperationalUpdateError("UPDATE_JOURNAL_INVALID")
    paths = _paths_for_journal(journal_path)
    state = _validate_update_journal(
        paths,
        state,
        state.get("update_id"),
        journal_path=journal_path,
    )
    transitions = state.get("transitions")
    if not isinstance(transitions, list):
        raise OperationalUpdateError("UPDATE_TRANSITION_HISTORY_INVALID")
    for expected_sequence, transition in enumerate(transitions, start=1):
        if not isinstance(transition, dict) or transition.get("sequence") != expected_sequence:
            raise OperationalUpdateError("UPDATE_TRANSITION_SEQUENCE_INVALID")
    if kind not in {
        "INTENT",
        "CONFIRMED",
        "RECOVERY_INTENT",
        "RECOVERY_CONFIRMED",
        "ATTEMPT_FAILED_RECOVERED",
    }:
        raise OperationalUpdateError("UPDATE_TRANSITION_KIND_INVALID")
    pending_action = state.get("pending_action")
    is_intent = kind in {"INTENT", "RECOVERY_INTENT"}
    if is_intent and pending_action is not None:
        raise OperationalUpdateError("UPDATE_TRANSITION_PENDING")
    if kind in {"CONFIRMED", "ATTEMPT_FAILED_RECOVERED"}:
        if pending_action != action or not transitions:
            raise OperationalUpdateError("UPDATE_TRANSITION_INTENT_REQUIRED")
        pending = transitions[-1]
        allowed_pending_kinds = (
            {"INTENT"}
            if kind == "CONFIRMED"
            else {"INTENT", "RECOVERY_INTENT"}
        )
        if (
            pending.get("kind") not in allowed_pending_kinds
            or pending.get("action") != action
            or pending.get("before") != before
            or pending.get("expected") != expected
        ):
            raise OperationalUpdateError("UPDATE_TRANSITION_INTENT_MISMATCH")
        if observed is None:
            raise OperationalUpdateError("UPDATE_TRANSITION_OBSERVATION_REQUIRED")
    elif kind == "RECOVERY_CONFIRMED":
        if pending_action != action or not transitions:
            raise OperationalUpdateError("UPDATE_TRANSITION_INTENT_REQUIRED")
        pending = transitions[-1]
        if (
            pending.get("kind") != "RECOVERY_INTENT"
            or pending.get("action") != action
            or pending.get("before") != before
            or pending.get("expected") != expected
        ):
            raise OperationalUpdateError("UPDATE_TRANSITION_INTENT_MISMATCH")
        if observed is None:
            raise OperationalUpdateError("UPDATE_TRANSITION_OBSERVATION_REQUIRED")
    elif observed is not None:
        raise OperationalUpdateError("UPDATE_TRANSITION_OBSERVATION_UNEXPECTED")

    timestamp = datetime.now(UTC).isoformat()
    transition = {
        "sequence": len(transitions) + 1,
        "kind": kind,
        "action": action,
        "at_utc": timestamp,
        "before": before,
        "expected": expected,
    }
    if observed is not None:
        transition["observed"] = observed
    transitions.append(transition)
    if is_intent:
        state["pending_action"] = action
    else:
        state["pending_action"] = None
        if (
            kind in {"CONFIRMED", "RECOVERY_CONFIRMED"}
            and action in {"ROTATE_ACTIVE_TO_OLD", "ROTATE_STAGE_TO_ACTIVE"}
            and not state.get("first_mutation_at")
        ):
            state["first_mutation_at"] = timestamp
        if kind == "ATTEMPT_FAILED_RECOVERED":
            state["phase"] = (
                "TERMINAL"
                if state.get("result") in _UPDATE_TERMINAL_RESULTS
                else "RECOVERY_REQUIRED"
            )
        if action == "FINALIZE_UPDATE" and kind == "CONFIRMED":
            result = (observed or {}).get("result")
            if result not in _UPDATE_TERMINAL_RESULTS:
                raise OperationalUpdateError("UPDATE_TERMINAL_RESULT_INVALID")
            state["phase"] = "TERMINAL"
            state["result"] = result
            state["error_code"] = (observed or {}).get("error_code")
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json_durable(journal_path, state)
    return state


def _update_file_identity(path: Path) -> dict[str, Any]:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return {"exists": False}
    except OSError as exc:
        raise OperationalUpdateError("UPDATE_FILE_IDENTITY_UNKNOWN") from exc
    attributes = int(getattr(metadata, "st_file_attributes", 0))
    if (
        not stat.S_ISREG(metadata.st_mode)
        or stat.S_ISLNK(metadata.st_mode)
        or attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
    ):
        raise OperationalUpdateError("UPDATE_FILE_IDENTITY_UNSAFE")
    try:
        digest = _sha256(path)
    except OSError as exc:
        raise OperationalUpdateError("UPDATE_FILE_IDENTITY_UNKNOWN") from exc
    return {
        "exists": True,
        "size": metadata.st_size,
        "mtime_ns": metadata.st_mtime_ns,
        "sha256": digest,
    }


def _data_file_identity(path: Path) -> dict[str, Any]:
    """Track byte/existence identity; SQLite may update SHM lock metadata on read."""
    identity = _update_file_identity(path)
    if not identity["exists"]:
        return {"exists": False}
    return {
        "exists": True,
        "size": identity["size"],
        "sha256": identity["sha256"],
    }


def _json_payload_file_identity(payload: object) -> dict[str, Any]:
    """Return the byte identity written by the durable JSON serializer."""
    content = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return {
        "exists": True,
        "size": len(content),
        "sha256": hashlib.sha256(content).hexdigest().upper(),
    }


def _windows_path_length(path: Path) -> int:
    return len(str(path).encode("utf-16-le")) // 2


def _durable_json_temp_path(path: Path) -> Path:
    return path.with_name(f".{path.name}.{'f' * 32}.tmp")


def _update_tree_identity(
    root: Path,
    *,
    projected_roots: tuple[Path, ...] = (),
) -> dict[str, Any]:
    try:
        root_metadata = root.lstat()
    except OSError as exc:
        raise OperationalUpdateError("UPDATE_APPLICATION_GENERATION_INVALID") from exc
    root_attributes = int(getattr(root_metadata, "st_file_attributes", 0))
    if stat.S_ISLNK(root_metadata.st_mode) or root_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
        raise OperationalUpdateError("UPDATE_PATH_UNSAFE")
    if not stat.S_ISDIR(root_metadata.st_mode):
        raise OperationalUpdateError("UPDATE_APPLICATION_GENERATION_INVALID")
    digest = hashlib.sha256()
    file_count = 0
    total_bytes = 0
    if any(
        _windows_path_length(projected_root) > _MAX_UPDATE_PATH_LENGTH
        for projected_root in projected_roots
    ):
        raise OperationalUpdateError("UPDATE_PATH_TOO_LONG")
    for current, directories, files in os.walk(root, followlinks=False):
        current_path = Path(current)
        relative_directory = current_path.relative_to(root)
        if any(
            _windows_path_length(projected_root / relative_directory) > _MAX_UPDATE_PATH_LENGTH
            for projected_root in projected_roots
        ):
            raise OperationalUpdateError("UPDATE_PATH_TOO_LONG")
        for name in directories:
            directory = current_path / name
            metadata = directory.lstat()
            attributes = int(getattr(metadata, "st_file_attributes", 0))
            if stat.S_ISLNK(metadata.st_mode) or attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                raise OperationalUpdateError("UPDATE_APPLICATION_REPARSE_POINT")
            relative_path = directory.relative_to(root)
            if any(
                _windows_path_length(projected_root / relative_path) > _MAX_UPDATE_PATH_LENGTH
                for projected_root in projected_roots
            ):
                raise OperationalUpdateError("UPDATE_PATH_TOO_LONG")
        for name in files:
            path = current_path / name
            identity = _update_file_identity(path)
            relative_path = path.relative_to(root)
            relative = relative_path.as_posix()
            if any(
                _windows_path_length(projected_root / relative_path) > _MAX_UPDATE_PATH_LENGTH
                for projected_root in projected_roots
            ):
                raise OperationalUpdateError("UPDATE_PATH_TOO_LONG")
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            digest.update(str(identity["size"]).encode("ascii"))
            digest.update(b"\0")
            digest.update(identity["sha256"].encode("ascii"))
            digest.update(b"\n")
            file_count += 1
            total_bytes += int(identity["size"])
    return {"sha256": digest.hexdigest().upper(), "files": file_count, "bytes": total_bytes}


def _directory_presence(path: Path) -> dict[str, bool]:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return {"exists": False}
    except OSError as exc:
        raise OperationalUpdateError("UPDATE_DIRECTORY_IDENTITY_UNKNOWN") from exc
    attributes = int(getattr(metadata, "st_file_attributes", 0))
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or stat.S_ISLNK(metadata.st_mode)
        or attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
    ):
        raise OperationalUpdateError("UPDATE_DIRECTORY_IDENTITY_UNSAFE")
    return {"exists": True}


def _copy_application_bundle(source: Path, destination: Path) -> dict[str, Any]:
    try:
        resolved = source.expanduser().resolve(strict=True)
    except OSError as exc:
        raise OperationalUpdateError("UPDATE_BUNDLE_REQUIRED") from exc
    if not resolved.is_dir() or destination.exists() or destination.is_symlink():
        raise OperationalUpdateError("UPDATE_STAGE_COLLISION_OR_INVALID")
    source_identity = _update_tree_identity(resolved)
    try:
        shutil.copytree(resolved, destination, symlinks=False)
    except OSError as exc:
        raise OperationalUpdateError("UPDATE_STAGE_COPY_FAILED") from exc
    staged_identity = _update_tree_identity(destination)
    if staged_identity != source_identity:
        raise OperationalUpdateError("UPDATE_STAGE_IDENTITY_MISMATCH")
    return staged_identity


def _runtime_database_files(path: Path) -> tuple[Path, ...]:
    captured = _database_capture_files(path)
    if captured is None:
        raise OperationalUpdateError("UPDATE_DATABASE_SIDECARS_AMBIGUOUS")
    return captured


def _verify_data_snapshot(snapshot_database: Path) -> dict[str, Any]:
    from .db import CURRENT_SCHEMA_REVISION

    try:
        uri = snapshot_database.resolve(strict=True).as_uri() + "?mode=ro"
        with closing(sqlite3.connect(uri, uri=True, timeout=5.0)) as connection:
            connection.execute("PRAGMA query_only = ON")
            quick_check = [row[0] for row in connection.execute("PRAGMA quick_check")]
            if quick_check != ["ok"]:
                raise OperationalUpdateError("UPDATE_SNAPSHOT_QUICK_CHECK_FAILED")
            if connection.execute("PRAGMA foreign_key_check").fetchall():
                raise OperationalUpdateError("UPDATE_SNAPSHOT_FOREIGN_KEY_CHECK_FAILED")
            revision_rows = connection.execute(
                "SELECT version_num FROM alembic_version ORDER BY version_num"
            ).fetchall()
            if revision_rows != [(CURRENT_SCHEMA_REVISION,)]:
                raise OperationalUpdateError("UPDATE_SNAPSHOT_SCHEMA_UNSUPPORTED")
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            if not set(_DATA_SENTINEL_TABLES).issubset(tables):
                raise OperationalUpdateError("UPDATE_SNAPSHOT_REQUIRED_TABLE_MISSING")
            columns: dict[str, set[str]] = {}
            for table in _DATA_SENTINEL_TABLES:
                rows = connection.execute(f'PRAGMA table_info("{table}")').fetchall()
                columns[table] = {str(row[1]) for row in rows}
                if "id" not in columns[table]:
                    raise OperationalUpdateError("UPDATE_SNAPSHOT_REQUIRED_COLUMN_MISSING")
            samples: dict[str, list[Any]] = {}
            counts: dict[str, int] = {}
            for table in _DATA_SENTINEL_TABLES:
                samples[table] = [
                    row[0]
                    for row in connection.execute(
                        f'SELECT id FROM "{table}" ORDER BY id LIMIT 3'
                    )
                ]
            for table in _DATA_SENTINEL_COUNT_TABLES:
                counts[table] = int(
                    connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                )
    except OperationalUpdateError:
        raise
    except (OSError, sqlite3.Error) as exc:
        raise OperationalUpdateError("UPDATE_SNAPSHOT_READ_ONLY_CHECK_FAILED") from exc
    return {
        "schema_revision": CURRENT_SCHEMA_REVISION,
        "table_columns": {table: sorted(value) for table, value in columns.items()},
        "primary_key_samples": samples,
        "aggregate_row_counts": counts,
    }


def _create_lkg_snapshot(
    paths: OperationalPaths,
    update_id: str,
    update_directory: Path,
    *,
    old_application: dict[str, Any],
) -> dict[str, Any]:
    if os.name != "nt":
        raise OperationalUpdateError("UPDATE_DATA_CAPTURE_UNSUPPORTED")
    snapshot_root = paths.data_dir / "backups" / update_id
    if _unsafe_path(snapshot_root, paths.root) or snapshot_root.exists():
        raise OperationalUpdateError("UPDATE_SNAPSHOT_COLLISION_OR_UNSAFE")
    source_db_files = _runtime_database_files(paths.database_path)
    all_sources = (paths.config_path, *source_db_files)
    sidecar_candidates = tuple(Path(f"{paths.database_path}{suffix}") for suffix in ("-wal", "-shm"))
    observed_sources = (*all_sources, *sidecar_candidates)
    before = {str(path): _update_file_identity(path) for path in observed_sources}
    if not paths.config_path.is_file() or not paths.database_path.is_file():
        raise OperationalUpdateError("UPDATE_DATA_CAPTURE_REQUIRED_FILE_MISSING")
    snapshot_root.mkdir(parents=True, exist_ok=False)
    try:
        with ExitStack() as stack:
            source_handles = {
                path: stack.enter_context(_open_exclusive_database_file(path))
                for path in all_sources
            }
            destination_for = {
                paths.config_path: snapshot_root / "config.yaml",
                paths.database_path: snapshot_root / "egp.db",
            }
            for source_path in source_db_files:
                suffix = str(source_path)[len(str(paths.database_path)) :]
                destination_for[source_path] = Path(f"{snapshot_root / 'egp.db'}{suffix}")
            for source_path, destination in destination_for.items():
                handle = source_handles[source_path]
                handle.seek(0)
                with destination.open("xb") as target:
                    shutil.copyfileobj(handle, target, length=1024 * 1024)
                    target.flush()
                    os.fsync(target.fileno())
        if {str(path): _update_file_identity(path) for path in observed_sources} != before:
            raise OperationalUpdateError("UPDATE_DATA_CHANGED_DURING_SNAPSHOT")
        for source_path, destination in destination_for.items():
            if _update_file_identity(source_path)["sha256"] != _update_file_identity(destination)["sha256"]:
                raise OperationalUpdateError("UPDATE_DATA_SNAPSHOT_IDENTITY_MISMATCH")
        data_verification = _verify_data_snapshot(snapshot_root / "egp.db")
        snapshot_db_files = _runtime_database_files(snapshot_root / "egp.db")
        snapshot_files = (snapshot_root / "config.yaml", *snapshot_db_files)
        snapshot_identities = {
            path.relative_to(paths.root).as_posix(): _update_file_identity(path)
            for path in snapshot_files
        }
        migration_receipt, migration_error = _json(paths.migration_receipt_path)
        if migration_error or migration_receipt is None:
            raise OperationalUpdateError("UPDATE_MIGRATION_RECEIPT_INVALID")
        lkg = {
            "schema_version": "qi-crawler-last-known-good-v1",
            "update_id": update_id,
            "application_generation": old_application,
            "acceptance_sha256": _sha256(paths.acceptance_path),
            "migration_receipt_sha256": _sha256(paths.migration_receipt_path),
            "database_snapshot": {
                "path": (snapshot_root / "egp.db").relative_to(paths.root).as_posix(),
                "sha256": snapshot_identities[
                    (snapshot_root / "egp.db").relative_to(paths.root).as_posix()
                ]["sha256"],
                "sidecars": {
                    path.name[len("egp.db") :]: identity
                    for path in snapshot_db_files
                    if path != snapshot_root / "egp.db"
                    for identity in (snapshot_identities[path.relative_to(paths.root).as_posix()],)
                },
                "verification": data_verification,
            },
            "config_snapshot": {
                "path": (snapshot_root / "config.yaml").relative_to(paths.root).as_posix(),
                "sha256": snapshot_identities[
                    (snapshot_root / "config.yaml").relative_to(paths.root).as_posix()
                ]["sha256"],
            },
            "snapshot_artifacts": snapshot_identities,
            "runtime_verification_reference": "NOT_PERFORMED",
            "restore_rehearsal_status": "NOT_PERFORMED",
            "database_restore_authorized": False,
        }
        lkg_path = update_directory / "last_known_good.json"
        _write_json_durable(lkg_path, lkg)
        if {
            path.relative_to(paths.root).as_posix(): _update_file_identity(path)
            for path in snapshot_files
        } != snapshot_identities:
            raise OperationalUpdateError("UPDATE_DATA_SNAPSHOT_CHANGED_AFTER_SEAL")
        return lkg
    except OperationalUpdateError:
        raise
    except (OSError, sqlite3.Error) as exc:
        raise OperationalUpdateError("UPDATE_DATA_SNAPSHOT_FAILED") from exc


def _query_process_image_path(process_id: int) -> str:
    if os.name != "nt":
        raise OperationalUpdateError("UPDATE_PROCESS_IMAGE_QUERY_UNSUPPORTED")
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    open_process = kernel32.OpenProcess
    open_process.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    open_process.restype = wintypes.HANDLE
    query_path = kernel32.QueryFullProcessImageNameW
    query_path.argtypes = (wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD))
    query_path.restype = wintypes.BOOL
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = (wintypes.HANDLE,)
    close_handle.restype = wintypes.BOOL
    handle = open_process(0x1000, False, process_id)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        raise OperationalUpdateError("UPDATE_PROCESS_IMAGE_PATH_UNKNOWN")
    try:
        buffer = ctypes.create_unicode_buffer(32768)
        length = wintypes.DWORD(len(buffer))
        if not query_path(handle, 0, buffer, ctypes.byref(length)):
            raise OperationalUpdateError("UPDATE_PROCESS_IMAGE_PATH_UNKNOWN")
        return buffer.value
    finally:
        close_handle(handle)


def _restart_manager_resource_holders(resources: tuple[Path, ...]) -> tuple[tuple[int, str], ...]:
    if os.name != "nt":
        raise OperationalUpdateError("UPDATE_RESOURCE_CENSUS_UNSUPPORTED")
    from ctypes import wintypes

    class FILETIME(ctypes.Structure):
        _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]

    class RM_UNIQUE_PROCESS(ctypes.Structure):
        _fields_ = [("dwProcessId", wintypes.DWORD), ("ProcessStartTime", FILETIME)]

    class RM_PROCESS_INFO(ctypes.Structure):
        _fields_ = [
            ("Process", RM_UNIQUE_PROCESS),
            ("strAppName", wintypes.WCHAR * 256),
            ("strServiceShortName", wintypes.WCHAR * 64),
            ("ApplicationType", ctypes.c_int),
            ("AppStatus", wintypes.ULONG),
            ("TSSessionId", wintypes.DWORD),
            ("bRestartable", wintypes.BOOL),
        ]

    rstrtmgr = ctypes.WinDLL("Rstrtmgr", use_last_error=True)
    start_session = rstrtmgr.RmStartSession
    start_session.argtypes = (ctypes.POINTER(wintypes.DWORD), wintypes.DWORD, wintypes.LPWSTR)
    start_session.restype = wintypes.DWORD
    register = rstrtmgr.RmRegisterResources
    register.argtypes = (
        wintypes.DWORD,
        wintypes.UINT,
        ctypes.POINTER(wintypes.LPCWSTR),
        wintypes.UINT,
        ctypes.c_void_p,
        wintypes.UINT,
        ctypes.POINTER(wintypes.LPCWSTR),
    )
    register.restype = wintypes.DWORD
    get_list = rstrtmgr.RmGetList
    get_list.argtypes = (
        wintypes.DWORD,
        ctypes.POINTER(wintypes.UINT),
        ctypes.POINTER(wintypes.UINT),
        ctypes.POINTER(RM_PROCESS_INFO),
        ctypes.POINTER(wintypes.DWORD),
    )
    get_list.restype = wintypes.DWORD
    end_session = rstrtmgr.RmEndSession
    end_session.argtypes = (wintypes.DWORD,)
    end_session.restype = wintypes.DWORD

    session = wintypes.DWORD()
    key = ctypes.create_unicode_buffer(33)
    result = start_session(ctypes.byref(session), 0, key)
    if result != 0:
        raise OperationalUpdateError("UPDATE_RESOURCE_CENSUS_FAILED")
    try:
        files = (wintypes.LPCWSTR * len(resources))(*(str(path) for path in resources))
        result = register(session, len(resources), files, 0, None, 0, None)
        if result != 0:
            raise OperationalUpdateError("UPDATE_RESOURCE_CENSUS_FAILED")
        needed = wintypes.UINT()
        count = wintypes.UINT()
        reasons = wintypes.DWORD()
        result = get_list(session, ctypes.byref(needed), ctypes.byref(count), None, ctypes.byref(reasons))
        if result not in (0, 234):  # ERROR_SUCCESS / ERROR_MORE_DATA
            raise OperationalUpdateError("UPDATE_RESOURCE_CENSUS_FAILED")
        if needed.value == 0:
            return ()
        entries = (RM_PROCESS_INFO * needed.value)()
        count = wintypes.UINT(needed.value)
        result = get_list(session, ctypes.byref(needed), ctypes.byref(count), entries, ctypes.byref(reasons))
        if result != 0:
            raise OperationalUpdateError("UPDATE_RESOURCE_CENSUS_FAILED")
        holders: list[tuple[int, str]] = []
        for entry in entries[: count.value]:
            process_id = int(entry.Process.dwProcessId)
            if process_id == os.getpid():
                continue
            holders.append((process_id, _query_process_image_path(process_id)))
        return tuple(holders)
    finally:
        end_session(session)


def _assert_no_old_runtime_holders(
    paths: OperationalPaths,
    additional_executables: tuple[Path, ...] = (),
) -> None:
    if os.name != "nt":
        raise OperationalUpdateError("UPDATE_RESOURCE_CENSUS_UNSUPPORTED")
    from . import operational_release

    exact_executables = {paths.executable, *additional_executables}
    normalized_executables = {
        os.path.normcase(str(path.resolve(strict=False))).casefold()
        for path in exact_executables
    }
    try:
        process_records = operational_release._cim_process_census()
    except operational_release.OperationalReleaseError as exc:
        raise OperationalUpdateError("UPDATE_PROCESS_CENSUS_FAILED") from exc
    for record in process_records:
        executable = record.get("ExecutablePath")
        if not isinstance(executable, str) or not executable.strip():
            raise OperationalUpdateError("UPDATE_PROCESS_PATH_AUTHORITY_UNKNOWN")
        if os.path.normcase(executable).casefold() in normalized_executables:
            raise OperationalUpdateError("UPDATE_OLD_PROCESS_PRESENT")

    data_paths = [paths.config_path, paths.database_path]
    data_paths.extend(Path(f"{paths.database_path}{suffix}") for suffix in ("-wal", "-shm"))
    resources = tuple(path for path in (*exact_executables, *data_paths) if path.exists())
    holders = _restart_manager_resource_holders(resources)
    if holders:
        raise OperationalUpdateError("UPDATE_RUNTIME_RESOURCE_HELD")


def _hold_data_resources(paths: OperationalPaths, stack: ExitStack) -> None:
    database_files = _runtime_database_files(paths.database_path)
    for path in (paths.config_path, *database_files):
        try:
            stack.enter_context(_open_exclusive_database_file(path))
        except OSError as exc:
            raise OperationalUpdateError("UPDATE_DATA_RESOURCE_HELD") from exc


def _intent(
    journal_path: Path,
    action: str,
    before: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    _append_update_transition(
        journal_path,
        kind="INTENT",
        action=action,
        before=before,
        expected=expected,
    )


def _confirm(
    journal_path: Path,
    action: str,
    before: dict[str, Any],
    expected: dict[str, Any],
    observed: dict[str, Any],
) -> None:
    _append_update_transition(
        journal_path,
        kind="CONFIRMED",
        action=action,
        before=before,
        expected=expected,
        observed=observed,
    )


def _mutate_and_confirm(
    journal_path: Path,
    *,
    action: str,
    before: dict[str, Any],
    expected: dict[str, Any],
    mutate: Callable[[], None],
    observe: Callable[[], dict[str, Any]],
    recovery: bool = False,
) -> dict[str, Any]:
    """Apply one operation only between durable intent and observed confirmation."""
    intent_kind = "RECOVERY_INTENT" if recovery else "INTENT"
    confirm_kind = "RECOVERY_CONFIRMED" if recovery else "CONFIRMED"
    _append_update_transition(
        journal_path,
        kind=intent_kind,
        action=action,
        before=before,
        expected=expected,
    )
    mutate()
    observed = observe()
    if observed != expected:
        raise OperationalUpdateError("UPDATE_MUTATION_OBSERVATION_MISMATCH")
    _append_update_transition(
        journal_path,
        kind=confirm_kind,
        action=action,
        before=before,
        expected=expected,
        observed=observed,
    )
    return observed


def _terminalize_update(
    journal_path: Path,
    *,
    result: str,
    error_code: str | None = None,
) -> None:
    state, error = _json(journal_path)
    if error or state is None:
        raise OperationalUpdateError("UPDATE_JOURNAL_INVALID")
    paths = _paths_for_journal(journal_path)
    state = _validate_update_journal(
        paths, state, state.get("update_id"), journal_path=journal_path
    )
    if result not in _UPDATE_TERMINAL_RESULTS:
        raise OperationalUpdateError("UPDATE_TERMINAL_RESULT_INVALID")
    pending_action = state.get("pending_action")
    if pending_action:
        transitions = state.get("transitions")
        if not isinstance(transitions, list) or not transitions:
            raise OperationalUpdateError("UPDATE_TRANSITION_HISTORY_INVALID")
        pending = transitions[-1]
        if pending_action in {"ROTATE_ACTIVE_TO_OLD", "ROTATE_STAGE_TO_ACTIVE", "COMMIT_ACCEPTANCE"}:
            raise OperationalUpdateError("UPDATE_ACTIVE_MUTATION_UNCONFIRMED")
        _append_update_transition(
            journal_path,
            kind="ATTEMPT_FAILED_RECOVERED",
            action=str(pending_action),
            before=pending.get("before", {}),
            expected=pending.get("expected", {}),
            observed={"preserved": True, "error_code": error_code},
        )
        state, error = _json(journal_path)
        if error or state is None:
            raise OperationalUpdateError("UPDATE_JOURNAL_INVALID")
    before = {"phase": state.get("phase"), "result": state.get("result")}
    expected = {"phase": "TERMINAL", "result": result}
    _intent(journal_path, "FINALIZE_UPDATE", before, expected)
    observed = {"phase": "TERMINAL", "result": result, "error_code": error_code}
    if error_code:
        observed["error_code"] = error_code
    _confirm(journal_path, "FINALIZE_UPDATE", before, expected, observed)


def _mark_recovery_required(journal_path: Path, error_code: str) -> None:
    """Persist a hold state while retaining any unconfirmed transition intent."""
    state, error = _json(journal_path)
    if error or state is None or state.get("result") in _UPDATE_TERMINAL_RESULTS:
        raise OperationalUpdateError("UPDATE_JOURNAL_INVALID")
    paths = _paths_for_journal(journal_path)
    _validate_update_journal(
        paths, state, state.get("update_id"), journal_path=journal_path
    )
    state["phase"] = "RECOVERY_REQUIRED"
    state["result"] = "RECOVERY_REQUIRED"
    state["recovery_error_code"] = error_code
    _write_json_durable(journal_path, state)


def _clear_active_marker(
    paths: OperationalPaths,
    journal_path: Path,
    update_id: str,
    *,
    recovery: bool = False,
) -> None:
    marker_path = paths.control_root / "update_marker.json"
    marker, error = _json(marker_path)
    if error or marker is None or marker.get("update_id") != update_id:
        raise OperationalUpdateError("UPDATE_MARKER_IDENTITY_MISMATCH")
    _mutate_and_confirm(
        journal_path,
        action="RECOVERY_CLEAR_ACTIVE_MARKER" if recovery else "CLEAR_ACTIVE_MARKER",
        before={"marker": _data_file_identity(marker_path)},
        expected={"marker": {"exists": False}},
        mutate=marker_path.unlink,
        observe=lambda: {"marker": _data_file_identity(marker_path)},
        recovery=recovery,
    )


def _relative_root_path(paths: OperationalPaths, relative: object) -> Path:
    if not isinstance(relative, str) or not relative or "\x00" in relative:
        raise OperationalUpdateError("UPDATE_RECOVERY_PATH_UNSAFE")
    components = re.split(r"[\\/]", relative)
    candidate = paths.root / relative
    if (
        any(component in {"", ".", ".."} for component in components)
        or Path(relative).is_absolute()
        or Path(relative).drive
        or Path(relative).root
        or _unsafe_path(candidate, paths.root)
    ):
        raise OperationalUpdateError("UPDATE_RECOVERY_PATH_UNSAFE")
    return candidate


def _preflight_operational_paths(paths: OperationalPaths) -> None:
    """Prove root-local lock/control paths before lock acquisition can write."""
    try:
        root_metadata = paths.root.lstat()
    except OSError as exc:
        raise OperationalUpdateError("UPDATE_ROOT_PATH_UNSAFE") from exc
    root_attributes = int(getattr(root_metadata, "st_file_attributes", 0))
    if (
        not stat.S_ISDIR(root_metadata.st_mode)
        or stat.S_ISLNK(root_metadata.st_mode)
        or root_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
        or _unsafe_path(paths.root, paths.root)
    ):
        raise OperationalUpdateError("UPDATE_ROOT_PATH_UNSAFE")

    if paths != operational_paths(paths.root):
        raise OperationalUpdateError("UPDATE_CONTROL_PATH_UNSAFE")
    safety_paths = (
        (paths.control_root, "UPDATE_CONTROL_PATH_UNSAFE", True),
        (paths.control_root / "update.lock", "UPDATE_CONTROL_PATH_UNSAFE", False),
        (paths.control_root / "updates", "UPDATE_CONTROL_PATH_UNSAFE", True),
        (paths.control_root / "update_marker.json", "UPDATE_CONTROL_PATH_UNSAFE", False),
        (paths.acceptance_path, "UPDATE_CONTROL_PATH_UNSAFE", False),
        (paths.migration_receipt_path, "UPDATE_CONTROL_PATH_UNSAFE", False),
        (paths.application_root, "UPDATE_APPLICATION_PATH_UNSAFE", True),
        (paths.root / ".update", "UPDATE_TRANSIENT_PATH_UNSAFE", True),
        (paths.data_root, "UPDATE_DATA_PATH_UNSAFE", True),
        (paths.data_dir, "UPDATE_DATA_PATH_UNSAFE", True),
        (paths.config_path, "UPDATE_DATA_PATH_UNSAFE", False),
        (paths.database_path, "UPDATE_DATA_PATH_UNSAFE", False),
        (Path(f"{paths.database_path}-wal"), "UPDATE_DATA_PATH_UNSAFE", False),
        (Path(f"{paths.database_path}-shm"), "UPDATE_DATA_PATH_UNSAFE", False),
        (paths.data_dir / "backups", "UPDATE_DATA_PATH_UNSAFE", True),
    )
    for path, error_code, directory_expected in safety_paths:
        if _unsafe_path(path, paths.root):
            raise OperationalUpdateError(error_code)
        if path.exists():
            metadata = path.lstat()
            attributes = int(getattr(metadata, "st_file_attributes", 0))
            if (
                stat.S_ISLNK(metadata.st_mode)
                or attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
                or stat.S_ISDIR(metadata.st_mode) != directory_expected
            ):
                raise OperationalUpdateError(error_code)
    lock_path = paths.control_root / "update.lock"
    if _windows_path_length(lock_path) > _MAX_UPDATE_PATH_LENGTH:
        raise OperationalUpdateError("UPDATE_PATH_TOO_LONG")


def _existing_ancestor(path: Path) -> Path:
    current = path
    while not current.exists():
        parent = current.parent
        if parent == current:
            raise OperationalUpdateError("UPDATE_ROTATION_VOLUME_UNKNOWN")
        current = parent
    return current


def _preflight_rotation_volume(paths: OperationalPaths, expected: dict[str, Path]) -> None:
    try:
        root_device = paths.root.stat().st_dev
        for path in (
            paths.application_root,
            expected["old"].parent,
            paths.control_root / "updates",
            paths.data_dir / "backups",
        ):
            if _existing_ancestor(path).stat().st_dev != root_device:
                raise OperationalUpdateError("UPDATE_ROTATION_VOLUME_MISMATCH")
    except OSError as exc:
        raise OperationalUpdateError("UPDATE_ROTATION_VOLUME_UNKNOWN") from exc


def _preflight_update_generation(
    paths: OperationalPaths,
    bundle: Path,
    update_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Bound projected generation and journal paths before attempt creation."""
    if not _safe_update_id(update_id):
        raise OperationalUpdateError("UPDATE_ID_INVALID")
    expected = _expected_update_paths(paths, update_id)
    if _unsafe_path(bundle, bundle):
        raise OperationalUpdateError("UPDATE_BUNDLE_PATH_UNSAFE")
    bundle_metadata = bundle.lstat()
    bundle_attributes = int(getattr(bundle_metadata, "st_file_attributes", 0))
    if (
        not stat.S_ISDIR(bundle_metadata.st_mode)
        or stat.S_ISLNK(bundle_metadata.st_mode)
        or bundle_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
    ):
        raise OperationalUpdateError("UPDATE_BUNDLE_PATH_UNSAFE")

    for path in (expected["old"].parent, paths.control_root / "updates" / update_id, expected["snapshot_root"]):
        if _unsafe_path(path, paths.root):
            raise OperationalUpdateError("UPDATE_PATH_UNSAFE")
        if path.exists() or path.is_symlink():
            raise OperationalUpdateError("UPDATE_ID_COLLISION_OR_UNSAFE")

    projected_roots = (
        paths.application_root,
        expected["stage"],
        expected["old"],
        expected["failed"],
    )
    current_identity = _update_tree_identity(
        paths.application_root,
        projected_roots=projected_roots,
    )
    bundle_identity = _update_tree_identity(bundle, projected_roots=projected_roots)
    journal_files = (
        expected["journal"],
        expected["acceptance_snapshot"],
        expected["lkg_manifest"],
        paths.control_root / "update_marker.json",
        paths.acceptance_path,
        expected["snapshot_root"] / "egp.db",
        expected["snapshot_root"] / "config.yaml",
        expected["snapshot_root"] / "egp.db-wal",
        expected["snapshot_root"] / "egp.db-shm",
    )
    path_budget_targets = (
        *journal_files,
        *(
            _durable_json_temp_path(path)
            for path in (
                expected["journal"],
                expected["lkg_manifest"],
                paths.control_root / "update_marker.json",
                paths.acceptance_path,
            )
        ),
    )
    if any(
        _windows_path_length(path) > _MAX_UPDATE_PATH_LENGTH
        for path in path_budget_targets
    ):
        raise OperationalUpdateError("UPDATE_PATH_TOO_LONG")
    _preflight_rotation_volume(paths, expected)
    return current_identity, bundle_identity


def _generation_identity(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    return _update_tree_identity(path)


def _transition_for(state: dict[str, Any], action: str) -> dict[str, Any] | None:
    transitions = state.get("transitions")
    if not isinstance(transitions, list):
        raise OperationalUpdateError("UPDATE_TRANSITION_HISTORY_INVALID")
    return next(
        (entry for entry in reversed(transitions) if entry.get("action") == action),
        None,
    )


def _reconcile_interrupted_rotation(
    journal_path: Path,
    paths: OperationalPaths,
    state: dict[str, Any],
    active: Path,
    old: Path,
    stage: Path,
) -> dict[str, Any]:
    pending_action = state.get("pending_action")
    if pending_action is None:
        return state
    transition = _transition_for(state, str(pending_action))
    if transition is None or transition.get("kind") not in {"INTENT", "RECOVERY_INTENT"}:
        raise OperationalUpdateError("UPDATE_TRANSITION_HISTORY_INVALID")
    before = transition.get("before")
    expected = transition.get("expected")
    if not isinstance(before, dict) or not isinstance(expected, dict):
        raise OperationalUpdateError("UPDATE_TRANSITION_HISTORY_INVALID")
    action = str(pending_action)
    if action == "ROTATE_ACTIVE_TO_OLD":
        observed = {"active": _generation_identity(active), "old": _generation_identity(old)}
    elif action == "RECOVERY_RESTORE_OLD_ACTIVE":
        observed = {"old": _generation_identity(old), "active": _generation_identity(active)}
    elif action in {"ROTATE_STAGE_TO_ACTIVE", "RECOVERY_MOVE_ACTIVE_TO_FAILED"}:
        failed = old.parent / "failed"
        source = stage if action == "ROTATE_STAGE_TO_ACTIVE" else active
        destination = active if action == "ROTATE_STAGE_TO_ACTIVE" else failed
        observed = {
            "stage": _generation_identity(source),
            "active": _generation_identity(destination),
        } if action == "ROTATE_STAGE_TO_ACTIVE" else {
            "active": _generation_identity(source),
            "failed": _generation_identity(destination),
        }
    elif action in {"COMMIT_ACCEPTANCE", "RECOVERY_RESTORE_ACCEPTANCE"}:
        observed = {"acceptance": _data_file_identity(paths.acceptance_path)}
    elif action in {"SET_ACTIVE_MARKER", "CLEAR_ACTIVE_MARKER", "RECOVERY_CLEAR_ACTIVE_MARKER"}:
        observed = {
            "marker": _data_file_identity(paths.control_root / "update_marker.json")
        }
    else:
        raise OperationalUpdateError("UPDATE_PENDING_ACTION_UNSUPPORTED_FOR_RECOVERY")
    if observed == expected:
        kind = (
            "RECOVERY_CONFIRMED"
            if transition.get("kind") == "RECOVERY_INTENT"
            else "CONFIRMED"
        )
    elif observed == before:
        kind = "ATTEMPT_FAILED_RECOVERED"
        observed = {"preserved": True, "actual": observed}
    else:
        raise OperationalUpdateError("UPDATE_RECOVERY_AMBIGUOUS")
    return _append_update_transition(
        journal_path,
        kind=kind,
        action=action,
        before=before,
        expected=expected,
        observed=observed,
    )


def _verify_update_data_unchanged(
    paths: OperationalPaths, state: dict[str, Any]
) -> None:
    before = state.get("source_data_before")
    if not isinstance(before, dict):
        raise OperationalUpdateError("UPDATE_DATA_IDENTITY_MISSING")
    expected_paths = {
        str(path)
        for path in (
            paths.config_path,
            paths.database_path,
            Path(f"{paths.database_path}-wal"),
            Path(f"{paths.database_path}-shm"),
        )
    }
    if set(before) != expected_paths:
        raise OperationalUpdateError("UPDATE_DATA_IDENTITY_PATHS_INVALID")
    after = {name: _data_file_identity(Path(name)) for name in before}
    if after != before:
        raise OperationalUpdateError("UPDATE_SOURCE_DATA_CHANGED")
    if _sha256(paths.migration_receipt_path) != state.get("migration_receipt_sha256"):
        raise OperationalUpdateError("UPDATE_MIGRATION_RECEIPT_CHANGED")


def _verify_lkg_binding(
    paths: OperationalPaths,
    state: dict[str, Any],
    update_id: str,
    old_path: Path,
) -> None:
    expected = _expected_update_paths(paths, update_id)
    if not _safe_update_id(update_id) or old_path != expected["old"]:
        raise OperationalUpdateError("UPDATE_LKG_MANIFEST_INVALID")
    manifest_path = _relative_root_path(paths, state.get("lkg_manifest_path", ""))
    if manifest_path != expected["lkg_manifest"]:
        raise OperationalUpdateError("UPDATE_LKG_MANIFEST_INVALID")
    manifest, error = _json(manifest_path)
    if not isinstance(manifest, dict):
        raise OperationalUpdateError("UPDATE_LKG_MANIFEST_INVALID")
    if (
        error
        or manifest.get("schema_version") != "qi-crawler-last-known-good-v1"
        or manifest.get("update_id") != update_id
        or manifest.get("application_generation")
        != {
            "path": old_path.relative_to(paths.root).as_posix(),
            "identity": state.get("application", {}).get("old"),
        }
    ):
        raise OperationalUpdateError("UPDATE_LKG_MANIFEST_INVALID")

    database = manifest.get("database_snapshot")
    config = manifest.get("config_snapshot")
    artifacts = manifest.get("snapshot_artifacts")
    if (
        not isinstance(database, dict)
        or not isinstance(config, dict)
        or not isinstance(artifacts, dict)
        or not artifacts
    ):
        raise OperationalUpdateError("UPDATE_LKG_SNAPSHOT_BINDING_MISSING")

    snapshot_root = expected["snapshot_root"]
    if _unsafe_path(snapshot_root, paths.root) or not _directory_presence(snapshot_root)["exists"]:
        raise OperationalUpdateError("UPDATE_LKG_SNAPSHOT_PATH_UNSAFE")
    expected_database = snapshot_root / "egp.db"
    expected_config = snapshot_root / "config.yaml"
    database_relative = snapshot_root.relative_to(paths.root).as_posix() + "/egp.db"
    config_relative = snapshot_root.relative_to(paths.root).as_posix() + "/config.yaml"
    if (
        not _strict_relative_path(paths, database.get("path"), expected_database)
        or not _strict_relative_path(paths, config.get("path"), expected_config)
    ):
        raise OperationalUpdateError("UPDATE_LKG_SNAPSHOT_PATH_UNSAFE")

    sidecars = database.get("sidecars")
    if not isinstance(sidecars, dict) or set(sidecars) - {"-wal", "-shm"}:
        raise OperationalUpdateError("UPDATE_LKG_SNAPSHOT_BINDING_INVALID")
    expected_relatives = {database_relative, config_relative}
    expected_relatives.update(f"{database_relative}{suffix}" for suffix in sidecars)
    if set(artifacts) != expected_relatives or any(
        not isinstance(relative, str) or not isinstance(identity, dict)
        for relative, identity in artifacts.items()
    ):
        raise OperationalUpdateError("UPDATE_LKG_SNAPSHOT_BINDING_INVALID")
    if (
        database.get("sha256") != artifacts[database_relative].get("sha256")
        or config.get("sha256") != artifacts[config_relative].get("sha256")
    ):
        raise OperationalUpdateError("UPDATE_LKG_SNAPSHOT_BINDING_INVALID")
    for suffix, identity in sidecars.items():
        relative = f"{database_relative}{suffix}"
        if identity != artifacts[relative]:
            raise OperationalUpdateError("UPDATE_LKG_SNAPSHOT_BINDING_INVALID")

    expected_names = {"egp.db", "config.yaml", *(f"egp.db{suffix}" for suffix in sidecars)}
    try:
        actual_entries = tuple(snapshot_root.iterdir())
    except OSError as exc:
        raise OperationalUpdateError("UPDATE_LKG_SNAPSHOT_PATH_UNSAFE") from exc
    if {entry.name for entry in actual_entries} != expected_names or any(
        not entry.is_file() or _unsafe_path(entry, paths.root) for entry in actual_entries
    ):
        raise OperationalUpdateError("UPDATE_LKG_SNAPSHOT_BINDING_INVALID")

    for relative, expected_identity in artifacts.items():
        artifact = _relative_root_path(paths, relative)
        if _update_file_identity(artifact) != expected_identity:
            raise OperationalUpdateError("UPDATE_LKG_SNAPSHOT_IDENTITY_MISMATCH")


def recover_operational_application_update(paths: OperationalPaths) -> dict[str, Any]:
    """Reconcile exact app/acceptance identities; never mutate operational Data."""
    if os.name != "nt":
        raise OperationalUpdateError("UPDATE_WINDOWS_PROTECTION_REQUIRED")
    _preflight_operational_paths(paths)
    lock = _ExclusiveFileLock(paths.control_root / "update.lock")
    try:
        lock.acquire()
    except (MaintenanceBusy, OSError) as exc:
        raise OperationalUpdateError("UPDATE_SINGLETON_BUSY") from exc
    try:
        updates_root = paths.control_root / "updates"
        marker_path = paths.control_root / "update_marker.json"
        states = _load_update_journals(paths)
        marker_exists = marker_path.exists()
        marker, marker_error = _json(marker_path) if marker_exists else (None, None)
        if marker_exists and (marker_error or not isinstance(marker, dict)):
            raise OperationalUpdateError("UPDATE_MARKER_INVALID")
        unresolved_ids = {
            candidate_id
            for candidate_id, candidate_state in states.items()
            if candidate_state.get("result") not in _UPDATE_TERMINAL_RESULTS
            or candidate_state.get("pending_action") is not None
        }
        if marker is not None:
            update_id = marker.get("update_id")
            if (
                marker.get("schema_version") != UPDATE_POINTER_SCHEMA
                or not _safe_update_id(update_id)
                or marker.get("journal") != f"updates/{update_id}/state.json"
            ):
                raise OperationalUpdateError("UPDATE_MARKER_INVALID")
            if update_id not in states:
                raise OperationalUpdateError("UPDATE_JOURNAL_REQUIRED")
            if unresolved_ids - {update_id}:
                raise OperationalUpdateError("UPDATE_JOURNAL_ORPHAN")
            journal_path = updates_root / update_id / "state.json"
            state = states[update_id]
        else:
            if len(unresolved_ids) != 1:
                raise OperationalUpdateError("UPDATE_RECOVERY_TARGET_AMBIGUOUS")
            update_id = next(iter(unresolved_ids))
            journal_path = updates_root / update_id / "state.json"
            state = states[update_id]
        if state.get("result") in _UPDATE_TERMINAL_RESULTS:
            if marker is None and state.get("pending_action") is None:
                return {"update_id": update_id, "result": state["result"]}
            if marker is not None and state.get("pending_action") is None:
                _clear_active_marker(paths, journal_path, update_id, recovery=True)
                return {"update_id": update_id, "result": state["result"]}

        app = state.get("application")
        acceptance = state.get("acceptance")
        if not isinstance(app, dict) or not isinstance(acceptance, dict):
            raise OperationalUpdateError("UPDATE_JOURNAL_INVALID")
        active = _relative_root_path(paths, str(app.get("active_path", "")))
        old = _relative_root_path(paths, str(app.get("old_path", "")))
        stage = _relative_root_path(paths, str(app.get("stage_path", "")))
        expected_paths = _expected_update_paths(paths, update_id)
        if (
            active != expected_paths["active"]
            or old != expected_paths["old"]
            or stage != expected_paths["stage"]
            or _relative_root_path(paths, app.get("failed_path")) != expected_paths["failed"]
        ):
            raise OperationalUpdateError("UPDATE_RECOVERY_PATH_UNSAFE")
        state = _reconcile_interrupted_rotation(journal_path, paths, state, active, old, stage)
        if state.get("pending_action") is not None:
            raise OperationalUpdateError("UPDATE_RECOVERY_PENDING_ACTION")
        if state.get("result") in _UPDATE_TERMINAL_RESULTS:
            if marker is None:
                return {"update_id": update_id, "result": state["result"]}
            _clear_active_marker(paths, journal_path, update_id, recovery=True)
            return {"update_id": update_id, "result": state["result"]}

        old_identity = app.get("old")
        if not isinstance(old_identity, dict):
            raise OperationalUpdateError("UPDATE_JOURNAL_INVALID")
        old_acceptance_sha = acceptance.get("old_sha256")
        active_identity = _generation_identity(active)
        current_acceptance_sha = _update_file_identity(paths.acceptance_path).get("sha256")
        if (
            state.get("first_mutation_at") is None
            and active_identity == old_identity
            and current_acceptance_sha == old_acceptance_sha
        ):
            _verify_update_data_unchanged(paths, state)
            _terminalize_update(journal_path, result="FAILED_NO_MUTATION")
            if marker is not None:
                _clear_active_marker(paths, journal_path, update_id, recovery=True)
            return {"update_id": update_id, "result": "FAILED_NO_MUTATION"}

        stage_rotation = _transition_for(state, "ROTATE_STAGE_TO_ACTIVE")
        new_identity = (
            stage_rotation.get("expected", {}).get("active")
            if isinstance(stage_rotation, dict)
            else None
        )
        if not isinstance(new_identity, dict):
            copy_transition = _transition_for(state, "COPY_BUNDLE_TO_STAGE")
            new_identity = (
                copy_transition.get("expected", {}).get("stage")
                if isinstance(copy_transition, dict)
                else None
            )
        if not isinstance(new_identity, dict):
            raise OperationalUpdateError("UPDATE_NEW_APPLICATION_IDENTITY_MISSING")
        new_acceptance_transition = _transition_for(state, "COMMIT_ACCEPTANCE")
        new_acceptance_sha = None
        if isinstance(new_acceptance_transition, dict):
            new_acceptance_sha = (
                new_acceptance_transition.get("expected", {})
                .get("acceptance", {})
                .get("sha256")
            )
        snapshot_path = _relative_root_path(paths, str(acceptance.get("snapshot_path", "")))
        snapshot_identity = _update_file_identity(snapshot_path)
        if (
            snapshot_identity.get("sha256") != old_acceptance_sha
            or not isinstance(old_acceptance_sha, str)
        ):
            raise OperationalUpdateError("UPDATE_ACCEPTANCE_SNAPSHOT_INVALID")
        if marker is not None and marker.get("update_id") != update_id:
            raise OperationalUpdateError("UPDATE_MARKER_IDENTITY_MISMATCH")
        _verify_update_data_unchanged(paths, state)

        active_identity = _generation_identity(active)
        old_generation_identity = _generation_identity(old)
        stage_identity = _generation_identity(stage)
        failed = old.parent / "failed"
        failed_identity = _generation_identity(failed)
        current_acceptance_sha = _update_file_identity(paths.acceptance_path).get("sha256")
        if current_acceptance_sha not in {old_acceptance_sha, new_acceptance_sha}:
            raise OperationalUpdateError("UPDATE_ACCEPTANCE_IDENTITY_AMBIGUOUS")

        _verify_lkg_binding(paths, state, update_id, old)

        from . import operational_release

        if (
            active_identity == new_identity
            and stage_identity == {"exists": False}
            and old_generation_identity == old_identity
            and failed_identity == {"exists": False}
            and current_acceptance_sha == new_acceptance_sha
        ):
            try:
                validated = operational_release.validate_operational_acceptance(
                    paths.executable, immutable_database=True
                )
                if validated.get("source_git_sha") != operational_release._bundle_identity(
                    active
                ).get("source_git_sha"):
                    raise OperationalUpdateError("UPDATE_FORWARD_RECOVERY_IDENTITY_MISMATCH")
                _assert_no_old_runtime_holders(paths, (old / "QI-Crawler.exe",))
                _verify_update_data_unchanged(paths, state)
                _terminalize_update(journal_path, result="RECOVERY_COMPLETE")
                if marker is not None:
                    _clear_active_marker(paths, journal_path, update_id, recovery=True)
                return {"update_id": update_id, "result": "RECOVERY_COMPLETE"}
            except operational_release.OperationalReleaseError:
                pass

        rollback_allowed = (
            active_identity == old_identity
            and old_generation_identity == {"exists": False}
        ) or (
            active_identity == {"exists": False}
            and old_generation_identity == old_identity
        ) or (
            active_identity == new_identity
            and old_generation_identity == old_identity
            and stage_identity == {"exists": False}
            and failed_identity in ({"exists": False}, new_identity)
        )
        if not rollback_allowed or current_acceptance_sha not in {
            old_acceptance_sha,
            new_acceptance_sha,
        }:
            raise OperationalUpdateError("UPDATE_RECOVERY_AMBIGUOUS")

        old_payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
        needs_app_mutation = active_identity != old_identity
        needs_acceptance_mutation = current_acceptance_sha != old_acceptance_sha
        if needs_app_mutation or needs_acceptance_mutation:
            with ExitStack() as resource_stack:
                _hold_data_resources(paths, resource_stack)
                _assert_no_old_runtime_holders(paths, (old / "QI-Crawler.exe",))
                if active_identity == new_identity:
                    if failed_identity != {"exists": False}:
                        raise OperationalUpdateError("UPDATE_RECOVERY_FAILED_PATH_COLLISION")
                    _mutate_and_confirm(
                        journal_path,
                        action="RECOVERY_MOVE_ACTIVE_TO_FAILED",
                        before={"active": new_identity, "failed": {"exists": False}},
                        expected={"active": {"exists": False}, "failed": new_identity},
                        mutate=lambda: os.replace(active, failed),
                        observe=lambda: {
                            "active": _generation_identity(active),
                            "failed": _generation_identity(failed),
                        },
                        recovery=True,
                    )
                if _generation_identity(active) == {"exists": False}:
                    _assert_no_old_runtime_holders(paths, (old / "QI-Crawler.exe",))
                    _mutate_and_confirm(
                        journal_path,
                        action="RECOVERY_RESTORE_OLD_ACTIVE",
                        before={"old": old_identity, "active": {"exists": False}},
                        expected={"old": {"exists": False}, "active": old_identity},
                        mutate=lambda: os.replace(old, active),
                        observe=lambda: {
                            "old": _generation_identity(old),
                            "active": _generation_identity(active),
                        },
                        recovery=True,
                    )
                if needs_acceptance_mutation:
                    _mutate_and_confirm(
                        journal_path,
                        action="RECOVERY_RESTORE_ACCEPTANCE",
                        before={"acceptance": _data_file_identity(paths.acceptance_path)},
                        expected={"acceptance": _json_payload_file_identity(old_payload)},
                        mutate=lambda: _write_json_durable(paths.acceptance_path, old_payload),
                        observe=lambda: {
                            "acceptance": _data_file_identity(paths.acceptance_path)
                        },
                        recovery=True,
                    )

        if _generation_identity(active) != old_identity:
            raise OperationalUpdateError("UPDATE_ROLLBACK_IDENTITY_MISMATCH")
        if _update_file_identity(paths.acceptance_path).get("sha256") != old_acceptance_sha:
            raise OperationalUpdateError("UPDATE_ROLLBACK_ACCEPTANCE_MISMATCH")
        _verify_update_data_unchanged(paths, state)
        _terminalize_update(journal_path, result="ROLLED_BACK")
        if marker is not None:
            _clear_active_marker(paths, journal_path, update_id, recovery=True)
        return {"update_id": update_id, "result": "ROLLED_BACK"}
    finally:
        lock.release()


def apply_operational_application_update(
    paths: OperationalPaths,
    bundle_path: Path | str,
    *,
    confirmed: bool,
) -> dict[str, Any]:
    """Stage and rotate only the app generation; never write or restore Data."""
    if confirmed is not True:
        raise OperationalUpdateError("UPDATE_CONFIRMATION_REQUIRED")
    if os.name != "nt":
        raise OperationalUpdateError("UPDATE_WINDOWS_PROTECTION_REQUIRED")
    from . import operational_release

    _preflight_operational_paths(paths)
    lock = _ExclusiveFileLock(paths.control_root / "update.lock")
    try:
        lock.acquire()
    except (MaintenanceBusy, OSError) as exc:
        raise OperationalUpdateError("UPDATE_SINGLETON_BUSY") from exc

    journal_path: Path | None = None
    update_id = uuid4().hex
    transient = paths.root / ".update" / update_id
    stage = transient / "stage"
    old_generation = transient / "old"
    current_before: dict[str, Any] | None = None
    acceptance_before_sha: str | None = None
    try:
        assert_operational_startup_allowed(paths)
        try:
            operational_release.validate_operational_acceptance(
                paths.executable, immutable_database=True
            )
        except operational_release.OperationalReleaseError as exc:
            raise OperationalUpdateError("UPDATE_CURRENT_ACCEPTANCE_INVALID") from exc
        bundle_input = Path(bundle_path).expanduser()
        try:
            bundle_metadata = bundle_input.lstat()
        except OSError as exc:
            raise OperationalUpdateError("UPDATE_BUNDLE_REQUIRED") from exc
        bundle_attributes = int(getattr(bundle_metadata, "st_file_attributes", 0))
        if (
            not stat.S_ISDIR(bundle_metadata.st_mode)
            or stat.S_ISLNK(bundle_metadata.st_mode)
            or bundle_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
        ):
            raise OperationalUpdateError("UPDATE_BUNDLE_PATH_UNSAFE")
        new_bundle = bundle_input.resolve(strict=True)
        try:
            new_identity = operational_release._bundle_identity(new_bundle)
        except operational_release.OperationalReleaseError as exc:
            raise OperationalUpdateError("UPDATE_BUNDLE_INVALID") from exc
        if (
            new_identity.get("version") != operational_release.__version__
            or new_identity.get("release_channel") != operational_release.OPERATIONAL_RELEASE_CHANNEL
        ):
            raise OperationalUpdateError("UPDATE_BUNDLE_VERSION_OR_CHANNEL_INVALID")

        current_before, bundle_tree_identity = _preflight_update_generation(
            paths, new_bundle, update_id
        )
        acceptance_before_bytes = paths.acceptance_path.read_bytes()
        acceptance_before_sha = hashlib.sha256(acceptance_before_bytes).hexdigest().upper()
        migration_bytes = paths.migration_receipt_path.read_bytes()
        migration_before_sha = hashlib.sha256(migration_bytes).hexdigest().upper()
        data_candidates = (
            paths.config_path,
            paths.database_path,
            Path(f"{paths.database_path}-wal"),
            Path(f"{paths.database_path}-shm"),
        )
        source_data_before = {str(path): _data_file_identity(path) for path in data_candidates}

        update_directory = paths.control_root / "updates" / update_id
        if update_directory.exists() or _unsafe_path(update_directory, paths.root):
            raise OperationalUpdateError("UPDATE_ID_COLLISION_OR_UNSAFE")
        update_directory.mkdir(parents=True, exist_ok=False)
        journal_path = update_directory / "state.json"
        acceptance_snapshot_path = update_directory / "acceptance.before.json"
        state = {
            "schema_version": UPDATE_STATE_SCHEMA,
            "update_id": update_id,
            "phase": "PREPARING",
            "result": None,
            "first_mutation_at": None,
            "pending_action": None,
            "transitions": [],
            "application": {
                "old": current_before,
                "new": new_identity,
                "active_path": str(paths.application_root.relative_to(paths.root)),
                "old_path": str(old_generation.relative_to(paths.root)),
                "stage_path": str(stage.relative_to(paths.root)),
                "failed_path": str((transient / "failed").relative_to(paths.root)),
            },
            "acceptance": {
                "old_sha256": acceptance_before_sha,
                "snapshot_path": str(acceptance_snapshot_path.relative_to(paths.root)),
            },
            "migration_receipt_sha256": migration_before_sha,
            "source_data_before": source_data_before,
            "lkg_manifest_path": str(
                (update_directory / "last_known_good.json").relative_to(paths.root)
            ),
        }
        _write_json_durable(journal_path, state)

        def capture_acceptance_snapshot() -> None:
            with acceptance_snapshot_path.open("xb") as stream:
                stream.write(acceptance_before_bytes)
                stream.flush()
                os.fsync(stream.fileno())

        _mutate_and_confirm(
            journal_path,
            action="CAPTURE_ACCEPTANCE_SNAPSHOT",
            before={"snapshot": {"exists": False}},
            expected={"snapshot": {"sha256": acceptance_before_sha}},
            mutate=capture_acceptance_snapshot,
            observe=lambda: {
                "snapshot": {
                    "sha256": _update_file_identity(acceptance_snapshot_path).get(
                        "sha256"
                    )
                }
            },
        )

        marker_path = paths.control_root / "update_marker.json"
        marker_before = _data_file_identity(marker_path)
        marker_payload = {
            "schema_version": UPDATE_POINTER_SCHEMA,
            "update_id": update_id,
            "journal": f"updates/{update_id}/state.json",
        }
        _mutate_and_confirm(
            journal_path,
            action="SET_ACTIVE_MARKER",
            before={"marker": marker_before},
            expected={"marker": _json_payload_file_identity(marker_payload)},
            mutate=lambda: _write_json_durable(marker_path, marker_payload),
            observe=lambda: {"marker": _data_file_identity(marker_path)},
        )

        before_app_identity = _update_tree_identity(paths.application_root)
        lkg_manifest: dict[str, Any] = {}
        lkg_expected = {
            "snapshot_id": update_id,
            "lkg_schema": "qi-crawler-last-known-good-v1",
        }

        def capture_lkg() -> None:
            lkg_manifest.update(
                _create_lkg_snapshot(
                    paths,
                    update_id,
                    update_directory,
                    old_application={
                        "path": old_generation.relative_to(paths.root).as_posix(),
                        "identity": before_app_identity,
                    },
                )
            )

        _mutate_and_confirm(
            journal_path,
            action="CAPTURE_LKG_SNAPSHOT",
            before={"application": before_app_identity, "data": source_data_before},
            expected=lkg_expected,
            mutate=capture_lkg,
            observe=lambda: {
                "snapshot_id": update_id,
                "lkg_schema": _json(update_directory / "last_known_good.json")[0].get(
                    "schema_version"
                ),
            },
        )

        transient_root = transient.parent
        stage_before = {
            "transient_root": _directory_presence(transient_root),
            "transient": _directory_presence(transient),
            "stage": {"exists": False},
        }
        stage_expected = {
            "transient_root": {"exists": True},
            "transient": {"exists": True},
            "stage": bundle_tree_identity,
        }
        staged_identity: dict[str, Any] = {}

        def copy_to_stage() -> None:
            transient.mkdir(parents=True, exist_ok=False)
            staged_identity.update(_copy_application_bundle(new_bundle, stage))

        _mutate_and_confirm(
            journal_path,
            action="COPY_BUNDLE_TO_STAGE",
            before=stage_before,
            expected=stage_expected,
            mutate=copy_to_stage,
            observe=lambda: {
                "transient_root": _directory_presence(transient_root),
                "transient": _directory_presence(transient),
                "stage": _update_tree_identity(stage),
            },
        )
        if staged_identity != bundle_tree_identity:
            raise OperationalUpdateError("UPDATE_STAGE_IDENTITY_MISMATCH")
        state, error = _json(journal_path)
        if error or state is None:
            raise OperationalUpdateError("UPDATE_JOURNAL_INVALID")
        state["phase"] = "STAGED"
        state["application"]["new"] = staged_identity
        _write_json_durable(journal_path, state)

        with ExitStack() as resource_stack:
            _hold_data_resources(paths, resource_stack)
            _assert_no_old_runtime_holders(paths)
            # A second census closes the known old-binary appearance window
            # between initial census and the first directory rotation.
            _assert_no_old_runtime_holders(paths)
            active_identity = _update_tree_identity(paths.application_root)
            if active_identity != current_before or old_generation.exists():
                raise OperationalUpdateError("UPDATE_PRECOMMIT_IDENTITY_CHANGED")
            _mutate_and_confirm(
                journal_path,
                action="ROTATE_ACTIVE_TO_OLD",
                before={"active": active_identity, "old": {"exists": False}},
                expected={"active": {"exists": False}, "old": current_before},
                mutate=lambda: os.replace(paths.application_root, old_generation),
                observe=lambda: {
                    "active": {"exists": False},
                    "old": _update_tree_identity(old_generation),
                },
            )
            staged_identity = _update_tree_identity(stage)
            _mutate_and_confirm(
                journal_path,
                action="ROTATE_STAGE_TO_ACTIVE",
                before={"stage": staged_identity, "active": {"exists": False}},
                expected={"stage": {"exists": False}, "active": staged_identity},
                mutate=lambda: os.replace(stage, paths.application_root),
                observe=lambda: {
                    "stage": {"exists": False},
                    "active": _update_tree_identity(paths.application_root),
                },
            )
            active_new_identity = _update_tree_identity(paths.application_root)
            state, error = _json(journal_path)
            if error or state is None:
                raise OperationalUpdateError("UPDATE_JOURNAL_INVALID")
            state["phase"] = "NEW_APP_ACTIVE"
            _write_json_durable(journal_path, state)

            _assert_no_old_runtime_holders(paths, (old_generation / "QI-Crawler.exe",))
            new_bundle_identity = operational_release._bundle_identity(paths.application_root)
            migration_receipt = operational_release._read_json(
                paths.migration_receipt_path, "OPERATIONAL_MIGRATION_RECEIPT_INVALID"
            )
            new_acceptance = operational_release._operational_acceptance_payload(
                paths, new_bundle_identity, migration_receipt
            )
            acceptance_before = _data_file_identity(paths.acceptance_path)
            acceptance_expected = _json_payload_file_identity(new_acceptance)
            _mutate_and_confirm(
                journal_path,
                action="COMMIT_ACCEPTANCE",
                before={"acceptance": acceptance_before},
                expected={"acceptance": acceptance_expected},
                mutate=lambda: _write_json_durable(paths.acceptance_path, new_acceptance),
                observe=lambda: {"acceptance": _data_file_identity(paths.acceptance_path)},
            )

        _assert_no_old_runtime_holders(paths, (old_generation / "QI-Crawler.exe",))
        try:
            validated_acceptance = operational_release.validate_operational_acceptance(
                paths.executable, immutable_database=True
            )
        except operational_release.OperationalReleaseError as exc:
            raise OperationalUpdateError("UPDATE_POSTCHECK_ACCEPTANCE_FAILED") from exc
        data_after = {str(path): _data_file_identity(path) for path in data_candidates}
        if data_after != source_data_before:
            raise OperationalUpdateError("UPDATE_SOURCE_DATA_CHANGED")
        if _sha256(paths.migration_receipt_path) != migration_before_sha:
            raise OperationalUpdateError("UPDATE_MIGRATION_RECEIPT_CHANGED")
        if validated_acceptance.get("source_git_sha") != new_identity.get("source_git_sha"):
            raise OperationalUpdateError("UPDATE_POSTCHECK_APPLICATION_MISMATCH")
        _terminalize_update(journal_path, result="COMPLETE")
        _clear_active_marker(paths, journal_path, update_id)
        return {
            "update_id": update_id,
            "result": "COMPLETE",
            "journal_path": str(journal_path),
            "lkg_manifest_path": str(update_directory / "last_known_good.json"),
            "old_generation_path": str(old_generation),
            "application_identity": active_new_identity,
            "acceptance": validated_acceptance,
        }
    except Exception as exc:
        if journal_path is not None and journal_path.exists():
            try:
                state, state_error = _json(journal_path)
                if state_error or state is None:
                    raise OperationalUpdateError("UPDATE_JOURNAL_INVALID")
                if state.get("result") is None:
                    active_identity = (
                        _update_tree_identity(paths.application_root)
                        if paths.application_root.is_dir()
                        else {"exists": False}
                    )
                    acceptance_identity = _update_file_identity(paths.acceptance_path)
                    unchanged_before_mutation = (
                        state.get("first_mutation_at") is None
                        and active_identity == current_before
                        and acceptance_identity.get("sha256") == acceptance_before_sha
                    )
                    if unchanged_before_mutation:
                        if state.get("pending_action") in {
                            "ROTATE_ACTIVE_TO_OLD",
                            "ROTATE_STAGE_TO_ACTIVE",
                            "COMMIT_ACCEPTANCE",
                        }:
                            try:
                                state = _reconcile_interrupted_rotation(
                                    journal_path,
                                    paths,
                                    state,
                                    paths.application_root,
                                    old_generation,
                                    stage,
                                )
                            except OperationalUpdateError as reconcile_exc:
                                _mark_recovery_required(
                                    journal_path, str(reconcile_exc)
                                )
                                raise OperationalUpdateError(
                                    "UPDATE_RECOVERY_STATE_UNCERTAIN"
                                ) from reconcile_exc
                        if (
                            state.get("first_mutation_at") is not None
                            or state.get("pending_action") is not None
                        ):
                            _mark_recovery_required(journal_path, str(exc))
                            raise OperationalUpdateError(
                                "UPDATE_RECOVERY_STATE_UNCERTAIN"
                            ) from exc
                        _terminalize_update(
                            journal_path,
                            result="FAILED_NO_MUTATION",
                            error_code=str(exc),
                        )
                        marker_path = paths.control_root / "update_marker.json"
                        if marker_path.exists():
                            _clear_active_marker(paths, journal_path, update_id)
                    else:
                        _mark_recovery_required(journal_path, str(exc))
            except (OSError, OperationalUpdateError) as state_exc:
                raise OperationalUpdateError("UPDATE_RECOVERY_STATE_UNCERTAIN") from state_exc
        if isinstance(exc, OperationalUpdateError):
            raise
        raise OperationalUpdateError("UPDATE_FAILED") from exc
    finally:
        lock.release()


@dataclass(frozen=True, slots=True)
class ArtifactState:
    """One observed artifact and its phase-aware state."""

    name: str
    path: str
    state: str


@dataclass(frozen=True, slots=True)
class EvidenceIdentity:
    """A stable identity value used by the classification."""

    name: str
    value: str


@dataclass(frozen=True, slots=True)
class OperationalUpdateObservation:
    """Immutable observation result; deliberately contains no recovery actions."""

    classification: str
    observed_phase: str
    reasons: tuple[str, ...]
    evidence_identities: tuple[EvidenceIdentity, ...]
    input_stable: bool
    artifacts: tuple[ArtifactState, ...]

    @property
    def artifact_states(self) -> Mapping[str, str]:
        return MappingProxyType({item.name: item.state for item in self.artifacts})


@dataclass(frozen=True, slots=True)
class _FileIdentity:
    path: str
    kind: str
    size: int
    sha256: str
    link_target: str
    error: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(path.read_bytes().decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None, "INVALID"
    return (value, None) if isinstance(value, dict) else (None, "INVALID")


def _file_identity(path: Path, root: Path) -> _FileIdentity:
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError:
        relative = str(path)
    try:
        metadata = path.lstat()
        attributes = int(getattr(metadata, "st_file_attributes", 0))
        if stat.S_ISLNK(metadata.st_mode) or attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            target = os.readlink(path) if stat.S_ISLNK(metadata.st_mode) else "REPARSE_POINT"
            return _FileIdentity(relative, "link", 0, "", str(target), "")
        if stat.S_ISDIR(metadata.st_mode):
            return _FileIdentity(relative, "directory", 0, "", "", "")
        if stat.S_ISREG(metadata.st_mode):
            return _FileIdentity(relative, "file", metadata.st_size, _sha256(path), "", "")
        return _FileIdentity(relative, "other", metadata.st_size, "", "", "")
    except FileNotFoundError:
        return _FileIdentity(relative, "missing", 0, "", "", "")
    except OSError as exc:
        return _FileIdentity(relative, "error", 0, "", "", type(exc).__name__)


def _snapshot(paths: tuple[Path, ...], root: Path) -> tuple[_FileIdentity, ...]:
    return tuple(_file_identity(path, root) for path in paths)


def _observation_paths(paths: OperationalPaths) -> tuple[Path, ...]:
    journal_path = paths.control_root / "update_journal.json"
    observed = (
        paths.control_root / "active_update.json",
        journal_path,
        paths.control_root / "update_receipt.json",
        paths.executable,
        paths.config_path,
        paths.database_path,
        Path(f"{paths.database_path}-wal"),
        Path(f"{paths.database_path}-shm"),
    )
    journal, error = _json(journal_path)
    if error or journal is None or not isinstance(journal.get("backup"), dict):
        return observed
    backup_value = journal["backup"].get("path")
    if not isinstance(backup_value, str) or not backup_value:
        return observed
    backup_path = Path(os.path.abspath(paths.control_root / backup_value))
    return observed + (backup_path,) if not _unsafe_path(backup_path, paths.root) else observed


def _unsafe_path(path: Path, root: Path) -> bool:
    try:
        relative_parts = path.relative_to(root).parts
    except ValueError:
        return True
    if any(part in {"", ".", ".."} for part in relative_parts):
        return True
    current = root
    try:
        if current.exists() or current.is_symlink():
            metadata = current.lstat()
            attributes = int(getattr(metadata, "st_file_attributes", 0))
            if stat.S_ISLNK(metadata.st_mode) or attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                return True
        for part in relative_parts:
            current /= part
            if not current.exists() and not current.is_symlink():
                continue
            metadata = current.lstat()
            attributes = int(getattr(metadata, "st_file_attributes", 0))
            if stat.S_ISLNK(metadata.st_mode) or attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                return True
    except OSError:
        return True
    return False


def _read_database_paths(
    path: Path,
    *,
    immutable: bool,
    timeout: float = 5.0,
    deadline: float | None = None,
) -> tuple[dict[str, str] | None, str | None]:
    uri = path.as_uri() + "?mode=ro"
    if immutable:
        uri += "&immutable=1"
    try:
        remaining = timeout if deadline is None else max(0.0, deadline - time.monotonic())
        with closing(sqlite3.connect(uri, uri=True, timeout=min(timeout, remaining))) as connection:
            connection.execute("PRAGMA query_only = ON")
            if deadline is not None:
                connection.set_progress_handler(
                    lambda: int(time.monotonic() >= deadline), 1000
                )
            rows = connection.execute("SELECT id, stored_path FROM documents ORDER BY id").fetchall()
    except (OSError, sqlite3.Error):
        if deadline is not None and time.monotonic() >= deadline:
            return None, "DATABASE_SNAPSHOT_TIMEOUT"
        return None, "DATABASE_UNREADABLE"
    if deadline is not None and time.monotonic() >= deadline:
        return None, "DATABASE_SNAPSHOT_TIMEOUT"
    return {str(row[0]): str(row[1]) for row in rows}, None


def _database_capture_files(path: Path) -> tuple[Path, ...] | None:
    sidecars: dict[str, Path] = {}
    for suffix in ("-wal", "-shm", "-journal"):
        sidecar = Path(f"{path}{suffix}")
        try:
            metadata = sidecar.lstat()
        except FileNotFoundError:
            continue
        except OSError:
            return None
        attributes = int(getattr(metadata, "st_file_attributes", 0))
        if (
            not stat.S_ISREG(metadata.st_mode)
            or stat.S_ISLNK(metadata.st_mode)
            or attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
        ):
            return None
        sidecars[suffix] = sidecar
    if "-journal" in sidecars or ("-wal" in sidecars) != ("-shm" in sidecars):
        return None
    if "-wal" in sidecars:
        return path, sidecars["-wal"], sidecars["-shm"]
    return (path,)


def _open_exclusive_database_file(path: Path):
    if os.name != "nt":
        raise NotImplementedError
    import msvcrt
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    create_file.restype = wintypes.HANDLE
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = (wintypes.HANDLE,)
    close_handle.restype = wintypes.BOOL
    handle = create_file(
        str(path),
        0x80000000,  # GENERIC_READ
        0,  # No sharing: SQLite clients cannot open or replace the source file.
        None,
        3,  # OPEN_EXISTING
        0x80,  # FILE_ATTRIBUTE_NORMAL
        None,
    )
    if handle == wintypes.HANDLE(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        descriptor = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
    except BaseException:
        close_handle(handle)
        raise
    try:
        return os.fdopen(descriptor, "rb")
    except BaseException:
        os.close(descriptor)
        raise


def _database_file_state(
    path: Path,
    deadline: float,
    *,
    stream=None,
    header_size: int = 100,
) -> tuple[bytes, int, str] | None:
    try:
        before = path.lstat()
        attributes = int(getattr(before, "st_file_attributes", 0))
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_ISLNK(before.st_mode)
            or attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
        ):
            return None
        digest = hashlib.sha256()
        header = bytearray()
        size = 0
        context = path.open("rb") if stream is None else nullcontext(stream)
        with context as source:
            source.seek(0)
            while chunk := source.read(1024 * 1024):
                if time.monotonic() >= deadline:
                    raise TimeoutError
                if len(header) < header_size:
                    header.extend(chunk[: header_size - len(header)])
                digest.update(chunk)
                size += len(chunk)
        after = path.lstat()
    except TimeoutError:
        raise
    except OSError:
        return None
    if (
        len(header) < header_size
        or size != before.st_size
        or (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    ):
        return None
    return bytes(header), size, digest.hexdigest().upper()


def _copy_database(path: Path, destination: Path, deadline: float, *, source_stream=None) -> None:
    context = path.open("rb") if source_stream is None else nullcontext(source_stream)
    with context as source, destination.open("wb") as target:
        source.seek(0)
        while chunk := source.read(1024 * 1024):
            if time.monotonic() >= deadline:
                raise TimeoutError
            target.write(chunk)
    if time.monotonic() >= deadline:
        raise TimeoutError


def _database_paths(path: Path, *, active_wal: bool) -> tuple[dict[str, str] | None, str | None]:
    if not active_wal:
        return _read_database_paths(path, immutable=True)
    if os.name != "nt":
        return None, "DATABASE_CAPTURE_UNSUPPORTED"
    deadline = time.monotonic() + 5.0
    source_paths = _database_capture_files(path)
    if source_paths is None:
        return None, "DATABASE_CAPTURE_UNPROVEN"
    try:
        with ExitStack() as stack:
            source_streams = {}
            for source_path in source_paths:
                try:
                    source_streams[source_path] = stack.enter_context(
                        _open_exclusive_database_file(source_path)
                    )
                except OSError as exc:
                    if getattr(exc, "winerror", None) in (32, 33):
                        return None, "DATABASE_CAPTURE_BUSY"
                    if getattr(exc, "winerror", None) == 2:
                        return None, "DATABASE_CHANGED_DURING_SNAPSHOT"
                    return None, "DATABASE_UNREADABLE"

            if _database_capture_files(path) != source_paths:
                return None, "DATABASE_CHANGED_DURING_SNAPSHOT"

            def source_state(source_path: Path):
                header_size = (
                    100
                    if source_path == path
                    else 32
                    if source_path.name.endswith("-wal")
                    else 1
                )
                return _database_file_state(
                    source_path,
                    deadline,
                    stream=source_streams[source_path],
                    header_size=header_size,
                )

            source_before = tuple(source_state(source_path) for source_path in source_paths)
            if source_before[0] is None:
                return None, "DATABASE_UNREADABLE"
            if any(state is None for state in source_before[1:]):
                return None, "DATABASE_CAPTURE_UNPROVEN"
            database_header = source_before[0][0]
            if database_header[:16] != b"SQLite format 3\x00":
                return None, "DATABASE_UNREADABLE"
            has_wal = len(source_paths) == 3
            if has_wal:
                if database_header[18:20] != b"\x02\x02":
                    return None, "DATABASE_CAPTURE_UNPROVEN"
                wal_state, shm_state = source_before[1:]
                wal_header, wal_size = wal_state[:2]
                wal_page_size = int.from_bytes(wal_header[8:12], "big")
                database_page_size = int.from_bytes(database_header[16:18], "big")
                if database_page_size == 1:
                    database_page_size = 65_536
                frame_size = _WAL_FRAME_HEADER_SIZE + wal_page_size
                if (
                    wal_header[:4] not in (b"\x37\x7f\x06\x82", b"\x37\x7f\x06\x83")
                    or int.from_bytes(wal_header[4:8], "big") != _WAL_FORMAT_VERSION
                    or not 512 <= wal_page_size <= 65_536
                    or wal_page_size & (wal_page_size - 1)
                    or wal_page_size != database_page_size
                    or wal_size < _WAL_HEADER_SIZE + frame_size
                    or (wal_size - _WAL_HEADER_SIZE) % frame_size
                    or shm_state[1] < _SHM_REGION_SIZE
                    or shm_state[1] % _SHM_REGION_SIZE
                ):
                    return None, "DATABASE_CAPTURE_UNPROVEN"
            elif database_header[18:20] != b"\x01\x01":
                return None, "DATABASE_CAPTURE_UNPROVEN"

            with tempfile.TemporaryDirectory(prefix="qi-update-observation-") as directory:
                snapshot = Path(directory) / path.name
                snapshot_paths = tuple(
                    snapshot
                    if source_path == path
                    else Path(f"{snapshot}{source_path.name[len(path.name):]}")
                    for source_path in source_paths
                )
                for source_path, snapshot_path in zip(source_paths, snapshot_paths):
                    _copy_database(
                        source_path,
                        snapshot_path,
                        deadline,
                        source_stream=source_streams[source_path],
                    )

                if _database_capture_files(path) != source_paths:
                    return None, "DATABASE_CHANGED_DURING_SNAPSHOT"
                source_after_copy = tuple(source_state(source_path) for source_path in source_paths)
                snapshot_states = tuple(
                    _database_file_state(
                        snapshot_path,
                        deadline,
                        header_size=100 if source_path == path else 32 if source_path.name.endswith("-wal") else 1,
                    )
                    for source_path, snapshot_path in zip(source_paths, snapshot_paths)
                )
                if any(state is None for state in (*source_after_copy, *snapshot_states)):
                    return None, "DATABASE_UNREADABLE"
                if source_after_copy != source_before or snapshot_states != source_before:
                    return None, "DATABASE_CHANGED_DURING_SNAPSHOT"

                rows, error = _read_database_paths(
                    snapshot,
                    immutable=False,
                    timeout=1.0,
                    deadline=deadline,
                )
                if _database_capture_files(path) != source_paths:
                    return None, "DATABASE_CHANGED_DURING_SNAPSHOT"
                source_after_verification = tuple(
                    source_state(source_path) for source_path in source_paths
                )
                if source_after_verification != source_before:
                    return None, "DATABASE_CHANGED_DURING_SNAPSHOT"
                return rows, error
    except TimeoutError:
        return None, "DATABASE_SNAPSHOT_TIMEOUT"
    except OSError:
        return None, "DATABASE_UNREADABLE"

def _artifact(name: str, path: Path, state: str) -> ArtifactState:
    return ArtifactState(name=name, path=str(path), state=state)


def _hold(
    phase: str,
    reasons: list[str],
    identities: list[EvidenceIdentity],
    artifacts: list[ArtifactState],
) -> tuple[str, str, list[str], list[EvidenceIdentity], list[ArtifactState]]:
    return "RECOVERY_REQUIRED_AMBIGUOUS", phase, reasons, identities, artifacts


def _evaluate(
    paths: OperationalPaths,
) -> tuple[
    str,
    str,
    list[str],
    list[EvidenceIdentity],
    list[ArtifactState],
    tuple[Path, ...],
]:
    root = paths.root
    marker_path = paths.control_root / "active_update.json"
    journal_path = paths.control_root / "update_journal.json"
    receipt_path = paths.control_root / "update_receipt.json"
    fixed = (
        marker_path,
        journal_path,
        receipt_path,
        paths.executable,
        paths.config_path,
        paths.database_path,
        Path(f"{paths.database_path}-wal"),
        Path(f"{paths.database_path}-shm"),
    )
    artifacts: list[ArtifactState] = []
    identities: list[EvidenceIdentity] = []

    if not marker_path.exists():
        artifacts.append(_artifact("marker", marker_path, "PHASE_VALID_ABSENCE"))
        if journal_path.exists() or receipt_path.exists():
            return (*_hold("IDLE", ["ORPHANED_UPDATE_EVIDENCE"], identities, artifacts), fixed)
        return "NO_ACTIVE_UPDATE", "IDLE", [], identities, artifacts, fixed

    marker, marker_error = _json(marker_path)
    if marker_error or marker is None:
        artifacts.append(_artifact("marker", marker_path, "PRESENT_INVALID"))
        return (*_hold("UNKNOWN", ["MARKER_INVALID"], identities, artifacts), fixed)
    artifacts.append(_artifact("marker", marker_path, "PRESENT_VALID"))
    if marker.get("schema_version") != MARKER_SCHEMA:
        return (*_hold("UNKNOWN", ["MARKER_SCHEMA_UNSUPPORTED"], identities, artifacts), fixed)
    update_id = marker.get("update_id")
    if not isinstance(update_id, str) or not update_id:
        return (*_hold("UNKNOWN", ["MARKER_INVALID"], identities, artifacts), fixed)
    identities.append(EvidenceIdentity("update_id", update_id))
    if marker.get("journal") != journal_path.name:
        return (*_hold("UNKNOWN", ["JOURNAL_PATH_UNSAFE"], identities, artifacts), fixed)
    if not journal_path.is_file():
        artifacts.append(_artifact("journal", journal_path, "REQUIRED_ARTIFACT_MISSING"))
        return (*_hold("UNKNOWN", ["JOURNAL_REQUIRED"], identities, artifacts), fixed)

    journal, journal_error = _json(journal_path)
    if journal_error or journal is None:
        artifacts.append(_artifact("journal", journal_path, "PRESENT_INVALID"))
        return (*_hold("UNKNOWN", ["JOURNAL_INVALID"], identities, artifacts), fixed)
    artifacts.append(_artifact("journal", journal_path, "PRESENT_VALID"))
    if journal.get("schema_version") != JOURNAL_SCHEMA:
        return (*_hold("UNKNOWN", ["JOURNAL_SCHEMA_UNSUPPORTED"], identities, artifacts), fixed)
    if journal.get("update_id") != update_id:
        return (*_hold("UNKNOWN", ["UPDATE_ID_MISMATCH"], identities, artifacts), fixed)
    phase = journal.get("phase")
    if phase not in _PHASES:
        return (*_hold("UNKNOWN", ["PHASE_UNSUPPORTED"], identities, artifacts), fixed)

    application = journal.get("application")
    config = journal.get("config")
    database = journal.get("database")
    backup_spec = journal.get("backup")
    if not all(isinstance(value, dict) for value in (application, config, database, backup_spec)):
        return (*_hold(phase, ["JOURNAL_CONTRACT_INVALID"], identities, artifacts), fixed)

    backup_value = backup_spec.get("path")
    if not isinstance(backup_value, str) or not backup_value:
        return (*_hold(phase, ["BACKUP_PATH_UNSAFE"], identities, artifacts), fixed)
    backup_path = Path(os.path.abspath(paths.control_root / backup_value))
    observed = fixed + (backup_path,)
    if _unsafe_path(backup_path, root):
        return (*_hold(phase, ["BACKUP_PATH_UNSAFE"], identities, artifacts), observed)

    reasons: list[str] = []
    expected_new = phase in _NEW_IDENTITY_PHASES
    app_sha = _file_identity(paths.executable, root).sha256
    config_sha = _file_identity(paths.config_path, root).sha256
    expected_app = application.get("new_sha256" if expected_new else "old_sha256")
    expected_config = config.get("new_sha256" if expected_new else "old_sha256")
    identities.extend(
        (EvidenceIdentity("application_sha256", app_sha), EvidenceIdentity("config_sha256", config_sha))
    )
    if not app_sha or app_sha != expected_app:
        reasons.append("APPLICATION_IDENTITY_MISMATCH")
    if not config_sha or config_sha != expected_config:
        reasons.append("CONFIG_IDENTITY_MISMATCH")

    active_rows, database_error = _database_paths(paths.database_path, active_wal=True)
    old_rows = database.get("old_paths")
    new_rows = database.get("new_paths")
    if database_error:
        reasons.append(database_error)
        db_state = "UNKNOWN"
    elif active_rows == old_rows:
        db_state = "OLD"
    elif active_rows == new_rows:
        db_state = "NEW"
    else:
        db_state = "MIXED_OR_UNKNOWN"
    identities.append(EvidenceIdentity("database_state", db_state))
    expected_db = "NEW" if expected_new else "OLD"
    if db_state != expected_db:
        reasons.append("DATABASE_STATE_MIXED_OR_UNKNOWN")

    if phase in _BACKUP_PHASES:
        if not backup_path.is_file():
            artifacts.append(_artifact("backup", backup_path, "REQUIRED_ARTIFACT_MISSING"))
            reasons.append("BACKUP_REQUIRED")
        else:
            backup_sha = _file_identity(backup_path, root).sha256
            identities.append(EvidenceIdentity("backup_sha256", backup_sha))
            if not backup_sha or backup_sha != backup_spec.get("sha256"):
                artifacts.append(_artifact("backup", backup_path, "IDENTITY_MISMATCH"))
                reasons.append("BACKUP_IDENTITY_MISMATCH")
            else:
                backup_rows, backup_error = _database_paths(backup_path, active_wal=False)
                if backup_error or backup_rows != backup_spec.get("baseline_paths") or backup_rows != old_rows:
                    artifacts.append(_artifact("backup", backup_path, "IDENTITY_MISMATCH"))
                    reasons.append("BACKUP_BASELINE_MISMATCH")
                else:
                    artifacts.append(_artifact("backup", backup_path, "PRESENT_VALID"))
    else:
        artifacts.append(_artifact("backup", backup_path, "PHASE_VALID_ABSENCE"))

    if phase in _RECEIPT_PHASES:
        if not receipt_path.is_file():
            artifacts.append(_artifact("receipt", receipt_path, "REQUIRED_ARTIFACT_MISSING"))
            reasons.append("RECEIPT_REQUIRED")
        else:
            receipt, receipt_error = _json(receipt_path)
            if receipt_error or receipt is None:
                artifacts.append(_artifact("receipt", receipt_path, "PRESENT_INVALID"))
                reasons.append("RECEIPT_INVALID")
            elif receipt.get("schema_version") != RECEIPT_SCHEMA:
                artifacts.append(_artifact("receipt", receipt_path, "UNSUPPORTED_STATE"))
                reasons.append("RECEIPT_SCHEMA_UNSUPPORTED")
            elif receipt.get("update_id") != update_id:
                artifacts.append(_artifact("receipt", receipt_path, "IDENTITY_MISMATCH"))
                reasons.append("RECEIPT_UPDATE_ID_MISMATCH")
            else:
                artifacts.append(_artifact("receipt", receipt_path, "PRESENT_VALID"))
                if receipt.get("application_sha256") != application.get("new_sha256"):
                    reasons.append("RECEIPT_APPLICATION_MISMATCH")
                if receipt.get("config_sha256") != config.get("new_sha256"):
                    reasons.append("RECEIPT_CONFIG_MISMATCH")
                if receipt.get("database_state") != "NEW":
                    reasons.append("RECEIPT_DATABASE_MISMATCH")
    else:
        artifacts.append(_artifact("receipt", receipt_path, "PHASE_VALID_ABSENCE"))

    if reasons:
        return (*_hold(phase, list(dict.fromkeys(reasons)), identities, artifacts), observed)
    return _CLASSIFICATIONS[phase], phase, [], identities, artifacts, observed


def classify_operational_update_state(
    paths: OperationalPaths,
    *,
    observation_hook: Callable[[str], None] | None = None,
) -> OperationalUpdateObservation:
    """Observe update evidence twice and classify it without mutating operational state."""

    initial_paths = _observation_paths(paths)
    before = _snapshot(initial_paths, paths.root)
    classification, phase, reasons, identities, artifacts, _ = _evaluate(paths)
    if observation_hook is not None:
        observation_hook("after_read")
    after = _snapshot(initial_paths, paths.root)
    stable = before == after
    if not stable:
        classification = "OBSERVATION_UNSTABLE"
        reasons = list(dict.fromkeys([*reasons, "INPUT_CHANGED_DURING_OBSERVATION"]))
    return OperationalUpdateObservation(
        classification=classification,
        observed_phase=phase,
        reasons=tuple(reasons),
        evidence_identities=tuple(identities),
        input_stable=stable,
        artifacts=tuple(artifacts),
    )


def assert_operational_startup_allowed(paths: OperationalPaths) -> None:
    """Fail closed when a root-local app update is active or ambiguous."""
    _preflight_operational_paths(paths)
    marker_path = paths.control_root / "update_marker.json"
    updates_root = paths.control_root / "updates"
    transient_root = paths.root / ".update"
    if _unsafe_path(marker_path, paths.root) or _unsafe_path(updates_root, paths.root):
        raise OperationalUpdateError("UPDATE_CONTROL_PATH_UNSAFE")
    if _unsafe_path(transient_root, paths.root):
        raise OperationalUpdateError("UPDATE_TRANSIENT_PATH_UNSAFE")

    states = _load_update_journals(paths)
    try:
        transient_entries = tuple(transient_root.iterdir()) if transient_root.exists() else ()
    except OSError as exc:
        raise OperationalUpdateError("UPDATE_TRANSIENT_STATE_UNKNOWN") from exc

    for entry in transient_entries:
        if (
            not entry.is_dir()
            or entry.is_symlink()
            or _unsafe_path(entry, paths.root)
            or entry.name not in states
        ):
            raise OperationalUpdateError("UPDATE_ORPHAN_TRANSIENT_GENERATION")
        try:
            children = tuple(entry.iterdir())
        except OSError as exc:
            raise OperationalUpdateError("UPDATE_TRANSIENT_STATE_UNKNOWN") from exc
        for child in children:
            if (
                child.name not in {"stage", "old", "failed"}
                or not child.is_dir()
                or child.is_symlink()
                or _unsafe_path(child, paths.root)
            ):
                raise OperationalUpdateError("UPDATE_TRANSIENT_GENERATION_INVALID")
        if states[entry.name].get("result") not in _UPDATE_TERMINAL_RESULTS:
            raise OperationalUpdateError("UPDATE_RECOVERY_REQUIRED")

    if not marker_path.exists():
        if any(
            state.get("result") not in _UPDATE_TERMINAL_RESULTS
            or state.get("pending_action") is not None
            for state in states.values()
        ):
            raise OperationalUpdateError("UPDATE_JOURNAL_ORPHAN")
        return

    if not marker_path.is_file():
        raise OperationalUpdateError("UPDATE_MARKER_INVALID")
    marker, marker_error = _json(marker_path)
    if marker_error or not isinstance(marker, dict):
        raise OperationalUpdateError("UPDATE_MARKER_INVALID")
    update_id = marker.get("update_id")
    if (
        marker.get("schema_version") != UPDATE_POINTER_SCHEMA
        or not _safe_update_id(update_id)
    ):
        raise OperationalUpdateError("UPDATE_MARKER_INVALID")
    relative_journal = f"updates/{update_id}/state.json"
    if marker.get("journal") != relative_journal:
        raise OperationalUpdateError("UPDATE_JOURNAL_PATH_UNSAFE")
    if update_id not in states:
        raise OperationalUpdateError("UPDATE_JOURNAL_REQUIRED")
    journal_path = updates_root / update_id / "state.json"
    if _unsafe_path(journal_path, paths.root):
        raise OperationalUpdateError("UPDATE_JOURNAL_PATH_UNSAFE")
    if not journal_path.is_file():
        raise OperationalUpdateError("UPDATE_JOURNAL_REQUIRED")
    state = states[update_id]
    if any(
        other_id != update_id
        and (
            other_state.get("result") not in _UPDATE_TERMINAL_RESULTS
            or other_state.get("pending_action") is not None
        )
        for other_id, other_state in states.items()
    ):
        raise OperationalUpdateError("UPDATE_JOURNAL_ORPHAN")
    if state.get("result") not in _UPDATE_TERMINAL_RESULTS:
        raise OperationalUpdateError("UPDATE_RECOVERY_REQUIRED")
    if state.get("pending_action") is not None:
        raise OperationalUpdateError("UPDATE_RECOVERY_REQUIRED")
    raise OperationalUpdateError("UPDATE_MARKER_TERMINAL_STATE")
