"""Persistence adapter for Warehouse completeness assertions and ledgers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .db import Database
from .models import (
    TenderCoreCoverageRecord,
    TenderDocumentMembershipRecord,
    TenderPublicationExpectationItemRecord,
    TenderPublicationExpectationSetRecord,
    TenderReleaseRecord,
    utcnow,
)


class TenderCompletenessPersistenceError(ValueError):
    """Raised when a completeness record cannot be persisted safely."""


@dataclass(frozen=True, slots=True)
class PersistedCoreCoverage:
    id: int
    release_id: int
    membership_id: int
    role_code: str
    state: str
    content_locator: str
    evidence: str
    actor: str
    dependency_note: str | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class PersistedPublicationExpectationItem:
    id: int
    expectation_set_id: int
    logical_key: str
    description: str
    state: str
    matched_membership_id: int | None
    evidence: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class PersistedPublicationExpectationSet:
    id: int
    release_id: int
    basis: str
    authority: str
    evidence: str
    actor: str
    created_at: datetime
    items: tuple[PersistedPublicationExpectationItem, ...] = ()


def _core(record: TenderCoreCoverageRecord) -> PersistedCoreCoverage:
    return PersistedCoreCoverage(
        id=record.id,
        release_id=record.release_id,
        membership_id=record.membership_id,
        role_code=record.role_code,
        state=record.state,
        content_locator=record.content_locator,
        evidence=record.evidence,
        actor=record.actor,
        dependency_note=record.dependency_note,
        created_at=record.created_at,
    )


def _item(record: TenderPublicationExpectationItemRecord) -> PersistedPublicationExpectationItem:
    return PersistedPublicationExpectationItem(
        id=record.id,
        expectation_set_id=record.expectation_set_id,
        logical_key=record.logical_key,
        description=record.description,
        state=record.state,
        matched_membership_id=record.matched_membership_id,
        evidence=record.evidence,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _expectation(
    record: TenderPublicationExpectationSetRecord,
    items: tuple[PersistedPublicationExpectationItem, ...] = (),
) -> PersistedPublicationExpectationSet:
    return PersistedPublicationExpectationSet(
        id=record.id,
        release_id=record.release_id,
        basis=record.basis,
        authority=record.authority,
        evidence=record.evidence,
        actor=record.actor,
        created_at=record.created_at,
        items=items,
    )


class TenderCompletenessPersistence:
    """SQLAlchemy adapter; all completeness semantics remain in the service."""

    def __init__(self, database: Database):
        self.database = database
        self.database.require_current_schema()

    def add_core_coverage(
        self,
        *,
        release_id: int,
        membership_id: int,
        role_code: str,
        state: str,
        content_locator: str,
        evidence: str,
        actor: str,
        dependency_note: str | None,
    ) -> PersistedCoreCoverage:
        with self.database.session() as session:
            if session.get(TenderReleaseRecord, release_id) is None:
                raise TenderCompletenessPersistenceError("release not found")
            if session.get(TenderDocumentMembershipRecord, membership_id) is None:
                raise TenderCompletenessPersistenceError("membership not found")
            record = TenderCoreCoverageRecord(
                release_id=release_id,
                membership_id=membership_id,
                role_code=role_code,
                state=state,
                content_locator=content_locator,
                evidence=evidence,
                actor=actor,
                dependency_note=dependency_note,
                created_at=utcnow(),
            )
            session.add(record)
            session.flush()
            return _core(record)

    def core_coverage(
        self, release_id: int, role_code: str | None = None
    ) -> tuple[PersistedCoreCoverage, ...]:
        with self.database.session() as session:
            statement = select(TenderCoreCoverageRecord).where(
                TenderCoreCoverageRecord.release_id == release_id
            )
            if role_code is not None:
                statement = statement.where(TenderCoreCoverageRecord.role_code == role_code)
            records = session.scalars(
                statement.order_by(TenderCoreCoverageRecord.id)
            )
            return tuple(_core(record) for record in records)

    def create_expectation_set(
        self,
        *,
        release_id: int,
        basis: str,
        authority: str,
        evidence: str,
        actor: str,
    ) -> int:
        with self.database.session() as session:
            if session.get(TenderReleaseRecord, release_id) is None:
                raise TenderCompletenessPersistenceError("release not found")
            record = TenderPublicationExpectationSetRecord(
                release_id=release_id,
                basis=basis,
                authority=authority,
                evidence=evidence,
                actor=actor,
                created_at=utcnow(),
            )
            session.add(record)
            session.flush()
            return record.id

    def add_expectation_item(
        self,
        expectation_set_id: int,
        *,
        logical_key: str,
        description: str,
    ) -> int:
        with self.database.session() as session:
            if session.get(TenderPublicationExpectationSetRecord, expectation_set_id) is None:
                raise TenderCompletenessPersistenceError("expectation set not found")
            record = TenderPublicationExpectationItemRecord(
                expectation_set_id=expectation_set_id,
                logical_key=logical_key,
                description=description,
                state="EXPECTED",
                created_at=utcnow(),
                updated_at=utcnow(),
            )
            session.add(record)
            try:
                session.flush()
            except IntegrityError as exc:
                raise TenderCompletenessPersistenceError("duplicate logical expectation item") from exc
            return record.id

    def expectation_sets(
        self, release_id: int
    ) -> tuple[PersistedPublicationExpectationSet, ...]:
        with self.database.session() as session:
            sets = tuple(
                session.scalars(
                    select(TenderPublicationExpectationSetRecord)
                    .where(TenderPublicationExpectationSetRecord.release_id == release_id)
                    .order_by(TenderPublicationExpectationSetRecord.id)
                )
            )
            result: list[PersistedPublicationExpectationSet] = []
            for expectation_set in sets:
                items = tuple(
                    _item(item)
                    for item in session.scalars(
                        select(TenderPublicationExpectationItemRecord)
                        .where(
                            TenderPublicationExpectationItemRecord.expectation_set_id
                            == expectation_set.id
                        )
                        .order_by(TenderPublicationExpectationItemRecord.id)
                    )
                )
                result.append(_expectation(expectation_set, items))
            return tuple(result)

    def expectation_set(
        self, expectation_set_id: int
    ) -> PersistedPublicationExpectationSet:
        with self.database.session() as session:
            expectation_set = session.get(
                TenderPublicationExpectationSetRecord, expectation_set_id
            )
            if expectation_set is None:
                raise TenderCompletenessPersistenceError("expectation set not found")
            items = tuple(
                _item(item)
                for item in session.scalars(
                    select(TenderPublicationExpectationItemRecord)
                    .where(
                        TenderPublicationExpectationItemRecord.expectation_set_id
                        == expectation_set_id
                    )
                    .order_by(TenderPublicationExpectationItemRecord.id)
                )
            )
            return _expectation(expectation_set, items)

    def reconcile_item(
        self,
        expectation_set_id: int,
        logical_key: str,
        *,
        state: str,
        matched_membership_id: int | None,
        evidence: str,
    ) -> None:
        with self.database.session() as session:
            record = session.scalar(
                select(TenderPublicationExpectationItemRecord).where(
                    TenderPublicationExpectationItemRecord.expectation_set_id
                    == expectation_set_id,
                    TenderPublicationExpectationItemRecord.logical_key == logical_key,
                )
            )
            if record is None:
                raise TenderCompletenessPersistenceError("expectation item not found")
            record.state = state
            record.matched_membership_id = matched_membership_id
            record.evidence = evidence
            record.updated_at = utcnow()
