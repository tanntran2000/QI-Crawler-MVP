from __future__ import annotations

from pathlib import Path

import pytest

from qi_crawler.db import Database
from qi_crawler.tender_case import AuthorityClass
from qi_crawler.tender_case_service import ManagedDocumentMissing, TenderCaseService
from qi_crawler.tender_completeness import (
    CoreCoverageState,
    CoreRole,
    PublicationExpectationBasis,
    PublicationPackageState,
    TenderCompletenessService,
)


def _workspace(tmp_path: Path, raw_id: str = "IB2600502358-00") -> tuple[Database, TenderCaseService, int]:
    database = Database(f"sqlite:///{tmp_path / 'warehouse.db'}")
    documents = TenderCaseService(database, tmp_path / "managed")
    documents.create_case("case-1")
    release = documents.add_release("case-1", raw_id)
    return database, documents, release.release_id


def _add_source(documents: TenderCaseService, release_id: int, tmp_path: Path, name: str, content: bytes, *, authority=AuthorityClass.SOURCE_E_HSMT):
    source = tmp_path / name
    source.write_bytes(content)
    return documents.add_document(
        "case-1",
        release_id,
        source,
        authority=authority,
        evidence=f"Team Bid confirmed source: {name}",
    )


def test_direct_ib_without_pl_and_one_file_can_cover_all_core_roles(tmp_path: Path) -> None:
    database, documents, release_id = _workspace(tmp_path)
    membership = _add_source(documents, release_id, tmp_path, "master.pdf", b"master source")
    completeness = TenderCompletenessService(database, document_root=tmp_path / "managed")

    for role in CoreRole:
        completeness.confirm_core_role(
            release_id,
            membership.id,
            role,
            state=CoreCoverageState.CONFIRMED,
            content_locator=f"pages:{role.value}:1-2",
            evidence="Human opened and checked the source pages",
            actor="bid-reviewer",
        )

    readiness = completeness.core_readiness(release_id)
    assert readiness.full_research_ready is True
    assert all(readiness.role_states[role] is CoreCoverageState.CONFIRMED for role in CoreRole)
    assert documents.open_case("case-1").plan_context is None


def test_partial_core_research_remains_readable_and_does_not_block_workspace(tmp_path: Path) -> None:
    database, documents, release_id = _workspace(tmp_path)
    membership = _add_source(documents, release_id, tmp_path, "scope.pdf", b"scope")
    completeness = TenderCompletenessService(database)

    completeness.confirm_core_role(
        release_id,
        membership.id,
        CoreRole.SCOPE_AND_QUANTITY,
        state=CoreCoverageState.CONFIRMED,
        content_locator="pages:1-3",
        evidence="Human checked the scope table",
        actor="bid-reviewer",
    )
    readiness = completeness.core_readiness(release_id)

    assert readiness.full_research_ready is False
    assert readiness.role_states[CoreRole.SCOPE_AND_QUANTITY] is CoreCoverageState.CONFIRMED
    assert readiness.role_states[CoreRole.TECHNICAL_REQUIREMENTS] is CoreCoverageState.UNKNOWN
    assert readiness.role_states[CoreRole.TECHNICAL_EVALUATION] is CoreCoverageState.UNKNOWN


def test_filename_only_does_not_confirm_a_core_role(tmp_path: Path) -> None:
    database, documents, release_id = _workspace(tmp_path)
    membership = _add_source(documents, release_id, tmp_path, "Chuong V.pdf", b"technical source")
    completeness = TenderCompletenessService(database)

    with pytest.raises(ValueError, match="content locator"):
        completeness.confirm_core_role(
            release_id,
            membership.id,
            CoreRole.TECHNICAL_REQUIREMENTS,
            state=CoreCoverageState.CONFIRMED,
            content_locator="filename:Chuong V.pdf",
            evidence="filename only",
            actor="machine-suggestion",
        )


def test_supporting_appendix_can_supplement_one_core_role(tmp_path: Path) -> None:
    database, documents, release_id = _workspace(tmp_path)
    main = _add_source(documents, release_id, tmp_path, "chapter-v.pdf", b"chapter v")
    appendix = _add_source(documents, release_id, tmp_path, "technical-appendix.pdf", b"appendix")
    completeness = TenderCompletenessService(database)

    completeness.confirm_core_role(
        release_id,
        main.id,
        CoreRole.TECHNICAL_REQUIREMENTS,
        state=CoreCoverageState.NEEDS_SUPPLEMENT,
        content_locator="section:technical-requirements",
        evidence="Chapter V references the appendix",
        actor="bid-reviewer",
        dependency_note="technical-appendix.pdf is required",
    )
    completeness.confirm_core_role(
        release_id,
        appendix.id,
        CoreRole.TECHNICAL_REQUIREMENTS,
        state=CoreCoverageState.CONFIRMED,
        content_locator="pages:1-4",
        evidence="Referenced appendix checked",
        actor="bid-reviewer",
    )

    assert completeness.core_readiness(release_id).role_states[CoreRole.TECHNICAL_REQUIREMENTS] is CoreCoverageState.CONFIRMED


def test_missing_referenced_appendix_is_needs_supplement(tmp_path: Path) -> None:
    database, documents, release_id = _workspace(tmp_path)
    main = _add_source(documents, release_id, tmp_path, "chapter-v.pdf", b"chapter v")
    completeness = TenderCompletenessService(database)

    completeness.confirm_core_role(
        release_id,
        main.id,
        CoreRole.TECHNICAL_REQUIREMENTS,
        state=CoreCoverageState.NEEDS_SUPPLEMENT,
        content_locator="section:technical-requirements",
        evidence="Chapter V references a missing appendix",
        actor="bid-reviewer",
        dependency_note="missing technical appendix",
    )

    assert completeness.core_readiness(release_id).role_states[CoreRole.TECHNICAL_REQUIREMENTS] is CoreCoverageState.NEEDS_SUPPLEMENT


def test_reference_only_membership_cannot_confirm_core_content(tmp_path: Path) -> None:
    database, documents, release_id = _workspace(tmp_path)
    reference = _add_source(
        documents,
        release_id,
        tmp_path,
        "reference.pdf",
        b"reference",
        authority=AuthorityClass.REFERENCE_ONLY,
    )
    completeness = TenderCompletenessService(database)

    with pytest.raises(ValueError, match="SOURCE_E_HSMT"):
        completeness.confirm_core_role(
            release_id,
            reference.id,
            CoreRole.TECHNICAL_EVALUATION,
            state=CoreCoverageState.CONFIRMED,
            content_locator="pages:1-2",
            evidence="reference only",
            actor="bid-reviewer",
        )


def test_publication_unknown_does_not_become_complete_from_observed_files(tmp_path: Path) -> None:
    database, _documents, release_id = _workspace(tmp_path)
    completeness = TenderCompletenessService(database)

    assert completeness.publication_summary(release_id).state is PublicationPackageState.UNKNOWN


def test_publication_complete_list_missing_item_is_missing(tmp_path: Path) -> None:
    database, documents, release_id = _workspace(tmp_path)
    member = _add_source(documents, release_id, tmp_path, "scope.pdf", b"scope")
    completeness = TenderCompletenessService(database)
    expectation_id = completeness.create_publication_expectation(
        release_id,
        basis=PublicationExpectationBasis.COMPLETE_LIST,
        authority="official-manifest",
        evidence="official source manifest",
        actor="bid-reviewer",
    )
    completeness.add_publication_item(expectation_id, "scope", "Scope document")
    completeness.add_publication_item(expectation_id, "technical", "Technical document")

    summary = completeness.reconcile_publication(
        release_id, expectation_id, observed_logical_keys={"scope": member.id}
    )
    assert summary.state is PublicationPackageState.MISSING
    assert summary.missing_count == 1


def test_publication_complete_list_before_reconciliation_is_unknown(tmp_path: Path) -> None:
    database, _documents, release_id = _workspace(tmp_path)
    completeness = TenderCompletenessService(database)
    expectation_id = completeness.create_publication_expectation(
        release_id,
        basis=PublicationExpectationBasis.COMPLETE_LIST,
        authority="official-manifest",
        evidence="official source manifest",
        actor="bid-reviewer",
    )
    completeness.add_publication_item(expectation_id, "scope", "Scope document")

    summary = completeness.publication_summary(release_id)
    assert summary.state is PublicationPackageState.UNKNOWN
    assert summary.unknown_count == 1


def test_publication_complete_list_with_all_items_is_complete(tmp_path: Path) -> None:
    database, documents, release_id = _workspace(tmp_path)
    member = _add_source(documents, release_id, tmp_path, "scope.pdf", b"scope")
    completeness = TenderCompletenessService(database)
    expectation_id = completeness.create_publication_expectation(
        release_id,
        basis=PublicationExpectationBasis.COMPLETE_LIST,
        authority="official-manifest",
        evidence="official source manifest",
        actor="bid-reviewer",
    )
    completeness.add_publication_item(expectation_id, "scope", "Scope document")

    summary = completeness.reconcile_publication(
        release_id, expectation_id, observed_logical_keys={"scope": member.id}
    )
    assert summary.state is PublicationPackageState.COMPLETE
    assert summary.missing_count == 0


def test_conflicting_authoritative_complete_lists_remain_visible(tmp_path: Path) -> None:
    database, _documents, release_id = _workspace(tmp_path)
    completeness = TenderCompletenessService(database)
    first = completeness.create_publication_expectation(
        release_id,
        basis=PublicationExpectationBasis.COMPLETE_LIST,
        authority="official-manifest-a",
        evidence="manifest A",
        actor="reviewer-a",
    )
    second = completeness.create_publication_expectation(
        release_id,
        basis=PublicationExpectationBasis.COMPLETE_LIST,
        authority="official-manifest-b",
        evidence="manifest B",
        actor="reviewer-b",
    )
    completeness.add_publication_item(first, "scope", "Scope document")
    completeness.add_publication_item(second, "technical", "Technical document")

    summary = completeness.publication_summary(release_id)
    assert summary.state is PublicationPackageState.CONFLICT
    assert summary.conflict_count == 1


def test_exact_revision_and_membership_guard_retrieval(tmp_path: Path) -> None:
    database, documents, release_id = _workspace(tmp_path)
    member = _add_source(documents, release_id, tmp_path, "same-name.pdf", b"source")
    completeness = TenderCompletenessService(database, document_root=tmp_path / "managed")
    destination = tmp_path / "retrieved.pdf"

    documents.retrieve_managed_original(member.id, destination)
    assert destination.read_bytes() == b"source"

    documents.managed_path(member.document_id).unlink()
    with pytest.raises(ManagedDocumentMissing):
        completeness.retrieve_document("case-1", release_id, member.id, tmp_path / "missing.pdf")
