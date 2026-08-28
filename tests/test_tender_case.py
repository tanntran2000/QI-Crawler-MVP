from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from qi_crawler.market_intelligence.opportunity_contract import (
    OpportunityIdentity,
    OpportunityIdentityNamespace,
)
from qi_crawler.tender_case import (
    AuthorityClass,
    PlanContext,
    TenderCase,
    TenderCaseStatus,
    TenderDocumentMembership,
    TenderRelease,
    TenderReleaseError,
)


def _identity(raw: str) -> OpportunityIdentity:
    return OpportunityIdentity.from_raw(raw)


def test_plan_context_accepts_pl_only() -> None:
    context = PlanContext(_identity("PL2600000001-00"))
    assert context.identity.namespace is OpportunityIdentityNamespace.PL


def test_plan_context_rejects_ib_namespace() -> None:
    with pytest.raises(ValueError, match="PL"):
        PlanContext(_identity("IB2600000001-00"))


def test_provisional_case_has_no_fabricated_ib() -> None:
    case = TenderCase(case_id="case-1")
    assert case.status is TenderCaseStatus.PROVISIONAL
    assert case.human_link_required is True
    assert case.releases == ()


def test_tender_release_requires_ib_exact_revision() -> None:
    with pytest.raises(TenderReleaseError, match="IB"):
        TenderRelease(_identity("PL2600000001-00"))
    with pytest.raises(TenderReleaseError, match="revision"):
        TenderRelease(_identity("IB2600000001"))


def test_revisions_coexist_and_exact_duplicate_is_rejected() -> None:
    case = TenderCase(case_id="case-1")
    first = TenderRelease(_identity("IB2600000001-00"))
    second = TenderRelease(_identity("IB2600000001-01"))
    case = case.add_release(first).add_release(second)
    assert [release.identity.raw_id for release in case.releases] == [
        "IB2600000001-00",
        "IB2600000001-01",
    ]
    with pytest.raises(TenderReleaseError, match="duplicate"):
        case.add_release(first)


def test_adding_revision_does_not_mutate_original_case() -> None:
    case = TenderCase(case_id="case-1").add_release(
        TenderRelease(_identity("IB2600000001-00"))
    )
    revised = case.add_release(TenderRelease(_identity("IB2600000001-01")))
    assert len(case.releases) == 1
    assert len(revised.releases) == 2


def test_document_membership_keeps_authority_separate_from_document_identity() -> None:
    membership = TenderDocumentMembership(
        release=TenderRelease(_identity("IB2600000001-00")),
        document_id=42,
        authority=AuthorityClass.SOURCE_E_HSMT,
        evidence="content:page:1",
    )
    assert membership.document_id == 42
    assert membership.authority is AuthorityClass.SOURCE_E_HSMT
    with pytest.raises(FrozenInstanceError):
        membership.document_id = 7
