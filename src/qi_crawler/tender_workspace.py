"""Operational Team Bid workspace backed by TenderCase authority.

The service deliberately keeps document bytes immutable and represents working
state as append-only workspace entries plus explicit transitions.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import tempfile
import unicodedata
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .db import Database
from .document_intake import extract_document_identity, sanitize_filename
from .market_intelligence.opportunity_contract import OpportunityIdentity
from .models import (
    Document,
    TenderCaseRecord,
    TenderDocumentMembershipRecord,
    TenderReleaseRecord,
    TenderWorkspaceEntryRecord,
    TenderWorkspaceTransitionRecord,
)
from .tender_case import AuthorityClass, TenderCase
from .tender_case_service import TenderCaseService, TenderCaseServiceError
from .workspace_candidate_intake import (
    ROLE_CODES,
    ConfirmedWorkspaceCandidate,
    WorkspaceCandidate,
    WorkspaceCandidateError,
    scan_folder,
)


class TenderWorkspaceError(TenderCaseServiceError):
    """Raised when a logical workspace operation cannot complete safely."""


class TeamBidZone(StrEnum):
    SOURCE_E_HSMT = "01_Source_E-HSMT"
    REQUIREMENT_REGISTER = "02_Requirement_Register"
    LEGAL_CAPABILITY = "03_Legal_Capability"
    TECHNICAL_VENDOR = "04_Technical_Vendor"
    COMMERCIAL_PRICE = "05_Commercial_Price"
    SUBMISSION_FINAL = "06_Submission_FINAL"
    EVIDENCE_ARCHIVE = "07_Evidence_Archive"


TEAM_BID_ZONES = tuple(TeamBidZone)


class ManagedIntegrityState(StrEnum):
    NOT_CHECKED = "NOT_CHECKED"
    VERIFIED = "VERIFIED"
    MISSING = "MISSING"
    MISMATCH = "MISMATCH"


class WorkspaceOperationalState(StrEnum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    WITHDRAWN_BY_CORRECTION = "WITHDRAWN_BY_CORRECTION"


class WorkspaceTransitionType(StrEnum):
    SUPERSEDE = "SUPERSEDE"
    SOURCE_CORRECTION = "SOURCE_CORRECTION"


ZONE_AUTHORITIES = {
    TeamBidZone.SOURCE_E_HSMT: frozenset({AuthorityClass.SOURCE_E_HSMT}),
    TeamBidZone.REQUIREMENT_REGISTER: frozenset({AuthorityClass.DERIVED_REQUIREMENT}),
    TeamBidZone.LEGAL_CAPABILITY: frozenset({AuthorityClass.WORKING_E_HSDT}),
    TeamBidZone.TECHNICAL_VENDOR: frozenset({AuthorityClass.WORKING_E_HSDT}),
    TeamBidZone.COMMERCIAL_PRICE: frozenset({AuthorityClass.WORKING_E_HSDT}),
    TeamBidZone.SUBMISSION_FINAL: frozenset({AuthorityClass.FINAL_SUBMISSION}),
    TeamBidZone.EVIDENCE_ARCHIVE: frozenset(
        {AuthorityClass.EVIDENCE_ARCHIVE, AuthorityClass.REFERENCE_ONLY}
    ),
}


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
    slot_key: str
    operational_state: WorkspaceOperationalState = WorkspaceOperationalState.ACTIVE
    integrity_state: ManagedIntegrityState = ManagedIntegrityState.NOT_CHECKED


@dataclass(frozen=True, slots=True)
class WorkspaceTransition:
    id: int
    prior_entry_id: int
    successor_entry_id: int | None
    transition_type: WorkspaceTransitionType
    actor: str | None
    reason: str
    evidence: str


@dataclass(frozen=True, slots=True)
class WorkspaceZoneView:
    zone: TeamBidZone
    entries: tuple[WorkspaceEntry, ...]


@dataclass(frozen=True, slots=True)
class TenderWorkspaceManifest:
    case_id: str
    zones: tuple[WorkspaceZoneView, ...]
    release_id: int | None = None
    history: tuple[WorkspaceTransition, ...] = ()

    def for_zone(self, zone: TeamBidZone | str) -> tuple[WorkspaceEntry, ...]:
        normalized = TeamBidZone(zone)
        for view in self.zones:
            if view.zone is normalized:
                return view.entries
        return ()

    @property
    def entries(self) -> tuple[WorkspaceEntry, ...]:
        return tuple(entry for view in self.zones for entry in view.entries)

    @property
    def active_entries(self) -> tuple[WorkspaceEntry, ...]:
        return tuple(
            entry for entry in self.entries
            if entry.operational_state is WorkspaceOperationalState.ACTIVE
        )


@dataclass(frozen=True, slots=True)
class WorkspaceExportResult:
    output: Path
    entry_count: int


@dataclass(frozen=True, slots=True)
class TenderCaseSearchResult:
    case_id: str
    release_id: int | None
    release_raw_id: str | None
    release_base_id: str | None
    release_revision: str | None
    plan_raw_id: str | None
    plan_base_id: str | None


@dataclass(frozen=True, slots=True)
class WorkspaceReplaceResult:
    status: str
    entry: WorkspaceEntry
    transition: WorkspaceTransition | None = None


@dataclass(frozen=True, slots=True)
class TenderWorkspaceDashboard:
    case_id: str
    release_id: int
    release_raw_id: str
    release_base_id: str
    release_revision: str
    plan_raw_id: str | None
    available_revisions: tuple[str, ...]
    zones: tuple[WorkspaceZoneView, ...]
    claims: tuple[str, ...] = ()


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

    def search_cases(self, query: str) -> tuple[TenderCaseSearchResult, ...]:
        """Search authoritative case/release identifiers without selecting a revision."""
        needle = " ".join(str(query or "").split()).casefold()
        if not needle:
            return ()
        with self.database.session() as session:
            records = tuple(
                session.scalars(
                    select(TenderCaseRecord).order_by(TenderCaseRecord.id)
                )
            )
            results = []
            for case in records:
                releases = tuple(sorted(case.releases, key=lambda item: item.id))
                candidates = releases or (None,)
                for record in candidates:
                    values = (
                        case.case_key,
                        record.raw_id if record is not None else "",
                        record.base_id if record is not None else "",
                        record.revision if record is not None else "",
                        case.plan_id_raw or "",
                        case.plan_base_id or "",
                    )
                    if any(needle in value.casefold() for value in values):
                        results.append(
                            TenderCaseSearchResult(
                                case_id=case.case_key,
                                release_id=record.id if record is not None else None,
                                release_raw_id=record.raw_id if record is not None else None,
                                release_base_id=record.base_id if record is not None else None,
                                release_revision=record.revision if record is not None else None,
                                plan_raw_id=case.plan_id_raw,
                                plan_base_id=case.plan_base_id,
                            )
                        )
        return tuple(results)

    def scan_folder(self, input_path: Path) -> tuple[WorkspaceCandidate, ...]:
        """Discover supported files without creating Warehouse state."""

        try:
            with self.database.session() as session:
                duplicate_shas = tuple(session.scalars(select(Document.sha256)))
            return scan_folder(input_path, duplicate_shas=duplicate_shas)
        except WorkspaceCandidateError as exc:
            raise TenderWorkspaceError(str(exc)) from exc

    def add_confirmed_candidates(
        self,
        case_id: str,
        release_id: int,
        confirmed_candidates: tuple[ConfirmedWorkspaceCandidate, ...]
        | list[ConfirmedWorkspaceCandidate],
    ) -> tuple[WorkspaceEntry, ...]:
        """Ingest only candidates explicitly confirmed by a Human."""

        self._validate_release(case_id, release_id)
        created: list[tuple[int, int, bool]] = []
        entries: list[WorkspaceEntry] = []
        for confirmed in confirmed_candidates:
            if not isinstance(confirmed, ConfirmedWorkspaceCandidate):
                raise TenderWorkspaceError("confirmed candidate is invalid")
            normalized_authority = self._authority(confirmed.authority)
            normalized_zone = self._zone(confirmed.zone)
            self._validate_zone_authority(normalized_zone, normalized_authority)
            role = str(confirmed.role or "").strip().upper()
            if role not in ROLE_CODES:
                raise TenderWorkspaceError("unsupported managed role")
            if role == "REF" and normalized_authority is not AuthorityClass.REFERENCE_ONLY:
                raise TenderWorkspaceError("REF role requires REFERENCE_ONLY authority")
            if normalized_authority is AuthorityClass.REFERENCE_ONLY and role != "REF":
                raise TenderWorkspaceError("REFERENCE_ONLY requires REF role")
            candidate = confirmed.candidate
            digest = self._hash_candidate(candidate)
            existing_document_ids = self._document_ids_by_sha(digest)
            try:
                self._validate_candidate_identity(release_id, candidate, normalized_authority)
                membership = self.case_service.add_document(
                    case_id,
                    release_id,
                    candidate.source_path,
                    authority=normalized_authority,
                    evidence=confirmed.evidence,
                    uploaded_by=confirmed.uploaded_by,
                )
                created.append((membership.id, membership.document_id, not existing_document_ids))
                slot_key = self._next_managed_slot(release_id, role)
                entries.append(self.assign_membership(membership.id, normalized_zone, slot_key=slot_key))
            except Exception:
                self._cleanup_created(created)
                self._cleanup_new_documents(digest, existing_document_ids)
                raise
        return tuple(entries)

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
        normalized_authority = self._authority(authority)
        self._validate_zone_authority(normalized_zone, normalized_authority)
        self._validate_release(case_id, release_id)
        path = Path(input_path).expanduser()
        if path.is_dir():
            raise TenderWorkspaceError(
                "Folder intake requires scan and explicit candidate confirmation."
            )
        candidates = (path,)
        created: list[tuple[int, int, bool]] = []
        entries: list[WorkspaceEntry] = []
        for candidate in candidates:
            digest: str | None = None
            existing_document_ids = frozenset()
            try:
                digest = self._hash_path(candidate)
                existing_document_ids = self._document_ids_by_sha(digest)
                membership = self.case_service.add_document(
                    case_id,
                    release_id,
                    candidate,
                    authority=normalized_authority,
                    evidence=evidence,
                    uploaded_by=uploaded_by,
                )
                created.append(
                    (membership.id, membership.document_id, not existing_document_ids)
                )
                entries.append(self.assign_membership(membership.id, normalized_zone))
            except Exception:
                self._cleanup_created(created)
                if digest is not None:
                    self._cleanup_new_documents(digest, existing_document_ids)
                raise
        return tuple(entries)

    def assign_membership(
        self, membership_id: int, zone: TeamBidZone | str, *, slot_key: str | None = None
    ) -> WorkspaceEntry:
        normalized_zone = self._zone(zone)
        with self.database.session() as session:
            membership = session.get(TenderDocumentMembershipRecord, membership_id)
            if membership is None:
                raise TenderWorkspaceError("membership not found")
            try:
                authority = AuthorityClass(membership.authority_class)
            except ValueError as exc:
                raise TenderWorkspaceError("unsupported document authority") from exc
            self._validate_zone_authority(normalized_zone, authority)
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
            if slot_key is not None:
                occupied = session.scalar(
                    select(TenderWorkspaceEntryRecord)
                    .where(TenderWorkspaceEntryRecord.slot_key == slot_key)
                    .where(
                        ~select(TenderWorkspaceTransitionRecord.prior_entry_id)
                        .where(
                            TenderWorkspaceTransitionRecord.prior_entry_id
                            == TenderWorkspaceEntryRecord.id
                        )
                        .exists()
                    )
                )
                if occupied is not None:
                    raise TenderWorkspaceError("semantic slot already has an active entry")
            record = TenderWorkspaceEntryRecord(
                membership_id=membership_id,
                zone_code=normalized_zone.value,
                slot_key=slot_key or uuid4().hex,
            )
            session.add(record)
            try:
                session.flush()
            except IntegrityError as exc:
                raise TenderWorkspaceError("document already assigned to this zone") from exc
            return self._entry(record, membership, document, normalized_zone)

    def replace_entry(
        self,
        case_id: str,
        release_id: int,
        prior_entry_id: int,
        replacement_path: Path,
        *,
        evidence: str,
        actor: str | None = None,
    ) -> WorkspaceReplaceResult:
        prior = self._load_entry(case_id, release_id, prior_entry_id)
        if prior.authority is AuthorityClass.SOURCE_E_HSMT:
            raise TenderWorkspaceError("generic source replacement is forbidden")
        if self._hash_path(Path(replacement_path)) == prior.sha256:
            return WorkspaceReplaceResult("NO_CHANGE_IDENTICAL_CONTENT", prior)
        return self._replace_loaded_entry(
            case_id,
            release_id,
            prior,
            replacement_path,
            evidence=evidence,
            actor=actor,
            transition_type=WorkspaceTransitionType.SUPERSEDE,
        )

    def correct_source_entry(
        self,
        case_id: str,
        release_id: int,
        prior_entry_id: int,
        replacement_path: Path | None = None,
        *,
        operator: str,
        reason: str,
        evidence: str,
    ) -> WorkspaceReplaceResult:
        if not str(operator or "").strip():
            raise TenderWorkspaceError("named operator is required")
        if not str(reason or "").strip() or not str(evidence or "").strip():
            raise TenderWorkspaceError("reason and evidence are required")
        prior = self._load_entry(case_id, release_id, prior_entry_id)
        if prior.authority is not AuthorityClass.SOURCE_E_HSMT:
            raise TenderWorkspaceError("source correction requires SOURCE_E_HSMT")
        if replacement_path is None:
            transition = self._append_transition(
                prior.id,
                None,
                WorkspaceTransitionType.SOURCE_CORRECTION,
                actor=operator.strip(),
                reason=reason.strip(),
                evidence=evidence.strip(),
            )
            withdrawn = replace(
                prior,
                operational_state=WorkspaceOperationalState.WITHDRAWN_BY_CORRECTION,
            )
            return WorkspaceReplaceResult("WITHDRAWN_BY_CORRECTION", withdrawn, transition)
        identity = extract_document_identity(Path(replacement_path))
        if identity.raw_notice_id:
            try:
                detected = OpportunityIdentity.from_raw(identity.raw_notice_id)
            except ValueError as exc:
                raise TenderWorkspaceError("source document identity is invalid") from exc
            expected = OpportunityIdentity.from_raw(prior.release_raw_id)
            if detected != expected:
                raise TenderWorkspaceError("NEW_RELEASE_REQUIRED")
        if self._hash_path(Path(replacement_path)) == prior.sha256:
            return WorkspaceReplaceResult("NO_CHANGE_IDENTICAL_CONTENT", prior)
        return self._replace_loaded_entry(
            case_id,
            release_id,
            prior,
            replacement_path,
            evidence=evidence,
            actor=operator.strip(),
            transition_type=WorkspaceTransitionType.SOURCE_CORRECTION,
            reason=reason.strip(),
        )

    def manifest(self, case_id: str, release_id: int | None = None) -> TenderWorkspaceManifest:
        case_record_id = self._case_id(case_id)
        with self.database.session() as session:
            query = (
                select(TenderWorkspaceEntryRecord)
                .join(TenderDocumentMembershipRecord)
                .join(TenderReleaseRecord)
                .join(Document)
                .where(TenderReleaseRecord.case_id == case_record_id)
                .order_by(TenderWorkspaceEntryRecord.zone_code, TenderWorkspaceEntryRecord.id)
            )
            if release_id is not None:
                self._validate_release_in_session(session, case_record_id, release_id)
                query = query.where(TenderReleaseRecord.id == release_id)
            records = tuple(session.scalars(query))
            transition_query = (
                select(TenderWorkspaceTransitionRecord)
                .join(
                    TenderWorkspaceEntryRecord,
                    TenderWorkspaceTransitionRecord.prior_entry_id
                    == TenderWorkspaceEntryRecord.id,
                )
                .join(
                    TenderDocumentMembershipRecord,
                    TenderWorkspaceEntryRecord.membership_id
                    == TenderDocumentMembershipRecord.id,
                )
                .join(
                    TenderReleaseRecord,
                    TenderDocumentMembershipRecord.release_id == TenderReleaseRecord.id,
                )
                .where(TenderReleaseRecord.case_id == case_record_id)
                .order_by(TenderWorkspaceTransitionRecord.id)
            )
            if release_id is not None:
                transition_query = transition_query.where(TenderReleaseRecord.id == release_id)
            transitions = tuple(session.scalars(transition_query))
            outgoing = {item.prior_entry_id: item for item in transitions}
            entries = tuple(
                self._entry(
                    record,
                    record.membership,
                    record.membership.document,
                    TeamBidZone(record.zone_code),
                    outgoing.get(record.id),
                )
                for record in records
            )
            history = tuple(self._transition(item) for item in transitions)
        return self._manifest(case_id, entries, release_id, history)

    def release_manifest(self, case_id: str, release_id: int) -> TenderWorkspaceManifest:
        return self.manifest(case_id, release_id)

    def release_dashboard(
        self, case_id: str, release_id: int, *, verify_integrity: bool = False
    ) -> TenderWorkspaceDashboard:
        manifest = self.release_manifest(case_id, release_id)
        with self.database.session() as session:
            release = session.get(TenderReleaseRecord, release_id)
            if release is None or release.case_id != self._case_id(case_id):
                raise TenderWorkspaceError("release does not belong to case")
            case = session.get(TenderCaseRecord, release.case_id)
            revisions = tuple(
                session.scalars(
                    select(TenderReleaseRecord.revision)
                    .where(TenderReleaseRecord.case_id == release.case_id)
                    .order_by(TenderReleaseRecord.id)
                )
            )
        zones = tuple(
            WorkspaceZoneView(
                view.zone,
                tuple(self._with_integrity(entry, verify_integrity) for entry in view.entries),
            )
            for view in manifest.zones
        )
        return TenderWorkspaceDashboard(
            case_id=case_id,
            release_id=release_id,
            release_raw_id=release.raw_id,
            release_base_id=release.base_id,
            release_revision=release.revision,
            plan_raw_id=case.plan_id_raw if case else None,
            available_revisions=revisions,
            zones=zones,
        )

    def export_release(
        self, case_id: str, release_id: int, destination: Path
    ) -> WorkspaceExportResult:
        output = Path(destination).expanduser().resolve()
        if output.exists():
            raise TenderWorkspaceError("workspace export destination already exists")
        output.parent.mkdir(parents=True, exist_ok=True)
        manifest = self.release_manifest(case_id, release_id)
        active = manifest.active_entries
        names = self._export_names(active)
        stage = Path(tempfile.mkdtemp(prefix="warehouse-export-", dir=output.parent))
        try:
            for zone in TEAM_BID_ZONES:
                (stage / zone.value).mkdir(parents=True, exist_ok=True)
            exported = []
            active_ids = {entry.id for entry in active}
            transitions_by_prior = {
                transition.prior_entry_id: {
                    "id": transition.id,
                    "successor_entry_id": transition.successor_entry_id,
                    "transition_type": transition.transition_type.value,
                    "actor": transition.actor,
                    "reason": transition.reason,
                    "evidence": transition.evidence,
                }
                for transition in manifest.history
            }
            for entry in manifest.entries:
                export_name = names.get(entry.id)
                if entry.id in active_ids:
                    target = stage / entry.zone.value / export_name
                    self.case_service.retrieve_managed_original(entry.membership_id, target)
                    exported.append(
                        {
                            "zone": entry.zone.value,
                            "release_id": entry.release_id,
                            "release_raw_id": entry.release_raw_id,
                            "release_base_id": entry.release_base_id,
                            "release_revision": entry.release_revision,
                            "slot_key": entry.slot_key,
                            "entry_id": entry.id,
                            "membership_id": entry.membership_id,
                            "document_id": entry.document_id,
                            "original_filename": entry.filename,
                            "export_filename": export_name,
                            "sha256": entry.sha256,
                            "authority_class": entry.authority.value,
                            "operational_state": entry.operational_state.value,
                            "transition": transitions_by_prior.get(entry.id),
                        }
                    )
                else:
                    exported.append(
                        {
                            "zone": entry.zone.value,
                            "release_id": entry.release_id,
                            "release_raw_id": entry.release_raw_id,
                            "release_base_id": entry.release_base_id,
                            "release_revision": entry.release_revision,
                            "slot_key": entry.slot_key,
                            "entry_id": entry.id,
                            "membership_id": entry.membership_id,
                            "document_id": entry.document_id,
                            "original_filename": entry.filename,
                            "export_filename": None,
                            "sha256": entry.sha256,
                            "authority_class": entry.authority.value,
                            "operational_state": entry.operational_state.value,
                            "transition": transitions_by_prior.get(entry.id),
                        }
                    )
            (stage / "WORKSPACE_MANIFEST.json").write_text(
                json.dumps(
                    {
                        "case_id": case_id,
                        "release_id": release_id,
                        "entries": exported,
                        "transitions": [
                            {
                                "id": transition.id,
                                "prior_entry_id": transition.prior_entry_id,
                                "successor_entry_id": transition.successor_entry_id,
                                "transition_type": transition.transition_type.value,
                                "actor": transition.actor,
                                "reason": transition.reason,
                                "evidence": transition.evidence,
                            }
                            for transition in manifest.history
                        ],
                    },
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
        return WorkspaceExportResult(output=output, entry_count=len(active))

    def export(self, case_id: str, destination: Path) -> WorkspaceExportResult:
        releases = self.case_service.get_release_manifest(case_id)
        if len(releases) != 1:
            raise TenderWorkspaceError("exact release required for multi-revision case")
        return self.export_release(case_id, releases[0].release_id, destination)

    def _replace_loaded_entry(
        self,
        case_id: str,
        release_id: int,
        prior: WorkspaceEntry,
        replacement_path: Path,
        *,
        evidence: str,
        actor: str | None,
        transition_type: WorkspaceTransitionType,
        reason: str | None = None,
    ) -> WorkspaceReplaceResult:
        if not str(evidence or "").strip():
            raise TenderWorkspaceError("replacement evidence is required")
        embedded = extract_document_identity(Path(replacement_path))
        if embedded.raw_notice_id:
            try:
                detected = OpportunityIdentity.from_raw(embedded.raw_notice_id)
            except ValueError as exc:
                raise TenderWorkspaceError("replacement document identity is invalid") from exc
            if detected != OpportunityIdentity.from_raw(prior.release_raw_id):
                raise TenderWorkspaceError("replacement release mismatch")
        digest = self._hash_path(Path(replacement_path))
        existing_document = self._document_by_sha(digest)
        membership = None
        try:
            membership = self.case_service.add_document(
                case_id,
                release_id,
                Path(replacement_path),
                authority=prior.authority,
                evidence=evidence,
                uploaded_by=actor,
            )
            with self.database.session() as session:
                current = session.get(TenderWorkspaceEntryRecord, prior.id)
                if current is None:
                    raise TenderWorkspaceError("workspace entry not found")
                outgoing = session.scalar(
                    select(TenderWorkspaceTransitionRecord).where(
                        TenderWorkspaceTransitionRecord.prior_entry_id == prior.id
                    )
                )
                if outgoing is not None:
                    raise TenderWorkspaceError("prior entry is not active")
                release = session.get(TenderReleaseRecord, release_id)
                membership_record = session.get(
                    TenderDocumentMembershipRecord, membership.id
                )
                if release is None or membership_record is None:
                    raise TenderWorkspaceError("replacement membership is invalid")
                if membership_record.release_id != release_id:
                    raise TenderWorkspaceError("replacement release mismatch")
                successor = TenderWorkspaceEntryRecord(
                    membership_id=membership.id,
                    zone_code=current.zone_code,
                    slot_key=current.slot_key or f"legacy-entry-{current.id}",
                )
                session.add(successor)
                session.flush()
                transition = TenderWorkspaceTransitionRecord(
                    prior_entry_id=current.id,
                    successor_entry_id=successor.id,
                    transition_type=transition_type.value,
                    actor=actor,
                    reason=reason or "workspace entry superseded",
                    evidence=evidence.strip(),
                )
                session.add(transition)
                session.flush()
                document = session.get(Document, membership.document_id)
                entry = self._entry(
                    successor,
                    membership_record,
                    document,
                    TeamBidZone(current.zone_code),
                )
                transition_view = self._transition(transition)
            return WorkspaceReplaceResult("REPLACED", entry, transition_view)
        except Exception:
            if membership is not None:
                self._cleanup_created(
                    [(membership.id, membership.document_id, existing_document is None)]
                )
            raise

    def _append_transition(
        self,
        prior_entry_id: int,
        successor_entry_id: int | None,
        transition_type: WorkspaceTransitionType,
        *,
        actor: str | None,
        reason: str,
        evidence: str,
    ) -> WorkspaceTransition:
        with self.database.session() as session:
            prior = session.get(TenderWorkspaceEntryRecord, prior_entry_id)
            if prior is None:
                raise TenderWorkspaceError("workspace entry not found")
            outgoing = session.scalar(
                select(TenderWorkspaceTransitionRecord).where(
                    TenderWorkspaceTransitionRecord.prior_entry_id == prior_entry_id
                )
            )
            if outgoing is not None:
                raise TenderWorkspaceError("prior entry is not active")
            if successor_entry_id == prior_entry_id:
                raise TenderWorkspaceError("workspace transition cycle is forbidden")
            transition = TenderWorkspaceTransitionRecord(
                prior_entry_id=prior_entry_id,
                successor_entry_id=successor_entry_id,
                transition_type=transition_type.value,
                actor=actor,
                reason=reason,
                evidence=evidence,
            )
            session.add(transition)
            try:
                session.flush()
            except IntegrityError as exc:
                raise TenderWorkspaceError("workspace transition violates lineage") from exc
            return self._transition(transition)

    def _load_entry(self, case_id: str, release_id: int, entry_id: int) -> WorkspaceEntry:
        case_record_id = self._case_id(case_id)
        with self.database.session() as session:
            record = session.scalar(
                select(TenderWorkspaceEntryRecord)
                .join(TenderDocumentMembershipRecord)
                .join(TenderReleaseRecord)
                .where(
                    TenderWorkspaceEntryRecord.id == entry_id,
                    TenderReleaseRecord.id == release_id,
                    TenderReleaseRecord.case_id == case_record_id,
                )
            )
            if record is None:
                raise TenderWorkspaceError("workspace entry does not belong to exact release")
            outgoing = session.scalar(
                select(TenderWorkspaceTransitionRecord).where(
                    TenderWorkspaceTransitionRecord.prior_entry_id == record.id
                )
            )
            return self._entry(
                record,
                record.membership,
                record.membership.document,
                TeamBidZone(record.zone_code),
                outgoing,
            )

    def _cleanup_created(self, created: list[tuple[int, int, bool]]) -> None:
        if not created:
            return
        with self.database.session() as session:
            for membership_id, document_id, document_created in reversed(created):
                entries = tuple(
                    session.scalars(
                        select(TenderWorkspaceEntryRecord).where(
                            TenderWorkspaceEntryRecord.membership_id == membership_id
                        )
                    )
                )
                for entry in entries:
                    session.delete(entry)
                membership = session.get(TenderDocumentMembershipRecord, membership_id)
                if membership is not None:
                    session.delete(membership)
                    session.flush()
                if document_created:
                    document = session.get(Document, document_id)
                    if document is not None:
                        refs = session.scalar(
                            select(TenderDocumentMembershipRecord.id).where(
                                TenderDocumentMembershipRecord.document_id == document_id
                            )
                        )
                        if refs is None:
                            stored = Path(document.stored_path)
                            session.delete(document)
                            try:
                                stored.unlink(missing_ok=True)
                            except OSError:
                                pass

    def _cleanup_new_documents(self, sha256: str, existing_ids: frozenset[int]) -> None:
        """Remove only newly-intaked, unreferenced Documents after a failed add."""
        with self.database.session() as session:
            documents = tuple(
                session.scalars(select(Document).where(Document.sha256 == sha256))
            )
            for document in documents:
                if document.id in existing_ids:
                    continue
                memberships = tuple(
                    session.scalars(
                        select(TenderDocumentMembershipRecord).where(
                            TenderDocumentMembershipRecord.document_id == document.id
                        )
                    )
                )
                for membership in memberships:
                    entries = tuple(
                        session.scalars(
                            select(TenderWorkspaceEntryRecord).where(
                                TenderWorkspaceEntryRecord.membership_id == membership.id
                            )
                        )
                    )
                    for entry in entries:
                        session.delete(entry)
                    session.delete(membership)
                session.flush()
                stored = Path(document.stored_path)
                session.delete(document)
                session.flush()
                try:
                    stored.unlink(missing_ok=True)
                except OSError:
                    pass

    def _manifest(
        self,
        case_id: str,
        entries: tuple[WorkspaceEntry, ...],
        release_id: int | None,
        history: tuple[WorkspaceTransition, ...],
    ) -> TenderWorkspaceManifest:
        ordered = tuple(
            sorted(
                entries,
                key=lambda entry: (
                    TEAM_BID_ZONES.index(entry.zone),
                    entry.slot_key,
                    entry.id,
                ),
            )
        )
        return TenderWorkspaceManifest(
            case_id=case_id,
            release_id=release_id,
            history=history,
            zones=tuple(
                WorkspaceZoneView(
                    zone=zone,
                    entries=tuple(
                        entry for entry in ordered if entry.zone is zone
                    ),
                )
                for zone in TEAM_BID_ZONES
            ),
        )

    @staticmethod
    def _zone(zone: TeamBidZone | str) -> TeamBidZone:
        try:
            return TeamBidZone(zone)
        except ValueError as exc:
            raise TenderWorkspaceError("unknown Team Bid workspace zone") from exc

    @staticmethod
    def _authority(authority: AuthorityClass | str) -> AuthorityClass:
        try:
            return AuthorityClass(authority)
        except ValueError as exc:
            raise TenderWorkspaceError("unsupported document authority") from exc

    @staticmethod
    def _validate_zone_authority(zone: TeamBidZone, authority: AuthorityClass) -> None:
        if authority not in ZONE_AUTHORITIES[zone]:
            raise TenderWorkspaceError(
                f"authority {authority.value} is not compatible with zone {zone.value}"
            )

    def _validate_release(self, case_id: str, release_id: int) -> None:
        case_record_id = self._case_id(case_id)
        with self.database.session() as session:
            self._validate_release_in_session(session, case_record_id, release_id)

    @staticmethod
    def _validate_release_in_session(session, case_record_id: int, release_id: int) -> None:
        release = session.get(TenderReleaseRecord, release_id)
        if release is None:
            raise TenderWorkspaceError("release not found")
        if release.case_id != case_record_id:
            raise TenderWorkspaceError("release does not belong to case")

    def _case_id(self, case_id: str) -> int:
        with self.database.session() as session:
            value = session.scalar(
                select(TenderCaseRecord.id).where(TenderCaseRecord.case_key == case_id)
            )
        if value is None:
            raise TenderWorkspaceError("case not found")
        return int(value)

    def _document_by_sha(self, sha256: str) -> Document | None:
        with self.database.session() as session:
            return session.scalar(select(Document).where(Document.sha256 == sha256))

    def _document_ids_by_sha(self, sha256: str) -> frozenset[int]:
        with self.database.session() as session:
            return frozenset(
                session.scalars(select(Document.id).where(Document.sha256 == sha256))
            )

    def _hash_candidate(self, candidate: WorkspaceCandidate) -> str:
        path = Path(candidate.source_path).expanduser().resolve()
        if not path.is_file():
            raise TenderWorkspaceError("CANDIDATE_CHANGED_SINCE_SCAN")
        digest = self._hash_path(path)
        if digest.casefold() != candidate.sha256.casefold():
            raise TenderWorkspaceError("CANDIDATE_CHANGED_SINCE_SCAN")
        return digest

    def _validate_candidate_identity(
        self,
        release_id: int,
        candidate: WorkspaceCandidate,
        authority: AuthorityClass,
    ) -> None:
        if authority is not AuthorityClass.SOURCE_E_HSMT:
            return
        if candidate.identity_status == "AMBIGUOUS":
            raise TenderWorkspaceError("PACKAGE_MISMATCH")
        if not candidate.detected_raw_id:
            return
        try:
            detected = OpportunityIdentity.from_raw(candidate.detected_raw_id)
            with self.database.session() as session:
                release = session.get(TenderReleaseRecord, release_id)
            if release is None:
                raise TenderWorkspaceError("release not found")
            expected = OpportunityIdentity.from_raw(release.raw_id)
        except (ValueError, TenderWorkspaceError) as exc:
            if isinstance(exc, TenderWorkspaceError):
                raise
            raise TenderWorkspaceError("PACKAGE_MISMATCH") from exc
        if detected.base_id != expected.base_id:
            raise TenderWorkspaceError("PACKAGE_MISMATCH")
        if detected.revision != expected.revision:
            raise TenderWorkspaceError("REVISION_TRANSITION_REQUIRED")

    def _next_managed_slot(self, release_id: int, role: str) -> str:
        with self.database.session() as session:
            release = session.get(TenderReleaseRecord, release_id)
            if release is None:
                raise TenderWorkspaceError("release not found")
            prefix = f"pkg:{release.raw_id}|role:{role}|seq:"
            values = tuple(
                session.scalars(
                    select(TenderWorkspaceEntryRecord.slot_key).where(
                        TenderWorkspaceEntryRecord.slot_key.like(f"{prefix}%")
                    )
                )
            )
        numbers = []
        for value in values:
            match = re.fullmatch(re.escape(prefix) + r"(\d+)", value or "")
            if match:
                numbers.append(int(match.group(1)))
        return f"{prefix}{max(numbers, default=0) + 1:02d}"

    @staticmethod
    def _hash_path(path: Path) -> str:
        digest = hashlib.sha256()
        try:
            with Path(path).open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
        except OSError as exc:
            raise TenderWorkspaceError("cannot read replacement file") from exc
        return digest.hexdigest()

    @staticmethod
    def _entry(
        record,
        membership,
        document,
        zone: TeamBidZone,
        outgoing=None,
    ) -> WorkspaceEntry:
        release = membership.release
        state = (
            WorkspaceOperationalState.WITHDRAWN_BY_CORRECTION
            if outgoing is not None and outgoing.successor_entry_id is None
            else WorkspaceOperationalState.SUPERSEDED
            if outgoing is not None
            else WorkspaceOperationalState.ACTIVE
        )
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
            slot_key=record.slot_key or f"legacy-entry-{record.id}",
            operational_state=state,
        )

    @staticmethod
    def _transition(record) -> WorkspaceTransition:
        return WorkspaceTransition(
            id=record.id,
            prior_entry_id=record.prior_entry_id,
            successor_entry_id=record.successor_entry_id,
            transition_type=WorkspaceTransitionType(record.transition_type),
            actor=record.actor,
            reason=record.reason,
            evidence=record.evidence,
        )

    @staticmethod
    def _with_integrity(entry: WorkspaceEntry, verify: bool) -> WorkspaceEntry:
        if not verify:
            return entry
        if not entry.stored_path.is_file():
            state = ManagedIntegrityState.MISSING
        else:
            try:
                digest = TenderWorkspaceService._hash_path(entry.stored_path)
            except TenderWorkspaceError:
                state = ManagedIntegrityState.MISSING
            else:
                state = (
                    ManagedIntegrityState.VERIFIED
                    if digest.casefold() == entry.sha256.casefold()
                    else ManagedIntegrityState.MISMATCH
                )
        return replace(entry, integrity_state=state)

    @staticmethod
    def _collision_key(filename: str) -> str:
        return unicodedata.normalize("NFKC", filename).rstrip(" .").casefold()

    @classmethod
    def _export_names(cls, entries: tuple[WorkspaceEntry, ...]) -> dict[int, str]:
        candidates = {
            entry.id: cls._managed_export_name(entry) for entry in entries
        }
        groups: dict[str, list[WorkspaceEntry]] = {}
        for entry in entries:
            groups.setdefault(cls._collision_key(candidates[entry.id]), []).append(entry)
        names = dict(candidates)
        for group in groups.values():
            if len(group) < 2:
                continue
            for entry in group:
                candidate = candidates[entry.id]
                suffix = Path(candidate).suffix
                stem = candidate[: -len(suffix)] if suffix else candidate
                names[entry.id] = f"{stem}__e{entry.id}_{entry.sha256[:8]}{suffix}"
        return names

    @staticmethod
    def _managed_export_name(entry: WorkspaceEntry) -> str:
        match = re.fullmatch(
            r"pkg:.+\|role:(?P<role>[A-Z0-9]+)\|seq:(?P<seq>\d+)",
            entry.slot_key,
        )
        if match:
            suffix = Path(entry.filename).suffix.lower()
            return f"{match.group('role')}_{int(match.group('seq')):02d}{suffix}"
        return sanitize_filename(entry.filename)


__all__ = [
    "TEAM_BID_ZONES",
    "ManagedIntegrityState",
    "TeamBidZone",
    "TenderCaseSearchResult",
    "TenderWorkspaceDashboard",
    "TenderWorkspaceError",
    "TenderWorkspaceManifest",
    "TenderWorkspaceService",
    "WorkspaceEntry",
    "WorkspaceExportResult",
    "WorkspaceOperationalState",
    "WorkspaceReplaceResult",
    "WorkspaceTransition",
    "WorkspaceTransitionType",
    "WorkspaceZoneView",
]
