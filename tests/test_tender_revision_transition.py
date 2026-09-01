from __future__ import annotations

from pathlib import Path

import pytest

from qi_crawler.db import Database
from qi_crawler.market_intelligence.opportunity_contract import OpportunityIdentity
from qi_crawler.tender_case import TenderRelease
from qi_crawler.tender_case_persistence import TenderCasePersistence
from qi_crawler.tender_revision_persistence import TenderRevisionPersistence
from qi_crawler.tender_revision_transition import (
    RevisionTransitionError,
    RevisionTransitionOutcome,
    SourceDiffState,
    TenderRevisionTransitionService,
)


@pytest.fixture
def transition_service(tmp_path: Path) -> TenderRevisionTransitionService:
    database = Database(f"sqlite:///{tmp_path / 'revision.db'}")
    cases = TenderCasePersistence(database)
    cases.create_case("case-revision")
    cases.add_release("case-revision", TenderRelease(OpportunityIdentity.from_raw("IB2600000001-00")))
    cases.add_release("case-revision", TenderRelease(OpportunityIdentity.from_raw("IB2600000001-01")))
    cases.add_release("case-revision", TenderRelease(OpportunityIdentity.from_raw("IB2600000001-02")))
    return TenderRevisionTransitionService(TenderRevisionPersistence(database))


def test_first_acceptance_persists_operational_latest(transition_service) -> None:
    result = transition_service.accept_revision(
        "case-revision", 1, actor="Team Bid", reason="first publication", evidence="HSMT verified"
    )
    assert result.outcome is RevisionTransitionOutcome.INITIAL_ACCEPTED
    assert result.latest.identity.raw_id == "IB2600000001-00"
    reopened = TenderRevisionTransitionService(transition_service.persistence)
    assert reopened.operational_latest("case-revision").identity.revision == "00"


def test_newer_acceptance_advances_and_preserves_previous(transition_service) -> None:
    transition_service.accept_revision("case-revision", 1, actor="Team Bid", reason="first", evidence="evidence")
    result = transition_service.accept_revision("case-revision", 2, actor="Team Bid", reason="revision", evidence="evidence")
    assert result.outcome is RevisionTransitionOutcome.ADVANCED
    assert result.previous.identity.revision == "00"
    assert result.latest.identity.revision == "01"
    assert [event.revision for event in transition_service.persistence.events_for_case("case-revision")] == ["00", "01"]


def test_rejected_newer_revision_does_not_change_latest(transition_service) -> None:
    transition_service.accept_revision("case-revision", 1, actor="Team Bid", reason="first", evidence="evidence")
    result = transition_service.reject_revision("case-revision", 2, actor="Team Bid", reason="not usable", evidence="review note")
    assert result.outcome is RevisionTransitionOutcome.REJECTED
    assert result.latest.identity.revision == "00"
    assert transition_service.operational_latest("case-revision").identity.revision == "00"


def test_older_revision_cannot_downgrade_latest(transition_service) -> None:
    transition_service.accept_revision("case-revision", 2, actor="Team Bid", reason="latest", evidence="evidence")
    result = transition_service.accept_revision("case-revision", 1, actor="Team Bid", reason="stale input", evidence="evidence")
    assert result.outcome is RevisionTransitionOutcome.NO_DOWNGRADE
    assert result.latest.identity.revision == "01"
    assert len(transition_service.persistence.events_for_case("case-revision")) == 1


def test_mismatched_lineage_is_held_without_guessing(transition_service) -> None:
    transition_service.accept_revision("case-revision", 1, actor="Team Bid", reason="first", evidence="evidence")
    cases = transition_service.persistence.case_persistence
    cases.add_release("case-revision", TenderRelease(OpportunityIdentity.from_raw("IB2600000002-00")))
    result = transition_service.accept_revision("case-revision", 4, actor="Team Bid", reason="foreign", evidence="mismatch")
    assert result.outcome is RevisionTransitionOutcome.HOLD
    assert result.latest.identity.raw_id == "IB2600000001-00"
    assert len(transition_service.persistence.events_for_case("case-revision")) == 1


def test_missing_decision_fails_closed(transition_service) -> None:
    with pytest.raises(RevisionTransitionError, match="decision"):
        transition_service.transition("case-revision", 1, decision=None, actor="Team Bid", reason="x", evidence="y")


def test_adjacent_diff_is_bounded_and_classifies_changes(transition_service) -> None:
    diff = transition_service.compare_adjacent_revisions(
        "case-revision", previous_release_id=1, latest_release_id=2,
        previous_snapshot={"C3": "a", "C5": "same"},
        latest_snapshot={"C3": "b", "C5": "same", "PL": "new"},
    )
    assert diff["C3"].state is SourceDiffState.CHANGED
    assert diff["C5"].state is SourceDiffState.UNCHANGED
    assert diff["PL"].state is SourceDiffState.ADDED


def test_adjacent_diff_marks_removed_and_rejects_non_adjacent(transition_service) -> None:
    diff = transition_service.compare_adjacent_revisions(
        "case-revision", 1, 2, previous_snapshot={"C3": "old"}, latest_snapshot={}
    )
    assert diff["C3"].state is SourceDiffState.REMOVED_FROM_NEW_REVISION
    with pytest.raises(RevisionTransitionError, match="adjacent"):
        transition_service.compare_adjacent_revisions(
            "case-revision", 1, 3, previous_snapshot={}, latest_snapshot={}
        )
