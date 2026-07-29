import asyncio
from pathlib import Path

from sqlalchemy import func, select

from egp_crawler.config import AppConfig
from egp_crawler.crawler import CrawlerService
from egp_crawler.importer import import_file
from egp_crawler.models import Notice


def test_import_csv_and_reject_invalid_row(tmp_path: Path):
    csv_path = tmp_path / "input.csv"
    csv_path.write_text(
        "Mã TBMT,Tên gói thầu,Bên mời thầu,Giá gói thầu,Thời điểm đóng thầu\n"
        "IB260001,Mua thiết bị mạng,Công ty A,1.200.000.000 VND,10:00 20/08/2026\n"
        ",,Công ty B,1000000 VND,\n",
        encoding="utf-8-sig",
    )
    config = AppConfig()
    config.storage.database_url = f"sqlite:///{tmp_path / 'test.db'}"
    config.storage.rejects_dir = tmp_path / "rejects"
    service = CrawlerService(config)
    try:
        summary = import_file(service, csv_path)
        assert summary.rows_found == 2
        assert summary.inserted == 1
        assert summary.rejected == 1
        assert summary.reject_file and summary.reject_file.exists()
        with service.db.session() as session:
            assert session.scalar(select(func.count()).select_from(Notice)) == 1
    finally:
        asyncio.run(service.close())
