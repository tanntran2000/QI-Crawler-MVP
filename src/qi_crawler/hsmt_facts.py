"""Small deterministic fact layer over persisted native HSMT evidence."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from hashlib import sha256

from sqlalchemy import select

from .db import Database
from .models import Document, DocumentEvidence, DocumentExtraction, HSMTFact

PACKAGE_OVERVIEW = "PACKAGE_OVERVIEW"
CHAPTER_III_EVALUATION = "CHAPTER_III_EVALUATION"
CHAPTER_V_TECHNICAL = "CHAPTER_V_TECHNICAL"
BOM_SUPPLY = "BOM_SUPPLY"
SCHEDULE_SOW = "SCHEDULE_SOW"
REQUIRED_DOCUMENTS = "REQUIRED_DOCUMENTS"
MISSING_INFORMATION = "MISSING_INFORMATION"

FACT_GROUPS = (
    PACKAGE_OVERVIEW,
    CHAPTER_III_EVALUATION,
    CHAPTER_V_TECHNICAL,
    BOM_SUPPLY,
    SCHEDULE_SOW,
    REQUIRED_DOCUMENTS,
    MISSING_INFORMATION,
)


@dataclass(frozen=True)
class HSMTFactView:
    id: int
    fact_group: str
    fact_key: str
    value: str | None
    status: str
    filename: str | None
    source_locator: str | None
    raw_evidence_text: str | None


class HSMTFactService:
    """Derive retrieval-backed facts without conclusions, scoring, or file mutation."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def refresh_tender(self, tender_id: int) -> None:
        """Persist missing facts from existing evidence only; never runs extraction."""
        self.database.require_current_schema()
        with self.database.session() as session:
            rows = list(
                session.execute(
                    select(Document, DocumentEvidence)
                    .join(DocumentExtraction, DocumentExtraction.document_id == Document.id)
                    .join(DocumentEvidence, DocumentEvidence.extraction_id == DocumentExtraction.id)
                    .where(Document.tender_id == tender_id)
                    .order_by(Document.id, DocumentEvidence.ordinal)
                )
            )
            candidates = [fact for document, evidence in rows for fact in _facts_from_evidence(document, evidence)]
            for group, key in ((SCHEDULE_SOW, "EXECUTION_PERIOD"),):
                values = {
                    item.normalized_value
                    for item in candidates
                    if item.fact_group == group and item.fact_key == key
                }
                if len(values) > 1:
                    for item in candidates:
                        if item.fact_group == group and item.fact_key == key:
                            item.status = "SOURCE_CONFLICT"
            present = {(item.fact_group, item.fact_key) for item in candidates}
            for group, key in ((PACKAGE_OVERVIEW, "PACKAGE_PURPOSE"), (SCHEDULE_SOW, "EXECUTION_PERIOD"), (BOM_SUPPLY, "SUPPLY_ITEM")):
                if (group, key) not in present:
                    candidates.append(_missing_fact(tender_id, group, key))
            for fact in candidates:
                if session.scalar(select(HSMTFact.id).where(HSMTFact.fingerprint == fact.fingerprint)) is None:
                    session.add(fact)

    def facts_for_tender(self, tender_id: int) -> tuple[HSMTFactView, ...]:
        self.database.require_current_schema()
        with self.database.session() as session:
            rows = session.execute(
                select(HSMTFact, Document.original_filename)
                .outerjoin(Document, Document.id == HSMTFact.document_id)
                .where(HSMTFact.tender_id == tender_id)
                .order_by(HSMTFact.fact_group, HSMTFact.id)
            )
            return tuple(
                HSMTFactView(
                    id=fact.id,
                    fact_group=fact.fact_group,
                    fact_key=fact.fact_key,
                    value=fact.normalized_value,
                    status=fact.status,
                    filename=filename,
                    source_locator=fact.source_locator,
                    raw_evidence_text=fact.raw_evidence_text,
                )
                for fact, filename in rows
            )


def _facts_from_evidence(document: Document, evidence: DocumentEvidence) -> list[HSMTFact]:
    text = (evidence.text or "").strip()
    lowered = text.casefold()
    output: list[HSMTFact] = []
    def add(group: str, key: str, value: str | None = None) -> None:
        output.append(_fact(document, evidence, group, key, value or text))

    if any(token in lowered for token in ("tên gói", "mục tiêu", "phạm vi gói")):
        add(PACKAGE_OVERVIEW, "PACKAGE_PURPOSE")
    if "giá gói thầu" in lowered:
        add(PACKAGE_OVERVIEW, "PACKAGE_VALUE")
    if any(token in lowered for token in ("hình thức lựa chọn", "phương thức lựa chọn", "loại hợp đồng")):
        add(PACKAGE_OVERVIEW, "PROCUREMENT_METHOD")
    if any(token in lowered for token in ("tiêu chuẩn đánh giá", "năng lực", "kinh nghiệm", "bảo hành", "tiến độ")):
        add(CHAPTER_III_EVALUATION, "EVALUATION_CRITERION")
    if any(token in lowered for token in ("yêu cầu kỹ thuật", "thông số", "tiêu chuẩn", "vật liệu", "thiết bị")):
        add(CHAPTER_V_TECHNICAL, "TECHNICAL_REQUIREMENT")
    if any(token in lowered for token in ("ngày", "tháng", "thời gian thực hiện", "thời gian giao hàng")) and re.search(r"\d+\s*(ngày|tháng)", lowered):
        add(SCHEDULE_SOW, "EXECUTION_PERIOD")
    for token, key in (("cung cấp", "SUPPLY"), ("lắp đặt", "INSTALL"), ("cấu hình", "CONFIGURE"), ("nghiệm thu", "HANDOVER"), ("đào tạo", "TRAINING"), ("bảo hành", "WARRANTY_SERVICE")):
        if token in lowered:
            add(SCHEDULE_SOW, key)
    for token, key in (("catalogue", "CATALOGUE"), ("co/cq", "CO_CQ"), ("xác nhận của hãng", "MANUFACTURER_CONFIRMATION"), ("bản dịch", "TRANSLATION"), ("cam kết", "COMPLIANCE_DECLARATION")):
        if token in lowered:
            add(REQUIRED_DOCUMENTS, key)
    if evidence.content_type in {"TABLE", "TABLE_ROW"}:
        match = re.match(r"\s*(.+?)\s*\|\s*(\d+(?:[.,]\d+)?)\s*\|\s*([^|]+)", text)
        if match:
            add(BOM_SUPPLY, "SUPPLY_ITEM", " | ".join(match.groups()))
        if any(token in lowered for token in ("spec", "cat6", "đồng", "vật liệu")):
            add(CHAPTER_V_TECHNICAL, "MATERIAL_SPEC")
    if any(token in lowered for token in ("phụ lục", "đính kèm")):
        output.append(
            _fact(
                document,
                evidence,
                MISSING_INFORMATION,
                "REFERENCED_ATTACHMENT",
                "Tài liệu có tham chiếu phụ lục/đính kèm; cần kiểm tra bộ tài liệu.",
                status="SOURCE_DOCUMENT_MISSING",
            )
        )
    return output


def _fact(
    document: Document,
    evidence: DocumentEvidence,
    group: str,
    key: str,
    value: str,
    *,
    status: str = "FOUND",
) -> HSMTFact:
    fingerprint = sha256(f"{document.tender_id}|{evidence.id}|{group}|{key}|{value}".encode()).hexdigest()
    return HSMTFact(
        tender_id=document.tender_id,
        document_id=document.id,
        evidence_id=evidence.id,
        fact_group=group,
        fact_key=key,
        normalized_value=value,
        raw_evidence_text=evidence.text,
        status=status,
        source_locator=evidence.source_locator,
        metadata_json=json.dumps({"page": evidence.page_number, "sheet": evidence.sheet_name}, ensure_ascii=False),
        fingerprint=fingerprint,
    )


def _missing_fact(tender_id: int, group: str, key: str) -> HSMTFact:
    fingerprint = sha256(f"{tender_id}|{group}|{key}|NOT_FOUND".encode()).hexdigest()
    return HSMTFact(
        tender_id=tender_id,
        document_id=None,
        evidence_id=None,
        fact_group=group,
        fact_key=key,
        normalized_value=None,
        raw_evidence_text=None,
        status="NOT_FOUND_IN_AVAILABLE_SOURCES",
        source_locator=None,
        metadata_json=None,
        fingerprint=fingerprint,
    )
