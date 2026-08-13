"""Fail-closed tender attachment discovery and acquisition.

Network acquisition is deliberately a staging concern. Immutable storage,
identity, hashing, duplicate/version handling and taxonomy remain owned by
``DocumentIntakeService``.
"""

from __future__ import annotations

import logging
import mimetypes
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from .browser import BrowserFetcher
from .compliance import AccessDenied
from .config import AppConfig
from .document_intake import (
    SUPPORTED_EXTENSIONS,
    DocumentIdentityMismatch,
    DocumentIntakeResult,
    DocumentIntakeService,
    DocumentValidationError,
    TenderDocumentTarget,
    sanitize_filename,
)
from .downloads import DownloadedFile, unique_destination
from .http_client import HttpFetcher

logger = logging.getLogger(__name__)

_IDENTITY_ATTRIBUTES = (
    "data-tender-code",
    "data-notice-code",
    "data-source-notice-id",
    "data-tender-id",
)
_CONTENT_DISPOSITION_FILENAME = re.compile(
    r"filename\*?=(?:UTF-8''|\")?([^\";]+)", re.IGNORECASE
)
_MIME_EXTENSIONS = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/zip": ".zip",
}


@dataclass(frozen=True)
class WebAttachmentCandidate:
    source_url: str
    filename: str
    mime_type: str | None
    title: str | None
    detected_tender_reference: str


@dataclass(frozen=True)
class WebDocumentFailure:
    source_url: str
    reason: str


@dataclass(frozen=True)
class WebDocumentIntakeSummary:
    tender_identifier: str
    discovered: int
    downloaded: int
    duplicates: int
    needs_review: int
    failed: int
    human_required: bool
    results: tuple[DocumentIntakeResult, ...]
    failures: tuple[WebDocumentFailure, ...]


class TenderWebDocumentService:
    """Discover and acquire attachments for one already-identified tender."""

    def __init__(
        self,
        config: AppConfig,
        intake: DocumentIntakeService,
        *,
        http_fetcher: HttpFetcher | None = None,
        browser_fetcher: BrowserFetcher | None = None,
    ) -> None:
        self.config = config
        self.intake = intake
        self.http = http_fetcher or HttpFetcher(config)
        self.browser = browser_fetcher or BrowserFetcher(config)
        self._owns_http = http_fetcher is None
        self._owns_browser = browser_fetcher is None

    async def close(self) -> None:
        if self._owns_http:
            await self.http.close()
        if self._owns_browser:
            await self.browser.close()

    async def acquire(self, tender_reference: str) -> WebDocumentIntakeSummary:
        target = self.intake.resolve_tender_target(tender_reference)
        logger.info(
            "WEB_DOCUMENT_DISCOVER_START tender=%s source_url=%s",
            target.identifier,
            target.source_url,
        )
        try:
            page = await self.http.fetch(target.source_url)
        except (httpx.TransportError, httpx.TimeoutException) as exc:
            raise AccessDenied(
                f"Không thể xác minh kết nối/TLS khi tìm tài liệu; HUMAN_REQUIRED: {exc}"
            ) from exc

        candidates = self.discover_direct_attachments(page.text, page.url, target)
        results: list[DocumentIntakeResult] = []
        failures: list[WebDocumentFailure] = []
        downloaded = 0

        for candidate in candidates:
            staged: Path | None = None
            try:
                staged = await self._download_direct(candidate)
                downloaded += 1
                results.append(self._intake_staged(staged, candidate, target))
            except (AccessDenied, DocumentIdentityMismatch):
                raise
            except Exception as exc:
                logger.exception("WEB_DOCUMENT_DOWNLOAD_FAILED url=%s", candidate.source_url)
                failures.append(WebDocumentFailure(candidate.source_url, str(exc)))
            finally:
                self._cleanup_staging(staged)

        dynamic_files: list[DownloadedFile] = []
        dynamic_errors: list[str] = []
        if (
            self.config.selectors.attachment_rows
            and self.config.selectors.attachment_download_button
        ):
            dynamic_files, dynamic_errors = await self.browser.download_page_attachments(
                target.source_url,
                target.identifier,
                headed=False,
            )
        for item in dynamic_files:
            candidate = WebAttachmentCandidate(
                source_url=item.source_url or target.source_url,
                filename=item.file_name,
                mime_type=item.content_type,
                title=item.file_name,
                detected_tender_reference=target.identifier,
            )
            try:
                downloaded += 1
                results.append(self._intake_staged(item.local_path, candidate, target))
            except (AccessDenied, DocumentIdentityMismatch):
                raise
            except Exception as exc:
                logger.exception("WEB_DOCUMENT_DYNAMIC_INTAKE_FAILED url=%s", candidate.source_url)
                failures.append(WebDocumentFailure(candidate.source_url, str(exc)))
            finally:
                self._cleanup_staging(item.local_path)
        failures.extend(
            WebDocumentFailure(target.source_url, reason) for reason in dynamic_errors
        )

        duplicates = sum(item.outcome == "DUPLICATE" for item in results)
        needs_review = sum(
            item.identity_status in {"UNLINKED", "NEEDS_REVIEW"}
            or item.classification_status == "NEEDS_REVIEW"
            for item in results
        )
        summary = WebDocumentIntakeSummary(
            tender_identifier=target.identifier,
            discovered=len(candidates) + len(dynamic_files) + len(dynamic_errors),
            downloaded=downloaded,
            duplicates=duplicates,
            needs_review=needs_review,
            failed=len(failures),
            human_required=False,
            results=tuple(results),
            failures=tuple(failures),
        )
        logger.info(
            "WEB_DOCUMENT_INTAKE_DONE tender=%s discovered=%s downloaded=%s "
            "duplicates=%s needs_review=%s failed=%s",
            target.identifier,
            summary.discovered,
            summary.downloaded,
            summary.duplicates,
            summary.needs_review,
            summary.failed,
        )
        return summary

    def discover_direct_attachments(
        self,
        html: str,
        page_url: str,
        target: TenderDocumentTarget,
    ) -> list[WebAttachmentCandidate]:
        """Return unique allowlisted direct document links from one tender page."""
        soup = BeautifulSoup(html, "html.parser")
        unique: dict[str, WebAttachmentCandidate] = {}
        for anchor in soup.select("a[href]"):
            source_url = urljoin(page_url, str(anchor.get("href") or "").strip())
            parsed = urlparse(source_url)
            if parsed.scheme not in {"http", "https"}:
                continue
            try:
                self.http.policy.validate_domain(source_url)
            except AccessDenied:
                continue
            title = str(anchor.get("title") or anchor.get_text(" ", strip=True) or "").strip()
            filename = self._candidate_filename(anchor.get("download"), parsed.path, title)
            mime_type = str(anchor.get("type") or "").split(";", 1)[0].strip() or None
            if Path(filename).suffix.lower() not in SUPPORTED_EXTENSIONS and mime_type:
                extension = _MIME_EXTENSIONS.get(mime_type.lower())
                if extension:
                    filename = sanitize_filename(f"{filename}{extension}")
            if not self._is_supported_candidate(filename, mime_type):
                continue
            detected = next(
                (
                    str(anchor.get(attribute) or "").strip()
                    for attribute in _IDENTITY_ATTRIBUTES
                    if str(anchor.get(attribute) or "").strip()
                ),
                target.identifier,
            )
            unique.setdefault(
                source_url,
                WebAttachmentCandidate(
                    source_url=source_url,
                    filename=filename,
                    mime_type=mime_type or mimetypes.guess_type(filename)[0],
                    title=title or None,
                    detected_tender_reference=detected,
                ),
            )
        logger.info(
            "WEB_DOCUMENT_DISCOVERY_DONE tender=%s discovered=%s",
            target.identifier,
            len(unique),
        )
        return list(unique.values())

    @staticmethod
    def _candidate_filename(download: object, path: str, title: str) -> str:
        for value in (str(download or ""), unquote(path).rsplit("/", 1)[-1], title):
            value = value.strip()
            if Path(value).suffix.lower() in SUPPORTED_EXTENSIONS:
                return sanitize_filename(value)
        return sanitize_filename(unquote(path).rsplit("/", 1)[-1] or "document")

    @staticmethod
    def _is_supported_candidate(filename: str, mime_type: str | None) -> bool:
        if Path(filename).suffix.lower() in SUPPORTED_EXTENSIONS:
            return True
        return (mime_type or "").lower() in _MIME_EXTENSIONS

    async def _download_direct(self, candidate: WebAttachmentCandidate) -> Path:
        await self.http.policy.require_robots_access(self.http.client, candidate.source_url)
        await self.http.limiter.wait(candidate.source_url)
        max_bytes = self.config.storage.max_attachment_mb * 1024 * 1024
        stage_dir = self.config.storage.download_dir / ".document-intake-staging"
        try:
            async with self.http.client.stream("GET", candidate.source_url) as response:
                if response.status_code in {401, 403, 429}:
                    raise AccessDenied(
                        f"Website từ chối tải tài liệu HTTP {response.status_code}; HUMAN_REQUIRED"
                    )
                response.raise_for_status()
                content_type = response.headers.get("content-type", "").split(";", 1)[0]
                if content_type in {"text/html", "application/xhtml+xml"}:
                    self.http.policy.detect_block_page((await response.aread()).decode(errors="ignore"))
                    raise DocumentValidationError("Liên kết tải trả về trang HTML thay vì tài liệu.")
                filename = self._response_filename(response, candidate)
                if Path(filename).suffix.lower() not in SUPPORTED_EXTENSIONS:
                    raise DocumentValidationError("Tệp tải về không thuộc PDF, DOCX, XLSX hoặc ZIP.")
                declared = int(response.headers.get("content-length", "0") or 0)
                if declared > max_bytes:
                    raise DocumentValidationError("Tài liệu vượt giới hạn dung lượng cấu hình.")
                stage_dir.mkdir(parents=True, exist_ok=True)
                destination = unique_destination(stage_dir, filename)
                temporary = destination.with_name(f"{destination.name}.part")
                size = 0
                try:
                    with temporary.open("xb") as stream:
                        async for chunk in response.aiter_bytes():
                            size += len(chunk)
                            if size > max_bytes:
                                raise DocumentValidationError(
                                    "Tài liệu vượt giới hạn dung lượng trong khi tải."
                                )
                            stream.write(chunk)
                    if size == 0:
                        raise DocumentValidationError("Website trả về tệp rỗng.")
                    temporary.replace(destination)
                except Exception:
                    temporary.unlink(missing_ok=True)
                    destination.unlink(missing_ok=True)
                    raise
                logger.info(
                    "WEB_DOCUMENT_DOWNLOADED url=%s filename=%s downloaded_at=%s",
                    candidate.source_url,
                    filename,
                    datetime.now(UTC).isoformat(),
                )
                return destination
        except (httpx.TransportError, httpx.TimeoutException) as exc:
            raise AccessDenied(
                f"Không thể xác minh kết nối/TLS khi tải tài liệu; HUMAN_REQUIRED: {exc}"
            ) from exc

    @staticmethod
    def _response_filename(
        response: httpx.Response, candidate: WebAttachmentCandidate
    ) -> str:
        disposition = response.headers.get("content-disposition", "")
        match = _CONTENT_DISPOSITION_FILENAME.search(disposition)
        filename = unquote(match.group(1).strip()) if match else candidate.filename
        return sanitize_filename(filename)

    def _intake_staged(
        self,
        path: Path,
        candidate: WebAttachmentCandidate,
        target: TenderDocumentTarget,
    ) -> DocumentIntakeResult:
        self.intake.verify_tender_identity(
            target.identifier,
            detected_tender_reference=candidate.detected_tender_reference,
            source_url=candidate.source_url,
        )
        return self.intake.intake_file(
            path,
            tender_reference=target.identifier,
            document_name=candidate.title,
            document_source="web",
            source_url=candidate.source_url,
            detected_tender_reference=candidate.detected_tender_reference,
        )

    @staticmethod
    def _cleanup_staging(path: Path | None) -> None:
        if path is None:
            return
        path.unlink(missing_ok=True)
        try:
            path.parent.rmdir()
        except OSError:
            pass
