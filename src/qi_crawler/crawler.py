from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from .browser import BrowserFetcher, RenderedListPage
from .compliance import AccessDenied, SessionExpired
from .config import AppConfig
from .db import Database
from .downloads import (
    DownloadedFile,
    normalize_extension,
    safe_filename,
    unique_destination,
)
from .http_client import HttpFetcher
from .keywords import matches_any_keyword
from .models import Attachment, CrawlRun, CrawlTask, Notice, TenderItem
from .parser import ParsedNotice, extract_detail_links, parse_notice_html
from .source_adapters import DiscoveredTender, SourceAdapter, SourceRegistry
from .validation import validate_notice

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScanSummary:
    run_id: int | None
    discovered: int
    matched: int
    queued: int
    limited: int
    new: int
    existing: int
    success: int
    failed: int
    pending: int
    skipped: int
    pages_scanned: int


def url_hash(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def parsed_content_hash(parsed: ParsedNotice) -> str:
    payload = _canonical_parsed_notice_payload(parsed)
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _canonical_parsed_notice_payload(parsed: ParsedNotice) -> dict[str, object]:
    """Return the deterministic source state used for semantic change detection."""

    def iso(value: datetime | None) -> str | None:
        return value.isoformat() if value is not None else None

    attachment_payloads = [
        {"source_url": item.source_url, "file_name": item.file_name}
        for item in parsed.attachments
    ]
    attachment_payloads.sort(
        key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True)
    )
    item_payloads = [
        {
            "item_code": item.item_code,
            "product_name": item.product_name,
            "specification": item.specification,
            "quantity": item.quantity,
            "minimum_quantity": item.minimum_quantity,
            "maximum_quantity": item.maximum_quantity,
            "unit": item.unit,
            "source_document": item.source_document,
            "source_location": item.source_location,
            "extraction_confidence": item.extraction_confidence,
            "needs_human_review": item.needs_human_review,
        }
        for item in parsed.items
    ]
    item_payloads.sort(key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True))
    return {
        "source_url": parsed.source_url,
        "notice_code": parsed.notice_code,
        "source_notice_id": parsed.source_notice_id,
        "source_name": parsed.source_name,
        "plan_code": parsed.plan_code,
        "title": parsed.title,
        "buyer": parsed.buyer,
        "procuring_entity_address": parsed.procuring_entity_address,
        "buyer_tax_code": parsed.buyer_tax_code,
        "investor": parsed.investor,
        "investor_tax_code": parsed.investor_tax_code,
        "project_name": parsed.project_name,
        "package_description": parsed.package_description,
        "package_price": parsed.package_price,
        "estimated_price": parsed.estimated_price,
        "currency": parsed.currency,
        "published_at": parsed.published_at,
        "closing_at": parsed.closing_at,
        "location": parsed.location,
        "sector": parsed.sector,
        "selection_method": parsed.selection_method,
        "selection_form": parsed.selection_form,
        "notice_version": (parsed.notice_version or "").strip() or None,
        "notice_type": parsed.notice_type or "tbmt",
        "funding_source": parsed.funding_source,
        "contract_type": parsed.contract_type,
        "bid_type": parsed.bid_type,
        "document_issue_at": iso(parsed.document_issue_at),
        "document_price": parsed.document_price,
        "bid_security_amount": parsed.bid_security_amount,
        "bid_security_method": parsed.bid_security_method,
        "issue_location": parsed.issue_location,
        "published_at_dt": iso(parsed.published_at_dt),
        "closing_at_dt": iso(parsed.closing_at_dt),
        "bid_open_at": iso(parsed.bid_open_at),
        "contract_duration": parsed.contract_duration,
        "raw_text": parsed.raw_text,
        "attachments": attachment_payloads,
        "items": item_payloads,
    }


def _source_name_from_kind(source_kind: str, source_url: str) -> str:
    if source_kind.startswith("web:"):
        return source_kind.removeprefix("web:")
    if source_kind not in {"web", "import"}:
        return source_kind
    hostname = (urlparse(source_url).hostname or "unknown-source").lower()
    if hostname.endswith("coteccons.vn"):
        return "coteccons"
    if hostname.endswith("muasamcong.mpi.gov.vn"):
        return "egp"
    return hostname.removeprefix("www.")


def _source_notice_id_from_url(source_url: str) -> str | None:
    parsed = urlparse(source_url)
    query = parse_qs(parsed.query)
    for key in ("notifyNo", "noticeId", "notice_id", "id"):
        values = query.get(key)
        if values and values[0].strip():
            return values[0].strip()
    parts = [part for part in parsed.path.split("/") if part]
    for part in reversed(parts):
        if part.isdigit():
            return part
    return None


def _enrich_source_identity(parsed: ParsedNotice, source_kind: str) -> None:
    parsed.source_name = (parsed.source_name or _source_name_from_kind(source_kind, parsed.source_url)).strip()
    parsed.source_notice_id = (
        parsed.source_notice_id or parsed.notice_code or _source_notice_id_from_url(parsed.source_url)
    )


class CrawlerService:
    def __init__(self, config: AppConfig):
        self.config = config
        self.db = Database(config.storage.database_url)
        self.db.require_current_schema()
        self.http = HttpFetcher(config)
        self.browser = BrowserFetcher(config)
        self.source_registry = SourceRegistry(config)
        self._session_source_name: str | None = None
        self._session_required = False
        self.human_required_reason: str | None = None
        self._browser_started = False

    async def close(self) -> None:
        await self.http.close()
        if self._browser_started:
            await self.browser.close()

    async def _ensure_browser(self, headed: bool = False) -> None:
        if not self._browser_started:
            await self.browser.start(headed=headed)
            self._browser_started = True

    def _session_state_for_url(self, url: str) -> tuple[Path | None, str | None, bool]:
        """Find a locally saved, browser-only session for a configured adapter."""
        adapter = self.source_registry.adapter_for_url(url)
        source_name = self._session_source_name or (adapter.source_name if adapter else None)
        if source_name is None:
            return None, None, False
        safe_name = re.sub(r"[^a-zA-Z0-9_-]+", "-", source_name).strip("-")
        state = Path("data/sessions") / f"{safe_name}_storage_state.json"
        required = self._session_required or bool(adapter and adapter.source.requires_auth)
        return (state if state.exists() else None), source_name, required

    def use_authenticated_session(self, source_name: str) -> None:
        """Prefer a named session for this crawl; the profile must be user-created."""
        self._session_source_name = source_name
        self._session_required = True

    async def _get_html(self, url: str) -> str:
        state, source_name, session_required = self._session_state_for_url(url)
        if session_required and state is None:
            source_label = (source_name or "website").upper()
            raise SessionExpired(
                f"{source_label}_SESSION_EXPIRED: Chua co phien dang nhap hop le. "
                f"Vui long chay QI-Crawler dang-nhap --source {source_name or 'TEN_NGUON'}."
            )
        if state is not None:
            self._browser_started = True
            try:
                return await self.browser.fetch_authenticated_html(url, state)
            except SessionExpired as exc:
                source_label = (source_name or "website").upper()
                raise SessionExpired(
                    f"{source_label}_SESSION_EXPIRED: {exc}"
                ) from exc
        try:
            result = await self.http.fetch(url)
            if self.config.crawl.use_browser_fallback and len(result.text) < 5000:
                raise ValueError("HTML shell qua ngan; chuyen sang browser")
            return result.text
        except AccessDenied:
            raise
        except Exception as exc:
            if not self.config.crawl.use_browser_fallback:
                raise
            logger.info("HTTP fetch chua du/khong thanh cong (%s), dung Playwright: %s", exc, url)
            # HttpFetcher already checked robots.txt before this fallback.
            await self._ensure_browser(headed=False)
            return await self.browser.fetch_html(url)

    def _save_raw_html(self, url: str, html: str) -> Path:
        directory = self.config.storage.raw_dir / "html"
        content = html.encode("utf-8")
        directory.mkdir(parents=True, exist_ok=True)
        content_hash = hashlib.sha256(content).hexdigest()
        path = directory / f"{content_hash}.html"
        try:
            with path.open("xb") as handle:
                handle.write(content)
        except FileExistsError:
            if path.read_bytes() != content:
                raise ValueError("raw HTML content-addressed collision") from None
        return path

    def _parse_detail(self, html: str, url: str) -> ParsedNotice:
        """Parse through a configured source adapter, with a generic fallback.

        The HTTP policy still rejects an unapproved domain before this method is
        reached. The fallback keeps manually configured authenticated sources
        usable until their dedicated adapter is added.
        """
        adapter = self.source_registry.adapter_for_url(url)
        if adapter is not None:
            parsed = adapter.parse_detail(html, url)
            parsed.attachments = [
                item
                for item in parsed.attachments
                if Path(urlparse(item.source_url).path).suffix.lower()
                in self.config.storage.allowed_attachment_extensions
            ]
            return parsed
        return parse_notice_html(
            html,
            url,
            self.config.storage.allowed_attachment_extensions,
        )

    async def crawl_notice(self, url: str, download_attachments: bool | None = None) -> Notice:
        html = await self._get_html(url)
        raw_path = self._save_raw_html(url, html)
        parsed = self._parse_detail(html, url)
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
                except AccessDenied:
                    # A successful detail page does not make a blocked file
                    # download safe. Surface HUMAN_REQUIRED to the operator.
                    raise
                except Exception:
                    logger.exception("Khong tai duoc attachment id=%s", attachment_id)
        return notice

    def upsert_parsed_notice(
        self,
        parsed: ParsedNotice,
        raw_html_path: Path | None = None,
        source_kind: str = "web",
        strict_validation: bool = False,
        crawl_run_id: int | None = None,
    ) -> tuple[Notice, bool, bool]:
        """Return (notice, created, changed)."""
        _enrich_source_identity(parsed, source_kind)
        validation = validate_notice(parsed, strict=strict_validation)
        if not validation.valid:
            raise ValueError("; ".join(validation.errors))

        version = (parsed.notice_version or "").strip() or None
        identity_url = (
            f"{parsed.source_url}#qi-version={version}" if version else parsed.source_url
        )
        hash_value = url_hash(identity_url)
        content_hash = parsed_content_hash(parsed)
        now = datetime.now(UTC)
        with self.db.session() as session:
            notice = None
            # e-GP publishes explicit revisions. Its real notice code plus version must
            # remain the primary key so one revision does not overwrite another.
            if parsed.notice_code:
                statement = select(Notice).where(
                    Notice.source_name == parsed.source_name,
                    Notice.notice_code == parsed.notice_code,
                )
                if version:
                    statement = statement.where(Notice.notice_version == version)
                else:
                    statement = statement.where(
                        or_(Notice.notice_version.is_(None), Notice.notice_version == "")
                    )
                notice = session.scalar(statement.order_by(Notice.id.asc()))
            # Sources without an e-GP code (for example Coteccons) are stable by
            # their own source identifier within the source name.
            if (
                notice is None
                and not parsed.notice_code
                and parsed.source_notice_id
                and parsed.source_name
            ):
                notice = session.scalar(
                    select(Notice)
                    .where(
                        Notice.source_name == parsed.source_name,
                        Notice.source_notice_id == parsed.source_notice_id,
                    )
                    .order_by(Notice.id.asc())
                )
            if notice is None:
                notice = session.scalar(select(Notice).where(Notice.url_hash == hash_value))
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
            notice.source_notice_id = parsed.source_notice_id
            notice.source_name = parsed.source_name
            notice.plan_code = parsed.plan_code
            notice.title = parsed.title
            notice.buyer = parsed.buyer
            notice.procuring_entity_address = parsed.procuring_entity_address
            notice.buyer_tax_code = parsed.buyer_tax_code
            notice.investor = parsed.investor
            notice.investor_tax_code = parsed.investor_tax_code
            notice.project_name = parsed.project_name
            notice.package_description = parsed.package_description
            notice.package_price = parsed.package_price
            notice.estimated_price = parsed.estimated_price
            notice.currency = parsed.currency
            notice.published_at = parsed.published_at
            notice.closing_at = parsed.closing_at
            notice.location = parsed.location
            notice.sector = parsed.sector
            notice.selection_method = parsed.selection_method
            notice.selection_form = parsed.selection_form
            notice.notice_version = version
            notice.notice_type = parsed.notice_type or "tbmt"
            notice.funding_source = parsed.funding_source
            notice.contract_type = parsed.contract_type
            notice.bid_type = parsed.bid_type
            notice.document_issue_at = parsed.document_issue_at
            notice.document_price = parsed.document_price
            notice.bid_security_amount = parsed.bid_security_amount
            notice.bid_security_method = parsed.bid_security_method
            notice.issue_location = parsed.issue_location
            notice.published_at_dt = parsed.published_at_dt
            notice.closing_at_dt = parsed.closing_at_dt
            notice.bid_open_at = parsed.bid_open_at
            notice.contract_duration = parsed.contract_duration
            if crawl_run_id is not None:
                notice.crawl_run_id = crawl_run_id
            notice.crawl_status = "ok"
            notice.raw_text = parsed.raw_text
            if raw_html_path:
                notice.raw_html_path = str(raw_html_path)
            critical_missing = (
                not parsed.notice_code and not parsed.source_notice_id,
                not parsed.title,
                parsed.package_price is None,
                not parsed.closing_at,
                not parsed.source_url,
            )
            if any(critical_missing):
                notice.data_quality_status = "INSUFFICIENT_DATA"
            else:
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
            existing_items = {item.item_code: item for item in notice.tender_items}
            for item in parsed.items:
                current_item = existing_items.get(item.item_code)
                if current_item is None:
                    notice.tender_items.append(
                        TenderItem(
                            item_code=item.item_code,
                            product_name=item.product_name,
                            specification=item.specification,
                            quantity=item.quantity,
                            minimum_quantity=item.minimum_quantity,
                            maximum_quantity=item.maximum_quantity,
                            unit=item.unit,
                            source_document=item.source_document,
                            source_location=item.source_location,
                            extraction_confidence=item.extraction_confidence,
                            needs_human_review=item.needs_human_review,
                        )
                    )
                else:
                    current_item.product_name = item.product_name
                    current_item.specification = item.specification
                    current_item.quantity = item.quantity
                    current_item.minimum_quantity = item.minimum_quantity
                    current_item.maximum_quantity = item.maximum_quantity
                    current_item.unit = item.unit
                    current_item.source_document = item.source_document
                    current_item.source_location = item.source_location
                    current_item.extraction_confidence = item.extraction_confidence
                    current_item.needs_human_review = item.needs_human_review
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
            await self.http.policy.require_robots_access(self.http.client, source_url)
            await self.http.limiter.wait(source_url)
            max_bytes = self.config.storage.max_attachment_mb * 1024 * 1024

            async with self.http.client.stream("GET", source_url) as response:
                if response.status_code in {401, 403, 429}:
                    raise AccessDenied(
                        f"May chu tu choi/gioi han tai tep HTTP {response.status_code}: "
                        f"{source_url}"
                    )
                response.raise_for_status()
                declared = int(response.headers.get("content-length", "0") or 0)
                if declared > max_bytes:
                    raise ValueError(f"Tep vuot gioi han {self.config.storage.max_attachment_mb} MB")
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
                                raise ValueError("Tep vuot gioi han trong khi tai")
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
                logger.exception("Retry attachment that bai: id=%s", attachment_id)
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
        parsed = self._parse_detail(html, url)
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

    def _prepare_crawl_tasks(
        self,
        urls: list[str],
        source_name: str,
        resume_run_id: int | None,
        run_notes: str | None = None,
    ) -> tuple[int, list[int]]:
        with self.db.session() as session:
            if resume_run_id is not None:
                run = session.get(CrawlRun, resume_run_id)
                if run is None:
                    raise ValueError(f"Khong tim thay crawl run {resume_run_id}")
                run.status = "running"
                run.finished_at = None
                for task in session.scalars(
                    select(CrawlTask).where(
                        CrawlTask.crawl_run_id == run.id,
                        CrawlTask.status.in_(["RUNNING", "HUMAN_REQUIRED"]),
                    )
                ):
                    task.status = "PENDING"
                    task.last_error = "Run truoc bi gian doan; se chay lai khi resume."
                task_ids = list(
                    session.scalars(
                        select(CrawlTask.id)
                        .where(
                            CrawlTask.crawl_run_id == run.id,
                            CrawlTask.status.in_(["PENDING", "FAILED_RETRYABLE"]),
                        )
                        .order_by(CrawlTask.page_index)
                    ).all()
                )
                return run.id, task_ids

            # max_pages_per_run bounds list pagination, not the number of
            # discovered detail tasks. Every selected unique tender is queued.
            unique_urls = list(dict.fromkeys(urls))
            run = CrawlRun(
                status="running",
                source_name=source_name,
                records_found=len(unique_urls),
                notes=run_notes,
            )
            session.add(run)
            session.flush()
            session.add_all(
                CrawlTask(crawl_run_id=run.id, url=url, page_index=index)
                for index, url in enumerate(unique_urls, start=1)
            )
            session.flush()
            task_ids = list(
                session.scalars(
                    select(CrawlTask.id)
                    .where(CrawlTask.crawl_run_id == run.id)
                    .order_by(CrawlTask.page_index)
                ).all()
            )
            return run.id, task_ids

    @staticmethod
    def _is_retryable_crawl_error(exc: Exception) -> bool:
        return isinstance(
            exc,
            (
                TimeoutError,
                ConnectionError,
                OSError,
                httpx.TransportError,
                httpx.TimeoutException,
                PlaywrightTimeoutError,
            ),
        )

    def _finalize_crawl_run(self, run_id: int, interrupted: bool = False) -> tuple[int, int]:
        with self.db.session() as session:
            run = session.get(CrawlRun, run_id)
            if run is None:
                return 0, 0
            tasks = list(
                session.scalars(select(CrawlTask).where(CrawlTask.crawl_run_id == run_id)).all()
            )
            completed = sum(task.status == "COMPLETED" for task in tasks)
            failed = sum(task.status == "FAILED" for task in tasks)
            run.pages_ok = completed
            run.pages_failed = failed
            run.finished_at = datetime.now(UTC)
            run.status = "interrupted" if interrupted else ("completed" if failed == 0 else "partial")
            return completed, failed

    def _crawl_run_task_counts(self, run_id: int) -> tuple[int, int, int]:
        """Return completed, failed and resumable/pending task counts."""
        with self.db.session() as session:
            statuses = session.scalars(
                select(CrawlTask.status).where(CrawlTask.crawl_run_id == run_id)
            ).all()
        success = sum(status == "COMPLETED" for status in statuses)
        failed = sum(status == "FAILED" for status in statuses)
        pending = len(statuses) - success - failed
        return success, failed, pending

    def _stop_run_for_human(self, run_id: int, reason: str) -> None:
        """Stop a batch safely while keeping incomplete tasks resumable."""
        with self.db.session() as session:
            run = session.get(CrawlRun, run_id)
            if run is not None:
                run.status = "human_required"
                run.error_message = reason[:2000]
                run.finished_at = datetime.now(UTC)
            for task in session.scalars(
                select(CrawlTask).where(
                    CrawlTask.crawl_run_id == run_id,
                    CrawlTask.status == "RUNNING",
                )
            ):
                task.status = "PENDING"
                task.last_error = "Batch da dung de nguoi dung xu ly yeu cau truy cap."

    async def _crawl_task(self, task_id: int, run_id: int) -> None:
        while True:
            with self.db.session() as session:
                task = session.get(CrawlTask, task_id)
                if task is None or task.status in {"COMPLETED", "FAILED"}:
                    return
                task.status = "RUNNING"
                task.attempt_count += 1
                task.started_at = task.started_at or datetime.now(UTC)
                task.last_error = None
                url = task.url
                attempt_count = task.attempt_count
            try:
                html = await self._get_html(url)
                raw_path = self._save_raw_html(url, html)
                parsed = self._parse_detail(html, url)
                notice, created, changed = self.upsert_parsed_notice(
                    parsed, raw_html_path=raw_path, source_kind="web", crawl_run_id=run_id
                )
                if self.config.storage.download_attachments:
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
                        except AccessDenied:
                            raise
                        except Exception:
                            logger.exception("Khong tai duoc attachment id=%s", attachment_id)
                with self.db.session() as session:
                    task = session.get(CrawlTask, task_id)
                    run = session.get(CrawlRun, run_id)
                    if task is not None:
                        task.status = "COMPLETED"
                        task.finished_at = datetime.now(UTC)
                        task.processed_at = task.finished_at
                    if run is not None:
                        run.records_inserted += int(created)
                        run.records_updated += int((not created) and changed)
                logger.info("Da luu notice id=%s url=%s", notice.id, url)
                return
            except asyncio.CancelledError:
                with self.db.session() as session:
                    task = session.get(CrawlTask, task_id)
                    if task is not None:
                        task.last_error = "Crawl bi huy/gian doan; cho resume."
                raise
            except AccessDenied as exc:
                self.human_required_reason = str(exc)
                with self.db.session() as session:
                    task = session.get(CrawlTask, task_id)
                    if task is not None:
                        task.status = "HUMAN_REQUIRED"
                        task.last_error = str(exc)[:2000]
                        task.finished_at = datetime.now(UTC)
                    run = session.get(CrawlRun, run_id)
                    if run is not None:
                        run.status = "human_required"
                        run.error_message = str(exc)[:2000]
                raise
            except Exception as exc:
                retryable = self._is_retryable_crawl_error(exc)
                can_retry = retryable and attempt_count <= self.config.crawl.max_retries
                with self.db.session() as session:
                    task = session.get(CrawlTask, task_id)
                    if task is not None:
                        task.last_error = str(exc)[:2000]
                        task.status = "FAILED_RETRYABLE" if can_retry else "FAILED"
                        if not can_retry:
                            task.finished_at = datetime.now(UTC)
                    if not can_retry:
                        run = session.get(CrawlRun, run_id)
                        if run is not None:
                            run.records_failed += 1
                if can_retry:
                    delay = min(
                        self.config.crawl.retry_backoff_seconds * (2 ** (attempt_count - 1)),
                        15.0,
                    )
                    if delay:
                        await asyncio.sleep(delay)
                    continue
                logger.exception("Crawl that bai: %s", url)
                return

    async def crawl_urls(
        self,
        urls: list[str],
        source_name: str = "web",
        resume_run_id: int | None = None,
        run_notes: str | None = None,
    ) -> tuple[int, int]:
        run_id, task_ids = self._prepare_crawl_tasks(
            urls, source_name, resume_run_id, run_notes
        )
        semaphore = asyncio.Semaphore(self.config.crawl.concurrency)
        stop_for_human = asyncio.Event()

        async def one(task_id: int) -> None:
            async with semaphore:
                if stop_for_human.is_set():
                    return
                try:
                    await self._crawl_task(task_id, run_id)
                except AccessDenied:
                    # Set before releasing the semaphore so the next queued
                    # worker cannot start another request.
                    stop_for_human.set()
                    raise

        workers = [asyncio.create_task(one(task_id)) for task_id in task_ids]
        try:
            await asyncio.gather(*workers)
        except AccessDenied as exc:
            for worker in workers:
                if not worker.done():
                    worker.cancel()
            await asyncio.gather(*workers, return_exceptions=True)
            self._stop_run_for_human(run_id, str(exc))
            raise
        except asyncio.CancelledError:
            for worker in workers:
                if not worker.done():
                    worker.cancel()
            await asyncio.gather(*workers, return_exceptions=True)
            self._finalize_crawl_run(run_id, interrupted=True)
            raise
        return self._finalize_crawl_run(run_id)

    async def resume_crawl(self, run_id: int) -> tuple[int, int]:
        return await self.crawl_urls([], resume_run_id=run_id)

    async def collect_links(self, list_url: str) -> list[str]:
        html = await self._get_html(list_url)
        adapter = self.source_registry.adapter_for_url(list_url)
        if adapter is not None:
            return adapter.discover(html, list_url)
        return extract_detail_links(
            html,
            list_url,
            self.config.selectors.list_item,
            self.config.selectors.detail_link,
            self.config.allowed_domains,
        )

    async def _render_coteccons_ajax_pages(
        self, url: str, max_pages: int
    ) -> list[RenderedListPage]:
        """Render Coteccons' permitted list and follow its real AJAX selector."""
        state, source_name, session_required = self._session_state_for_url(url)
        if session_required and state is None:
            raise SessionExpired(
                f"{(source_name or 'website').upper()}_SESSION_EXPIRED: "
                "Can dang nhap lai truoc khi render trang danh sach."
            )
        self._browser_started = True
        try:
            return await self.browser.collect_coteccons_ajax_pages(
                url=url,
                max_pages=max_pages,
                storage_state=state,
            )
        except AccessDenied:
            raise
        except (RuntimeError, OSError, httpx.TransportError, PlaywrightTimeoutError) as exc:
            logger.warning(
                "list_page=%s pagination_mechanism=AJAX_POST "
                "stop_reason=ajax_discovery_failed error=%s",
                url,
                exc,
            )
            return []

    async def _discover_list_pages(
        self, list_url: str, max_pages: int
    ) -> tuple[SourceAdapter, list[DiscoveredTender], int]:
        """Discover one configured source list safely, with bounded pagination."""
        adapter = self.source_registry.require_adapter(list_url)
        pending = [list_url]
        seen_pages: set[str] = set()
        entries: dict[str, DiscoveredTender] = {}
        seen_source_ids: set[str] = set()
        pages_scanned = 0

        while pending and pages_scanned < max_pages:
            page_url = pending.pop(0)
            if page_url in seen_pages:
                continue
            seen_pages.add(page_url)
            html = await self._get_html(page_url)
            page_entries = adapter.discover_tenders(html, page_url)
            ajax_metadata = adapter.ajax_pagination_metadata(html, page_url)
            if adapter.source.adapter == "coteccons" and (
                not page_entries or ajax_metadata is not None
            ):
                rendered_pages = await self._render_coteccons_ajax_pages(
                    page_url, max_pages - pages_scanned
                )
                for rendered_page in rendered_pages:
                    pages_scanned += 1
                    rendered_entries = adapter.discover_tenders(
                        rendered_page.html, page_url
                    )
                    new_ids: list[str] = []
                    for entry in rendered_entries:
                        if entry.source_notice_id in seen_source_ids:
                            continue
                        seen_source_ids.add(entry.source_notice_id)
                        entries[entry.url] = entry
                        new_ids.append(entry.source_notice_id)
                    logger.info(
                        "list_page=%s total_pages=%s current_selected_page=%s "
                        "discovered_ids=%s discovered_count=%s "
                        "pagination_mechanism=AJAX_POST",
                        page_url,
                        rendered_page.total_pages,
                        rendered_page.page_number,
                        new_ids,
                        len(new_ids),
                    )
                return adapter, list(entries.values()), pages_scanned

            pages_scanned += 1
            before = len(entries)
            for entry in page_entries:
                if entry.source_notice_id in seen_source_ids:
                    continue
                seen_source_ids.add(entry.source_notice_id)
                entries[entry.url] = entry
            # Do not keep traversing a source whose pagination no longer yields
            # new tender identities; it prevents both loops and stale pages.
            if len(entries) == before:
                break
            for next_page in adapter.pagination_links(html, page_url):
                if next_page not in seen_pages and next_page not in pending:
                    pending.append(next_page)
        return adapter, list(entries.values()), pages_scanned

    @staticmethod
    def _scan_notes(list_url: str) -> str:
        return f"scan-list:{list_url}"

    def _resumable_scan_run(self, adapter: SourceAdapter, list_url: str) -> CrawlRun | None:
        with self.db.session() as session:
            runs = session.scalars(
                select(CrawlRun)
                .where(
                    CrawlRun.source_name == adapter.source_name,
                    CrawlRun.status.in_(["running", "interrupted", "partial", "human_required"]),
                )
                .order_by(CrawlRun.id.desc())
            ).all()
            return next(
                (run for run in runs if run.notes == self._scan_notes(list_url)),
                None,
            )

    def _existing_source_ids(self, source_name: str, entries: list[DiscoveredTender]) -> set[str]:
        source_ids = {entry.source_notice_id for entry in entries}
        if not source_ids:
            return set()
        with self.db.session() as session:
            return set(
                session.scalars(
                    select(Notice.source_notice_id).where(
                        Notice.source_name == source_name,
                        Notice.source_notice_id.in_(source_ids),
                    )
                ).all()
            )

    @staticmethod
    def _filter_discovered_tenders(
        entries: list[DiscoveredTender], keyword_terms: tuple[str, ...]
    ) -> tuple[list[DiscoveredTender], int]:
        if not keyword_terms:
            return entries, 0
        selected: list[DiscoveredTender] = []
        skipped = 0
        for entry in entries:
            # Empty list metadata is insufficient evidence, so retain the URL
            # for detail parsing rather than silently losing a tender.
            if not entry.metadata_text or matches_any_keyword(entry.metadata_text, keyword_terms):
                selected.append(entry)
            else:
                skipped += 1
        return selected, skipped

    async def scan_list(
        self,
        list_url: str,
        *,
        keyword_terms: tuple[str, ...] = (),
        max_pages: int = 25,
        resume: bool = False,
    ) -> ScanSummary:
        """Discover Coteccons-style list pages, then batch crawl detail tasks."""
        adapter = self.source_registry.require_adapter(list_url)
        if resume:
            existing_run = self._resumable_scan_run(adapter, list_url)
            if existing_run is not None:
                success, failed = await self.resume_crawl(existing_run.id)
                queued = existing_run.records_found
                _, _, pending = self._crawl_run_task_counts(existing_run.id)
                return ScanSummary(
                    run_id=existing_run.id,
                    discovered=queued,
                    matched=queued,
                    queued=queued,
                    limited=0,
                    new=0,
                    existing=queued,
                    success=success,
                    failed=failed,
                    pending=pending,
                    skipped=0,
                    pages_scanned=0,
                )

        adapter, discovered, pages_scanned = await self._discover_list_pages(list_url, max_pages)
        selected, skipped = self._filter_discovered_tenders(discovered, keyword_terms)
        existing_source_ids = self._existing_source_ids(adapter.source_name, selected)
        queued = len(selected)
        success, failed = await self.crawl_urls(
            [entry.url for entry in selected],
            source_name=adapter.source_name,
            run_notes=self._scan_notes(list_url),
        )
        run_id = None if not selected else self._latest_run_id(adapter.source_name, list_url)
        pending = 0 if run_id is None else self._crawl_run_task_counts(run_id)[2]
        return ScanSummary(
            run_id=run_id,
            discovered=len(discovered),
            matched=len(selected),
            queued=queued,
            limited=0,
            new=len(selected) - len(existing_source_ids),
            existing=len(existing_source_ids),
            success=success,
            failed=failed,
            pending=pending,
            skipped=skipped,
            pages_scanned=pages_scanned,
        )

    def _latest_run_id(self, source_name: str, list_url: str) -> int | None:
        with self.db.session() as session:
            return session.scalar(
                select(CrawlRun.id)
                .where(CrawlRun.source_name == source_name, CrawlRun.notes == self._scan_notes(list_url))
                .order_by(CrawlRun.id.desc())
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
