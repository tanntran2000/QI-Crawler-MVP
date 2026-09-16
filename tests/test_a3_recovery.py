from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from tools.release.a3_process_observer import CensusSnapshot, ScopeProof, ScopeProofAuthority
from tools.release.a3_recovery import (
    MaterialWriteBoundExceeded,
    RecoveryController,
    RecoveryStatus,
    SimulatedRecoveryCrash,
    sqlite_writer_quiescence_probe,
)

SCHEMA = "0020_add_tender_operational_revision_events"
REPO = Path(__file__).resolve().parents[1]


class _Observer:
    def __init__(self, zero: bool = True, scope_proof: ScopeProof | None = None) -> None:
        self.zero = zero
        self.scope_proof = scope_proof or ScopeProof(
            observed_scope="SANDBOX_PROCESS_TREE",
            scope_complete=True,
            zero_proof_authority=ScopeProofAuthority.COMPLETE_PID_TREE,
            scope_evidence={
                "process_tree_complete": True,
                "root_absent": True,
                "tree_dead": True,
            },
        )

    def snapshot(self) -> CensusSnapshot:
        return CensusSnapshot(
            event_name="fixture",
            timestamp_utc="2026-09-10T00:00:00Z",
            records=(),
            legacy_count=0,
            unresolved_relevant_count=0 if self.zero else 1,
            legacy_zero_proven=self.zero,
            observed_scope=self.scope_proof.observed_scope,
            scope_complete=self.scope_proof.scope_complete,
            zero_proof_authority=self.scope_proof.zero_proof_authority,
            scope_evidence=self.scope_proof.scope_evidence,
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


def test_old_scope_less_zero_snapshot_fails_closed_without_mutation(tmp_path: Path) -> None:
    old_snapshot = ScopeProof()

    class _OldObserver:
        def snapshot(self) -> CensusSnapshot:
            return CensusSnapshot(
                event_name="old",
                timestamp_utc="2026-09-10T00:00:00Z",
                records=(),
                legacy_count=0,
                unresolved_relevant_count=0,
                legacy_zero_proven=True,
                observed_scope=old_snapshot.observed_scope,
                scope_complete=old_snapshot.scope_complete,
                zero_proof_authority=old_snapshot.zero_proof_authority,
                scope_evidence=old_snapshot.scope_evidence,
            )

    controller = _controller(tmp_path, observer=_OldObserver())
    result = controller.recover()

    assert result.status == RecoveryStatus.RECOVERY_REQUIRED
    assert result.mutated is False
    assert controller.canonical_path.read_bytes() == b"stub"


def test_unrecognized_scope_authority_fails_closed_without_mutation(tmp_path: Path) -> None:
    invalid = _Observer(
        scope_proof=ScopeProof(
            observed_scope="F5_CONTROLLER_JOB_DRAINED",
            scope_complete=False,
            zero_proof_authority=None,
        )
    )
    snapshot = CensusSnapshot(
        event_name="invalid",
        timestamp_utc="2026-09-10T00:00:00Z",
        records=(),
        legacy_count=0,
        unresolved_relevant_count=0,
        legacy_zero_proven=True,
        observed_scope="F5_CONTROLLER_JOB_DRAINED",
        scope_complete=True,
        zero_proof_authority="MACHINE_WIDE_SCAN",
        scope_evidence={},
    )

    class _InvalidObserver:
        def snapshot(self) -> CensusSnapshot:
            return snapshot

    controller = _controller(tmp_path, observer=_InvalidObserver())
    result = controller.recover()

    assert result.status == RecoveryStatus.RECOVERY_REQUIRED
    assert result.mutated is False
    assert invalid.scope_proof.scope_complete is False


def test_valid_modern_scope_proof_passes_zero_proof_gate(tmp_path: Path) -> None:
    controller = _controller(tmp_path)
    result = controller.recover()

    assert result.status == RecoveryStatus.LEGACY_READY


@pytest.mark.parametrize("modern", [False, True])
def test_recovery_cli_scope_contract_is_fail_closed_or_preserved(
    tmp_path: Path, modern: bool
) -> None:
    controller = _controller(tmp_path)
    observer_json = tmp_path / ("modern.json" if modern else "old.json")
    payload: dict[str, object] = {
        "event_name": "cli",
        "timestamp_utc": "2026-09-10T00:00:00Z",
        "records": [],
        "legacy_count": 0,
        "unresolved_relevant_count": 0,
        "legacy_zero_proven": True,
    }
    if modern:
        payload.update(
            {
                "observed_scope": "SANDBOX_PROCESS_TREE",
                "scope_complete": True,
                "zero_proof_authority": "COMPLETE_PID_TREE",
                "scope_evidence": {
                    "process_tree_complete": True,
                    "root_absent": True,
                    "tree_dead": True,
                },
            }
        )
    observer_json.write_text(json.dumps(payload), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.release.a3_recovery",
            "--canonical",
            str(controller.canonical_path),
            "--recovery",
            str(controller.recovery_path),
            "--transaction-root",
            str(controller.transaction_root),
            "--db-root",
            str(controller.db_root),
            "--legacy-sha256",
            controller.expected_legacy_sha256,
            "--expected-schema",
            SCHEMA,
            "--observer-json",
            str(observer_json),
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == (0 if modern else 2), result.stderr
    response = json.loads(result.stdout)
    assert response["status"] == (
        RecoveryStatus.LEGACY_READY.value if modern else RecoveryStatus.RECOVERY_REQUIRED.value
    )
    assert response["mutated"] is modern


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
