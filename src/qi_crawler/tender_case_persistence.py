"""Persistence port for the domain-first tender-case aggregate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .db import Database
from .market_intelligence.opportunity_contract import OpportunityIdentity
from .models import (
    TenderCaseRecord,
    TenderDocumentMembershipRecord,
    TenderReleaseRecord,
)
from .tender_case import (
    AuthorityClass,
    PlanContext,
    TenderCase,
    TenderCaseError,
    TenderDocumentMembership,
    TenderRelease,
    TenderReleaseError,
)


@dataclass(frozen=True, slots=True)
class PersistedTenderRelease:
    release_id: int
    case_id: int
    release: TenderRelease

    @property
    def raw_id(self) -> str:
        return self.release.identity.raw_id

    @property
    def base_id(self) -> str:
        return self.release.identity.base_id

    @property
    def revision(self) -> str:
        return self.release.identity.revision or ""


class TenderCasePersistence:
    """Small SQLAlchemy adapter; domain objects remain database-independent."""

    def __init__(self, database: Database):
        self.database = database
        self.database.require_current_schema()

    def create_case(
        self, case_key: str, *, plan_context: PlanContext | None = None
    ) -> TenderCase:
        case = TenderCase(case_id=case_key, plan_context=plan_context)
        try:
            with self.database.session() as session:
                session.add(
                    TenderCaseRecord(
                        case_key=case.case_id,
                        plan_id_raw=(
                            plan_context.identity.raw_id if plan_context is not None else None
                        ),
                        plan_base_id=(
                            plan_context.identity.base_id if plan_context is not None else None
                        ),
                        plan_revision=(
                            plan_context.identity.revision if plan_context is not None else None
                        ),
                        status=case.status.value,
                    )
                )
        except IntegrityError as exc:
            raise TenderCaseError("tender case already exists") from exc
        return case

    def open_case(self, case_key: str) -> TenderCase:
        with self.database.session() as session:
            record = session.scalar(
                select(TenderCaseRecord).where(TenderCaseRecord.case_key == case_key)
            )
            if record is None:
                raise TenderCaseError("case not found")
            plan_context = None
            if record.plan_id_raw is not None:
                plan_context = PlanContext(OpportunityIdentity.from_raw(record.plan_id_raw))
            releases = tuple(
                TenderRelease(OpportunityIdentity.from_raw(item.raw_id))
                for item in sorted(record.releases, key=lambda item: item.id)
            )
        return TenderCase(case_id=record.case_key, plan_context=plan_context, releases=releases)

    def add_release(
        self,
        case_key: str,
        release: TenderRelease,
        *,
        notice_id: int | None = None,
    ) -> PersistedTenderRelease:
        if not isinstance(release, TenderRelease):
            raise TenderReleaseError("release must be a TenderRelease")
        with self.database.session() as session:
            case = session.scalar(
                select(TenderCaseRecord).where(TenderCaseRecord.case_key == case_key)
            )
            if case is None:
                raise TenderCaseError("case not found")
            duplicate = session.scalar(
                select(TenderReleaseRecord).where(
                    TenderReleaseRecord.case_id == case.id,
                    TenderReleaseRecord.base_id == release.identity.base_id,
                    TenderReleaseRecord.revision == release.identity.revision,
                )
            )
            if duplicate is not None:
                raise TenderReleaseError("duplicate exact release")
            record = TenderReleaseRecord(
                case_id=case.id,
                notice_id=notice_id,
                raw_id=release.identity.raw_id,
                base_id=release.identity.base_id,
                revision=release.identity.revision or "",
            )
            session.add(record)
            case.status = "LINKED"
            try:
                session.flush()
            except IntegrityError as exc:
                raise TenderReleaseError("duplicate exact release") from exc
            return PersistedTenderRelease(record.id, case.id, release)

    def add_membership(
        self,
        release_id: int,
        document_id: int,
        authority: AuthorityClass,
        evidence: str,
    ) -> TenderDocumentMembershipRecord:
        with self.database.session() as session:
            release_record = session.get(TenderReleaseRecord, release_id)
            if release_record is None:
                raise TenderReleaseError("release not found")
            membership = TenderDocumentMembership(
                TenderRelease(OpportunityIdentity.from_raw(release_record.raw_id)),
                document_id,
                authority,
                evidence,
            )
            record = TenderDocumentMembershipRecord(
                release_id=release_id,
                document_id=membership.document_id,
                authority_class=membership.authority.value,
                evidence=membership.evidence,
            )
            session.add(record)
            try:
                session.flush()
            except IntegrityError as exc:
                raise TenderCaseError("duplicate document membership") from exc
            return record

    def memberships_for_release(self, release_id: int) -> tuple[TenderDocumentMembershipRecord, ...]:
        with self.database.session() as session:
            return tuple(
                session.scalars(
                    select(TenderDocumentMembershipRecord)
                    .where(TenderDocumentMembershipRecord.release_id == release_id)
                    .order_by(TenderDocumentMembershipRecord.id)
                )
            )

    def release_record(self, release_id: int) -> TenderReleaseRecord:
        with self.database.session() as session:
            record = session.get(TenderReleaseRecord, release_id)
            if record is None:
                raise TenderReleaseError("release not found")
            return record
