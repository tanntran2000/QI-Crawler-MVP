from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from qi_crawler.market_intelligence.filter_engine import (
    FilterProfile,
    FilterReasonCode,
    evaluate_plan_package,
)
from qi_crawler.market_intelligence.khmt_contract import (
    ProvinceCityStatus,
    load_sanitized_khmt_fixture,
)

FIXTURE = Path(__file__).parent / "fixtures" / "khmt" / "khmt_sanitized_golden.json"


def _package():
    return load_sanitized_khmt_fixture(FIXTURE)[1][0]


@pytest.mark.parametrize(
    ("price", "profile", "matched", "reason"),
    [
        (Decimal(500), FilterProfile(max_budget=Decimal(500)), True, "MATCH_BUDGET"),
        (Decimal(500), FilterProfile(min_budget=Decimal(500)), True, "MATCH_BUDGET"),
        (
            Decimal(501),
            FilterProfile(max_budget=Decimal(500)),
            False,
            "EXCLUDED_OVER_MAX_BUDGET",
        ),
        (
            Decimal(499),
            FilterProfile(min_budget=Decimal(500)),
            False,
            "EXCLUDED_UNDER_MIN_BUDGET",
        ),
        (None, FilterProfile(max_budget=Decimal(500)), False, "PRICE_UNKNOWN"),
    ],
)
def test_budget_filter_is_inclusive_and_missing_is_not_zero(
    price: Decimal | None,
    profile: FilterProfile,
    matched: bool,
    reason: str,
) -> None:
    evaluation = evaluate_plan_package(replace(_package(), package_price=price), profile)

    assert evaluation.matched is matched
    assert FilterReasonCode(reason) in evaluation.reasons


def test_province_filter_matches_resolved_code_only() -> None:
    package = replace(
        _package(),
        province_city_code="HCM",
        province_city_name="Thành phố Hồ Chí Minh",
        province_city_status=ProvinceCityStatus.CONFIRMED,
    )

    matched = evaluate_plan_package(package, FilterProfile(province_city_codes={"HCM"}))
    missed = evaluate_plan_package(package, FilterProfile(province_city_codes={"HN"}))

    assert matched.matched is True
    assert FilterReasonCode.MATCH_PROVINCE in matched.reasons
    assert missed.matched is False
    assert FilterReasonCode.PROVINCE_NOT_MATCHED in missed.reasons


def test_unresolved_province_does_not_silently_match() -> None:
    package = replace(
        _package(),
        province_city_code=None,
        province_city_name=None,
        province_city_status=ProvinceCityStatus.NEEDS_REVIEW,
    )

    evaluation = evaluate_plan_package(package, FilterProfile(province_city_codes={"HCM"}))

    assert evaluation.matched is False
    assert evaluation.reasons == (FilterReasonCode.PROVINCE_NEEDS_REVIEW,)


def test_include_keyword_uses_any_semantics_and_reports_matched_field() -> None:
    package = replace(_package(), package_name="Cung cấp máy chủ cho Thành phố")

    evaluation = evaluate_plan_package(
        package,
        FilterProfile(include_keywords=("firewall", "may chu")),
    )

    assert evaluation.matched is True
    assert FilterReasonCode.MATCH_KEYWORD in evaluation.reasons
    assert "package_name" in evaluation.matched_fields


def test_include_keyword_miss_and_exclude_hit_are_explainable() -> None:
    package = replace(_package(), project="Synthetic restricted project")

    include_miss = evaluate_plan_package(package, FilterProfile(include_keywords=("fiber optic",)))
    excluded = evaluate_plan_package(package, FilterProfile(exclude_keywords=("restricted",)))

    assert include_miss.matched is False
    assert FilterReasonCode.INCLUDE_KEYWORD_NOT_FOUND in include_miss.reasons
    assert excluded.matched is False
    assert FilterReasonCode.EXCLUDE_KEYWORD_FOUND in excluded.reasons


def test_selection_method_matches_normalized_value_not_raw_spelling() -> None:
    package = replace(
        _package(),
        selection_method_raw="Chỉ định thầu rút gọn",
        selection_method="CHI_DINH_THAU_RUT_GON",
    )

    matched = evaluate_plan_package(
        package,
        FilterProfile(selection_methods={"CHI_DINH_THAU_RUT_GON"}),
    )
    missed = evaluate_plan_package(
        package,
        FilterProfile(selection_methods={"DAU_THAU_RONG_RAI"}),
    )

    assert matched.matched is True
    assert FilterReasonCode.MATCH_SELECTION_METHOD in matched.reasons
    assert missed.matched is False
    assert FilterReasonCode.SELECTION_METHOD_NOT_MATCHED in missed.reasons


def test_multiple_conditions_combine_deterministically_without_score() -> None:
    package = replace(
        _package(),
        package_price=Decimal(400000000),
        province_city_code="HCM",
        province_city_name="Thành phố Hồ Chí Minh",
        province_city_status=ProvinceCityStatus.CONFIRMED,
        selection_method="CHI_DINH_THAU_RUT_GON",
    )
    profile = FilterProfile(
        max_budget=Decimal(500000000),
        province_city_codes={"HCM"},
        include_keywords=("network",),
        selection_methods={"CHI_DINH_THAU_RUT_GON"},
    )

    evaluation = evaluate_plan_package(package, profile)

    assert evaluation.matched is True
    assert evaluation.reasons == (
        FilterReasonCode.MATCH_BUDGET,
        FilterReasonCode.MATCH_PROVINCE,
        FilterReasonCode.MATCH_KEYWORD,
        FilterReasonCode.MATCH_SELECTION_METHOD,
    )
    assert not hasattr(evaluation, "score")


def test_revisions_and_source_rows_remain_distinct_filter_results() -> None:
    _, packages = load_sanitized_khmt_fixture(FIXTURE)
    evaluations = [evaluate_plan_package(package, FilterProfile()) for package in packages]

    assert all(item.matched for item in evaluations)
    assert [(item.plan_revision, item.source_row) for item in evaluations] == [
        ("00", 8),
        ("00", 9),
        ("01", 14),
        ("00", 21),
    ]
