"""Application service for exact-SHA managed-source integrity and recovery."""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select

from .db import Database
from .models import (
    Document,
    TenderCaseRecord,
    TenderDocumentMembershipRecord,
    TenderReleaseRecord,
)
from .tender_recovery import (
    ManagedIntegrityState,
    RecoveryAction,
    RecoveryInspection,
    RecoveryReport,
    RecoveryResult,
)
from .tender_recovery_persistence import TenderRecoveryPersistence


class TenderRecoveryService:
    """Reconcile and restore only an exact existing package membership."""

    def __init__(self, database: Database, document_root: Path):
        self.database = database
        self.document_root = Path(document_root).expanduser().resolve()
        self.persistence = TenderRecoveryPersistence(database)

    def inspect_release(self, case_id: str, release_id: int) -> RecoveryReport:
        self._validate_release(case_id, release_id)
        with self.database.session() as session:
            rows = tuple(
                session.execute(
                    select(TenderDocumentMembershipRecord, Document)
                    .join(Document, Document.id == TenderDocumentMembershipRecord.document_id)
                    .where(TenderDocumentMembershipRecord.release_id == release_id)
                    .order_by(TenderDocumentMembershipRecord.id)
                )
            )
        entries = tuple(self._inspect_membership(membership, document) for membership, document in rows)
        return RecoveryReport(case_id=case_id, release_id=release_id, entries=entries)

    def reconcile(self, case_id: str, release_id: int) -> RecoveryReport:
        case_record_id = self._validate_release(case_id, release_id)
        report = self.inspect_release(case_id, release_id)
        for entry in report.entries:
            self.persistence.append(
                case_id=self._case_record_id(case_id),
                release_id=release_id,
                membership_id=entry.membership_id,
                document_id=entry.document_id,
                action=RecoveryAction.INTEGRITY_SCAN.value,
                expected_sha256=entry.expected_sha256,
                observed_sha256=entry.observed_sha256,
                candidate_sha256=None,
                managed_path=str(entry.path),
                candidate_path=None,
                quarantine_path=None,
                actor="system",
                reason="managed source integrity scan",
                evidence=f"state={entry.state.value}",
                result=entry.state.value,
            )
        orphans = tuple(
            RecoveryInspection(
                membership_id=None,
                document_id=None,
                release_id=None,
                expected_sha256=None,
                observed_sha256=self._sha(path),
                path=path,
                state=ManagedIntegrityState.ORPHANED,
            )
            for path in self._orphan_paths()
        )
        for orphan in orphans:
            self.persistence.append(
                case_id=case_record_id,
                release_id=None,
                membership_id=None,
                document_id=None,
                action=RecoveryAction.ORPHAN_SCAN.value,
                expected_sha256=None,
                observed_sha256=orphan.observed_sha256,
                candidate_sha256=None,
                managed_path=str(orphan.path),
                candidate_path=None,
                quarantine_path=None,
                actor="system",
                reason="unreferenced managed bytes",
                evidence="orphan is not auto-adopted",
                result=ManagedIntegrityState.ORPHANED.value,
            )
        return RecoveryReport(case_id=case_id, release_id=release_id, entries=report.entries, orphans=orphans)

    def assess_candidate(
        self,
        case_id: str,
        release_id: int,
        membership_id: int,
        candidate_path: Path,
    ) -> RecoveryInspection:
        """Classify an explicit candidate without changing managed state."""
        self._validate_release(case_id, release_id)
        with self.database.session() as session:
            membership = session.get(TenderDocumentMembershipRecord, membership_id)
            if membership is None:
                raise ValueError("membership not found")
            if membership.release_id != release_id:
                raise ValueError("membership does not belong to release")
            document = session.get(Document, membership.document_id)
            if document is None:
                raise ValueError("managed document not found")
        candidate = Path(candidate_path).expanduser().resolve()
        if not candidate.is_file():
            raise ValueError("recovery candidate is missing")
        observed = self._sha(candidate)
        state = (
            ManagedIntegrityState.RECOVERABLE
            if observed.casefold() == document.sha256.casefold()
            else ManagedIntegrityState.MISMATCH
        )
        return RecoveryInspection(
            membership_id=membership.id,
            document_id=document.id,
            release_id=release_id,
            expected_sha256=document.sha256,
            observed_sha256=observed,
            path=candidate,
            state=state,
        )

    def recover(
        self,
        case_id: str,
        release_id: int,
        membership_id: int,
        candidate_path: Path,
        *,
        actor: str,
        reason: str,
        evidence: str,
    ) -> RecoveryResult:
        if not str(actor or "").strip() or not str(reason or "").strip() or not str(evidence or "").strip():
            raise ValueError("actor, reason and evidence are required")
        case_record_id = self._validate_release(case_id, release_id)
        with self.database.session() as session:
            membership = session.get(TenderDocumentMembershipRecord, membership_id)
            if membership is None:
                raise ValueError("membership not found")
            if membership.release_id != release_id:
                raise ValueError("membership does not belong to release")
            document = session.get(Document, membership.document_id)
            if document is None:
                raise ValueError("managed document not found")
            expected_sha = document.sha256
            managed_path = Path(document.stored_path).expanduser().resolve()
            document_id = document.id
        self._ensure_managed_target(managed_path)
        candidate = Path(candidate_path).expanduser().resolve()
        if not candidate.is_file():
            raise ValueError("recovery candidate is missing")
        candidate_sha = self._sha(candidate)
        if candidate_sha.casefold() != expected_sha.casefold():
            self.persistence.append(
                case_id=case_record_id,
                release_id=release_id,
                membership_id=membership_id,
                document_id=document_id,
                action=RecoveryAction.RECOVER.value,
                expected_sha256=expected_sha,
                observed_sha256=self._sha(managed_path) if managed_path.is_file() else None,
                candidate_sha256=candidate_sha,
                managed_path=str(managed_path),
                candidate_path=str(candidate),
                quarantine_path=None,
                actor=actor.strip(),
                reason=reason.strip(),
                evidence=evidence.strip(),
                result="REJECTED_WRONG_SHA",
            )
            raise ValueError("recovery candidate SHA-256 mismatch")

        observed_sha = self._sha(managed_path) if managed_path.is_file() else None
        quarantine_path: Path | None = None
        if observed_sha is not None and observed_sha.casefold() != expected_sha.casefold():
            quarantine_path = self._quarantine(managed_path, observed_sha)
        managed_path.parent.mkdir(parents=True, exist_ok=True)
        staging_dir = self.document_root / ".recovery-staging"
        staging_dir.mkdir(parents=True, exist_ok=True)
        staged_fd, staged_name = tempfile.mkstemp(
            prefix="recover-", suffix=managed_path.suffix, dir=staging_dir
        )
        os.close(staged_fd)
        staged = Path(staged_name)
        try:
            shutil.copyfile(candidate, staged)
            if self._sha(staged).casefold() != expected_sha.casefold():
                raise ValueError("staged recovery SHA-256 mismatch")
            os.replace(staged, managed_path)
        finally:
            staged.unlink(missing_ok=True)
        verified_sha = self._sha(managed_path)
        if verified_sha.casefold() != expected_sha.casefold():
            raise ValueError("recovered managed object failed SHA-256 verification")
        self.persistence.append(
            case_id=case_record_id,
            release_id=release_id,
            membership_id=membership_id,
            document_id=document_id,
            action=RecoveryAction.RECOVER.value,
            expected_sha256=expected_sha,
            observed_sha256=observed_sha,
            candidate_sha256=candidate_sha,
            managed_path=str(managed_path),
            candidate_path=str(candidate),
            quarantine_path=str(quarantine_path) if quarantine_path else None,
            actor=actor.strip(),
            reason=reason.strip(),
            evidence=evidence.strip(),
            result=ManagedIntegrityState.RECOVERED.value,
        )
        return RecoveryResult(
            state=ManagedIntegrityState.RECOVERED,
            membership_id=membership_id,
            document_id=document_id,
            release_id=release_id,
            expected_sha256=expected_sha,
            verified_sha256=verified_sha,
            managed_path=managed_path,
            quarantine_path=quarantine_path,
        )

    def history(self, case_id: str, release_id: int):
        case_record_id = self._validate_release(case_id, release_id)
        return self.persistence.list(case_id=case_record_id, release_id=release_id)

    def _validate_release(self, case_id: str, release_id: int) -> int:
        case_record_id = self._case_record_id(case_id)
        with self.database.session() as session:
            release = session.get(TenderReleaseRecord, release_id)
            if release is None:
                raise ValueError("release not found")
            if release.case_id != case_record_id:
                raise ValueError("release does not belong to case")
        return case_record_id

    def _case_record_id(self, case_id: str) -> int:
        with self.database.session() as session:
            value = session.scalar(select(TenderCaseRecord.id).where(TenderCaseRecord.case_key == case_id))
        if value is None:
            raise ValueError("case not found")
        return int(value)

    def _inspect_membership(self, membership, document) -> RecoveryInspection:
        path = Path(document.stored_path).expanduser().resolve()
        if not self._beneath_root(path):
            return RecoveryInspection(
                membership_id=membership.id,
                document_id=document.id,
                release_id=membership.release_id,
                expected_sha256=document.sha256,
                observed_sha256=None,
                path=path,
                state=ManagedIntegrityState.MISMATCH,
            )
        if not path.is_file():
            state = ManagedIntegrityState.MISSING
            observed = None
        else:
            observed = self._sha(path)
            state = (
                ManagedIntegrityState.VERIFIED
                if observed.casefold() == document.sha256.casefold()
                else ManagedIntegrityState.MISMATCH
            )
        return RecoveryInspection(
            membership_id=membership.id,
            document_id=document.id,
            release_id=membership.release_id,
            expected_sha256=document.sha256,
            observed_sha256=observed,
            path=path,
            state=state,
        )

    def _orphan_paths(self) -> tuple[Path, ...]:
        if not self.document_root.is_dir():
            return ()
        excluded = {".recovery-staging", ".recovery-quarantine"}
        with self.database.session() as session:
            referenced = {
                Path(path).expanduser().resolve()
                for path in session.scalars(select(Document.stored_path))
            }
        return tuple(
            path
            for path in sorted(self.document_root.rglob("*"))
            if path.is_file() and not any(part in excluded for part in path.relative_to(self.document_root).parts) and path.resolve() not in referenced
        )

    def _quarantine(self, managed_path: Path, observed_sha: str) -> Path:
        directory = self.document_root / ".recovery-quarantine"
        directory.mkdir(parents=True, exist_ok=True)
        destination = directory / f"{managed_path.name}.{observed_sha[:16]}.{uuid4().hex}.quarantine"
        shutil.copy2(managed_path, destination)
        if self._sha(destination).casefold() != observed_sha.casefold():
            destination.unlink(missing_ok=True)
            raise ValueError("quarantine verification failed")
        return destination

    def _ensure_managed_target(self, path: Path) -> None:
        if not self._beneath_root(path):
            raise ValueError("managed target escapes document root")

    def _beneath_root(self, path: Path) -> bool:
        try:
            path.relative_to(self.document_root)
        except ValueError:
            return False
        return True

    @staticmethod
    def _sha(path: Path) -> str:
        if not path.is_file():
            return ""
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
