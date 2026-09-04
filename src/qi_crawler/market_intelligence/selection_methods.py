"""Canonical selection-method normalization shared by source adapters and UI."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from qi_crawler.keywords import normalize_keyword

_LABEL_TO_CODE = {
    "chi dinh thau": "CHI_DINH_THAU",
    "chi dinh thau rut gon": "CHI_DINH_THAU_RUT_GON",
    "chao hang canh tranh": "CHAO_HANG_CANH_TRANH",
    "dau thau rong rai": "DAU_THAU_RONG_RAI",
    "chao gia truc tuyen theo quy trinh rut gon": (
        "CHAO_GIA_TRUC_TUYEN_THEO_QUY_TRINH_RUT_GON"
    ),
    "chao gia truc tuyen": "CHAO_GIA_TRUC_TUYEN",
    "dau thau han che": "DAU_THAU_HAN_CHE",
    "khac": "KHAC",
    "tu thuc hien": "TU_THUC_HIEN",
    "mua sam truc tiep": "MUA_SAM_TRUC_TIEP",
}

SUPPORTED_SELECTION_METHODS = frozenset(_LABEL_TO_CODE.values())


def _compact(value: Any) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).split()).strip()
    return text or None


def normalize_selection_method(value: Any) -> str | None:
    """Map a bounded source label or canonical code to its canonical code.

    Unknown, non-blank source text is deliberately unsupported rather than
    guessed. Callers that need the original observation must retain it
    separately.
    """

    raw = _compact(value)
    if raw is None:
        return None
    code = raw.upper()
    if code in SUPPORTED_SELECTION_METHODS:
        return code
    first_component = raw.split(",", maxsplit=1)[0].strip()
    return _LABEL_TO_CODE.get(normalize_keyword(first_component))


def normalize_selection_method_filters(values: Iterable[Any]) -> frozenset[str]:
    """Normalize UI filter values and reject unknown non-blank tokens."""

    normalized: set[str] = set()
    unknown: list[str] = []
    for value in values:
        raw = _compact(value)
        if raw is None:
            continue
        code = normalize_selection_method(raw)
        if code is None:
            unknown.append(raw)
        else:
            normalized.add(code)
    if unknown:
        raise ValueError("Unsupported selection method: " + ", ".join(unknown))
    return frozenset(normalized)


__all__ = [
    "SUPPORTED_SELECTION_METHODS",
    "normalize_selection_method",
    "normalize_selection_method_filters",
]
