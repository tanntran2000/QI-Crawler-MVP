"""Targeted KHMT search that delegates all matching to the MI-1 filter engine."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from .filter_engine import (
    FilterEvaluation,
    FilterProfile,
    OpportunityFilterDisposition,
    OpportunityFilterEvaluation,
    evaluate_opportunity,
    evaluate_plan_package,
)
from .khmt_contract import PlanPackage
from .khmt_normalization import normalize_search_value
from .opportunity_radar import OpportunityRadarItem


class TargetedSearchValidationError(ValueError):
    """Raised when a caller supplies an invalid search contract."""


@dataclass(frozen=True, slots=True)
class TargetedSearchRequest:
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
            frozenset(code.upper() for code in self.province_city_codes),
        )
        object.__setattr__(
            self,
            "selection_methods",
            frozenset(method.upper() for method in self.selection_methods),
        )
        object.__setattr__(
            self,
            "include_keywords",
            tuple(
                normalized
                for keyword in self.include_keywords
                if (normalized := normalize_search_value(keyword))
            ),
        )
        object.__setattr__(
            self,
            "exclude_keywords",
            tuple(
                normalized
                for keyword in self.exclude_keywords
                if (normalized := normalize_search_value(keyword))
            ),
        )

    def to_filter_profile(self) -> FilterProfile:
        if self.min_budget is not None and self.min_budget < 0:
            raise TargetedSearchValidationError("min_budget cannot be negative")
        if self.max_budget is not None and self.max_budget < 0:
            raise TargetedSearchValidationError("max_budget cannot be negative")
        if (
            self.min_budget is not None
            and self.max_budget is not None
            and self.min_budget > self.max_budget
        ):
            raise TargetedSearchValidationError("min_budget cannot exceed max_budget")
        return FilterProfile(
            name=self.name,
            min_budget=self.min_budget,
            max_budget=self.max_budget,
            province_city_codes=self.province_city_codes,
            include_keywords=self.include_keywords,
            exclude_keywords=self.exclude_keywords,
            selection_methods=self.selection_methods,
        )


@dataclass(frozen=True, slots=True)
class SearchEvaluation:
    package: PlanPackage
    evaluation: FilterEvaluation


@dataclass(frozen=True, slots=True)
class TargetedSearchResult:
    request: TargetedSearchRequest
    total_examined: int
    matched_count: int
    nonmatched_count: int
    hits: tuple[SearchEvaluation, ...]
    evaluated: tuple[SearchEvaluation, ...]


@dataclass(frozen=True, slots=True)
class OpportunitySearchEvaluation:
    item: OpportunityRadarItem
    evaluation: OpportunityFilterEvaluation


@dataclass(frozen=True, slots=True)
class TargetedOpportunitySearchResult:
    request: TargetedSearchRequest
    total_examined: int
    matched_count: int
    indeterminate_count: int
    nonmatched_count: int
    matches: tuple[OpportunitySearchEvaluation, ...]
    indeterminate: tuple[OpportunitySearchEvaluation, ...]
    nonmatches: tuple[OpportunitySearchEvaluation, ...]
    evaluated: tuple[OpportunitySearchEvaluation, ...]


def search_opportunities(
    items: Iterable[OpportunityRadarItem], request: TargetedSearchRequest
) -> TargetedOpportunitySearchResult:
    """Evaluate source-neutral radar items in stable order and bucket outcomes."""

    profile = request.to_filter_profile()
    evaluated = tuple(
        OpportunitySearchEvaluation(item=item, evaluation=evaluate_opportunity(item, profile))
        for item in tuple(items)
    )
    matches = tuple(
        result
        for result in evaluated
        if result.evaluation.disposition is OpportunityFilterDisposition.MATCH
    )
    indeterminate = tuple(
        result
        for result in evaluated
        if result.evaluation.disposition is OpportunityFilterDisposition.INDETERMINATE
    )
    nonmatches = tuple(
        result
        for result in evaluated
        if result.evaluation.disposition is OpportunityFilterDisposition.NO_MATCH
    )
    return TargetedOpportunitySearchResult(
        request=request,
        total_examined=len(evaluated),
        matched_count=len(matches),
        indeterminate_count=len(indeterminate),
        nonmatched_count=len(nonmatches),
        matches=matches,
        indeterminate=indeterminate,
        nonmatches=nonmatches,
        evaluated=evaluated,
    )


def search_packages(
    packages: Iterable[PlanPackage], request: TargetedSearchRequest
) -> TargetedSearchResult:
    """Evaluate every package in stable input order through the MI-1 authority."""

    profile = request.to_filter_profile()
    universe = tuple(packages)
    evaluated = tuple(
        SearchEvaluation(
            package=package,
            evaluation=evaluate_plan_package(package, profile),
        )
        for package in universe
    )
    hits = tuple(item for item in evaluated if item.evaluation.matched)
    return TargetedSearchResult(
        request=request,
        total_examined=len(evaluated),
        matched_count=len(hits),
        nonmatched_count=len(evaluated) - len(hits),
        hits=hits,
        evaluated=evaluated,
    )
