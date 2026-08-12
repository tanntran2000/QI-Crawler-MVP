from __future__ import annotations

import html
import re
import unicodedata
from datetime import datetime

from ..datetime_utils import parse_datetime_utc


def fold_text(value: object) -> str:
    text = str(value or "").replace("Đ", "D").replace("đ", "d")
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn").lower()


def clean_text(value: object, *, preserve_newlines: bool = False) -> str | None:
    if value is None:
        return None
    text = html.unescape(str(value)).replace("\xa0", " ").replace("\r", "\n").replace("\t", " ")
    if preserve_newlines:
        lines = [re.sub(r"[ ]+", " ", line).strip() for line in text.split("\n")]
        text = "\n".join(line for line in lines if line)
    else:
        text = re.sub(r"\s+", " ", text).strip()
    return text or None


def parse_number(value: object) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = clean_text(value)
    if not text:
        return None
    digits = re.sub(r"[^0-9-]", "", text)
    if not digits or digits == "-":
        return None
    return float(digits)


def parse_datetime_value(value: object) -> datetime | None:
    """Backward-compatible export helper backed by the shared UTC parser."""
    return parse_datetime_utc(value)


def display_datetime(value: datetime | None, fallback: str | None = None) -> str | None:
    if value is not None:
        return value.strftime("%d/%m/%Y %H:%M")
    return clean_text(fallback)


def format_package_name(
    package_name: str | None,
    notice_id: str | None,
    source_notice_id: str | None,
    source_name: str | None,
    published_at: datetime | None,
    published_at_source: str | None,
) -> str | None:
    package = clean_text(package_name)
    if not package:
        return None
    details: list[str] = []
    if notice_id:
        details.append(f"Số thông báo: {clean_text(notice_id)}")
    elif source_notice_id:
        source = clean_text(source_name) or "Nguồn khác"
        source_label = "Coteccons eBidding" if source.lower() == "coteccons" else source
        prefix = "COTEC-" if source.lower() == "coteccons" else ""
        details.append(f"Mã nguồn: {prefix}{clean_text(source_notice_id)}. Nguồn: {source_label}")
    published = display_datetime(published_at, published_at_source)
    if published:
        details.append(f"Thời điểm đăng tải: {published}")
    if not notice_id and source_notice_id:
        prefix = re.match(r"^\s*GÓI\s+THẦU\s*:\s*", package, re.IGNORECASE)
        if prefix:
            package = f"GÓI THẦU: {package[prefix.end():].strip()}"
        else:
            package = f"GÓI THẦU: {package}"
    return f"{package}\n({'. '.join(details)})" if details else package


def raw_field(raw_text: str | None, *labels: str) -> str | None:
    text = html.unescape(raw_text or "")
    lines = [clean_text(line) for line in text.splitlines()]
    clean_lines = [line for line in lines if line]
    folded_labels = tuple(fold_text(label).rstrip(":") for label in labels)
    for index, line in enumerate(clean_lines):
        folded_line = fold_text(line)
        for label in folded_labels:
            if folded_line.rstrip(":") == label and index + 1 < len(clean_lines):
                return clean_lines[index + 1]
            if folded_line.startswith(label) and ":" in line:
                value = clean_text(line.split(":", 1)[1])
                if value:
                    return value
    return None
