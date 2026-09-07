from __future__ import annotations

from decimal import Decimal

from openpyxl import Workbook, load_workbook

from qi_crawler.gui_services import run_bid_radar_excel_screening
from qi_crawler.market_intelligence.excel_screening import (
    C07Result,
    C09Result,
    C10Result,
    ScreeningResult,
    export_screening_workbook,
    screen_excel_workbook,
)


def _write_khmt(path, rows, *, filename_header="TBMT_07_09.xlsx"):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "KHLCNT"
    sheet.append(["Báo cáo kế hoạch lựa chọn nhà thầu"])
    sheet.append([])
    sheet.append(
        [
            "SỐ KẾ HOẠCH",
            "TÊN GÓI THẦU",
            "TÊN DỰ ÁN",
            "TÊN CHỦ ĐẦU TƯ",
            "GIÁ GÓI THẦU",
            "NỘI DUNG PHÊ DUYỆT",
        ]
    )
    for row in rows:
        sheet.append(row)
    workbook.save(path)


def _write_tbmt(path, rows):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Bản tin điện tử"
    sheet.append(["TBMT report"])
    sheet.append([])
    sheet.append(["BÊN MỜI THẦU", "DỰ ÁN", "GÓI THẦU", "GIÁ GÓI THẦU", "ĐỊA CHỈ BÊN MỜI THẦU"])
    for row in rows:
        sheet.append(row)
    workbook.save(path)


def _khmt_row(plan_id, package, project, buyer, price, approval=""):
    return [plan_id, package, project, buyer, price, approval]


def test_source_authority_uses_identity_and_accounts_duplicate_packages(tmp_path):
    path = tmp_path / "TBMT_07_09.xlsx"
    _write_khmt(
        path,
        [
            _khmt_row(
                "PL2600290673-00",
                "Mua máy chủ và thiết bị lưu trữ",
                "Chương trình chuyển đổi số",
                "Đơn vị Đồng Nai",
                "1.999.999.999",
            ),
            _khmt_row(
                "PL2600290673-00",
                "Mua sắm trang thiết bị",
                "Chương trình chuyển đổi số",
                "Đơn vị Đồng Nai",
                "2.000.000.001",
            ),
        ],
    )
    result = screen_excel_workbook(path)

    assert result.source_type == "KHMT"
    assert result.filename_schema_conflict is True
    assert result.identity_namespace == "PL"
    assert result.data_record_rows == 2
    assert result.read_ok_rows == 2
    assert len(result.records) == 2
    assert [record.identity for record in result.records] == [
        "PL2600290673-00",
        "PL2600290673-00",
    ]
    assert result.records[0].c07 is C07Result.PASS
    assert result.records[0].c09 is C09Result.PASS
    assert result.records[1].c07 is C07Result.UNKNOWN
    assert result.records[1].screening is ScreeningResult.NEEDS_REVIEW
    assert result.records[0].c10 is C10Result.UNKNOWN
    assert result.records[0].location_hint == "Đồng Nai"


def test_c07_is_package_scoped_and_generic_equipment_stays_unknown(tmp_path):
    path = tmp_path / "KHMT.xlsx"
    _write_khmt(
        path,
        [
            _khmt_row("PL2600000001-00", "Triển khai mạng LAN và switch", "", "", 10),
            _khmt_row("PL2600000002-00", "Mua sắm trang thiết bị", "Chương trình chuyển đổi số", "", 10),
            _khmt_row("PL2600000003-00", "Cấp license Windows", "", "", 10),
            _khmt_row("PL2600000004-00", "Thiết bị an toàn thông tin firewall", "", "", 10),
            _khmt_row("PL2600000005-00", "Mua camera giám sát", "", "", 10),
        ],
    )
    result = screen_excel_workbook(path)

    assert [record.c07 for record in result.records] == [
        C07Result.PASS,
        C07Result.UNKNOWN,
        C07Result.PASS,
        C07Result.PASS,
        C07Result.PASS,
    ]
    assert result.records[1].screening is ScreeningResult.NEEDS_REVIEW
    assert result.records[0].c07_rule_code == "R07-NETWORK"
    assert result.records[2].c07_rule_code == "R07-SOFTWARE-LICENSE"
    assert result.records[3].c07_rule_code == "R07-CYBERSECURITY"


def test_c09_exact_two_billion_boundary(tmp_path):
    path = tmp_path / "KHMT.xlsx"
    _write_khmt(
        path,
        [
            _khmt_row("PL2600000011-00", "Mua máy tính", "", "", "1.999.999.999"),
            _khmt_row("PL2600000012-00", "Mua máy tính", "", "", "2.000.000.000"),
            _khmt_row("PL2600000013-00", "Mua máy tính", "", "", "2.000.000.001"),
            _khmt_row("PL2600000014-00", "Mua máy tính", "", "", "không rõ"),
        ],
    )
    result = screen_excel_workbook(path)

    assert [record.package_price for record in result.records] == [
        Decimal(1999999999),
        Decimal(2000000000),
        Decimal(2000000001),
        None,
    ]
    assert [record.c09 for record in result.records] == [
        C09Result.PASS,
        C09Result.PASS,
        C09Result.FAIL,
        C09Result.UNKNOWN,
    ]
    assert all(record.screening is ScreeningResult.SELECT for record in result.records)


def test_accounting_and_four_sheet_export_preserve_provenance(tmp_path):
    source = tmp_path / "KHMT.xlsx"
    _write_khmt(
        source,
        [
            _khmt_row("PL2600000021-00", "Mua máy tính", "", "", 100),
            ["không phải mã PL", "Gói bị lỗi", "", "", 100, ""],
        ],
    )
    workbook = load_workbook(source)
    workbook.active.append(["TỔNG CỘNG", None, None, None, None, None])
    workbook.save(source)

    result = screen_excel_workbook(source)
    assert result.post_header_nonempty_rows == 3
    assert result.data_record_rows == 2
    assert result.read_ok_rows == 1
    assert result.read_error_rows == 1
    assert result.non_record_rows == 1
    assert result.accounting_invariant_status == "PASS"

    output = tmp_path / "screened.xlsx"
    export_screening_workbook(result, output)
    exported = load_workbook(output, read_only=True, data_only=True)
    assert exported.sheetnames == [
        "01_CO_HOI_XEM_XET",
        "02_CAN_BO_SUNG",
        "03_AUDIT_TOAN_BO",
        "04_META",
    ]
    assert next(exported["01_CO_HOI_XEM_XET"].iter_rows(values_only=True))[:6] == (
        "Tên gói",
        "Giá gói",
        "Lý do phù hợp",
        "Địa bàn gợi ý",
        "Cần kiểm tra gì",
        "Mã PL/IB",
    )
    audit_values = list(exported["03_AUDIT_TOAN_BO"].iter_rows(values_only=True))
    assert any(row[0] == "READ_ERROR" for row in audit_values[1:])
    meta = {row[0]: row[1] for row in exported["04_META"].iter_rows(values_only=True) if row[0]}
    assert meta["SOURCE_SHA256"] == result.source_sha256
    assert meta["DATA_RECORD_ROWS"] == 2
    assert meta["READ_ERROR_ROWS"] == 1
    exported.close()


def test_tbmt_identity_schema_is_retained_and_location_is_hint_only(tmp_path):
    path = tmp_path / "KHMT_named_wrongly.xlsx"
    _write_tbmt(
        path,
        [
            [
                "Bên mời thầu",
                "Dự án số hóa",
                "Mua phần mềm bản quyền (Số thông báo: IB2600500001-00)",
                "2.000.000.000",
                "TP.HCM",
            ]
        ],
    )
    result = screen_excel_workbook(path)
    record = result.records[0]
    assert result.source_type == "TBMT"
    assert result.filename_schema_conflict is True
    assert result.identity_namespace == "IB"
    assert record.identity == "IB2600500001-00"
    assert record.c07 is C07Result.PASS
    assert record.c10 is C10Result.UNKNOWN
    assert record.location_hint == "TPHCM"


def test_gui_service_delegates_screening_and_export(tmp_path):
    source = tmp_path / "KHMT.xlsx"
    _write_khmt(source, [_khmt_row("PL2600000031-00", "Mua máy tính", "", "", 100)])
    output = tmp_path / "team-bid-screening.xlsx"
    result = run_bid_radar_excel_screening(source, output_path=output)

    assert result.output_path == output.resolve()
    assert result.run.select_count == 1
    assert output.is_file()
