from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .tbmt_schema import NormalizedTenderRecord


class DataQuality(StrEnum):
    VALID = "VALID"
    WARNING = "WARNING"
    INVALID = "INVALID"


@dataclass(slots=True)
class TBMTValidation:
    status: DataQuality
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


def validate_tbmt_record(record: NormalizedTenderRecord) -> TBMTValidation:
    errors: list[str] = []
    warnings: list[str] = []
    if not record.notice_id:
        errors.append("Thiếu mã TBMT/notice ID")
    if not record.package_name:
        errors.append("Thiếu tên gói thầu")
    if errors:
        return TBMTValidation(DataQuality.INVALID, tuple(errors), tuple(warnings))

    if not record.procuring_entity:
        warnings.append("Thiếu bên mời thầu")
    if not record.bid_close_at:
        warnings.append("Thiếu thời gian đóng thầu chuẩn hóa")
    if not record.procuring_entity_address:
        warnings.append("Thiếu địa chỉ bên mời thầu")
    if record.package_price is None:
        warnings.append("Thiếu giá gói thầu")
    if record.bid_security_amount is None:
        warnings.append("Thiếu bảo đảm dự thầu")
    if warnings:
        return TBMTValidation(DataQuality.WARNING, tuple(errors), tuple(warnings))
    return TBMTValidation(DataQuality.VALID)
