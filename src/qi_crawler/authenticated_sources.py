from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse

import yaml
from pydantic import BaseModel, Field

from .browser import BrowserFetcher
from .compliance import AccessDenied
from .config import AppConfig
from .crawler import CrawlerService
from .keywords import matches_any_keyword, normalize_keyword
from .parser import ParsedNotice, extract_detail_links, parse_notice_html

logger = logging.getLogger(__name__)

SOURCE_DIR = Path("data/sources")
SESSION_DIR = Path("data/sessions")
EGP_VIETNAM_URL = "https://muasamcong.mpi.gov.vn/vi/web/guest/contractor-selection"


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


@dataclass(frozen=True)
class SourceValidation:
    current_url: str
    item_count: int
    link_count: int
    ready: bool


def egp_vietnam_source(
    name: str = "egp-vietnam",
    list_url: str = EGP_VIETNAM_URL,
) -> WebSource:
    """Return a conservative e-GP profile based on stable detail URL markers."""
    return WebSource(
        name=name,
        list_url=list_url,
        item_selector=(
            'a[href*="contractor-selection"][href*="notifyNo="], '
            'a[href*="contractor-selection"][href*="step=tbmt"]'
        ),
        link_selector="a[href]",
        next_selector=(
            'a[rel="next"], button[aria-label="Next"]:not([disabled]), '
            '.pagination .next:not(.disabled) a'
        ),
        page_ready="main, body",
        max_pages=5,
    )


def extract_source_links(html: str, source: WebSource) -> list[str]:
    """Extract allowed tender-detail links from a saved list-page snapshot.

    This is the offline counterpart of the configured browser selectors.  It is
    deliberately small so source profiles can be regression-tested without a
    live login session or a browser in CI.
    """
    return extract_detail_links(
        html,
        source.list_url,
        source.item_selector,
        source.link_selector,
        [source.domain],
    )


def safe_source_name(value: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9_-]+", "-", normalize_keyword(value)).strip("-")
    if not name:
        raise ValueError("Ten nguon khong hop le")
    return name


def source_path(name: str) -> Path:
    return SOURCE_DIR / f"{safe_source_name(name)}.yaml"


def session_path(name: str) -> Path:
    return SESSION_DIR / f"{safe_source_name(name)}_storage_state.json"


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
        raise FileNotFoundError(f"Chua co nguon '{name}'. Hay chay them-nguon truoc.")
    return WebSource.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


async def create_login_session(
    config: AppConfig,
    source: WebSource,
    wait_for_confirmation: Callable[[], Awaitable[None]] | None = None,
    browser_ready: Callable[[], None] | None = None,
) -> Path:
    browser = BrowserFetcher(config)
    try:
        await browser.ensure_browser_access_allowed(source.list_url)
        await browser.start(headed=True)
        page = await browser.new_page()
        await page.goto(source.list_url, wait_until="domcontentloaded")
        if browser_ready is not None:
            browser_ready()
        if wait_for_confirmation is None:
            print("Trinh duyet da mo. Hay tu dang nhap, nhap OTP/CAPTCHA neu website yeu cau.")
            print("Khi da nhin thay trang danh sach goi thau, quay lai terminal va nhan Enter.")
            await asyncio.to_thread(input)
        else:
            await wait_for_confirmation()
        current_host = (urlparse(page.url).hostname or "").lower()
        if current_host != source.domain and not current_host.endswith(f".{source.domain}"):
            raise ValueError("Sau dang nhap, trinh duyet dang o domain khac nguon da khai bao.")
        source.list_url = page.url
        save_source(source)
        path = session_path(source.name)
        await browser.save_storage_state(path)
        return path
    finally:
        await browser.close()


async def collect_authenticated_source(
    service: CrawlerService,
    source: WebSource,
    keyword: str | tuple[str, ...],
    limit: int = 50,
) -> AuthenticatedCollectionSummary:
    state = session_path(source.name)
    if not state.exists():
        raise FileNotFoundError(f"Chua co phien dang nhap cho '{source.name}'. Hay chay dang-nhap.")
    await service.browser.ensure_browser_access_allowed(source.list_url)
    await service.browser.start(headed=False, storage_state=state)
    page = await service.browser.new_page()
    result = AuthenticatedCollectionSummary()
    seen: set[str] = set()
    try:
        await page.goto(source.list_url, wait_until="domcontentloaded")
        await page.locator(source.page_ready).first.wait_for(state="visible")
        if source.search_input and source.search_button:
            search_value = keyword if isinstance(keyword, str) else keyword[0]
            await page.locator(source.search_input).first.fill(search_value)
            await page.locator(source.search_button).first.click()
            await page.wait_for_timeout(service.config.crawl.render_wait_ms)
        for _ in range(source.max_pages):
            items = page.locator(source.item_selector)
            count = await items.count()
            result.scanned += count
            for index in range(count):
                item = items.nth(index)
                text = (await item.inner_text()).strip()
                terms = (keyword,) if isinstance(keyword, str) else keyword
                if not text or not matches_any_keyword(text, terms):
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
                detail_page = None
                try:
                    await service.browser.ensure_browser_access_allowed(url)
                    await service.browser.limiter.wait(url)
                    detail_page = await service.browser.new_page()
                    await detail_page.goto(url, wait_until="domcontentloaded")
                    await detail_page.locator(source.page_ready).first.wait_for(state="visible")
                    if service.config.crawl.render_wait_ms:
                        await detail_page.wait_for_timeout(service.config.crawl.render_wait_ms)
                    html = await detail_page.content()
                    service.browser.policy.detect_block_page(html)
                    parsed = parse_notice_html(
                        html,
                        url,
                        service.config.storage.allowed_attachment_extensions,
                    )
                    parsed.title = parsed.title or text[:1000]
                    parsed.raw_text = parsed.raw_text or text
                except AccessDenied:
                    # Authentication, CAPTCHA and access-policy failures are not
                    # incomplete metadata. Stop so the operator can intervene.
                    raise
                except Exception as exc:  # noqa: BLE001 - keep list metadata for manual review
                    logger.warning("Khong doc duoc trang chi tiet %s: %s", url, exc)
                finally:
                    if detail_page is not None:
                        await detail_page.close()
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


async def validate_authenticated_source(
    config: AppConfig,
    source: WebSource,
) -> SourceValidation:
    """Validate saved login state and source selectors without collecting data."""
    state = session_path(source.name)
    if not state.exists():
        raise FileNotFoundError(
            f"Chua co phien dang nhap cho '{source.name}'. Hay chay dang-nhap."
        )
    browser = BrowserFetcher(config)
    try:
        await browser.ensure_browser_access_allowed(source.list_url)
        await browser.start(headed=False, storage_state=state)
        page = await browser.new_page()
        try:
            await page.goto(source.list_url, wait_until="domcontentloaded")
            await page.locator(source.page_ready).first.wait_for(state="visible")
            items = page.locator(source.item_selector)
            item_count = await items.count()
            link_count = 0
            for index in range(min(item_count, 50)):
                item = items.nth(index)
                candidate = item.locator(source.link_selector).first
                link = candidate if await candidate.count() else item
                if await link.get_attribute("href"):
                    link_count += 1
            return SourceValidation(
                current_url=page.url,
                item_count=item_count,
                link_count=link_count,
                ready=item_count > 0 and link_count > 0,
            )
        finally:
            await page.close()
    finally:
        await browser.close()
