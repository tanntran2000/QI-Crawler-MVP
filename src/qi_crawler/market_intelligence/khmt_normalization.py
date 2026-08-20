"""Conservative normalization helpers for KHMT source values."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from qi_crawler.keywords import normalize_keyword

_PLAN_ID_PATTERN = re.compile(r"^(PL\d{10})(?:-(\d{2}))?$")
_GROUPED_INTEGER_PATTERN = re.compile(r"^\d{1,3}(?:([.,])\d{3})(?:\1\d{3})*$")
_SPACE_GROUPED_INTEGER_PATTERN = re.compile(r"^\d{1,3}(?: \d{3})+$")

_SELECTION_METHODS = {
    "chi dinh thau": "CHI_DINH_THAU",
    "chi dinh thau rut gon": "CHI_DINH_THAU_RUT_GON",
    "chao hang canh tranh": "CHAO_HANG_CANH_TRANH",
    "dau thau rong rai": "DAU_THAU_RONG_RAI",
}


@dataclass(frozen=True, slots=True)
class PlanIdentity:
    raw: str
    base_id: str
    revision: str | None


def compact_text(value: Any) -> str | None:
    """Extract a source cell as compact text without semantic rewriting."""

    if value is None:
        return None
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    text = str(value).strip()
    return " ".join(text.split()) or None


def parse_plan_identity(value: Any) -> PlanIdentity | None:
    raw = compact_text(value)
    if raw is None:
        return None
    matched = _PLAN_ID_PATTERN.fullmatch(raw)
    if matched is None:
        return None
    return PlanIdentity(raw=raw, base_id=matched.group(1), revision=matched.group(2))


def parse_package_price(value: Any) -> Decimal | None:
    """Parse unambiguous integer currency amounts; never treat invalid as zero."""

    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, Decimal):
        return value if value.is_finite() else None
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(str(value)) if math.isfinite(value) else None

    raw = compact_text(value)
    if raw is None:
        return None
    normalized = raw.replace("\u00a0", " ")
    if normalized.isdigit():
        return Decimal(normalized)
    if _SPACE_GROUPED_INTEGER_PATTERN.fullmatch(normalized):
        normalized = normalized.replace(" ", "")
    elif _GROUPED_INTEGER_PATTERN.fullmatch(normalized):
        normalized = normalized.replace(".", "").replace(",", "")
    else:
        return None
    try:
        return Decimal(normalized)
    except InvalidOperation:
        return None


def normalize_selection_method(value: Any) -> str | None:
    raw = compact_text(value)
    if raw is None:
        return None
    return _SELECTION_METHODS.get(normalize_keyword(raw))


def normalize_search_value(value: Any) -> str:
    raw = compact_text(value)
    return normalize_keyword(raw or "")
