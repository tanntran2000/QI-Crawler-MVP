"""Explainable deterministic filtering for normalized KHMT packages."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from .khmt_contract import PlanPackage, ProvinceCityStatus
from .khmt_normalization import normalize_search_value


class FilterReasonCode(StrEnum):
    MATCH_BUDGET = "MATCH_BUDGET"
    MATCH_PROVINCE = "MATCH_PROVINCE"
    MATCH_KEYWORD = "MATCH_KEYWORD"
    MATCH_SELECTION_METHOD = "MATCH_SELECTION_METHOD"
    EXCLUDED_OVER_MAX_BUDGET = "EXCLUDED_OVER_MAX_BUDGET"
    EXCLUDED_UNDER_MIN_BUDGET = "EXCLUDED_UNDER_MIN_BUDGET"
    PRICE_UNKNOWN = "PRICE_UNKNOWN"
    PROVINCE_NEEDS_REVIEW = "PROVINCE_NEEDS_REVIEW"
    PROVINCE_NOT_MATCHED = "PROVINCE_NOT_MATCHED"
    INCLUDE_KEYWORD_NOT_FOUND = "INCLUDE_KEYWORD_NOT_FOUND"
    EXCLUDE_KEYWORD_FOUND = "EXCLUDE_KEYWORD_FOUND"
    SELECTION_METHOD_NOT_MATCHED = "SELECTION_METHOD_NOT_MATCHED"


@dataclass(frozen=True, slots=True)
class FilterProfile:
    name: str | None = None
    min_budget: Decimal | None = None
    max_budget: Decimal | None = None
    province_city_codes: frozenset[str] = frozenset()
    include_keywords: tuple[str, ...] = ()
    exclude_keywords: tuple[str, ...] = ()
    selection_methods: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "province_city_codes",
            frozenset(value.upper() for value in self.province_city_codes),
        )
        object.__setattr__(
            self,
            "selection_methods",
            frozenset(value.upper() for value in self.selection_methods),
        )
        object.__setattr__(self, "include_keywords", tuple(self.include_keywords))
        object.__setattr__(self, "exclude_keywords", tuple(self.exclude_keywords))


@dataclass(frozen=True, slots=True)
class FilterEvaluation:
    matched: bool
    reasons: tuple[FilterReasonCode, ...]
    matched_fields: tuple[str, ...]
    plan_base_id: str
    plan_revision: str | None
    source_row: int
    profile_name: str | None


def _keyword_fields(package: PlanPackage) -> dict[str, str]:
    return {
        "package_name": normalize_search_value(package.package_name),
        "investor": normalize_search_value(package.investor),
        "project": normalize_search_value(package.project),
        "approval_content_raw": normalize_search_value(package.approval_content_raw),
    }


def evaluate_plan_package(package: PlanPackage, profile: FilterProfile) -> FilterEvaluation:
    matched = True
    reasons: list[FilterReasonCode] = []
    matched_fields: list[str] = []

    if profile.min_budget is not None or profile.max_budget is not None:
        if package.package_price is None:
            matched = False
            reasons.append(FilterReasonCode.PRICE_UNKNOWN)
        elif profile.min_budget is not None and package.package_price < profile.min_budget:
            matched = False
            reasons.append(FilterReasonCode.EXCLUDED_UNDER_MIN_BUDGET)
        elif profile.max_budget is not None and package.package_price > profile.max_budget:
            matched = False
            reasons.append(FilterReasonCode.EXCLUDED_OVER_MAX_BUDGET)
        else:
            reasons.append(FilterReasonCode.MATCH_BUDGET)

    if profile.province_city_codes:
        if (
            package.province_city_status is ProvinceCityStatus.NEEDS_REVIEW
            or package.province_city_code is None
        ):
            matched = False
            reasons.append(FilterReasonCode.PROVINCE_NEEDS_REVIEW)
        elif package.province_city_code.upper() not in profile.province_city_codes:
            matched = False
            reasons.append(FilterReasonCode.PROVINCE_NOT_MATCHED)
        else:
            reasons.append(FilterReasonCode.MATCH_PROVINCE)

    fields = _keyword_fields(package)
    include_terms = tuple(
        term for keyword in profile.include_keywords if (term := normalize_search_value(keyword))
    )
    if include_terms:
        include_matches = [
            field for field, value in fields.items() if any(term in value for term in include_terms)
        ]
        if include_matches:
            reasons.append(FilterReasonCode.MATCH_KEYWORD)
            matched_fields.extend(include_matches)
        else:
            matched = False
            reasons.append(FilterReasonCode.INCLUDE_KEYWORD_NOT_FOUND)

    exclude_terms = tuple(
        term for keyword in profile.exclude_keywords if (term := normalize_search_value(keyword))
    )
    exclude_matches = [
        field for field, value in fields.items() if any(term in value for term in exclude_terms)
    ]
    if exclude_matches:
        matched = False
        reasons.append(FilterReasonCode.EXCLUDE_KEYWORD_FOUND)
        matched_fields.extend(exclude_matches)

    if profile.selection_methods:
        if (package.selection_method or "").upper() in profile.selection_methods:
            reasons.append(FilterReasonCode.MATCH_SELECTION_METHOD)
        else:
            matched = False
            reasons.append(FilterReasonCode.SELECTION_METHOD_NOT_MATCHED)

    return FilterEvaluation(
        matched=matched,
        reasons=tuple(reasons),
        matched_fields=tuple(dict.fromkeys(matched_fields)),
        plan_base_id=package.plan.plan_base_id,
        plan_revision=package.plan.plan_revision,
        source_row=package.source_row,
        profile_name=profile.name,
    )
