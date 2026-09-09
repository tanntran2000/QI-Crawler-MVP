"""Append-only persistence for managed-source recovery evidence."""

from __future__ import annotations

from sqlalchemy import select

from .db import Database
from .models import TenderRecoveryEventRecord


class TenderRecoveryPersistence:
    def __init__(self, database: Database):
        self.database = database

    def append(
        self,
        *,
        case_id: int | None,
        release_id: int | None,
        membership_id: int | None,
        document_id: int | None,
        action: str,
        expected_sha256: str | None,
        observed_sha256: str | None,
        candidate_sha256: str | None,
        managed_path: str | None,
        candidate_path: str | None,
        quarantine_path: str | None,
        actor: str,
        reason: str,
        evidence: str,
        result: str,
    ) -> TenderRecoveryEventRecord:
        record = TenderRecoveryEventRecord(
            case_id=case_id,
            release_id=release_id,
            membership_id=membership_id,
            document_id=document_id,
            action=action,
            expected_sha256=expected_sha256,
            observed_sha256=observed_sha256,
            candidate_sha256=candidate_sha256,
            managed_path=managed_path,
            candidate_path=candidate_path,
            quarantine_path=quarantine_path,
            actor=actor,
            reason=reason,
            evidence=evidence,
            result=result,
        )
        with self.database.session() as session:
            session.add(record)
            session.flush()
            session.expunge(record)
        return record

    def list(
        self, *, case_id: int | None = None, release_id: int | None = None
    ) -> tuple[TenderRecoveryEventRecord, ...]:
        with self.database.session() as session:
            query = select(TenderRecoveryEventRecord).order_by(TenderRecoveryEventRecord.id)
            if case_id is not None:
                query = query.where(TenderRecoveryEventRecord.case_id == case_id)
            if release_id is not None:
                query = query.where(TenderRecoveryEventRecord.release_id == release_id)
            rows = tuple(session.scalars(query))
            for row in rows:
                session.expunge(row)
        return rows
