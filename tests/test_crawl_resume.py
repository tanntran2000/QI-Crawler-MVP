import asyncio
from pathlib import Path

import httpx
import pytest
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from sqlalchemy import select

from qi_crawler.compliance import AccessDenied
from qi_crawler.config import AppConfig
from qi_crawler.crawler import CrawlerService
from qi_crawler.models import CrawlRun, CrawlTask


def _service(
    tmp_path: Path,
    retries: int = 1,
    download_attachments: bool = False,
) -> CrawlerService:
    config = AppConfig()
    config.crawl.concurrency = 1
    config.crawl.max_retries = retries
    config.crawl.retry_backoff_seconds = 0
    config.storage.database_url = f"sqlite:///{tmp_path / 'crawl.db'}"
    config.storage.raw_dir = tmp_path / "raw"
    config.storage.download_dir = tmp_path / "downloads"
    config.storage.download_attachments = download_attachments
    return CrawlerService(config)


def _html(url: str) -> str:
    code = url.rsplit("/", 1)[-1]
    return f"""
    <html><body>
      <div>Ma TBMT: {code}</div>
      <div>Ten goi thau: Goi {code}</div>
      <div>Ben moi thau: QI</div>
      <div>Gia goi thau: 1000000 VND</div>
      <div>Thoi diem dong thau: 10:00 20/08/2026</div>
    </body></html>
    """


def test_interrupted_run_resumes_only_incomplete_urls(tmp_path: Path) -> None:
    service = _service(tmp_path)
    urls = [f"https://example.test/tender/IB26000{index}" for index in range(1, 7)]
    first_calls: list[str] = []
    fourth_started = asyncio.Event()
    block_until_cancelled = asyncio.Event()

    async def interrupted_fetch(url: str) -> str:
        first_calls.append(url)
        if url == urls[3]:
            fourth_started.set()
            await block_until_cancelled.wait()
        return _html(url)

    async def run_until_interrupted() -> None:
        worker = asyncio.create_task(service.crawl_urls(urls, source_name="test"))
        await fourth_started.wait()
        worker.cancel()
        with pytest.raises(asyncio.CancelledError):
            await worker

    try:
        service._get_html = interrupted_fetch  # type: ignore[method-assign]
        asyncio.run(run_until_interrupted())

        with service.db.session() as session:
            run = session.scalar(select(CrawlRun))
            assert run is not None
            assert run.status == "interrupted"
            assert [task.status for task in session.scalars(
                select(CrawlTask).where(CrawlTask.crawl_run_id == run.id).order_by(CrawlTask.page_index)
            )] == ["COMPLETED", "COMPLETED", "COMPLETED", "RUNNING", "PENDING", "PENDING"]
            run_id = run.id

        resumed_calls: list[str] = []

        async def resumed_fetch(url: str) -> str:
            resumed_calls.append(url)
            return _html(url)

        service._get_html = resumed_fetch  # type: ignore[method-assign]
        ok, failed = asyncio.run(service.resume_crawl(run_id))

        assert first_calls == urls[:4]
        assert resumed_calls == urls[3:]
        assert (ok, failed) == (6, 0)
        with service.db.session() as session:
            statuses = session.scalars(
                select(CrawlTask.status).where(CrawlTask.crawl_run_id == run_id)
            ).all()
            assert statuses == ["COMPLETED"] * 6
    finally:
        asyncio.run(service.close())


def test_retry_is_limited_and_one_failed_url_does_not_stop_batch(tmp_path: Path) -> None:
    service = _service(tmp_path, retries=1)
    urls = ["https://example.test/tender/IB2600101", "https://example.test/tender/IB2600102"]
    attempts: dict[str, int] = {url: 0 for url in urls}

    async def fetch(url: str) -> str:
        attempts[url] += 1
        if url == urls[0] and attempts[url] == 1:
            raise httpx.ReadTimeout("transient timeout")
        if url == urls[1]:
            raise httpx.ReadTimeout("permanent timeout")
        return _html(url)

    try:
        service._get_html = fetch  # type: ignore[method-assign]
        ok, failed = asyncio.run(service.crawl_urls(urls, source_name="test"))

        assert (ok, failed) == (1, 1)
        assert attempts == {urls[0]: 2, urls[1]: 2}
        with service.db.session() as session:
            tasks = session.scalars(select(CrawlTask).order_by(CrawlTask.page_index)).all()
            assert [(task.status, task.attempt_count) for task in tasks] == [
                ("COMPLETED", 2),
                ("FAILED", 2),
            ]
            run = session.scalar(select(CrawlRun))
            assert run is not None
            assert run.status == "partial"
    finally:
        asyncio.run(service.close())


def test_retry_classifies_httpx_and_playwright_errors(tmp_path: Path) -> None:
    service = _service(tmp_path)
    try:
        assert service._is_retryable_crawl_error(httpx.ReadTimeout("timeout"))
        assert service._is_retryable_crawl_error(httpx.ConnectError("connection failed"))
        assert service._is_retryable_crawl_error(PlaywrightTimeoutError("timeout"))
    finally:
        asyncio.run(service.close())


def test_batch_crawl_downloads_pending_attachments(tmp_path: Path) -> None:
    service = _service(tmp_path, download_attachments=True)
    downloaded: list[tuple[int, int]] = []

    async def fetch(_: str) -> str:
        return _html("https://example.test/tender/IB2600201").replace(
            "</body>", '<a href="/attachments/hsmt.pdf">Tải E-HSMT</a></body>'
        )

    async def download(notice_id: int, attachment_id: int) -> None:
        downloaded.append((notice_id, attachment_id))

    try:
        service._get_html = fetch  # type: ignore[method-assign]
        service._download_attachment_http = download  # type: ignore[method-assign]
        assert asyncio.run(service.crawl_urls(["https://example.test/tender/IB2600201"])) == (1, 0)
        assert len(downloaded) == 1
    finally:
        asyncio.run(service.close())


def test_single_crawl_surfaces_human_required_for_blocked_attachment(tmp_path: Path) -> None:
    service = _service(tmp_path, download_attachments=True)

    async def fetch(_: str) -> str:
        return _html("https://example.test/tender/IB2600202").replace(
            "</body>", '<a href="/attachments/hsmt.pdf">Tải E-HSMT</a></body>'
        )

    async def blocked_download(_notice_id: int, _attachment_id: int) -> None:
        raise AccessDenied("HTTP 403 attachment; HUMAN_REQUIRED")

    try:
        service._get_html = fetch  # type: ignore[method-assign]
        service._download_attachment_http = blocked_download  # type: ignore[method-assign]
        with pytest.raises(AccessDenied, match="HUMAN_REQUIRED"):
            asyncio.run(service.crawl_notice("https://example.test/tender/IB2600202"))
    finally:
        asyncio.run(service.close())
