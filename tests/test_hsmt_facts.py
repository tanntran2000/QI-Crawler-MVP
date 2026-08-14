from __future__ import annotations

from hashlib import sha256

from sqlalchemy import select

from qi_crawler.db import Database
from qi_crawler.hsmt_facts import HSMTFactService
from qi_crawler.models import Document, DocumentEvidence, DocumentExtraction, HSMTFact, Notice


def _seed_evidence(database: Database, rows: list[str]) -> int:
    database.require_current_schema()
    with database.session() as session:
        notice = Notice(
            source_url="https://example.test/tender",
            url_hash=sha256(b"tender").hexdigest(),
            title="Goi thu nghiem",
        )
        session.add(notice)
        session.flush()
        document = Document(
            tender_id=notice.id,
            document_source="manual_upload",
            document_type="E_HSMT",
            file_format="PDF",
            classification_status="VERIFIED",
            original_filename="HSMT.pdf",
            stored_path="C:/safe/HSMT.pdf",
            mime_type="application/pdf",
            file_size=1,
            sha256="a" * 64,
        )
        session.add(document)
        session.flush()
        extraction = DocumentExtraction(
            document_id=document.id,
            extractor_version="native-v1",
            status="NATIVE_OK",
        )
        session.add(extraction)
        session.flush()
        for ordinal, text in enumerate(rows, start=1):
            session.add(
                DocumentEvidence(
                    extraction_id=extraction.id,
                    ordinal=ordinal,
                    source_locator=f"page:{ordinal}",
                    page_number=ordinal,
                    content_type="TABLE_ROW" if "|" in text else "TEXT",
                    text=text,
                    metadata_json='{"flags": ["NATIVE_OK"]}',
                )
            )
        return notice.id


def test_facts_are_created_from_persisted_evidence_with_lineage(tmp_path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'facts.db'}")
    tender_id = _seed_evidence(
        database,
        [
            "Tên gói thầu: Cung cấp hạ tầng mạng",
            "Dây mạng CAT6 | 14 | thùng | đồng 99,97%",
            "Thời gian thực hiện 120 ngày; cung cấp, lắp đặt, nghiệm thu, đào tạo, bảo hành.",
            "Yêu cầu catalogue, CO/CQ và xác nhận của hãng.",
        ],
    )

    service = HSMTFactService(database)
    service.refresh_tender(tender_id)
    facts = service.facts_for_tender(tender_id)

    assert any(item.fact_group == "BOM_SUPPLY" and "14 | thùng" in (item.value or "") for item in facts)
    assert any(item.fact_group == "CHAPTER_V_TECHNICAL" for item in facts)
    assert any(item.fact_key == "EXECUTION_PERIOD" for item in facts)
    assert all(item.source_locator or item.status != "FOUND" for item in facts)
    service.refresh_tender(tender_id)
    with database.session() as session:
        assert len(list(session.scalars(select(HSMTFact)))) == len(facts)


def test_missing_attachment_and_conflicting_schedule_are_flagged(tmp_path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'facts-conflict.db'}")
    tender_id = _seed_evidence(
        database,
        [
            "Thời gian thực hiện 30 ngày.",
            "Thời gian thực hiện 45 ngày; xem phụ lục đính kèm.",
        ],
    )

    service = HSMTFactService(database)
    service.refresh_tender(tender_id)
    facts = service.facts_for_tender(tender_id)

    assert any(item.status == "SOURCE_CONFLICT" for item in facts)
    assert any(item.status == "SOURCE_DOCUMENT_MISSING" for item in facts)
    assert any(
        item.fact_key == "SUPPLY_ITEM" and item.status == "NOT_FOUND_IN_AVAILABLE_SOURCES"
        for item in facts
    )
