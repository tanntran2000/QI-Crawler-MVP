"""Domain Core values for source-neutral Human Review."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .opportunity_contract import (
    OpportunityIdentityNamespace,
    OpportunitySourceType,
)
from .opportunity_radar import OpportunityRadarItem


class OpportunityReviewError(ValueError):
    """Raised when a review lacks a valid source identity or human authority."""


class OpportunityReviewDecision(StrEnum):
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


@dataclass(frozen=True, slots=True)
class OpportunityReviewIdentity:
    observation_key: str
    source_type: OpportunitySourceType
    identity_namespace: OpportunityIdentityNamespace
    identity_raw: str
    identity_base_id: str
    identity_revision: str | None
    source_sha256: str
    source_sheet: str
    source_row: int

    @classmethod
    def from_item(cls, item: OpportunityRadarItem) -> OpportunityReviewIdentity:
        if not isinstance(item, OpportunityRadarItem):
            raise OpportunityReviewError("Review identity requires an OpportunityRadarItem.")
        return cls(
            observation_key=item.observation_key,
            source_type=item.source_type,
            identity_namespace=item.identity.namespace,
            identity_raw=item.identity.raw_id,
            identity_base_id=item.identity.base_id,
            identity_revision=item.identity.revision,
            source_sha256=item.source_sha256,
            source_sheet=item.sheet,
            source_row=item.source_row,
        )


@dataclass(frozen=True, slots=True)
class OpportunityReviewRecord:
    event_id: int
    identity: OpportunityReviewIdentity
    decision: OpportunityReviewDecision
    reviewer: str
    note: str | None
    opportunity_snapshot_json: str
    snapshot_schema_version: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class OpportunityReviewWrite:
    identity: OpportunityReviewIdentity
    decision: OpportunityReviewDecision
    reviewer: str
    note: str | None
    opportunity_snapshot_json: str
    snapshot_schema_version: str


__all__ = [
    "OpportunityReviewDecision",
    "OpportunityReviewError",
    "OpportunityReviewIdentity",
    "OpportunityReviewRecord",
    "OpportunityReviewWrite",
]
