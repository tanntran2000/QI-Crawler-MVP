from __future__ import annotations

from qi_crawler.market_intelligence.tbmt_schema import (
    OBSERVED_TBMT_HEADERS,
    REQUIRED_TBMT_HEADERS,
    canonical_tbmt_header,
)

EXPECTED_HEADERS = (
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


def test_observed_tbmt_headers_match_exact_source_order() -> None:
    assert OBSERVED_TBMT_HEADERS == EXPECTED_HEADERS
    assert len(OBSERVED_TBMT_HEADERS) == 18


def test_observed_tbmt_headers_are_unique() -> None:
    assert len(set(OBSERVED_TBMT_HEADERS)) == len(OBSERVED_TBMT_HEADERS)


def test_selection_method_and_form_are_distinct_source_fields() -> None:
    assert "PHƯƠNG THỨC LỰA CHỌN NHÀ THẦU" in REQUIRED_TBMT_HEADERS or (
        "PHƯƠNG THỨC LỰA CHỌN NHÀ THẦU" in OBSERVED_TBMT_HEADERS
    )
    assert "HÌNH THỨC LỰA CHỌN NHÀ THẦU" in OBSERVED_TBMT_HEADERS
    assert OBSERVED_TBMT_HEADERS.index("PHƯƠNG THỨC LỰA CHỌN NHÀ THẦU") != OBSERVED_TBMT_HEADERS.index(
        "HÌNH THỨC LỰA CHỌN NHÀ THẦU"
    )


def test_guarantee_schedule_and_duration_fields_are_preserved() -> None:
    assert "BẢO ĐẢM DỰ THẦU" in OBSERVED_TBMT_HEADERS
    assert "HÌNH THỨC BẢO ĐẢM DỰ THẦU" in OBSERVED_TBMT_HEADERS
    assert "THỜI GIAN ĐÓNG THẦU(HẠN CUỐI TIẾP NHẬN BG)" in OBSERVED_TBMT_HEADERS
    assert "THỜI GIAN MỞ THẦU" in OBSERVED_TBMT_HEADERS
    assert "THỜI GIAN THỰC HIỆN HỢP ĐỒNG" in OBSERVED_TBMT_HEADERS


def test_canonical_tbmt_header_tolerates_case_and_whitespace() -> None:
    assert canonical_tbmt_header("  gói \t tin  ") == "GÓI TIN"
    assert canonical_tbmt_header(" bên  mời thầu ") == "BÊN MỜI THẦU"


def test_canonical_tbmt_header_preserves_unknown_source_header() -> None:
    assert canonical_tbmt_header("  CỘT NGUỒN MỚI  ") == "CỘT NGUỒN MỚI"


def test_canonical_tbmt_header_returns_none_for_blank_values() -> None:
    assert canonical_tbmt_header(None) is None
    assert canonical_tbmt_header(" \t ") is None
