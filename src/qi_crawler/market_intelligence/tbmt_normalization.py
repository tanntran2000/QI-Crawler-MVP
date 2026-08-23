"""Conservative TBMT source-value and IB identity normalization."""

from __future__ import annotations

import math
import re
from decimal import Decimal, InvalidOperation
from typing import Any

from qi_crawler.market_intelligence.opportunity_contract import OpportunityIdentity

_IDENTITY_TOKEN_RE = re.compile(
    r"\b(?P<raw>(?P<namespace>PL|IB)[0-9]{8,14}"
    r"(?:\s*-\s*(?P<revision>[0-9A-Za-z]+))?)\b",
    re.IGNORECASE,
)
_EXTENDED_IDENTITY_SUFFIX_RE = re.compile(r"^\s*-\s*[0-9A-Za-z]")
_GROUPED_INTEGER_RE = re.compile(r"^\d{1,3}(?:([.,])\d{3})+$")
_SPACE_GROUPED_INTEGER_RE = re.compile(r"^\d{1,3}(?: \d{3})+$")


def compact_source_text(value: Any) -> str | None:
    """Trim and compact source text without classifying values as garbage."""

    if value is None:
        return None
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    text = " ".join(str(value).split())
    return text or None


def parse_tbmt_package_price(value: Any) -> Decimal | None:
    """Parse only unambiguous, non-negative TBMT currency values."""

    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, Decimal):
        return value if value.is_finite() and value >= 0 else None
    if isinstance(value, int):
        return Decimal(value) if value >= 0 else None
    if isinstance(value, float):
        if not math.isfinite(value) or value < 0:
            return None
        return Decimal(str(value))

    raw = compact_source_text(value)
    if raw is None:
        return None
    if raw.isdigit():
        return Decimal(raw)
    if _SPACE_GROUPED_INTEGER_RE.fullmatch(raw):
        raw = raw.replace(" ", "")
    elif _GROUPED_INTEGER_RE.fullmatch(raw):
        raw = raw.replace(".", "").replace(",", "")
    else:
        return None
    try:
        return Decimal(raw)
    except InvalidOperation:
        return None


def parse_tbmt_notice_identity(value: Any) -> OpportunityIdentity | None:
    """Parse exactly one revisioned PL/IB identity from a TBMT source cell.

    TBMT rows require an IB identity with a two-digit revision. Any PL,
    missing/malformed revision, or ambiguous identity set is rejected.
    """

    if value is None:
        return None
    text = str(value)
    if not text.strip():
        return None
    matches = list(_IDENTITY_TOKEN_RE.finditer(text))
    if len(matches) != 1:
        return None
    match = matches[0]
    if _EXTENDED_IDENTITY_SUFFIX_RE.match(text[match.end() :]):
        return None
    if match.group("namespace").upper() != "IB":
        return None
    revision = match.group("revision")
    if revision is None or not re.fullmatch(r"[0-9]{2}", revision):
        return None
    try:
        return OpportunityIdentity.from_raw(match.group("raw"))
    except ValueError:
        return None
