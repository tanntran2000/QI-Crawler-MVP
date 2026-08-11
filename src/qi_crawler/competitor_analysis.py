"""Competitor analysis module: build and query contractor profiles from bid results.

This module provides DAUTHAU.INFO-equivalent "Doc vi doi thu" capabilities:
- Build contractor profiles from KQLCNT/KQMT data
- Win rate analysis by sector and region
- Competitor comparison (up to 3 contractors)
- Detect suspicious bidding patterns
- Analyze buyer-contractor relationships
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select

from .db import Database
from .models import BidOpening, BidResult, Contractor, InvestorProfile, Notice


@dataclass(frozen=True)
class ContractorStats:
    """Summary statistics for a single contractor."""

    tax_code: str
    name: str
    total_wins: int
    total_bids: int
    win_rate: float
    total_win_value: float
    avg_win_value: float
    avg_discount_rate: float | None
    main_sectors: list[str]
    main_provinces: list[str]
    active_years: int
    recent_wins: int  # Last 12 months.


@dataclass(frozen=True)
class CompetitorComparison:
    """Side-by-side comparison of up to 3 contractors."""

    contractors: tuple[ContractorStats, ...]
    common_packages: int
    common_sectors: list[str]
    notes: list[str]


@dataclass(frozen=True)
class BiddingPattern:
    """Detected suspicious bidding pattern."""

    pattern_type: str
    description: str
    contractors: list[str]
    package_count: int
    confidence: float


@dataclass(frozen=True)
class BuyerAnalysis:
    """Analysis of a buyer/investor's procurement history."""

    tax_code: str
    name: str
    total_packages: int
    total_value: float
    top_contractors: list[tuple[str, int, float]]
    main_sectors: list[str]
    avg_package_value: float


def build_contractor_profile(db: Database, tax_code: str) -> ContractorStats | None:
    """Build or update a contractor profile from bid result data."""
    with db.session() as session:
        results = session.scalars(
            select(BidResult).where(BidResult.contractor_tax_code == tax_code)
        ).all()
        openings = session.scalars(
            select(BidOpening).where(BidOpening.contractor_tax_code == tax_code)
        ).all()

        if not results and not openings:
            return None

        name = ""
        wins = [r for r in results if r.is_winner]
        total_bids = len(results) + len(openings)
        total_wins = len(wins)
        total_win_value = sum(r.winning_price or 0 for r in wins)
        avg_win_value = total_win_value / total_wins if total_wins else 0.0

        discount_rates = [r.discount_rate for r in results if r.discount_rate is not None]
        avg_discount = sum(discount_rates) / len(discount_rates) if discount_rates else None

        # Collect sectors from linked notices.
        notice_ids = {r.notice_id for r in results} | {o.notice_id for o in openings}
        sectors: list[str] = []
        provinces: list[str] = []
        years: set[int] = set()
        recent_wins = 0
        now = datetime.now(UTC)

        for notice_id in notice_ids:
            notice = session.get(Notice, notice_id)
            if notice:
                if notice.sector:
                    sectors.append(notice.sector)
                if notice.location:
                    provinces.append(notice.location.split(",")[0].strip())
                if notice.published_at:
                    try:
                        year = int(notice.published_at[:4])
                        years.add(year)
                    except (ValueError, IndexError):
                        pass

        for r in wins:
            if r.result_date:
                try:
                    rd = datetime.fromisoformat(r.result_date[:10])
                    if (now - rd.replace(tzinfo=UTC)).days <= 365:
                        recent_wins += 1
                except (ValueError, TypeError):
                    pass

        name = wins[0].contractor_name if wins else (results[0].contractor_name if results else "")

        sector_counts = Counter(sectors)
        province_counts = Counter(provinces)
        main_sectors = [s for s, _ in sector_counts.most_common(5)]
        main_provinces = [p for p, _ in province_counts.most_common(5)]

        # Update or create Contractor record.
        contractor = session.scalar(
            select(Contractor).where(Contractor.tax_code == tax_code)
        )
        if contractor is None:
            contractor = Contractor(tax_code=tax_code, name=name)
            session.add(contractor)
        contractor.name = name
        contractor.total_wins = total_wins
        contractor.total_bids = total_bids
        contractor.total_win_value = total_win_value
        contractor.win_rate = round(total_wins / total_bids * 100, 2) if total_bids else 0.0
        contractor.avg_discount_rate = avg_discount
        contractor.main_sectors = json.dumps(main_sectors, ensure_ascii=False)
        contractor.last_seen_at = now

    return ContractorStats(
        tax_code=tax_code,
        name=name,
        total_wins=total_wins,
        total_bids=total_bids,
        win_rate=round(total_wins / total_bids * 100, 2) if total_bids else 0.0,
        total_win_value=total_win_value,
        avg_win_value=avg_win_value,
        avg_discount_rate=round(avg_discount, 2) if avg_discount is not None else None,
        main_sectors=main_sectors,
        main_provinces=main_provinces,
        active_years=len(years),
        recent_wins=recent_wins,
    )


def compare_contractors(
    db: Database,
    tax_codes: list[str],
) -> CompetitorComparison:
    """Compare up to 3 contractors side by side."""
    if len(tax_codes) > 3:
        tax_codes = tax_codes[:3]

    stats = []
    for tc in tax_codes:
        profile = build_contractor_profile(db, tc)
        if profile:
            stats.append(profile)

    # Find packages where these contractors competed.
    with db.session() as session:
        all_notice_ids: list[set[int]] = []
        for tc in tax_codes:
            result_ids = set(
                session.scalars(
                    select(BidResult.notice_id).where(BidResult.contractor_tax_code == tc)
                ).all()
            )
            opening_ids = set(
                session.scalars(
                    select(BidOpening.notice_id).where(BidOpening.contractor_tax_code == tc)
                ).all()
            )
            all_notice_ids.append(result_ids | opening_ids)

    common_ids = set.intersection(*all_notice_ids) if all_notice_ids else set()
    common_sectors = list(
        set.intersection(*(set(s.main_sectors) for s in stats)) if stats else set()
    )

    notes: list[str] = []
    if len(common_ids) > 3:
        notes.append(
            f"Cac nha thau nay da cung du thau {len(common_ids)} goi thau. "
            "Can xem xet moi quan he canh tranh."
        )

    return CompetitorComparison(
        contractors=tuple(stats),
        common_packages=len(common_ids),
        common_sectors=common_sectors,
        notes=notes,
    )


def detect_bidding_patterns(
    db: Database,
    min_common_packages: int = 3,
) -> list[BiddingPattern]:
    """Detect suspicious bidding patterns from KQLCNT/KQMT data."""
    patterns: list[BiddingPattern] = []

    with db.session() as session:
        # Find pairs of contractors that frequently bid together.
        results = session.scalars(select(BidResult)).all()
        openings = session.scalars(select(BidOpening)).all()

        # Group by notice_id.
        notice_bidders: dict[int, set[str]] = {}
        for r in results:
            if r.contractor_tax_code:
                notice_bidders.setdefault(r.notice_id, set()).add(r.contractor_tax_code)
        for o in openings:
            if o.contractor_tax_code:
                notice_bidders.setdefault(o.notice_id, set()).add(o.contractor_tax_code)

        # Count co-occurrence pairs.
        pair_counts: Counter[tuple[str, str]] = Counter()
        for bidders in notice_bidders.values():
            sorted_bidders = sorted(bidders)
            for i, a in enumerate(sorted_bidders):
                for b in sorted_bidders[i + 1:]:
                    pair_counts[(a, b)] += 1

        for (a, b), count in pair_counts.most_common(20):
            if count >= min_common_packages:
                # Check if one always loses when the other wins.
                a_wins_when_both = 0
                b_wins_when_both = 0
                both_packages = 0
                for notice_id, bidders in notice_bidders.items():
                    if a in bidders and b in bidders:
                        both_packages += 1
                        winners = [
                            r.contractor_tax_code
                            for r in results
                            if r.notice_id == notice_id and r.is_winner
                        ]
                        if a in winners:
                            a_wins_when_both += 1
                        if b in winners:
                            b_wins_when_both += 1

                if both_packages >= min_common_packages:
                    if a_wins_when_both == both_packages or b_wins_when_both == both_packages:
                        patterns.append(
                            BiddingPattern(
                                pattern_type="one_sided_wins",
                                description=(
                                    f"Mot nha thau luon thang khi ca hai cung du thau "
                                    f"({both_packages} goi). Can kiem tra 'quan xanh quan do'."
                                ),
                                contractors=[a, b],
                                package_count=both_packages,
                                confidence=min(0.9, 0.5 + both_packages * 0.1),
                            )
                        )
                    else:
                        patterns.append(
                            BiddingPattern(
                                pattern_type="frequent_co_bidding",
                                description=(
                                    f"Hai nha thau thuong xuyen cung du thau ({count} goi)."
                                ),
                                contractors=[a, b],
                                package_count=count,
                                confidence=min(0.7, 0.3 + count * 0.05),
                            )
                        )

    return patterns


def analyze_buyer(db: Database, buyer_tax_code: str) -> BuyerAnalysis | None:
    """Analyze a buyer/investor's procurement history and preferred contractors."""
    with db.session() as session:
        notices = session.scalars(
            select(Notice).where(
                (Notice.buyer_tax_code == buyer_tax_code)
                | (Notice.investor_tax_code == buyer_tax_code)
            )
        ).all()

        if not notices:
            return None

        name = notices[0].buyer or notices[0].investor or ""
        total_value = sum(n.package_price or 0 for n in notices)

        # Find top contractors for this buyer.
        notice_ids = [n.id for n in notices]
        contractor_wins: Counter[str] = Counter()
        contractor_values: dict[str, float] = {}
        for notice_id in notice_ids:
            results = session.scalars(
                select(BidResult).where(
                    BidResult.notice_id == notice_id, BidResult.is_winner.is_(True)
                )
            ).all()
            for r in results:
                key = r.contractor_tax_code or r.contractor_name
                contractor_wins[key] += 1
                contractor_values[key] = contractor_values.get(key, 0) + (r.winning_price or 0)

        top_contractors = [
            (name, count, contractor_values.get(name, 0))
            for name, count in contractor_wins.most_common(10)
        ]

        sectors = [n.sector for n in notices if n.sector]
        sector_counts = Counter(sectors)
        main_sectors = [s for s, _ in sector_counts.most_common(5)]

        avg_value = total_value / len(notices) if notices else 0.0

        # Update or create InvestorProfile record.
        profile = session.scalar(
            select(InvestorProfile).where(InvestorProfile.tax_code == buyer_tax_code)
        )
        if profile is None:
            profile = InvestorProfile(tax_code=buyer_tax_code, name=name)
            session.add(profile)
        profile.name = name
        profile.total_packages = len(notices)
        profile.total_package_value = total_value
        profile.main_sectors = json.dumps(main_sectors, ensure_ascii=False)
        profile.last_seen_at = datetime.now(UTC)

    return BuyerAnalysis(
        tax_code=buyer_tax_code,
        name=name,
        total_packages=len(notices),
        total_value=total_value,
        top_contractors=top_contractors,
        main_sectors=main_sectors,
        avg_package_value=avg_value,
    )


def search_contractors(
    db: Database,
    query: str | None = None,
    province: str | None = None,
    min_wins: int = 0,
    limit: int = 50,
) -> list[Contractor]:
    """Search contractor profiles with optional filters."""
    with db.session() as session:
        statement = select(Contractor).order_by(Contractor.total_wins.desc())
        if query:
            pattern = f"%{query}%"
            statement = statement.where(
                Contractor.name.ilike(pattern) | Contractor.tax_code.ilike(pattern)
            )
        if province:
            statement = statement.where(Contractor.province.ilike(f"%{province}%"))
        if min_wins > 0:
            statement = statement.where(Contractor.total_wins >= min_wins)
        return list(session.scalars(statement.limit(limit)).all())
