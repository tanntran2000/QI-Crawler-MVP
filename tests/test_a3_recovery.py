from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pytest

from tools.release.a3_process_observer import CensusSnapshot
from tools.release.a3_recovery import (
    MaterialWriteBoundExceeded,
    RecoveryController,
    RecoveryStatus,
    SimulatedRecoveryCrash,
    sqlite_writer_quiescence_probe,
)

SCHEMA = "0020_add_tender_operational_revision_events"


class _Observer:
    def __init__(self, zero: bool = True) -> None:
        self.zero = zero

    def snapshot(self) -> CensusSnapshot:
        return CensusSnapshot(
            event_name="fixture",
            timestamp_utc="2026-09-10T00:00:00Z",
            records=(),
            legacy_count=0,
            unresolved_relevant_count=0 if self.zero else 1,
            legacy_zero_proven=self.zero,
        )


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _db(path: Path, schema: str = SCHEMA) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
        connection.execute("INSERT INTO alembic_version(version_num) VALUES (?)", (schema,))
        connection.commit()


def _controller(tmp_path: Path, *, observer: _Observer | None = None, barrier: bool = False) -> RecoveryController:
    canonical = tmp_path / "QI-Crawler.exe"
    recovery = tmp_path / "recovery" / "QI-Crawler.exe"
    recovery.parent.mkdir()
    canonical.write_bytes(b"stub")
    recovery.write_bytes(b"legacy-v09")
    db_root = tmp_path / "data"
    db_root.mkdir()
    _db(db_root / "egp.db")
    return RecoveryController(
        canonical_path=canonical,
        recovery_path=recovery,
        transaction_root=tmp_path / "txn",
        db_root=db_root,
        expected_legacy_sha256=_sha(recovery),
        expected_schema=SCHEMA,
        observer=observer or _Observer(),
        barrier_confirmed=barrier,
    )


def test_prebarrier_recovery_restores_legacy_and_reaches_ready(tmp_path: Path) -> None:
    controller = _controller(tmp_path)
    db = controller.db_root / "egp.db"
    generation_before = db.read_bytes()
    result = controller.recover()

    assert result.status == RecoveryStatus.LEGACY_READY
    assert controller.canonical_path.read_bytes() == b"legacy-v09"
    assert result.db_generation_unchanged is True
    assert db.read_bytes() == generation_before
    with sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True) as connection:
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone()[0] == SCHEMA


def test_recovery_is_idempotent(tmp_path: Path) -> None:
    controller = _controller(tmp_path)
    first = controller.recover()
    second = controller.recover()

    assert first.status == second.status == RecoveryStatus.LEGACY_READY
    assert second.mutated is False


def test_recovery_journal_refuses_oversized_payload_before_persist(tmp_path: Path) -> None:
    controller = _controller(tmp_path)
    controller.max_journal_bytes = 32

    with pytest.raises(MaterialWriteBoundExceeded, match="MATERIAL_WRITE_BOUND_EXCEEDED"):
        controller.recover()

    assert not controller.journal_path.exists()
    assert not controller.journal_path.with_suffix(".tmp").exists()


def test_barrier_confirmed_forbids_automatic_legacy_restore(tmp_path: Path) -> None:
    result = _controller(tmp_path, barrier=True).recover()

    assert result.status == RecoveryStatus.MAINTENANCE_RECOVERY_REQUIRED
    assert result.mutated is False


def test_unresolved_observer_fails_closed(tmp_path: Path) -> None:
    result = _controller(tmp_path, observer=_Observer(zero=False)).recover()

    assert result.status == RecoveryStatus.RECOVERY_REQUIRED
    assert result.mutated is False


def test_schema_mismatch_fails_closed(tmp_path: Path) -> None:
    controller = _controller(tmp_path)
    db = controller.db_root / "egp.db"
    with sqlite3.connect(controller.db_root / "egp.db") as connection:
        connection.execute(
            "UPDATE alembic_version SET version_num = ?",
            ("0022_add_tender_recovery_events",),
        )
        connection.commit()
    generation_before = db.read_bytes()

    result = controller.recover()
    assert result.status == RecoveryStatus.RECOVERY_REQUIRED
    assert result.mutated is False
    assert result.db_generation_unchanged is True
    assert db.read_bytes() == generation_before
    assert controller.canonical_path.read_bytes() == b"stub"


@pytest.mark.parametrize("failpoint", ["R0", "R1", "R2", "R3"])
def test_failpoint_retry_is_deterministic(tmp_path: Path, failpoint: str) -> None:
    controller = _controller(tmp_path)
    crashing = RecoveryController(
        canonical_path=controller.canonical_path,
        recovery_path=controller.recovery_path,
        transaction_root=controller.transaction_root,
        db_root=controller.db_root,
        expected_legacy_sha256=controller.expected_legacy_sha256,
        expected_schema=SCHEMA,
        observer=_Observer(),
        failpoint=failpoint,
    )

    with pytest.raises(SimulatedRecoveryCrash):
        crashing.recover()

    retry = controller.recover()
    assert retry.status == RecoveryStatus.LEGACY_READY
    assert controller.canonical_path.read_bytes() == b"legacy-v09"


def test_sqlite_writer_probe_is_read_only_and_preserves_generation(tmp_path: Path) -> None:
    db = tmp_path / "egp.db"
    _db(db)
    before = db.read_bytes()

    result = sqlite_writer_quiescence_probe(db)

    assert result.success is True
    assert result.schema == SCHEMA
    assert db.read_bytes() == before
