"""Application handoff from a confirmed Bid Radar observation to TenderCase."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .market_intelligence.opportunity_contract import OpportunitySourceType
from .market_intelligence.opportunity_radar import OpportunityRadarItem
from .market_intelligence.opportunity_review import (
    OpportunityReviewDecision,
    OpportunityReviewService,
)
from .tender_case import PlanContext
from .tender_workspace import TenderWorkspaceService


class OpportunityWorkspaceHandoffError(ValueError):
    """Raised when a confirmed observation cannot be safely routed."""


class OpportunityWorkspaceHandoffDisposition(StrEnum):
    OPENED_EXISTING = "OPENED_EXISTING"
    CREATED_PROVISIONAL_CASE = "CREATED_PROVISIONAL_CASE"
    CREATED_EXACT_RELEASE = "CREATED_EXACT_RELEASE"
    ADDED_EXACT_REVISION = "ADDED_EXACT_REVISION"


@dataclass(frozen=True, slots=True)
class OpportunityWorkspaceHandoffResult:
    disposition: OpportunityWorkspaceHandoffDisposition
    case_id: str
    source_type: OpportunitySourceType
    identity_raw_id: str
    release_id: int | None
    release_raw_id: str | None
    human_link_required: bool
    created_case: bool
    created_release: bool


class OpportunityWorkspaceHandoffService:
    """Route only the latest persisted CONFIRMED observation to a workspace."""

    def __init__(
        self,
        review_service: OpportunityReviewService,
        workspace_service: TenderWorkspaceService,
    ) -> None:
        self.review_service = review_service
        self.workspace_service = workspace_service

    def handoff(self, item: OpportunityRadarItem) -> OpportunityWorkspaceHandoffResult:
        # This must remain the first operation: the GUI's cached row is not authority.
        latest_review = self.review_service.current_event(item)
        if latest_review is None or latest_review.decision is not OpportunityReviewDecision.CONFIRMED:
            raise OpportunityWorkspaceHandoffError(
                "only the latest persisted CONFIRMED review may open a workspace"
            )
        if item.source_type is OpportunitySourceType.TBMT:
            return self._handoff_tbmt(item)
        if item.source_type is OpportunitySourceType.KHMT:
            return self._handoff_khmt(item)
        raise OpportunityWorkspaceHandoffError("unsupported opportunity source type")

    def _handoff_tbmt(self, item: OpportunityRadarItem) -> OpportunityWorkspaceHandoffResult:
        identity = item.identity
        if identity.namespace.value != "IB" or not identity.revision:
            raise OpportunityWorkspaceHandoffError(
                "TBMT handoff requires an exact IB revision"
            )

        exact = tuple(
            result
            for result in self.workspace_service.search_cases(identity.raw_id)
            if result.release_raw_id == identity.raw_id
        )
        exact_cases = _case_ids(exact)
        if len(exact_cases) > 1:
            raise OpportunityWorkspaceHandoffError(
                "exact IB release is ambiguous across TenderCases"
            )
        if exact_cases:
            result = exact[0]
            return self._result(
                OpportunityWorkspaceHandoffDisposition.OPENED_EXISTING,
                result.case_id,
                item,
                result.release_id,
                result.release_raw_id,
            )

        lineage = tuple(
            result
            for result in self.workspace_service.search_cases(identity.base_id)
            if result.release_base_id == identity.base_id
        )
        lineage_cases = _case_ids(lineage)
        if len(lineage_cases) > 1:
            raise OpportunityWorkspaceHandoffError(
                "IB lineage is ambiguous across TenderCases"
            )
        if lineage_cases:
            case_id = next(iter(lineage_cases))
            release = self.workspace_service.add_release(case_id, identity)
            return self._result(
                OpportunityWorkspaceHandoffDisposition.ADDED_EXACT_REVISION,
                case_id,
                item,
                release.release_id,
                release.raw_id,
                created_release=True,
            )

        case_id = identity.base_id
        self.workspace_service.create_case(case_id)
        release = self.workspace_service.add_release(case_id, identity)
        return self._result(
            OpportunityWorkspaceHandoffDisposition.CREATED_EXACT_RELEASE,
            case_id,
            item,
            release.release_id,
            release.raw_id,
            created_case=True,
            created_release=True,
        )

    def _handoff_khmt(self, item: OpportunityRadarItem) -> OpportunityWorkspaceHandoffResult:
        identity = item.identity
        if identity.namespace.value != "PL":
            raise OpportunityWorkspaceHandoffError("KHMT handoff requires a PL identity")

        exact = tuple(
            result
            for result in self.workspace_service.search_cases(identity.raw_id)
            if result.plan_raw_id == identity.raw_id
        )
        exact_cases = _case_ids(exact)
        if len(exact_cases) > 1:
            raise OpportunityWorkspaceHandoffError(
                "exact PL PlanContext is ambiguous across TenderCases"
            )
        if exact_cases:
            return self._result(
                OpportunityWorkspaceHandoffDisposition.OPENED_EXISTING,
                next(iter(exact_cases)),
                item,
                None,
                None,
                human_link_required=not bool(exact[0].release_id),
            )

        other_revision = tuple(
            result
            for result in self.workspace_service.search_cases(identity.base_id)
            if result.plan_base_id == identity.base_id
            and result.plan_raw_id is not None
            and result.plan_raw_id != identity.raw_id
        )
        if other_revision:
            raise OpportunityWorkspaceHandoffError(
                "another exact PL revision exists; human resolution is required"
            )

        case_id = identity.raw_id
        self.workspace_service.create_case(case_id, plan_context=PlanContext(identity))
        return self._result(
            OpportunityWorkspaceHandoffDisposition.CREATED_PROVISIONAL_CASE,
            case_id,
            item,
            None,
            None,
            human_link_required=True,
            created_case=True,
        )

    @staticmethod
    def _result(
        disposition: OpportunityWorkspaceHandoffDisposition,
        case_id: str,
        item: OpportunityRadarItem,
        release_id: int | None,
        release_raw_id: str | None,
        *,
        human_link_required: bool = False,
        created_case: bool = False,
        created_release: bool = False,
    ) -> OpportunityWorkspaceHandoffResult:
        return OpportunityWorkspaceHandoffResult(
            disposition=disposition,
            case_id=case_id,
            source_type=item.source_type,
            identity_raw_id=item.identity.raw_id,
            release_id=release_id,
            release_raw_id=release_raw_id,
            human_link_required=human_link_required,
            created_case=created_case,
            created_release=created_release,
        )


def _case_ids(results) -> frozenset[str]:
    return frozenset(result.case_id for result in results)


__all__ = [
    "OpportunityWorkspaceHandoffDisposition",
    "OpportunityWorkspaceHandoffError",
    "OpportunityWorkspaceHandoffResult",
    "OpportunityWorkspaceHandoffService",
]
