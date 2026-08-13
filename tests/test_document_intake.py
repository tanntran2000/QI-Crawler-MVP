from __future__ import annotations

import hashlib
import logging
import zipfile
from pathlib import Path

import pytest
from sqlalchemy import func, select

from qi_crawler.db import Database
from qi_crawler.document_intake import (
    DocumentIntakeService,
    DocumentStorageError,
    DocumentValidationError,
    sanitize_filename,
)
from qi_crawler.models import Document, Notice


@pytest.fixture
def intake(tmp_path: Path) -> tuple[DocumentIntakeService, Database, Path]:
    database = Database(f"sqlite:///{tmp_path / 'documents.db'}")
    root = tmp_path / "store"
    return DocumentIntakeService(database, root), database, root


def _write(path: Path, content: bytes) -> Path:
    path.write_bytes(content)
    return path


@pytest.mark.parametrize(
    ("filename", "content", "document_type"),
    [
        ("hsmt.pdf", b"%PDF-1.7\nmanual hsmt", "PDF"),
        ("yeu-cau.docx", b"PK\x03\x04docx-content", "DOCX"),
        ("bang-khoi-luong.xlsx", b"PK\x03\x04xlsx-content", "XLSX"),
    ],
)
def test_supported_document_upload_preserves_original_and_sha256(
    intake: tuple[DocumentIntakeService, Database, Path],
    tmp_path: Path,
    filename: str,
    content: bytes,
    document_type: str,
) -> None:
    service, database, root = intake
    source = _write(tmp_path / filename, content)

    result = service.intake_file(source, uploaded_by="Team Bid")

    assert result.outcome == "IMPORTED"
    assert result.document_type == document_type
    assert result.file_size == len(content)
    assert result.sha256 == hashlib.sha256(content).hexdigest()
    assert result.stored_path.read_bytes() == content
    assert result.stored_path.is_relative_to(root.resolve())
    with database.session() as session:
        document = session.get(Document, result.document_id)
        assert document is not None
        assert document.document_source == "manual_upload"
        assert document.uploaded_by == "Team Bid"
        assert document.status == "STORED"


def test_zip_upload_preserves_archive_and_records_supported_entries(
    intake: tuple[DocumentIntakeService, Database, Path],
    tmp_path: Path,
) -> None:
    service, _database, _root = intake
    source = tmp_path / "hsmt.zip"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("Ho-so/HSMT.pdf", b"pdf")
        archive.writestr("Ho-so/readme.txt", b"not extracted")
        archive.writestr("BOQ.xlsx", b"xlsx")
    original = source.read_bytes()

    result = service.intake_file(source)

    assert result.outcome == "IMPORTED"
    assert result.document_type == "ZIP"
    assert result.stored_path.read_bytes() == original
    assert result.discovered_files == ("Ho-so/HSMT.pdf", "BOQ.xlsx")
    assert not (result.stored_path.parent / "Ho-so").exists()


def test_duplicate_sha_reuses_record_and_physical_file(
    intake: tuple[DocumentIntakeService, Database, Path],
    tmp_path: Path,
) -> None:
    service, database, root = intake
    first_source = _write(tmp_path / "first.pdf", b"same bytes")
    second_source = _write(tmp_path / "second.pdf", b"same bytes")

    first = service.intake_file(first_source)
    duplicate = service.intake_file(second_source)

    assert duplicate.outcome == "DUPLICATE"
    assert duplicate.document_id == first.document_id
    assert duplicate.stored_path == first.stored_path
    assert duplicate.version == first.version
    with database.session() as session:
        assert session.scalar(select(func.count(Document.id))) == 1
    assert [path for path in root.rglob("*") if path.is_file()] == [first.stored_path]


def test_same_tender_changed_file_creates_new_version_without_overwrite(
    intake: tuple[DocumentIntakeService, Database, Path],
    tmp_path: Path,
) -> None:
    service, database, _root = intake
    with database.session() as session:
        tender = Notice(
            source_url="https://example.test/tender/1",
            url_hash="1" * 64,
            notice_code="IB2600000001-00",
            source_name="egp",
            title="Tender",
        )
        session.add(tender)
        session.flush()
        tender_id = tender.id
    first_source = _write(tmp_path / "hsmt-v1.pdf", b"version one")
    second_source = _write(tmp_path / "hsmt-v2.pdf", b"version two")

    first = service.intake_file(first_source, tender_reference="IB2600000001-00")
    second = service.intake_file(second_source, tender_reference="IB2600000001-00")

    assert (first.version, second.version) == (1, 2)
    assert first.tender_id == second.tender_id == tender_id
    assert first.tender_identifier == second.tender_identifier == "IB2600000001-00"
    assert first.stored_path != second.stored_path
    assert first.stored_path.read_bytes() == b"version one"
    assert second.stored_path.read_bytes() == b"version two"
    with database.session() as session:
        assert session.scalar(select(func.count(Document.id))) == 2


def test_folder_upload_imports_supported_files_only(
    intake: tuple[DocumentIntakeService, Database, Path],
    tmp_path: Path,
) -> None:
    service, _database, _root = intake
    folder = tmp_path / "HSMT"
    folder.mkdir()
    _write(folder / "a.pdf", b"a")
    _write(folder / "b.docx", b"b")
    _write(folder / "ignore.txt", b"ignore")

    batch = service.intake_path(folder)

    assert batch.imported == 2
    assert batch.duplicates == 0
    assert {item.original_filename for item in batch.results} == {"a.pdf", "b.docx"}


def test_filename_sanitization_is_windows_safe() -> None:
    assert sanitize_filename("CON.pdf") == "_CON.pdf"
    safe = sanitize_filename("../../HSMT: 2026?.PDF")
    assert safe.endswith(".pdf")
    assert not any(character in safe for character in "/\\:?")


def test_zip_path_traversal_is_blocked_before_storage(
    intake: tuple[DocumentIntakeService, Database, Path],
    tmp_path: Path,
) -> None:
    service, database, root = intake
    source = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("../escape.pdf", b"unsafe")

    with pytest.raises(DocumentValidationError, match="không an toàn"):
        service.intake_file(source)

    with database.session() as session:
        assert session.scalar(select(func.count(Document.id))) == 0
    assert not root.exists()


@pytest.mark.parametrize(
    ("filename", "content", "message"),
    [
        ("notes.txt", b"text", "PDF, DOCX, XLSX"),
        ("empty.pdf", b"", "file rỗng"),
    ],
)
def test_invalid_input_is_rejected_without_record(
    intake: tuple[DocumentIntakeService, Database, Path],
    tmp_path: Path,
    filename: str,
    content: bytes,
    message: str,
) -> None:
    service, database, root = intake
    source = _write(tmp_path / filename, content)

    with pytest.raises(DocumentValidationError, match=message):
        service.intake_file(source)

    with database.session() as session:
        assert session.scalar(select(func.count(Document.id))) == 0
    assert not root.exists()


def test_database_failure_cleans_stored_orphan(
    intake: tuple[DocumentIntakeService, Database, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, database, root = intake
    source = _write(tmp_path / "hsmt.pdf", b"will roll back")

    def fail_record(**_kwargs) -> Document:
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(service, "_create_record", fail_record)
    with pytest.raises(RuntimeError, match="database unavailable"):
        service.intake_file(source)

    with database.session() as session:
        assert session.scalar(select(func.count(Document.id))) == 0
    assert not [path for path in root.rglob("*") if path.is_file()]


def test_storage_failure_creates_no_database_record(
    tmp_path: Path,
) -> None:
    database = Database(f"sqlite:///{tmp_path / 'storage-failure.db'}")
    root_file = _write(tmp_path / "not-a-directory", b"occupied")
    service = DocumentIntakeService(database, root_file)
    source = _write(tmp_path / "hsmt.pdf", b"source")

    with pytest.raises(DocumentStorageError):
        service.intake_file(source)

    with database.session() as session:
        assert session.scalar(select(func.count(Document.id))) == 0


def test_audit_log_contains_safe_intake_stages(
    intake: tuple[DocumentIntakeService, Database, Path],
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    service, _database, _root = intake
    source = _write(tmp_path / "audit.pdf", b"SECRET_CONTENT_MARKER")

    with caplog.at_level(logging.INFO):
        service.intake_file(source)

    message = caplog.text
    for event in (
        "DOCUMENT_INTAKE_START",
        "HASH_DONE",
        "DUPLICATE_CHECK_DONE",
        "FILE_STORED",
        "DOCUMENT_RECORD_CREATED",
        "DOCUMENT_INTAKE_DONE",
    ):
        assert event in message
    assert "SECRET_CONTENT_MARKER" not in message
