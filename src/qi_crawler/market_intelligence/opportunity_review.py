"""Source-neutral Human Review application backend.

This module owns review normalization and authority semantics for opportunity
observations.  Persistence is supplied through a repository port so the
backend remains independent of SQLAlchemy and delivery surfaces.
"""

from __future__ import annotations

import json
import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum, StrEnum
from typing import Any, Protocol

from .opportunity_contract import (
    OpportunityIdentityNamespace,
    OpportunitySourceType,
)
from .opportunity_radar import OpportunityRadarItem

SNAPSHOT_SCHEMA_VERSION = "mi-opportunity-review-v1"


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


class OpportunityReviewRepository(Protocol):
    def latest(self, observation_key: str) -> OpportunityReviewRecord | None: ...

    def history(self, observation_key: str) -> tuple[OpportunityReviewRecord, ...]: ...

    def append(self, write: OpportunityReviewWrite) -> OpportunityReviewRecord: ...

    def latest_for_keys(
        self, observation_keys: tuple[str, ...]
    ) -> Mapping[str, OpportunityReviewRecord]: ...


class OpportunityReviewService:
    """Application authority for explicit, append-only opportunity reviews."""

    def __init__(self, repository: OpportunityReviewRepository) -> None:
        self.repository = repository

    def record_decision(
        self,
        item: OpportunityRadarItem,
        *,
        decision: OpportunityReviewDecision | str,
        reviewer: str,
        note: str | None = None,
    ) -> OpportunityReviewRecord:
        identity = OpportunityReviewIdentity.from_item(item)
        normalized_decision = _decision(decision)
        normalized_reviewer = _required_text("reviewer", reviewer)
        normalized_note = note.strip() if note and note.strip() else None
        snapshot = serialize_opportunity_snapshot(item)
        latest = self.repository.latest(identity.observation_key)
        if latest is not None and (
            latest.decision,
            latest.reviewer,
            latest.note,
        ) == (
            normalized_decision,
            normalized_reviewer,
            normalized_note,
        ):
            return latest
        return self.repository.append(
            OpportunityReviewWrite(
                identity=identity,
                decision=normalized_decision,
                reviewer=normalized_reviewer,
                note=normalized_note,
                opportunity_snapshot_json=snapshot,
                snapshot_schema_version=SNAPSHOT_SCHEMA_VERSION,
            )
        )

    def current_event(self, item: OpportunityRadarItem) -> OpportunityReviewRecord | None:
        identity = OpportunityReviewIdentity.from_item(item)
        return self.repository.latest(identity.observation_key)

    def list_history(self, item: OpportunityRadarItem) -> tuple[OpportunityReviewRecord, ...]:
        identity = OpportunityReviewIdentity.from_item(item)
        return self.repository.history(identity.observation_key)

    def current_confirmed(
        self, items: Iterable[OpportunityRadarItem]
    ) -> tuple[OpportunityReviewRecord, ...]:
        universe = tuple(items)
        identities = tuple(OpportunityReviewIdentity.from_item(item) for item in universe)
        keys = tuple(dict.fromkeys(identity.observation_key for identity in identities))
        if not keys:
            return ()
        latest_by_key = self.repository.latest_for_keys(keys)
        confirmed: list[OpportunityReviewRecord] = []
        seen: set[str] = set()
        for identity in identities:
            if identity.observation_key in seen:
                continue
            seen.add(identity.observation_key)
            record = latest_by_key.get(identity.observation_key)
            if record is not None and record.decision is OpportunityReviewDecision.CONFIRMED:
                confirmed.append(record)
        return tuple(confirmed)


def serialize_opportunity_snapshot(item: OpportunityRadarItem) -> str:
    """Serialize one source observation without losing raw/provenance values."""

    identity = OpportunityReviewIdentity.from_item(item)
    payload = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "source": {
            "source_type": identity.source_type,
            "identity_namespace": identity.identity_namespace,
            "identity_raw": identity.identity_raw,
            "identity_base_id": identity.identity_base_id,
            "identity_revision": identity.identity_revision,
            "observation_key": identity.observation_key,
            "filename": item.source_filename,
            "sha256": item.source_sha256,
            "sheet": item.sheet,
            "row": item.source_row,
            "schema_version": item.schema_version,
        },
        "opportunity": {
            "package_name": item.package_name,
            "project": item.project,
            "package_price_raw": item.package_price_raw,
            "package_price": item.package_price,
            "funding_source": item.funding_source,
            "investor": item.investor,
            "procuring_entity": item.procuring_entity,
            "approval_content": item.approval_content,
            "package_main_content": item.package_main_content,
            "selection_method": item.selection_method,
            "procurement_method": item.procurement_method,
            "location_detail_raw": item.location_detail_raw,
            "province_city_code": item.province_city_code,
            "province_city_name": item.province_city_name,
            "province_city_status": item.province_city_status,
            "province_city_evidence": item.province_city_evidence,
        },
        "source_fields": item.source_fields,
        "raw_fields": item.raw_fields,
        "provenance": item.provenance,
    }
    return json.dumps(
        _json_safe(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise OpportunityReviewError("Snapshot contains a non-finite number.")
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Enum):
        return _json_safe(value.value)
    if isinstance(value, Mapping):
        return {
            str(key): _json_safe(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    raise OpportunityReviewError(f"Unsupported snapshot value: {type(value).__name__}.")


def _decision(value: OpportunityReviewDecision | str) -> OpportunityReviewDecision:
    try:
        return OpportunityReviewDecision(str(value).strip().upper())
    except ValueError as exc:
        raise OpportunityReviewError("Invalid opportunity review decision.") from exc


def _required_text(name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise OpportunityReviewError(f"{name} is required.")
    return value.strip()


__all__ = [
    "SNAPSHOT_SCHEMA_VERSION",
    "OpportunityReviewDecision",
    "OpportunityReviewError",
    "OpportunityReviewIdentity",
    "OpportunityReviewRecord",
    "OpportunityReviewRepository",
    "OpportunityReviewService",
    "OpportunityReviewWrite",
    "serialize_opportunity_snapshot",
]
