from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from openpyxl import load_workbook

from qi_crawler.db import Database
from qi_crawler.export.tbmt_excel import TEMPLATE_PATH, export_tbmt
from qi_crawler.export.tbmt_schema import META_SHEET_NAME, SHEET_NAME, TBMT_COLUMNS
from qi_crawler.models import Notice


def _database(tmp_path) -> Database:
    db = Database(f"sqlite:///{tmp_path / 'tbmt.db'}")
    db.create_all()
    return db


def test_tbmt_export_uses_stable_schema_and_typed_values(tmp_path) -> None:
    db = _database(tmp_path)
    with db.session() as session:
        session.add(
            Notice(
                source_url="https://example.test/tender/IB260001",
                url_hash="a" * 64,
                content_hash="b" * 64,
                notice_code="IB260001",
                title="Cung cấp cáp &amp; thiết bị mạng",
                package_description="Cáp quang\u00a0và router",
                buyer="QI Technologies",
                procuring_entity_address="123 Lãnh Binh Thăng",
                project_name="Nâng cấp hạ tầng",
                funding_source="Vốn doanh nghiệp",
                package_price=1_250_000_000,
                selection_method="Một giai đoạn một túi hồ sơ",
                selection_form="Đấu thầu rộng rãi",
                document_issue_at=datetime(2026, 8, 10, 8, 0, tzinfo=UTC),
                document_price=330_000,
                bid_security_amount=25_000_000,
                bid_security_method="Thư bảo lãnh",
                issue_location="Hệ thống e-GP",
                published_at="10/08/2026 07:30",
                published_at_dt=datetime(2026, 8, 10, 7, 30, tzinfo=UTC),
                closing_at_dt=datetime(2026, 8, 20, 9, 0, tzinfo=UTC),
                bid_open_at=datetime(2026, 8, 20, 9, 15, tzinfo=UTC),
                contract_duration="120 ngày",
                crawl_run_id=7,
                review_status="approved",
            )
        )

    before_hash = hashlib.sha256(TEMPLATE_PATH.read_bytes()).hexdigest()
    result = export_tbmt(
        db,
        output=tmp_path / "TBMT.xlsx",
        rejects_dir=tmp_path / "rejects",
        latest_run_only=False,
    )
    after_hash = hashlib.sha256(TEMPLATE_PATH.read_bytes()).hexdigest()

    assert before_hash == after_hash
    assert result.exported_records == 1
    workbook = load_workbook(result.output)
    assert workbook.sheetnames == [SHEET_NAME, META_SHEET_NAME]
    assert workbook[META_SHEET_NAME].sheet_state == "hidden"
    sheet = workbook[SHEET_NAME]
    assert tuple(sheet.cell(10, column).value for column in range(1, 19)) == TBMT_COLUMNS
    assert "Cung cấp cáp & thiết bị mạng" in sheet["E11"].value
    assert "Số thông báo: IB260001" in sheet["E11"].value
    assert sheet["F11"].value == "Cáp quang và router"
    assert sheet["H11"].value == 1_250_000_000
    assert isinstance(sheet["K11"].value, datetime)
    assert isinstance(sheet["P11"].value, datetime)
    assert sheet.freeze_panes == "A11"
    assert sheet.auto_filter.ref == "A10:R11"
    assert sheet["O11"].hyperlink.target == "https://example.test/tender/IB260001"


def test_tbmt_export_rejects_invalid_records_and_never_overwrites(tmp_path) -> None:
    db = _database(tmp_path)
    with db.session() as session:
        session.add(
            Notice(
                source_url="https://example.test/invalid",
                url_hash="c" * 64,
                title="Thiếu mã thông báo",
            )
        )

    first = export_tbmt(
        db,
        output=tmp_path / "TBMT.xlsx",
        rejects_dir=tmp_path / "rejects",
        latest_run_only=False,
    )
    second = export_tbmt(
        db,
        output=tmp_path / "TBMT.xlsx",
        rejects_dir=tmp_path / "rejects",
        latest_run_only=False,
    )

    assert first.output.name == "TBMT.xlsx"
    assert second.output.name == "TBMT_v2.xlsx"
    assert first.rejected_records == 1
    assert first.reject_output is not None
    assert first.reject_output.exists()
    workbook = load_workbook(first.output)
    assert workbook[SHEET_NAME].max_row == 10
