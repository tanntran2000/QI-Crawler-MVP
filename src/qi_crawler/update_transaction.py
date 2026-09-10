"""Durable maintenance ownership and SQLite write barrier primitives."""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Self
from uuid import uuid4

PHASES = frozenset(
    {
        "PRECHECKED",
        "PAYLOAD_STAGED",
        "PAYLOAD_VERIFIED",
        "DB_BACKUP_VERIFIED",
        "APPLICATION_QUIESCED",
        "APP_COMMITTING",
        "APP_COMMITTED",
        "DB_MIGRATING",
        "DB_MIGRATED",
        "POSTCHECKING",
        "COMPLETE",
        "RECOVERY_REQUIRED",
    }
)


class MaintenanceBusy(RuntimeError):
    """Another maintenance owner currently holds the exclusive barrier."""


class MaintenanceStateError(RuntimeError):
    """A transaction journal cannot be resumed or advanced safely."""


class _ExclusiveFileLock:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._handle = None

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.open("a+b")
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, BlockingIOError) as exc:
            handle.close()
            raise MaintenanceBusy("maintenance barrier is already owned") from exc
        self._handle = handle

    def release(self) -> None:
        if self._handle is None:
            return
        try:
            if os.name == "nt":
                import msvcrt

                self._handle.seek(0)
                msvcrt.locking(self._handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
        finally:
            self._handle.close()
            self._handle = None


def _write_json_durable(path: Path, payload: dict[str, object]) -> None:
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    raw = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    with temporary.open("wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def legacy_write(database_path: Path, value: str) -> None:
    """Represent a legacy writer that knows nothing about the journal."""
    connection = sqlite3.connect(database_path, timeout=0.0)
    try:
        connection.execute("INSERT INTO events(value) VALUES (?)", (value,))
        connection.commit()
    finally:
        connection.close()


@dataclass
class MaintenanceTransaction:
    data_root: Path
    database_path: Path
    transaction_id: str
    journal_path: Path
    _connection: sqlite3.Connection
    _owner_lock: _ExclusiveFileLock
    state: dict[str, object]

    @classmethod
    def start(cls, data_root: Path, database_path: Path) -> MaintenanceTransaction:
        root = Path(data_root).resolve()
        database = Path(database_path).resolve()
        transaction_id = uuid4().hex
        owner_lock = _ExclusiveFileLock(root / "maintenance" / "maintenance.lock")
        owner_lock.acquire()
        journal_dir = root / "maintenance" / "updates" / transaction_id
        try:
            journal_dir.mkdir(parents=True, exist_ok=False)
            journal_path = journal_dir / "state.json"
            state: dict[str, object] = {
                "transaction_id": transaction_id,
                "data_root": str(root),
                "database_path": str(database),
                "phase": "PRECHECKED",
                "barrier_acquired": False,
                "migration_started": False,
                "migration_completed": False,
                "app_commit_started": False,
                "app_commit_completed": False,
                "postcheck_completed": False,
                "owner_pid": os.getpid(),
                "python_executable": sys.executable,
            }
            _write_json_durable(journal_path, state)
            connection = sqlite3.connect(database, timeout=0.0, isolation_level=None)
            connection.execute("PRAGMA busy_timeout=0")
            # RESERVED blocks other writers while allowing legacy readers to
            # inspect schema and reach their write attempt.
            connection.execute("BEGIN IMMEDIATE")
        except Exception:
            owner_lock.release()
            raise
        state["phase"] = "APPLICATION_QUIESCED"
        state["barrier_acquired"] = True
        _write_json_durable(journal_path, state)
        return cls(root, database, transaction_id, journal_path, connection, owner_lock, state)

    @classmethod
    def resume(cls, data_root: Path, database_path: Path) -> MaintenanceTransaction:
        root = Path(data_root).resolve()
        database = Path(database_path).resolve()
        update_root = root / "maintenance" / "updates"
        journals = sorted(update_root.glob("*/state.json"))
        candidates = []
        for journal in journals:
            state = json.loads(journal.read_text(encoding="utf-8"))
            if state.get("database_path") == str(database) and state.get("phase") != "COMPLETE":
                candidates.append((journal, state))
        if len(candidates) != 1:
            raise MaintenanceStateError("expected exactly one incomplete maintenance transaction")
        journal_path, state = candidates[0]
        transaction = cls._resume_existing(root, database, journal_path, state)
        return transaction

    @classmethod
    def _resume_existing(
        cls,
        root: Path,
        database: Path,
        journal_path: Path,
        state: dict[str, object],
    ) -> MaintenanceTransaction:
        owner_lock = _ExclusiveFileLock(root / "maintenance" / "maintenance.lock")
        owner_lock.acquire()
        try:
            connection = sqlite3.connect(database, timeout=0.0, isolation_level=None)
            connection.execute("PRAGMA busy_timeout=0")
            connection.execute("BEGIN IMMEDIATE")
        except Exception:
            owner_lock.release()
            raise
        state["phase"] = "RECOVERY_REQUIRED"
        state["barrier_acquired"] = True
        state["owner_pid"] = os.getpid()
        _write_json_durable(journal_path, state)
        return cls(
            root,
            database,
            str(state["transaction_id"]),
            journal_path,
            connection,
            owner_lock,
            state,
        )

    def write(self, statement: str, parameters: tuple[object, ...] = ()) -> None:
        self._connection.execute(statement, parameters)

    def mark_phase(self, phase: str) -> None:
        if phase not in PHASES or phase == "COMPLETE":
            raise MaintenanceStateError(f"unsupported transaction phase: {phase}")
        self.state["phase"] = phase
        if phase == "DB_MIGRATING":
            self.state["migration_started"] = True
        if phase == "DB_MIGRATED":
            self.state["migration_completed"] = True
        _write_json_durable(self.journal_path, self.state)

    def complete(self) -> None:
        if self.state.get("phase") == "COMPLETE":
            return
        self.state["phase"] = "POSTCHECKING"
        _write_json_durable(self.journal_path, self.state)
        try:
            self._connection.commit()
            self.state["postcheck_completed"] = True
            self.state["phase"] = "COMPLETE"
            _write_json_durable(self.journal_path, self.state)
        finally:
            self._connection.close()
            self._owner_lock.release()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if exc_type is None:
            self.complete()
            return
        self._connection.rollback()
        self._connection.close()
        self._owner_lock.release()


__all__ = ["MaintenanceBusy", "MaintenanceStateError", "MaintenanceTransaction", "legacy_write"]
