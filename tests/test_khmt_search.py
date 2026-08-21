from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from qi_crawler.market_intelligence.filter_engine import FilterReasonCode
from qi_crawler.market_intelligence.khmt_contract import (
    ProvinceCityStatus,
    load_sanitized_khmt_fixture,
)
from qi_crawler.market_intelligence.search import (
    TargetedSearchRequest,
    TargetedSearchValidationError,
    search_packages,
)

FIXTURE = Path(__file__).parent / "fixtures" / "khmt" / "khmt_sanitized_golden.json"


def _base_package():
    return load_sanitized_khmt_fixture(FIXTURE)[1][0]


def _package(
    source_row: int,
    *,
    price: Decimal | None = Decimal(400000000),
    code: str | None = "HCM",
    name: str | None = "Thành phố Hồ Chí Minh",
    status: ProvinceCityStatus = ProvinceCityStatus.INFERRED,
    method: str | None = "CHI_DINH_THAU_RUT_GON",
    package_name: str = "Synthetic network package",
):
    base = _base_package()
    return replace(
        base,
        source_row=source_row,
        package_price=price,
        province_city_code=code,
        province_city_name=name,
        province_city_status=status,
        selection_method=method,
        package_name=package_name,
        provenance={
            "source_filename": base.plan.import_batch.source_filename,
            "source_sha256": base.plan.import_batch.source_sha256,
            "sheet": base.plan.import_batch.sheet,
            "source_row": source_row,
        },
    )


def test_no_filters_evaluates_and_matches_every_package_in_source_order() -> None:
    packages = (_package(9), _package(3), _package(14))

    result = search_packages(packages, TargetedSearchRequest())

    assert result.total_examined == 3
    assert result.matched_count == 3
    assert result.nonmatched_count == 0
    assert [hit.package.source_row for hit in result.hits] == [9, 3, 14]
    assert len(result.evaluated) == 3


@pytest.mark.parametrize(
    "search_request",
    [
        TargetedSearchRequest(min_budget=Decimal(-1)),
        TargetedSearchRequest(max_budget=Decimal(-1)),
        TargetedSearchRequest(min_budget=Decimal(2), max_budget=Decimal(1)),
    ],
)
def test_invalid_budget_request_is_rejected(
    search_request: TargetedSearchRequest,
) -> None:
    with pytest.raises(TargetedSearchValidationError):
        search_request.to_filter_profile()


def test_budget_range_reuses_filter_reasons_and_keeps_unknown_visible() -> None:
    packages = (
        _package(1, price=Decimal(300000000)),
        _package(2, price=Decimal(600000000)),
        _package(3, price=None),
    )
    request = TargetedSearchRequest(
        min_budget=Decimal(200000000),
        max_budget=Decimal(500000000),
    )

    result = search_packages(packages, request)

    assert result.matched_count == 1
    assert result.nonmatched_count == 2
    reasons = {item.package.source_row: item.evaluation.reasons for item in result.evaluated}
    assert FilterReasonCode.MATCH_BUDGET in reasons[1]
    assert FilterReasonCode.EXCLUDED_OVER_MAX_BUDGET in reasons[2]
    assert FilterReasonCode.PRICE_UNKNOWN in reasons[3]


def test_province_filters_multiple_codes_and_retains_needs_review_reason() -> None:
    packages = (
        _package(1, code="HCM", name="Thành phố Hồ Chí Minh"),
        _package(2, code="HN", name="Thành phố Hà Nội"),
        _package(3, code=None, name=None, status=ProvinceCityStatus.NEEDS_REVIEW),
    )

    result = search_packages(
        packages,
        TargetedSearchRequest(province_city_codes={"HCM", "HN"}),
    )

    assert result.matched_count == 2
    assert result.nonmatched_count == 1
    assert FilterReasonCode.PROVINCE_NEEDS_REVIEW in result.evaluated[2].evaluation.reasons


def test_keyword_and_exclusion_semantics_come_from_mi1_profile() -> None:
    packages = (
        _package(1, package_name="Cung cấp máy chủ"),
        _package(2, package_name="Cung cấp firewall restricted"),
        _package(3, package_name="Dịch vụ khác"),
    )
    request = TargetedSearchRequest(
        include_keywords=("máy chủ", "firewall"),
        exclude_keywords=("restricted",),
    )

    result = search_packages(packages, request)

    assert [hit.package.source_row for hit in result.hits] == [1]
    assert FilterReasonCode.EXCLUDE_KEYWORD_FOUND in result.evaluated[1].evaluation.reasons
    assert FilterReasonCode.INCLUDE_KEYWORD_NOT_FOUND in result.evaluated[2].evaluation.reasons


def test_unknown_method_is_evaluated_not_pre_dropped() -> None:
    result = search_packages(
        (_package(1, method=None),),
        TargetedSearchRequest(selection_methods={"CHI_DINH_THAU_RUT_GON"}),
    )

    assert result.total_examined == 1
    assert result.matched_count == 0
    assert result.nonmatched_count == 1
    assert FilterReasonCode.SELECTION_METHOD_NOT_MATCHED in result.evaluated[0].evaluation.reasons


def test_search_calls_mi1_evaluator_for_every_package(monkeypatch: pytest.MonkeyPatch) -> None:
    from qi_crawler.market_intelligence import search

    original = search.evaluate_plan_package
    calls: list[int] = []

    def tracked(package, profile):
        calls.append(package.source_row)
        return original(package, profile)

    monkeypatch.setattr(search, "evaluate_plan_package", tracked)
    packages = (_package(4), _package(2), _package(7))

    result = search.search_packages(packages, TargetedSearchRequest(max_budget=Decimal(500000000)))

    assert calls == [4, 2, 7]
    assert result.total_examined == result.matched_count + result.nonmatched_count


def test_repeated_search_is_deterministic_and_retains_provenance() -> None:
    packages = (_package(8), _package(9))
    request = TargetedSearchRequest(include_keywords=("network",))

    first = search_packages(packages, request)
    second = search_packages(packages, request)

    assert first == second
    assert first.hits[0].package.raw_fields is packages[0].raw_fields
    assert first.hits[0].package.provenance["source_sha256"] == (
        packages[0].plan.import_batch.source_sha256
    )


def test_golden_shape_profile_matches_three_and_explains_other_exclusions() -> None:
    packages = (
        _package(1),
        _package(2),
        _package(3),
        _package(4, code=None, name=None, status=ProvinceCityStatus.NEEDS_REVIEW),
        _package(5, price=Decimal(500000001)),
        _package(6, method="CHAO_HANG_CANH_TRANH"),
    )
    request = TargetedSearchRequest(
        max_budget=Decimal(500000000),
        province_city_codes={"HCM"},
        selection_methods={"CHI_DINH_THAU_RUT_GON"},
    )

    result = search_packages(packages, request)

    assert [hit.package.source_row for hit in result.hits] == [1, 2, 3]
    for hit in result.hits:
        assert hit.evaluation.reasons == (
            FilterReasonCode.MATCH_BUDGET,
            FilterReasonCode.MATCH_PROVINCE,
            FilterReasonCode.MATCH_SELECTION_METHOD,
        )
    excluded = {item.package.source_row: item.evaluation.reasons for item in result.evaluated}
    assert FilterReasonCode.PROVINCE_NEEDS_REVIEW in excluded[4]
    assert FilterReasonCode.EXCLUDED_OVER_MAX_BUDGET in excluded[5]
    assert FilterReasonCode.SELECTION_METHOD_NOT_MATCHED in excluded[6]
