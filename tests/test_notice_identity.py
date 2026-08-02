import asyncio
from pathlib import Path

from sqlalchemy import func, select

from qi_crawler.config import AppConfig
from qi_crawler.crawler import CrawlerService
from qi_crawler.models import Notice
from qi_crawler.parser import ParsedNotice


def _parsed(version: str, title: str) -> ParsedNotice:
    return ParsedNotice(
        source_url="https://example.test/tender/IB260001",
        notice_code="IB260001",
        notice_version=version,
        title=title,
        buyer="QI Buyer",
        package_price=1_000_000,
        currency="VND",
        published_at="2026-08-01",
        closing_at="2026-08-20",
        location="Ho Chi Minh City",
        sector="Information Technology",
        selection_method="Open bidding",
        raw_text=f"{title} with detailed network requirements",
    )


def test_notice_code_and_version_form_stable_identity(tmp_path: Path) -> None:
    config = AppConfig()
    config.storage.database_url = f"sqlite:///{tmp_path / 'identity.db'}"
    service = CrawlerService(config)
    try:
        _, first_created, _ = service.upsert_parsed_notice(_parsed("1", "Version one"))
        _, repeated_created, repeated_changed = service.upsert_parsed_notice(
            _parsed("1", "Version one updated")
        )
        _, second_created, _ = service.upsert_parsed_notice(_parsed("2", "Version two"))

        assert first_created
        assert not repeated_created
        assert repeated_changed
        assert second_created
        with service.db.session() as session:
            assert session.scalar(select(func.count()).select_from(Notice)) == 2
            versions = set(session.scalars(select(Notice.notice_version)).all())
            assert versions == {"1", "2"}
    finally:
        asyncio.run(service.close())
