from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from sqlalchemy import func, select

from qi_crawler.compliance import AccessDenied
from qi_crawler.config import AppConfig, SourceConfig
from qi_crawler.crawler import CrawlerService
from qi_crawler.models import CrawlRun, CrawlTask, Notice
from qi_crawler.source_adapters import CotecconsAdapter

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "golden" / "source"
LIST_URL = "https://ebidding.coteccons.vn/Index"
PAGE_2 = "https://ebidding.coteccons.vn/Index?page=2"
PAGE_3 = "https://ebidding.coteccons.vn/Index?page=3"


def _fixture(name: str) -> str:
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def _service(tmp_path: Path, retries: int = 0) -> CrawlerService:
    config = AppConfig.model_validate(
        {
            "sources": {
                "coteccons": {
                    "enabled": True,
                    "priority": 1,
                    "domain": "ebidding.coteccons.vn",
                    "adapter": "coteccons",
                }
            },
            "crawl": {
                "concurrency": 1,
                "max_retries": retries,
                "retry_backoff_seconds": 0,
            },
            "storage": {
                "database_url": f"sqlite:///{tmp_path / 'scan.db'}",
                "raw_dir": str(tmp_path / "raw"),
                "download_attachments": False,
            },
        }
    )
    return CrawlerService(config)


def _detail_html(url: str) -> str:
    source_id = url.rsplit("/", 1)[-1]
    return f"""
    <html><body>
      <div>Tên gói thầu: GÓI THẦU {source_id}</div>
      <div>Bên mời thầu: Coteccons</div>
      <div>Thời điểm đóng thầu: 10:00 20/08/2026</div>
    </body></html>
    """


def test_coteccons_discovery_normalizes_and_filters_detail_links() -> None:
    adapter = CotecconsAdapter(
        "coteccons", SourceConfig(domain="ebidding.coteccons.vn", adapter="coteccons")
    )

    entries = adapter.discover_tenders(_fixture("coteccons_list_page_1.html"), LIST_URL)

    assert [(entry.source_notice_id, entry.url) for entry in entries] == [
        ("2607301", "https://ebidding.coteccons.vn/Index/ChiTiet/2607301"),
        ("2607302", "https://ebidding.coteccons.vn/Index/ChiTiet/2607302"),
    ]
    assert adapter.pagination_links(_fixture("coteccons_list_page_1.html"), LIST_URL) == [PAGE_2]


def test_coteccons_discovery_paginates_deduplicates_and_stops_loops(tmp_path: Path) -> None:
    service = _service(tmp_path)
    pages = {
        LIST_URL: _fixture("coteccons_list_page_1.html"),
        PAGE_2: _fixture("coteccons_list_page_2.html"),
        PAGE_3: _fixture("coteccons_list_page_3.html"),
    }
    calls: list[str] = []

    async def fetch(url: str) -> str:
        calls.append(url)
        return pages[url]

    try:
        service._get_html = fetch  # type: ignore[method-assign]
        _, entries, page_count = asyncio.run(service._discover_list_pages(LIST_URL, max_pages=5))

        assert [entry.source_notice_id for entry in entries] == ["2607301", "2607302", "2607303"]
        assert page_count == 3
        assert calls == [LIST_URL, PAGE_2, PAGE_3]
    finally:
        asyncio.run(service.close())


def test_coteccons_discovery_respects_max_pages(tmp_path: Path) -> None:
    service = _service(tmp_path)
    pages = {
        LIST_URL: _fixture("coteccons_list_page_1.html"),
        PAGE_2: _fixture("coteccons_list_page_2.html"),
    }

    async def fetch(url: str) -> str:
        return pages[url]

    try:
        service._get_html = fetch  # type: ignore[method-assign]
        _, entries, page_count = asyncio.run(service._discover_list_pages(LIST_URL, max_pages=2))

        assert page_count == 2
        assert [entry.source_notice_id for entry in entries] == ["2607301", "2607302", "2607303"]
    finally:
        asyncio.run(service.close())


def test_scan_filters_accented_keywords_without_modifying_keyword_pool(tmp_path: Path) -> None:
    service = _service(tmp_path)
    groups_path = Path("keyword-groups.yaml")
    before = groups_path.read_bytes()

    async def fetch(url: str) -> str:
        if url == LIST_URL:
            return _fixture("coteccons_list_page_1.html")
        return _detail_html(url)

    try:
        service._get_html = fetch  # type: ignore[method-assign]
        summary = asyncio.run(
            service.scan_list(LIST_URL, keyword_terms=("chong tham",), max_pages=1)
        )

        assert (summary.discovered, summary.matched, summary.skipped, summary.success) == (2, 1, 1, 1)
        assert groups_path.read_bytes() == before
    finally:
        asyncio.run(service.close())


def test_scan_updates_existing_notice_without_duplicates(tmp_path: Path) -> None:
    service = _service(tmp_path)

    async def fetch(url: str) -> str:
        if url == LIST_URL:
            return _fixture("coteccons_list_page_1.html")
        return _detail_html(url)

    try:
        service._get_html = fetch  # type: ignore[method-assign]
        first = asyncio.run(service.scan_list(LIST_URL, max_pages=1))
        second = asyncio.run(service.scan_list(LIST_URL, max_pages=1))

        assert (first.new, first.existing, first.success) == (2, 0, 2)
        assert (second.new, second.existing, second.success) == (0, 2, 2)
        with service.db.session() as session:
            assert session.scalar(select(func.count()).select_from(Notice)) == 2
            assert {
                value
                for value in session.scalars(select(Notice.source_notice_id)).all()
            } == {"2607301", "2607302"}
    finally:
        asyncio.run(service.close())


def test_scan_resumes_interrupted_batch_without_recrawling_completed_tasks(tmp_path: Path) -> None:
    service = _service(tmp_path)
    second_url = "https://ebidding.coteccons.vn/Index/ChiTiet/2607302"
    started = asyncio.Event()
    never = asyncio.Event()

    async def interrupted_fetch(url: str) -> str:
        if url == LIST_URL:
            return _fixture("coteccons_list_page_1.html")
        if url == second_url:
            started.set()
            await never.wait()
        return _detail_html(url)

    async def interrupt() -> None:
        task = asyncio.create_task(service.scan_list(LIST_URL, max_pages=1))
        await started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    try:
        service._get_html = interrupted_fetch  # type: ignore[method-assign]
        asyncio.run(interrupt())
        with service.db.session() as session:
            run = session.scalar(select(CrawlRun))
            assert run is not None and run.status == "interrupted"
            assert [task.status for task in session.scalars(select(CrawlTask).order_by(CrawlTask.page_index))] == [
                "COMPLETED",
                "RUNNING",
            ]

        resumed_calls: list[str] = []

        async def resumed_fetch(url: str) -> str:
            resumed_calls.append(url)
            return _detail_html(url)

        service._get_html = resumed_fetch  # type: ignore[method-assign]
        summary = asyncio.run(service.scan_list(LIST_URL, resume=True))

        assert summary.success == 2
        assert resumed_calls == [second_url]
    finally:
        asyncio.run(service.close())


def test_one_failed_detail_does_not_stop_scan_batch(tmp_path: Path) -> None:
    service = _service(tmp_path)
    failed_url = "https://ebidding.coteccons.vn/Index/ChiTiet/2607302"

    async def fetch(url: str) -> str:
        if url == LIST_URL:
            return _fixture("coteccons_list_page_1.html")
        if url == failed_url:
            raise ValueError("malformed detail")
        return _detail_html(url)

    try:
        service._get_html = fetch  # type: ignore[method-assign]
        summary = asyncio.run(service.scan_list(LIST_URL, max_pages=1))

        assert (summary.success, summary.failed) == (1, 1)
    finally:
        asyncio.run(service.close())


def test_scan_queues_more_than_config_page_limit_without_silent_truncation(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)
    service.config.crawl.max_pages_per_run = 10
    detail_urls = [
        f"https://ebidding.coteccons.vn/Index/ChiTiet/{2607400 + index}"
        for index in range(12)
    ]
    list_html = "<html><body>" + "".join(
        f'<a href="{url}">Tender {index}</a>' for index, url in enumerate(detail_urls)
    ) + "</body></html>"

    async def fetch(url: str) -> str:
        return list_html if url == LIST_URL else _detail_html(url)

    try:
        service._get_html = fetch  # type: ignore[method-assign]
        summary = asyncio.run(service.scan_list(LIST_URL, max_pages=1))

        assert summary.matched == summary.queued + summary.limited
        assert summary.success + summary.failed + summary.pending == summary.queued
        assert (summary.discovered, summary.matched) == (12, 12)
        assert (summary.queued, summary.limited, summary.pending) == (12, 0, 0)
        assert summary.success == 12
        with service.db.session() as session:
            assert session.scalar(select(func.count()).select_from(CrawlTask)) == 12
    finally:
        asyncio.run(service.close())


def test_access_denied_stops_remaining_scan_tasks(tmp_path: Path) -> None:
    service = _service(tmp_path)
    detail_urls = [
        f"https://ebidding.coteccons.vn/Index/ChiTiet/{source_id}"
        for source_id in (2607501, 2607502, 2607503)
    ]
    list_html = "<html><body>" + "".join(
        f'<a href="{url}">Tender</a>' for url in detail_urls
    ) + "</body></html>"
    calls: list[str] = []

    async def fetch(url: str) -> str:
        calls.append(url)
        if url == LIST_URL:
            return list_html
        if url == detail_urls[1]:
            raise AccessDenied("HTTP 403: HUMAN_REQUIRED")
        return _detail_html(url)

    try:
        service._get_html = fetch  # type: ignore[method-assign]
        with pytest.raises(AccessDenied, match="HUMAN_REQUIRED"):
            asyncio.run(service.scan_list(LIST_URL, max_pages=1))

        assert calls == [LIST_URL, detail_urls[0], detail_urls[1]]
        assert service.human_required_reason == "HTTP 403: HUMAN_REQUIRED"
        with service.db.session() as session:
            tasks = session.scalars(select(CrawlTask).order_by(CrawlTask.page_index)).all()
            assert [task.status for task in tasks] == [
                "COMPLETED",
                "HUMAN_REQUIRED",
                "PENDING",
            ]
            run = session.scalar(select(CrawlRun))
            assert run is not None and run.status == "human_required"
    finally:
        asyncio.run(service.close())


def test_coteccons_discovery_renders_when_http_html_has_no_detail_links(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)
    calls: list[str] = []

    async def fetch(_: str) -> str:
        return "<html><body><div id='app'></div>" + (" " * 6000) + "</body></html>"

    async def allow(url: str) -> None:
        calls.append(f"robots:{url}")

    async def start(headed: bool = False) -> None:
        calls.append(f"start:{headed}")

    async def render(url: str) -> str:
        calls.append(f"render:{url}")
        return _fixture("coteccons_list_page_1.html")

    try:
        service._get_html = fetch  # type: ignore[method-assign]
        service.browser.ensure_browser_access_allowed = allow  # type: ignore[method-assign]
        service.browser.start = start  # type: ignore[method-assign]
        service.browser.fetch_html = render  # type: ignore[method-assign]

        _, entries, pages_scanned = asyncio.run(
            service._discover_list_pages(LIST_URL, max_pages=1)
        )

        assert pages_scanned == 1
        assert [entry.source_notice_id for entry in entries] == ["2607301", "2607302"]
        assert calls == [f"robots:{LIST_URL}", "start:False", f"render:{LIST_URL}"]
    finally:
        asyncio.run(service.close())
