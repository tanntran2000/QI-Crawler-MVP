"""Shared conservative normalization for integer money inputs."""

from __future__ import annotations

import math
import re
from decimal import Decimal
from typing import Any

_DOT_GROUPED_INTEGER = re.compile(r"^\d{1,3}(?:\.\d{3})+$")
_COMMA_GROUPED_INTEGER = re.compile(r"^\d{1,3}(?:,\d{3})+$")
_SPACE_GROUPED_INTEGER = re.compile(r"^\d{1,3}(?: \d{3})+$")


def _compact_money_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        return str(value)
    if isinstance(value, Decimal):
        return str(value) if value.is_finite() else None
    text = " ".join(str(value).strip().split())
    return text or None


def normalize_money_value(value: Any) -> Decimal | None:
    """Return an unambiguous numeric value, or None for invalid input."""

    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, Decimal):
        return value if value.is_finite() else None
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(str(value)) if math.isfinite(value) else None

    raw = _compact_money_text(value)
    if raw is None:
        return None
    if raw.isdigit():
        normalized = raw
    elif _DOT_GROUPED_INTEGER.fullmatch(raw):
        normalized = raw.replace(".", "")
    elif _COMMA_GROUPED_INTEGER.fullmatch(raw):
        normalized = raw.replace(",", "")
    elif _SPACE_GROUPED_INTEGER.fullmatch(raw):
        normalized = raw.replace(" ", "")
    else:
        return None
    return Decimal(normalized)


def parse_optional_money_input(value: str) -> Decimal | None:
    """Parse an optional UI money field and reject nonblank invalid input."""

    if not value or not value.strip():
        return None
    normalized = normalize_money_value(value)
    if normalized is None:
        raise ValueError("Ngân sách phải là số hợp lệ.")
    return normalized
