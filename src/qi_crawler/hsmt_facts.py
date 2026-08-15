"""Deterministic, source-traceable HSMT facts derived from native evidence."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from hashlib import sha256
from typing import Protocol

from sqlalchemy import delete, select

from .db import Database
from .models import Document, DocumentEvidence, DocumentExtraction, HSMTFact

PACKAGE_OVERVIEW = "PACKAGE_OVERVIEW"
CHAPTER_III_EVALUATION = "CHAPTER_III_EVALUATION"
CHAPTER_V_TECHNICAL = "CHAPTER_V_TECHNICAL"
BOM_SUPPLY = "BOM_SUPPLY"  # Historical storage key; values are HSMT requirements, never a BOM.
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


@dataclass(frozen=True)
class ParsedSourceFact:
    """A parser-validated source value, never a keyword hit by itself."""

    fact_group: str
    fact_key: str
    value: str
    metadata: dict[str, object]
    status: str = "FOUND"


class SourceFactParser(Protocol):
    def parse(self, text: str, evidence: DocumentEvidence) -> list[ParsedSourceFact]: ...


def _display_text(text: str) -> str:
    """Repair legacy mojibake for matching/display without changing raw evidence."""
    if "Ã" not in text and "Â" not in text:
        return text
    try:
        return text.encode("latin1").decode("utf-8")
    except UnicodeError:
        return text


def _compact(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" ;:-\n\t")


def _text_matches(text: str, pattern: str) -> re.Match[str] | None:
    return re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)


class PackageParser:
    _purpose = re.compile(
        r"(?:tên gói thầu|mục tiêu gói thầu|mục đích gói thầu|phạm vi gói thầu)\s*"
        r"(?:(?:\d+\.)?[A-Z]{2,10}\s*)?[:\-]\s*(.{3,500}?)"
        r"(?=\n\s*(?:tên gói thầu|mục tiêu gói thầu|mục đích gói thầu|phạm vi gói thầu|"
        r"dự án(?:/dự toán)?|phát hành|ban hành|mục lục|chương\s+[ivx]+)\b|$)",
        re.IGNORECASE | re.DOTALL,
    )

    def parse(self, text: str, evidence: DocumentEvidence) -> list[ParsedSourceFact]:
        match = self._purpose.search(text)
        if not match:
            return []
        value = _compact(match.group(1))
        value = re.sub(r"^(?:mẫu\s*số\s*\S+\s*[:\-]\s*)+", "", value, flags=re.IGNORECASE)
        value = re.sub(r"^(?:\d+\.)?[A-Z]{2,10}\s*:\s*", "", value, flags=re.IGNORECASE)
        return [ParsedSourceFact(PACKAGE_OVERVIEW, "PACKAGE_PURPOSE", value, {})] if value else []


class ProcurementParser:
    _rules = (
        ("SELECTION_METHOD", r"\bchào hàng cạnh tranh(?: trong nước)?\b"),
        ("SELECTION_PROCEDURE", r"\bmột giai đoạn một túi hồ sơ\b"),
        ("CONTRACT_TYPE", r"\btrọn gói\b"),
    )

    def parse(self, text: str, evidence: DocumentEvidence) -> list[ParsedSourceFact]:
        return [
            ParsedSourceFact(PACKAGE_OVERVIEW, key, match.group(0), {})
            for key, pattern in self._rules
            if (match := _text_matches(text, pattern))
        ]


_SUPPLY_ROW = re.compile(
    r"^\s*(?P<item>[^|\n]{2,}?)\s*\|\s*"
    r"(?P<quantity>\d+(?:[.,]\d+)?)(?:\s*\|\s*|\s+)(?P<unit>[^\s|\n\d][^|\n]{0,23})"
    r"(?:\s*\|\s*(?P<spec>[^\n]+))?\s*$",
    re.IGNORECASE,
)
_SUPPLY_LIST = re.compile(
    r"^\s*(?:[-•]|\d+[.)])\s*(?P<item>[^:\n]{2,}?)\s*[:\-]\s*"
    r"(?P<quantity>\d+(?:[.,]\d+)?)\s+(?P<unit>[^;\n\d]{1,24})"
    r"(?:\s*[;\-]\s*(?P<spec>[^\n]+))?\s*$",
    re.IGNORECASE,
)
_QUANTITY_UNIT = re.compile(r"^(?P<quantity>\d+(?:[.,]\d+)?)\s*(?P<unit>[^\d;|]{1,24})$", re.IGNORECASE)
_UNIT_QUANTITY = re.compile(r"^(?P<unit>[^\d;|]{1,24})\s*(?P<quantity>\d+(?:[.,]\d+)?)$", re.IGNORECASE)
_KNOWN_UNITS = r"bộ|cái|chiếc|thùng|mét|m|kg|gói|lô|hộp|cuộn|tủ|license|giấy phép"
_CANONICAL_UNITS = {"bộ": "SET", "cái": "PIECE", "chiếc": "PIECE", "thùng": "CARTON", "mét": "METER"}
_SUPPLY_LAYOUT_ROW = re.compile(
    rf"(?:^|(?<=\n)|\b\d+[ \t]+ngày[ \t]+\d+[ \t]+ngày[ \t\r\n]+)"
    rf"\d+(?![ \t]+ngày\b)[ \t]+(?P<item>[^\n]+(?:\n[^\n]+){{0,4}})[ \t\r\n]+"
    rf"(?P<unit>{_KNOWN_UNITS})[ \t]+(?P<quantity>\d+(?:[.,]\d+)?)[ \t\r\n]+"
    r"Theo[ \t\r\n]+quy[ \t\r\n]+định[ \t\r\n]+tại[ \t\r\n]+Chương[ \t\r\n]+V",
    re.IGNORECASE | re.MULTILINE,
)


def _supply_fields(text: str, evidence: DocumentEvidence) -> dict[str, object] | None:
    rows = _supply_rows(text, evidence)
    return rows[0] if rows else None


def _supply_rows(text: str, evidence: DocumentEvidence) -> list[dict[str, object]]:
    match = _SUPPLY_ROW.match(text) if evidence.content_type in {"TABLE", "TABLE_ROW"} else _SUPPLY_LIST.match(text)
    if match:
        fields = _build_supply_fields(match.group("item"), match.group("quantity"), match.group("unit"), match.group("spec") or "")
        return [fields] if fields is not None else []
    if not _has_technical_context(text, evidence):
        return []
    layout_rows = [
        _build_supply_fields(item.group("item"), item.group("quantity"), item.group("unit"), "")
        for item in _SUPPLY_LAYOUT_ROW.finditer(text)
    ]
    if valid_rows := [fields for fields in layout_rows if fields is not None]:
        return valid_rows
    list_rows = [
        _build_supply_fields(item.group("item"), item.group("quantity"), item.group("unit"), item.group("spec") or "")
        for line in text.splitlines()
        if (item := _SUPPLY_LIST.match(line))
    ]
    return [fields for fields in list_rows if fields is not None] or _nearby_supply_fields(text)


def _has_technical_context(text: str, evidence: DocumentEvidence) -> bool:
    context = " ".join((evidence.section_heading or "", text))
    return bool(
        _text_matches(
            context,
            r"chương\s*v|yêu cầu về kỹ thuật|yêu cầu kỹ thuật|chỉ dẫn kỹ thuật|danh mục hàng hóa|phạm vi cung cấp",
        )
    )


def _build_supply_fields(item_text: str, raw_quantity: str, raw_unit_text: str, specification: str) -> dict[str, object] | None:
    raw_unit = _compact(raw_unit_text)
    item = _compact(item_text)
    if not item or not raw_unit or not _text_matches(raw_unit, rf"^(?:{_KNOWN_UNITS})\b"):
        return None
    inline_specification = ""
    if ":" in item:
        name, candidate_specification = item.split(":", 1)
        if _text_matches(candidate_specification, r"[%±≥≤<>]|\b(?:tiêu chuẩn|vật liệu|đồng|thép|nhựa|mm|gbps|w|v)\b"):
            item = _compact(name)
            inline_specification = _compact(candidate_specification)
    quantity: int | float = int(raw_quantity) if raw_quantity.isdigit() else float(raw_quantity.replace(",", "."))
    return {
        "item_name": item,
        "raw_quantity_text": raw_quantity,
        "quantity": quantity,
        "raw_unit": raw_unit,
        "canonical_unit": _CANONICAL_UNITS.get(raw_unit.casefold(), "UNCLASSIFIED"),
        "specification": _compact(specification) or inline_specification,
    }


def _nearby_supply_fields(text: str) -> list[dict[str, object]]:
    """Parse a conservative PDF/list layout: item + nearby quantity/unit + optional spec."""
    lines = [_compact(line) for line in text.splitlines() if _compact(line)]
    output: list[dict[str, object]] = []
    for index, line in enumerate(lines):
        match = _QUANTITY_UNIT.match(line)
        used = 1
        if not match and index + 1 < len(lines) and line.replace(",", ".").replace(".", "", 1).isdigit():
            unit_match = _text_matches(lines[index + 1], rf"^(?:{_KNOWN_UNITS})\b")
            if unit_match:
                match = re.match(r"(?P<quantity>.+)", line)
                raw_unit = lines[index + 1]
                used = 2
            else:
                raw_unit = ""
        else:
            raw_unit = match.group("unit") if match else ""
        if not match or index == 0:
            continue
        item = lines[index - 1]
        if not _looks_like_supply_item(item):
            continue
        spec = _nearby_spec(lines, index + used)
        fields = _build_supply_fields(item, match.group("quantity"), raw_unit, spec)
        if fields is not None:
            output.append(fields)
    return output


def _looks_like_supply_item(value: str) -> bool:
    normalized = value.casefold().strip(":-")
    headings = {
        "stt",
        "số lượng",
        "đơn vị",
        "mô tả",
        "danh mục",
        "yêu cầu kỹ thuật",
        "chỉ dẫn kỹ thuật",
        "phạm vi cung cấp",
    }
    return len(normalized) >= 3 and normalized not in headings


def _nearby_spec(lines: list[str], start: int) -> str:
    candidates = lines[start : start + 2]
    specs = [
        line
        for line in candidates
        if _text_matches(line, r"[%±≥≤<>]|\b(?:tiêu chuẩn|vật liệu|đồng|thép|nhựa|mm|gbps|w|v)\b")
    ]
    return "; ".join(specs)


class SupplyItemParser:
    def parse(self, text: str, evidence: DocumentEvidence) -> list[ParsedSourceFact]:
        output: list[ParsedSourceFact] = []
        for fields in _supply_rows(text, evidence):
            value = f"{fields['item_name']} — {fields['raw_quantity_text']} {fields['raw_unit']}"
            if spec := fields["specification"]:
                value = f"{value} — {spec}"
            output.append(ParsedSourceFact(BOM_SUPPLY, "SUPPLY_REQUIREMENT", value, fields))
        return output


class TechnicalSpecParser:
    def parse(self, text: str, evidence: DocumentEvidence) -> list[ParsedSourceFact]:
        return [
            ParsedSourceFact(
                CHAPTER_V_TECHNICAL,
                "ITEM_TECHNICAL_SPEC",
                f"{fields['item_name']} — {fields['specification']}",
                {"item_name": fields["item_name"], "specification": fields["specification"]},
            )
            for fields in _supply_rows(text, evidence)
            if fields["specification"]
        ]


class ScheduleParser:
    _period = re.compile(
        r"(?:thời gian thực hiện|thời gian giao hàng|thời hạn thực hiện|tiến độ)\s*[:\-]?\s*"
        r"(\d+(?:[.,]\d+)?\s*(?:ngày|tháng|năm))",
        re.IGNORECASE,
    )

    def parse(self, text: str, evidence: DocumentEvidence) -> list[ParsedSourceFact]:
        output = [
            ParsedSourceFact(SCHEDULE_SOW, "EXECUTION_PERIOD", _compact(match.group(1)), {})
            for match in self._period.finditer(text)
        ]
        if _text_matches(text, r"ngày\s+giao\s+hàng\s+muộn\s+nhất"):
            output.extend(
                ParsedSourceFact(SCHEDULE_SOW, "EXECUTION_PERIOD", _compact(match.group(1)), {})
                for match in re.finditer(r"\b\d+\s+ngày\s+(\d+\s+ngày)\b", text, re.IGNORECASE)
            )
        return output


class WorkScopeParser:
    _actions = (
        ("CUNG CẤP", r"\bcung cấp\b"),
        ("VẬN CHUYỂN", r"\bvận chuyển\b"),
        ("LẮP ĐẶT", r"\blắp đặt\b"),
        ("CẤU HÌNH", r"\bcấu hình\b"),
        ("TÍCH HỢP", r"\btích hợp\b"),
        ("KIỂM THỬ", r"\bkiểm thử\b"),
        ("NGHIỆM THU", r"\bnghiệm thu\b"),
        ("BÀN GIAO", r"\bbàn giao\b"),
        ("ĐÀO TẠO", r"\bđào tạo\b"),
        ("BẢO HÀNH", r"\bbảo hành\b"),
    )

    def parse(self, text: str, evidence: DocumentEvidence) -> list[ParsedSourceFact]:
        scope = _text_matches(text, r"phạm vi công việc|phạm vi cung cấp|dịch vụ liên quan bao gồm|các dịch vụ bao gồm")
        if not scope or _text_matches(text[scope.end() : scope.end() + 30], r"^\s*của\s+hợp\s+đồng"):
            return []
        actions = [label for label, pattern in self._actions if _text_matches(text, pattern)]
        output: list[ParsedSourceFact] = []
        if len(actions) >= 2:
            output.append(ParsedSourceFact(SCHEDULE_SOW, "WORK_SCOPE", "; ".join(actions), {"actions": actions}))
        for label, pattern in self._actions:
            match = _text_matches(text, rf"{pattern}\s*(\d+(?:[.,]\d+)?\s*(?:{_KNOWN_UNITS}))")
            if match:
                output.append(ParsedSourceFact(SCHEDULE_SOW, "WORK_QUANTITY", f"{label} — {match.group(1)}", {"action": label}))
        return output


class RequiredDocumentParser:
    _labels = (
        ("Catalogue", r"\bcatalogue\b|\bcatalog\b"),
        ("CO/CQ", r"\bco\s*/\s*cq\b"),
        ("Xác nhận của hãng", r"xác nhận của hãng"),
        ("Bản dịch", r"\bbản dịch\b"),
    )

    def parse(self, text: str, evidence: DocumentEvidence) -> list[ParsedSourceFact]:
        if not _text_matches(text, r"\byêu cầu\b|\bhồ sơ\b|\btài liệu\b"):
            return []
        documents = [label for label, pattern in self._labels if _text_matches(text, pattern)]
        if not documents:
            return []
        return [ParsedSourceFact(REQUIRED_DOCUMENTS, "REQUIRED_DOCUMENTS", "; ".join(documents), {"documents": documents})]


_PARSERS: tuple[SourceFactParser, ...] = (
    PackageParser(),
    ProcurementParser(),
    SupplyItemParser(),
    TechnicalSpecParser(),
    ScheduleParser(),
    WorkScopeParser(),
    RequiredDocumentParser(),
)


class HSMTFactService:
    """Derive concise source requirements from existing evidence only."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def refresh_tender(self, tender_id: int) -> None:
        """Rebuild derived facts; raw evidence remains the immutable source."""
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
            _resolve_source_document_references(candidates, {document.original_filename.casefold() for document, _ in rows})
            _mark_schedule_conflicts(candidates)
            _add_missing_facts(candidates, tender_id)
            session.execute(delete(HSMTFact).where(HSMTFact.tender_id == tender_id))
            for fact in _collapse_semantic_facts(candidates):
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
    raw_text = (evidence.text or "").strip()
    text = _display_text(raw_text)
    output = [
        _fact(document, evidence, parsed)
        for parser in _PARSERS
        for parsed in parser.parse(text, evidence)
    ]
    if (
        not any(item.fact_group == BOM_SUPPLY for item in output)
        and _text_matches(text, rf"\d+(?:[.,]\d+)?\s*(?:{_KNOWN_UNITS})\b")
        and _has_technical_context(text, evidence)
        and not _text_matches(text, r"\bví dụ\b")
    ):
        output.append(
            _fact(
                document,
                evidence,
                ParsedSourceFact(
                    MISSING_INFORMATION,
                    "SUPPLY_REQUIREMENT_UNCERTAIN",
                    "Có số lượng/đơn vị nhưng chưa xác định chắc chắn dòng yêu cầu cung ứng.",
                    {},
                    "NEEDS_REVIEW",
                ),
            )
        )
    if match := _text_matches(
        text,
        r"(?:yêu cầu về kỹ thuật|yêu cầu kỹ thuật|chỉ dẫn kỹ thuật)\s*[:\-]\s*([^\n]+?\.(?:pdf|docx|xlsx))\b",
    ):
        output.append(
            _fact(
                document,
                evidence,
                ParsedSourceFact(
                    MISSING_INFORMATION,
                    "TECHNICAL_SOURCE_DOCUMENT",
                    _compact(match.group(1)),
                    {},
                    "NEEDS_REVIEW",
                ),
            )
        )
    if _text_matches(text, r"(?:xem|theo)\s+(?:phụ lục|đính kèm)"):
        output.append(
            _fact(
                document,
                evidence,
                ParsedSourceFact(
                    MISSING_INFORMATION,
                    "REFERENCED_ATTACHMENT",
                    "Tài liệu có tham chiếu phụ lục/đính kèm; cần kiểm tra bộ tài liệu.",
                    {},
                    "SOURCE_DOCUMENT_MISSING",
                ),
            )
        )
    return output


def _mark_schedule_conflicts(candidates: list[HSMTFact]) -> None:
    values = {
        _semantic_value(item.normalized_value)
        for item in candidates
        if item.fact_group == SCHEDULE_SOW and item.fact_key == "EXECUTION_PERIOD"
    }
    if len(values) > 1:
        for item in candidates:
            if item.fact_group == SCHEDULE_SOW and item.fact_key == "EXECUTION_PERIOD":
                item.status = "SOURCE_CONFLICT"


def _add_missing_facts(candidates: list[HSMTFact], tender_id: int) -> None:
    for group, key in (
        (PACKAGE_OVERVIEW, "PACKAGE_PURPOSE"),
        (SCHEDULE_SOW, "EXECUTION_PERIOD"),
        (BOM_SUPPLY, "SUPPLY_REQUIREMENT"),
    ):
        supply_needs_review = group == BOM_SUPPLY and any(
            item.fact_key in {"SUPPLY_REQUIREMENT_UNCERTAIN", "TECHNICAL_SOURCE_DOCUMENT"}
            and item.status in {"NEEDS_REVIEW", "SOURCE_DOCUMENT_MISSING"}
            for item in candidates
        )
        if not supply_needs_review and not any(item.fact_group == group and item.fact_key == key for item in candidates):
            candidates.append(_missing_fact(tender_id, group, key))


def _semantic_value(value: str | None) -> str:
    return re.sub(r"\W+", "", (value or "").casefold())


def _resolve_source_document_references(candidates: list[HSMTFact], available_names: set[str]) -> None:
    for fact in candidates:
        if fact.fact_key != "TECHNICAL_SOURCE_DOCUMENT" or not fact.normalized_value:
            continue
        if fact.normalized_value.casefold() not in available_names:
            fact.status = "SOURCE_DOCUMENT_MISSING"


def _collapse_semantic_facts(candidates: list[HSMTFact]) -> list[HSMTFact]:
    """Keep one concise fact per meaning while retaining all evidence references."""
    unique: dict[tuple[str, str, str, str], HSMTFact] = {}
    for fact in candidates:
        key = (fact.fact_group, fact.fact_key, _semantic_value(fact.normalized_value), fact.status)
        previous = unique.get(key)
        if previous is None and fact.fact_key == "PACKAGE_PURPOSE":
            previous = next(
                (
                    existing
                    for existing in unique.values()
                    if existing.fact_group == fact.fact_group
                    and existing.fact_key == fact.fact_key
                    and existing.status == fact.status
                    and _same_package_purpose(existing.normalized_value, fact.normalized_value)
                ),
                None,
            )
        if previous is None:
            unique[key] = fact
            continue
        _add_evidence_reference(previous, fact)
    return list(unique.values())


def _same_package_purpose(left: str | None, right: str | None) -> bool:
    """Collapse formatting/wrapping variants only; material wording stays separate."""
    left_value = _semantic_value(left)
    right_value = _semantic_value(right)
    if not left_value or not right_value:
        return False
    if left_value in right_value or right_value in left_value:
        return True
    left_tokens = set(re.findall(r"\w+", (left or "").casefold()))
    right_tokens = set(re.findall(r"\w+", (right or "").casefold()))
    return bool(left_tokens and right_tokens) and len(left_tokens & right_tokens) / min(len(left_tokens), len(right_tokens)) >= 0.9


def _add_evidence_reference(previous: HSMTFact, fact: HSMTFact) -> None:
    metadata = json.loads(previous.metadata_json or "{}")
    references = metadata.setdefault("evidence_references", [])
    references.append({"evidence_id": fact.evidence_id, "source_locator": fact.source_locator})
    previous.metadata_json = json.dumps(metadata, ensure_ascii=False)


def _fact(document: Document, evidence: DocumentEvidence, parsed: ParsedSourceFact) -> HSMTFact:
    fingerprint = sha256(
        f"{document.tender_id}|{evidence.id}|{parsed.fact_group}|{parsed.fact_key}|{parsed.value}".encode()
    ).hexdigest()
    metadata = {"page": evidence.page_number, "sheet": evidence.sheet_name, **parsed.metadata}
    return HSMTFact(
        tender_id=document.tender_id,
        document_id=document.id,
        evidence_id=evidence.id,
        fact_group=parsed.fact_group,
        fact_key=parsed.fact_key,
        normalized_value=parsed.value,
        raw_evidence_text=evidence.text,
        status=parsed.status,
        source_locator=evidence.source_locator,
        metadata_json=json.dumps(metadata, ensure_ascii=False),
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
