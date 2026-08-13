from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from sqlalchemy import select

from qi_crawler.db import Database
from qi_crawler.document_intake import DocumentIntakeService
from qi_crawler.document_taxonomy import (
    TEMPLATE_REGISTRY,
    ClassificationStatus,
    DocumentClassificationError,
    DocumentClassificationService,
    TenderDocumentType,
    classify_document,
)
from qi_crawler.models import Document, Notice


@pytest.mark.parametrize(
    ("title", "expected_type"),
    [
        ("Hồ sơ mời thầu qua mạng", TenderDocumentType.E_HSMT),
        ("Yêu cầu kỹ thuật hệ thống", TenderDocumentType.TECHNICAL_REQUIREMENT),
        ("Văn bản sửa đổi số 01", TenderDocumentType.AMENDMENT),
    ],
)
def test_verified_metadata_produces_candidate_not_verified(
    title: str,
    expected_type: TenderDocumentType,
) -> None:
    result = classify_document(
        metadata_title=title,
        filename="neutral.pdf",
        identity_status="VERIFIED_LINKED",
    )

    assert result.document_type == expected_type
    assert result.status == ClassificationStatus.CANDIDATE


def test_boq_xlsx_is_candidate_from_filename_only() -> None:
    result = classify_document(
        metadata_title=None,
        filename="BOQ-goi-thau.xlsx",
        identity_status="VERIFIED_LINKED",
    )

    assert result.document_type == TenderDocumentType.BOQ_BOM
    assert result.status == ClassificationStatus.CANDIDATE
    assert result.status != ClassificationStatus.VERIFIED


def test_unknown_document_is_not_guessed() -> None:
    result = classify_document(
        metadata_title="Tài liệu nội bộ",
        filename="document.pdf",
        identity_status="VERIFIED_LINKED",
    )

    assert result.document_type == TenderDocumentType.OTHER
    assert result.status == ClassificationStatus.UNKNOWN


def test_ambiguous_signals_need_review() -> None:
    result = classify_document(
        metadata_title="Yêu cầu kỹ thuật kèm BOQ",
        filename="document.xlsx",
        identity_status="VERIFIED_LINKED",
    )

    assert result.document_type == TenderDocumentType.OTHER
    assert result.status == ClassificationStatus.NEEDS_REVIEW
    assert set(result.matched_types) == {
        TenderDocumentType.TECHNICAL_REQUIREMENT,
        TenderDocumentType.BOQ_BOM,
    }


def test_unverified_identity_never_creates_verified_or_candidate() -> None:
    result = classify_document(
        metadata_title="Hồ sơ mời thầu qua mạng",
        filename="E-HSMT.pdf",
        identity_status="UNLINKED",
    )

    assert result.document_type == TenderDocumentType.E_HSMT
    assert result.status == ClassificationStatus.NEEDS_REVIEW


def test_template_registry_contains_all_requested_families() -> None:
    assert tuple(TEMPLATE_REGISTRY) == (
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
        "11",
        "12",
        "13",
        "14",
    )


def _add_tender(database: Database, code: str) -> int:
    database.require_current_schema()
    source_url = f"https://example.test/egp/{code}"
    with database.session() as session:
        tender = Notice(
            source_url=source_url,
            url_hash=hashlib.sha256(source_url.encode()).hexdigest(),
            notice_code=code,
            source_name="egp",
            title=f"Tender {code}",
            contract_type="Hàng hóa",
            selection_method="Một giai đoạn một túi hồ sơ",
        )
        session.add(tender)
        session.flush()
        return tender.id


def test_intake_classifies_only_after_identity_guard_and_user_can_confirm(
    tmp_path: Path,
) -> None:
    database = Database(f"sqlite:///{tmp_path / 'taxonomy.db'}")
    tender_id = _add_tender(database, "IB2600001000-00")
    source = tmp_path / "neutral.pdf"
    source.write_bytes(b"E-HSMT")
    intake = DocumentIntakeService(database, tmp_path / "documents")

    result = intake.intake_file(
        source,
        tender_reference="IB2600001000-00",
        document_name="Hồ sơ mời thầu qua mạng",
    )

    assert result.tender_id == tender_id
    assert result.identity_status == "VERIFIED_LINKED"
    assert result.document_type == "E_HSMT"
    assert result.file_format == "PDF"
    assert result.classification_status == "CANDIDATE"
    assert result.package_type == "Hàng hóa"
    assert result.selection_method == "Một giai đoạn một túi hồ sơ"

    confirmed = DocumentClassificationService(database).confirm(
        result.document_id,
        "E_HSMT",
        template_code="4",
        package_type="Hàng hóa",
        selection_method="Một giai đoạn một túi hồ sơ",
    )

    assert confirmed.status == ClassificationStatus.VERIFIED
    with database.session() as session:
        document = session.get(Document, result.document_id)
        assert document is not None
        assert document.document_type == "E_HSMT"
        assert document.template_code == "4"
        assert document.classification_status == "VERIFIED"


def test_unlinked_document_cannot_be_human_verified_as_linked_taxonomy(
    tmp_path: Path,
) -> None:
    database = Database(f"sqlite:///{tmp_path / 'unlinked.db'}")
    source = tmp_path / "E-HSMT.pdf"
    source.write_bytes(b"unlinked")
    result = DocumentIntakeService(database, tmp_path / "documents").intake_file(source)

    with pytest.raises(DocumentClassificationError, match="Identity tender"):
        DocumentClassificationService(database).confirm(result.document_id, "E_HSMT")


def test_legacy_document_remains_readable_after_taxonomy_migration(
    tmp_path: Path,
) -> None:
    database = Database(f"sqlite:///{tmp_path / 'legacy-document.db'}")
    tender_id = _add_tender(database, "IB2600001001-00")
    stored = tmp_path / "legacy.pdf"
    stored.write_bytes(b"legacy")
    with database.session() as session:
        document = Document(
            tender_id=tender_id,
            document_source="manual_upload",
            document_type="OTHER",
            file_format="PDF",
            original_filename="legacy.pdf",
            stored_path=str(stored),
            mime_type="application/pdf",
            file_size=6,
            sha256=hashlib.sha256(b"legacy").hexdigest(),
            version=1,
            status="STORED",
            classification_status="UNKNOWN",
        )
        session.add(document)
        session.flush()
        document_id = document.id

    manifest = DocumentIntakeService(
        database,
        tmp_path / "documents",
    ).manifest_for_tender("IB2600001001-00")

    assert manifest.documents[0].document_id == document_id
    assert manifest.documents[0].file_format == "PDF"
    assert manifest.documents[0].document_type == "OTHER"
    assert manifest.documents[0].classification_status == "UNKNOWN"
    with database.session() as session:
        assert session.scalar(select(Document.sha256)) == hashlib.sha256(b"legacy").hexdigest()
