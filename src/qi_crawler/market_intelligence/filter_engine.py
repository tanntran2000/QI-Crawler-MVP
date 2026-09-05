"""Explainable deterministic filtering for normalized KHMT packages."""

from __future__ import annotations

import re
import unicodedata
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
    UNFILTERED = "UNFILTERED"


@dataclass(frozen=True, slots=True)
class FilterProfile:
    name: str | None = None
    min_budget: Decimal | None = None
    max_budget: Decimal | None = None
    province_city_codes: frozenset[str] = frozenset()
    include_keywords: tuple[str, ...] = ()
    exclude_keywords: tuple[str, ...] = ()
    selection_methods: frozenset[str] = frozenset()
    literal_find: bool = False

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

    @property
    def has_active_criteria(self) -> bool:
        """Return whether this profile contains at least one effective filter."""

        return any(
            (
                self.min_budget is not None,
                self.max_budget is not None,
                bool(self.province_city_codes),
                any(normalize_search_value(keyword) for keyword in self.include_keywords),
                any(normalize_search_value(keyword) for keyword in self.exclude_keywords),
                any(str(method).strip() for method in self.selection_methods),
            )
        )


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
class CriterionEvidence:
    """One deterministic, source-neutral observation for a filter criterion."""

    field: str | None
    observed_value: str | None
    expected_values: tuple[str, ...] = ()
    matched_terms: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CriterionEvaluation:
    criterion: str
    outcome: CriterionOutcome
    reason_code: FilterReasonCode
    matched_fields: tuple[str, ...] = ()
    evidence: tuple[CriterionEvidence, ...] = ()


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


_NON_BUSINESS_FIELD_NAMES = {
    "source_sha256",
    "observation_key",
    "source_row",
    "sheet",
    "schema_version",
    "source_filename",
    "source_type",
    "provenance",
}


def normalize_literal_find(value: object) -> str:
    """Normalize Find text without removing accents or changing characters."""

    if value is None:
        return ""
    text = unicodedata.normalize("NFC", str(value))
    return re.sub(r"\s+", " ", text).casefold().strip()


def _is_business_field_name(name: object) -> bool:
    key = str(name).strip()
    lowered = key.casefold()
    if not key or lowered in _NON_BUSINESS_FIELD_NAMES:
        return False
    if "sha" in lowered or "observation" in lowered or "diagnostic" in lowered:
        return False
    return not (
        lowered.endswith("_id") or lowered in {"id", "raw_id", "base_id", "revision"}
    )


def searchable_business_fields(item: OpportunityRadarItem) -> dict[str, str | None]:
    """Return deterministic, user-facing source fields eligible for generic Find."""

    fields: dict[str, str | None] = {"raw_tender_id": _optional_text(item.identity.raw_id)}
    explicit = (
        ("package_name", item.package_name),
        ("project", item.project),
        ("investor", item.investor),
        ("procuring_entity", item.procuring_entity),
        ("approval_content", item.approval_content),
        ("package_main_content", item.package_main_content),
        ("selection_method_raw", item.selection_method_raw),
        ("location_detail_raw", item.location_detail_raw),
        ("province_city_name", item.province_city_name),
        ("province_city_evidence", item.province_city_evidence),
    )
    for label, value in explicit:
        text = _optional_text(value)
        if label not in fields and text is not None:
            fields[label] = text
    for mapping in (item.source_fields, item.raw_fields):
        for label, value in mapping.items():
            if not _is_business_field_name(label) or not isinstance(value, str):
                continue
            text = _optional_text(value)
            if label not in fields and text is not None:
                fields[label] = text
    return fields


def _decimal_text(value: Decimal) -> str:
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _budget_evidence(
    profile: FilterProfile, price: Decimal | None
) -> tuple[CriterionEvidence, ...]:
    expected: list[str] = []
    if profile.min_budget is not None:
        expected.append(f"min={profile.min_budget}")
    if profile.max_budget is not None:
        expected.append(f"max={profile.max_budget}")
    return (
        CriterionEvidence(
            field="package_price",
            observed_value=_decimal_text(price) if price is not None else None,
            expected_values=tuple(expected),
        ),
    )


def _province_evidence(
    item: OpportunityRadarItem, profile: FilterProfile
) -> tuple[CriterionEvidence, ...]:
    observed = _optional_text(item.province_city_code)
    return (
        CriterionEvidence(
            field="province_city_code",
            observed_value=observed.upper() if observed is not None else None,
            expected_values=tuple(sorted(profile.province_city_codes)),
        ),
    )


def _keyword_evidence(
    fields: dict[str, str | None], terms: tuple[str, ...], *, literal: bool = False
) -> tuple[CriterionEvidence, ...]:
    normalize = normalize_literal_find if literal else normalize_search_value
    entries: list[CriterionEvidence] = []
    for field, value in fields.items():
        normalized = normalize(value) if value is not None else None
        matched_terms = tuple(
            normalize_search_value(term) if literal else term
            for term in terms
            if normalized is not None
            and (normalize_literal_find(term) if literal else term) in normalized
        )
        if matched_terms or value is None:
            entries.append(
                CriterionEvidence(
                    field=field,
                    observed_value=value,
                    expected_values=terms,
                    matched_terms=matched_terms,
                )
            )
    if not entries:
        entries = [
            CriterionEvidence(
                field=field,
                observed_value=value,
                expected_values=terms,
            )
            for field, value in fields.items()
        ]
    return tuple(entries)


def _selection_evidence(
    item: OpportunityRadarItem, profile: FilterProfile, method: str | None
) -> tuple[CriterionEvidence, ...]:
    expected = tuple(sorted(profile.selection_methods))
    if method is not None:
        return (
            CriterionEvidence(
                field="selection_method",
                observed_value=method.upper(),
                expected_values=expected,
            ),
        )
    raw = _optional_text(getattr(item, "selection_method_raw", None))
    return (
        CriterionEvidence(
            field="selection_method_raw" if raw is not None else "selection_method",
            observed_value=raw,
            expected_values=expected,
        ),
    )


def _criterion(
    name: str,
    outcome: CriterionOutcome,
    reason: FilterReasonCode,
    *,
    matched_fields: tuple[str, ...] = (),
    evidence: tuple[CriterionEvidence, ...] = (),
) -> CriterionEvaluation:
    return CriterionEvaluation(
        criterion=name,
        outcome=outcome,
        reason_code=reason,
        matched_fields=matched_fields,
        evidence=evidence,
    )


def evaluate_opportunity(
    item: OpportunityRadarItem, profile: FilterProfile
) -> OpportunityFilterEvaluation:
    """Evaluate one source-neutral opportunity without scoring or side effects."""

    if not profile.has_active_criteria:
        return OpportunityFilterEvaluation(
            observation_key=item.observation_key,
            identity=item.identity,
            disposition=OpportunityFilterDisposition.UNFILTERED,
            criteria=(),
            matched_fields=(),
            profile_name=profile.name,
        )

    criteria: list[CriterionEvaluation] = []
    matched_fields: list[str] = []

    if profile.min_budget is not None or profile.max_budget is not None:
        price = _finite_price(item.package_price)
        budget_evidence = _budget_evidence(profile, price)
        if price is None:
            criteria.append(
                _criterion(
                    "budget",
                    CriterionOutcome.UNKNOWN,
                    FilterReasonCode.BUDGET_UNKNOWN,
                    evidence=budget_evidence,
                )
            )
        elif profile.min_budget is not None and price < profile.min_budget:
            criteria.append(
                _criterion(
                    "budget",
                    CriterionOutcome.FAIL,
                    FilterReasonCode.BUDGET_BELOW_MIN,
                    evidence=budget_evidence,
                )
            )
        elif profile.max_budget is not None and price > profile.max_budget:
            criteria.append(
                _criterion(
                    "budget",
                    CriterionOutcome.FAIL,
                    FilterReasonCode.BUDGET_ABOVE_MAX,
                    evidence=budget_evidence,
                )
            )
        else:
            criteria.append(
                _criterion(
                    "budget",
                    CriterionOutcome.PASS,
                    FilterReasonCode.BUDGET_MATCH,
                    evidence=budget_evidence,
                )
            )

    if profile.province_city_codes:
        province_evidence = _province_evidence(item, profile)
        if item.province_city_status is ProvinceCityStatus.NEEDS_REVIEW:
            criteria.append(
                _criterion(
                    "province_city",
                    CriterionOutcome.UNKNOWN,
                    FilterReasonCode.LOCATION_NEEDS_REVIEW,
                    evidence=province_evidence,
                )
            )
        elif not item.province_city_code:
            criteria.append(
                _criterion(
                    "province_city",
                    CriterionOutcome.UNKNOWN,
                    FilterReasonCode.LOCATION_UNKNOWN,
                    evidence=province_evidence,
                )
            )
        elif item.province_city_code.upper() in profile.province_city_codes:
            criteria.append(
                _criterion(
                    "province_city",
                    CriterionOutcome.PASS,
                    FilterReasonCode.LOCATION_MATCH,
                    evidence=province_evidence,
                )
            )
        else:
            criteria.append(
                _criterion(
                    "province_city",
                    CriterionOutcome.FAIL,
                    FilterReasonCode.LOCATION_NOT_MATCHED,
                    evidence=province_evidence,
                )
            )

    literal_find = profile.literal_find
    fields = searchable_business_fields(item) if literal_find else _opportunity_keyword_fields(item)
    include_terms = tuple(
        term
        for keyword in profile.include_keywords
        if (
            term := (normalize_literal_find(keyword) if literal_find else normalize_search_value(keyword))
        )
    )
    if include_terms:
        include_evidence = _keyword_evidence(fields, include_terms, literal=literal_find)
        include_matches = tuple(
            entry.field
            for entry in include_evidence
            if entry.matched_terms and entry.field is not None
        )
        if include_matches:
            matched_fields.extend(include_matches)
            criteria.append(
                _criterion(
                    "include_keywords",
                    CriterionOutcome.PASS,
                    FilterReasonCode.INCLUDE_KEYWORD_MATCH,
                    matched_fields=include_matches,
                    evidence=include_evidence,
                )
            )
        elif any(value is None for value in fields.values()):
            criteria.append(
                _criterion(
                    "include_keywords",
                    CriterionOutcome.UNKNOWN,
                    FilterReasonCode.INCLUDE_KEYWORD_INDETERMINATE,
                    evidence=include_evidence,
                )
            )
        else:
            criteria.append(
                _criterion(
                    "include_keywords",
                    CriterionOutcome.FAIL,
                    FilterReasonCode.INCLUDE_KEYWORD_NOT_FOUND,
                    evidence=include_evidence,
                )
            )

    exclude_terms = tuple(
        term
        for keyword in profile.exclude_keywords
        if (
            term := (normalize_literal_find(keyword) if literal_find else normalize_search_value(keyword))
        )
    )
    if exclude_terms:
        exclude_evidence = _keyword_evidence(fields, exclude_terms, literal=literal_find)
        exclude_matches = tuple(
            entry.field
            for entry in exclude_evidence
            if entry.matched_terms and entry.field is not None
        )
        if exclude_matches:
            matched_fields.extend(exclude_matches)
            criteria.append(
                _criterion(
                    "exclude_keywords",
                    CriterionOutcome.FAIL,
                    FilterReasonCode.EXCLUDE_KEYWORD_FOUND,
                    matched_fields=exclude_matches,
                    evidence=exclude_evidence,
                )
            )
        elif any(value is None for value in fields.values()):
            criteria.append(
                _criterion(
                    "exclude_keywords",
                    CriterionOutcome.UNKNOWN,
                    FilterReasonCode.EXCLUDE_KEYWORD_INDETERMINATE,
                    evidence=exclude_evidence,
                )
            )
        else:
            criteria.append(
                _criterion(
                    "exclude_keywords",
                    CriterionOutcome.PASS,
                    FilterReasonCode.EXCLUDE_KEYWORD_NOT_FOUND,
                    evidence=exclude_evidence,
                )
            )

    if profile.selection_methods:
        method = _optional_text(item.selection_method)
        selection_evidence = _selection_evidence(item, profile, method)
        if method is None:
            criteria.append(
                _criterion(
                    "selection_method",
                    CriterionOutcome.UNKNOWN,
                    FilterReasonCode.SELECTION_METHOD_UNKNOWN,
                    evidence=selection_evidence,
                )
            )
        elif method.upper() in profile.selection_methods:
            criteria.append(
                _criterion(
                    "selection_method",
                    CriterionOutcome.PASS,
                    FilterReasonCode.SELECTION_METHOD_MATCH,
                    evidence=selection_evidence,
                )
            )
        else:
            criteria.append(
                _criterion(
                    "selection_method",
                    CriterionOutcome.FAIL,
                    FilterReasonCode.SELECTION_METHOD_NOT_MATCHED,
                    evidence=selection_evidence,
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
    legacy_exclude_unknown = any(
        criterion.reason_code is FilterReasonCode.EXCLUDE_KEYWORD_INDETERMINATE
        for criterion in generic.criteria
    )
    other_unknown = any(
        criterion.outcome is CriterionOutcome.UNKNOWN
        and criterion.reason_code is not FilterReasonCode.EXCLUDE_KEYWORD_INDETERMINATE
        for criterion in generic.criteria
    )
    reasons = [
        reason
        for criterion in generic.criteria
        if (reason := _legacy_reason(criterion)) is not None
    ]
    return FilterEvaluation(
        matched=(
            generic.disposition
            in (
                OpportunityFilterDisposition.MATCH,
                OpportunityFilterDisposition.UNFILTERED,
            )
            or (
                generic.disposition is OpportunityFilterDisposition.INDETERMINATE
                and legacy_exclude_unknown
                and not other_unknown
            )
        ),
        reasons=tuple(reasons),
        matched_fields=generic.matched_fields,
        plan_base_id=package.plan.plan_base_id,
        plan_revision=package.plan.plan_revision,
        source_row=package.source_row,
        profile_name=profile.name,
    )
