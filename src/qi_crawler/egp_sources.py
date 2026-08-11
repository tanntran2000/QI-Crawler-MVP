"""Pre-configured source profiles for Vietnam e-GP procurement pages.

Each profile defines the URL pattern, selectors and page type for a specific
category of procurement data on muasamcong.mpi.gov.vn:

- TBMT: Thong bao moi thau (tender notice)
- KHLCNT: Ke hoach lua chon nha thau (selection plan)
- KQLCNT: Ket qua lua chon nha thau (bid result)
- KQMT: Ket qua mo thau (bid opening)
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin

from .authenticated_sources import WebSource

EGP_BASE = "https://muasamcong.mpi.gov.vn"


@dataclass(frozen=True)
class EgpPageType:
    """Metadata describing one type of e-GP listing page."""

    code: str
    label: str
    description: str
    list_path: str
    detail_url_markers: tuple[str, ...]
    item_selector: str
    extra_fields: tuple[str, ...]


TBMT = EgpPageType(
    code="tbmt",
    label="Thong bao moi thau",
    description="Thong tin goi thau dang cong khai moi thau",
    list_path="/vi/web/guest/contractor-selection",
    detail_url_markers=("contractor-selection", "notifyNo=", "step=tbmt"),
    item_selector=(
        'a[href*="contractor-selection"][href*="notifyNo="], '
        'a[href*="contractor-selection"][href*="step=tbmt"]'
    ),
    extra_fields=(
        "Ma TBMT", "Ten goi thau", "Ben moi thau", "Chu dau tu",
        "Gia goi thau", "Thoi diem dong thau", "Phuong thuc LCNT",
    ),
)

KHLCNT = EgpPageType(
    code="khlcnt",
    label="Ke hoach lua chon nha thau",
    description="Ke hoach tong the lua chon nha thau cho du an dau tu",
    list_path="/vi/web/guest/contractor-selection?render=khlcnt",
    detail_url_markers=("contractor-selection", "planNo=", "step=khlcnt"),
    item_selector=(
        'a[href*="contractor-selection"][href*="planNo="], '
        'a[href*="contractor-selection"][href*="step=khlcnt"], '
        'a[href*="planNo="]'
    ),
    extra_fields=(
        "Ma KHLCNT", "Ten du an", "Chu dau tu", "Tong muc dau tu",
        "Nguon von", "Dia diem", "Ngay phe duyet",
    ),
)

KQLCNT = EgpPageType(
    code="kqlcnt",
    label="Ket qua lua chon nha thau",
    description="Ket qua chon nha thau trung thau va gia trung thau",
    list_path="/vi/web/guest/contractor-selection?render=kqlcnt",
    detail_url_markers=("contractor-selection", "step=kqlcnt", "resultNo="),
    item_selector=(
        'a[href*="contractor-selection"][href*="step=kqlcnt"], '
        'a[href*="contractor-selection"][href*="resultNo="], '
        'a[href*="resultNo="]'
    ),
    extra_fields=(
        "Ma goi thau", "Nha thau trung", "Gia trung thau",
        "Thoi gian thuc hien", "Ngay ky hop dong",
    ),
)

KQMT = EgpPageType(
    code="kqmt",
    label="Ket qua mo thau",
    description="Danh sach nha thau tham du va gia du thau khi mo thau",
    list_path="/vi/web/guest/contractor-selection?render=kqmt",
    detail_url_markers=("contractor-selection", "step=kqmt"),
    item_selector=(
        'a[href*="contractor-selection"][href*="step=kqmt"], '
        'a[href*="openingNo="]'
    ),
    extra_fields=(
        "Ma goi thau", "So luong nha thau", "Ngay mo thau",
    ),
)

ALL_PAGE_TYPES: dict[str, EgpPageType] = {
    "tbmt": TBMT,
    "khlcnt": KHLCNT,
    "kqlcnt": KQLCNT,
    "kqmt": KQMT,
}

# Common selectors shared across e-GP page types.
EGP_NEXT_SELECTOR = (
    'a[rel="next"], button[aria-label="Next"]:not([disabled]), '
    '.pagination .next:not(.disabled) a'
)
EGP_PAGE_READY = "main, body"


def egp_source_for_type(
    page_type: EgpPageType,
    name: str | None = None,
    base_url: str = EGP_BASE,
    max_pages: int = 5,
) -> WebSource:
    """Return a ``WebSource`` pre-configured for the given e-GP page type."""
    source_name = name or f"egp-{page_type.code}"
    list_url = urljoin(base_url, page_type.list_path)
    return WebSource(
        name=source_name,
        list_url=list_url,
        item_selector=page_type.item_selector,
        link_selector="a[href]",
        next_selector=EGP_NEXT_SELECTOR,
        page_ready=EGP_PAGE_READY,
        max_pages=max_pages,
    )


def all_egp_sources(
    base_url: str = EGP_BASE,
    max_pages: int = 5,
) -> dict[str, WebSource]:
    """Return pre-configured ``WebSource`` instances for all e-GP page types."""
    return {
        page_type.code: egp_source_for_type(page_type, base_url=base_url, max_pages=max_pages)
        for page_type in ALL_PAGE_TYPES.values()
    }


# Labels used by parser to extract KHLCNT-specific fields from HTML.
KHLCNT_LABELS = {
    "plan_code": ("Ma KHLCNT", "Ma ke hoach"),
    "project_name": ("Ten du an", "Ten ke hoach"),
    "investor": ("Chu dau tu",),
    "buyer": ("Ben moi thau", "Don vi moi thau"),
    "total_investment": ("Tong muc dau tu", "Gia tri du an"),
    "funding_source": ("Nguon von",),
    "location": ("Dia diem thuc hien", "Dia diem"),
    "sector": ("Linh vuc",),
    "approval_date": ("Ngay phe duyet",),
    "expected_start": ("Thoi gian bat dau", "Thoi gian thuc hien tu"),
    "expected_end": ("Thoi gian ket thuc", "Thoi gian thuc hien den"),
}

# Labels used by parser to extract KQLCNT-specific fields from HTML.
KQLCNT_LABELS = {
    "notice_code": ("Ma TBMT", "Ma thong bao", "Ma goi thau"),
    "result_code": ("Ma KQLCNT", "Ma ket qua"),
    "contractor_name": ("Nha thau trung thau", "Nha thau duoc lua chon"),
    "contractor_tax_code": ("Ma so thue nha thau",),
    "winning_price": ("Gia trung thau", "Gia hop dong"),
    "bid_price": ("Gia du thau", "Gia de nghi trung thau"),
    "contract_duration": ("Thoi gian thuc hien hop dong",),
    "result_date": ("Ngay phe duyet KQLCNT", "Ngay phe duyet ket qua"),
}

# Labels used by parser to extract KQMT-specific fields from HTML.
KQMT_LABELS = {
    "notice_code": ("Ma TBMT", "Ma goi thau"),
    "contractor_name": ("Ten nha thau",),
    "contractor_tax_code": ("Ma so thue",),
    "bid_price": ("Gia du thau", "Gia de xuat"),
    "bid_security_amount": ("Bao lanh du thau",),
    "opening_date": ("Ngay mo thau", "Thoi diem mo thau"),
}

# Labels used to extract tax code from buyer/investor sections.
TAX_CODE_LABELS = ("Ma so thue", "MST", "Ma so doanh nghiep")
