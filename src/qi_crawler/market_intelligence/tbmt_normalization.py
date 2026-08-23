"""Conservative TBMT source-value and IB identity normalization."""

from __future__ import annotations

import re
from typing import Any

from qi_crawler.market_intelligence.opportunity_contract import OpportunityIdentity

_IDENTITY_TOKEN_RE = re.compile(
    r"\b(?P<raw>(?P<namespace>PL|IB)[0-9]{8,14}"
    r"(?:\s*-\s*(?P<revision>[0-9A-Za-z]+))?)\b",
    re.IGNORECASE,
)


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
    if match.group("namespace").upper() != "IB":
        return None
    revision = match.group("revision")
    if revision is None or not re.fullmatch(r"[0-9]{2}", revision):
        return None
    try:
        return OpportunityIdentity.from_raw(match.group("raw"))
    except ValueError:
        return None
