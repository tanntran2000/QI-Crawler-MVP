"""Small, offline and evidence-first province/city resolver for MI-1."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from qi_crawler.keywords import normalize_keyword

from .khmt_contract import ProvinceCityStatus
from .khmt_normalization import compact_text

LOCATION_ALIAS_VERSION = "mi-1-2026-08"
LOCATION_EVIDENCE_FIELDS = (
    "TÊN CHỦ ĐẦU TƯ",
    "TÊN DỰ ÁN",
    "NỘI DUNG PHÊ DUYỆT",
    "TÊN GÓI THẦU",
)

_LOCATIONS = {
    "HCM": (
        "Thành phố Hồ Chí Minh",
        ("thành phố hồ chí minh", "tp. hồ chí minh", "tp hồ chí minh", "tp.hcm", "tp hcm"),
    ),
    "HN": (
        "Thành phố Hà Nội",
        ("thành phố hà nội", "tp. hà nội", "tp hà nội", "hà nội"),
    ),
}


@dataclass(frozen=True, slots=True)
class ProvinceCityResolution:
    code: str | None
    name: str | None
    status: ProvinceCityStatus
    evidence: str
    location_detail_raw: str | None
    alias_version: str = LOCATION_ALIAS_VERSION


def _search_text(value: str) -> str:
    normalized = normalize_keyword(value)
    return re.sub(r"[^a-z0-9]+", " ", normalized).strip()


def _contains_alias(text: str, alias: str) -> bool:
    return f" {_search_text(alias)} " in f" {_search_text(text)} "


def resolve_province_city(raw_fields: dict[str, Any]) -> ProvinceCityResolution:
    matches: dict[str, tuple[str, list[str], str]] = {}
    for field_name in LOCATION_EVIDENCE_FIELDS:
        raw_value = compact_text(raw_fields.get(field_name))
        if raw_value is None:
            continue
        for code, (name, aliases) in _LOCATIONS.items():
            if any(_contains_alias(raw_value, alias) for alias in aliases):
                existing = matches.setdefault(code, (name, [], raw_value))
                existing[1].append(f"{field_name}: {raw_value}")

    if len(matches) == 1:
        code, (name, evidence, location_text) = next(iter(matches.items()))
        return ProvinceCityResolution(
            code=code,
            name=name,
            status=ProvinceCityStatus.CONFIRMED,
            evidence=" | ".join(evidence),
            location_detail_raw=location_text,
        )
    if len(matches) > 1:
        evidence = [item for _, (_, items, _) in matches.items() for item in items]
        return ProvinceCityResolution(
            code=None,
            name=None,
            status=ProvinceCityStatus.NEEDS_REVIEW,
            evidence=f"Conflicting province/city evidence: {' | '.join(evidence)}",
            location_detail_raw=None,
        )
    return ProvinceCityResolution(
        code=None,
        name=None,
        status=ProvinceCityStatus.NEEDS_REVIEW,
        evidence="No explicit, unambiguous province/city in supported source fields",
        location_detail_raw=None,
    )
