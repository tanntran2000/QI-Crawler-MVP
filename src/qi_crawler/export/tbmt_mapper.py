from __future__ import annotations

from typing import ClassVar

from .tbmt_formatter import (
    clean_text,
    format_package_name,
    parse_datetime_value,
    parse_number,
    raw_field,
)
from .tbmt_schema import TBMT_COLUMNS, NormalizedTenderRecord, TBMTExcelRow


class TBMTExcelMapper:
    """Convert rich Notice records to the stable TBMT-1.0 Excel contract."""

    _NOTICE_LABELS: ClassVar[dict[str, str]] = {
        "tbmt": "Thông báo mời thầu",
        "khlcnt": "Kế hoạch lựa chọn nhà thầu",
        "kqlcnt": "Kết quả lựa chọn nhà thầu",
        "kqmt": "Kết quả mở thầu",
        "extension": "Thông báo gia hạn",
        "cancelled": "Thông báo hủy thầu",
    }

    def normalize(self, notice: object) -> NormalizedTenderRecord:
        raw_text = getattr(notice, "raw_text", None)
        document_issue = getattr(notice, "document_issue_at", None) or parse_datetime_value(
            raw_field(
                raw_text,
                "Thời gian phát hành E-HSMT",
                "Thời gian phát hành HSMT",
                "Thời điểm phát hành E-HSMT",
                "Thời điểm phát hành HSMT",
            )
        )
        document_price = getattr(notice, "document_price", None)
        if document_price is None:
            document_price = parse_number(
                raw_field(raw_text, "Giá bán 1 bộ E-HSMT", "Giá bán 1 bộ HSMT", "Giá HSMT")
            )
        security_amount = getattr(notice, "bid_security_amount", None)
        if security_amount is None:
            security_amount = parse_number(
                raw_field(raw_text, "Giá trị bảo đảm dự thầu", "Bảo đảm dự thầu")
            )
        bid_open = getattr(notice, "bid_open_at", None) or parse_datetime_value(
            raw_field(raw_text, "Thời gian mở thầu", "Thời điểm mở thầu", "Ngày mở thầu")
        )
        if bid_open is None:
            bid_open = next(
                (
                    parse_datetime_value(item.opening_date)
                    for item in getattr(notice, "bid_openings", [])
                    if item.opening_date
                ),
                None,
            )
        contract_duration = clean_text(getattr(notice, "contract_duration", None)) or raw_field(
            raw_text, "Thời gian thực hiện hợp đồng"
        )
        if not contract_duration:
            contract_duration = next(
                (
                    clean_text(item.contract_duration)
                    for item in getattr(notice, "bid_results", [])
                    if item.contract_duration
                ),
                None,
            )

        return NormalizedTenderRecord(
            database_id=getattr(notice, "id", None),
            notice_id=clean_text(getattr(notice, "notice_code", None)),
            notice_version=clean_text(getattr(notice, "notice_version", None)),
            notice_type=clean_text(getattr(notice, "notice_type", None)) or "tbmt",
            source_url=clean_text(getattr(notice, "source_url", None)),
            source_kind=clean_text(getattr(notice, "source_kind", None)),
            package_name=clean_text(getattr(notice, "title", None)),
            package_description=(
                clean_text(getattr(notice, "package_description", None), preserve_newlines=True)
                or raw_field(raw_text, "Nội dung chính của gói thầu", "Mô tả gói thầu")
                or clean_text(getattr(notice, "title", None))
            ),
            procuring_entity=clean_text(getattr(notice, "buyer", None)),
            procuring_entity_address=(
                clean_text(getattr(notice, "procuring_entity_address", None))
                or raw_field(
                    raw_text,
                    "Địa chỉ bên mời thầu",
                    "Địa chỉ của bên mời thầu",
                    "Địa chỉ chủ đầu tư",
                )
            ),
            project_name=(
                clean_text(getattr(notice, "project_name", None))
                or raw_field(raw_text, "Tên dự án", "Dự án", "Tên kế hoạch")
            ),
            funding_source=(
                clean_text(getattr(notice, "funding_source", None))
                or raw_field(raw_text, "Nguồn vốn")
            ),
            package_price=parse_number(getattr(notice, "package_price", None)),
            currency=clean_text(getattr(notice, "currency", None)),
            selection_method=(
                clean_text(getattr(notice, "selection_method", None))
                or raw_field(raw_text, "Phương thức lựa chọn nhà thầu")
            ),
            selection_form=(
                clean_text(getattr(notice, "selection_form", None))
                or raw_field(raw_text, "Hình thức lựa chọn nhà thầu")
            ),
            document_issue_at=document_issue,
            document_price=document_price,
            bid_security_amount=security_amount,
            bid_security_method=(
                clean_text(getattr(notice, "bid_security_method", None))
                or raw_field(raw_text, "Hình thức bảo đảm dự thầu")
            ),
            issue_location=(
                clean_text(getattr(notice, "issue_location", None))
                or raw_field(raw_text, "Địa điểm phát hành E-HSMT", "Địa điểm phát hành HSMT")
                or clean_text(getattr(notice, "source_url", None))
            ),
            bid_close_at=(
                getattr(notice, "closing_at_dt", None)
                or parse_datetime_value(getattr(notice, "closing_at", None))
            ),
            bid_open_at=bid_open,
            contract_duration=contract_duration,
            published_at=(
                getattr(notice, "published_at_dt", None)
                or parse_datetime_value(getattr(notice, "published_at", None))
            ),
            published_at_source=clean_text(getattr(notice, "published_at", None)),
            content_hash=clean_text(getattr(notice, "content_hash", None)),
            crawl_run_id=getattr(notice, "crawl_run_id", None),
            crawl_status=clean_text(getattr(notice, "crawl_status", None)) or "ok",
            review_status=clean_text(getattr(notice, "review_status", None)) or "pending",
            crawled_at=getattr(notice, "last_seen_at", None),
        )

    def map(self, record: NormalizedTenderRecord, index: int) -> TBMTExcelRow:
        notice_label = self._NOTICE_LABELS.get(
            record.notice_type.lower(), "Thông báo mời thầu"
        )
        values: dict[str, object] = {
            "GÓI TIN": f"{index}. {notice_label}",
            "BÊN MỜI THẦU": record.procuring_entity,
            "ĐỊA CHỈ BÊN MỜI THẦU": record.procuring_entity_address,
            "DỰ ÁN": record.project_name,
            "GÓI THẦU": format_package_name(
                record.package_name,
                record.notice_id,
                record.published_at,
                record.published_at_source,
            ),
            "NỘI DUNG CHÍNH CỦA GÓI THẦU": record.package_description,
            "NGUỒN VỐN": record.funding_source,
            "GIÁ GÓI THẦU": record.package_price,
            "PHƯƠNG THỨC LỰA CHỌN NHÀ THẦU": record.selection_method,
            "HÌNH THỨC LỰA CHỌN NHÀ THẦU": record.selection_form,
            "THỜI GIAN PHÁT HÀNH HSMT": record.document_issue_at,
            "GIÁ BÁN 1 BỘ HSMT": record.document_price,
            "BẢO ĐẢM DỰ THẦU": record.bid_security_amount,
            "HÌNH THỨC BẢO ĐẢM DỰ THẦU": record.bid_security_method,
            "ĐỊA ĐIỂM PHÁT HÀNH": record.issue_location,
            "THỜI GIAN ĐÓNG THẦU(HẠN CUỐI TIẾP NHẬN BG)": record.bid_close_at,
            "THỜI GIAN MỞ THẦU": record.bid_open_at,
            "THỜI GIAN THỰC HIỆN HỢP ĐỒNG": record.contract_duration,
        }
        if tuple(values) != TBMT_COLUMNS:
            raise RuntimeError("TBMT mapper is not synchronized with the TBMT-1.0 schema")
        return TBMTExcelRow(values=values, record=record)
