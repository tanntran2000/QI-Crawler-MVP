"""Read-only observation and fail-closed classification of operational updates."""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import sqlite3
import stat
import tempfile
import time
from collections.abc import Callable, Mapping
from contextlib import ExitStack, closing, nullcontext
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from .operational_release import OperationalPaths

MARKER_SCHEMA = "qi-crawler-operational-update-marker-v1"
JOURNAL_SCHEMA = "qi-crawler-operational-update-journal-v1"
RECEIPT_SCHEMA = "qi-crawler-operational-update-receipt-v1"
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
        path.relative_to(root)
    except ValueError:
        return True
    current = root
    try:
        relative_parts = path.relative_to(root).parts
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
