"""Auditable, immutable intake for manual and future web tender documents."""

from __future__ import annotations

import hashlib
import json
import logging
import mimetypes
import os
import re
import stat
import tempfile
import unicodedata
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath

from sqlalchemy import func, or_, select

from .db import Database
from .document_taxonomy import classify_document
from .models import Document, Notice

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = frozenset({".pdf", ".docx", ".xlsx", ".zip"})
DOCUMENT_TYPES = {
    ".pdf": "PDF",
    ".docx": "DOCX",
    ".xlsx": "XLSX",
    ".zip": "ZIP",
}
MIME_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".zip": "application/zip",
}
WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


class DocumentIntakeError(RuntimeError):
    """Base class for a fail-closed document intake error."""


class DocumentValidationError(DocumentIntakeError):
    """The selected input is unsupported, empty, unreadable or unsafe."""


class DocumentStorageError(DocumentIntakeError):
    """The original could not be stored without risking overwrite or loss."""


class DocumentIdentityMismatch(DocumentValidationError):
    """Trusted identity evidence points at a different tender."""

    def __init__(self, expected: str, detected: str):
        self.expected = expected
        self.detected = detected
        super().__init__(
            f"CRITICAL_MISMATCH: expected tender {expected}; detected {detected}."
        )


@dataclass(frozen=True)
class DocumentIntakeResult:
    outcome: str
    document_id: int
    original_filename: str
    stored_path: Path
    document_type: str
    mime_type: str
    file_size: int
    sha256: str
    version: int
    tender_id: int | None
    tender_identifier: str | None
    discovered_files: tuple[str, ...] = ()
    identity_status: str = "UNLINKED"
    expected_identity: str | None = None
    detected_identity: str | None = None
    file_format: str | None = None
    template_code: str | None = None
    package_type: str | None = None
    selection_method: str | None = None
    classification_status: str = "UNKNOWN"


@dataclass(frozen=True)
class DocumentBatchResult:
    results: tuple[DocumentIntakeResult, ...]

    @property
    def imported(self) -> int:
        return sum(item.outcome == "IMPORTED" for item in self.results)

    @property
    def duplicates(self) -> int:
        return sum(item.outcome == "DUPLICATE" for item in self.results)


@dataclass(frozen=True)
class DocumentManifestEntry:
    document_id: int
    document_type: str
    file_format: str | None
    template_code: str | None
    package_type: str | None
    selection_method: str | None
    classification_status: str
    filename: str
    sha256: str
    version: int
    source: str
    status: str
    stored_path: Path
    uploaded_at: datetime


@dataclass(frozen=True)
class TenderDocumentManifest:
    tender_id: int
    tender_identifier: str
    tender_title: str
    source: str
    identity_status: str
    documents: tuple[DocumentManifestEntry, ...]


@dataclass(frozen=True)
class TenderDocumentTarget:
    """Minimal verified tender context exposed to document acquisition services."""

    tender_id: int
    identifier: str
    source_name: str
    source_url: str


@dataclass(frozen=True)
class _IdentityResolution:
    status: str
    tender: Notice | None
    expected: str | None
    detected: str | None


def sanitize_filename(filename: str) -> str:
    """Return a Windows-safe leaf name while retaining the supported extension."""
    leaf = Path(filename.replace("\\", "/")).name
    normalized = unicodedata.normalize("NFKC", leaf)
    suffix = Path(normalized).suffix.lower()
    stem = normalized[: -len(suffix)] if suffix else normalized
    stem = re.sub(r"[^\w .()\-]+", "_", stem, flags=re.UNICODE)
    stem = re.sub(r"\s+", " ", stem).strip(" .")
    if not stem:
        stem = "document"
    if stem.upper() in WINDOWS_RESERVED_NAMES:
        stem = f"_{stem}"
    return f"{stem[:120]}{suffix}"


def _safe_scope(value: str) -> str:
    safe = sanitize_filename(value).rsplit(".", 1)[0]
    return safe or "unlinked"


class DocumentIntakeService:
    """Store one immutable original and create one auditable database record."""

    def __init__(self, database: Database, document_root: Path):
        self.database = database
        self.database.require_current_schema()
        self.document_root = document_root.expanduser().resolve()

    def resolve_tender_target(self, tender_reference: str) -> TenderDocumentTarget:
        """Resolve one unique tender before any web document acquisition starts."""
        tender = self._lookup_tender(tender_reference)
        if tender is None:
            raise DocumentValidationError(
                "Không tìm thấy tender đã xác định; không tải hoặc tự đoán tài liệu từ web."
            )
        return TenderDocumentTarget(
            tender_id=tender.id,
            identifier=self._notice_identifier(tender),
            source_name=tender.source_name or tender.source_kind or "web",
            source_url=tender.source_url,
        )

    def verify_tender_identity(
        self,
        tender_reference: str,
        *,
        detected_tender_reference: str | None,
        source_url: str | None,
    ) -> str:
        """Run the existing Identity Guard before a staged web file is hashed."""
        return self._resolve_identity(
            tender_reference,
            detected_tender_reference=detected_tender_reference,
            source_url=source_url,
        ).status

    def intake_path(
        self,
        input_path: Path,
        *,
        tender_reference: str | None = None,
        document_name: str | None = None,
        document_source: str = "manual_upload",
        source_url: str | None = None,
        uploaded_by: str | None = None,
        detected_tender_reference: str | None = None,
    ) -> DocumentBatchResult:
        candidate = input_path.expanduser()
        if candidate.is_symlink():
            raise DocumentValidationError("Không chấp nhận đường dẫn liên kết (symlink).")
        if candidate.is_dir():
            supported = sorted(
                path
                for path in candidate.rglob("*")
                if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
            )
            if not supported:
                raise DocumentValidationError("Thư mục không có PDF, DOCX, XLSX hoặc ZIP.")
            results = tuple(
                self.intake_file(
                    path,
                    tender_reference=tender_reference,
                    document_name=document_name if len(supported) == 1 else None,
                    document_source=document_source,
                    source_url=source_url,
                    uploaded_by=uploaded_by,
                    detected_tender_reference=detected_tender_reference,
                )
                for path in supported
            )
            return DocumentBatchResult(results)
        return DocumentBatchResult(
            (
                self.intake_file(
                    candidate,
                    tender_reference=tender_reference,
                    document_name=document_name,
                    document_source=document_source,
                    source_url=source_url,
                    uploaded_by=uploaded_by,
                    detected_tender_reference=detected_tender_reference,
                ),
            )
        )

    def intake_file(
        self,
        input_path: Path,
        *,
        tender_reference: str | None = None,
        document_name: str | None = None,
        document_source: str = "manual_upload",
        source_url: str | None = None,
        uploaded_by: str | None = None,
        detected_tender_reference: str | None = None,
    ) -> DocumentIntakeResult:
        logger.info(
            "DOCUMENT_INTAKE_START source=%s filename=%s",
            document_source,
            input_path.name,
        )
        path = self._validate_input(input_path)
        if document_source not in {"manual_upload", "web"}:
            raise DocumentValidationError("Nguồn tài liệu không được hỗ trợ.")
        if document_source == "web" and not source_url:
            raise DocumentValidationError("Tài liệu từ web phải có source_url.")

        sha256, file_size = self._hash_file(path)
        logger.info("HASH_DONE sha256=%s file_size=%s", sha256, file_size)
        discovered_files = self._inspect_zip(path) if path.suffix.lower() == ".zip" else ()
        identity = self._resolve_identity(
            tender_reference,
            detected_tender_reference=detected_tender_reference,
            source_url=source_url,
        )
        duplicate = self._find_duplicate(sha256)
        logger.info("DUPLICATE_CHECK_DONE duplicate=%s", duplicate is not None)
        if duplicate is not None:
            self._guard_duplicate_identity(duplicate, identity)
            stored_path = Path(duplicate.stored_path)
            if not stored_path.is_file():
                raise DocumentStorageError(
                    "Bản ghi trùng tồn tại nhưng file gốc không còn trong Document Store."
                )
            result = self._result(
                duplicate,
                "DUPLICATE",
                self._tender_identifier(duplicate.tender_id),
                identity_status=self._document_identity_status(duplicate),
                expected_identity=identity.expected,
                detected_identity=identity.detected,
            )
            logger.info(
                "DOCUMENT_INTAKE_DONE outcome=DUPLICATE document_id=%s",
                duplicate.id,
            )
            return result

        tender = identity.tender
        classification = classify_document(
            metadata_title=(document_name or "").strip() or None,
            filename=path.name,
            identity_status=identity.status,
            package_type=tender.contract_type if tender else None,
            selection_method=tender.selection_method if tender else None,
        )
        version = self._next_version(tender.id if tender else None)
        safe_filename = sanitize_filename(path.name)
        scope = self._tender_scope(tender)
        source_scope = self._source_scope(tender, document_source)
        destination = self.document_root / source_scope / scope / sha256 / safe_filename
        stored_path, created = self._atomic_store(path, destination)
        logger.info("FILE_STORED sha256=%s stored_path=%s", sha256, stored_path)
        mime_type = MIME_TYPES.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0]
        try:
            document = self._create_record(
                tender_id=tender.id if tender else None,
                document_source=document_source,
                document_type=classification.document_type.value,
                file_format=DOCUMENT_TYPES[path.suffix.lower()],
                template_code=classification.template_code,
                package_type=classification.package_type,
                selection_method=classification.selection_method,
                classification_status=classification.status.value,
                display_name=(document_name or "").strip() or None,
                original_filename=path.name,
                stored_path=stored_path,
                mime_type=mime_type or "application/octet-stream",
                file_size=file_size,
                sha256=sha256,
                version=version,
                source_url=source_url,
                uploaded_by=(uploaded_by or "").strip() or None,
                zip_supported_entries=discovered_files,
                status=identity.status,
            )
        except Exception:
            if created:
                self._cleanup_orphan(stored_path)
            raise
        logger.info(
            "DOCUMENT_RECORD_CREATED document_id=%s tender_id=%s version=%s",
            document.id,
            document.tender_id,
            document.version,
        )
        result = self._result(
            document,
            "IMPORTED",
            self._notice_identifier(tender) if tender else None,
            identity_status=identity.status,
            expected_identity=identity.expected,
            detected_identity=identity.detected,
        )
        logger.info(
            "DOCUMENT_INTAKE_DONE outcome=IMPORTED document_id=%s",
            document.id,
        )
        return result

    @staticmethod
    def _validate_input(input_path: Path) -> Path:
        try:
            if input_path.is_symlink():
                raise DocumentValidationError(
                    "Không chấp nhận đường dẫn liên kết (symlink)."
                )
            path = input_path.expanduser().resolve(strict=True)
            if not path.is_file():
                raise DocumentValidationError("Đường dẫn không phải là một file.")
            extension = path.suffix.lower()
            if extension not in SUPPORTED_EXTENSIONS:
                raise DocumentValidationError("Chỉ hỗ trợ PDF, DOCX, XLSX và ZIP.")
            if path.stat().st_size <= 0:
                raise DocumentValidationError("Không thể nhập file rỗng.")
            with path.open("rb") as stream:
                stream.read(1)
            return path
        except DocumentIntakeError:
            raise
        except (OSError, PermissionError) as exc:
            raise DocumentValidationError("Không thể đọc file đã chọn.") from exc

    @staticmethod
    def _hash_file(path: Path) -> tuple[str, int]:
        digest = hashlib.sha256()
        size = 0
        try:
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
                    size += len(chunk)
        except OSError as exc:
            raise DocumentValidationError("Không thể đọc file để tính SHA-256.") from exc
        return digest.hexdigest(), size

    @staticmethod
    def _inspect_zip(path: Path) -> tuple[str, ...]:
        supported: list[str] = []
        try:
            with zipfile.ZipFile(path) as archive:
                for entry in archive.infolist():
                    normalized = entry.filename.replace("\\", "/")
                    pure_path = PurePosixPath(normalized)
                    mode = entry.external_attr >> 16
                    if (
                        pure_path.is_absolute()
                        or ".." in pure_path.parts
                        or (pure_path.parts and ":" in pure_path.parts[0])
                        or stat.S_ISLNK(mode)
                    ):
                        raise DocumentValidationError(
                            f"ZIP chứa đường dẫn không an toàn: {entry.filename}"
                        )
                    if not entry.is_dir() and pure_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                        supported.append(normalized)
        except DocumentIntakeError:
            raise
        except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
            raise DocumentValidationError("File ZIP không hợp lệ hoặc không thể đọc.") from exc
        return tuple(dict.fromkeys(supported))

    def _find_duplicate(self, sha256: str) -> Document | None:
        with self.database.session() as session:
            return session.scalar(select(Document).where(Document.sha256 == sha256))

    def _lookup_tender(self, reference: str | None) -> Notice | None:
        value = (reference or "").strip()
        if not value:
            return None
        predicates = [Notice.notice_code == value, Notice.source_notice_id == value]
        if value.isdigit():
            predicates.append(Notice.id == int(value))
        with self.database.session() as session:
            matches = tuple(
                session.scalars(select(Notice).where(or_(*predicates)).limit(2))
            )
        if len(matches) > 1:
            raise DocumentValidationError(
                "Mã tender không duy nhất trong database; không tự động lựa chọn."
            )
        return matches[0] if matches else None

    def _lookup_tender_by_source_url(self, source_url: str | None) -> Notice | None:
        value = (source_url or "").strip()
        if not value:
            return None
        with self.database.session() as session:
            matches = tuple(
                session.scalars(
                    select(Notice).where(Notice.source_url == value).limit(2)
                )
            )
        if len(matches) > 1:
            raise DocumentValidationError(
                "URL nguồn khớp nhiều tender; không tự động lựa chọn."
            )
        return matches[0] if matches else None

    def _resolve_identity(
        self,
        tender_reference: str | None,
        *,
        detected_tender_reference: str | None,
        source_url: str | None,
    ) -> _IdentityResolution:
        expected_value = (tender_reference or "").strip() or None
        detected_value = (detected_tender_reference or "").strip() or None
        logger.info(
            "DOCUMENT_IDENTITY_CHECK expected=%s detected=%s source_url_present=%s",
            expected_value,
            detected_value,
            bool(source_url),
        )
        expected = self._lookup_tender(expected_value)
        detected = self._lookup_tender(detected_value)
        if detected_value is None:
            detected = self._lookup_tender_by_source_url(source_url)
            if detected is not None:
                detected_value = self._notice_identifier(detected)

        unknown_expected = expected_value is not None and expected is None
        unknown_detected = detected_value is not None and detected is None
        if unknown_expected or unknown_detected:
            logger.info(
                "DOCUMENT_IDENTITY_UNLINKED status=NEEDS_REVIEW expected=%s detected=%s",
                expected_value,
                detected_value,
            )
            return _IdentityResolution(
                status="NEEDS_REVIEW",
                tender=None,
                expected=expected_value,
                detected=detected_value,
            )

        if expected is not None and detected is not None and expected.id != detected.id:
            expected_identifier = self._notice_identifier(expected)
            detected_identifier = self._notice_identifier(detected)
            logger.error(
                "DOCUMENT_IDENTITY_MISMATCH expected=%s detected=%s",
                expected_identifier,
                detected_identifier,
            )
            raise DocumentIdentityMismatch(expected_identifier, detected_identifier)

        tender = expected or detected
        if tender is None:
            logger.info("DOCUMENT_IDENTITY_UNLINKED status=UNLINKED")
            return _IdentityResolution(
                status="UNLINKED",
                tender=None,
                expected=expected_value,
                detected=detected_value,
            )

        identifier = self._notice_identifier(tender)
        logger.info("DOCUMENT_IDENTITY_VERIFIED tender=%s", identifier)
        return _IdentityResolution(
            status="VERIFIED_LINKED",
            tender=tender,
            expected=expected_value or identifier,
            detected=detected_value,
        )

    def _guard_duplicate_identity(
        self,
        duplicate: Document,
        identity: _IdentityResolution,
    ) -> None:
        if (
            identity.status == "NEEDS_REVIEW"
            and identity.expected is not None
            and duplicate.tender_id is not None
        ):
            detected = self._tender_identifier(duplicate.tender_id) or "UNLINKED"
            logger.error(
                "DOCUMENT_IDENTITY_MISMATCH expected=%s detected=%s duplicate_document_id=%s",
                identity.expected,
                detected,
                duplicate.id,
            )
            raise DocumentIdentityMismatch(identity.expected, detected)
        if identity.tender is None:
            return
        if duplicate.tender_id == identity.tender.id:
            return
        expected = self._notice_identifier(identity.tender)
        detected = self._tender_identifier(duplicate.tender_id) or "UNLINKED"
        logger.error(
            "DOCUMENT_IDENTITY_MISMATCH expected=%s detected=%s duplicate_document_id=%s",
            expected,
            detected,
            duplicate.id,
        )
        raise DocumentIdentityMismatch(expected, detected)

    def _next_version(self, tender_id: int | None) -> int:
        with self.database.session() as session:
            predicate = (
                Document.tender_id == tender_id
                if tender_id is not None
                else Document.tender_id.is_(None)
            )
            current = session.scalar(select(func.max(Document.version)).where(predicate))
        return int(current or 0) + 1

    @staticmethod
    def _tender_scope(tender: Notice | None) -> str:
        if tender is None:
            return "unlinked"
        identifier = tender.notice_code or tender.source_notice_id or f"tender-{tender.id}"
        return _safe_scope(identifier)

    @staticmethod
    def _source_scope(tender: Notice | None, document_source: str) -> str:
        return _safe_scope(tender.source_name or document_source) if tender else _safe_scope(
            document_source
        )

    @staticmethod
    def _notice_identifier(tender: Notice) -> str:
        return tender.notice_code or tender.source_notice_id or str(tender.id)

    def _tender_identifier(self, tender_id: int | None) -> str | None:
        if tender_id is None:
            return None
        with self.database.session() as session:
            tender = session.get(Notice, tender_id)
            return self._notice_identifier(tender) if tender else None

    @staticmethod
    def _document_identity_status(document: Document) -> str:
        if document.status in {
            "VERIFIED_LINKED",
            "UNLINKED",
            "MISMATCH",
            "NEEDS_REVIEW",
        }:
            return document.status
        return "VERIFIED_LINKED" if document.tender_id is not None else "UNLINKED"

    def manifest_for_tender(self, tender_reference: str) -> TenderDocumentManifest:
        """Return the database-backed immutable document manifest for one tender."""
        tender = self._lookup_tender(tender_reference)
        if tender is None:
            raise DocumentValidationError("Không tìm thấy tender để lập document manifest.")
        with self.database.session() as session:
            documents = tuple(
                session.scalars(
                    select(Document)
                    .where(Document.tender_id == tender.id)
                    .order_by(Document.version, Document.id)
                )
            )
        source = tender.source_name or "unknown"
        entries = tuple(
            DocumentManifestEntry(
                document_id=document.id,
                document_type=document.document_type,
                file_format=document.file_format or self._legacy_file_format(document),
                template_code=document.template_code,
                package_type=document.package_type,
                selection_method=document.selection_method,
                classification_status=document.classification_status or "UNKNOWN",
                filename=document.original_filename,
                sha256=document.sha256,
                version=document.version,
                source=document.document_source,
                status=self._document_identity_status(document),
                stored_path=Path(document.stored_path),
                uploaded_at=document.uploaded_at,
            )
            for document in documents
        )
        return TenderDocumentManifest(
            tender_id=tender.id,
            tender_identifier=self._notice_identifier(tender),
            tender_title=tender.title or "Chưa có tên gói",
            source=source,
            identity_status="VERIFIED_LINKED",
            documents=entries,
        )

    def _atomic_store(self, source: Path, destination: Path) -> tuple[Path, bool]:
        temporary_path: Path | None = None
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                raise DocumentStorageError(
                    "Document Store đã có file cùng đường dẫn; không ghi đè."
                )
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=destination.parent,
                prefix=".intake-",
                suffix=".tmp",
                delete=False,
            ) as target, source.open("rb") as origin:
                temporary_path = Path(target.name)
                for chunk in iter(lambda: origin.read(1024 * 1024), b""):
                    target.write(chunk)
                target.flush()
                os.fsync(target.fileno())
            os.link(temporary_path, destination)
            temporary_path.unlink()
            return destination.resolve(), True
        except FileExistsError as exc:
            raise DocumentStorageError("Document Store từ chối ghi đè file gốc.") from exc
        except DocumentIntakeError:
            raise
        except OSError as exc:
            raise DocumentStorageError("Không thể lưu file vào Document Store.") from exc
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink(missing_ok=True)

    def _create_record(
        self,
        *,
        tender_id: int | None,
        document_source: str,
        document_type: str,
        file_format: str,
        template_code: str | None,
        package_type: str | None,
        selection_method: str | None,
        classification_status: str,
        display_name: str | None,
        original_filename: str,
        stored_path: Path,
        mime_type: str,
        file_size: int,
        sha256: str,
        version: int,
        source_url: str | None,
        uploaded_by: str | None,
        zip_supported_entries: tuple[str, ...],
        status: str,
    ) -> Document:
        document = Document(
            tender_id=tender_id,
            document_source=document_source,
            document_type=document_type,
            file_format=file_format,
            template_code=template_code,
            package_type=package_type,
            selection_method=selection_method,
            classification_status=classification_status,
            display_name=display_name,
            original_filename=original_filename,
            stored_path=str(stored_path),
            mime_type=mime_type,
            file_size=file_size,
            sha256=sha256,
            version=version,
            source_url=source_url,
            uploaded_by=uploaded_by,
            status=status,
            zip_supported_entries=(
                json.dumps(zip_supported_entries, ensure_ascii=False)
                if zip_supported_entries
                else None
            ),
        )
        with self.database.session() as session:
            session.add(document)
            session.flush()
        return document

    @staticmethod
    def _cleanup_orphan(path: Path) -> None:
        path.unlink(missing_ok=True)
        try:
            path.parent.rmdir()
        except OSError:
            return

    @staticmethod
    def _result(
        document: Document,
        outcome: str,
        tender_identifier: str | None,
        *,
        identity_status: str,
        expected_identity: str | None,
        detected_identity: str | None,
    ) -> DocumentIntakeResult:
        entries = tuple(json.loads(document.zip_supported_entries or "[]"))
        return DocumentIntakeResult(
            outcome=outcome,
            document_id=document.id,
            original_filename=document.original_filename,
            stored_path=Path(document.stored_path),
            document_type=document.document_type,
            mime_type=document.mime_type,
            file_size=document.file_size,
            sha256=document.sha256,
            version=document.version,
            tender_id=document.tender_id,
            tender_identifier=tender_identifier,
            discovered_files=entries,
            identity_status=identity_status,
            expected_identity=expected_identity,
            detected_identity=detected_identity,
            file_format=document.file_format or DocumentIntakeService._legacy_file_format(
                document
            ),
            template_code=document.template_code,
            package_type=document.package_type,
            selection_method=document.selection_method,
            classification_status=document.classification_status or "UNKNOWN",
        )

    @staticmethod
    def _legacy_file_format(document: Document) -> str | None:
        if document.document_type in DOCUMENT_TYPES.values():
            return document.document_type
        return Path(document.original_filename).suffix.lstrip(".").upper() or None
