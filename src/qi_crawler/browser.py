from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx
from playwright.async_api import (
    Browser,
    BrowserContext,
    Locator,
    Page,
    async_playwright,
)
from playwright.async_api import (
    TimeoutError as PlaywrightTimeoutError,
)

from .compliance import AccessDenied, AccessPolicy, DomainRateLimiter
from .config import AppConfig
from .downloads import (
    DownloadedFile,
    calculate_sha256,
    normalize_extension,
    safe_filename,
    unique_destination,
)
from .parser import extract_detail_links

logger = logging.getLogger(__name__)


class BrowserFetcher:
    def __init__(self, config: AppConfig):
        self.config = config
        self.policy = AccessPolicy(config)
        self.limiter = DomainRateLimiter(config.crawl.requests_per_minute)
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    async def start(self, headed: bool = False, storage_state: Path | None = None) -> None:
        if self._browser and self._context:
            return
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=not headed)
        context_options = {
            "user_agent": self.config.compliance.identify_user_agent,
            "locale": "vi-VN",
            "accept_downloads": True,
        }
        if storage_state and storage_state.exists():
            context_options["storage_state"] = str(storage_state)
        self._context = await self._browser.new_context(
            **context_options,
        )

    async def save_storage_state(self, path: Path) -> None:
        if not self._context:
            raise RuntimeError("Trình duyệt chưa được khởi động")
        path.parent.mkdir(parents=True, exist_ok=True)
        await self._context.storage_state(path=str(path))

    async def close(self) -> None:
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def new_page(self) -> Page:
        if not self._context:
            raise RuntimeError("BrowserFetcher.start() chưa được gọi")
        page = await self._context.new_page()
        page.set_default_timeout(self.config.crawl.browser_timeout_seconds * 1000)
        return page

    async def ensure_browser_access_allowed(self, url: str) -> None:
        """Check allowlist and robots.txt before direct browser automation."""
        self.policy.validate_domain(url)
        async with httpx.AsyncClient(
            timeout=self.config.crawl.request_timeout_seconds,
            headers={"User-Agent": self.config.compliance.identify_user_agent},
            follow_redirects=True,
        ) as client:
            if not await self.policy.allowed_by_robots(client, url):
                raise AccessDenied(f"robots.txt không cho phép tự động truy cập URL: {url}")

    async def fetch_html(self, url: str) -> str:
        self.policy.validate_domain(url)
        # robots.txt is checked by the HTTP fetcher before browser fallback.
        await self.limiter.wait(url)
        page = await self.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_selector(self.config.selectors.page_ready)
            if self.config.crawl.render_wait_ms:
                await page.wait_for_timeout(self.config.crawl.render_wait_ms)
            html = await page.content()
            self.policy.detect_block_page(html)
            return html
        finally:
            await page.close()

    async def collect_paginated_links(
        self,
        url: str,
        keyword: str | None = None,
        max_pages: int | None = None,
        headed: bool = False,
    ) -> list[str]:
        """Search and paginate on a permitted dynamic list page."""
        await self.ensure_browser_access_allowed(url)
        await self.start(headed=headed)
        page = await self.new_page()
        links: list[str] = []
        seen: set[str] = set()
        page_limit = min(max_pages or self.config.crawl.max_pages_per_run, self.config.crawl.max_pages_per_run)

        try:
            await self.limiter.wait(url)
            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_selector(self.config.selectors.page_ready)

            if keyword:
                if not self.config.selectors.search_input or not self.config.selectors.search_button:
                    raise ValueError(
                        "Cần cấu hình selectors.search_input và selectors.search_button để tìm kiếm."
                    )
                await page.locator(self.config.selectors.search_input).first.fill(keyword)
                await self.limiter.wait(page.url)
                await page.locator(self.config.selectors.search_button).first.click()

            ready_selector = self.config.selectors.result_ready or self.config.selectors.list_item
            await page.locator(ready_selector).first.wait_for(state="visible")
            if self.config.crawl.render_wait_ms:
                await page.wait_for_timeout(self.config.crawl.render_wait_ms)

            for page_number in range(1, page_limit + 1):
                html = await page.content()
                self.policy.detect_block_page(html)
                page_links = extract_detail_links(
                    html,
                    page.url,
                    self.config.selectors.list_item,
                    self.config.selectors.detail_link,
                    self.config.allowed_domains,
                )
                for item in page_links:
                    if item not in seen:
                        seen.add(item)
                        links.append(item)
                logger.info("Trang %s: tổng cộng %s link duy nhất", page_number, len(links))

                if page_number >= page_limit:
                    break
                next_button = page.locator(self.config.selectors.next_page).first
                if await next_button.count() == 0 or not await next_button.is_visible():
                    break
                disabled = await next_button.get_attribute("disabled")
                aria_disabled = await next_button.get_attribute("aria-disabled")
                css_class = (await next_button.get_attribute("class") or "").lower()
                if disabled is not None or aria_disabled == "true" or "disabled" in css_class:
                    break

                first_link = page.locator(self.config.selectors.list_item).first
                previous_href = await first_link.get_attribute("href") if await first_link.count() else None
                await self.limiter.wait(page.url)
                await next_button.click()
                if self.config.crawl.render_wait_ms:
                    await page.wait_for_timeout(self.config.crawl.render_wait_ms)

                # Avoid infinite loops when a Next button does not change the result set.
                current_first = page.locator(self.config.selectors.list_item).first
                current_href = await current_first.get_attribute("href") if await current_first.count() else None
                if previous_href and current_href == previous_href:
                    logger.warning("Nút Next không làm thay đổi trang; dừng phân trang.")
                    break
        finally:
            await page.close()
        return links

    async def download_from_click(
        self,
        page: Page,
        package_id: str,
        locator: Locator,
        filename_hint: str | None = None,
    ) -> DownloadedFile:
        """Capture one browser download triggered by an already-resolved locator."""
        self.policy.validate_domain(page.url)
        await self.limiter.wait(page.url)
        await locator.wait_for(state="visible")

        async with page.expect_download(
            timeout=self.config.crawl.browser_timeout_seconds * 1000
        ) as download_info:
            await locator.click()

        download = await download_info.value
        failure = await download.failure()
        if failure:
            raise RuntimeError(f"Playwright download thất bại: {failure}")

        suggested = safe_filename(download.suggested_filename or filename_hint)
        filename = normalize_extension(
            suggested,
            content_type=None,
            allowed_extensions=self.config.storage.allowed_attachment_extensions,
        )
        package_dir = self.config.storage.download_dir / safe_filename(
            package_id, fallback="unknown-package"
        )
        package_dir.mkdir(parents=True, exist_ok=True)
        destination = unique_destination(package_dir, filename)
        temporary = destination.with_name(f"{destination.name}.part")

        try:
            await download.save_as(temporary)
            size = temporary.stat().st_size
            max_bytes = self.config.storage.max_attachment_mb * 1024 * 1024
            if size > max_bytes:
                raise ValueError(
                    f"Tệp {filename} vượt giới hạn {self.config.storage.max_attachment_mb} MB"
                )
            sha256 = calculate_sha256(temporary)
            temporary.replace(destination)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise

        source_url = download.url
        if source_url.startswith(("http://", "https://")):
            self.policy.validate_domain(source_url)
        logger.info("Đã tải bằng Playwright: %s", destination)
        return DownloadedFile(
            file_name=filename,
            local_path=destination,
            sha256=sha256,
            size_bytes=size,
            source_url=source_url,
            method="playwright",
        )

    async def download_page_attachments(
        self,
        url: str,
        package_id: str,
        headed: bool = False,
    ) -> tuple[list[DownloadedFile], list[str]]:
        """Download every configured attachment row on a permitted detail page."""
        rows_selector = self.config.selectors.attachment_rows
        button_selector = self.config.selectors.attachment_download_button
        if not rows_selector or not button_selector:
            raise ValueError(
                "Cần cấu hình selectors.attachment_rows và "
                "selectors.attachment_download_button."
            )

        await self.ensure_browser_access_allowed(url)
        await self.start(headed=headed)
        page = await self.new_page()
        downloaded: list[DownloadedFile] = []
        errors: list[str] = []
        try:
            await self.limiter.wait(url)
            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_selector(self.config.selectors.page_ready)
            if self.config.crawl.render_wait_ms:
                await page.wait_for_timeout(self.config.crawl.render_wait_ms)
            self.policy.detect_block_page(await page.content())

            rows = page.locator(rows_selector)
            count = await rows.count()
            if count == 0:
                logger.warning("Không tìm thấy hàng attachment bằng selector: %s", rows_selector)
            for index in range(count):
                row = rows.nth(index)
                button = row.locator(button_selector).first
                if await button.count() == 0:
                    continue
                filename_hint = None
                if self.config.selectors.attachment_name:
                    name_locator = row.locator(self.config.selectors.attachment_name).first
                    if await name_locator.count():
                        filename_hint = (await name_locator.inner_text()).strip()
                if not filename_hint:
                    filename_hint = (await row.inner_text()).strip()[:180]
                try:
                    item = await self.download_from_click(
                        page=page,
                        package_id=package_id,
                        locator=button,
                        filename_hint=filename_hint,
                    )
                    downloaded.append(item)
                except PlaywrightTimeoutError:
                    message = f"Hàng {index + 1}: click không phát sinh sự kiện download"
                    logger.exception(message)
                    errors.append(message)
                except Exception as exc:
                    message = f"Hàng {index + 1}: {exc}"
                    logger.exception("Tải attachment động thất bại")
                    errors.append(message)
        finally:
            await page.close()
        return downloaded, errors

    async def discover_json(self, url: str, duration_seconds: int, headed: bool) -> list[Path]:
        if not headed:
            logger.info("Discovery headless: chỉ ghi phản hồi tự động phát sinh khi mở trang.")
        await self.ensure_browser_access_allowed(url)
        await self.start(headed=headed)
        page = await self.new_page()
        saved: list[Path] = []
        pending: list[asyncio.Task] = []

        async def capture(response) -> None:
            try:
                parsed = urlparse(response.url)
                if not any(
                    parsed.hostname == domain or (parsed.hostname or "").endswith(f".{domain}")
                    for domain in self.config.allowed_domains
                ):
                    return
                content_type = (await response.all_headers()).get("content-type", "")
                if "json" not in content_type.lower():
                    return
                body = await response.body()
                if len(body) > 10 * 1024 * 1024:
                    return
                try:
                    data = json.loads(body)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    return
                stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
                slug = re.sub(r"[^a-zA-Z0-9._-]+", "_", parsed.path.strip("/") or "root")[-100:]
                path = self.config.storage.discovery_dir / f"{stamp}_{slug}.json"
                envelope = {
                    "captured_at": datetime.now(UTC).isoformat(),
                    "request_url": response.url,
                    "status": response.status,
                    "data": data,
                }
                path.write_text(json.dumps(envelope, ensure_ascii=False, indent=2), encoding="utf-8")
                saved.append(path)
                logger.info("Đã ghi JSON: %s", path)
            except Exception as exc:  # noqa: BLE001 - malformed third-party responses are isolated
                logger.debug("Bỏ qua response discovery: %s", exc)

        def on_response(response) -> None:
            pending.append(asyncio.create_task(capture(response)))

        page.on("response", on_response)
        try:
            await self.limiter.wait(url)
            await page.goto(url, wait_until="domcontentloaded")
            logger.info(
                "Discovery đang chạy. Với --headed, hãy thao tác tìm kiếm trên cửa sổ trình duyệt."
            )
            await page.wait_for_timeout(duration_seconds * 1000)
            self.policy.detect_block_page(await page.content())
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)
        finally:
            await page.close()
        return saved
