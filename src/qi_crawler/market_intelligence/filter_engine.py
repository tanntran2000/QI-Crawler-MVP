"""Explainable deterministic filtering for normalized KHMT packages."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from types import SimpleNamespace

from .khmt_contract import PlanPackage, ProvinceCityStatus
from .khmt_normalization import normalize_search_value
from .opportunity_contract import OpportunitySourceType
from .opportunity_radar import OpportunityRadarItem


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
    INCLUDE_KEYWORD_MATCH = "INCLUDE_KEYWORD_MATCH"
    INCLUDE_KEYWORD_INDETERMINATE = "INCLUDE_KEYWORD_INDETERMINATE"
    EXCLUDE_KEYWORD_FOUND = "EXCLUDE_KEYWORD_FOUND"
    EXCLUDE_KEYWORD_NOT_FOUND = "EXCLUDE_KEYWORD_NOT_FOUND"
    EXCLUDE_KEYWORD_INDETERMINATE = "EXCLUDE_KEYWORD_INDETERMINATE"
    SELECTION_METHOD_NOT_MATCHED = "SELECTION_METHOD_NOT_MATCHED"
    BUDGET_MATCH = "BUDGET_MATCH"
    BUDGET_BELOW_MIN = "BUDGET_BELOW_MIN"
    BUDGET_ABOVE_MAX = "BUDGET_ABOVE_MAX"
    BUDGET_UNKNOWN = "BUDGET_UNKNOWN"
    LOCATION_MATCH = "LOCATION_MATCH"
    LOCATION_NOT_MATCHED = "LOCATION_NOT_MATCHED"
    LOCATION_UNKNOWN = "LOCATION_UNKNOWN"
    LOCATION_NEEDS_REVIEW = "LOCATION_NEEDS_REVIEW"
    SELECTION_METHOD_MATCH = "SELECTION_METHOD_MATCH"
    SELECTION_METHOD_UNKNOWN = "SELECTION_METHOD_UNKNOWN"


class CriterionOutcome(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class OpportunityFilterDisposition(StrEnum):
    MATCH = "MATCH"
    NO_MATCH = "NO_MATCH"
    INDETERMINATE = "INDETERMINATE"


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


@dataclass(frozen=True, slots=True)
class CriterionEvaluation:
    criterion: str
    outcome: CriterionOutcome
    reason_code: FilterReasonCode
    matched_fields: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class OpportunityFilterEvaluation:
    observation_key: str
    identity: object
    disposition: OpportunityFilterDisposition
    criteria: tuple[CriterionEvaluation, ...]
    matched_fields: tuple[str, ...]
    profile_name: str | None


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _finite_price(value: object) -> Decimal | None:
    if value is None:
        return None
    try:
        price = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return price if price.is_finite() else None


def _opportunity_keyword_fields(item: OpportunityRadarItem) -> dict[str, str | None]:
    fields: dict[str, str | None] = {
        "package_name": _optional_text(item.package_name),
        "project": _optional_text(item.project),
    }
    if item.source_type is OpportunitySourceType.KHMT:
        fields.update(
            {
                "investor": _optional_text(item.investor),
                "approval_content": _optional_text(item.approval_content),
            }
        )
    else:
        fields.update(
            {
                "procuring_entity": _optional_text(item.procuring_entity),
                "package_main_content": _optional_text(item.package_main_content),
            }
        )
    return fields


def _criterion(
    name: str,
    outcome: CriterionOutcome,
    reason: FilterReasonCode,
    *,
    matched_fields: tuple[str, ...] = (),
) -> CriterionEvaluation:
    return CriterionEvaluation(
        criterion=name,
        outcome=outcome,
        reason_code=reason,
        matched_fields=matched_fields,
    )


def evaluate_opportunity(
    item: OpportunityRadarItem, profile: FilterProfile
) -> OpportunityFilterEvaluation:
    """Evaluate one source-neutral opportunity without scoring or side effects."""

    criteria: list[CriterionEvaluation] = []
    matched_fields: list[str] = []

    if profile.min_budget is not None or profile.max_budget is not None:
        price = _finite_price(item.package_price)
        if price is None:
            criteria.append(
                _criterion("budget", CriterionOutcome.UNKNOWN, FilterReasonCode.BUDGET_UNKNOWN)
            )
        elif profile.min_budget is not None and price < profile.min_budget:
            criteria.append(
                _criterion("budget", CriterionOutcome.FAIL, FilterReasonCode.BUDGET_BELOW_MIN)
            )
        elif profile.max_budget is not None and price > profile.max_budget:
            criteria.append(
                _criterion("budget", CriterionOutcome.FAIL, FilterReasonCode.BUDGET_ABOVE_MAX)
            )
        else:
            criteria.append(
                _criterion("budget", CriterionOutcome.PASS, FilterReasonCode.BUDGET_MATCH)
            )

    if profile.province_city_codes:
        if item.province_city_status is ProvinceCityStatus.NEEDS_REVIEW:
            criteria.append(
                _criterion(
                    "province_city",
                    CriterionOutcome.UNKNOWN,
                    FilterReasonCode.LOCATION_NEEDS_REVIEW,
                )
            )
        elif not item.province_city_code:
            criteria.append(
                _criterion(
                    "province_city",
                    CriterionOutcome.UNKNOWN,
                    FilterReasonCode.LOCATION_UNKNOWN,
                )
            )
        elif item.province_city_code.upper() in profile.province_city_codes:
            criteria.append(
                _criterion("province_city", CriterionOutcome.PASS, FilterReasonCode.LOCATION_MATCH)
            )
        else:
            criteria.append(
                _criterion(
                    "province_city",
                    CriterionOutcome.FAIL,
                    FilterReasonCode.LOCATION_NOT_MATCHED,
                )
            )

    fields = _opportunity_keyword_fields(item)
    include_terms = tuple(
        term for keyword in profile.include_keywords if (term := normalize_search_value(keyword))
    )
    if include_terms:
        include_matches = tuple(
            field
            for field, value in fields.items()
            if value is not None
            and any(term in normalize_search_value(value) for term in include_terms)
        )
        if include_matches:
            matched_fields.extend(include_matches)
            criteria.append(
                _criterion(
                    "include_keywords",
                    CriterionOutcome.PASS,
                    FilterReasonCode.INCLUDE_KEYWORD_MATCH,
                    matched_fields=include_matches,
                )
            )
        elif any(value is None for value in fields.values()):
            criteria.append(
                _criterion(
                    "include_keywords",
                    CriterionOutcome.UNKNOWN,
                    FilterReasonCode.INCLUDE_KEYWORD_INDETERMINATE,
                )
            )
        else:
            criteria.append(
                _criterion(
                    "include_keywords",
                    CriterionOutcome.FAIL,
                    FilterReasonCode.INCLUDE_KEYWORD_NOT_FOUND,
                )
            )

    exclude_terms = tuple(
        term for keyword in profile.exclude_keywords if (term := normalize_search_value(keyword))
    )
    if exclude_terms:
        exclude_matches = tuple(
            field
            for field, value in fields.items()
            if value is not None
            and any(term in normalize_search_value(value) for term in exclude_terms)
        )
        if exclude_matches:
            matched_fields.extend(exclude_matches)
            criteria.append(
                _criterion(
                    "exclude_keywords",
                    CriterionOutcome.FAIL,
                    FilterReasonCode.EXCLUDE_KEYWORD_FOUND,
                    matched_fields=exclude_matches,
                )
            )
        elif any(value is None for value in fields.values()):
            criteria.append(
                _criterion(
                    "exclude_keywords",
                    CriterionOutcome.UNKNOWN,
                    FilterReasonCode.EXCLUDE_KEYWORD_INDETERMINATE,
                )
            )
        else:
            criteria.append(
                _criterion(
                    "exclude_keywords",
                    CriterionOutcome.PASS,
                    FilterReasonCode.EXCLUDE_KEYWORD_NOT_FOUND,
                )
            )

    if profile.selection_methods:
        method = _optional_text(item.selection_method)
        if method is None:
            criteria.append(
                _criterion(
                    "selection_method",
                    CriterionOutcome.UNKNOWN,
                    FilterReasonCode.SELECTION_METHOD_UNKNOWN,
                )
            )
        elif method.upper() in profile.selection_methods:
            criteria.append(
                _criterion(
                    "selection_method",
                    CriterionOutcome.PASS,
                    FilterReasonCode.SELECTION_METHOD_MATCH,
                )
            )
        else:
            criteria.append(
                _criterion(
                    "selection_method",
                    CriterionOutcome.FAIL,
                    FilterReasonCode.SELECTION_METHOD_NOT_MATCHED,
                )
            )

    outcomes = {criterion.outcome for criterion in criteria}
    if CriterionOutcome.FAIL in outcomes:
        disposition = OpportunityFilterDisposition.NO_MATCH
    elif CriterionOutcome.UNKNOWN in outcomes:
        disposition = OpportunityFilterDisposition.INDETERMINATE
    else:
        disposition = OpportunityFilterDisposition.MATCH
    return OpportunityFilterEvaluation(
        observation_key=item.observation_key,
        identity=item.identity,
        disposition=disposition,
        criteria=tuple(criteria),
        matched_fields=tuple(dict.fromkeys(matched_fields)),
        profile_name=profile.name,
    )


def _legacy_reason(criterion: CriterionEvaluation) -> FilterReasonCode | None:
    return {
        FilterReasonCode.BUDGET_MATCH: FilterReasonCode.MATCH_BUDGET,
        FilterReasonCode.BUDGET_BELOW_MIN: FilterReasonCode.EXCLUDED_UNDER_MIN_BUDGET,
        FilterReasonCode.BUDGET_ABOVE_MAX: FilterReasonCode.EXCLUDED_OVER_MAX_BUDGET,
        FilterReasonCode.BUDGET_UNKNOWN: FilterReasonCode.PRICE_UNKNOWN,
        FilterReasonCode.LOCATION_MATCH: FilterReasonCode.MATCH_PROVINCE,
        FilterReasonCode.LOCATION_NOT_MATCHED: FilterReasonCode.PROVINCE_NOT_MATCHED,
        FilterReasonCode.LOCATION_UNKNOWN: FilterReasonCode.PROVINCE_NEEDS_REVIEW,
        FilterReasonCode.LOCATION_NEEDS_REVIEW: FilterReasonCode.PROVINCE_NEEDS_REVIEW,
        FilterReasonCode.INCLUDE_KEYWORD_MATCH: FilterReasonCode.MATCH_KEYWORD,
        FilterReasonCode.INCLUDE_KEYWORD_NOT_FOUND: FilterReasonCode.INCLUDE_KEYWORD_NOT_FOUND,
        FilterReasonCode.INCLUDE_KEYWORD_INDETERMINATE: FilterReasonCode.INCLUDE_KEYWORD_NOT_FOUND,
        FilterReasonCode.EXCLUDE_KEYWORD_FOUND: FilterReasonCode.EXCLUDE_KEYWORD_FOUND,
        FilterReasonCode.SELECTION_METHOD_MATCH: FilterReasonCode.MATCH_SELECTION_METHOD,
        FilterReasonCode.SELECTION_METHOD_NOT_MATCHED: FilterReasonCode.SELECTION_METHOD_NOT_MATCHED,
        FilterReasonCode.SELECTION_METHOD_UNKNOWN: FilterReasonCode.SELECTION_METHOD_NOT_MATCHED,
    }.get(criterion.reason_code)


def _legacy_plan_package_observation(package: PlanPackage) -> SimpleNamespace:
    """Adapt legacy KHMT packages without imposing the radar identity parser.

    MI-1 fixtures and callers may use their own source identity spelling.  The
    source-neutral evaluator only needs the semantic fields here; strict radar
    identity/provenance validation remains owned by ``OpportunityRadarItem``.
    """

    identity = SimpleNamespace(
        raw_id=package.plan.plan_id_raw,
        base_id=package.plan.plan_base_id,
        revision=package.plan.plan_revision,
        namespace="PL",
    )
    return SimpleNamespace(
        source_type=OpportunitySourceType.KHMT,
        identity=identity,
        observation_key=(
            f"legacy:{package.plan.plan_id_raw}:{package.source_row}"
        ),
        package_name=package.package_name,
        project=package.project,
        package_price=package.package_price,
        investor=package.investor,
        approval_content=package.approval_content_raw,
        procuring_entity=None,
        package_main_content=None,
        selection_method=package.selection_method,
        province_city_code=package.province_city_code,
        province_city_status=package.province_city_status,
    )


def evaluate_plan_package(package: PlanPackage, profile: FilterProfile) -> FilterEvaluation:
    generic = evaluate_opportunity(_legacy_plan_package_observation(package), profile)
    reasons = [
        reason
        for criterion in generic.criteria
        if (reason := _legacy_reason(criterion)) is not None
    ]
    return FilterEvaluation(
        matched=generic.disposition is OpportunityFilterDisposition.MATCH,
        reasons=tuple(reasons),
        matched_fields=generic.matched_fields,
        plan_base_id=package.plan.plan_base_id,
        plan_revision=package.plan.plan_revision,
        source_row=package.source_row,
        profile_name=profile.name,
    )
