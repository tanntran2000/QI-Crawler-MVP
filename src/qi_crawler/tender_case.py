"""Database-independent domain contract for the minimum tender warehouse.

The domain keeps procurement-plan (PL) lineage separate from tender-notice
(IB) publication identities.  Persistence and application services adapt this
contract; this module deliberately has no SQLAlchemy, filesystem, or GUI
dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from .market_intelligence.opportunity_contract import (
    OpportunityIdentity,
    OpportunityIdentityNamespace,
)


class TenderCaseError(ValueError):
    """Base error for invalid tender-case domain state."""


class TenderReleaseError(TenderCaseError):
    """Raised when an IB release is missing or duplicated."""


class AuthorityClass(StrEnum):
    SOURCE_E_HSMT = "SOURCE_E_HSMT"
    DERIVED_REQUIREMENT = "DERIVED_REQUIREMENT"
    WORKING_E_HSDT = "WORKING_E_HSDT"
    FINAL_SUBMISSION = "FINAL_SUBMISSION"
    EVIDENCE_ARCHIVE = "EVIDENCE_ARCHIVE"
    REFERENCE_ONLY = "REFERENCE_ONLY"


class TenderCaseStatus(StrEnum):
    PROVISIONAL = "PROVISIONAL"
    LINKED = "LINKED"


@dataclass(frozen=True, slots=True)
class PlanContext:
    """Optional plan lineage; a PL identity is never converted into an IB."""

    identity: OpportunityIdentity

    def __post_init__(self) -> None:
        if not isinstance(self.identity, OpportunityIdentity):
            raise TenderCaseError("plan context requires an OpportunityIdentity")
        if self.identity.namespace is not OpportunityIdentityNamespace.PL:
            raise TenderCaseError("plan context requires PL identity")


@dataclass(frozen=True, slots=True)
class TenderRelease:
    """One exact IB publication revision within a tender case."""

    identity: OpportunityIdentity
    notice_id: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.identity, OpportunityIdentity):
            raise TenderReleaseError("release requires an OpportunityIdentity")
        if self.identity.namespace is not OpportunityIdentityNamespace.IB:
            raise TenderReleaseError("tender release requires IB identity")
        if not self.identity.revision:
            raise TenderReleaseError("tender release requires an exact revision")
        if self.notice_id is not None and (
            not isinstance(self.notice_id, int) or isinstance(self.notice_id, bool) or self.notice_id < 1
        ):
            raise TenderReleaseError("notice_id must be a positive integer")


@dataclass(frozen=True, slots=True)
class TenderDocumentMembership:
    """An explicit document-to-release link, separate from document identity."""

    release: TenderRelease
    document_id: int
    authority: AuthorityClass
    evidence: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not isinstance(self.release, TenderRelease):
            raise TenderCaseError("membership requires a TenderRelease")
        if not isinstance(self.document_id, int) or isinstance(self.document_id, bool) or self.document_id < 1:
            raise TenderCaseError("document_id must be a positive integer")
        try:
            authority = AuthorityClass(self.authority)
        except ValueError as exc:
            raise TenderCaseError("unsupported document authority") from exc
        if not isinstance(self.evidence, str) or not self.evidence.strip():
            raise TenderCaseError("membership evidence is required")
        if not isinstance(self.created_at, datetime):
            raise TenderCaseError("created_at must be a datetime")
        object.__setattr__(self, "authority", authority)


@dataclass(frozen=True, slots=True)
class TenderCase:
    """Immutable aggregate snapshot for one human-managed tender case."""

    case_id: str
    plan_context: PlanContext | None = None
    releases: tuple[TenderRelease, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.case_id, str) or not self.case_id.strip():
            raise TenderCaseError("case_id must be non-empty")
        if self.plan_context is not None and not isinstance(self.plan_context, PlanContext):
            raise TenderCaseError("plan_context must be a PlanContext")
        releases = tuple(self.releases)
        if any(not isinstance(release, TenderRelease) for release in releases):
            raise TenderCaseError("releases must contain TenderRelease values")
        identities = [release.identity for release in releases]
        if len(set(identities)) != len(identities):
            raise TenderReleaseError("duplicate exact release")
        object.__setattr__(self, "releases", releases)

    @property
    def status(self) -> TenderCaseStatus:
        return TenderCaseStatus.LINKED if self.releases else TenderCaseStatus.PROVISIONAL

    @property
    def human_link_required(self) -> bool:
        return not self.releases

    def add_release(self, release: TenderRelease) -> TenderCase:
        if not isinstance(release, TenderRelease):
            raise TenderReleaseError("release must be a TenderRelease")
        if release.identity in {item.identity for item in self.releases}:
            raise TenderReleaseError("duplicate exact release")
        return TenderCase(
            case_id=self.case_id,
            plan_context=self.plan_context,
            releases=self.releases + (release,),
        )
