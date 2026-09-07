"""Conservative normalization helpers for KHMT source values."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from qi_crawler.keywords import normalize_keyword
from qi_crawler.market_intelligence.selection_methods import (
    normalize_selection_method as _normalize_selection_method,
)
from qi_crawler.market_intelligence.value_normalization import normalize_money_value

_PLAN_ID_PATTERN = re.compile(r"^(PL\d{10})(?:-(\d{2}))?$")



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

    return normalize_money_value(value)

def normalize_selection_method(value: Any) -> str | None:
    """Backward-compatible KHMT wrapper around the shared contract."""

    return _normalize_selection_method(value)


def normalize_search_value(value: Any) -> str:
    raw = compact_text(value)
    return normalize_keyword(raw or "")
