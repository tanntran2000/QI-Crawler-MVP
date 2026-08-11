from __future__ import annotations

from datetime import UTC, datetime

import pytest

from qi_crawler.bid_intelligence import fold_text
from qi_crawler.datetime_utils import parse_datetime_utc
from qi_crawler.export.tbmt_formatter import parse_datetime_value as parse_export_datetime
from qi_crawler.parser import parse_datetime_value as parse_tender_datetime


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2026-08-10T10:30:00+07:00", datetime(2026, 8, 10, 3, 30, tzinfo=UTC)),
        ("2026-08-10T10:30:00Z", datetime(2026, 8, 10, 10, 30, tzinfo=UTC)),
        ("2026-08-10T10:30:00", datetime(2026, 8, 10, 10, 30, tzinfo=UTC)),
        ("10 giờ 30 ngày 10/08/2026", datetime(2026, 8, 10, 10, 30, tzinfo=UTC)),
        ("10:30 10/08/2026", datetime(2026, 8, 10, 10, 30, tzinfo=UTC)),
        ("10/08/2026 - 10:30", datetime(2026, 8, 10, 10, 30, tzinfo=UTC)),
    ],
)
def test_parse_datetime_utc_supports_tender_formats(value: str, expected: datetime) -> None:
    assert parse_datetime_utc(value) == expected


def test_shared_parsers_are_utc_aware_and_consistent() -> None:
    value = "2026-08-10 10:30:00"

    assert parse_tender_datetime(value) == parse_datetime_utc(value)
    assert parse_export_datetime(value) == parse_datetime_utc(value)
    assert parse_datetime_utc(value).tzinfo is UTC


def test_parse_datetime_utc_rejects_invalid_values() -> None:
    assert parse_datetime_utc("khong phai ngay") is None
    assert parse_datetime_utc(None) is None


def test_fold_text_normalizes_vietnamese_d_stroke() -> None:
    assert fold_text("Đáp ứng kỹ thuật") == "dap ung ky thuat"
