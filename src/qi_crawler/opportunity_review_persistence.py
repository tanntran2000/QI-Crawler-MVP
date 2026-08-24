"""SQLAlchemy persistence adapter for source-neutral opportunity reviews."""

from __future__ import annotations

from collections.abc import Mapping

from sqlalchemy import select

from .db import Database
from .market_intelligence.opportunity_contract import (
    OpportunityIdentityNamespace,
    OpportunitySourceType,
)
from .market_intelligence.opportunity_review import (
    OpportunityReviewRepository,
)
from .market_intelligence.opportunity_review_contract import (
    OpportunityReviewDecision,
    OpportunityReviewIdentity,
    OpportunityReviewRecord,
    OpportunityReviewWrite,
)
from .models import OpportunityReviewEvent


class SqlAlchemyOpportunityReviewRepository(OpportunityReviewRepository):
    """Persist review events without changing review authority semantics."""

    def __init__(self, database: Database) -> None:
        self.database = database
        self.database.require_current_schema()

    def latest(self, observation_key: str) -> OpportunityReviewRecord | None:
        with self.database.session() as session:
            event = session.scalar(
                select(OpportunityReviewEvent)
                .where(OpportunityReviewEvent.observation_key == observation_key)
                .order_by(OpportunityReviewEvent.id.desc())
                .limit(1)
            )
            return _to_record(event) if event is not None else None

    def history(self, observation_key: str) -> tuple[OpportunityReviewRecord, ...]:
        with self.database.session() as session:
            events = session.scalars(
                select(OpportunityReviewEvent)
                .where(OpportunityReviewEvent.observation_key == observation_key)
                .order_by(OpportunityReviewEvent.id)
            ).all()
            return tuple(_to_record(event) for event in events)

    def append(self, write: OpportunityReviewWrite) -> OpportunityReviewRecord:
        event = OpportunityReviewEvent(
            observation_key=write.identity.observation_key,
            source_type=write.identity.source_type.value,
            identity_namespace=write.identity.identity_namespace.value,
            identity_raw=write.identity.identity_raw,
            identity_base_id=write.identity.identity_base_id,
            identity_revision=write.identity.identity_revision,
            source_sha256=write.identity.source_sha256,
            source_sheet=write.identity.source_sheet,
            source_row=write.identity.source_row,
            decision=write.decision.value,
            reviewer=write.reviewer,
            note=write.note,
            opportunity_snapshot_json=write.opportunity_snapshot_json,
            snapshot_schema_version=write.snapshot_schema_version,
        )
        with self.database.session() as session:
            session.add(event)
            session.flush()
            return _to_record(event)

    def latest_for_keys(
        self, observation_keys: tuple[str, ...]
    ) -> Mapping[str, OpportunityReviewRecord]:
        if not observation_keys:
            return {}
        with self.database.session() as session:
            events = session.scalars(
                select(OpportunityReviewEvent)
                .where(OpportunityReviewEvent.observation_key.in_(observation_keys))
                .order_by(OpportunityReviewEvent.id)
            ).all()
            latest: dict[str, OpportunityReviewRecord] = {}
            for event in events:
                latest[event.observation_key] = _to_record(event)
            return latest


def _to_record(event: OpportunityReviewEvent) -> OpportunityReviewRecord:
    identity = OpportunityReviewIdentity(
        observation_key=event.observation_key,
        source_type=OpportunitySourceType(event.source_type),
        identity_namespace=OpportunityIdentityNamespace(event.identity_namespace),
        identity_raw=event.identity_raw,
        identity_base_id=event.identity_base_id,
        identity_revision=event.identity_revision,
        source_sha256=event.source_sha256,
        source_sheet=event.source_sheet,
        source_row=event.source_row,
    )
    return OpportunityReviewRecord(
        event_id=event.id,
        identity=identity,
        decision=OpportunityReviewDecision(event.decision),
        reviewer=event.reviewer,
        note=event.note,
        opportunity_snapshot_json=event.opportunity_snapshot_json,
        snapshot_schema_version=event.snapshot_schema_version,
        created_at=event.created_at,
    )


__all__ = ["SqlAlchemyOpportunityReviewRepository"]
