from __future__ import annotations

import json
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
            "Chào hàng cạnh tranh trong nước; Một giai đoạn một túi hồ sơ; Trọn gói.",
            "Dây mạng CAT6 | 14 | thùng | đồng 99,97%",
            "Thời gian thực hiện 120 ngày; cung cấp, lắp đặt, nghiệm thu, đào tạo, bảo hành.",
            "Yêu cầu catalogue, CO/CQ và xác nhận của hãng.",
        ],
    )

    service = HSMTFactService(database)
    service.refresh_tender(tender_id)
    facts = service.facts_for_tender(tender_id)

    assert any(item.fact_group == "BOM_SUPPLY" and "14 thùng" in (item.value or "") for item in facts)
    assert any(item.fact_key == "ITEM_TECHNICAL_SPEC" for item in facts)
    assert any(item.fact_key == "EXECUTION_PERIOD" for item in facts)
    assert {item.value for item in facts if item.fact_key == "SELECTION_METHOD"} == {"Chào hàng cạnh tranh trong nước"}
    assert {item.value for item in facts if item.fact_key == "SELECTION_PROCEDURE"} == {"Một giai đoạn một túi hồ sơ"}
    assert {item.value for item in facts if item.fact_key == "CONTRACT_TYPE"} == {"Trọn gói"}
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
        item.fact_key == "SUPPLY_REQUIREMENT" and item.status == "NOT_FOUND_IN_AVAILABLE_SOURCES"
        for item in facts
    )


def test_keyword_candidate_without_validated_parser_is_not_persisted(tmp_path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'facts-generic.db'}")
    tender_id = _seed_evidence(
        database,
        ["Yêu cầu kỹ thuật và tiêu chuẩn chung được nêu trong hồ sơ."],
    )

    service = HSMTFactService(database)
    service.refresh_tender(tender_id)
    facts = service.facts_for_tender(tender_id)

    assert not any(item.fact_key == "TECHNICAL_REQUIREMENT" for item in facts)
    assert not any(item.status == "FOUND" and "tiêu chuẩn chung" in (item.value or "") for item in facts)


def test_supply_requirement_preserves_source_notation_and_item_linked_spec(tmp_path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'facts-supply.db'}")
    tender_id = _seed_evidence(
        database,
        ["Cáp CAT6 | 14 | thùng | 40×60; 99,97%; 0,530 ± 0,005 mm; ≥176 Gbps; 305 ± 1,5 m"],
    )

    service = HSMTFactService(database)
    service.refresh_tender(tender_id)
    facts = service.facts_for_tender(tender_id)

    supply = next(item for item in facts if item.fact_key == "SUPPLY_REQUIREMENT")
    spec = next(item for item in facts if item.fact_key == "ITEM_TECHNICAL_SPEC")
    expected = "40×60; 99,97%; 0,530 ± 0,005 mm; ≥176 Gbps; 305 ± 1,5 m"
    assert supply.value == f"Cáp CAT6 — 14 thùng — {expected}"
    assert spec.value == f"Cáp CAT6 — {expected}"
    assert "4.270" not in supply.value


def test_schedule_and_work_scope_are_concise_and_deduplicated(tmp_path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'facts-schedule.db'}")
    tender_id = _seed_evidence(
        database,
        [
            "Thời gian thực hiện: 120 ngày. Phạm vi công việc: Cung cấp, lắp đặt, cấu hình, tích hợp, kiểm thử, bàn giao.",
            "Phạm vi công việc: Cung cấp, lắp đặt, cấu hình, tích hợp, kiểm thử, bàn giao.",
        ],
    )

    service = HSMTFactService(database)
    service.refresh_tender(tender_id)
    facts = service.facts_for_tender(tender_id)

    assert [item.value for item in facts if item.fact_key == "EXECUTION_PERIOD"] == ["120 ngày"]
    assert [item.value for item in facts if item.fact_key == "WORK_SCOPE"] == [
        "CUNG CẤP; LẮP ĐẶT; CẤU HÌNH; TÍCH HỢP; KIỂM THỬ; BÀN GIAO"
    ]


def test_structured_list_supply_fallback_is_validated_before_persisting(tmp_path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'facts-list.db'}")
    tender_id = _seed_evidence(database, ["Yêu cầu kỹ thuật\n- Bộ phát Wi-Fi: 01 bộ; bảo hành 36 tháng"])
    service = HSMTFactService(database)
    service.refresh_tender(tender_id)

    facts = service.facts_for_tender(tender_id)
    assert any(item.value == "Bộ phát Wi-Fi — 01 bộ — bảo hành 36 tháng" for item in facts)


def test_multiline_supply_and_item_linked_spec_are_extracted_once(tmp_path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'facts-multiline.db'}")
    tender_id = _seed_evidence(
        database,
        [
            "Yêu cầu kỹ thuật\nMáy chủ\n01 bộ\nCPU ≥ 176 Gbps; kích thước 40×60 mm",
            "Yêu cầu kỹ thuật\nMáy chủ\n01 bộ\nCPU ≥ 176 Gbps; kích thước 40×60 mm",
        ],
    )
    service = HSMTFactService(database)
    service.refresh_tender(tender_id)

    facts = service.facts_for_tender(tender_id)
    assert [item.value for item in facts if item.fact_key == "SUPPLY_REQUIREMENT"] == ["Máy chủ — 01 bộ — CPU ≥ 176 Gbps; kích thước 40×60 mm"]
    assert [item.value for item in facts if item.fact_key == "ITEM_TECHNICAL_SPEC"] == ["Máy chủ — CPU ≥ 176 Gbps; kích thước 40×60 mm"]
    with database.session() as session:
        supply = session.scalar(select(HSMTFact).where(HSMTFact.fact_key == "SUPPLY_REQUIREMENT"))
        assert len(json.loads(supply.metadata_json or "{}")["evidence_references"]) == 1


def test_case_insensitive_semantic_dedup_and_uncertain_supply_status(tmp_path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'facts-dedup.db'}")
    tender_id = _seed_evidence(database, ["Trọn gói", "trọn gói", "Yêu cầu kỹ thuật\n01 bộ"])
    service = HSMTFactService(database)
    service.refresh_tender(tender_id)

    facts = service.facts_for_tender(tender_id)
    assert len([item for item in facts if item.fact_key == "CONTRACT_TYPE"]) == 1
    assert any(item.fact_key == "SUPPLY_REQUIREMENT_UNCERTAIN" and item.status == "NEEDS_REVIEW" for item in facts)
    assert not any(item.fact_key == "SUPPLY_REQUIREMENT" and item.status == "NOT_FOUND_IN_AVAILABLE_SOURCES" for item in facts)


def test_non_technical_quantity_does_not_become_supply_requirement(tmp_path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'facts-noise.db'}")
    tender_id = _seed_evidence(database, ["Thời hạn bảo hành 01 năm; số lượng hộp hồ sơ: 328.500 hộp."])

    service = HSMTFactService(database)
    service.refresh_tender(tender_id)

    facts = service.facts_for_tender(tender_id)
    assert not any(item.fact_key == "SUPPLY_REQUIREMENT" and item.status == "FOUND" for item in facts)


def test_illustrative_technical_example_does_not_create_review_warning(tmp_path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'facts-example.db'}")
    tender_id = _seed_evidence(
        database,
        ["Ví dụ: phạm vi cung cấp gồm 20 máy tính và 20 máy in để minh họa hợp đồng tương tự."],
    )

    service = HSMTFactService(database)
    service.refresh_tender(tender_id)

    facts = service.facts_for_tender(tender_id)
    assert not any(item.fact_key == "SUPPLY_REQUIREMENT_UNCERTAIN" for item in facts)


def test_missing_referenced_technical_document_is_needs_review_not_not_found(tmp_path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'facts-technical-reference.db'}")
    tender_id = _seed_evidence(database, ["Yêu cầu về kỹ thuật: Chương V Yêu cầu kỹ thuật.docx"])

    service = HSMTFactService(database)
    service.refresh_tender(tender_id)

    facts = service.facts_for_tender(tender_id)
    reference = next(item for item in facts if item.fact_key == "TECHNICAL_SOURCE_DOCUMENT")
    assert reference.status == "SOURCE_DOCUMENT_MISSING"
    assert not any(item.fact_key == "SUPPLY_REQUIREMENT" and item.status == "NOT_FOUND_IN_AVAILABLE_SOURCES" for item in facts)


def test_package_purpose_formatting_variants_share_one_business_fact(tmp_path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'facts-purpose.db'}")
    tender_id = _seed_evidence(
        database,
        [
            "Tên gói thầu 01.MSTB: Mua sắm trang thiết bị thiết yếu phục vụ khám chữa bệnh",
            "Mục đích gói thầu: Mua sắm trang thiết bị thiết yếu phục vụ khám chữa bệnh",
        ],
    )

    service = HSMTFactService(database)
    service.refresh_tender(tender_id)

    facts = service.facts_for_tender(tender_id)
    purposes = [item for item in facts if item.fact_key == "PACKAGE_PURPOSE"]
    assert [item.value for item in purposes] == ["Mua sắm trang thiết bị thiết yếu phục vụ khám chữa bệnh"]


def test_layout_supply_rows_and_delivery_milestone_are_parsed_without_calculation(tmp_path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'facts-layout.db'}")
    tender_id = _seed_evidence(
        database,
        [
            (
                "Danh mục hàng hóa\nNgày giao hàng muộn nhất\n"
                "1 Máy chủ\nBộ 1 Theo quy định tại Chương V\n10 ngày 120 ngày"
            )
        ],
    )

    service = HSMTFactService(database)
    service.refresh_tender(tender_id)

    facts = service.facts_for_tender(tender_id)
    assert any(item.value == "Máy chủ — 1 Bộ" for item in facts if item.fact_key == "SUPPLY_REQUIREMENT")
    assert [item.value for item in facts if item.fact_key == "EXECUTION_PERIOD"] == ["120 ngày"]


def test_contract_boilerplate_does_not_become_work_scope(tmp_path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'facts-contract-boilerplate.db'}")
    tender_id = _seed_evidence(
        database,
        ["Sửa đổi hợp đồng trong phạm vi công việc của hợp đồng: cung cấp, vận chuyển và cấu hình."],
    )

    service = HSMTFactService(database)
    service.refresh_tender(tender_id)

    facts = service.facts_for_tender(tender_id)
    assert not any(item.fact_key == "WORK_SCOPE" and item.status == "FOUND" for item in facts)
