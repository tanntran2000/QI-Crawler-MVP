from __future__ import annotations

import asyncio
from dataclasses import replace
from pathlib import Path

from sqlalchemy import func, select

from qi_crawler.config import AppConfig
from qi_crawler.crawler import CrawlerService
from qi_crawler.models import Attachment, TenderItem
from qi_crawler.parser import ParsedAttachment, ParsedNotice, ParsedTenderItem


def _service(tmp_path: Path) -> CrawlerService:
    config = AppConfig()
    config.storage.database_url = f"sqlite:///{tmp_path / 'reconciliation.db'}"
    config.storage.raw_dir = tmp_path / "raw"
    config.storage.download_attachments = False
    return CrawlerService(config)


def _notice(
    *,
    attachments: list[ParsedAttachment] | None = None,
    items: list[ParsedTenderItem] | None = None,
    notice_version: str | None = "00",
    **overrides: object,
) -> ParsedNotice:
    values: dict[str, object] = {
        "source_url": "https://source.example/notices/IB2600000001-00",
        "notice_code": "IB2600000001",
        "source_name": "source",
        "title": "Tender",
        "buyer": "QI Buyer",
        "package_price": 100.0,
        "currency": "VND",
        "published_at": "2026-08-01",
        "closing_at": "2026-08-20",
        "location": "Ho Chi Minh City",
        "notice_version": notice_version,
        "attachments": attachments or [],
        "items": items or [],
        "raw_text": "source evidence",
    }
    values.update(overrides)
    return ParsedNotice(**values)


def _item(code: str) -> ParsedTenderItem:
    return ParsedTenderItem(
        item_code=code,
        product_name=f"Product {code}",
        specification="spec",
        quantity=1.0,
        unit="piece",
    )


def _attachment(url_suffix: str) -> ParsedAttachment:
    return ParsedAttachment(source_url=f"https://source.example/files/{url_suffix}.pdf")


def _close(service: CrawlerService) -> None:
    asyncio.run(service.close())


def test_attachment_present_to_absent_becomes_inactive(tmp_path: Path) -> None:
    service = _service(tmp_path)
    try:
        service.upsert_parsed_notice(_notice(attachments=[_attachment("a")]))
        service.upsert_parsed_notice(_notice())
        with service.db.session() as session:
            row = session.scalar(select(Attachment))
            assert row is not None
            assert row.source_active is False
            assert row.source_removed_at is not None
            assert session.scalar(select(func.count()).select_from(Attachment)) == 1
    finally:
        _close(service)


def test_tender_item_present_to_absent_becomes_inactive(tmp_path: Path) -> None:
    service = _service(tmp_path)
    try:
        service.upsert_parsed_notice(_notice(items=[_item("A")]))
        service.upsert_parsed_notice(_notice())
        with service.db.session() as session:
            row = session.scalar(select(TenderItem))
            assert row is not None
            assert row.source_active is False
            assert row.source_removed_at is not None
            assert session.scalar(select(func.count()).select_from(TenderItem)) == 1
    finally:
        _close(service)


def test_partial_attachment_reconciliation_keeps_present_rows_active(tmp_path: Path) -> None:
    service = _service(tmp_path)
    try:
        service.upsert_parsed_notice(_notice(attachments=[_attachment("a"), _attachment("b")]))
        service.upsert_parsed_notice(_notice(attachments=[_attachment("b"), _attachment("c")]))
        with service.db.session() as session:
            rows = session.scalars(select(Attachment).order_by(Attachment.source_url)).all()
            assert [(row.source_url.rsplit("/", 1)[-1], row.source_active) for row in rows] == [
                ("a.pdf", False),
                ("b.pdf", True),
                ("c.pdf", True),
            ]
    finally:
        _close(service)


def test_partial_tender_item_reconciliation_keeps_present_rows_active(tmp_path: Path) -> None:
    service = _service(tmp_path)
    try:
        service.upsert_parsed_notice(_notice(items=[_item("A"), _item("B")]))
        service.upsert_parsed_notice(_notice(items=[_item("B"), _item("C")]))
        with service.db.session() as session:
            rows = session.scalars(select(TenderItem).order_by(TenderItem.item_code)).all()
            assert [(row.item_code, row.source_active) for row in rows] == [
                ("A", False),
                ("B", True),
                ("C", True),
            ]
    finally:
        _close(service)


def test_reappearing_attachment_reactivates_same_row(tmp_path: Path) -> None:
    service = _service(tmp_path)
    try:
        parsed = _notice(attachments=[_attachment("a")])
        service.upsert_parsed_notice(parsed)
        service.upsert_parsed_notice(_notice())
        service.upsert_parsed_notice(parsed)
        with service.db.session() as session:
            row = session.scalar(select(Attachment))
            assert row is not None
            assert row.source_active is True
            assert row.source_removed_at is None
            assert session.scalar(select(func.count()).select_from(Attachment)) == 1
    finally:
        _close(service)


def test_reappearing_tender_item_reactivates_same_row(tmp_path: Path) -> None:
    service = _service(tmp_path)
    try:
        parsed = _notice(items=[_item("A")])
        service.upsert_parsed_notice(parsed)
        service.upsert_parsed_notice(_notice())
        service.upsert_parsed_notice(parsed)
        with service.db.session() as session:
            row = session.scalar(select(TenderItem))
            assert row is not None
            assert row.source_active is True
            assert row.source_removed_at is None
            assert session.scalar(select(func.count()).select_from(TenderItem)) == 1
    finally:
        _close(service)


def test_downloaded_attachment_evidence_survives_source_removal(tmp_path: Path) -> None:
    service = _service(tmp_path)
    try:
        service.upsert_parsed_notice(_notice(attachments=[_attachment("a")]))
        with service.db.session() as session:
            row = session.scalar(select(Attachment))
            assert row is not None
            row.download_status = "downloaded"
            row.sha256 = "a" * 64
            row.local_path = str(tmp_path / "evidence.pdf")
            attachment_id = row.id
        service.upsert_parsed_notice(_notice())
        with service.db.session() as session:
            row = session.get(Attachment, attachment_id)
            assert row is not None
            assert row.source_active is False
            assert row.download_status == "downloaded"
            assert row.sha256 == "a" * 64
            assert row.local_path == str(tmp_path / "evidence.pdf")
    finally:
        _close(service)


def test_identical_snapshot_does_not_churn_lifecycle_timestamp(tmp_path: Path) -> None:
    service = _service(tmp_path)
    try:
        parsed = _notice(attachments=[_attachment("a")], items=[_item("A")])
        _, _, first_changed = service.upsert_parsed_notice(parsed)
        with service.db.session() as session:
            attachment = session.scalar(select(Attachment))
            item = session.scalar(select(TenderItem))
            assert attachment is not None and item is not None
            attachment_seen = attachment.source_last_seen_at
            item_seen = item.source_last_seen_at
            attachment_removed = attachment.source_removed_at
            item_removed = item.source_removed_at
        _, _, second_changed = service.upsert_parsed_notice(replace(parsed))
        with service.db.session() as session:
            attachment = session.scalar(select(Attachment))
            item = session.scalar(select(TenderItem))
            assert attachment is not None and item is not None
            assert first_changed is True
            assert second_changed is False
            assert attachment.source_last_seen_at == attachment_seen
            assert item.source_last_seen_at == item_seen
            assert attachment.source_removed_at == attachment_removed
            assert item.source_removed_at == item_removed
    finally:
        _close(service)


def test_revision_reconciliation_does_not_deactivate_other_revision(tmp_path: Path) -> None:
    service = _service(tmp_path)
    try:
        service.upsert_parsed_notice(
            _notice(
                notice_version="00",
                attachments=[_attachment("revision-00")],
                source_url="https://source.example/notices/IB2600000001-00",
            )
        )
        service.upsert_parsed_notice(
            _notice(
                notice_version="01",
                attachments=[_attachment("revision-01")],
                source_url="https://source.example/notices/IB2600000001-01",
            )
        )
        with service.db.session() as session:
            rows = session.scalars(select(Attachment).order_by(Attachment.source_url)).all()
            assert len(rows) == 2
            assert all(row.source_active is True for row in rows)
    finally:
        _close(service)


def test_inactive_pending_attachment_is_not_downloaded(tmp_path: Path) -> None:
    service = _service(tmp_path)
    calls: list[int] = []

    async def download(notice_id: int, attachment_id: int) -> None:
        calls.append(attachment_id)

    async def run() -> None:
        try:
            service.upsert_parsed_notice(
                _notice(
                    attachments=[_attachment("a")],
                    source_url="https://source.example/notices/IB2600000001-00",
                )
            )
            service.upsert_parsed_notice(_notice())
            service._get_html = lambda _url: asyncio.sleep(0, result="<html />")  # type: ignore[method-assign]
            service._parse_detail = lambda _html, _url: _notice()  # type: ignore[method-assign]
            service._download_attachment_http = download  # type: ignore[method-assign]
            await service.crawl_notice(
                "https://source.example/notices/IB2600000001-00", download_attachments=True
            )
            assert calls == []
        finally:
            await service.close()

    asyncio.run(run())


def test_hash_changes_when_child_disappears(tmp_path: Path) -> None:
    service = _service(tmp_path)
    try:
        first, _, first_changed = service.upsert_parsed_notice(
            _notice(attachments=[_attachment("a")], items=[_item("A")])
        )
        second, _, second_changed = service.upsert_parsed_notice(_notice())
        assert first_changed is True
        assert second_changed is True
        assert first.content_hash != second.content_hash
    finally:
        _close(service)


def test_inactive_failed_attachment_is_not_retried(tmp_path: Path) -> None:
    service = _service(tmp_path)
    calls: list[int] = []

    async def download(_notice_id: int, attachment_id: int) -> None:
        calls.append(attachment_id)

    try:
        service.upsert_parsed_notice(_notice(attachments=[_attachment("a")]))
        service.upsert_parsed_notice(_notice())
        with service.db.session() as session:
            row = session.scalar(select(Attachment))
            assert row is not None
            row.download_status = "failed"
        service._download_attachment_http = download  # type: ignore[method-assign]
        assert asyncio.run(service.retry_failed_attachments()) == (0, 0)
        assert calls == []
    finally:
        _close(service)
