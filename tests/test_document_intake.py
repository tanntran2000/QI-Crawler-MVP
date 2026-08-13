from __future__ import annotations

import hashlib
import logging
import zipfile
from pathlib import Path

import pytest
from sqlalchemy import func, select

from qi_crawler.db import Database
from qi_crawler.document_intake import (
    DocumentIdentityMismatch,
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


def _add_tender(
    database: Database,
    code: str,
    *,
    source: str = "egp",
    source_notice_id: str | None = None,
) -> int:
    source_url = f"https://example.test/{source}/{code}"
    with database.session() as session:
        tender = Notice(
            source_url=source_url,
            url_hash=hashlib.sha256(source_url.encode()).hexdigest(),
            notice_code=code,
            source_notice_id=source_notice_id,
            source_name=source,
            title=f"Tender {code}",
        )
        session.add(tender)
        session.flush()
        return tender.id


@pytest.mark.parametrize(
    ("filename", "content", "file_format"),
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
    file_format: str,
) -> None:
    service, database, root = intake
    source = _write(tmp_path / filename, content)

    result = service.intake_file(source, uploaded_by="Team Bid")

    assert result.outcome == "IMPORTED"
    assert result.document_type == "OTHER"
    assert result.file_format == file_format
    assert result.classification_status in {"UNKNOWN", "NEEDS_REVIEW"}
    assert result.file_size == len(content)
    assert result.sha256 == hashlib.sha256(content).hexdigest()
    assert result.stored_path.read_bytes() == content
    assert result.stored_path.is_relative_to(root.resolve())
    with database.session() as session:
        document = session.get(Document, result.document_id)
        assert document is not None
        assert document.document_source == "manual_upload"
        assert document.uploaded_by == "Team Bid"
        assert document.status == "UNLINKED"


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
    assert result.document_type == "OTHER"
    assert result.file_format == "ZIP"
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
    tender_id = _add_tender(database, "IB2600000001-00")
    first_source = _write(tmp_path / "hsmt-v1.pdf", b"version one")
    second_source = _write(tmp_path / "hsmt-v2.pdf", b"version two")

    first = service.intake_file(first_source, tender_reference="IB2600000001-00")
    second = service.intake_file(second_source, tender_reference="IB2600000001-00")

    assert (first.version, second.version) == (1, 2)
    assert first.tender_id == second.tender_id == tender_id
    assert first.tender_identifier == second.tender_identifier == "IB2600000001-00"
    assert first.identity_status == second.identity_status == "VERIFIED_LINKED"
    assert first.stored_path != second.stored_path
    assert first.stored_path.read_bytes() == b"version one"
    assert second.stored_path.read_bytes() == b"version two"
    with database.session() as session:
        assert session.scalar(select(func.count(Document.id))) == 2


def test_correct_tender_link_and_storage_are_identity_isolated(
    intake: tuple[DocumentIntakeService, Database, Path],
    tmp_path: Path,
) -> None:
    service, database, root = intake
    tender_id = _add_tender(database, "IB2600000010-00", source="egp")
    source = _write(tmp_path / "HSMT.pdf", b"verified tender document")

    result = service.intake_file(source, tender_reference="IB2600000010-00")

    assert result.identity_status == "VERIFIED_LINKED"
    assert result.tender_id == tender_id
    assert result.tender_identifier == "IB2600000010-00"
    relative = result.stored_path.relative_to(root.resolve())
    assert relative.parts[:2] == ("egp", "IB2600000010-00")


def test_exact_source_url_is_trusted_identity_evidence(
    intake: tuple[DocumentIntakeService, Database, Path],
    tmp_path: Path,
) -> None:
    service, database, _root = intake
    tender_id = _add_tender(database, "IB2600000010-01", source="egp")
    source_url = "https://example.test/egp/IB2600000010-01"
    source = _write(tmp_path / "downloaded.pdf", b"trusted source URL")

    result = service.intake_file(
        source,
        document_source="web",
        source_url=source_url,
    )

    assert result.tender_id == tender_id
    assert result.identity_status == "VERIFIED_LINKED"
    assert result.detected_identity == "IB2600000010-01"


def test_same_file_same_tender_is_exact_duplicate(
    intake: tuple[DocumentIntakeService, Database, Path],
    tmp_path: Path,
) -> None:
    service, database, _root = intake
    _add_tender(database, "IB2600000011-00")
    source = _write(tmp_path / "same.pdf", b"exact")

    first = service.intake_file(source, tender_reference="IB2600000011-00")
    duplicate = service.intake_file(source, tender_reference="IB2600000011-00")

    assert duplicate.outcome == "DUPLICATE"
    assert duplicate.document_id == first.document_id
    assert duplicate.identity_status == "VERIFIED_LINKED"


def test_same_filename_different_tender_is_not_same_document(
    intake: tuple[DocumentIntakeService, Database, Path],
    tmp_path: Path,
) -> None:
    service, database, _root = intake
    tender_a = _add_tender(database, "IB2600000012-00")
    tender_b = _add_tender(database, "IB2600000013-00")
    folder_a = tmp_path / "a"
    folder_b = tmp_path / "b"
    folder_a.mkdir()
    folder_b.mkdir()
    source_a = _write(folder_a / "HSMT.pdf", b"tender A")
    source_b = _write(folder_b / "HSMT.pdf", b"tender B")

    first = service.intake_file(source_a, tender_reference="IB2600000012-00")
    second = service.intake_file(source_b, tender_reference="IB2600000013-00")

    assert first.original_filename == second.original_filename
    assert first.sha256 != second.sha256
    assert first.tender_id == tender_a
    assert second.tender_id == tender_b
    assert first.stored_path != second.stored_path


def test_mismatched_detected_tender_is_rejected_before_storage(
    intake: tuple[DocumentIntakeService, Database, Path],
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    service, database, root = intake
    _add_tender(database, "IB2600000014-00")
    _add_tender(database, "IB2600000015-00")
    source = _write(tmp_path / "mismatch.pdf", b"mismatch")

    with (
        caplog.at_level(logging.INFO),
        pytest.raises(DocumentIdentityMismatch, match="CRITICAL_MISMATCH") as caught,
    ):
        service.intake_file(
            source,
            tender_reference="IB2600000014-00",
            detected_tender_reference="IB2600000015-00",
        )

    assert caught.value.expected == "IB2600000014-00"
    assert caught.value.detected == "IB2600000015-00"
    with database.session() as session:
        assert session.scalar(select(func.count(Document.id))) == 0
    assert not root.exists()
    assert "DOCUMENT_IDENTITY_CHECK" in caplog.text
    assert "DOCUMENT_IDENTITY_MISMATCH" in caplog.text


def test_unlinked_and_unknown_tender_are_never_guessed(
    intake: tuple[DocumentIntakeService, Database, Path],
    tmp_path: Path,
) -> None:
    service, _database, _root = intake
    unlinked = service.intake_file(_write(tmp_path / "unlinked.pdf", b"unlinked"))
    unknown = service.intake_file(
        _write(tmp_path / "unknown.pdf", b"unknown"),
        tender_reference="IB-NOT-IN-DATABASE",
    )

    assert unlinked.tender_id is None
    assert unlinked.identity_status == "UNLINKED"
    assert unknown.tender_id is None
    assert unknown.identity_status == "NEEDS_REVIEW"
    assert unknown.expected_identity == "IB-NOT-IN-DATABASE"


def test_exact_duplicate_cannot_reassign_linked_document(
    intake: tuple[DocumentIntakeService, Database, Path],
    tmp_path: Path,
) -> None:
    service, database, _root = intake
    tender_a = _add_tender(database, "IB2600000016-00")
    _add_tender(database, "IB2600000017-00")
    source = _write(tmp_path / "immutable.pdf", b"one immutable document")
    first = service.intake_file(source, tender_reference="IB2600000016-00")

    with pytest.raises(DocumentIdentityMismatch):
        service.intake_file(source, tender_reference="IB2600000017-00")

    with database.session() as session:
        documents = tuple(session.scalars(select(Document)))
    assert len(documents) == 1
    assert documents[0].id == first.document_id
    assert documents[0].tender_id == tender_a


def test_manifest_is_database_backed_and_normalizes_legacy_wp1_status(
    intake: tuple[DocumentIntakeService, Database, Path],
    tmp_path: Path,
) -> None:
    service, database, root = intake
    tender_id = _add_tender(database, "IB2600000018-00", source="egp")
    first = service.intake_file(
        _write(tmp_path / "v1.pdf", b"v1"),
        tender_reference="IB2600000018-00",
    )
    legacy_bytes = b"legacy WP1"
    legacy_sha = hashlib.sha256(legacy_bytes).hexdigest()
    legacy_path = root / "IB2600000018-00" / legacy_sha / "legacy.pdf"
    legacy_path.parent.mkdir(parents=True)
    legacy_path.write_bytes(legacy_bytes)
    with database.session() as session:
        session.add(
            Document(
                tender_id=tender_id,
                document_source="manual_upload",
                document_type="PDF",
                original_filename="legacy.pdf",
                stored_path=str(legacy_path),
                mime_type="application/pdf",
                file_size=len(legacy_bytes),
                sha256=legacy_sha,
                version=2,
                status="STORED",
            )
        )

    manifest = service.manifest_for_tender("IB2600000018-00")

    assert manifest.tender_id == tender_id
    assert manifest.tender_identifier == "IB2600000018-00"
    assert manifest.source == "egp"
    assert [item.version for item in manifest.documents] == [1, 2]
    assert manifest.documents[0].document_id == first.document_id
    assert manifest.documents[1].filename == "legacy.pdf"
    assert manifest.documents[1].stored_path.read_bytes() == legacy_bytes
    assert {item.status for item in manifest.documents} == {"VERIFIED_LINKED"}
    assert {item.source for item in manifest.documents} == {"manual_upload"}
    assert all(item.uploaded_at is not None for item in manifest.documents)


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
        "DOCUMENT_IDENTITY_CHECK",
        "DOCUMENT_IDENTITY_UNLINKED",
        "DUPLICATE_CHECK_DONE",
        "FILE_STORED",
        "DOCUMENT_RECORD_CREATED",
        "DOCUMENT_INTAKE_DONE",
    ):
        assert event in message
    assert "SECRET_CONTENT_MARKER" not in message
