"""Persistence port for append-only operational tender revision decisions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

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

    @property
    def base_id(self) -> str:
        return self.identity.base_id

    @property
    def revision(self) -> str:
        return self.identity.revision or ""


class TenderRevisionPersistence:
    """SQLAlchemy adapter for append-only operational revision events."""

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
    ) -> PersistedRevisionEvent:
        normalized_decision = str(decision or "").strip().upper()
        if normalized_decision not in {"ACCEPTED", "REJECTED"}:
            raise TenderRevisionPersistenceError("decision must be ACCEPTED or REJECTED")
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
            record = TenderOperationalRevisionEventRecord(
                case_id=case.id,
                release_id=release.id,
                base_id=release.base_id,
                revision=release.revision,
                decision=normalized_decision,
                actor=str(actor).strip(),
                reason=str(reason).strip(),
                evidence=str(evidence).strip(),
            )
            session.add(record)
            session.flush()
            return self._event(record, case.case_key)

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
                    TenderOperationalRevisionEventRecord.decision == "ACCEPTED",
                )
                .order_by(TenderOperationalRevisionEventRecord.id.desc())
            )
            return self._event(record, case.case_key) if record is not None else None

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
        )


__all__ = [
    "PersistedRevisionEvent",
    "TenderRevisionPersistence",
    "TenderRevisionPersistenceError",
]
