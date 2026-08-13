from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest
from openpyxl import Workbook
from pypdf import PdfWriter
from sqlalchemy import select

from qi_crawler.db import Database
from qi_crawler.document_intake import DocumentIntakeService
from qi_crawler.models import DocumentEvidence, DocumentExtraction
from qi_crawler.native_extraction import NativeExtractionError, NativeHSMTExtractionService


@pytest.fixture
def services(tmp_path: Path) -> tuple[DocumentIntakeService, NativeHSMTExtractionService, Database]:
    database = Database(f"sqlite:///{tmp_path / 'extraction.db'}")
    return (
        DocumentIntakeService(database, tmp_path / "documents"),
        NativeHSMTExtractionService(database),
        database,
    )


def _pdf(path: Path) -> Path:
    writer = PdfWriter()
    writer.add_blank_page(width=144, height=144)
    with path.open("wb") as stream:
        writer.write(stream)
    return path


def _docx(path: Path) -> Path:
    document = """<?xml version="1.0" encoding="UTF-8"?>
    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>
      <w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Yêu cầu kỹ thuật</w:t></w:r></w:p>
      <w:p><w:r><w:t>Cáp quang</w:t></w:r></w:p>
      <w:tbl><w:tr><w:tc><w:p><w:r><w:t>Hạng mục</w:t></w:r></w:p></w:tc>
      <w:tc><w:p><w:r><w:t>Số lượng</w:t></w:r></w:p></w:tc></w:tr>
      <w:tr><w:tc><w:p><w:r><w:t>Router</w:t></w:r></w:p></w:tc>
      <w:tc><w:p><w:r><w:t>2</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
    </w:body></w:document>"""
    styles = """<?xml version="1.0" encoding="UTF-8"?>
    <w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
      <w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/></w:style>
    </w:styles>"""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", document)
        archive.writestr("word/styles.xml", styles)
    return path


def _xlsx(path: Path) -> Path:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "BOQ"
    worksheet.append(["Hạng mục", "Số lượng"])
    worksheet.append(["Switch", 3])
    workbook.save(path)
    return path


@pytest.mark.parametrize(
    ("filename", "create", "expected_locator"),
    [
        ("hsmt.pdf", _pdf, "page:1"),
        ("hsmt.docx", _docx, "word/document.xml:paragraph:1"),
        ("boq.xlsx", _xlsx, "sheet:BOQ!A1:B1"),
    ],
)
def test_native_extraction_preserves_source_trace(
    services: tuple[DocumentIntakeService, NativeHSMTExtractionService, Database],
    tmp_path: Path,
    filename: str,
    create,
    expected_locator: str,
) -> None:
    intake, extractor, database = services
    source = create(tmp_path / filename)
    original_bytes = source.read_bytes()
    document = intake.intake_file(source)

    result = extractor.extract_document(document.document_id)

    assert result.outcome == "EXTRACTED"
    assert result.evidence_count >= 1
    assert source.read_bytes() == original_bytes
    with database.session() as session:
        extraction = session.get(DocumentExtraction, result.extraction_id)
        evidence = list(
            session.scalars(
                select(DocumentEvidence)
                .where(DocumentEvidence.extraction_id == result.extraction_id)
                .order_by(DocumentEvidence.ordinal)
            )
        )
    assert extraction is not None
    assert json.loads(extraction.metadata_json or "{}") == {
        "file_format": result.file_format,
        "source_sha256": document.sha256,
    }
    assert evidence[0].source_locator == expected_locator


def test_docx_heading_and_table_cells_are_preserved(
    services: tuple[DocumentIntakeService, NativeHSMTExtractionService, Database], tmp_path: Path
) -> None:
    intake, extractor, database = services
    document = intake.intake_file(_docx(tmp_path / "hsmt.docx"))
    result = extractor.extract_document(document.document_id)

    with database.session() as session:
        evidence = list(
            session.scalars(
                select(DocumentEvidence)
                .where(DocumentEvidence.extraction_id == result.extraction_id)
                .order_by(DocumentEvidence.ordinal)
            )
        )
    table = next(item for item in evidence if item.content_type == "TABLE")
    assert evidence[0].section_heading == "Yêu cầu kỹ thuật"
    assert json.loads(table.table_json or "[]") == [
        ["Hạng mục", "Số lượng"],
        ["Router", "2"],
    ]


def test_repeat_extraction_is_idempotent(
    services: tuple[DocumentIntakeService, NativeHSMTExtractionService, Database], tmp_path: Path
) -> None:
    intake, extractor, _database = services
    document = intake.intake_file(_xlsx(tmp_path / "boq.xlsx"))

    first = extractor.extract_document(document.document_id)
    second = extractor.extract_document(document.document_id)

    assert second.outcome == "ALREADY_EXTRACTED"
    assert second.extraction_id == first.extraction_id
    assert second.evidence_count == first.evidence_count


def test_unsupported_format_is_rejected_without_creating_extraction(
    services: tuple[DocumentIntakeService, NativeHSMTExtractionService, Database], tmp_path: Path
) -> None:
    intake, extractor, database = services
    source = tmp_path / "archive.zip"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("hsmt.pdf", b"not extracted in WP2")
    document = intake.intake_file(source)

    with pytest.raises(NativeExtractionError, match="PDF, DOCX va XLSX"):
        extractor.extract_document(document.document_id)
    with database.session() as session:
        assert session.scalar(select(DocumentExtraction)) is None
