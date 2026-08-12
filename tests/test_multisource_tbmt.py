from __future__ import annotations

import asyncio
from datetime import datetime

from openpyxl import load_workbook
from sqlalchemy import select

from qi_crawler.config import AppConfig
from qi_crawler.crawler import CrawlerService
from qi_crawler.export.tbmt_excel import export_tbmt
from qi_crawler.export.tbmt_formatter import clean_text, parse_number
from qi_crawler.export.tbmt_schema import SHEET_NAME
from qi_crawler.models import Notice

COTECCONS_URL = "https://ebidding.coteccons.vn/Index/ChiTiet/2607301"
COTECCONS_HTML = """
<html><body>
  <h1>GÓI THẦU : THI CÔNG CHỐNG THẤM</h1>
  <h3>Công ty Cổ phần Xây dựng Coteccons phát hành Hồ sơ mời thầu như sau:</h3>
  <table>
    <tr><th>Dự án:</th><td>MASTERISE ĐẠI AN</td></tr>
    <tr><th>Địa điểm:</th><td>Văn Giang, Hưng Yên</td></tr>
    <tr><th>Gói thầu:</th><td>THI CÔNG CHỐNG THẤM</td></tr>
    <tr><th>Thời gian đóng thầu:</th><td>08/08/2026 08:28:00</td></tr>
    <tr><th>Hình thức lựa chọn:</th><td>Chào giá cạnh tranh</td></tr>
  </table>
</body></html>
"""


def test_coteccons_without_tbmt_code_is_exported_with_warning(tmp_path) -> None:
    config = AppConfig()
    config.storage.database_url = f"sqlite:///{tmp_path / 'coteccons.db'}"
    config.storage.raw_dir = tmp_path / "raw"
    config.storage.download_attachments = False
    service = CrawlerService(config)

    async def get_fixture_html(_: str) -> str:
        return COTECCONS_HTML

    service._get_html = get_fixture_html  # type: ignore[method-assign]
    try:
        asyncio.run(service.crawl_notice(COTECCONS_URL))
        with service.db.session() as session:
            notice = session.scalar(select(Notice))
            assert notice is not None
            assert notice.notice_code is None
            assert notice.source_notice_id == "2607301"
            assert notice.source_name == "coteccons"

        result = export_tbmt(
            service.db,
            output=tmp_path / "TBMT_coteccons.xlsx",
            rejects_dir=tmp_path / "rejects",
            latest_run_only=False,
        )

        assert result.exported_records == 1
        assert result.warning_records == 1
        assert result.rejected_records == 0
        workbook = load_workbook(result.output)
        sheet = workbook[SHEET_NAME]
        assert sheet["B11"].value == "Công ty Cổ phần Xây dựng Coteccons"
        assert sheet["D11"].value == "MASTERISE ĐẠI AN"
        assert sheet["E11"].value == (
            "GÓI THẦU: THI CÔNG CHỐNG THẤM\n"
            "(Mã nguồn: COTEC-2607301. Nguồn: Coteccons eBidding)"
        )
        assert sheet["O11"].value == COTECCONS_URL
        assert sheet["O11"].hyperlink.target == COTECCONS_URL
        assert sheet["J11"].value == "Chào giá cạnh tranh"
        assert isinstance(sheet["P11"].value, datetime)
        assert sheet["P11"].value.hour == 8
        assert sheet["P11"].value.minute == 28
        assert sheet["C11"].value is None
        assert sheet["G11"].value is None
        assert sheet["H11"].value is None
        meta = workbook["__QI_META"]
        assert [cell.value for cell in meta[9]][:5] == [
            "Database ID",
            "Notice ID",
            "Source Name",
            "Source Notice ID",
            "Notice Version",
        ]
        assert meta[10][2].value == "coteccons"
        assert meta[10][3].value == "2607301"
    finally:
        asyncio.run(service.close())


def test_tbmt_cleaning_keeps_legitimate_23_and_decodes_html_entities() -> None:
    assert clean_text("23") == "23"
    assert clean_text("M&atilde; TBMT") == "Mã TBMT"
    assert parse_number("23") == 23.0
