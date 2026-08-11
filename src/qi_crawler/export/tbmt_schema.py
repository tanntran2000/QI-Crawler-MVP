from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

SCHEMA_VERSION = "TBMT-1.0"
SHEET_NAME = "Bản tin điện tử"
META_SHEET_NAME = "__QI_META"
HEADER_ROW = 10
DATA_START_ROW = 11

TBMT_COLUMNS = (
    "GÓI TIN",
    "BÊN MỜI THẦU",
    "ĐỊA CHỈ BÊN MỜI THẦU",
    "DỰ ÁN",
    "GÓI THẦU",
    "NỘI DUNG CHÍNH CỦA GÓI THẦU",
    "NGUỒN VỐN",
    "GIÁ GÓI THẦU",
    "PHƯƠNG THỨC LỰA CHỌN NHÀ THẦU",
    "HÌNH THỨC LỰA CHỌN NHÀ THẦU",
    "THỜI GIAN PHÁT HÀNH HSMT",
    "GIÁ BÁN 1 BỘ HSMT",
    "BẢO ĐẢM DỰ THẦU",
    "HÌNH THỨC BẢO ĐẢM DỰ THẦU",
    "ĐỊA ĐIỂM PHÁT HÀNH",
    "THỜI GIAN ĐÓNG THẦU(HẠN CUỐI TIẾP NHẬN BG)",
    "THỜI GIAN MỞ THẦU",
    "THỜI GIAN THỰC HIỆN HỢP ĐỒNG",
)

MONEY_COLUMNS = (8, 12, 13)
DATETIME_COLUMNS = (11, 16, 17)


@dataclass(slots=True)
class NormalizedTenderRecord:
    database_id: int | None
    notice_id: str | None
    notice_version: str | None
    notice_type: str
    source_url: str | None
    source_kind: str | None
    package_name: str | None
    package_description: str | None
    procuring_entity: str | None
    procuring_entity_address: str | None
    project_name: str | None
    funding_source: str | None
    package_price: float | None
    currency: str | None
    selection_method: str | None
    selection_form: str | None
    document_issue_at: datetime | None
    document_price: float | None
    bid_security_amount: float | None
    bid_security_method: str | None
    issue_location: str | None
    bid_close_at: datetime | None
    bid_open_at: datetime | None
    contract_duration: str | None
    published_at: datetime | None
    published_at_source: str | None
    content_hash: str | None
    crawl_run_id: int | None
    crawl_status: str | None
    review_status: str | None
    crawled_at: datetime | None


@dataclass(slots=True)
class TBMTExcelRow:
    values: dict[str, object]
    record: NormalizedTenderRecord
