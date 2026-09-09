"""Warehouse completeness and core HSMT readiness contracts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from sqlalchemy import select

from .db import Database
from .models import (
    Document,
    TenderCaseRecord,
    TenderDocumentMembershipRecord,
    TenderReleaseRecord,
)
from .tender_case import AuthorityClass
from .tender_case_service import TenderCaseService
from .tender_completeness_persistence import (
    PersistedCoreCoverage,
    TenderCompletenessPersistence,
)


class CoreRole(StrEnum):
    SCOPE_AND_QUANTITY = "SCOPE_AND_QUANTITY"
    TECHNICAL_REQUIREMENTS = "TECHNICAL_REQUIREMENTS"
    TECHNICAL_EVALUATION = "TECHNICAL_EVALUATION"


CORE_ROLE_LABELS: Mapping[CoreRole, str] = {
    CoreRole.SCOPE_AND_QUANTITY: "Phạm vi cung cấp và khối lượng",
    CoreRole.TECHNICAL_REQUIREMENTS: "Yêu cầu kỹ thuật và giải pháp",
    CoreRole.TECHNICAL_EVALUATION: "Tiêu chuẩn đánh giá kỹ thuật",
}


class CoreCoverageState(StrEnum):
    CONFIRMED = "CONFIRMED"
    NEEDS_SUPPLEMENT = "NEEDS_SUPPLEMENT"
    UNKNOWN = "UNKNOWN"
    CONFLICT = "CONFLICT"


class PublicationExpectationBasis(StrEnum):
    COMPLETE_LIST = "COMPLETE_LIST"
    PARTIAL_LIST = "PARTIAL_LIST"


class PublicationItemState(StrEnum):
    EXPECTED = "EXPECTED"
    FOUND = "FOUND"
    MISSING = "MISSING"
    CONFLICT = "CONFLICT"
    UNKNOWN = "UNKNOWN"
    SUPERSEDED = "SUPERSEDED"
    QUARANTINED = "QUARANTINED"


class PublicationPackageState(StrEnum):
    COMPLETE = "COMPLETE"
    MISSING = "MISSING"
    UNKNOWN = "UNKNOWN"
    CONFLICT = "CONFLICT"


@dataclass(frozen=True, slots=True)
class CoreCoverageAssertion:
    id: int
    release_id: int
    membership_id: int
    role: CoreRole
    state: CoreCoverageState
    content_locator: str
    evidence: str
    actor: str
    dependency_note: str | None


@dataclass(frozen=True, slots=True)
class CoreReadiness:
    release_id: int
    role_states: Mapping[CoreRole, CoreCoverageState]

    @property
    def full_research_ready(self) -> bool:
        return all(
            self.role_states[role] is CoreCoverageState.CONFIRMED for role in CoreRole
        )


@dataclass(frozen=True, slots=True)
class PublicationSummary:
    release_id: int
    state: PublicationPackageState
    expected_count: int = 0
    found_count: int = 0
    missing_count: int = 0
    conflict_count: int = 0
    unknown_count: int = 0
    partial_list_count: int = 0


class TenderCompletenessService:
    """Application service for exact-release completeness projections."""

    def __init__(self, database: Database, document_root: Path | None = None):
        self.database = database
        self.persistence = TenderCompletenessPersistence(database)
        self._documents = (
            TenderCaseService(database, document_root) if document_root is not None else None
        )

    def confirm_core_role(
        self,
        release_id: int,
        membership_id: int,
        role: CoreRole | str,
        *,
        state: CoreCoverageState | str,
        content_locator: str,
        evidence: str,
        actor: str,
        dependency_note: str | None = None,
    ) -> CoreCoverageAssertion:
        role_value = CoreRole(role)
        state_value = CoreCoverageState(state)
        self._validate_source_membership(release_id, membership_id)
        self._validate_text(evidence, "evidence")
        self._validate_text(actor, "actor")
        self._validate_locator(content_locator)
        if state_value is CoreCoverageState.CONFIRMED and actor.strip().lower().startswith(
            ("machine", "ai", "llm")
        ):
            raise ValueError("CONFIRMED core coverage requires a Human actor")
        record = self.persistence.add_core_coverage(
            release_id=release_id,
            membership_id=membership_id,
            role_code=role_value.value,
            state=state_value.value,
            content_locator=content_locator.strip(),
            evidence=evidence.strip(),
            actor=actor.strip(),
            dependency_note=dependency_note.strip() if dependency_note else None,
        )
        return self._core_assertion(record)

    def core_history(
        self, release_id: int, role: CoreRole | str | None = None
    ) -> tuple[CoreCoverageAssertion, ...]:
        role_code = CoreRole(role).value if role is not None else None
        return tuple(
            self._core_assertion(record)
            for record in self.persistence.core_coverage(release_id, role_code)
        )

    def core_readiness(self, release_id: int) -> CoreReadiness:
        history = self.persistence.core_coverage(release_id)
        grouped: dict[CoreRole, list[PersistedCoreCoverage]] = {
            role: [] for role in CoreRole
        }
        for record in history:
            grouped[CoreRole(record.role_code)].append(record)
        states: dict[CoreRole, CoreCoverageState] = {}
        for role, records in grouped.items():
            states[role] = self._project_role_state(records)
        return CoreReadiness(release_id=release_id, role_states=states)

    def create_publication_expectation(
        self,
        release_id: int,
        *,
        basis: PublicationExpectationBasis | str,
        authority: str,
        evidence: str,
        actor: str,
    ) -> int:
        basis_value = PublicationExpectationBasis(basis)
        self._validate_release(release_id)
        self._validate_text(authority, "authority")
        self._validate_text(evidence, "evidence")
        self._validate_text(actor, "actor")
        return self.persistence.create_expectation_set(
            release_id=release_id,
            basis=basis_value.value,
            authority=authority.strip(),
            evidence=evidence.strip(),
            actor=actor.strip(),
        )

    def add_publication_item(
        self, expectation_set_id: int, logical_key: str, description: str
    ) -> int:
        self._validate_text(logical_key, "logical key")
        self._validate_text(description, "description")
        return self.persistence.add_expectation_item(
            expectation_set_id,
            logical_key=logical_key.strip(),
            description=description.strip(),
        )

    def reconcile_publication(
        self,
        release_id: int,
        expectation_set_id: int,
        *,
        observed_logical_keys: Mapping[str, int],
        evidence: str = "exact-release membership reconciliation",
    ) -> PublicationSummary:
        expectation = self.persistence.expectation_set(expectation_set_id)
        if expectation.release_id != release_id:
            raise ValueError("expectation set does not belong to exact release")
        self._validate_text(evidence, "evidence")
        for logical_key, membership_id in observed_logical_keys.items():
            self._validate_source_membership(release_id, membership_id)
            self._validate_text(logical_key, "logical key")
        expected_keys = {item.logical_key for item in expectation.items}
        for item in expectation.items:
            membership_id = observed_logical_keys.get(item.logical_key)
            if membership_id is None:
                state = PublicationItemState.MISSING.value
            else:
                state = PublicationItemState.FOUND.value
            self.persistence.reconcile_item(
                expectation_set_id,
                item.logical_key,
                state=state,
                matched_membership_id=membership_id,
                evidence=evidence.strip(),
            )
        # Extra observed keys are intentionally not promoted into the expected ledger.
        _ = expected_keys
        return self.publication_summary(release_id)

    def publication_summary(self, release_id: int) -> PublicationSummary:
        expectation_sets = self.persistence.expectation_sets(release_id)
        if not expectation_sets:
            return PublicationSummary(release_id, PublicationPackageState.UNKNOWN)
        partial_count = sum(
            item.basis == PublicationExpectationBasis.PARTIAL_LIST.value
            for item in expectation_sets
        )
        complete_sets = [
            item
            for item in expectation_sets
            if item.basis == PublicationExpectationBasis.COMPLETE_LIST.value
        ]
        if not complete_sets:
            return PublicationSummary(
                release_id,
                PublicationPackageState.UNKNOWN,
                partial_list_count=partial_count,
            )
        signatures = {
            tuple(item.logical_key for item in expectation.items) for expectation in complete_sets
        }
        if len(signatures) > 1:
            return PublicationSummary(
                release_id,
                PublicationPackageState.CONFLICT,
                conflict_count=len(signatures) - 1,
                partial_list_count=partial_count,
            )
        current = complete_sets[-1]
        states = [PublicationItemState(item.state) for item in current.items]
        found_count = states.count(PublicationItemState.FOUND)
        missing_count = states.count(PublicationItemState.MISSING)
        conflict_count = states.count(PublicationItemState.CONFLICT)
        unknown_count = sum(
            state
            in {
                PublicationItemState.EXPECTED,
                PublicationItemState.UNKNOWN,
                PublicationItemState.SUPERSEDED,
                PublicationItemState.QUARANTINED,
            }
            for state in states
        )
        if conflict_count:
            state = PublicationPackageState.CONFLICT
        elif unknown_count:
            state = PublicationPackageState.UNKNOWN
        elif missing_count:
            state = PublicationPackageState.MISSING
        else:
            state = PublicationPackageState.COMPLETE
        return PublicationSummary(
            release_id,
            state,
            expected_count=len(states),
            found_count=found_count,
            missing_count=missing_count,
            conflict_count=conflict_count,
            unknown_count=unknown_count,
            partial_list_count=partial_count,
        )

    def retrieve_document(
        self, case_id: str, release_id: int, membership_id: int, destination: Path
    ) -> Path:
        if self._documents is None:
            raise ValueError("document_root is required for managed retrieval")
        with self.database.session() as session:
            row = session.execute(
                select(TenderReleaseRecord, TenderCaseRecord)
                .join(TenderCaseRecord, TenderCaseRecord.id == TenderReleaseRecord.case_id)
                .where(TenderReleaseRecord.id == release_id)
            ).first()
            if row is None or row[1].case_key != case_id:
                raise ValueError("release does not belong to exact case")
            membership = session.get(TenderDocumentMembershipRecord, membership_id)
            if membership is None or membership.release_id != release_id:
                raise ValueError("membership does not belong to exact release")
            document = session.get(Document, membership.document_id)
            if document is None:
                raise ValueError("managed document not found")
        return self._documents.retrieve_managed_original(membership_id, destination)

    def _validate_release(self, release_id: int) -> None:
        with self.database.session() as session:
            if session.get(TenderReleaseRecord, release_id) is None:
                raise ValueError("release not found")

    def _validate_source_membership(self, release_id: int, membership_id: int) -> None:
        with self.database.session() as session:
            release = session.get(TenderReleaseRecord, release_id)
            membership = session.get(TenderDocumentMembershipRecord, membership_id)
            if release is None:
                raise ValueError("release not found")
            if membership is None or membership.release_id != release_id:
                raise ValueError("membership does not belong to exact release")
            if membership.authority_class != AuthorityClass.SOURCE_E_HSMT.value:
                raise ValueError("core coverage requires SOURCE_E_HSMT membership")
            document = session.get(Document, membership.document_id)
            if document is None or not document.stored_path or not document.sha256:
                raise ValueError("managed document is not available")

    @staticmethod
    def _validate_text(value: str, label: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{label} is required")

    @staticmethod
    def _validate_locator(value: str) -> None:
        TenderCompletenessService._validate_text(value, "content locator")
        normalized = value.strip().lower()
        prefixes = (
            "page:",
            "pages:",
            "section:",
            "sheet:",
            "range:",
            "table:",
            "paragraph:",
            "line:",
            "entry:",
        )
        if not normalized.startswith(prefixes):
            raise ValueError("content locator must identify content, not only a filename")

    @staticmethod
    def _project_role_state(
        records: list[PersistedCoreCoverage],
    ) -> CoreCoverageState:
        if not records:
            return CoreCoverageState.UNKNOWN
        states = {CoreCoverageState(record.state) for record in records}
        if CoreCoverageState.CONFLICT in states:
            return CoreCoverageState.CONFLICT
        if CoreCoverageState.CONFIRMED in states:
            return CoreCoverageState.CONFIRMED
        if CoreCoverageState.NEEDS_SUPPLEMENT in states:
            return CoreCoverageState.NEEDS_SUPPLEMENT
        return CoreCoverageState.UNKNOWN

    @staticmethod
    def _core_assertion(record: PersistedCoreCoverage) -> CoreCoverageAssertion:
        return CoreCoverageAssertion(
            id=record.id,
            release_id=record.release_id,
            membership_id=record.membership_id,
            role=CoreRole(record.role_code),
            state=CoreCoverageState(record.state),
            content_locator=record.content_locator,
            evidence=record.evidence,
            actor=record.actor,
            dependency_note=record.dependency_note,
        )
