from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from qi_crawler.market_intelligence.discovery import (
    BudgetBucketCode,
    DiscoveryInvariantError,
    build_discovery,
)
from qi_crawler.market_intelligence.khmt_contract import (
    ProvinceCityStatus,
    load_sanitized_khmt_fixture,
)

FIXTURE = Path(__file__).parent / "fixtures" / "khmt" / "khmt_sanitized_golden.json"


def _base_package():
    return load_sanitized_khmt_fixture(FIXTURE)[1][0]


def _package(
    source_row: int,
    *,
    price: Decimal | None = Decimal(100000000),
    code: str | None = "HCM",
    name: str | None = "Thành phố Hồ Chí Minh",
    status: ProvinceCityStatus = ProvinceCityStatus.CONFIRMED,
    method: str | None = "CHI_DINH_THAU_RUT_GON",
    revision: str = "00",
):
    base = _base_package()
    plan = replace(
        base.plan,
        plan_id_raw=f"PL-SYN-2026-001-{revision}",
        plan_revision=revision,
    )
    return replace(
        base,
        plan=plan,
        source_row=source_row,
        package_price=price,
        province_city_code=code,
        province_city_name=name,
        province_city_status=status,
        selection_method=method,
        provenance={
            "source_filename": base.plan.import_batch.source_filename,
            "source_sha256": base.plan.import_batch.source_sha256,
            "sheet": base.plan.import_batch.sheet,
            "source_row": source_row,
        },
    )


def test_empty_universe_is_valid_zero_snapshot() -> None:
    snapshot = build_discovery(())

    assert snapshot.total_packages == 0
    assert snapshot.province_city_buckets == ()
    assert snapshot.location_needs_review_count == 0
    assert snapshot.location_reconciled_count == 0
    assert snapshot.budget_reconciled_count == 0
    assert snapshot.selection_reconciled_count == 0


def test_location_buckets_preserve_status_rows_and_reconcile() -> None:
    packages = (
        _package(8, status=ProvinceCityStatus.CONFIRMED),
        _package(9, status=ProvinceCityStatus.INFERRED),
        _package(
            10,
            code="HN",
            name="Thành phố Hà Nội",
            status=ProvinceCityStatus.CONFIRMED,
        ),
        _package(
            11,
            code=None,
            name=None,
            status=ProvinceCityStatus.NEEDS_REVIEW,
        ),
    )

    snapshot = build_discovery(packages)
    buckets = {bucket.code: bucket for bucket in snapshot.province_city_buckets}

    assert snapshot.total_packages == 4
    assert buckets["HCM"].total == 2
    assert buckets["HCM"].confirmed == 1
    assert buckets["HCM"].inferred == 1
    assert buckets["HN"].total == 1
    assert snapshot.location_needs_review_count == 1
    assert snapshot.location_reconciled_count == snapshot.total_packages


def test_plan_revisions_and_same_revision_rows_are_counted_as_packages() -> None:
    packages = (_package(8, revision="00"), _package(9, revision="00"), _package(14, revision="01"))

    snapshot = build_discovery(packages)

    assert snapshot.total_packages == 3
    assert snapshot.province_city_buckets[0].total == 3


@pytest.mark.parametrize(
    ("price", "expected"),
    [
        (Decimal(0), BudgetBucketCode.UNDER_OR_EQUAL_100M),
        (Decimal(100000000), BudgetBucketCode.UNDER_OR_EQUAL_100M),
        (Decimal(100000001), BudgetBucketCode.FROM_100M_TO_300M),
        (Decimal(300000000), BudgetBucketCode.FROM_100M_TO_300M),
        (Decimal(300000001), BudgetBucketCode.FROM_300M_TO_500M),
        (Decimal(500000000), BudgetBucketCode.FROM_300M_TO_500M),
        (Decimal(500000001), BudgetBucketCode.FROM_500M_TO_1B),
        (Decimal(1000000000), BudgetBucketCode.FROM_500M_TO_1B),
        (Decimal(1000000001), BudgetBucketCode.OVER_1B),
        (None, BudgetBucketCode.UNKNOWN_PRICE),
    ],
)
def test_budget_boundaries_are_exclusive_exhaustive(
    price: Decimal | None, expected: BudgetBucketCode
) -> None:
    snapshot = build_discovery((_package(1, price=price),))
    counts = {bucket.code: bucket.count for bucket in snapshot.budget_buckets}

    assert counts[expected] == 1
    assert sum(counts.values()) == 1
    assert snapshot.budget_reconciled_count == snapshot.total_packages


def test_budget_and_selection_buckets_reconcile_without_fabricating_unknowns() -> None:
    packages = (
        _package(1, price=Decimal(100000000), method="CHI_DINH_THAU_RUT_GON"),
        _package(2, price=Decimal(300000000), method="CHAO_HANG_CANH_TRANH"),
        _package(3, price=None, method=None),
    )

    snapshot = build_discovery(packages)
    methods = {
        bucket.selection_method: bucket.count for bucket in snapshot.selection_method_buckets
    }

    assert snapshot.unknown_price_count == 1
    assert snapshot.budget_reconciled_count == 3
    assert methods["CHI_DINH_THAU_RUT_GON"] == 1
    assert methods["CHAO_HANG_CANH_TRANH"] == 1
    assert snapshot.unsupported_selection_count == 1
    assert snapshot.selection_reconciled_count == 3


def test_resolved_status_without_identity_fails_clearly() -> None:
    invalid = _package(
        1,
        code=None,
        name=None,
        status=ProvinceCityStatus.CONFIRMED,
    )

    with pytest.raises(DiscoveryInvariantError, match="resolved province"):
        build_discovery((invalid,))
