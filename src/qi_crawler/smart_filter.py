"""Smart Filter: natural language search for procurement notices.

This module provides DAUTHAU.INFO-equivalent AI Smart Filter:
- Convert Vietnamese natural language queries to database filters
- Support follow-up queries to refine results
- Parse intent: sector, location, price range, deadline, buyer
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, or_, select

from .db import Database
from .keywords import normalize_keyword
from .models import Notice

# Vietnamese province mappings (common names to standardized forms).
PROVINCE_ALIASES: dict[str, str] = {
    "ha noi": "Ha Noi", "hn": "Ha Noi", "hanoi": "Ha Noi",
    "hcm": "Ho Chi Minh", "sai gon": "Ho Chi Minh", "saigon": "Ho Chi Minh",
    "tp hcm": "Ho Chi Minh", "tphcm": "Ho Chi Minh",
    "da nang": "Da Nang", "hai phong": "Hai Phong",
    "can tho": "Can Tho", "binh duong": "Binh Duong",
    "dong nai": "Dong Nai", "quang ninh": "Quang Ninh",
    "thanh hoa": "Thanh Hoa", "nghe an": "Nghe An",
    "hue": "Thua Thien Hue", "khanh hoa": "Khanh Hoa",
    "nha trang": "Khanh Hoa", "vung tau": "Ba Ria - Vung Tau",
}

# Sector keyword mappings.
SECTOR_KEYWORDS: dict[str, list[str]] = {
    "CNTT": ["cntt", "cong nghe thong tin", "it", "phan mem", "may tinh", "server", "mang"],
    "Xay dung": ["xay dung", "xay lap", "cong trinh", "construction", "nha"],
    "Y te": ["y te", "benh vien", "thuoc", "thiet bi y te", "medical"],
    "Giao duc": ["giao duc", "truong hoc", "dao tao", "education"],
    "Giao thong": ["giao thong", "duong", "cau", "transport", "road"],
    "Dien": ["dien", "nang luong", "electric", "power", "tram bien ap"],
    "Vien thong": ["vien thong", "telecom", "cap quang", "fiber"],
    "Moi truong": ["moi truong", "xu ly nuoc", "rac thai", "environment"],
    "Nong nghiep": ["nong nghiep", "thuy loi", "irrigation", "agriculture"],
}

# Time expressions.
TIME_PATTERNS: dict[str, int] = {
    "tuan nay": 7, "tuan truoc": 14,
    "thang nay": 30, "thang truoc": 60,
    "3 thang": 90, "6 thang": 180,
    "nam nay": 365, "1 nam": 365,
}


@dataclass
class SmartFilter:
    """Parsed filters from a natural language query."""

    raw_query: str = ""
    sectors: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    buyer_name: str | None = None
    min_price: float | None = None
    max_price: float | None = None
    days_back: int | None = None
    closing_within_days: int | None = None
    notice_type: str | None = None
    limit: int = 50

    @property
    def description(self) -> str:
        """Human-readable description of the active filters."""
        parts: list[str] = []
        if self.sectors:
            parts.append(f"Linh vuc: {', '.join(self.sectors)}")
        if self.locations:
            parts.append(f"Dia diem: {', '.join(self.locations)}")
        if self.keywords:
            parts.append(f"Tu khoa: {', '.join(self.keywords)}")
        if self.buyer_name:
            parts.append(f"Ben moi thau: {self.buyer_name}")
        if self.min_price or self.max_price:
            price = []
            if self.min_price:
                price.append(f"tu {self.min_price:,.0f}")
            if self.max_price:
                price.append(f"den {self.max_price:,.0f}")
            parts.append(f"Gia: {' '.join(price)}")
        if self.days_back:
            parts.append(f"Trong {self.days_back} ngay qua")
        if self.closing_within_days:
            parts.append(f"Dong thau trong {self.closing_within_days} ngay")
        return " | ".join(parts) if parts else "Tat ca goi thau"


def parse_price(text: str) -> float | None:
    """Parse a Vietnamese price expression to float."""
    normalized = normalize_keyword(text)
    # Match patterns like "5 ty", "500 trieu", "1.5 ty"
    match = re.search(r"([\d.,]+)\s*(ty|trieu|nghin|ngan|tr|t)", normalized)
    if not match:
        return None
    value = float(match.group(1).replace(",", "."))
    unit = match.group(2)
    multipliers = {"ty": 1e9, "t": 1e9, "trieu": 1e6, "tr": 1e6, "nghin": 1e3, "ngan": 1e3}
    return value * multipliers.get(unit, 1)


def parse_query(query: str) -> SmartFilter:
    """Parse a Vietnamese natural language query into structured filters."""
    normalized = normalize_keyword(query)
    result = SmartFilter(raw_query=query)

    # Detect sectors.
    for sector, keywords in SECTOR_KEYWORDS.items():
        if any(kw in normalized for kw in keywords):
            result.sectors.append(sector)

    # Detect locations.
    for alias, province in PROVINCE_ALIASES.items():
        if alias in normalized and province not in result.locations:
            result.locations.append(province)

    # Detect time expressions.
    for pattern, days in TIME_PATTERNS.items():
        if normalize_keyword(pattern) in normalized:
            result.days_back = days
            break

    # Detect time patterns like "3 thang", "2 nam".
    time_match = re.search(r"(\d+)\s*(thang|nam|tuan|ngay)", normalized)
    if time_match and not result.days_back:
        value = int(time_match.group(1))
        unit = time_match.group(2)
        multipliers = {"ngay": 1, "tuan": 7, "thang": 30, "nam": 365}
        result.days_back = value * multipliers.get(unit, 1)

    # Detect closing deadline.
    closing_match = re.search(r"sap\s*(?:dong|het\s*han)|con\s*(\d+)\s*ngay", normalized)
    if closing_match:
        result.closing_within_days = int(closing_match.group(1) or 7)

    # Detect price range.
    price_from = re.search(r"(?:tu|tren|lon\s*hon)\s*([\d.,]+\s*(?:ty|trieu|tr|t))", normalized)
    price_to = re.search(r"(?:den|duoi|nho\s*hon)\s*([\d.,]+\s*(?:ty|trieu|tr|t))", normalized)
    if price_from:
        result.min_price = parse_price(price_from.group(1))
    if price_to:
        result.max_price = parse_price(price_to.group(1))

    # Detect buyer name (after "ben moi thau" or "cua").
    buyer_match = re.search(r"(?:ben\s*moi\s*thau|cua)\s+(.+?)(?:\s*(?:o|tai|trong|tu|den)|$)", normalized)
    if buyer_match:
        result.buyer_name = buyer_match.group(1).strip()

    # Detect notice type.
    if "khlcnt" in normalized or "ke hoach" in normalized:
        result.notice_type = "khlcnt"
    elif "kqlcnt" in normalized or "ket qua" in normalized:
        result.notice_type = "kqlcnt"
    elif "kqmt" in normalized or "mo thau" in normalized:
        result.notice_type = "kqmt"

    # Remaining words as general keywords (exclude common stop words).
    stop_words = {
        "goi", "thau", "tim", "kiem", "o", "tai", "trong", "gan", "day",
        "moi", "nhat", "lon", "nho", "tu", "den", "va", "cac", "nhung",
        "co", "la", "cho", "voi", "cua", "ben", "nha", "theo",
    }
    words = normalized.split()
    for word in words:
        if len(word) > 2 and word not in stop_words:
            # Only add if not already captured by sector/location/price.
            already_captured = any(
                word in normalize_keyword(s)
                for s in result.sectors + result.locations
            )
            if not already_captured and word not in [normalize_keyword(k) for k in result.keywords]:
                result.keywords.append(word)

    # Deduplicate keywords.
    result.keywords = list(dict.fromkeys(result.keywords))[:10]

    return result


def execute_smart_filter(db: Database, smart_filter: SmartFilter) -> list[Notice]:
    """Execute a smart filter against the database and return matching notices."""
    with db.session() as session:
        statement = select(Notice).order_by(Notice.id.desc())

        conditions = []

        # Sector filter.
        for sector in smart_filter.sectors:
            conditions.append(
                or_(
                    Notice.sector.ilike(f"%{sector}%"),
                    Notice.ai_sector.ilike(f"%{sector}%"),
                    Notice.title.ilike(f"%{sector}%"),
                )
            )

        # Location filter.
        for location in smart_filter.locations:
            conditions.append(Notice.location.ilike(f"%{location}%"))

        # Keyword filter.
        for keyword in smart_filter.keywords[:5]:  # Limit to 5 keywords for performance.
            pattern = f"%{keyword}%"
            conditions.append(
                or_(
                    Notice.title.ilike(pattern),
                    Notice.raw_text.ilike(pattern),
                    Notice.buyer.ilike(pattern),
                )
            )

        # Buyer name filter.
        if smart_filter.buyer_name:
            conditions.append(Notice.buyer.ilike(f"%{smart_filter.buyer_name}%"))

        # Price range filter.
        if smart_filter.min_price:
            conditions.append(Notice.package_price >= smart_filter.min_price)
        if smart_filter.max_price:
            conditions.append(Notice.package_price <= smart_filter.max_price)

        # Time filter (published within N days).
        if smart_filter.days_back:
            cutoff = datetime.now(UTC) - timedelta(days=smart_filter.days_back)
            conditions.append(Notice.first_seen_at >= cutoff)

        # Notice type filter.
        if smart_filter.notice_type:
            conditions.append(Notice.notice_type == smart_filter.notice_type)

        if conditions:
            statement = statement.where(and_(*conditions))

        statement = statement.limit(smart_filter.limit)
        return list(session.scalars(statement).all())


def smart_search(db: Database, query: str, limit: int = 50) -> tuple[SmartFilter, list[Notice]]:
    """High-level API: parse query and execute search in one step."""
    smart_filter = parse_query(query)
    smart_filter.limit = limit
    results = execute_smart_filter(db, smart_filter)
    return smart_filter, results
