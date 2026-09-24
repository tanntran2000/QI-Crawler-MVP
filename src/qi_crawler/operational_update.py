"""Read-only observation and fail-closed classification of operational updates."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import stat
import tempfile
import time
from collections.abc import Callable, Mapping
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from .operational_release import OperationalPaths

MARKER_SCHEMA = "qi-crawler-operational-update-marker-v1"
JOURNAL_SCHEMA = "qi-crawler-operational-update-journal-v1"
RECEIPT_SCHEMA = "qi-crawler-operational-update-receipt-v1"

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
    path: Path, *, immutable: bool, timeout: float = 5.0
) -> tuple[dict[str, str] | None, str | None]:
    uri = path.as_uri() + "?mode=ro"
    if immutable:
        uri += "&immutable=1"
    try:
        with closing(sqlite3.connect(uri, uri=True, timeout=timeout)) as connection:
            connection.execute("PRAGMA query_only = ON")
            rows = connection.execute("SELECT id, stored_path FROM documents ORDER BY id").fetchall()
    except (OSError, sqlite3.Error):
        return None, "DATABASE_UNREADABLE"
    return {str(row[0]): str(row[1]) for row in rows}, None


def _database_paths(path: Path, *, active_wal: bool) -> tuple[dict[str, str] | None, str | None]:
    if not active_wal:
        return _read_database_paths(path, immutable=True)
    try:
        with tempfile.TemporaryDirectory(prefix="qi-update-observation-") as directory:
            snapshot = Path(directory) / path.name
            deadline = time.monotonic() + 5.0

            def enforce_deadline(_status: int, _remaining: int, _total: int) -> None:
                if time.monotonic() >= deadline:
                    raise sqlite3.OperationalError("DATABASE_SNAPSHOT_TIMEOUT")

            source_uri = path.resolve(strict=False).as_uri() + "?mode=ro"
            with closing(sqlite3.connect(source_uri, uri=True, timeout=1.0)) as source:
                source.execute("PRAGMA query_only = ON")
                source.execute("PRAGMA busy_timeout = 1000")
                data_version_start = int(source.execute("PRAGMA data_version").fetchone()[0])
                with closing(sqlite3.connect(snapshot, timeout=1.0)) as destination:
                    source.backup(
                        destination,
                        pages=128,
                        progress=enforce_deadline,
                        sleep=0.05,
                    )
                enforce_deadline(0, 0, 0)
                data_version_end = int(source.execute("PRAGMA data_version").fetchone()[0])
                if data_version_end != data_version_start:
                    return None, "DATABASE_CHANGED_DURING_SNAPSHOT"
            return _read_database_paths(snapshot, immutable=False, timeout=1.0)
    except sqlite3.OperationalError as exc:
        if str(exc) == "DATABASE_SNAPSHOT_TIMEOUT":
            return None, "DATABASE_SNAPSHOT_TIMEOUT"
        return None, "DATABASE_UNREADABLE"
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
