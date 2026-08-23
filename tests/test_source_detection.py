from __future__ import annotations

from pathlib import Path

import pytest
from openpyxl import Workbook

from qi_crawler.market_intelligence.source_detection import (
    SourceType,
    detect_source_type,
    resolve_source_type,
)

KHMT_HEADERS = [
    "GÓI TIN",
    "SỐ KẾ HOẠCH",
    "TÊN DỰ ÁN",
    "TÊN CHỦ ĐẦU TƯ",
    "TỔNG MỨC ĐẦU TƯ",
    "NỘI DUNG PHÊ DUYỆT",
    "TÊN GÓI THẦU",
    "NGUỒN VỐN",
    "GIÁ GÓI THẦU",
    "HÌNH THỨC LỰA CHỌN",
    "HÌNH THỨC HỢP ĐỒNG",
    "THỜI GIAN LỰA CHỌN",
    "THỜI GIAN THỰC HIỆN",
]

TBMT_HEADERS = [
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
]


def _workbook(path: Path, headers: list[str], identity: str) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(headers)
    values = ["1. Thông báo mời thầu"] + [""] * (len(headers) - 1)
    if "SỐ KẾ HOẠCH" in headers:
        values[headers.index("SỐ KẾ HOẠCH")] = identity
    if "GÓI THẦU" in headers:
        values[headers.index("GÓI THẦU")] = f"Cung cấp thiết bị (Số thông báo: {identity})"
    sheet.append(values)
    workbook.save(path)


def test_khmt_filename_and_content_auto_classify(tmp_path: Path) -> None:
    path = tmp_path / "KHMT_19_8_2026.xlsx"
    _workbook(path, KHMT_HEADERS, "PL2600265077-00")

    result = detect_source_type(path)

    assert result.filename_type is SourceType.KHMT
    assert result.content_type is SourceType.KHMT
    assert result.identity_namespace == "PL"
    assert result.auto_type is SourceType.KHMT
    assert result.requires_human is False


@pytest.mark.parametrize("name", ["tbmt_19_8_2026.xlsx", "TBMT-19_8_2026.xlsx", "TbMt 19.xlsx"])
def test_tbmt_filename_variants_and_identity_are_auto_classified(
    tmp_path: Path, name: str
) -> None:
    path = tmp_path / name
    _workbook(path, TBMT_HEADERS, "IB2600463290- 00")

    result = detect_source_type(path)

    assert result.filename_type is SourceType.TBMT
    assert result.content_type is SourceType.TBMT
    assert result.identity_namespace == "IB"
    assert result.identity_values == ("IB2600463290-00",)
    assert result.auto_type is SourceType.TBMT
    assert result.requires_human is False


def test_conflicting_filename_and_schema_requires_human(tmp_path: Path) -> None:
    path = tmp_path / "TBMT_conflict.xlsx"
    _workbook(path, KHMT_HEADERS, "PL2600265077-00")

    result = detect_source_type(path)

    assert result.auto_type is SourceType.UNKNOWN
    assert result.requires_human is True
    assert "conflict" in " ".join(result.reasons).lower()


def test_khmt_filename_with_tbmt_content_requires_human(tmp_path: Path) -> None:
    path = tmp_path / "KHMT_conflict.xlsx"
    _workbook(path, TBMT_HEADERS, "IB2600463290-00")

    result = detect_source_type(path)

    assert result.auto_type is SourceType.UNKNOWN
    assert result.requires_human is True
    assert result.identity_namespace == "IB"


def test_unknown_filename_never_auto_imports_even_with_strong_content(tmp_path: Path) -> None:
    path = tmp_path / "opportunity.xlsx"
    _workbook(path, KHMT_HEADERS, "PL2600265077-00")

    result = detect_source_type(path)

    assert result.filename_type is SourceType.UNKNOWN
    assert result.content_type is SourceType.KHMT
    assert result.auto_type is SourceType.UNKNOWN
    assert result.requires_human is True
    assert resolve_source_type(result, SourceType.KHMT).authority == "HUMAN"


def test_manual_override_keeps_identity_namespace_and_source_sha(tmp_path: Path) -> None:
    path = tmp_path / "unknown.xlsx"
    _workbook(path, KHMT_HEADERS, "PL2600265077-00")
    detection = detect_source_type(path)

    resolved = resolve_source_type(detection, SourceType.KHMT)

    assert resolved.final_type is SourceType.KHMT
    assert resolved.identity_namespace == "PL"
    assert resolved.source_sha256 == detection.source_sha256


def test_conflicting_identity_namespaces_require_human(tmp_path: Path) -> None:
    path = tmp_path / "TBMT_mixed.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(TBMT_HEADERS)
    values = [""] * len(TBMT_HEADERS)
    values[0] = "IB2600463290-00 and PL2600265077-00"
    sheet.append(values)
    workbook.save(path)

    result = detect_source_type(path)

    assert result.identity_namespace is None
    assert result.auto_type is SourceType.UNKNOWN
    assert result.requires_human is True
