"""Source contract for the observed TBMT workbook columns."""

from __future__ import annotations

import unicodedata
from typing import Any

OBSERVED_TBMT_HEADERS: tuple[str, ...] = (
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

REQUIRED_TBMT_HEADERS: frozenset[str] = frozenset(
    {
        "BÊN MỜI THẦU",
        "GÓI THẦU",
        "DỰ ÁN",
        "GIÁ GÓI THẦU",
    }
)

_CANONICAL_HEADERS = {header.casefold(): header for header in OBSERVED_TBMT_HEADERS}


def canonical_tbmt_header(value: Any) -> str | None:
    """Return a known TBMT header canonically, preserving unknown text."""

    if value is None:
        return None
    text = " ".join(unicodedata.normalize("NFKC", str(value)).split())
    if not text:
        return None
    return _CANONICAL_HEADERS.get(text.casefold(), text)
