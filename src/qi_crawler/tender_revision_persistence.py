"""Persistence port for append-only operational tender revision decisions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar

from sqlalchemy import select

from .db import Database
from .market_intelligence.opportunity_contract import OpportunityIdentity
from .models import (
    Document,
    TenderCaseRecord,
    TenderDocumentMembershipRecord,
    TenderOperationalRevisionEventRecord,
    TenderReleaseRecord,
    TenderWorkspaceEntryRecord,
)
from .tender_case import TenderCaseError
from .tender_case_persistence import TenderCasePersistence


class TenderRevisionPersistenceError(TenderCaseError):
    """Raised when an operational revision event cannot be persisted safely."""


@dataclass(frozen=True, slots=True)
class PersistedRevisionEvent:
    event_id: int
    case_id: str
    release_id: int
    identity: OpportunityIdentity
    decision: str
    actor: str
    reason: str
    evidence: str
    created_at: datetime
    from_release_id: int | None = None
    comparison_schema_version: str | None = None
    comparison_payload: str | None = None
    source_observation_complete: bool | None = None
    completeness_evidence: str | None = None
    accepted_at: datetime | None = None
    activated_at: datetime | None = None

    @property
    def base_id(self) -> str:
        return self.identity.base_id

    @property
    def revision(self) -> str:
        return self.identity.revision or ""


class TenderRevisionPersistence:
    """SQLAlchemy adapter for append-only operational revision events."""

    _DECISIONS: ClassVar[frozenset[str]] = frozenset({
        "ACCEPTED",
        "REJECTED",
        "ACCEPTED_PENDING",
        "TRANSITION_ACTIVATED",
        "COMPARISON",
    })

    def __init__(self, database: Database):
        self.database = database
        self.database.require_current_schema()
        self.case_persistence = TenderCasePersistence(database)

    def _case(self, session, case_id: str) -> TenderCaseRecord:
        record = session.scalar(
            select(TenderCaseRecord).where(TenderCaseRecord.case_key == case_id)
        )
        if record is None:
            raise TenderRevisionPersistenceError("case not found")
        return record

    def release_record(self, case_id: str, release_id: int) -> TenderReleaseRecord:
        with self.database.session() as session:
            case = self._case(session, case_id)
            release = session.get(TenderReleaseRecord, release_id)
            if release is None:
                raise TenderRevisionPersistenceError("release not found")
            if release.case_id != case.id:
                raise TenderRevisionPersistenceError("release does not belong to case")
            return release

    def record_event(
        self,
        case_id: str,
        release_id: int,
        decision: str,
        *,
        actor: str,
        reason: str,
        evidence: str,
        from_release_id: int | None = None,
        comparison_schema_version: str | None = None,
        comparison_payload: str | None = None,
        source_observation_complete: bool | None = None,
        completeness_evidence: str | None = None,
        accepted_at: datetime | None = None,
        activated_at: datetime | None = None,
    ) -> PersistedRevisionEvent:
        normalized_decision = str(decision or "").strip().upper()
        if normalized_decision not in self._DECISIONS:
            raise TenderRevisionPersistenceError("unsupported revision event")
        if not str(actor or "").strip():
            raise TenderRevisionPersistenceError("actor is required")
        if not str(reason or "").strip():
            raise TenderRevisionPersistenceError("reason is required")
        if not str(evidence or "").strip():
            raise TenderRevisionPersistenceError("evidence is required")
        with self.database.session() as session:
            case = self._case(session, case_id)
            release = session.get(TenderReleaseRecord, release_id)
            if release is None:
                raise TenderRevisionPersistenceError("release not found")
            if release.case_id != case.id:
                raise TenderRevisionPersistenceError("release does not belong to case")
            if from_release_id is not None:
                from_release = session.get(TenderReleaseRecord, from_release_id)
                if from_release is None or from_release.case_id != case.id:
                    raise TenderRevisionPersistenceError("from release does not belong to case")
            record = TenderOperationalRevisionEventRecord(
                case_id=case.id,
                release_id=release.id,
                base_id=release.base_id,
                revision=release.revision,
                decision=normalized_decision,
                from_release_id=from_release_id,
                comparison_schema_version=comparison_schema_version,
                comparison_payload=comparison_payload,
                source_observation_complete=source_observation_complete,
                completeness_evidence=completeness_evidence,
                accepted_at=accepted_at,
                activated_at=activated_at,
                actor=str(actor).strip(),
                reason=str(reason).strip(),
                evidence=str(evidence).strip(),
            )
            session.add(record)
            session.flush()
            return self._event(record, case.case_key)

    def record_comparison(
        self,
        case_id: str,
        previous_release_id: int,
        latest_release_id: int,
        *,
        payload: str,
        schema_version: str,
        actor: str,
        reason: str,
        evidence: str,
        source_observation_complete: bool | None = None,
        completeness_evidence: str | None = None,
    ) -> PersistedRevisionEvent:
        return self.record_event(
            case_id,
            latest_release_id,
            "COMPARISON",
            actor=actor,
            reason=reason,
            evidence=evidence,
            from_release_id=previous_release_id,
            comparison_schema_version=schema_version,
            comparison_payload=payload,
            source_observation_complete=source_observation_complete,
            completeness_evidence=completeness_evidence,
        )

    def events_for_case(self, case_id: str) -> tuple[PersistedRevisionEvent, ...]:
        with self.database.session() as session:
            case = self._case(session, case_id)
            records = tuple(
                session.scalars(
                    select(TenderOperationalRevisionEventRecord)
                    .where(TenderOperationalRevisionEventRecord.case_id == case.id)
                    .order_by(TenderOperationalRevisionEventRecord.id)
                )
            )
            return tuple(self._event(record, case.case_key) for record in records)

    def latest_event(self, case_id: str) -> PersistedRevisionEvent | None:
        events = self.events_for_case(case_id)
        return events[-1] if events else None

    def latest_accepted(self, case_id: str) -> PersistedRevisionEvent | None:
        with self.database.session() as session:
            case = self._case(session, case_id)
            record = session.scalar(
                select(TenderOperationalRevisionEventRecord)
                .where(
                    TenderOperationalRevisionEventRecord.case_id == case.id,
                    TenderOperationalRevisionEventRecord.decision.in_(
                        {"ACCEPTED", "TRANSITION_ACTIVATED"}
                    ),
                )
                .order_by(TenderOperationalRevisionEventRecord.id.desc())
            )
            return self._event(record, case.case_key) if record is not None else None

    def latest_pending(self, case_id: str) -> PersistedRevisionEvent | None:
        pending: PersistedRevisionEvent | None = None
        for event in self.events_for_case(case_id):
            if event.decision == "ACCEPTED_PENDING":
                if pending is not None and pending.release_id != event.release_id:
                    raise TenderRevisionPersistenceError("conflicting pending transitions")
                pending = event
            elif pending is not None and event.release_id == pending.release_id and event.decision in {
                "TRANSITION_ACTIVATED",
                "REJECTED",
            }:
                pending = None
        return pending

    pending_transition = latest_pending

    def latest_comparison(
        self, case_id: str, previous_release_id: int, latest_release_id: int
    ) -> PersistedRevisionEvent | None:
        matches = [
            event
            for event in self.events_for_case(case_id)
            if event.decision == "COMPARISON"
            and event.from_release_id == previous_release_id
            and event.release_id == latest_release_id
        ]
        return matches[-1] if matches else None

    def operational_latest(self, case_id: str) -> PersistedRevisionEvent | None:
        return self.latest_accepted(case_id)

    def document_snapshot(self, case_id: str, release_id: int) -> dict[str, str]:
        """Return a bounded slot-to-SHA snapshot for one exact release."""
        with self.database.session() as session:
            case = self._case(session, case_id)
            release = session.get(TenderReleaseRecord, release_id)
            if release is None:
                raise TenderRevisionPersistenceError("release not found")
            if release.case_id != case.id:
                raise TenderRevisionPersistenceError("release does not belong to case")
            rows = session.execute(
                select(TenderWorkspaceEntryRecord, Document.sha256)
                .join(
                    TenderDocumentMembershipRecord,
                    TenderWorkspaceEntryRecord.membership_id
                    == TenderDocumentMembershipRecord.id,
                )
                .join(Document, TenderDocumentMembershipRecord.document_id == Document.id)
                .where(TenderDocumentMembershipRecord.release_id == release_id)
                .order_by(TenderWorkspaceEntryRecord.id)
            ).all()
            return {
                entry.slot_key or f"membership:{entry.membership_id}": sha256
                for entry, sha256 in rows
            }

    @staticmethod
    def _event(
        record: TenderOperationalRevisionEventRecord, case_id: str
    ) -> PersistedRevisionEvent:
        return PersistedRevisionEvent(
            event_id=record.id,
            case_id=case_id,
            release_id=record.release_id,
            identity=OpportunityIdentity.from_raw(record.base_id + "-" + record.revision),
            decision=record.decision,
            actor=record.actor,
            reason=record.reason,
            evidence=record.evidence,
            created_at=record.created_at,
            from_release_id=record.from_release_id,
            comparison_schema_version=record.comparison_schema_version,
            comparison_payload=record.comparison_payload,
            source_observation_complete=record.source_observation_complete,
            completeness_evidence=record.completeness_evidence,
            accepted_at=record.accepted_at,
            activated_at=record.activated_at,
        )


__all__ = [
    "PersistedRevisionEvent",
    "TenderRevisionPersistence",
    "TenderRevisionPersistenceError",
]
