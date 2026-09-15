from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from qi_crawler import update_transaction as maintenance
from qi_crawler.update_transaction import (
    MaintenanceBusy,
    MaintenanceStateError,
    MaintenanceTransaction,
    legacy_write,
)


def _database(path: Path) -> None:
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE events (value TEXT NOT NULL)")
    connection.commit()
    connection.close()


def test_legacy_writer_can_write_before_maintenance(tmp_path: Path) -> None:
    database = tmp_path / "data.db"
    _database(database)

    legacy_write(database, "before")

    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT value FROM events").fetchall() == [("before",)]


def test_maintenance_barrier_blocks_legacy_but_allows_owner(tmp_path: Path) -> None:
    database = tmp_path / "data.db"
    _database(database)
    transaction = MaintenanceTransaction.start(tmp_path, database)

    try:
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            legacy_write(database, "legacy-during")
        transaction.write("INSERT INTO events(value) VALUES (?)", ("maintenance",))
    finally:
        transaction.complete()

    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT value FROM events").fetchall() == [("maintenance",)]


def test_second_maintenance_owner_is_rejected(tmp_path: Path) -> None:
    database = tmp_path / "data.db"
    _database(database)
    first = MaintenanceTransaction.start(tmp_path, database)

    try:
        with pytest.raises(MaintenanceBusy):
            MaintenanceTransaction.start(tmp_path, database)
    finally:
        first.complete()


def test_rejected_second_owner_does_not_leave_recovery_journal(tmp_path: Path) -> None:
    database = tmp_path / "data.db"
    _database(database)
    first = MaintenanceTransaction.start(tmp_path, database)

    try:
        with pytest.raises(MaintenanceBusy):
            MaintenanceTransaction.start(tmp_path, database)
        journals = list((tmp_path / "maintenance" / "updates").glob("*/state.json"))
        assert len(journals) == 1
    finally:
        first.complete()


def test_interrupted_transaction_reopens_as_recovery_required(tmp_path: Path) -> None:
    database = tmp_path / "data.db"
    _database(database)
    script = """
from pathlib import Path
import os
import sys
from qi_crawler.update_transaction import MaintenanceTransaction
transaction = MaintenanceTransaction.start(Path(sys.argv[1]), Path(sys.argv[2]))
transaction.write("INSERT INTO events(value) VALUES (?)", ("interrupted",))
transaction.mark_phase("DB_MIGRATING")
os._exit(73)
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(tmp_path), str(database)],
        check=False,
        cwd=Path(__file__).parents[1],
    )
    assert result.returncode == 73

    transaction = MaintenanceTransaction.resume(tmp_path, database)
    try:
        assert transaction.state["phase"] == "RECOVERY_REQUIRED"
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            legacy_write(database, "legacy-after-crash")
        transaction.write("INSERT INTO events(value) VALUES (?)", ("recovered",))
    finally:
        transaction.complete()

    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT value FROM events").fetchall() == [("recovered",)]


@pytest.mark.parametrize("operation", ["start", "resume", "postchecking", "complete"])
def test_journal_failure_releases_both_resources(tmp_path: Path, monkeypatch, operation: str) -> None:
    database = tmp_path / "data.db"
    _database(database)
    transaction = None
    if operation != "start":
        transaction = MaintenanceTransaction.start(tmp_path, database)
        if operation == "resume":
            transaction.__exit__(RuntimeError, RuntimeError("interrupted"), None)
    original = maintenance._write_json_durable
    failed_phase = {"start": "APPLICATION_QUIESCED", "resume": "RECOVERY_REQUIRED",
                    "postchecking": "POSTCHECKING", "complete": "COMPLETE"}[operation]
    fault = OSError("journal-storage-failure")

    def fail_journal(path, state):
        if state["phase"] == failed_phase:
            raise fault
        original(path, state)

    monkeypatch.setattr(maintenance, "_write_json_durable", fail_journal)
    with pytest.raises(OSError) as captured:
        if operation == "start":
            MaintenanceTransaction.start(tmp_path, database)
        elif operation == "resume":
            MaintenanceTransaction.resume(tmp_path, database)
        else:
            transaction.complete()
    assert captured.value is fault
    journals = list((tmp_path / "maintenance" / "updates").glob("*/state.json"))
    assert all(json.loads(path.read_text())["phase"] != "COMPLETE" for path in journals)
    if transaction is not None:
        assert transaction.state["phase"] != "COMPLETE"
    legacy_write(database, "reacquired")
    monkeypatch.setattr(maintenance, "_write_json_durable", original)
    with MaintenanceTransaction.resume(tmp_path, database):
        pass


@pytest.mark.parametrize("failure_source", ["body", "journal"])
def test_cleanup_failures_preserve_original_and_release_owner(tmp_path: Path, monkeypatch, failure_source: str) -> None:
    database = tmp_path / "data.db"
    _database(database)
    transaction = MaintenanceTransaction.start(tmp_path, database)
    actual = transaction._connection
    attempted = []

    class BrokenCleanup:
        def rollback(self):
            attempted.append("rollback")
            actual.rollback()
            raise OSError("rollback-cleanup-failure")

        def close(self):
            attempted.append("close")
            actual.close()
            raise OSError("close-cleanup-failure")

    transaction._connection = BrokenCleanup()
    original = RuntimeError("original-operation-failure")
    if failure_source == "body":
        transaction.__exit__(RuntimeError, original, None)
    else:
        def fail_journal(*args):
            raise original
        with monkeypatch.context() as scoped:
            scoped.setattr(maintenance, "_write_json_durable", fail_journal)
            with pytest.raises(RuntimeError) as captured:
                transaction.complete()
            assert captured.value is original
    assert attempted == ["rollback", "close"]
    assert any("rollback-cleanup-failure" in note for note in original.__notes__)
    assert any("close-cleanup-failure" in note for note in original.__notes__)
    legacy_write(database, "released")
    with MaintenanceTransaction.resume(tmp_path, database):
        pass


def test_resume_does_not_reopen_completion_before_owner_acquisition(tmp_path: Path, monkeypatch) -> None:
    database = tmp_path / "data.db"
    _database(database)
    first = MaintenanceTransaction.start(tmp_path, database)
    first.mark_phase("POSTCHECKING")
    acquire = maintenance._ExclusiveFileLock.acquire
    completed = False

    def finish_then_acquire(lock):
        nonlocal completed
        if not completed:
            first.complete()
            completed = True
        acquire(lock)

    monkeypatch.setattr(maintenance._ExclusiveFileLock, "acquire", finish_then_acquire)
    with pytest.raises(MaintenanceStateError, match="exactly one incomplete"):
        MaintenanceTransaction.resume(tmp_path, database)
    assert json.loads(first.journal_path.read_text())["phase"] == "COMPLETE"
    legacy_write(database, "after-completion")
    with MaintenanceTransaction.start(tmp_path, database):
        pass


def test_begin_failure_closes_open_connection(tmp_path: Path, monkeypatch) -> None:
    database = tmp_path / "data.db"
    _database(database)
    connect = maintenance.sqlite3.connect
    closed = []

    class Connection(sqlite3.Connection):
        def execute(self, statement, *args):
            if statement == "BEGIN IMMEDIATE":
                raise sqlite3.OperationalError("begin-failed")
            return super().execute(statement, *args)

        def close(self):
            closed.append(True)
            super().close()

    monkeypatch.setattr(maintenance.sqlite3, "connect", lambda *a, **kw: connect(*a, **kw, factory=Connection))
    with pytest.raises(sqlite3.OperationalError, match="begin-failed"):
        MaintenanceTransaction.start(tmp_path, database)
    assert closed == [True]
    monkeypatch.setattr(maintenance.sqlite3, "connect", connect)
    legacy_write(database, "released")
    with MaintenanceTransaction.resume(tmp_path, database):
        pass
