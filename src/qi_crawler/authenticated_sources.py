from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse

import yaml
from pydantic import BaseModel, Field

from .browser import BrowserFetcher
from .config import AppConfig
from .crawler import CrawlerService
from .parser import ParsedNotice

SOURCE_DIR = Path("data/sources")
SESSION_DIR = Path("data/sessions")


class WebSource(BaseModel):
    name: str
    list_url: str
    item_selector: str = "a[href]"
    link_selector: str = "a"
    next_selector: str | None = None
    search_input: str | None = None
    search_button: str | None = None
    page_ready: str = "body"
    max_pages: int = Field(default=5, ge=1, le=100)

    @property
    def domain(self) -> str:
        return (urlparse(self.list_url).hostname or "").lower()


@dataclass
class AuthenticatedCollectionSummary:
    scanned: int = 0
    matched: int = 0
    inserted: int = 0
    updated: int = 0


def safe_source_name(value: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-").lower()
    if not name:
        raise ValueError("Tên nguồn không hợp lệ")
    return name


def source_path(name: str) -> Path:
    return SOURCE_DIR / f"{safe_source_name(name)}.yaml"


def session_path(name: str) -> Path:
    return SESSION_DIR / f"{safe_source_name(name)}.json"


def save_source(source: WebSource) -> Path:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    path = source_path(source.name)
    path.write_text(
        yaml.safe_dump(source.model_dump(), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return path


def allow_source_domain(config_path: Path, domain: str) -> None:
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    domains = raw.setdefault("allowed_domains", [])
    if domain not in domains:
        domains.append(domain)
        raw["allowed_domains"] = sorted(set(domains))
        config_path.write_text(
            yaml.safe_dump(raw, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )


def load_source(name: str) -> WebSource:
    path = source_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Chưa có nguồn '{name}'. Hãy chạy them-nguon trước.")
    return WebSource.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


async def create_login_session(config: AppConfig, source: WebSource) -> Path:
    browser = BrowserFetcher(config)
    try:
        await browser.ensure_browser_access_allowed(source.list_url)
        await browser.start(headed=True)
        page = await browser.new_page()
        await page.goto(source.list_url, wait_until="domcontentloaded")
        print("Trình duyệt đã mở. Hãy tự đăng nhập, nhập OTP/CAPTCHA nếu website yêu cầu.")
        print("Khi đã nhìn thấy trang danh sách gói thầu, quay lại terminal và nhấn Enter.")
        await asyncio.to_thread(input)
        current_host = (urlparse(page.url).hostname or "").lower()
        if current_host != source.domain and not current_host.endswith(f".{source.domain}"):
            raise ValueError("Sau đăng nhập, trình duyệt đang ở domain khác nguồn đã khai báo.")
        path = session_path(source.name)
        await browser.save_storage_state(path)
        return path
    finally:
        await browser.close()


def _matches(text: str, keyword: str) -> bool:
    folded = text.casefold()
    return all(term.casefold() in folded for term in keyword.split() if term.strip())


async def collect_authenticated_source(
    service: CrawlerService,
    source: WebSource,
    keyword: str,
    limit: int = 50,
) -> AuthenticatedCollectionSummary:
    state = session_path(source.name)
    if not state.exists():
        raise FileNotFoundError(f"Chưa có phiên đăng nhập cho '{source.name}'. Hãy chạy dang-nhap.")
    await service.browser.ensure_browser_access_allowed(source.list_url)
    await service.browser.start(headed=False, storage_state=state)
    page = await service.browser.new_page()
    result = AuthenticatedCollectionSummary()
    seen: set[str] = set()
    try:
        await page.goto(source.list_url, wait_until="domcontentloaded")
        await page.locator(source.page_ready).first.wait_for(state="visible")
        if source.search_input and source.search_button:
            await page.locator(source.search_input).first.fill(keyword)
            await page.locator(source.search_button).first.click()
            await page.wait_for_timeout(service.config.crawl.render_wait_ms)
        for _ in range(source.max_pages):
            items = page.locator(source.item_selector)
            count = await items.count()
            result.scanned += count
            for index in range(count):
                item = items.nth(index)
                text = (await item.inner_text()).strip()
                if not text or not _matches(text, keyword):
                    continue
                candidate = item.locator(source.link_selector).first
                link = candidate if await candidate.count() else item
                href = await link.get_attribute("href")
                if not href:
                    continue
                url = urljoin(page.url, href)
                if url in seen or (urlparse(url).hostname or "").lower() != source.domain:
                    continue
                seen.add(url)
                parsed = ParsedNotice(
                    source_url=url,
                    notice_code=None,
                    title=text[:1000],
                    buyer=None,
                    investor=None,
                    package_price=None,
                    currency=None,
                    published_at=None,
                    closing_at=None,
                    attachments=[],
                    raw_text=text,
                )
                _, created, changed = service.upsert_parsed_notice(
                    parsed, source_kind=f"web:{source.name}"
                )
                result.matched += 1
                result.inserted += int(created)
                result.updated += int(not created and changed)
                if result.matched >= limit:
                    return result
            if not source.next_selector:
                break
            next_button = page.locator(source.next_selector).first
            if await next_button.count() == 0 or not await next_button.is_visible():
                break
            if await next_button.get_attribute("disabled") is not None:
                break
            await next_button.click()
            await page.wait_for_timeout(service.config.crawl.render_wait_ms)
    finally:
        await page.close()
    return result
