import asyncio
import json
from dataclasses import replace
from pathlib import Path

from sqlalchemy import func, select

from qi_crawler.config import AppConfig
from qi_crawler.crawler import CrawlerService
from qi_crawler.models import Attachment, Notice
from qi_crawler.parser import ParsedAttachment, ParsedNotice

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "golden" / "contracts_finder_v061.json"


def _golden_notices() -> list[dict]:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert fixture["fixture_version"] == "v0.6.1-core-baseline"
    notices = fixture["notices"]
    assert len(notices) == 6
    return notices


def _parsed_notice(item: dict) -> ParsedNotice:
    attachments = [
        ParsedAttachment(source_url=attachment["source_url"], file_name=attachment["file_name"])
        for attachment in item["attachments"]
    ]
    return ParsedNotice(
        source_url=item["source_url"],
        notice_code=item["source_notice_id"],
        title=item["title"],
        buyer=item["buyer"],
        package_price=item["package_price"],
        currency=item["currency"],
        published_at=item["published_at"],
        closing_at=item["closing_at"],
        attachments=attachments,
        raw_text=f"{item['title']}\n{item['buyer']}\n{item['closing_at']}",
    )


def test_golden_tenders_preserve_critical_fields_and_are_idempotent(tmp_path: Path) -> None:
    config = AppConfig()
    config.storage.database_url = f"sqlite:///{tmp_path / 'golden.db'}"
    service = CrawlerService(config)
    golden_notices = _golden_notices()
    initial_ids: dict[str, int] = {}

    try:
        for item in golden_notices:
            notice, created, _ = service.upsert_parsed_notice(_parsed_notice(item))
            assert created
            initial_ids[item["source_notice_id"]] = notice.id

        with service.db.session() as session:
            stored_by_code = {
                notice.notice_code: notice
                for notice in session.scalars(select(Notice).order_by(Notice.id)).all()
            }
            assert len(stored_by_code) == len(golden_notices)
            for item in golden_notices:
                notice = stored_by_code[item["source_notice_id"]]
                assert notice.id == initial_ids[item["source_notice_id"]]
                assert notice.title == item["title"]
                assert notice.buyer == item["buyer"]
                assert notice.package_price == item["package_price"]
                assert notice.closing_at == item["closing_at"]
                assert notice.source_url == item["source_url"]
                assert [attachment.source_url for attachment in notice.attachments] == [
                    attachment["source_url"] for attachment in item["attachments"]
                ]

        for item in golden_notices:
            notice, created, changed = service.upsert_parsed_notice(_parsed_notice(item))
            assert not created
            assert not changed
            assert notice.id == initial_ids[item["source_notice_id"]]

        with service.db.session() as session:
            assert session.scalar(select(func.count()).select_from(Notice)) == len(golden_notices)
            assert session.scalar(select(func.count()).select_from(Attachment)) == 1
    finally:
        asyncio.run(service.close())


def test_golden_tender_updates_in_place_without_creating_duplicate(tmp_path: Path) -> None:
    config = AppConfig()
    config.storage.database_url = f"sqlite:///{tmp_path / 'golden-update.db'}"
    service = CrawlerService(config)
    item = _golden_notices()[0]

    try:
        original, created, _ = service.upsert_parsed_notice(_parsed_notice(item))
        assert created

        updated_title = f"{item['title']} - updated"
        updated_deadline = "2026-08-20T17:00:00+01:00"
        updated = replace(
            _parsed_notice(item),
            title=updated_title,
            package_price=5_100_000.0,
            closing_at=updated_deadline,
        )
        notice, created, changed = service.upsert_parsed_notice(updated)

        assert not created
        assert changed
        assert notice.id == original.id
        assert notice.title == updated_title
        assert notice.package_price == 5_100_000.0
        assert notice.closing_at == updated_deadline
        with service.db.session() as session:
            assert session.scalar(select(func.count()).select_from(Notice)) == 1
    finally:
        asyncio.run(service.close())
