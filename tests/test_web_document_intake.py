from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path

import httpx
import pytest

from qi_crawler.browser import BrowserFetcher
from qi_crawler.compliance import AccessDenied
from qi_crawler.config import AppConfig
from qi_crawler.db import Database
from qi_crawler.document_intake import (
    DocumentIdentityMismatch,
    DocumentIntakeService,
    DocumentValidationError,
)
from qi_crawler.downloads import DownloadedFile
from qi_crawler.http_client import HttpFetcher
from qi_crawler.models import Notice
from qi_crawler.web_document_intake import TenderWebDocumentService


class _NoWait:
    async def wait(self, _url: str) -> None:
        return None


class _FakeBrowser:
    def __init__(self, files: list[DownloadedFile] | None = None, errors: list[str] | None = None):
        self.files = files or []
        self.errors = errors or []
        self.calls: list[tuple[str, str, bool]] = []

    async def download_page_attachments(
        self, url: str, package_id: str, headed: bool = False
    ) -> tuple[list[DownloadedFile], list[str]]:
        self.calls.append((url, package_id, headed))
        return self.files, self.errors


def _config(tmp_path: Path, *, dynamic: bool = False) -> AppConfig:
    config = AppConfig.model_validate(
        {
            "allowed_domains": ["example.test"],
            "compliance": {"obey_robots_txt": False},
            "crawl": {"requests_per_minute": 120},
            "storage": {
                "database_url": f"sqlite:///{tmp_path / 'web-documents.db'}",
                "document_dir": str(tmp_path / "documents"),
                "download_dir": str(tmp_path / "downloads"),
            },
            "selectors": (
                {
                    "attachment_rows": ".attachment",
                    "attachment_download_button": "button.download",
                }
                if dynamic
                else {}
            ),
        }
    )
    config.storage.document_dir.mkdir(parents=True, exist_ok=True)
    config.storage.download_dir.mkdir(parents=True, exist_ok=True)
    return config


def _add_tender(database: Database, code: str = "IB2600000001-00") -> None:
    url = "https://example.test/tender/1"
    with database.session() as session:
        session.add(
            Notice(
                source_url=url,
                url_hash=hashlib.sha256(url.encode()).hexdigest(),
                notice_code=code,
                source_notice_id="1",
                source_name="egp",
                title="Tender documents",
            )
        )


def _service(
    tmp_path: Path,
    handler,
    *,
    dynamic: bool = False,
    browser: _FakeBrowser | None = None,
) -> tuple[TenderWebDocumentService, httpx.AsyncClient, Database]:
    config = _config(tmp_path, dynamic=dynamic)
    database = Database(config.storage.database_url)
    intake = DocumentIntakeService(database, config.storage.document_dir)
    _add_tender(database)
    fetcher = HttpFetcher(config)
    old_client = fetcher.client
    asyncio.run(old_client.aclose())
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        follow_redirects=True,
    )
    fetcher.client = client
    fetcher.limiter = _NoWait()  # type: ignore[assignment]
    service = TenderWebDocumentService(
        config,
        intake,
        http_fetcher=fetcher,
        browser_fetcher=browser or _FakeBrowser(),  # type: ignore[arg-type]
    )
    return service, client, database


def test_direct_discovery_downloads_pdf_docx_xlsx_and_zip(tmp_path: Path) -> None:
    files = {
        "/files/hsmt.pdf": (b"%PDF-1.7 hsmt", "application/pdf"),
        "/files/spec.docx": (b"PK\x03\x04docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        "/files/boq.xlsx": (b"PK\x03\x04xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        "/files/package.zip": (b"PK\x05\x06" + b"\x00" * 18, "application/zip"),
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/tender/1":
            links = "".join(f'<a href="{path}">{Path(path).name}</a>' for path in files)
            return httpx.Response(200, text=f"<html>{links}</html>")
        content, mime = files[request.url.path]
        return httpx.Response(200, content=content, headers={"content-type": mime})

    service, client, _database = _service(tmp_path, handler)
    try:
        summary = asyncio.run(service.acquire("IB2600000001-00"))
    finally:
        asyncio.run(client.aclose())

    assert summary.discovered == 4
    assert summary.downloaded == 4
    assert summary.failed == 0
    assert {item.file_format for item in summary.results} == {"PDF", "DOCX", "XLSX", "ZIP"}
    assert all(item.identity_status == "VERIFIED_LINKED" for item in summary.results)
    assert not (tmp_path / "downloads" / ".document-intake-staging").exists()


def test_dynamic_playwright_download_uses_same_intake_service(tmp_path: Path) -> None:
    staged = tmp_path / "dynamic.pdf"
    staged.write_bytes(b"%PDF dynamic")
    browser = _FakeBrowser(
        [
            DownloadedFile(
                file_name="dynamic.pdf",
                local_path=staged,
                sha256="unused-by-intake",
                size_bytes=staged.stat().st_size,
                content_type="application/pdf",
                source_url="https://example.test/files/dynamic.pdf",
            )
        ]
    )

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html><button>dynamic</button></html>")

    service, client, _database = _service(
        tmp_path, handler, dynamic=True, browser=browser
    )
    try:
        summary = asyncio.run(service.acquire("IB2600000001-00"))
    finally:
        asyncio.run(client.aclose())

    assert summary.discovered == 1
    assert summary.downloaded == 1
    assert summary.results[0].identity_status == "VERIFIED_LINKED"
    assert browser.calls == [("https://example.test/tender/1", "IB2600000001-00", False)]
    assert not staged.exists()


def test_direct_signed_url_uses_declared_mime_type(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/tender/1":
            return httpx.Response(
                200,
                text='<a href="/download?id=5" type="application/pdf">HSMT</a>',
            )
        return httpx.Response(200, content=b"%PDF signed")

    service, client, _database = _service(tmp_path, handler)
    try:
        summary = asyncio.run(service.acquire("IB2600000001-00"))
    finally:
        asyncio.run(client.aclose())

    assert summary.discovered == 1
    assert summary.results[0].file_format == "PDF"


def test_rerun_is_duplicate_and_changed_file_is_new_version(tmp_path: Path) -> None:
    content = [b"%PDF version one"]

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/tender/1":
            return httpx.Response(200, text='<a href="/files/hsmt.pdf">HSMT.pdf</a>')
        return httpx.Response(200, content=content[0], headers={"content-type": "application/pdf"})

    service, client, _database = _service(tmp_path, handler)
    try:
        first = asyncio.run(service.acquire("IB2600000001-00"))
        duplicate = asyncio.run(service.acquire("IB2600000001-00"))
        content[0] = b"%PDF version two"
        changed = asyncio.run(service.acquire("IB2600000001-00"))
    finally:
        asyncio.run(client.aclose())

    assert first.results[0].version == 1
    assert duplicate.duplicates == 1
    assert duplicate.results[0].document_id == first.results[0].document_id
    assert changed.results[0].version == 2
    assert changed.results[0].document_id != first.results[0].document_id


def test_tender_mismatch_is_blocked(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/tender/1":
            return httpx.Response(
                200,
                text=(
                    '<a href="/files/wrong.pdf" '
                    'data-tender-code="IB2600000002-00">wrong.pdf</a>'
                ),
            )
        return httpx.Response(200, content=b"%PDF wrong", headers={"content-type": "application/pdf"})

    service, client, database = _service(tmp_path, handler)
    other_url = "https://example.test/tender/2"
    with database.session() as session:
        session.add(
            Notice(
                source_url=other_url,
                url_hash=hashlib.sha256(other_url.encode()).hexdigest(),
                notice_code="IB2600000002-00",
                source_notice_id="2",
                source_name="egp",
                title="Other tender",
            )
        )
    service.intake._hash_file = lambda _path: pytest.fail(  # type: ignore[method-assign]
        "identity mismatch must stop before hashing"
    )
    try:
        with pytest.raises(DocumentIdentityMismatch):
            asyncio.run(service.acquire("IB2600000001-00"))
    finally:
        asyncio.run(client.aclose())


def test_unknown_tender_is_blocked_before_network(tmp_path: Path) -> None:
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, text="unused")

    service, client, _database = _service(tmp_path, handler)
    try:
        with pytest.raises(DocumentValidationError, match="không tải hoặc tự đoán"):
            asyncio.run(service.acquire("UNKNOWN"))
    finally:
        asyncio.run(client.aclose())
    assert calls == 0


def test_ambiguous_tender_identity_is_blocked_before_network(tmp_path: Path) -> None:
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, text="unused")

    service, client, database = _service(tmp_path, handler)
    other_url = "https://example.test/other/1"
    with database.session() as session:
        session.add(
            Notice(
                source_url=other_url,
                url_hash=hashlib.sha256(other_url.encode()).hexdigest(),
                notice_code="IB2600000002-00",
                source_notice_id="1",
                source_name="other",
                title="Ambiguous source id",
            )
        )
    try:
        with pytest.raises(DocumentValidationError, match="không duy nhất"):
            asyncio.run(service.acquire("1"))
    finally:
        asyncio.run(client.aclose())
    assert calls == 0


@pytest.mark.parametrize("status_code", [401, 403])
def test_denied_download_requires_human(status_code: int, tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/tender/1":
            return httpx.Response(200, text='<a href="/files/hsmt.pdf">HSMT.pdf</a>')
        return httpx.Response(status_code)

    service, client, _database = _service(tmp_path, handler)
    try:
        with pytest.raises(AccessDenied, match="HUMAN_REQUIRED"):
            asyncio.run(service.acquire("IB2600000001-00"))
    finally:
        asyncio.run(client.aclose())


def test_download_failure_is_accounted_and_staging_is_cleaned(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/tender/1":
            return httpx.Response(200, text='<a href="/files/hsmt.pdf">HSMT.pdf</a>')
        return httpx.Response(500, text="temporary failure")

    service, client, _database = _service(tmp_path, handler)
    try:
        summary = asyncio.run(service.acquire("IB2600000001-00"))
    finally:
        asyncio.run(client.aclose())

    assert summary.discovered == 1
    assert summary.downloaded == 0
    assert summary.failed == 1
    assert not (tmp_path / "downloads" / ".document-intake-staging").exists()


def test_manual_upload_and_taxonomy_remain_available_after_web_import(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/tender/1":
            return httpx.Response(200, text='<a href="/files/boq.xlsx">BOQ.xlsx</a>')
        return httpx.Response(200, content=b"PK\x03\x04web-boq")

    service, client, database = _service(tmp_path, handler)
    try:
        web = asyncio.run(service.acquire("IB2600000001-00"))
    finally:
        asyncio.run(client.aclose())
    manual = tmp_path / "manual.pdf"
    manual.write_bytes(b"%PDF manual")
    manual_result = DocumentIntakeService(database, tmp_path / "documents").intake_file(manual)

    assert web.results[0].document_type == "BOQ_BOM"
    assert manual_result.outcome == "IMPORTED"


def test_browser_fetcher_type_is_preserved_for_production_contract() -> None:
    assert hasattr(BrowserFetcher, "download_page_attachments")
