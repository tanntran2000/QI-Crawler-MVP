from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from qi_crawler.update_transaction import MaintenanceBusy, MaintenanceTransaction, legacy_write


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
