"""Small, offline and evidence-first province/city resolver for MI-1."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from qi_crawler.keywords import normalize_keyword

from .khmt_contract import ProvinceCityStatus
from .khmt_normalization import compact_text

LOCATION_ALIAS_VERSION = "mi-1-2026-08.1"
ADMIN_UNIT_MAPPING_VERSION = "mi-1-golden-hcm-2026-08.1"
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

_ADMIN_UNIT_LOCATIONS = {
    "HCM": (
        "Thành phố Hồ Chí Minh",
        ("xã Châu Đức", "xã Phú Giáo", "phường Thới An"),
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
    matches: dict[str, dict[str, Any]] = {}
    for field_name in LOCATION_EVIDENCE_FIELDS:
        raw_value = compact_text(raw_fields.get(field_name))
        if raw_value is None:
            continue
        for code, (name, aliases) in _LOCATIONS.items():
            if any(_contains_alias(raw_value, alias) for alias in aliases):
                existing = matches.setdefault(
                    code,
                    {"name": name, "evidence": [], "raw": raw_value, "explicit": False},
                )
                existing["explicit"] = True
                existing["evidence"].append(f"{field_name}: {raw_value}")
        for code, (name, subunits) in _ADMIN_UNIT_LOCATIONS.items():
            if any(_contains_alias(raw_value, subunit) for subunit in subunits):
                existing = matches.setdefault(
                    code,
                    {"name": name, "evidence": [], "raw": raw_value, "explicit": False},
                )
                existing["evidence"].append(
                    f"{field_name}: {raw_value} [mapping={ADMIN_UNIT_MAPPING_VERSION}]"
                )

    if len(matches) == 1:
        code, match = next(iter(matches.items()))
        return ProvinceCityResolution(
            code=code,
            name=match["name"],
            status=(
                ProvinceCityStatus.CONFIRMED if match["explicit"] else ProvinceCityStatus.INFERRED
            ),
            evidence=" | ".join(dict.fromkeys(match["evidence"])),
            location_detail_raw=match["raw"],
        )
    if len(matches) > 1:
        evidence = [item for match in matches.values() for item in match["evidence"]]
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
