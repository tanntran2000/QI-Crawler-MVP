from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .tbmt_schema import NormalizedTenderRecord


class DataQuality(StrEnum):
    PASS = "PASS"
    WARNING = "WARNING"
    REJECT = "REJECT"


@dataclass(slots=True)
class TBMTValidation:
    status: DataQuality
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


def validate_tbmt_record(record: NormalizedTenderRecord) -> TBMTValidation:
    errors: list[str] = []
    warnings: list[str] = []
    if not record.package_name:
        errors.append("Thiếu tên gói thầu")
    if not record.source_url:
        errors.append("Thiếu URL nguồn")
    if not record.notice_id and not record.source_notice_id:
        errors.append("Thiếu cả mã TBMT và mã nguồn")
    if errors:
        return TBMTValidation(DataQuality.REJECT, tuple(errors), tuple(warnings))

    if not record.procuring_entity_address:
        warnings.append("Thiếu địa chỉ bên mời thầu")
    if not record.project_name:
        warnings.append("Thiếu dự án")
    if not record.funding_source:
        warnings.append("Thiếu nguồn vốn")
    if record.package_price is None:
        warnings.append("Thiếu giá gói thầu")
    if record.bid_security_amount is None:
        warnings.append("Thiếu bảo đảm dự thầu")
    if not record.contract_duration:
        warnings.append("Thiếu thời gian thực hiện hợp đồng")
    if warnings:
        return TBMTValidation(DataQuality.WARNING, tuple(errors), tuple(warnings))
    return TBMTValidation(DataQuality.PASS)
