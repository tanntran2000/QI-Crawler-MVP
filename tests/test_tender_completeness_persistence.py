from __future__ import annotations

from pathlib import Path

from qi_crawler.db import Database
from qi_crawler.tender_case import AuthorityClass
from qi_crawler.tender_case_service import TenderCaseService
from qi_crawler.tender_completeness import (
    CoreCoverageState,
    CoreRole,
    PublicationExpectationBasis,
    PublicationPackageState,
    TenderCompletenessService,
)


def test_core_correction_history_and_restart_are_persistent(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'warehouse.db'}")
    documents = TenderCaseService(database, tmp_path / "managed")
    documents.create_case("case-1")
    release = documents.add_release("case-1", "IB2600502358-00")
    source = tmp_path / "master.pdf"
    source.write_bytes(b"master")
    membership = documents.add_document(
        "case-1",
        release.release_id,
        source,
        authority=AuthorityClass.SOURCE_E_HSMT,
        evidence="Team Bid source",
    )

    first = TenderCompletenessService(database)
    first.confirm_core_role(
        release.release_id,
        membership.id,
        CoreRole.SCOPE_AND_QUANTITY,
        state=CoreCoverageState.NEEDS_SUPPLEMENT,
        content_locator="section:scope",
        evidence="first review",
        actor="reviewer-a",
    )
    first.confirm_core_role(
        release.release_id,
        membership.id,
        CoreRole.SCOPE_AND_QUANTITY,
        state=CoreCoverageState.CONFIRMED,
        content_locator="pages:1-2",
        evidence="corrected review",
        actor="reviewer-b",
    )

    reopened = TenderCompletenessService(database)
    assert reopened.core_readiness(release.release_id).role_states[CoreRole.SCOPE_AND_QUANTITY] is CoreCoverageState.CONFIRMED
    history = reopened.core_history(release.release_id, CoreRole.SCOPE_AND_QUANTITY)
    assert [entry.state for entry in history] == [
        CoreCoverageState.NEEDS_SUPPLEMENT,
        CoreCoverageState.CONFIRMED,
    ]


def test_publication_partial_list_cannot_prove_complete(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'warehouse.db'}")
    documents = TenderCaseService(database, tmp_path / "managed")
    documents.create_case("case-1")
    release = documents.add_release("case-1", "IB2600502358-00")
    completeness = TenderCompletenessService(database)

    expectation_id = completeness.create_publication_expectation(
        release.release_id,
        basis=PublicationExpectationBasis.PARTIAL_LIST,
        authority="team-bid-observation",
        evidence="partial source list",
        actor="bid-reviewer",
    )
    completeness.add_publication_item(expectation_id, "scope", "Scope document")
    summary = completeness.publication_summary(release.release_id)

    assert summary.state is PublicationPackageState.UNKNOWN
    assert summary.partial_list_count == 1


def test_same_sha_can_have_separate_release_memberships(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'warehouse.db'}")
    documents = TenderCaseService(database, tmp_path / "managed")
    documents.create_case("case-1")
    first = documents.add_release("case-1", "IB2600502358-00")
    second = documents.add_release("case-1", "IB2600502358-01")
    source = tmp_path / "same.pdf"
    source.write_bytes(b"same bytes")
    first_member = documents.add_document(
        "case-1", first.release_id, source,
        authority=AuthorityClass.SOURCE_E_HSMT,
        evidence="release 00",
    )
    second_member = documents.add_document(
        "case-1", second.release_id, source,
        authority=AuthorityClass.SOURCE_E_HSMT,
        evidence="release 01",
    )

    assert first_member.id != second_member.id
    assert first_member.document_id == second_member.document_id
