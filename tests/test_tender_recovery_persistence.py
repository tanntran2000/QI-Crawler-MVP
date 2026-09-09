from __future__ import annotations

from pathlib import Path

from qi_crawler.db import Database
from qi_crawler.tender_case import AuthorityClass
from qi_crawler.tender_case_service import TenderCaseService
from qi_crawler.tender_recovery_service import TenderRecoveryService


def test_recovery_event_history_is_append_only_and_restartable(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'recovery-persistence.db'}")
    case_service = TenderCaseService(database, tmp_path / "managed")
    case_service.create_case("case-persistence")
    release = case_service.add_release("case-persistence", "IB2600999100-00")
    source = tmp_path / "source.pdf"
    source.write_bytes(b"persistent recovery bytes")
    membership = case_service.add_document(
        "case-persistence",
        release.release_id,
        source,
        authority=AuthorityClass.SOURCE_E_HSMT,
        evidence="persistence fixture",
    )
    managed = case_service.managed_path(membership.document_id)
    managed.unlink()

    recovery = TenderRecoveryService(database, tmp_path / "managed")
    recovery.recover(
        "case-persistence",
        release.release_id,
        membership.id,
        source,
        actor="Team Bid",
        reason="restart persistence test",
        evidence="exact candidate",
    )
    reopened = TenderRecoveryService(database, tmp_path / "managed")

    history = reopened.history("case-persistence", release.release_id)
    assert len(history) == 1
    assert history[0].expected_sha256 == history[0].candidate_sha256
    assert history[0].result == "RECOVERED"
