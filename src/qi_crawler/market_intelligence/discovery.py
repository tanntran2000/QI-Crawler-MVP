"""Descriptive, reconciled discovery buckets over normalized KHMT packages."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from .khmt_contract import PlanPackage, ProvinceCityStatus


class DiscoveryInvariantError(ValueError):
    """Raised when normalized package state cannot be classified safely."""


class BudgetBucketCode(StrEnum):
    UNDER_OR_EQUAL_100M = "UNDER_OR_EQUAL_100M"
    FROM_100M_TO_300M = "FROM_100M_TO_300M"
    FROM_300M_TO_500M = "FROM_300M_TO_500M"
    FROM_500M_TO_1B = "FROM_500M_TO_1B"
    OVER_1B = "OVER_1B"
    UNKNOWN_PRICE = "UNKNOWN_PRICE"


_BUDGET_ORDER = tuple(BudgetBucketCode)
_HUNDRED_MILLION = Decimal(100000000)
_THREE_HUNDRED_MILLION = Decimal(300000000)
_FIVE_HUNDRED_MILLION = Decimal(500000000)
_ONE_BILLION = Decimal(1000000000)


@dataclass(frozen=True, slots=True)
class ProvinceCityBucket:
    code: str
    name: str
    total: int
    confirmed: int
    inferred: int


@dataclass(frozen=True, slots=True)
class BudgetBucket:
    code: BudgetBucketCode
    count: int


@dataclass(frozen=True, slots=True)
class SelectionMethodBucket:
    selection_method: str
    count: int


@dataclass(frozen=True, slots=True)
class DiscoverySnapshot:
    total_packages: int
    province_city_buckets: tuple[ProvinceCityBucket, ...]
    location_needs_review_count: int
    budget_buckets: tuple[BudgetBucket, ...]
    unknown_price_count: int
    selection_method_buckets: tuple[SelectionMethodBucket, ...]
    unsupported_selection_count: int

    @property
    def location_reconciled_count(self) -> int:
        return (
            sum(bucket.total for bucket in self.province_city_buckets)
            + self.location_needs_review_count
        )

    @property
    def budget_reconciled_count(self) -> int:
        return sum(bucket.count for bucket in self.budget_buckets)

    @property
    def selection_reconciled_count(self) -> int:
        return (
            sum(bucket.count for bucket in self.selection_method_buckets)
            + self.unsupported_selection_count
        )


def _budget_code(price: Decimal | None) -> BudgetBucketCode:
    if price is None:
        return BudgetBucketCode.UNKNOWN_PRICE
    if price < 0:
        raise DiscoveryInvariantError("normalized package price cannot be negative")
    if price <= _HUNDRED_MILLION:
        return BudgetBucketCode.UNDER_OR_EQUAL_100M
    if price <= _THREE_HUNDRED_MILLION:
        return BudgetBucketCode.FROM_100M_TO_300M
    if price <= _FIVE_HUNDRED_MILLION:
        return BudgetBucketCode.FROM_300M_TO_500M
    if price <= _ONE_BILLION:
        return BudgetBucketCode.FROM_500M_TO_1B
    return BudgetBucketCode.OVER_1B


def build_discovery(packages: Iterable[PlanPackage]) -> DiscoverySnapshot:
    """Summarize every package row without applying business preferences."""

    universe = tuple(packages)
    locations: dict[str, dict[str, int | str]] = {}
    location_needs_review_count = 0
    budget_counts = dict.fromkeys(_BUDGET_ORDER, 0)
    selection_counts: dict[str, int] = {}
    unsupported_selection_count = 0

    for package in universe:
        if package.province_city_status is ProvinceCityStatus.NEEDS_REVIEW:
            location_needs_review_count += 1
        else:
            if package.province_city_code is None or package.province_city_name is None:
                raise DiscoveryInvariantError(
                    "resolved province/city status requires canonical code and name"
                )
            code = package.province_city_code.upper()
            bucket = locations.setdefault(
                code,
                {
                    "name": package.province_city_name,
                    "confirmed": 0,
                    "inferred": 0,
                },
            )
            if bucket["name"] != package.province_city_name:
                raise DiscoveryInvariantError(
                    f"province/city code {code} has conflicting canonical names"
                )
            status_key = (
                "confirmed"
                if package.province_city_status is ProvinceCityStatus.CONFIRMED
                else "inferred"
            )
            bucket[status_key] = int(bucket[status_key]) + 1

        budget_code = _budget_code(package.package_price)
        budget_counts[budget_code] += 1

        if package.selection_method is None:
            unsupported_selection_count += 1
        else:
            method = package.selection_method.upper()
            selection_counts[method] = selection_counts.get(method, 0) + 1

    province_buckets = tuple(
        ProvinceCityBucket(
            code=code,
            name=str(bucket["name"]),
            confirmed=int(bucket["confirmed"]),
            inferred=int(bucket["inferred"]),
            total=int(bucket["confirmed"]) + int(bucket["inferred"]),
        )
        for code, bucket in sorted(locations.items())
    )
    snapshot = DiscoverySnapshot(
        total_packages=len(universe),
        province_city_buckets=province_buckets,
        location_needs_review_count=location_needs_review_count,
        budget_buckets=tuple(
            BudgetBucket(code=code, count=budget_counts[code]) for code in _BUDGET_ORDER
        ),
        unknown_price_count=budget_counts[BudgetBucketCode.UNKNOWN_PRICE],
        selection_method_buckets=tuple(
            SelectionMethodBucket(selection_method=method, count=count)
            for method, count in sorted(selection_counts.items())
        ),
        unsupported_selection_count=unsupported_selection_count,
    )
    if snapshot.location_reconciled_count != snapshot.total_packages:
        raise DiscoveryInvariantError("location discovery does not reconcile")
    if snapshot.budget_reconciled_count != snapshot.total_packages:
        raise DiscoveryInvariantError("budget discovery does not reconcile")
    if snapshot.selection_reconciled_count != snapshot.total_packages:
        raise DiscoveryInvariantError("selection discovery does not reconcile")
    return snapshot
