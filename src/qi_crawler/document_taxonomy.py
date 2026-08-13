"""Conservative tender-document taxonomy without AI, OCR or content extraction."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from sqlalchemy import select

from .db import Database
from .keywords import normalize_keyword
from .models import Document


class TenderDocumentType(StrEnum):
    E_TBMT = "E_TBMT"
    E_HSMT = "E_HSMT"
    E_HSDT = "E_HSDT"
    E_HSDXKT = "E_HSDXKT"
    E_HSDXTC = "E_HSDXTC"
    E_HSMST = "E_HSMST"
    E_HSMQT = "E_HSMQT"
    TECHNICAL_REQUIREMENT = "TECHNICAL_REQUIREMENT"
    BOQ_BOM = "BOQ_BOM"
    PRICE_SCHEDULE = "PRICE_SCHEDULE"
    CONTRACT_DRAFT = "CONTRACT_DRAFT"
    AMENDMENT = "AMENDMENT"
    CLARIFICATION = "CLARIFICATION"
    APPENDIX = "APPENDIX"
    BID_SECURITY = "BID_SECURITY"
    LEGAL = "LEGAL"
    CAPABILITY = "CAPABILITY"
    FINANCIAL = "FINANCIAL"
    VENDOR_EVIDENCE = "VENDOR_EVIDENCE"
    OTHER = "OTHER"


class ClassificationStatus(StrEnum):
    VERIFIED = "VERIFIED"
    CANDIDATE = "CANDIDATE"
    UNKNOWN = "UNKNOWN"
    NEEDS_REVIEW = "NEEDS_REVIEW"


DOCUMENT_TYPE_LABELS: dict[TenderDocumentType, str] = {
    TenderDocumentType.E_TBMT: "Thông báo mời thầu qua mạng",
    TenderDocumentType.E_HSMT: "Hồ sơ mời thầu qua mạng",
    TenderDocumentType.E_HSDT: "Hồ sơ dự thầu qua mạng",
    TenderDocumentType.E_HSDXKT: "Hồ sơ đề xuất kỹ thuật",
    TenderDocumentType.E_HSDXTC: "Hồ sơ đề xuất tài chính",
    TenderDocumentType.E_HSMST: "Hồ sơ mời sơ tuyển",
    TenderDocumentType.E_HSMQT: "Hồ sơ mời quan tâm",
    TenderDocumentType.TECHNICAL_REQUIREMENT: "Yêu cầu kỹ thuật",
    TenderDocumentType.BOQ_BOM: "Phạm vi cung cấp / BOQ / BOM",
    TenderDocumentType.PRICE_SCHEDULE: "Bảng giá / biểu giá",
    TenderDocumentType.CONTRACT_DRAFT: "Dự thảo hợp đồng",
    TenderDocumentType.AMENDMENT: "Văn bản sửa đổi",
    TenderDocumentType.CLARIFICATION: "Văn bản làm rõ",
    TenderDocumentType.APPENDIX: "Phụ lục",
    TenderDocumentType.BID_SECURITY: "Bảo đảm dự thầu",
    TenderDocumentType.LEGAL: "Hồ sơ pháp lý",
    TenderDocumentType.CAPABILITY: "Năng lực & kinh nghiệm",
    TenderDocumentType.FINANCIAL: "Hồ sơ tài chính",
    TenderDocumentType.VENDOR_EVIDENCE: "Tài liệu Hãng/NPP",
    TenderDocumentType.OTHER: "Tài liệu khác",
}

CLASSIFICATION_STATUS_LABELS: dict[ClassificationStatus, str] = {
    ClassificationStatus.VERIFIED: "Đã xác minh",
    ClassificationStatus.CANDIDATE: "Nhận diện sơ bộ",
    ClassificationStatus.UNKNOWN: "Chưa xác định",
    ClassificationStatus.NEEDS_REVIEW: "Cần kiểm tra",
}


@dataclass(frozen=True)
class TemplateFamily:
    code: str
    label: str


TEMPLATE_REGISTRY: dict[str, TemplateFamily] = {
    "3": TemplateFamily("3", "Xây lắp"),
    "4": TemplateFamily("4", "Hàng hóa"),
    "5": TemplateFamily("5", "Phi tư vấn"),
    "6": TemplateFamily("6", "Tư vấn"),
    "7": TemplateFamily("7", "EP"),
    "8": TemplateFamily("8", "EC"),
    "9": TemplateFamily("9", "PC"),
    "10": TemplateFamily("10", "EPC"),
    "11": TemplateFamily("11", "Máy đặt/máy mượn"),
    "12": TemplateFamily("12", "Chào giá trực tuyến"),
    "13": TemplateFamily("13", "Mua sắm trực tuyến"),
    "14": TemplateFamily("14", "Báo cáo đánh giá"),
}


_PATTERNS: dict[TenderDocumentType, tuple[str, ...]] = {
    TenderDocumentType.E_TBMT: ("e-tbmt", "thông báo mời thầu qua mạng"),
    TenderDocumentType.E_HSMT: ("e-hsmt", "hồ sơ mời thầu qua mạng"),
    TenderDocumentType.E_HSDT: ("e-hsdt", "hồ sơ dự thầu qua mạng"),
    TenderDocumentType.E_HSDXKT: ("e-hsdxkt", "hồ sơ đề xuất kỹ thuật"),
    TenderDocumentType.E_HSDXTC: ("e-hsdxtc", "hồ sơ đề xuất tài chính"),
    TenderDocumentType.E_HSMST: ("e-hsmst", "hồ sơ mời sơ tuyển"),
    TenderDocumentType.E_HSMQT: ("e-hsmqt", "hồ sơ mời quan tâm"),
    TenderDocumentType.TECHNICAL_REQUIREMENT: (
        "yêu cầu kỹ thuật",
        "technical requirement",
        "technical specification",
    ),
    TenderDocumentType.BOQ_BOM: (
        "boq",
        "bom",
        "bảng khối lượng",
        "phạm vi cung cấp",
        "bill of quantity",
        "bill of material",
    ),
    TenderDocumentType.PRICE_SCHEDULE: ("bảng giá", "biểu giá", "price schedule"),
    TenderDocumentType.CONTRACT_DRAFT: ("dự thảo hợp đồng", "draft contract"),
    TenderDocumentType.AMENDMENT: ("văn bản sửa đổi", "amendment", "addendum"),
    TenderDocumentType.CLARIFICATION: ("văn bản làm rõ", "clarification"),
    TenderDocumentType.APPENDIX: ("phụ lục", "appendix"),
    TenderDocumentType.BID_SECURITY: ("bảo đảm dự thầu", "bid security"),
    TenderDocumentType.LEGAL: ("hồ sơ pháp lý", "legal document"),
    TenderDocumentType.CAPABILITY: (
        "năng lực kinh nghiệm",
        "năng lực & kinh nghiệm",
        "capability experience",
    ),
    TenderDocumentType.FINANCIAL: ("hồ sơ tài chính", "financial statement"),
    TenderDocumentType.VENDOR_EVIDENCE: (
        "tài liệu hãng",
        "tài liệu nhà phân phối",
        "vendor evidence",
    ),
}


@dataclass(frozen=True)
class DocumentClassification:
    document_type: TenderDocumentType
    template_code: str | None
    package_type: str | None
    selection_method: str | None
    status: ClassificationStatus
    matched_types: tuple[TenderDocumentType, ...] = ()


def _contains_phrase(text: str, phrase: str) -> bool:
    normalized_text = normalize_keyword(text)
    normalized_phrase = normalize_keyword(phrase)
    if not normalized_phrase:
        return False
    return bool(
        re.search(
            rf"(?<!\w){re.escape(normalized_phrase)}(?!\w)",
            normalized_text,
        )
    )


def _matched_types(text: str) -> tuple[TenderDocumentType, ...]:
    return tuple(
        document_type
        for document_type, patterns in _PATTERNS.items()
        if any(_contains_phrase(text, pattern) for pattern in patterns)
    )


def classify_document(
    *,
    metadata_title: str | None,
    filename: str,
    identity_status: str,
    template_code: str | None = None,
    package_type: str | None = None,
    selection_method: str | None = None,
) -> DocumentClassification:
    """Return a conservative candidate; only user confirmation can be VERIFIED."""
    metadata_matches = _matched_types(metadata_title or "")
    filename_matches = _matched_types(filename)
    matches = tuple(dict.fromkeys((*metadata_matches, *filename_matches)))
    safe_template = template_code if template_code in TEMPLATE_REGISTRY else None

    if len(matches) > 1:
        return DocumentClassification(
            document_type=TenderDocumentType.OTHER,
            template_code=safe_template,
            package_type=package_type,
            selection_method=selection_method,
            status=ClassificationStatus.NEEDS_REVIEW,
            matched_types=matches,
        )
    if len(matches) == 1:
        status = (
            ClassificationStatus.CANDIDATE
            if identity_status == "VERIFIED_LINKED"
            else ClassificationStatus.NEEDS_REVIEW
        )
        return DocumentClassification(
            document_type=matches[0],
            template_code=safe_template,
            package_type=package_type,
            selection_method=selection_method,
            status=status,
            matched_types=matches,
        )
    return DocumentClassification(
        document_type=TenderDocumentType.OTHER,
        template_code=safe_template,
        package_type=package_type,
        selection_method=selection_method,
        status=(
            ClassificationStatus.UNKNOWN
            if identity_status == "VERIFIED_LINKED"
            else ClassificationStatus.NEEDS_REVIEW
        ),
    )


class DocumentClassificationError(RuntimeError):
    """Classification cannot be confirmed safely."""


class DocumentClassificationService:
    """Persist an explicit human confirmation on the existing Document record."""

    def __init__(self, database: Database):
        self.database = database
        self.database.require_current_schema()

    def confirm(
        self,
        document_id: int,
        document_type: str,
        *,
        template_code: str | None = None,
        package_type: str | None = None,
        selection_method: str | None = None,
    ) -> DocumentClassification:
        try:
            selected_type = TenderDocumentType(document_type)
        except ValueError as exc:
            raise DocumentClassificationError("Loại tài liệu không hợp lệ.") from exc
        safe_template = (template_code or "").strip() or None
        if safe_template is not None and safe_template not in TEMPLATE_REGISTRY:
            raise DocumentClassificationError("Mã template chưa có trong registry.")

        with self.database.session() as session:
            document = session.scalar(
                select(Document).where(Document.id == document_id).limit(1)
            )
            if document is None:
                raise DocumentClassificationError("Không tìm thấy tài liệu.")
            identity_verified = document.status == "VERIFIED_LINKED" or (
                document.status == "STORED" and document.tender_id is not None
            )
            if not identity_verified:
                raise DocumentClassificationError(
                    "Identity tender chưa được xác minh; không thể xác nhận loại tài liệu."
                )
            document.document_type = selected_type.value
            document.template_code = safe_template
            document.package_type = (package_type or "").strip() or None
            document.selection_method = (selection_method or "").strip() or None
            document.classification_status = ClassificationStatus.VERIFIED.value

        return DocumentClassification(
            document_type=selected_type,
            template_code=safe_template,
            package_type=(package_type or "").strip() or None,
            selection_method=(selection_method or "").strip() or None,
            status=ClassificationStatus.VERIFIED,
            matched_types=(selected_type,),
        )
