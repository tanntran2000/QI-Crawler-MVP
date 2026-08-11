"""Price intelligence module: analyze and compare procurement pricing.

This module provides DAUTHAU.INFO-equivalent "Soi gia goi thau" capabilities:
- Extract and compare estimated vs actual prices
- Price trend analysis by sector and region
- Identify price anomalies
- Estimate reasonable price range for new packages
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from .db import Database
from .models import BidResult, Notice


@dataclass(frozen=True)
class PriceComparison:
    """Comparison between estimated and actual winning price for a package."""

    notice_id: int
    notice_code: str | None
    title: str | None
    estimated_price: float | None
    winning_price: float | None
    package_price: float | None
    discount_percent: float | None
    currency: str | None
    sector: str | None
    location: str | None


@dataclass(frozen=True)
class SectorPriceStats:
    """Aggregate pricing statistics for a sector."""

    sector: str
    package_count: int
    total_value: float
    avg_package_price: float
    avg_discount_percent: float | None
    min_discount: float | None
    max_discount: float | None
    median_price: float


@dataclass(frozen=True)
class PriceEstimate:
    """Estimated price range for a new package based on historical data."""

    sector: str
    location: str | None
    estimated_low: float
    estimated_mid: float
    estimated_high: float
    based_on_count: int
    avg_discount_rate: float | None
    note: str


def compare_prices(db: Database, notice_id: int) -> PriceComparison | None:
    """Compare estimated price vs winning price for a specific notice."""
    with db.session() as session:
        notice = session.get(Notice, notice_id)
        if not notice:
            return None

        winner = session.scalar(
            select(BidResult).where(
                BidResult.notice_id == notice_id,
                BidResult.is_winner.is_(True),
            )
        )
        winning_price = winner.winning_price if winner else None
        reference_price = notice.estimated_price or notice.package_price
        discount = None
        if winning_price and reference_price and reference_price > 0:
            discount = round((1 - winning_price / reference_price) * 100, 2)

        return PriceComparison(
            notice_id=notice.id,
            notice_code=notice.notice_code,
            title=notice.title,
            estimated_price=notice.estimated_price,
            winning_price=winning_price,
            package_price=notice.package_price,
            discount_percent=discount,
            currency=notice.currency,
            sector=notice.sector,
            location=notice.location,
        )


def sector_price_stats(
    db: Database,
    sector: str | None = None,
    location: str | None = None,
) -> list[SectorPriceStats]:
    """Compute aggregate pricing stats grouped by sector."""
    with db.session() as session:
        statement = select(Notice).where(Notice.package_price.isnot(None))
        if sector:
            statement = statement.where(Notice.sector.ilike(f"%{sector}%"))
        if location:
            statement = statement.where(Notice.location.ilike(f"%{location}%"))
        notices = session.scalars(statement.order_by(Notice.sector)).all()

    sector_groups: dict[str, list[Notice]] = {}
    for n in notices:
        key = n.sector or "Khong xac dinh"
        sector_groups.setdefault(key, []).append(n)

    results: list[SectorPriceStats] = []
    for sector_name, group in sorted(sector_groups.items()):
        prices = [n.package_price for n in group if n.package_price and n.package_price > 0]
        if not prices:
            continue
        total = sum(prices)
        avg = total / len(prices)
        sorted_prices = sorted(prices)
        mid = len(sorted_prices) // 2
        median = (
            sorted_prices[mid]
            if len(sorted_prices) % 2
            else (sorted_prices[mid - 1] + sorted_prices[mid]) / 2
        )

        # Compute discount stats from bid results.
        notice_ids = [n.id for n in group]
        discounts: list[float] = []
        with db.session() as session:
            bid_results = session.scalars(
                select(BidResult).where(
                    BidResult.notice_id.in_(notice_ids),
                    BidResult.is_winner.is_(True),
                    BidResult.discount_rate.isnot(None),
                )
            ).all()
            discounts = [r.discount_rate for r in bid_results if r.discount_rate is not None]

        results.append(
            SectorPriceStats(
                sector=sector_name,
                package_count=len(prices),
                total_value=total,
                avg_package_price=round(avg, 0),
                avg_discount_percent=(
                    round(sum(discounts) / len(discounts), 2) if discounts else None
                ),
                min_discount=round(min(discounts), 2) if discounts else None,
                max_discount=round(max(discounts), 2) if discounts else None,
                median_price=round(median, 0),
            )
        )

    return results


def estimate_price(
    db: Database,
    sector: str,
    location: str | None = None,
    reference_price: float | None = None,
) -> PriceEstimate | None:
    """Estimate a reasonable price range for a new package based on historical data."""
    with db.session() as session:
        statement = select(Notice).where(
            Notice.package_price.isnot(None),
            Notice.sector.ilike(f"%{sector}%"),
        )
        if location:
            statement = statement.where(Notice.location.ilike(f"%{location}%"))
        notices = session.scalars(statement).all()

    prices = [n.package_price for n in notices if n.package_price and n.package_price > 0]
    if not prices:
        return None

    avg = sum(prices) / len(prices)
    sorted_prices = sorted(prices)

    # Percentile-based range.
    low_idx = max(0, int(len(sorted_prices) * 0.25))
    high_idx = min(len(sorted_prices) - 1, int(len(sorted_prices) * 0.75))
    low = sorted_prices[low_idx]
    high = sorted_prices[high_idx]

    # Compute average discount rate for this sector.
    notice_ids = [n.id for n in notices]
    avg_discount = None
    with db.session() as session:
        bid_results = session.scalars(
            select(BidResult).where(
                BidResult.notice_id.in_(notice_ids),
                BidResult.is_winner.is_(True),
                BidResult.discount_rate.isnot(None),
            )
        ).all()
        discounts = [r.discount_rate for r in bid_results if r.discount_rate is not None]
        if discounts:
            avg_discount = round(sum(discounts) / len(discounts), 2)

    # If reference price is given, adjust estimates around it.
    if reference_price and reference_price > 0 and avg_discount is not None:
        mid = reference_price * (1 - avg_discount / 100)
        low = mid * 0.9
        high = mid * 1.1
        note = (
            f"Uoc tinh dua tren gia du toan {reference_price:,.0f} "
            f"va ty le giam trung binh {avg_discount:.1f}% cua {len(notices)} goi tuong tu."
        )
    else:
        mid = avg
        note = (
            f"Uoc tinh dua tren {len(prices)} goi thau linh vuc '{sector}' "
            f"(Q1={low:,.0f}, trung binh={avg:,.0f}, Q3={high:,.0f})."
        )

    return PriceEstimate(
        sector=sector,
        location=location,
        estimated_low=round(low, 0),
        estimated_mid=round(mid, 0),
        estimated_high=round(high, 0),
        based_on_count=len(prices),
        avg_discount_rate=avg_discount,
        note=note,
    )


def find_price_anomalies(
    db: Database,
    threshold_percent: float = 30.0,
) -> list[PriceComparison]:
    """Find packages where winning price deviates significantly from estimated price."""
    with db.session() as session:
        notices = session.scalars(
            select(Notice).where(
                Notice.estimated_price.isnot(None),
                Notice.estimated_price > 0,
            )
        ).all()

    anomalies: list[PriceComparison] = []
    for notice in notices:
        comparison = compare_prices(db, notice.id)
        if comparison and comparison.discount_percent is not None and abs(comparison.discount_percent) > threshold_percent:
            anomalies.append(comparison)

    anomalies.sort(key=lambda c: abs(c.discount_percent or 0), reverse=True)
    return anomalies
