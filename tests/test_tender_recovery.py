from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from qi_crawler.db import Database
from qi_crawler.tender_case import AuthorityClass
from qi_crawler.tender_case_service import TenderCaseService
from qi_crawler.tender_recovery import ManagedIntegrityState
from qi_crawler.tender_recovery_service import TenderRecoveryService


@pytest.fixture
def recovery_context(tmp_path: Path):
    database = Database(f"sqlite:///{tmp_path / 'recovery.db'}")
    case_service = TenderCaseService(database, tmp_path / "managed")
    recovery = TenderRecoveryService(database, tmp_path / "managed")
    case_service.create_case("case-recovery")
    release = case_service.add_release("case-recovery", "IB2600999000-00")
    source = tmp_path / "source.pdf"
    source.write_bytes(b"recovery source bytes")
    membership = case_service.add_document(
        "case-recovery",
        release.release_id,
        source,
        authority=AuthorityClass.SOURCE_E_HSMT,
        evidence="explicit recovery fixture source",
    )
    managed = case_service.managed_path(membership.document_id)
    return recovery, case_service, release.release_id, membership, source, managed


def test_recovery_scan_marks_missing_managed_object_fail_closed(recovery_context) -> None:
    recovery, _case_service, release_id, membership, _source, managed = recovery_context
    managed.unlink()

    report = recovery.inspect_release("case-recovery", release_id)

    assert report.entries[0].membership_id == membership.id
    assert report.entries[0].state is ManagedIntegrityState.MISSING
    assert report.entries[0].expected_sha256
    assert report.entries[0].observed_sha256 is None


def test_exact_sha_recovery_restores_bytes_and_is_verified(recovery_context) -> None:
    recovery, case_service, release_id, membership, source, managed = recovery_context
    managed.unlink()

    result = recovery.recover(
        "case-recovery",
        release_id,
        membership.id,
        source,
        actor="Team Bid",
        reason="restore missing managed object",
        evidence="exact byte-identical disposable candidate",
    )

    expected = hashlib.sha256(source.read_bytes()).hexdigest()
    assert result.state is ManagedIntegrityState.RECOVERED
    assert managed.read_bytes() == source.read_bytes()
    assert result.verified_sha256 == expected
    assert case_service.managed_path(membership.document_id) == managed


def test_exact_sha_candidate_is_recoverable_before_explicit_action(recovery_context) -> None:
    recovery, _case_service, release_id, membership, source, managed = recovery_context
    managed.unlink()

    candidate = recovery.assess_candidate(
        "case-recovery", release_id, membership.id, source
    )

    assert candidate.state is ManagedIntegrityState.RECOVERABLE
    assert candidate.expected_sha256 == candidate.observed_sha256


def test_wrong_sha_candidate_is_rejected_without_overwrite(recovery_context) -> None:
    recovery, _case_service, release_id, membership, _source, managed = recovery_context
    managed.unlink()
    wrong = managed.parent / "same-name-wrong-bytes.pdf"
    wrong.write_bytes(b"wrong bytes")

    with pytest.raises(ValueError, match="SHA"):
        recovery.recover(
            "case-recovery",
            release_id,
            membership.id,
            wrong,
            actor="Team Bid",
            reason="wrong candidate",
            evidence="negative recovery fixture",
        )

    assert not managed.exists()


def test_mismatch_is_quarantined_before_exact_replacement(recovery_context) -> None:
    recovery, _case_service, release_id, membership, source, managed = recovery_context
    managed.write_bytes(b"tampered managed bytes")
    observed = recovery.inspect_release("case-recovery", release_id)
    assert observed.entries[0].state is ManagedIntegrityState.MISMATCH

    result = recovery.recover(
        "case-recovery",
        release_id,
        membership.id,
        source,
        actor="Team Bid",
        reason="replace tampered managed object",
        evidence="exact SHA candidate",
    )

    assert result.state is ManagedIntegrityState.RECOVERED
    assert result.quarantine_path is not None
    assert result.quarantine_path.is_file()
    assert result.quarantine_path.read_bytes() == b"tampered managed bytes"
    assert managed.read_bytes() == source.read_bytes()


def test_orphan_is_reported_without_auto_adoption(recovery_context) -> None:
    recovery, _case_service, release_id, _membership, _source, managed = recovery_context
    orphan = managed.parent / "unreferenced.bin"
    orphan.write_bytes(b"orphan bytes")

    report = recovery.reconcile("case-recovery", release_id)

    assert any(item.path == orphan for item in report.orphans)
    assert all(item.membership_id is None for item in report.orphans)


def test_recovery_rejects_membership_from_another_release(recovery_context) -> None:
    recovery, case_service, _release_id, membership, source, _managed = recovery_context
    other_release = case_service.add_release("case-recovery", "IB2600999000-01")

    with pytest.raises(ValueError, match="release"):
        recovery.recover(
            "case-recovery",
            other_release.release_id,
            membership.id,
            source,
            actor="Team Bid",
            reason="cross revision candidate",
            evidence="negative cross revision fixture",
        )


def test_recovery_is_idempotent_and_history_survives_restart(recovery_context) -> None:
    recovery, case_service, release_id, membership, source, _managed = recovery_context
    before = case_service.get_release_manifest("case-recovery", release_id)
    first = recovery.recover(
        "case-recovery",
        release_id,
        membership.id,
        source,
        actor="Team Bid",
        reason="restore managed object",
        evidence="exact candidate",
    )
    second = recovery.recover(
        "case-recovery",
        release_id,
        membership.id,
        source,
        actor="Team Bid",
        reason="repeat restore",
        evidence="same exact candidate",
    )
    restarted = TenderRecoveryService(recovery.database, recovery.document_root)
    after = case_service.get_release_manifest("case-recovery", release_id)

    assert first.state is ManagedIntegrityState.RECOVERED
    assert second.state is ManagedIntegrityState.RECOVERED
    assert len(restarted.history("case-recovery", release_id)) == 2
    assert [(item.document_id, item.authority_class) for item in after.memberships] == [
        (item.document_id, item.authority_class) for item in before.memberships
    ]
