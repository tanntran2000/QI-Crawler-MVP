from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


@dataclass
class ParsedAttachment:
    source_url: str
    file_name: str | None = None


@dataclass
class ParsedNotice:
    source_url: str
    notice_code: str | None = None
    title: str | None = None
    buyer: str | None = None
    investor: str | None = None
    package_price: float | None = None
    currency: str | None = None
    published_at: str | None = None
    closing_at: str | None = None
    raw_text: str = ""
    attachments: list[ParsedAttachment] = field(default_factory=list)


def _compact(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _fold(text: str) -> str:
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
                value = re.sub(rf"^{re.escape(label)}\s*:?\s*", "", line, flags=re.IGNORECASE)
                if value and value != line:
                    return _compact(value)
    return None


def parse_money(value: str | None) -> tuple[float | None, str | None]:
    if not value:
        return None, None
    folded = _fold(value)
    currency = "VND" if any(x in folded for x in ("vnd", "vnđ", "dong")) else None
    # Giá Việt Nam thường dùng dấu chấm phân tách hàng nghìn.
    digits = re.sub(r"[^0-9]", "", value)
    if not digits:
        return None, currency
    return float(digits), currency


def _looks_like_attachment(href: str, text: str, extensions: set[str]) -> bool:
    path = urlparse(href).path.lower()
    if any(path.endswith(ext) for ext in extensions):
        return True
    folded = _fold(text)
    return any(word in folded for word in ("tai ve", "dinh kem", "hsm t", "hsmt", "quyet dinh", "file"))


def parse_notice_html(
    html: str,
    source_url: str,
    attachment_extensions: list[str] | None = None,
) -> ParsedNotice:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "template"]):
        tag.decompose()

    lines = [_compact(line) for line in soup.get_text("\n").splitlines()]
    lines = [line for line in lines if line]
    raw_text = "\n".join(lines)

    title = _extract_label_value(lines, ("Tên gói thầu", "Tên dự án", "Tiêu đề"))
    if not title:
        heading = soup.find(["h1", "h2", "h3"])
        title = _compact(heading.get_text(" ")) if heading else None
        if title and "lựa chọn nhà thầu" in _fold(title):
            title = None

    notice_code = _extract_label_value(
        lines, ("Mã TBMT", "Mã thông báo", "Số TBMT", "Mã KHLCNT", "Mã gói thầu")
    )
    if not notice_code:
        match = re.search(r"\b(?:IB|TBMT|KHLCNT)[A-Z0-9._/-]{5,}\b", raw_text, re.IGNORECASE)
        notice_code = match.group(0) if match else None

    buyer = _extract_label_value(lines, ("Bên mời thầu", "Đơn vị mời thầu"))
    investor = _extract_label_value(lines, ("Chủ đầu tư",))
    price_text = _extract_label_value(lines, ("Giá gói thầu", "Giá dự toán", "Giá trị gói thầu"))
    package_price, currency = parse_money(price_text)
    published_at = _extract_label_value(lines, ("Ngày đăng tải", "Thời gian đăng tải"))
    closing_at = _extract_label_value(lines, ("Thời điểm đóng thầu", "Thời gian đóng thầu"))

    ext = set(attachment_extensions or [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip"])
    attachments: list[ParsedAttachment] = []
    seen: set[str] = set()
    for anchor in soup.select("a[href]"):
        href = urljoin(source_url, anchor.get("href", "").strip())
        text = _compact(anchor.get_text(" "))
        if href in seen or not href.startswith(("http://", "https://")):
            continue
        if _looks_like_attachment(href, text, ext):
            seen.add(href)
            file_name = text or urlparse(href).path.rsplit("/", 1)[-1] or None
            attachments.append(ParsedAttachment(source_url=href, file_name=file_name))

    return ParsedNotice(
        source_url=source_url,
        notice_code=notice_code,
        title=title,
        buyer=buyer,
        investor=investor,
        package_price=package_price,
        currency=currency,
        published_at=published_at,
        closing_at=closing_at,
        raw_text=raw_text,
        attachments=attachments,
    )


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
