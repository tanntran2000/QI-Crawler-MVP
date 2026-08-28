"""Operational Team Bid workspace backed by TenderCase authority."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .db import Database
from .market_intelligence.opportunity_contract import OpportunityIdentity
from .models import (
    Document,
    TenderDocumentMembershipRecord,
    TenderWorkspaceEntryRecord,
)
from .tender_case import AuthorityClass, TenderCase
from .tender_case_service import TenderCaseService, TenderCaseServiceError


class TenderWorkspaceError(TenderCaseServiceError):
    """Raised when a logical workspace operation cannot be completed safely."""


class TeamBidZone(StrEnum):
    SOURCE_E_HSMT = "01_Source_E-HSMT"
    REQUIREMENT_REGISTER = "02_Requirement_Register"
    LEGAL_CAPABILITY = "03_Legal_Capability"
    TECHNICAL_VENDOR = "04_Technical_Vendor"
    COMMERCIAL_PRICE = "05_Commercial_Price"
    SUBMISSION_FINAL = "06_Submission_FINAL"
    EVIDENCE_ARCHIVE = "07_Evidence_Archive"


TEAM_BID_ZONES = tuple(TeamBidZone)


@dataclass(frozen=True, slots=True)
class WorkspaceEntry:
    id: int
    membership_id: int
    release_id: int
    release_raw_id: str
    release_base_id: str
    release_revision: str
    document_id: int
    filename: str
    zone: TeamBidZone
    authority: AuthorityClass
    sha256: str
    stored_path: Path


@dataclass(frozen=True, slots=True)
class WorkspaceZoneView:
    zone: TeamBidZone
    entries: tuple[WorkspaceEntry, ...]


@dataclass(frozen=True, slots=True)
class TenderWorkspaceManifest:
    case_id: str
    zones: tuple[WorkspaceZoneView, ...]

    def for_zone(self, zone: TeamBidZone | str) -> tuple[WorkspaceEntry, ...]:
        normalized = TeamBidZone(zone)
        for view in self.zones:
            if view.zone is normalized:
                return view.entries
        return ()

    @property
    def entries(self) -> tuple[WorkspaceEntry, ...]:
        return tuple(entry for view in self.zones for entry in view.entries)


@dataclass(frozen=True, slots=True)
class WorkspaceExportResult:
    output: Path
    entry_count: int


class TenderWorkspaceService:
    """Thin operational facade; TenderCase remains the identity authority."""

    def __init__(self, database: Database, document_root: Path):
        self.database = database
        self.case_service = TenderCaseService(database, document_root)

    def create_case(self, case_id: str, *, plan_context=None) -> TenderCase:
        return self.case_service.create_case(case_id, plan_context=plan_context)

    def open_case(self, case_id: str) -> TenderCase:
        return self.case_service.open_case(case_id)

    def add_release(self, case_id: str, release, *, notice_id: int | None = None):
        return self.case_service.add_release(case_id, release, notice_id=notice_id)

    def open_or_create_release(self, case_id: str, release) -> int:
        """Open a persisted case and exact IB revision, creating only missing state."""
        try:
            self.open_case(case_id)
        except TenderCaseServiceError as exc:
            if str(exc) != "case not found":
                raise
            self.create_case(case_id)
        identity = release if isinstance(release, OpportunityIdentity) else OpportunityIdentity.from_raw(
            release.identity.raw_id if hasattr(release, "identity") else str(release)
        )
        for manifest in self.case_service.get_release_manifest(case_id):
            if manifest.release.identity == identity:
                return manifest.release_id
        return self.add_release(case_id, identity).release_id

    def add_path_to_zone(
        self,
        case_id: str,
        release_id: int,
        input_path: Path,
        *,
        zone: TeamBidZone | str,
        authority: AuthorityClass,
        evidence: str,
        uploaded_by: str | None = None,
    ) -> tuple[WorkspaceEntry, ...]:
        normalized_zone = self._zone(zone)
        path = Path(input_path).expanduser()
        if path.is_dir():
            candidates = tuple(
                sorted(
                    candidate
                    for candidate in path.rglob("*")
                    if candidate.is_file()
                    and candidate.suffix.lower() in {".pdf", ".docx", ".xlsx", ".zip"}
                )
            )
            if not candidates:
                raise TenderWorkspaceError("Thư mục không có PDF, DOCX, XLSX hoặc ZIP.")
        else:
            candidates = (path,)
        entries = []
        for candidate in candidates:
            membership = self.case_service.add_document(
                case_id,
                release_id,
                candidate,
                authority=authority,
                evidence=evidence,
                uploaded_by=uploaded_by,
            )
            entries.append(self.assign_membership(membership.id, normalized_zone))
        return tuple(entries)

    def assign_membership(
        self, membership_id: int, zone: TeamBidZone | str
    ) -> WorkspaceEntry:
        normalized_zone = self._zone(zone)
        with self.database.session() as session:
            membership = session.get(TenderDocumentMembershipRecord, membership_id)
            if membership is None:
                raise TenderWorkspaceError("membership not found")
            document = session.get(Document, membership.document_id)
            if document is None:
                raise TenderWorkspaceError("managed document not found")
            existing = session.scalar(
                select(TenderWorkspaceEntryRecord).where(
                    TenderWorkspaceEntryRecord.membership_id == membership_id,
                    TenderWorkspaceEntryRecord.zone_code == normalized_zone.value,
                )
            )
            if existing is not None:
                raise TenderWorkspaceError("document already assigned to this zone")
            record = TenderWorkspaceEntryRecord(
                membership_id=membership_id,
                zone_code=normalized_zone.value,
            )
            session.add(record)
            try:
                session.flush()
            except IntegrityError as exc:
                raise TenderWorkspaceError("document already assigned to this zone") from exc
            return self._entry(record, membership, document, normalized_zone)

    def manifest(self, case_id: str) -> TenderWorkspaceManifest:
        self.open_case(case_id)
        case_record_id = self._case_id(case_id)
        with self.database.session() as session:
            records = tuple(
                session.scalars(
                    select(TenderWorkspaceEntryRecord)
                    .join(TenderDocumentMembershipRecord)
                    .join(Document)
                    .where(
                        TenderDocumentMembershipRecord.release.has(case_id=case_record_id)
                    )
                    .order_by(TenderWorkspaceEntryRecord.zone_code, TenderWorkspaceEntryRecord.id)
                )
            )
            entries = tuple(
                self._entry(
                    record,
                    record.membership,
                    record.membership.document,
                    TeamBidZone(record.zone_code),
                )
                for record in records
            )
        return TenderWorkspaceManifest(
            case_id=case_id,
            zones=tuple(
                WorkspaceZoneView(
                    zone=zone,
                    entries=tuple(entry for entry in entries if entry.zone is zone),
                )
                for zone in TEAM_BID_ZONES
            ),
        )

    def export(self, case_id: str, destination: Path) -> WorkspaceExportResult:
        output = Path(destination).expanduser().resolve()
        if output.exists():
            raise TenderWorkspaceError("workspace export destination already exists")
        output.parent.mkdir(parents=True, exist_ok=True)
        manifest = self.manifest(case_id)
        stage = Path(tempfile.mkdtemp(prefix="warehouse-export-", dir=output.parent))
        try:
            for zone in TEAM_BID_ZONES:
                (stage / zone.value).mkdir(parents=True, exist_ok=True)
            exported = []
            for entry in manifest.entries:
                target = stage / entry.zone.value / entry.filename
                self.case_service.retrieve_managed_original(entry.membership_id, target)
                digest = hashlib.sha256(target.read_bytes()).hexdigest()
                if digest.casefold() != entry.sha256.casefold():
                    raise TenderWorkspaceError("exported document SHA-256 mismatch")
                exported.append(
                    {
                        "zone": entry.zone.value,
                        "release_id": entry.release_id,
                        "release_raw_id": entry.release_raw_id,
                        "release_base_id": entry.release_base_id,
                        "release_revision": entry.release_revision,
                        "membership_id": entry.membership_id,
                        "document_id": entry.document_id,
                        "filename": entry.filename,
                        "sha256": entry.sha256,
                        "authority_class": entry.authority.value,
                    }
                )
            (stage / "WORKSPACE_MANIFEST.json").write_text(
                json.dumps(
                    {"case_id": case_id, "entries": exported},
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            stage.replace(output)
        except Exception:
            shutil.rmtree(stage, ignore_errors=True)
            raise
        return WorkspaceExportResult(output=output, entry_count=len(exported))

    @staticmethod
    def _zone(zone: TeamBidZone | str) -> TeamBidZone:
        try:
            return TeamBidZone(zone)
        except ValueError as exc:
            raise TenderWorkspaceError("unknown Team Bid workspace zone") from exc

    def _case_id(self, case_id: str) -> int:
        from .models import TenderCaseRecord

        with self.database.session() as session:
            value = session.scalar(
                select(TenderCaseRecord.id).where(TenderCaseRecord.case_key == case_id)
            )
        if value is None:
            raise TenderWorkspaceError("case not found")
        return int(value)

    @staticmethod
    def _entry(record, membership, document, zone: TeamBidZone) -> WorkspaceEntry:
        release = membership.release
        return WorkspaceEntry(
            id=record.id,
            membership_id=record.membership_id,
            release_id=release.id,
            release_raw_id=release.raw_id,
            release_base_id=release.base_id,
            release_revision=release.revision,
            document_id=document.id,
            filename=document.original_filename,
            zone=zone,
            authority=AuthorityClass(membership.authority_class),
            sha256=document.sha256,
            stored_path=Path(document.stored_path),
        )


__all__ = [
    "TEAM_BID_ZONES",
    "TeamBidZone",
    "TenderWorkspaceError",
    "TenderWorkspaceManifest",
    "TenderWorkspaceService",
    "WorkspaceEntry",
    "WorkspaceExportResult",
    "WorkspaceZoneView",
]
