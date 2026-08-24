"""Domain Core values for source-neutral Human Review."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .opportunity_contract import (
    OpportunityIdentityNamespace,
    OpportunitySourceType,
)


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
