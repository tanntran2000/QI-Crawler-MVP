from __future__ import annotations

import asyncio
import hashlib
import tempfile
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import func, select

from qi_crawler.config import AppConfig
from qi_crawler.crawler import CrawlerService, parsed_content_hash
from qi_crawler.models import Notice
from qi_crawler.parser import ParsedAttachment, ParsedNotice, ParsedTenderItem


def _raw_service(raw_dir: Path) -> CrawlerService:
    service = CrawlerService.__new__(CrawlerService)
    service.config = SimpleNamespace(storage=SimpleNamespace(raw_dir=raw_dir))
    return service


@pytest.fixture
def raw_capture_service() -> tuple[CrawlerService, Path]:
    with tempfile.TemporaryDirectory(prefix="qi-si-") as directory:
        raw_dir = Path(directory)
        yield _raw_service(raw_dir), raw_dir


def _service(tmp_path: Path) -> CrawlerService:
    config = AppConfig()
    config.storage.database_url = f"sqlite:///{tmp_path / 'integrity.db'}"
    return CrawlerService(config)


def _notice(
    *,
    source_url: str = "https://source-a.example/notices/X",
    source_name: str = "source-a",
    notice_code: str | None = "X",
    notice_version: str | None = "1",
    title: str = "Tender X",
    **overrides: object,
) -> ParsedNotice:
    values: dict[str, object] = {
        "source_url": source_url,
        "notice_code": notice_code,
        "source_notice_id": None,
        "source_name": source_name,
        "title": title,
        "buyer": "QI Buyer",
        "package_price": 1_000_000.0,
        "currency": "VND",
        "published_at": "2026-08-01",
        "closing_at": "2026-08-20",
        "location": "Ho Chi Minh City",
        "sector": "Information Technology",
        "selection_method": "Open bidding",
        "notice_version": notice_version,
        "raw_text": f"{title} source evidence",
    }
    values.update(overrides)
    return ParsedNotice(**values)


def _item(**overrides: object) -> ParsedTenderItem:
    values: dict[str, object] = {
        "item_code": "1",
        "product_name": "Network switch",
        "specification": "48 ports",
        "quantity": 2.0,
        "minimum_quantity": 1.0,
        "maximum_quantity": 3.0,
        "unit": "piece",
        "source_document": "BOQ.xlsx",
        "source_location": "Sheet1!A1",
        "extraction_confidence": 0.95,
        "needs_human_review": False,
    }
    values.update(overrides)
    return ParsedTenderItem(**values)


def test_raw_capture_same_url_different_bytes_is_immutable(
    raw_capture_service: tuple[CrawlerService, Path],
) -> None:
    service, _ = raw_capture_service
    first = service._save_raw_html("https://example.test/notice", "<p>v1</p>")
    second = service._save_raw_html("https://example.test/notice", "<p>v2</p>")

    assert first != second
    assert first.read_text(encoding="utf-8") == "<p>v1</p>"
    assert second.read_text(encoding="utf-8") == "<p>v2</p>"


def test_raw_capture_same_url_same_bytes_is_idempotent(
    raw_capture_service: tuple[CrawlerService, Path],
) -> None:
    service, _ = raw_capture_service
    first = service._save_raw_html("https://example.test/notice", "<p>same</p>")
    second = service._save_raw_html("https://example.test/notice", "<p>same</p>")

    assert first == second
    assert first.read_text(encoding="utf-8") == "<p>same</p>"


def test_raw_capture_corrupt_content_addressed_collision_fails_closed(
    raw_capture_service: tuple[CrawlerService, Path],
) -> None:
    service, raw_dir = raw_capture_service
    url = "https://example.test/notice"
    html = "<p>expected</p>"
    content_digest = hashlib.sha256(html.encode("utf-8")).hexdigest()
    collision = raw_dir / "html" / f"{content_digest}.html"
    collision.parent.mkdir(parents=True, exist_ok=True)
    collision.write_text("tampered", encoding="utf-8")

    with pytest.raises(ValueError, match="collision"):
        service._save_raw_html(url, html)

    assert collision.read_text(encoding="utf-8") == "tampered"


def test_notice_identity_is_scoped_by_source(tmp_path: Path) -> None:
    service = _service(tmp_path)
    try:
        source_a, _, _ = service.upsert_parsed_notice(
            _notice(source_url="https://source-a.example/notice/2607301", source_name="source-a", notice_code="2607301", notice_version=None),
        )
        source_b, _, _ = service.upsert_parsed_notice(
            _notice(source_url="https://source-b.example/notice/2607301", source_name="source-b", notice_code="2607301", notice_version=None, title="Source B"),
        )

        assert source_a.id != source_b.id
        with service.db.session() as session:
            assert session.scalar(select(func.count()).select_from(Notice)) == 2
            rows = session.scalars(select(Notice).order_by(Notice.id)).all()
            assert [(row.source_name, row.title) for row in rows] == [
                ("source-a", "Tender X"),
                ("source-b", "Source B"),
            ]
    finally:
        asyncio.run(service.close())


def test_same_source_same_revision_updates_one_notice(tmp_path: Path) -> None:
    service = _service(tmp_path)
    try:
        first, _, _ = service.upsert_parsed_notice(_notice(source_url="https://source-a.example/one"))
        second, created, changed = service.upsert_parsed_notice(
            _notice(source_url="https://source-a.example/two", title="Updated")
        )

        assert second.id == first.id
        assert not created
        assert changed
        assert second.title == "Updated"
    finally:
        asyncio.run(service.close())


def test_same_source_different_revision_creates_distinct_notices(tmp_path: Path) -> None:
    service = _service(tmp_path)
    try:
        first, _, _ = service.upsert_parsed_notice(_notice(notice_version="1"))
        second, created, _ = service.upsert_parsed_notice(
            _notice(source_url="https://source-a.example/revised", notice_version="2")
        )

        assert created
        assert first.id != second.id
        with service.db.session() as session:
            assert session.scalar(select(func.count()).select_from(Notice)) == 2
    finally:
        asyncio.run(service.close())


def test_source_local_fallback_remains_stable(tmp_path: Path) -> None:
    service = _service(tmp_path)
    try:
        first, _, _ = service.upsert_parsed_notice(
            _notice(
                source_url="https://source-a.example/local/one",
                source_name="source-a",
                notice_code=None,
                source_notice_id="local-1",
            )
        )
        second, created, changed = service.upsert_parsed_notice(
            _notice(
                source_url="https://source-a.example/local/two",
                source_name="source-a",
                notice_code=None,
                source_notice_id="local-1",
                title="Updated local",
            )
        )

        assert second.id == first.id
        assert not created
        assert changed
    finally:
        asyncio.run(service.close())


def test_semantic_hash_covers_estimated_price(tmp_path: Path) -> None:
    service = _service(tmp_path)
    try:
        baseline = _notice(estimated_price=1_200_000.0)
        first, _, _ = service.upsert_parsed_notice(baseline)
        second, _, changed = service.upsert_parsed_notice(
            replace(baseline, estimated_price=1_300_000.0)
        )
        assert changed
        assert second.content_hash != first.content_hash
    finally:
        asyncio.run(service.close())


def test_semantic_hash_covers_buyer_tax_code(tmp_path: Path) -> None:
    service = _service(tmp_path)
    try:
        baseline = _notice(buyer_tax_code="0101234567")
        first, _, _ = service.upsert_parsed_notice(baseline)
        second, _, changed = service.upsert_parsed_notice(
            replace(baseline, buyer_tax_code="0107654321")
        )
        assert changed
        assert second.content_hash != first.content_hash
    finally:
        asyncio.run(service.close())


def test_semantic_hash_covers_tender_item_fields(tmp_path: Path) -> None:
    service = _service(tmp_path)
    try:
        baseline = _notice(items=[_item()])
        first, _, _ = service.upsert_parsed_notice(baseline)
        second, _, changed = service.upsert_parsed_notice(
            replace(baseline, items=[_item(minimum_quantity=2.0)])
        )
        assert changed
        assert second.content_hash != first.content_hash
    finally:
        asyncio.run(service.close())


def test_semantic_hash_covers_attachment_filename_population(tmp_path: Path) -> None:
    service = _service(tmp_path)
    try:
        baseline = _notice(
            attachments=[ParsedAttachment(source_url="https://source-a.example/boq.xlsx")]
        )
        first, _, _ = service.upsert_parsed_notice(baseline)
        second, _, changed = service.upsert_parsed_notice(
            replace(
                baseline,
                attachments=[
                    ParsedAttachment(
                        source_url="https://source-a.example/boq.xlsx", file_name="boq.xlsx"
                    )
                ],
            )
        )
        assert changed
        assert second.content_hash != first.content_hash
    finally:
        asyncio.run(service.close())


def test_semantic_hash_is_order_deterministic_for_attachments_and_items() -> None:
    attachments = [
        ParsedAttachment(source_url="https://source-a.example/a.pdf", file_name="a.pdf"),
        ParsedAttachment(source_url="https://source-a.example/b.pdf", file_name="b.pdf"),
    ]
    items = [_item(item_code="1"), _item(item_code="2", product_name="Router")]
    first = _notice(attachments=attachments, items=items)
    reordered = replace(first, attachments=list(reversed(attachments)), items=list(reversed(items)))

    assert parsed_content_hash(first) == parsed_content_hash(reordered)


def test_identical_normalized_semantic_state_is_unchanged(tmp_path: Path) -> None:
    service = _service(tmp_path)
    try:
        baseline = _notice(notice_version=" 1 ")
        first, _, _ = service.upsert_parsed_notice(baseline)
        second, created, changed = service.upsert_parsed_notice(
            replace(baseline, notice_version="1")
        )

        assert second.id == first.id
        assert not created
        assert not changed
        assert second.content_hash == first.content_hash
    finally:
        asyncio.run(service.close())
