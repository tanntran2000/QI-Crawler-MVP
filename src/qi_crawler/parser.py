from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from .datetime_utils import parse_datetime_utc


@dataclass
class ParsedAttachment:
    source_url: str
    file_name: str | None = None


@dataclass
class ParsedTenderItem:
    item_code: str
    product_name: str
    specification: str | None = None
    quantity: float | None = None
    minimum_quantity: float | None = None
    maximum_quantity: float | None = None
    unit: str | None = None
    source_document: str | None = None
    source_location: str | None = None
    extraction_confidence: float = 0.0
    needs_human_review: bool = True


@dataclass
class ParsedNotice:
    source_url: str
    notice_code: str | None = None
    plan_code: str | None = None
    title: str | None = None
    buyer: str | None = None
    procuring_entity_address: str | None = None
    buyer_tax_code: str | None = None
    investor: str | None = None
    investor_tax_code: str | None = None
    project_name: str | None = None
    package_description: str | None = None
    package_price: float | None = None
    estimated_price: float | None = None
    currency: str | None = None
    published_at: str | None = None
    closing_at: str | None = None
    location: str | None = None
    sector: str | None = None
    selection_method: str | None = None
    selection_form: str | None = None
    notice_version: str | None = None
    notice_type: str = "tbmt"
    funding_source: str | None = None
    contract_type: str | None = None
    bid_type: str | None = None
    document_issue_at: datetime | None = None
    document_price: float | None = None
    bid_security_amount: float | None = None
    bid_security_method: str | None = None
    issue_location: str | None = None
    published_at_dt: datetime | None = None
    closing_at_dt: datetime | None = None
    bid_open_at: datetime | None = None
    contract_duration: str | None = None
    raw_text: str = ""
    attachments: list[ParsedAttachment] = field(default_factory=list)
    items: list[ParsedTenderItem] = field(default_factory=list)


@dataclass
class ParsedSelectionPlan:
    """Parsed data from a KHLCNT (selection plan) page."""
    source_url: str
    plan_code: str | None = None
    project_name: str | None = None
    investor: str | None = None
    investor_tax_code: str | None = None
    buyer: str | None = None
    buyer_tax_code: str | None = None
    total_investment: float | None = None
    currency: str | None = None
    funding_source: str | None = None
    location: str | None = None
    sector: str | None = None
    approval_date: str | None = None
    expected_start: str | None = None
    expected_end: str | None = None
    package_count: int | None = None
    raw_text: str = ""
    raw_html_path: str | None = None


@dataclass
class ParsedBidResult:
    """Parsed data from a KQLCNT (bid result) page."""
    source_url: str
    notice_code: str | None = None
    plan_code: str | None = None
    result_code: str | None = None
    contractor_name: str | None = None
    contractor_tax_code: str | None = None
    is_winner: bool = False
    bid_price: float | None = None
    winning_price: float | None = None
    currency: str | None = None
    discount_rate: float | None = None
    contract_duration: str | None = None
    evaluation_score: float | None = None
    ranking: int | None = None
    result_date: str | None = None
    raw_text: str = ""


@dataclass
class ParsedBidOpening:
    """Parsed data from a KQMT (bid opening) page."""
    source_url: str
    notice_code: str | None = None
    contractor_name: str | None = None
    contractor_tax_code: str | None = None
    bid_price: float | None = None
    currency: str | None = None
    bid_security_amount: float | None = None
    technical_score: float | None = None
    opening_date: str | None = None
    status: str | None = None
    raw_text: str = ""


def _compact(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _fold(text: str) -> str:
    text = text.replace("\u0110", "D").replace("\u0111", "d")
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn").lower()


def _extract_label_value(lines: list[str], labels: tuple[str, ...]) -> str | None:
    folded_labels = tuple(_fold(label) for label in labels)
    for idx, line in enumerate(lines):
        folded = _fold(line)
        for label, folded_label in zip(labels, folded_labels):
            if (
                folded == folded_label.rstrip(":")
                or folded == f"{folded_label.rstrip(':')}:"
            ) and idx + 1 < len(lines):
                return lines[idx + 1]
            if folded.startswith(folded_label):
                if ":" in line:
                    value = line.split(":", 1)[1].strip()
                else:
                    value = line[len(label) :].strip()
                if value and value != line:
                    return _compact(value)
    return None


def parse_money(value: str | None) -> tuple[float | None, str | None]:
    """Parse common Vietnamese and international tender price formats.

    Vietnamese notices usually use punctuation only as thousands separators,
    while international notices may include a decimal component.  The value is
    returned as a float for compatibility with the current database schema.
    """
    if not value:
        return None, None
    folded = _fold(value)
    currency = _detect_currency(value, folded)
    number = _parse_decimal_amount(value, currency)
    if number is None:
        return None, currency
    return float(number), currency


def _detect_currency(value: str, folded: str) -> str | None:
    lower = value.lower()
    if (
        any(token in folded for token in ("vnd", "dong"))
        or chr(0x20AB) in value
        or f"vn{chr(0x0111)}" in lower
    ):
        return "VND"
    if "usd" in folded or "$" in value:
        return "USD"
    if "eur" in folded or chr(0x20AC) in value:
        return "EUR"
    if "gbp" in folded or chr(0x00A3) in value:
        return "GBP"
    return None


def _parse_decimal_amount(value: str, currency: str | None) -> Decimal | None:
    """Keep a decimal fraction when the source actually supplies one."""
    compact = re.sub(r"[^0-9,.-]", "", value)
    if not re.search(r"\d", compact):
        return None

    sign = "-" if compact.startswith("-") else ""
    compact = compact.lstrip("-")

    # VND tender prices conventionally have no fractional unit.  Both dots and
    # commas are therefore treated as grouping markers (e.g. 1.500.000 VND).
    if currency == "VND":
        digits = re.sub(r"[^0-9]", "", compact)
        return Decimal(f"{sign}{digits}") if digits else None

    separators = [index for index, char in enumerate(compact) if char in ",."]
    if not separators:
        normalized = compact
    else:
        decimal_index = separators[-1]
        fraction = compact[decimal_index + 1 :]
        before = compact[:decimal_index]
        # A final group of one or two digits is a decimal fraction. A group of
        # three digits is treated as a standard thousands group (1,500 USD).
        if len(fraction) in (1, 2):
            normalized = f"{re.sub(r'[^0-9]', '', before)}.{fraction}"
        else:
            normalized = re.sub(r"[^0-9]", "", compact)

    try:
        return Decimal(f"{sign}{normalized}")
    except InvalidOperation:
        return None


def parse_datetime_value(value: str | None) -> datetime | None:
    """Backward-compatible tender timestamp parser; values are always UTC-aware."""
    return parse_datetime_utc(value)


def _looks_like_attachment(href: str, text: str, extensions: set[str]) -> bool:
    path = urlparse(href).path.lower()
    if any(path.endswith(ext) for ext in extensions):
        return True
    folded = _fold(text)
    return any(word in folded for word in ("tai ve", "dinh kem", "hsm t", "hsmt", "quyet dinh", "file"))


def _extract_tax_code(lines: list[str]) -> str | None:
    """Try to extract a Vietnamese tax code (MST) from page text."""
    tax_labels = ("Ma so thue", "MST", "Ma so doanh nghiep")
    value = _extract_label_value(lines, tax_labels)
    if value and re.match(r"^\d{10,13}$", re.sub(r"[^0-9]", "", value)):
        return re.sub(r"[^0-9]", "", value)
    # Fallback: look for a 10-13 digit code near tax-related labels.
    combined = " ".join(lines)
    match = re.search(r"(?:ma\s*so\s*thue|MST)[:\s]*(\d{10,13})", combined, re.IGNORECASE)
    return match.group(1) if match else None


def _extract_attachments(
    soup: BeautifulSoup,
    source_url: str,
    extensions: set[str],
) -> list[ParsedAttachment]:
    """Extract attachment links from parsed HTML."""
    attachments: list[ParsedAttachment] = []
    seen: set[str] = set()
    for anchor in soup.select("a[href]"):
        href = urljoin(source_url, anchor.get("href", "").strip())
        text = _compact(anchor.get_text(" "))
        if href in seen or not href.startswith(("http://", "https://")):
            continue
        if _looks_like_attachment(href, text, extensions):
            seen.add(href)
            file_name = text or urlparse(href).path.rsplit("/", 1)[-1] or None
            attachments.append(ParsedAttachment(source_url=href, file_name=file_name))
    return attachments


def _prepare_soup_and_lines(html: str) -> tuple[BeautifulSoup, list[str], str]:
    """Strip scripts/styles and return soup, non-empty text lines, and raw_text."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "template"]):
        tag.decompose()
    lines = [_compact(line) for line in soup.get_text("\n").splitlines()]
    lines = [line for line in lines if line]
    raw_text = "\n".join(lines)
    return soup, lines, raw_text


def parse_notice_html(
    html: str,
    source_url: str,
    attachment_extensions: list[str] | None = None,
) -> ParsedNotice:
    soup, lines, raw_text = _prepare_soup_and_lines(html)

    title = _extract_label_value(lines, ("Ten goi thau", "Ten du an", "Tieu de"))
    if not title:
        heading = soup.find(["h1", "h2", "h3"])
        title = _compact(heading.get_text(" ")) if heading else None
        if title and "lua chon nha thau" in _fold(title):
            title = None

    notice_code = _extract_label_value(
        lines, ("Ma TBMT", "Ma thong bao", "So TBMT", "Ma KHLCNT", "Ma goi thau")
    )
    if not notice_code:
        match = re.search(r"\b(?:IB|TBMT|KHLCNT)[A-Z0-9._/-]{5,}\b", raw_text, re.IGNORECASE)
        notice_code = match.group(0) if match else None

    plan_code = _extract_label_value(lines, ("Ma KHLCNT", "Ma ke hoach"))
    buyer = _extract_label_value(lines, ("Ben moi thau", "Don vi moi thau"))
    procuring_entity_address = _extract_label_value(
        lines,
        ("Dia chi ben moi thau", "Dia chi cua ben moi thau", "Dia chi chu dau tu"),
    )
    buyer_tax_code = _extract_tax_code(lines)
    investor = _extract_label_value(lines, ("Chu dau tu",))
    investor_tax_code = _extract_label_value(lines, ("Ma so thue chu dau tu",))
    project_name = _extract_label_value(lines, ("Ten du an", "Du an", "Ten ke hoach"))
    package_description = _extract_label_value(
        lines,
        ("Noi dung chinh cua goi thau", "Mo ta goi thau", "Pham vi cong viec"),
    )
    price_text = _extract_label_value(lines, ("Gia goi thau", "Gia tri goi thau"))
    package_price, currency = parse_money(price_text)
    estimated_text = _extract_label_value(lines, ("Gia du toan", "Gia du kien"))
    estimated_price, _ = parse_money(estimated_text)
    published_at = _extract_label_value(lines, ("Ngay dang tai", "Thoi gian dang tai"))
    closing_at = _extract_label_value(lines, ("Thoi diem dong thau", "Thoi gian dong thau"))
    location = _extract_label_value(
        lines,
        ("Dia diem thuc hien", "Dia diem", "Noi thuc hien goi thau"),
    )
    sector = _extract_label_value(lines, ("Linh vuc", "Phan loai linh vuc"))
    selection_method = _extract_label_value(lines, ("Phuong thuc lua chon nha thau",))
    selection_form = _extract_label_value(lines, ("Hinh thuc lua chon nha thau",))
    notice_version = _extract_label_value(
        lines,
        ("Phien ban", "Lan dang", "Lan thay doi"),
    )
    funding_source = _extract_label_value(lines, ("Nguon von",))
    contract_type = _extract_label_value(lines, ("Loai hop dong",))
    bid_type = _extract_label_value(lines, ("Hinh thuc du thau", "Phuong thuc dau thau"))
    document_issue_text = _extract_label_value(
        lines,
        (
            "Thoi gian phat hanh E-HSMT",
            "Thoi gian phat hanh HSMT",
            "Thoi diem phat hanh E-HSMT",
            "Thoi diem phat hanh HSMT",
        ),
    )
    document_price_text = _extract_label_value(
        lines,
        ("Gia ban 1 bo E-HSMT", "Gia ban 1 bo HSMT", "Gia E-HSMT", "Gia HSMT"),
    )
    document_price, _ = parse_money(document_price_text)
    bid_security_text = _extract_label_value(
        lines,
        ("Gia tri bao dam du thau", "Bao dam du thau"),
    )
    bid_security_amount, _ = parse_money(bid_security_text)
    bid_security_method = _extract_label_value(lines, ("Hinh thuc bao dam du thau",))
    issue_location = _extract_label_value(
        lines,
        ("Dia diem phat hanh E-HSMT", "Dia diem phat hanh HSMT", "Dia diem phat hanh"),
    )
    bid_open_text = _extract_label_value(
        lines,
        ("Thoi gian mo thau", "Thoi diem mo thau", "Ngay mo thau"),
    )
    contract_duration = _extract_label_value(lines, ("Thoi gian thuc hien hop dong",))

    ext = set(attachment_extensions or [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip"])
    attachments = _extract_attachments(soup, source_url, ext)

    return ParsedNotice(
        source_url=source_url,
        notice_code=notice_code,
        plan_code=plan_code,
        title=title,
        buyer=buyer,
        procuring_entity_address=procuring_entity_address,
        buyer_tax_code=buyer_tax_code,
        investor=investor,
        investor_tax_code=investor_tax_code,
        project_name=project_name,
        package_description=package_description,
        package_price=package_price,
        estimated_price=estimated_price,
        currency=currency,
        published_at=published_at,
        closing_at=closing_at,
        location=location,
        sector=sector,
        selection_method=selection_method,
        selection_form=selection_form,
        notice_version=notice_version,
        funding_source=funding_source,
        contract_type=contract_type,
        bid_type=bid_type,
        document_issue_at=parse_datetime_value(document_issue_text),
        document_price=document_price,
        bid_security_amount=bid_security_amount,
        bid_security_method=bid_security_method,
        issue_location=issue_location,
        published_at_dt=parse_datetime_value(published_at),
        closing_at_dt=parse_datetime_value(closing_at),
        bid_open_at=parse_datetime_value(bid_open_text),
        contract_duration=contract_duration,
        raw_text=raw_text,
        attachments=attachments,
    )


def parse_khlcnt_html(html: str, source_url: str) -> ParsedSelectionPlan:
    """Parse a KHLCNT (selection plan) detail page."""
    _, lines, raw_text = _prepare_soup_and_lines(html)

    plan_code = _extract_label_value(lines, ("Ma KHLCNT", "Ma ke hoach"))
    if not plan_code:
        match = re.search(r"\bKHLCNT[A-Z0-9._/-]{3,}\b", raw_text, re.IGNORECASE)
        plan_code = match.group(0) if match else None

    project_name = _extract_label_value(lines, ("Ten du an", "Ten ke hoach"))
    investor = _extract_label_value(lines, ("Chu dau tu",))
    investor_tax_code = _extract_tax_code(lines)
    buyer = _extract_label_value(lines, ("Ben moi thau", "Don vi moi thau"))
    buyer_tax_code = None  # Use investor tax code context.
    total_text = _extract_label_value(lines, ("Tong muc dau tu", "Gia tri du an"))
    total_investment, currency = parse_money(total_text)
    funding_source = _extract_label_value(lines, ("Nguon von",))
    location = _extract_label_value(lines, ("Dia diem thuc hien", "Dia diem"))
    sector = _extract_label_value(lines, ("Linh vuc",))
    approval_date = _extract_label_value(lines, ("Ngay phe duyet",))
    expected_start = _extract_label_value(lines, ("Thoi gian bat dau", "Thoi gian thuc hien tu"))
    expected_end = _extract_label_value(lines, ("Thoi gian ket thuc", "Thoi gian thuc hien den"))
    count_text = _extract_label_value(lines, ("So luong goi thau",))
    package_count = None
    if count_text:
        digits = re.sub(r"[^0-9]", "", count_text)
        package_count = int(digits) if digits else None

    return ParsedSelectionPlan(
        source_url=source_url,
        plan_code=plan_code,
        project_name=project_name,
        investor=investor,
        investor_tax_code=investor_tax_code,
        buyer=buyer,
        buyer_tax_code=buyer_tax_code,
        total_investment=total_investment,
        currency=currency,
        funding_source=funding_source,
        location=location,
        sector=sector,
        approval_date=approval_date,
        expected_start=expected_start,
        expected_end=expected_end,
        package_count=package_count,
        raw_text=raw_text,
    )


def parse_kqlcnt_html(html: str, source_url: str) -> list[ParsedBidResult]:
    """Parse a KQLCNT (bid result) page. May return multiple results (one per contractor)."""
    _, lines, raw_text = _prepare_soup_and_lines(html)

    notice_code = _extract_label_value(lines, ("Ma TBMT", "Ma thong bao", "Ma goi thau"))
    plan_code = _extract_label_value(lines, ("Ma KHLCNT",))
    result_code = _extract_label_value(lines, ("Ma KQLCNT", "Ma ket qua"))

    # Extract winning contractor info.
    contractor_name = _extract_label_value(
        lines, ("Nha thau trung thau", "Nha thau duoc lua chon")
    )
    contractor_tax_code = _extract_label_value(lines, ("Ma so thue nha thau",))
    if not contractor_tax_code:
        contractor_tax_code = _extract_tax_code(lines)
    winning_text = _extract_label_value(lines, ("Gia trung thau", "Gia hop dong"))
    winning_price, currency = parse_money(winning_text)
    bid_text = _extract_label_value(lines, ("Gia du thau", "Gia de nghi trung thau"))
    bid_price, _ = parse_money(bid_text)
    contract_duration = _extract_label_value(lines, ("Thoi gian thuc hien hop dong",))
    result_date = _extract_label_value(
        lines, ("Ngay phe duyet KQLCNT", "Ngay phe duyet ket qua")
    )

    discount_rate = None
    if winning_price and bid_price and bid_price > 0:
        discount_rate = round((1 - winning_price / bid_price) * 100, 2)

    if not contractor_name:
        return []

    return [
        ParsedBidResult(
            source_url=source_url,
            notice_code=notice_code,
            plan_code=plan_code,
            result_code=result_code,
            contractor_name=contractor_name,
            contractor_tax_code=contractor_tax_code,
            is_winner=True,
            bid_price=bid_price,
            winning_price=winning_price,
            currency=currency,
            discount_rate=discount_rate,
            contract_duration=contract_duration,
            result_date=result_date,
            raw_text=raw_text,
        )
    ]


def parse_kqmt_html(html: str, source_url: str) -> list[ParsedBidOpening]:
    """Parse a KQMT (bid opening) page. May return multiple entries (one per bidder)."""
    _, lines, raw_text = _prepare_soup_and_lines(html)

    notice_code = _extract_label_value(lines, ("Ma TBMT", "Ma goi thau"))
    opening_date = _extract_label_value(lines, ("Ngay mo thau", "Thoi diem mo thau"))

    # Try to find a table of bidders. Common structure in e-GP.
    results: list[ParsedBidOpening] = []

    # If structured data is not found, try basic extraction.
    contractor_name = _extract_label_value(lines, ("Ten nha thau",))
    if contractor_name:
        contractor_tax_code = _extract_tax_code(lines)
        bid_text = _extract_label_value(lines, ("Gia du thau", "Gia de xuat"))
        bid_price, currency = parse_money(bid_text)
        security_text = _extract_label_value(lines, ("Bao lanh du thau",))
        security, _ = parse_money(security_text)
        results.append(
            ParsedBidOpening(
                source_url=source_url,
                notice_code=notice_code,
                contractor_name=contractor_name,
                contractor_tax_code=contractor_tax_code,
                bid_price=bid_price,
                currency=currency,
                bid_security_amount=security,
                opening_date=opening_date,
                raw_text=raw_text,
            )
        )

    return results


def extract_detail_links(
    html: str,
    base_url: str,
    list_item_selector: str,
    detail_link_selector: str,
    allowed_domains: list[str],
) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    seen: set[str] = set()
    for item in soup.select(list_item_selector):
        anchor = item if item.name == "a" else item.select_one(detail_link_selector)
        if not anchor or not anchor.get("href"):
            continue
        url = urljoin(base_url, anchor["href"])
        host = (urlparse(url).hostname or "").lower()
        if not any(host == d or host.endswith(f".{d}") for d in allowed_domains):
            continue
        if url not in seen:
            seen.add(url)
            links.append(url)
    return links
