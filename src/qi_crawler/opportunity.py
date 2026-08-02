from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from .keywords import matches_any_keyword, normalize_keyword
from .models import CompanyEvidence, InventoryItem, Notice
from .stock import check_stock


@dataclass(frozen=True)
class KeywordGroup:
    name: str
    terms: tuple[str, ...]
    weight: float


@dataclass(frozen=True)
class ScoreComponent:
    name: str
    score: float
    maximum: float
    explanation: str


@dataclass(frozen=True)
class OpportunityAssessment:
    notice_id: int
    score: float | None
    status: str
    priority: str
    matched_keywords: tuple[str, ...]
    matched_groups: tuple[str, ...]
    excluded_keywords: tuple[str, ...]
    matched_evidence: tuple[str, ...]
    missing_fields: tuple[str, ...]
    components: tuple[ScoreComponent, ...]
    risks: tuple[str, ...]
    reasons: tuple[str, ...]
    next_action: str
    alerts: tuple[str, ...]
    days_left: float | None


PRODUCT_EVIDENCE_TYPES = {"product", "solution", "manufacturer", "catalog"}
SIMILAR_EVIDENCE_TYPES = {
    "contract",
    "project",
    "reference",
    "past_performance",
    "experience",
}
SUPPLY_EVIDENCE_TYPES = {"supply", "support", "service", "manufacturer_support"}
FINANCIAL_CAPACITY_TYPES = {"financial", "credit", "cashflow"}
PAYMENT_EVIDENCE_TYPES = {"payment"}
LOCATION_EVIDENCE_TYPES = {"location", "sla", "service", "delivery"}


def _notice_text(notice: Notice) -> str:
    return " ".join(
        filter(
            None,
            (
                notice.title,
                notice.raw_text,
                notice.buyer,
                notice.investor,
                notice.location,
                notice.sector,
                notice.selection_method,
            ),
        )
    )


def _evidence_terms(item: CompanyEvidence) -> tuple[str, ...]:
    return tuple(
        part.strip()
        for part in (item.keywords or "").replace(";", ",").split(",")
        if part.strip()
    )


def _evidence_matches(item: CompanyEvidence, text: str) -> bool:
    terms = _evidence_terms(item)
    return bool(terms) and any(matches_any_keyword(text, [term]) for term in terms)


def _inventory_matches(item: InventoryItem, text: str) -> bool:
    terms = [item.product_name]
    terms.extend(
        part.strip()
        for part in (item.aliases or "").replace(";", ",").split(",")
        if part.strip()
    )
    return item.verified and any(matches_any_keyword(text, [term]) for term in terms)


def _parse_deadline(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    patterns = (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%H:%M %d/%m/%Y",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
    )
    for pattern in patterns:
        try:
            return datetime.strptime(text[:19], pattern).replace(tzinfo=UTC)
        except ValueError:
            continue
    try:
        parsed = datetime.fromisoformat(text)
        return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)
    except ValueError:
        return None


def _critical_missing_fields(notice: Notice) -> tuple[str, ...]:
    missing: list[str] = []
    if not notice.notice_code:
        missing.append("notice_code")
    if not notice.title:
        missing.append("title")
    if notice.package_price is None:
        missing.append("package_price")
    if not notice.closing_at or _parse_deadline(notice.closing_at) is None:
        missing.append("closing_at")
    if not notice.source_url:
        missing.append("source_url")
    raw = normalize_keyword(notice.raw_text or "")
    title = normalize_keyword(notice.title or "")
    if not raw or raw == title:
        missing.append("detail_information")
    return tuple(missing)


def _priority_for_status(status: str) -> str:
    return {
        "PRIORITY": "A",
        "REVIEW": "B",
        "SKIP": "C",
        "INSUFFICIENT_DATA": "U",
    }[status]


def _action_for_status(status: str) -> str:
    return {
        "PRIORITY": "Tai E-HSMT va giao Presales phan tich",
        "REVIEW": "Bo sung du lieu va giao nguoi phu trach kiem tra",
        "SKIP": "Bo qua hoac chi theo doi",
        "INSUFFICIENT_DATA": "Mo trang chi tiet va bo sung metadata truoc khi xep hang",
    }[status]


def assess_opportunity(
    notice: Notice,
    keyword_groups: tuple[KeywordGroup, ...],
    evidence: list[CompanyEvidence],
    inventory: list[InventoryItem],
    *,
    required_any: tuple[str, ...] = (),
    required_all: tuple[str, ...] = (),
    excluded_terms: tuple[str, ...] = (),
    now: datetime | None = None,
    priority_threshold: float = 75.0,
    review_threshold: float = 55.0,
    closing_soon_days: int = 3,
    new_alert_hours: int = 24,
) -> OpportunityAssessment:
    now = now or datetime.now(UTC)
    text = _notice_text(notice)
    reasons: list[str] = []
    risks: list[str] = []
    alerts: list[str] = []

    excluded = tuple(term for term in excluded_terms if matches_any_keyword(text, [term]))
    matched_group_names: list[str] = []
    matched_keywords: list[str] = []
    keyword_score = 0.0
    for group in keyword_groups:
        group_matches = [term for term in group.terms if matches_any_keyword(text, [term])]
        if not group_matches:
            continue
        matched_group_names.append(group.name)
        matched_keywords.extend(group_matches)
        keyword_score += group.weight
    keyword_score = min(keyword_score, 30.0)
    matched_keywords = list(dict.fromkeys(matched_keywords))

    required_any_ok = not required_any or any(
        matches_any_keyword(text, [term]) for term in required_any
    )
    missing_required = tuple(
        term for term in required_all if not matches_any_keyword(text, [term])
    )
    keyword_component = ScoreComponent(
        "keyword_sector",
        keyword_score,
        30.0,
        (
            f"Khop nhom: {', '.join(matched_group_names)}"
            if matched_group_names
            else "Khong khop nhom keyword duong"
        ),
    )

    deadline = _parse_deadline(notice.closing_at)
    days_left = (deadline - now).total_seconds() / 86400 if deadline else None
    if excluded or not matched_keywords or not required_any_ok or missing_required:
        if excluded:
            risks.append(f"Khop keyword loai tru: {', '.join(excluded)}")
        if not required_any_ok:
            risks.append("Khong dat dieu kien OR bat buoc")
        if missing_required:
            risks.append(f"Thieu keyword AND bat buoc: {', '.join(missing_required)}")
        if not matched_keywords:
            risks.append("Khong co keyword duong phu hop")
        return OpportunityAssessment(
            notice.id,
            0.0,
            "SKIP",
            "C",
            tuple(matched_keywords),
            tuple(matched_group_names),
            excluded,
            (),
            (),
            (keyword_component,),
            tuple(risks),
            tuple(reasons),
            _action_for_status("SKIP"),
            (),
            days_left,
        )

    if days_left is not None and days_left <= 0:
        risks.append("Goi da het han")
        return OpportunityAssessment(
            notice.id,
            0.0,
            "SKIP",
            "C",
            tuple(matched_keywords),
            tuple(matched_group_names),
            excluded,
            (),
            (),
            (keyword_component,),
            tuple(risks),
            ("Khong xep hang goi da het han",),
            _action_for_status("SKIP"),
            (),
            days_left,
        )

    verified = [item for item in evidence if item.verified]
    product_evidence = [
        item
        for item in verified
        if item.evidence_type.casefold() in PRODUCT_EVIDENCE_TYPES
        and _evidence_matches(item, text)
    ]
    similar_evidence = [
        item
        for item in verified
        if item.evidence_type.casefold() in SIMILAR_EVIDENCE_TYPES
        and _evidence_matches(item, text)
    ]
    supply_evidence = [
        item
        for item in verified
        if item.evidence_type.casefold() in SUPPLY_EVIDENCE_TYPES
        and _evidence_matches(item, text)
    ]
    financial_capacity = [
        item for item in verified if item.evidence_type.casefold() in FINANCIAL_CAPACITY_TYPES
    ]
    payment_evidence = [
        item for item in verified if item.evidence_type.casefold() in PAYMENT_EVIDENCE_TYPES
    ]
    financial_evidence = financial_capacity + payment_evidence
    location_evidence = [
        item
        for item in verified
        if item.evidence_type.casefold() in LOCATION_EVIDENCE_TYPES
        and _evidence_matches(item, " ".join(filter(None, (notice.location, text))))
    ]
    inventory_matches = [item for item in inventory if _inventory_matches(item, text)]

    product_score = 20.0 if product_evidence or inventory_matches else 0.0
    components: list[ScoreComponent] = [
        keyword_component,
        ScoreComponent(
            "product_solution",
            product_score,
            20.0,
            (
                "Co san pham/giai phap da xac minh"
                if product_score
                else "Chua co san pham/giai phap da xac minh"
            ),
        ),
    ]
    similar_score = 20.0 if similar_evidence else 0.0
    components.append(
        ScoreComponent(
            "similar_contract",
            similar_score,
            20.0,
            (
                f"Hop dong/du an tuong tu: {', '.join(item.evidence_code for item in similar_evidence)}"
                if similar_evidence
                else "Chua co hop dong/du an tuong tu da xac minh"
            ),
        )
    )

    supply_score = 0.0
    supply_explanation = "Chua co du lieu cung ung/ton kho phu hop"
    if notice.tender_items:
        stock_results = [check_stock(item, inventory) for item in notice.tender_items]
        if stock_results and all(item.status == "MEETS_STOCK" for item in stock_results):
            supply_score = 10.0
            supply_explanation = "Ton kho da xac minh dap ung cac dong co so luong"
        elif any(item.status in {"MEETS_STOCK", "STOCK_SHORTAGE"} for item in stock_results):
            supply_score = 5.0
            supply_explanation = "Co kha nang cung ung nhung can bo sung/kiem tra so luong"
    elif inventory_matches or supply_evidence:
        supply_score = 5.0
        supply_explanation = "Co tin hieu cung ung; chua co BOQ de kiem dem day du"
    components.append(ScoreComponent("supply_inventory", supply_score, 10.0, supply_explanation))

    financial_score = 0.0
    if financial_capacity and payment_evidence:
        financial_score = 10.0
    elif financial_evidence:
        financial_score = 5.0
    components.append(
        ScoreComponent(
            "financial_payment",
            financial_score,
            10.0,
            (
                "Co du bang chung nang luc tai chinh va dieu kien thanh toan"
                if financial_score == 10.0
                else (
                    "Co mot phan bang chung; can doi chieu quy mo va thanh toan"
                    if financial_evidence
                    else "Chua co du lieu tai chinh/thanh toan da xac minh"
                )
            ),
        )
    )

    time_score = 0.0
    if days_left is not None:
        if days_left >= 7:
            time_score = 5.0
        elif days_left >= 3:
            time_score = 3.0
        else:
            time_score = 1.0
    components.append(
        ScoreComponent(
            "preparation_time",
            time_score,
            5.0,
            f"Con {days_left:.1f} ngay" if days_left is not None else "Chua doc duoc deadline",
        )
    )

    location_score = 5.0 if notice.location and location_evidence else 0.0
    components.append(
        ScoreComponent(
            "location_sla",
            location_score,
            5.0,
            (
                "Co bang chung dia diem/SLA phu hop"
                if location_score
                else "Can kiem tra dia diem va kha nang dap ung SLA"
            ),
        )
    )

    matched_evidence = tuple(
        dict.fromkeys(
            item.evidence_code
            for item in (
                product_evidence
                + similar_evidence
                + supply_evidence
                + financial_evidence
                + location_evidence
            )
        )
    )
    missing = _critical_missing_fields(notice)
    if missing:
        risks.append(f"Thieu du lieu quan trong: {', '.join(missing)}")
    if not product_score:
        risks.append("Chua xac nhan san pham/giai phap QI")
    if not similar_score:
        risks.append("Chua co hop dong tuong tu phu hop")
    if supply_score < 10:
        risks.append("Can kiem tra ton kho, hang ho tro va BOQ")
    if financial_score < 10:
        risks.append("Can doi chieu quy mo tai chinh va dieu kien thanh toan")
    if not notice.location:
        risks.append("Chua co dia diem thuc hien")
    if not notice.sector:
        risks.append("Chua co linh vuc")
    if not notice.selection_method:
        risks.append("Chua co phuong thuc lua chon")

    total = round(min(sum(item.score for item in components), 100.0), 1)
    if missing:
        status = "INSUFFICIENT_DATA"
        reported_score = None
        reasons.append("Chua xep hang cho den khi du metadata quan trong")
    elif total >= priority_threshold:
        status = "PRIORITY"
        reported_score = total
    elif total >= review_threshold:
        status = "REVIEW"
        reported_score = total
    else:
        status = "SKIP"
        reported_score = total

    first_seen = notice.first_seen_at
    if first_seen:
        first_seen = first_seen.replace(tzinfo=UTC) if first_seen.tzinfo is None else first_seen
        if (now - first_seen.astimezone(UTC)).total_seconds() <= new_alert_hours * 3600:
            alerts.append("NEW_MATCH")
    if days_left is not None and 0 < days_left <= closing_soon_days:
        alerts.append("CLOSING_SOON")

    reasons.extend(item.explanation for item in components)
    return OpportunityAssessment(
        notice.id,
        reported_score,
        status,
        _priority_for_status(status),
        tuple(matched_keywords),
        tuple(matched_group_names),
        excluded,
        matched_evidence,
        missing,
        tuple(components),
        tuple(dict.fromkeys(risks)),
        tuple(reasons),
        _action_for_status(status),
        tuple(alerts),
        days_left,
    )
