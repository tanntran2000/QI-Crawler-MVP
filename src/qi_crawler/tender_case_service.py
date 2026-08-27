"""Application use cases for TenderCase and managed document membership."""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select

from .db import Database
from .document_intake import DocumentIntakeService, extract_document_identity
from .market_intelligence.opportunity_contract import OpportunityIdentity
from .models import Document, TenderCaseRecord, TenderReleaseRecord
from .tender_case import (
    AuthorityClass,
    PlanContext,
    TenderCase,
    TenderCaseError,
    TenderRelease,
)
from .tender_case_persistence import (
    PersistedTenderRelease,
    TenderCasePersistence,
)


class TenderCaseServiceError(TenderCaseError):
    """Expected application-level validation or lookup error."""


class ManagedDocumentMissing(TenderCaseServiceError):
    """The membership's managed object no longer exists."""


class ManagedDocumentShaMismatch(TenderCaseServiceError):
    """Managed bytes do not match the immutable Document SHA-256."""


@dataclass(frozen=True, slots=True)
class ReleaseMembershipView:
    id: int
    document_id: int
    authority_class: str
    evidence: str
    stored_path: Path | None
    sha256: str | None


@dataclass(frozen=True, slots=True)
class ReleaseManifest:
    case_id: str
    release_id: int
    release: TenderRelease
    memberships: tuple[ReleaseMembershipView, ...]


class TenderCaseService:
    """Use-case facade; all storage and source intake stay behind existing ports."""

    def __init__(self, database: Database, document_root: Path):
        self.database = database
        self.persistence = TenderCasePersistence(database)
        self.intake = DocumentIntakeService(database, document_root)

    def create_case(
        self, case_id: str, *, plan_context: PlanContext | None = None
    ) -> TenderCase:
        return self.persistence.create_case(case_id, plan_context=plan_context)

    def open_case(self, case_id: str) -> TenderCase:
        try:
            return self.persistence.open_case(case_id)
        except TenderCaseError as exc:
            raise TenderCaseServiceError(str(exc)) from exc

    def add_release(
        self,
        case_id: str,
        release: TenderRelease | OpportunityIdentity | str,
        *,
        notice_id: int | None = None,
    ) -> PersistedTenderRelease:
        try:
            if isinstance(release, str):
                release = TenderRelease(OpportunityIdentity.from_raw(release))
            elif isinstance(release, OpportunityIdentity):
                release = TenderRelease(release)
            return self.persistence.add_release(case_id, release, notice_id=notice_id)
        except TenderCaseError as exc:
            raise TenderCaseServiceError(str(exc)) from exc

    def add_document(
        self,
        case_id: str,
        release_id: int,
        source_path: Path,
        *,
        authority: AuthorityClass,
        evidence: str,
        uploaded_by: str | None = None,
        document_name: str | None = None,
    ):
        try:
            authority = AuthorityClass(authority)
        except ValueError as exc:
            raise TenderCaseServiceError("unsupported document authority") from exc
        if not isinstance(evidence, str) or not evidence.strip():
            raise TenderCaseServiceError("membership evidence is required")

        try:
            release_record = self.persistence.release_record(release_id)
            release = TenderRelease(OpportunityIdentity.from_raw(release_record.raw_id))
            case_record_id = self._case_record_id(case_id)
            if release_record.case_id != case_record_id:
                raise TenderCaseServiceError("release does not belong to case")
        except TenderCaseError as exc:
            raise TenderCaseServiceError(str(exc)) from exc

        # Read native content identity at the source boundary because an unlinked
        # intake intentionally does not promote content identity into a Notice.
        content_identity = extract_document_identity(Path(source_path))
        # Intake is deliberately reused; this service never creates another byte store.
        try:
            result = self.intake.intake_file(
                Path(source_path),
                document_name=document_name,
                uploaded_by=uploaded_by,
            )
        except Exception as exc:
            if isinstance(exc, TenderCaseServiceError):
                raise
            raise

        embedded_identity = content_identity.raw_notice_id or result.raw_notice_id
        if authority is AuthorityClass.SOURCE_E_HSMT and embedded_identity:
            try:
                content_identity = OpportunityIdentity.from_raw(embedded_identity)
            except ValueError as exc:
                raise TenderCaseServiceError("source document identity is invalid") from exc
            if content_identity != release.identity:
                raise TenderCaseServiceError(
                    "SOURCE_E_HSMT document identity does not match release"
                )
        elif authority is AuthorityClass.SOURCE_E_HSMT and not evidence.strip():
            raise TenderCaseServiceError("SOURCE_E_HSMT requires explicit evidence")

        try:
            return self.persistence.add_membership(
                release_id,
                result.document_id,
                authority,
                evidence.strip(),
            )
        except TenderCaseError as exc:
            raise TenderCaseServiceError(str(exc)) from exc

    def get_release_manifest(
        self, case_id: str, release_id: int | None = None
    ) -> ReleaseManifest | tuple[ReleaseManifest, ...]:
        releases = []
        if release_id is not None:
            record = self.persistence.release_record(release_id)
            if record.case_id != self._case_record_id(case_id):
                raise TenderCaseServiceError("release does not belong to case")
            releases = [(record, TenderRelease(OpportunityIdentity.from_raw(record.raw_id)))]
        else:
            with self.database.session() as session:
                records = tuple(
                    session.scalars(
                        select(TenderReleaseRecord)
                        .where(TenderReleaseRecord.case_id == self._case_record_id(case_id))
                        .order_by(TenderReleaseRecord.id)
                    )
                )
            releases = [
                (record, TenderRelease(OpportunityIdentity.from_raw(record.raw_id)))
                for record in records
            ]
        manifests = tuple(
            ReleaseManifest(
                case_id=case_id,
                release_id=record.id,
                release=release,
                memberships=self._membership_views(record.id),
            )
            for record, release in releases
        )
        return manifests[0] if release_id is not None else manifests

    def managed_path(self, document_id: int) -> Path:
        with self.database.session() as session:
            document = session.get(Document, document_id)
            if document is None:
                raise ManagedDocumentMissing("managed document not found")
            return Path(document.stored_path)

    def retrieve_managed_original(self, membership_id: int, destination: Path) -> Path:
        try:
            membership = self.persistence.membership_record(membership_id)
        except TenderCaseError as exc:
            raise TenderCaseServiceError(str(exc)) from exc
        with self.database.session() as session:
            document = session.get(Document, membership.document_id)
            if document is None:
                raise ManagedDocumentMissing("managed document not found")
            stored_path = Path(document.stored_path)
            expected_sha = document.sha256
        if not stored_path.is_file():
            raise ManagedDocumentMissing("managed document is missing")
        digest = hashlib.sha256()
        with stored_path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest().casefold() != expected_sha.casefold():
            raise ManagedDocumentShaMismatch("managed document SHA-256 mismatch")
        destination = Path(destination).expanduser()
        if destination.exists():
            raise TenderCaseServiceError("retrieval destination already exists")
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb", dir=destination.parent, prefix=".retrieve-", delete=False
            ) as target, stored_path.open("rb") as source:
                temporary = Path(target.name)
                shutil.copyfileobj(source, target)
                target.flush()
                os.fsync(target.fileno())
            os.link(temporary, destination)
            temporary.unlink()
            return destination
        except FileExistsError as exc:
            raise TenderCaseServiceError("retrieval destination already exists") from exc
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink(missing_ok=True)

    def _case_record_id(self, case_id: str) -> int:
        with self.database.session() as session:
            record = session.scalar(
                select(TenderCaseRecord.id).where(TenderCaseRecord.case_key == case_id)
            )
        if record is None:
            raise TenderCaseServiceError("case not found")
        return int(record)

    def _membership_views(self, release_id: int) -> tuple[ReleaseMembershipView, ...]:
        records = self.persistence.memberships_for_release(release_id)
        views: list[ReleaseMembershipView] = []
        with self.database.session() as session:
            for record in records:
                document = session.get(Document, record.document_id)
                views.append(
                    ReleaseMembershipView(
                        id=record.id,
                        document_id=record.document_id,
                        authority_class=record.authority_class,
                        evidence=record.evidence,
                        stored_path=Path(document.stored_path) if document else None,
                        sha256=document.sha256 if document else None,
                    )
                )
        return tuple(views)
