from __future__ import annotations

import logging
import zipfile
from hashlib import sha256
from pathlib import Path

import pytest
from openpyxl import Workbook
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
from sqlalchemy import func, select

import qi_crawler.document_intake as document_intake_module
from qi_crawler.config import AppConfig
from qi_crawler.db import Database
from qi_crawler.document_intake import (
    DocumentIdentityMismatch,
    DocumentIntakeService,
    extract_document_identity,
)
from qi_crawler.ground_truth import GroundTruthReviewService
from qi_crawler.gui_services import (
    run_create_manual_tender_workspace,
    run_document_extraction_inspection,
    run_document_intake,
)
from qi_crawler.manual_tender import (
    HUMAN_DECLARED,
    HUMAN_SHORTLISTED,
    MANUAL_TEAM_BID,
    ManualTenderWorkspaceError,
    ManualTenderWorkspaceService,
)
from qi_crawler.models import (
    Document,
    DocumentEvidence,
    DocumentExtraction,
    GroundTruthReview,
    Notice,
)
from qi_crawler.native_extraction import NativeHSMTExtractionService


@pytest.fixture
def services(tmp_path: Path):
    database = Database(f"sqlite:///{tmp_path / 'manual-workspace.db'}")
    workspace = ManualTenderWorkspaceService(database)
    intake = DocumentIntakeService(database, tmp_path / "documents")
    return database, workspace, intake


def _blank_pdf(path: Path) -> Path:
    writer = PdfWriter()
    writer.add_blank_page(width=144, height=144)
    with path.open("wb") as stream:
        writer.write(stream)
    return path


def _identity_pdf(path: Path, text: str) -> Path:
    writer = PdfWriter()
    page = writer.add_blank_page(width=144, height=144)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    font_ref = writer._add_object(font)
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref})}
    )
    contents = DecodedStreamObject()
    contents.set_data(f"BT /F1 12 Tf 12 72 Td ({text}) Tj ET".encode("latin-1"))
    page[NameObject("/Contents")] = writer._add_object(contents)
    with path.open("wb") as stream:
        writer.write(stream)
    return path


def _identity_docx(path: Path, text: str) -> Path:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "word/document.xml",
            f'''<?xml version="1.0" encoding="UTF-8"?>
            <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
              <w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body>
            </w:document>''',
        )
    return path


def _identity_xlsx(path: Path, text: str) -> Path:
    workbook = Workbook()
    workbook.active["A1"] = text
    workbook.save(path)
    workbook.close()
    return path


def test_manual_workspace_has_no_url_and_distinct_human_identity(services) -> None:
    database, workspace, intake = services

    created = workspace.create_workspace(
        "IB2500585490",
        package_name="Gói HSMT Team Bid",
        shortlisted=True,
        business_priority="HIGH",
        reviewed_by="Team Bid A",
        manual_note="Ưu tiên xử lý",
    )

    assert created.source_origin == MANUAL_TEAM_BID
    assert created.identity_status == HUMAN_DECLARED
    assert created.screening_status == HUMAN_SHORTLISTED
    assert created.business_priority == "HIGH"
    with database.session() as session:
        tender = session.get(Notice, created.tender_id)
    assert tender is not None
    assert tender.source_url is None
    assert tender.reviewed_at is not None
    assert tender.identity_status == HUMAN_DECLARED
    assert intake.manifest_for_tender("IB2500585490").identity_status == HUMAN_DECLARED


@pytest.mark.parametrize("filename", ["hsmt.pdf", "hsmt.docx", "boq.xlsx", "hsmt.zip"])
def test_manual_workspace_uses_existing_intake_for_all_supported_formats(
    services, tmp_path: Path, filename: str
) -> None:
    _database, workspace, intake = services
    workspace.create_workspace("IB2500585491")
    source = tmp_path / filename
    if source.suffix == ".zip":
        with zipfile.ZipFile(source, "w") as archive:
            archive.writestr("HSMT.pdf", b"pdf")
    else:
        source.write_bytes(b"%PDF" if source.suffix == ".pdf" else b"PK\x03\x04")

    result = intake.intake_file(source, tender_reference="IB2500585491")

    assert result.outcome == "IMPORTED"
    assert result.identity_status == HUMAN_DECLARED
    assert result.stored_path.parts[-4:-2] == ("team_bid", "IB2500585491")


def test_manual_identity_preserves_duplicate_version_and_cross_tender_guard(
    services, tmp_path: Path
) -> None:
    database, workspace, intake = services
    workspace.create_workspace("IB2500585492")
    workspace.create_workspace("IB2500585493")
    first = tmp_path / "first.pdf"
    first.write_bytes(b"version one")
    changed = tmp_path / "changed.pdf"
    changed.write_bytes(b"version two")

    initial = intake.intake_file(first, tender_reference="IB2500585492")
    duplicate = intake.intake_file(first, tender_reference="IB2500585492")
    version_two = intake.intake_file(changed, tender_reference="IB2500585492")
    with pytest.raises(DocumentIdentityMismatch):
        intake.intake_file(first, tender_reference="IB2500585493")

    assert duplicate.outcome == "DUPLICATE"
    assert (initial.version, version_two.version) == (1, 2)
    with database.session() as session:
        assert session.scalar(select(func.count(Document.id))) == 2


def test_manual_pdf_runs_native_extraction_without_ground_truth(services, tmp_path: Path) -> None:
    database, workspace, intake = services
    workspace.create_workspace("IB2500585494", shortlisted=True)
    imported = intake.intake_file(
        _blank_pdf(tmp_path / "Hồ sơ mời thầu_Bai2.pdf"),
        tender_reference="IB2500585494",
    )

    extraction = NativeHSMTExtractionService(database).extract_document(imported.document_id)
    GroundTruthReviewService(database)
    with database.session() as session:
        evidence = list(
            session.scalars(
                select(DocumentEvidence).where(DocumentEvidence.extraction_id == extraction.extraction_id)
            )
        )
        reviews = session.scalar(select(func.count(GroundTruthReview.id)))
    assert extraction.document_id == imported.document_id
    assert extraction.status == "NEEDS_REVIEW"
    assert evidence and evidence[0].source_locator == "page:1"
    assert reviews == 0


def test_manual_workspace_refuses_silent_web_identity_collision(services) -> None:
    database, workspace, _intake = services
    source_url = "https://example.test/IB2500585495"
    with database.session() as session:
        session.add(
            Notice(
                source_url=source_url,
                url_hash=sha256(source_url.encode()).hexdigest(),
                notice_code="IB2500585495",
                source_name="egp",
                title="Web tender",
            )
        )

    with pytest.raises(ManualTenderWorkspaceError, match="human review"):
        workspace.create_workspace("IB2500585495")


@pytest.mark.parametrize(
    ("filename", "writer", "locator"),
    [
        ("hsmt.pdf", _identity_pdf, "page:1"),
        ("hsmt.docx", _identity_docx, "word/document.xml"),
        ("hsmt.xlsx", _identity_xlsx, "sheet:Sheet"),
    ],
)
def test_content_identity_is_preserved_for_pdf_docx_and_xlsx(
    tmp_path: Path,
    filename: str,
    writer,
    locator: str,
) -> None:
    identity = extract_document_identity(
        writer(tmp_path / filename, "Tender IB2500585490-00")
    )

    assert identity.raw_notice_id == "IB2500585490-00"
    assert identity.base_notice_id == "IB2500585490"
    assert identity.revision == "00"
    assert identity.identity_source == "DOCUMENT_CONTENT"
    assert locator in (identity.evidence_locator or "")


def test_manual_workspace_content_same_tender_is_document_verified(
    services, tmp_path: Path
) -> None:
    _database, workspace, intake = services
    workspace.create_workspace("IB2500585490")

    result = intake.intake_file(
        _identity_pdf(tmp_path / "Hồ sơ mời thầu_Bai2.pdf", "IB2500585490-00"),
        tender_reference="IB2500585490",
    )

    assert result.identity_status == "DOCUMENT_VERIFIED"
    assert result.identity_match_status == "SAME_TENDER"
    assert result.raw_notice_id == "IB2500585490-00"
    assert result.base_notice_id == "IB2500585490"
    assert result.notice_revision == "00"


def test_verified_content_can_link_an_existing_unlinked_duplicate(
    services, tmp_path: Path
) -> None:
    database, workspace, intake = services
    source = _identity_pdf(tmp_path / "previously-unlinked.pdf", "IB2500585490-00")

    initial = intake.intake_file(source)
    workspace.create_workspace("IB2500585490")
    duplicate = intake.intake_file(source, tender_reference="IB2500585490")

    assert initial.identity_status == "UNLINKED"
    assert duplicate.outcome == "DUPLICATE"
    assert duplicate.identity_status == "DOCUMENT_VERIFIED"
    assert duplicate.identity_match_status == "SAME_TENDER"
    assert duplicate.base_notice_id == "IB2500585490"
    with database.session() as session:
        document = session.get(Document, duplicate.document_id)
        assert document is not None
        assert document.tender_id == duplicate.tender_id


def test_identity_backend_failure_is_needs_review_not_unlinked(
    services,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _database, workspace, intake = services
    workspace.create_workspace("IB2500585490")

    def fail_reader(_path: Path) -> list[tuple[str, str]]:
        raise RuntimeError("native backend unavailable")

    monkeypatch.setattr(document_intake_module, "_identity_content_regions", fail_reader)
    with caplog.at_level(logging.WARNING):
        result = intake.intake_file(
            _blank_pdf(tmp_path / "backend-failure.pdf"),
            tender_reference="IB2500585490",
        )

    assert result.identity_status == "NEEDS_REVIEW"
    assert result.identity_match_status == "EXTRACTION_FAILED"
    assert "IDENTITY_EXTRACTION_FAILED backend=pypdf file=backend-failure.pdf" in caplog.text


def test_manual_workspace_content_different_revision_keeps_version_lineage(
    services, tmp_path: Path
) -> None:
    _database, workspace, intake = services
    workspace.create_workspace("IB2500585491")

    first = intake.intake_file(
        _identity_pdf(tmp_path / "revision-00.pdf", "IB2500585491-00"),
        tender_reference="IB2500585491",
    )
    second = intake.intake_file(
        _identity_pdf(tmp_path / "revision-01.pdf", "IB2500585491-01"),
        tender_reference="IB2500585491",
    )

    assert first.identity_match_status == "SAME_TENDER"
    assert second.identity_match_status == "SAME_TENDER_DIFFERENT_REVISION"
    assert (first.version, second.version) == (1, 2)
    assert second.notice_revision == "01"


def test_content_mismatch_blocks_even_when_filename_matches_workspace(
    services, tmp_path: Path
) -> None:
    _database, workspace, intake = services
    workspace.create_workspace("IB2500585492")

    with pytest.raises(DocumentIdentityMismatch, match="CRITICAL_MISMATCH"):
        intake.intake_file(
            _identity_pdf(tmp_path / "IB2500585492.pdf", "IB2500999999-00"),
            tender_reference="IB2500585492",
        )


def test_manual_workspace_without_content_identity_allows_needs_review(
    services, tmp_path: Path
) -> None:
    _database, workspace, intake = services
    workspace.create_workspace("IB2500585493")

    result = intake.intake_file(
        _blank_pdf(tmp_path / "no-identity.pdf"),
        tender_reference="IB2500585493",
    )

    assert result.identity_status == HUMAN_DECLARED
    assert result.identity_match_status == "NO_CONTENT_ID"


def test_conflicting_content_identity_is_needs_review_without_guessing(
    services, tmp_path: Path
) -> None:
    _database, workspace, intake = services
    workspace.create_workspace("IB2500585494")

    result = intake.intake_file(
        _identity_pdf(
            tmp_path / "conflicting.pdf",
            "IB2500585494-00 và IB2500999999-00",
        ),
        tender_reference="IB2500585494",
    )

    assert result.identity_status == "NEEDS_REVIEW"
    assert result.identity_match_status == "AMBIGUOUS"


def test_gui_service_manual_workspace_reuses_intake_and_native_extraction(
    tmp_path: Path,
) -> None:
    config = AppConfig()
    config.storage.database_url = f"sqlite:///{tmp_path / 'manual-gui.db'}"
    config.storage.document_dir = tmp_path / "documents"

    manifest = run_create_manual_tender_workspace(
        config,
        "IB2500585496",
        "Gói do Team Bid cung cấp",
        True,
        "HIGH",
        "Team Bid A",
        "",
    )
    result = run_document_intake(
        config,
        _blank_pdf(tmp_path / "manual.pdf"),
        tender_reference=manifest.tender_identifier,
    )

    assert result.imported == 1
    assert result.results[0].identity_status == HUMAN_DECLARED
    database = Database(config.storage.database_url)
    with database.session() as session:
        evidence_count = session.scalar(select(func.count(DocumentEvidence.id)))
        review_count = session.scalar(select(func.count(GroundTruthReview.id)))
    assert evidence_count == 1
    assert review_count == 0


def test_gui_service_extracts_a_relinked_duplicate_when_evidence_is_missing(
    tmp_path: Path,
) -> None:
    config = AppConfig()
    config.storage.database_url = f"sqlite:///{tmp_path / 'relinked-gui.db'}"
    config.storage.document_dir = tmp_path / "documents"
    source = _identity_pdf(tmp_path / "hsmt.pdf", "IB2500585490-00")

    run_create_manual_tender_workspace(
        config,
        "IB2500585490",
        "Goi Team Bid",
        False,
        "NORMAL",
        "",
        "",
    )
    database = Database(config.storage.database_url)
    initial = DocumentIntakeService(database, config.storage.document_dir).intake_file(source)
    relinked = run_document_intake(config, source, tender_reference="IB2500585490")

    assert initial.identity_status == "UNLINKED"
    assert relinked.results[0].outcome == "DUPLICATE"
    with database.session() as session:
        assert session.scalar(select(func.count(DocumentExtraction.id))) == 1
        assert session.scalar(select(func.count(DocumentEvidence.id))) == 1

    inspection = run_document_extraction_inspection(config, relinked.results[0].document_id)
    assert inspection.status == "NATIVE_OK"
    assert inspection.page_count == 1
    assert inspection.evidence_count == 1
