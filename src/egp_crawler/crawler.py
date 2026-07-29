from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from .browser import BrowserFetcher
from .compliance import AccessDenied
from .config import AppConfig
from .db import Database
from .downloads import (
    DownloadedFile,
    normalize_extension,
    safe_filename,
    unique_destination,
)
from .http_client import HttpFetcher
from .models import Attachment, CrawlRun, Notice
from .parser import ParsedNotice, extract_detail_links, parse_notice_html
from .validation import validate_notice

logger = logging.getLogger(__name__)


def url_hash(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def parsed_content_hash(parsed: ParsedNotice) -> str:
    payload = {
        "notice_code": parsed.notice_code,
        "title": parsed.title,
        "buyer": parsed.buyer,
        "investor": parsed.investor,
        "package_price": parsed.package_price,
        "currency": parsed.currency,
        "published_at": parsed.published_at,
        "closing_at": parsed.closing_at,
        "attachments": sorted(item.source_url for item in parsed.attachments),
        "raw_text": parsed.raw_text,
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class CrawlerService:
    def __init__(self, config: AppConfig):
        self.config = config
        self.db = Database(config.storage.database_url)
        self.db.create_all()
        self.http = HttpFetcher(config)
        self.browser = BrowserFetcher(config)
        self._browser_started = False

    async def close(self) -> None:
        await self.http.close()
        if self._browser_started:
            await self.browser.close()

    async def _ensure_browser(self, headed: bool = False) -> None:
        if not self._browser_started:
            await self.browser.start(headed=headed)
            self._browser_started = True

    async def _get_html(self, url: str) -> str:
        try:
            result = await self.http.fetch(url)
            if self.config.crawl.use_browser_fallback and len(result.text) < 5000:
                raise ValueError("HTML shell quá ngắn; chuyển sang browser")
            return result.text
        except AccessDenied:
            raise
        except Exception as exc:
            if not self.config.crawl.use_browser_fallback:
                raise
            logger.info("HTTP fetch chưa đủ/không thành công (%s), dùng Playwright: %s", exc, url)
            # HttpFetcher already checked robots.txt before this fallback.
            await self._ensure_browser(headed=False)
            return await self.browser.fetch_html(url)

    def _save_raw_html(self, url: str, html: str) -> Path:
        directory = self.config.storage.raw_dir / "html"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{url_hash(url)}.html"
        path.write_text(html, encoding="utf-8")
        return path

    async def crawl_notice(self, url: str, download_attachments: bool | None = None) -> Notice:
        html = await self._get_html(url)
        raw_path = self._save_raw_html(url, html)
        parsed = parse_notice_html(
            html,
            url,
            self.config.storage.allowed_attachment_extensions,
        )
        notice, _, _ = self.upsert_parsed_notice(parsed, raw_html_path=raw_path, source_kind="web")
        should_download = (
            self.config.storage.download_attachments
            if download_attachments is None
            else download_attachments
        )
        if should_download:
            with self.db.session() as session:
                attachment_ids = session.scalars(
                    select(Attachment.id).where(
                        Attachment.notice_id == notice.id,
                        Attachment.download_status.in_(["pending", "failed"]),
                    )
                ).all()
            for attachment_id in attachment_ids:
                try:
                    await self._download_attachment_http(notice.id, attachment_id)
                except Exception:
                    logger.exception("Không tải được attachment id=%s", attachment_id)
        return notice

    def upsert_parsed_notice(
        self,
        parsed: ParsedNotice,
        raw_html_path: Path | None = None,
        source_kind: str = "web",
        strict_validation: bool = False,
    ) -> tuple[Notice, bool, bool]:
        """Return (notice, created, changed)."""
        validation = validate_notice(parsed, strict=strict_validation)
        if not validation.valid:
            raise ValueError("; ".join(validation.errors))

        hash_value = url_hash(parsed.source_url)
        content_hash = parsed_content_hash(parsed)
        now = datetime.now(UTC)
        with self.db.session() as session:
            notice = session.scalar(select(Notice).where(Notice.url_hash == hash_value))
            if notice is None and parsed.notice_code:
                notice = session.scalar(
                    select(Notice)
                    .where(Notice.notice_code == parsed.notice_code)
                    .order_by(Notice.id.asc())
                )
            created = notice is None
            changed = False
            if notice is None:
                notice = Notice(
                    source_url=parsed.source_url,
                    url_hash=hash_value,
                    first_seen_at=now,
                )
                session.add(notice)
                session.flush()
                changed = True
            else:
                changed = notice.content_hash != content_hash

            notice.source_url = parsed.source_url
            notice.url_hash = hash_value
            notice.content_hash = content_hash
            notice.source_kind = source_kind
            notice.notice_code = parsed.notice_code
            notice.title = parsed.title
            notice.buyer = parsed.buyer
            notice.investor = parsed.investor
            notice.package_price = parsed.package_price
            notice.currency = parsed.currency
            notice.published_at = parsed.published_at
            notice.closing_at = parsed.closing_at
            notice.raw_text = parsed.raw_text
            if raw_html_path:
                notice.raw_html_path = str(raw_html_path)
            notice.data_quality_status = "valid" if not validation.warnings else "warning"
            notice.last_seen_at = now

            existing = {item.source_url: item for item in notice.attachments}
            for item in parsed.attachments:
                current = existing.get(item.source_url)
                if current is None:
                    notice.attachments.append(
                        Attachment(
                            source_url=item.source_url,
                            file_name=item.file_name,
                            download_status="pending",
                        )
                    )
                elif item.file_name and not current.file_name:
                    current.file_name = item.file_name
            session.flush()
            session.refresh(notice)
            return notice, created, changed

    async def _download_attachment_http(self, notice_id: int, attachment_id: int) -> None:
        with self.db.session() as session:
            attachment = session.get(Attachment, attachment_id)
            if not attachment or attachment.notice_id != notice_id:
                return
            source_url = attachment.source_url
            attachment.download_attempts += 1
            attachment.last_attempt_at = datetime.now(UTC)
            attachment.download_status = "downloading"
            attachment.download_error = None

        try:
            self.http.policy.validate_domain(source_url)
            if not await self.http.policy.allowed_by_robots(self.http.client, source_url):
                raise AccessDenied(f"robots.txt không cho phép tải tệp: {source_url}")
            await self.http.limiter.wait(source_url)
            max_bytes = self.config.storage.max_attachment_mb * 1024 * 1024

            async with self.http.client.stream("GET", source_url) as response:
                if response.status_code in {401, 403, 429}:
                    raise AccessDenied(
                        f"Máy chủ từ chối/giới hạn tải tệp HTTP {response.status_code}: "
                        f"{source_url}"
                    )
                response.raise_for_status()
                declared = int(response.headers.get("content-length", "0") or 0)
                if declared > max_bytes:
                    raise ValueError(f"Tệp vượt giới hạn {self.config.storage.max_attachment_mb} MB")
                content_type = response.headers.get("content-type", "")
                url_name = urlparse(str(response.url)).path.rsplit("/", 1)[-1]
                with self.db.session() as session:
                    attachment = session.get(Attachment, attachment_id)
                    candidate = (attachment.file_name if attachment else None) or url_name or "attachment"
                filename = normalize_extension(
                    safe_filename(candidate),
                    content_type=content_type,
                    allowed_extensions=self.config.storage.allowed_attachment_extensions,
                )
                notice_dir = self.config.storage.download_dir / str(notice_id)
                notice_dir.mkdir(parents=True, exist_ok=True)
                destination = unique_destination(notice_dir, filename)
                temporary = destination.with_name(f"{destination.name}.part")
                digest = hashlib.sha256()
                size = 0
                try:
                    with temporary.open("wb") as output:
                        async for chunk in response.aiter_bytes():
                            size += len(chunk)
                            if size > max_bytes:
                                raise ValueError("Tệp vượt giới hạn trong khi tải")
                            digest.update(chunk)
                            output.write(chunk)
                    temporary.replace(destination)
                except Exception:
                    temporary.unlink(missing_ok=True)
                    raise

            with self.db.session() as session:
                attachment = session.get(Attachment, attachment_id)
                if attachment:
                    attachment.file_name = filename
                    attachment.local_path = str(destination)
                    attachment.sha256 = digest.hexdigest()
                    attachment.content_type = content_type
                    attachment.size_bytes = size
                    attachment.download_method = "http"
                    attachment.download_status = "downloaded"
                    attachment.download_error = None
                    attachment.downloaded_at = datetime.now(UTC)
        except Exception as exc:
            with self.db.session() as session:
                attachment = session.get(Attachment, attachment_id)
                if attachment:
                    attachment.download_status = (
                        "manual_review" if isinstance(exc, AccessDenied) else "failed"
                    )
                    attachment.download_error = str(exc)[:2000]
            raise

    async def retry_failed_attachments(self, limit: int = 100) -> tuple[int, int]:
        with self.db.session() as session:
            items = session.execute(
                select(Attachment.notice_id, Attachment.id)
                .where(Attachment.download_status.in_(["pending", "failed"]))
                .order_by(Attachment.id.asc())
                .limit(limit)
            ).all()
        ok = failed = 0
        for notice_id, attachment_id in items:
            try:
                await self._download_attachment_http(notice_id, attachment_id)
                ok += 1
            except Exception:
                failed += 1
                logger.exception("Retry attachment thất bại: id=%s", attachment_id)
        return ok, failed

    async def download_dynamic_attachments(
        self,
        url: str,
        package_id: str | None = None,
        headed: bool = False,
    ) -> tuple[Notice, list[DownloadedFile], list[str]]:
        """Download button-triggered files and persist their metadata."""
        # This workflow is browser-native from the beginning so --headed is honored.
        await self.browser.ensure_browser_access_allowed(url)
        await self._ensure_browser(headed=headed)
        html = await self.browser.fetch_html(url)
        raw_path = self._save_raw_html(url, html)
        parsed = parse_notice_html(
            html,
            url,
            self.config.storage.allowed_attachment_extensions,
        )
        notice, _, _ = self.upsert_parsed_notice(
            parsed, raw_html_path=raw_path, source_kind="web"
        )
        package_key = package_id or notice.notice_code or str(notice.id)
        downloaded, errors = await self.browser.download_page_attachments(
            url=url,
            package_id=package_key,
            headed=headed,
        )
        for item in downloaded:
            source_key = item.source_url or f"playwright://{url_hash(url)}/{item.sha256}"
            if not source_key.startswith(("http://", "https://")):
                source_key = f"playwright://{url_hash(url)}/{item.sha256}"
            with self.db.session() as session:
                attachment = session.scalar(
                    select(Attachment).where(
                        Attachment.notice_id == notice.id,
                        or_(Attachment.source_url == source_key, Attachment.sha256 == item.sha256),
                    )
                )
                if attachment is None:
                    attachment = Attachment(notice_id=notice.id, source_url=source_key)
                    session.add(attachment)
                attachment.file_name = item.file_name
                attachment.local_path = str(item.local_path)
                attachment.sha256 = item.sha256
                attachment.content_type = item.content_type
                attachment.size_bytes = item.size_bytes
                attachment.download_method = "playwright"
                attachment.download_status = "downloaded"
                attachment.download_error = None
                attachment.download_attempts = max(1, attachment.download_attempts)
                attachment.last_attempt_at = datetime.now(UTC)
                attachment.downloaded_at = datetime.now(UTC)
        return notice, downloaded, errors

    async def crawl_urls(self, urls: list[str], source_name: str = "web") -> tuple[int, int]:
        limited_urls = urls[: self.config.crawl.max_pages_per_run]
        with self.db.session() as session:
            run = CrawlRun(status="running", source_name=source_name, records_found=len(limited_urls))
            session.add(run)
            session.flush()
            run_id = run.id

        ok = failed = inserted = updated = 0
        semaphore = asyncio.Semaphore(self.config.crawl.concurrency)

        async def one(url: str) -> None:
            nonlocal ok, failed, inserted, updated
            async with semaphore:
                try:
                    html = await self._get_html(url)
                    raw_path = self._save_raw_html(url, html)
                    parsed = parse_notice_html(
                        html,
                        url,
                        self.config.storage.allowed_attachment_extensions,
                    )
                    notice, created, changed = self.upsert_parsed_notice(
                        parsed, raw_html_path=raw_path, source_kind="web"
                    )
                    if self.config.storage.download_attachments:
                        with self.db.session() as session:
                            ids = session.scalars(
                                select(Attachment.id).where(
                                    Attachment.notice_id == notice.id,
                                    Attachment.download_status.in_(["pending", "failed"]),
                                )
                            ).all()
                        for attachment_id in ids:
                            try:
                                await self._download_attachment_http(notice.id, attachment_id)
                            except Exception:
                                logger.exception("Không tải được attachment id=%s", attachment_id)
                    ok += 1
                    inserted += int(created)
                    updated += int((not created) and changed)
                    logger.info("Đã lưu notice id=%s url=%s", notice.id, url)
                except Exception:
                    failed += 1
                    logger.exception("Crawl thất bại: %s", url)

        await asyncio.gather(*(one(url) for url in limited_urls))
        with self.db.session() as session:
            run = session.get(CrawlRun, run_id)
            if run:
                run.finished_at = datetime.now(UTC)
                run.status = "completed" if failed == 0 else "partial"
                run.pages_ok = ok
                run.pages_failed = failed
                run.records_inserted = inserted
                run.records_updated = updated
                run.records_failed = failed
        return ok, failed

    async def collect_links(self, list_url: str) -> list[str]:
        html = await self._get_html(list_url)
        return extract_detail_links(
            html,
            list_url,
            self.config.selectors.list_item,
            self.config.selectors.detail_link,
            self.config.allowed_domains,
        )

    async def collect_dynamic_links(
        self,
        list_url: str,
        keyword: str | None,
        max_pages: int,
        headed: bool,
    ) -> list[str]:
        await self._ensure_browser(headed=headed)
        return await self.browser.collect_paginated_links(
            url=list_url,
            keyword=keyword,
            max_pages=max_pages,
            headed=headed,
        )

    def list_notices(self) -> list[Notice]:
        with self.db.session() as session:
            return list(
                session.scalars(
                    select(Notice)
                    .options(selectinload(Notice.attachments))
                    .order_by(Notice.id.desc())
                ).all()
            )
