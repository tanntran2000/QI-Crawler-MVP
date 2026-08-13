"""Packaged-runtime smoke checks used by release engineering."""

from __future__ import annotations

import asyncio
import hashlib
import json
import tempfile
import zipfile
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import httpx

from .browser import BrowserFetcher
from .config import AppConfig
from .db import Database
from .document_intake import DocumentIdentityMismatch, DocumentIntakeService
from .document_taxonomy import DocumentClassificationService
from .gui_services import run_export, run_scan, run_search, run_single_crawl
from .http_client import HttpFetcher
from .models import Notice
from .web_document_intake import TenderWebDocumentService

COTEC_LIST_URL = "https://ebidding.coteccons.vn/Index"
COTEC_DETAIL_URL = "https://ebidding.coteccons.vn/Index/ChiTiet/2607301"


def _browser_smoke(config: AppConfig) -> None:
    async def execute() -> None:
        browser = BrowserFetcher(config)
        try:
            await browser.start(headed=False)
            page = await browser.new_page()
            await page.close()
        finally:
            await browser.close()

    asyncio.run(execute())


def _document_intake_smoke(config: AppConfig, working_dir: Path) -> dict[str, object]:
    """Exercise the packaged Document Store using isolated synthetic files."""
    database = Database(config.storage.database_url)
    database.require_current_schema()
    stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")
    tender_code = f"SMOKE-DOC-{stamp}"
    tender_url = f"https://smoke.example/tender/{tender_code}"
    with database.session() as session:
        tender = Notice(
            source_url=tender_url,
            url_hash=hashlib.sha256(tender_url.encode()).hexdigest(),
            notice_code=tender_code,
            source_notice_id=tender_code,
            source_name="smoke",
            title="HSMT smoke test",
        )
        session.add(tender)

    intake = DocumentIntakeService(database, config.storage.document_dir)
    with tempfile.TemporaryDirectory(prefix="qi-crawler-document-smoke-", dir=working_dir) as raw:
        source_dir = Path(raw)
        samples = {
            "HSMT.pdf": b"%PDF smoke " + stamp.encode(),
            "technical.docx": b"PK\x03\x04 docx " + stamp.encode(),
            "BOQ.xlsx": b"PK\x03\x04 xlsx " + stamp.encode(),
        }
        files: list[Path] = []
        for filename, content in samples.items():
            path = source_dir / filename
            path.write_bytes(content)
            files.append(path)
        archive = source_dir / "appendix.zip"
        with zipfile.ZipFile(archive, "w") as zip_file:
            zip_file.writestr("appendix.pdf", b"%PDF appendix " + stamp.encode())
        files.append(archive)

        imported = [
            intake.intake_file(
                path,
                tender_reference=tender_code,
                document_name="Hồ sơ mời thầu qua mạng" if path.suffix == ".pdf" else None,
            )
            for path in files
        ]
        duplicate = intake.intake_file(files[0], tender_reference=tender_code)
        revised = source_dir / "HSMT-revised.pdf"
        revised.write_bytes(b"%PDF revised " + stamp.encode())
        new_version = intake.intake_file(revised, tender_reference=tender_code)

        other_url = f"https://smoke.example/tender/other-{stamp}"
        with database.session() as session:
            session.add(
                Notice(
                    source_url=other_url,
                    url_hash=hashlib.sha256(other_url.encode()).hexdigest(),
                    notice_code=f"SMOKE-OTHER-{stamp}",
                    source_notice_id=f"OTHER-{stamp}",
                    source_name="smoke",
                    title="Other smoke tender",
                )
            )
        try:
            intake.intake_file(files[0], tender_reference=f"SMOKE-OTHER-{stamp}")
        except DocumentIdentityMismatch:
            mismatch_blocked = True
        else:
            mismatch_blocked = False

        confirmed = DocumentClassificationService(database).confirm(
            imported[0].document_id,
            "E_HSMT",
        )

        async def web_attachment_smoke() -> int:
            if "smoke.example" not in config.allowed_domains:
                config.allowed_domains.append("smoke.example")
            original_robots = config.compliance.obey_robots_txt
            config.compliance.obey_robots_txt = False

            def handler(request: httpx.Request) -> httpx.Response:
                if request.url.path == f"/tender/{tender_code}":
                    return httpx.Response(
                        200,
                        text='<a href="/documents/web-hsmt.pdf">HSMT web</a>',
                    )
                return httpx.Response(200, content=b"%PDF web " + stamp.encode())

            fetcher = HttpFetcher(config)
            await fetcher.client.aclose()
            client = httpx.AsyncClient(
                transport=httpx.MockTransport(handler), follow_redirects=True
            )
            fetcher.client = client
            try:
                service = TenderWebDocumentService(config, intake, http_fetcher=fetcher)
                summary = await service.acquire(tender_code)
                return summary.downloaded
            finally:
                config.compliance.obey_robots_txt = original_robots
                await client.aclose()

        web_downloaded = asyncio.run(web_attachment_smoke())

    if not mismatch_blocked:
        raise RuntimeError("Document mismatch was not blocked")
    if duplicate.outcome != "DUPLICATE":
        raise RuntimeError("Duplicate document was not detected")
    if new_version.version != 5:
        raise RuntimeError("New document version was not created")
    if confirmed.status.value != "VERIFIED":
        raise RuntimeError("Taxonomy confirmation did not persist")
    if web_downloaded != 1:
        raise RuntimeError("Web attachment was not downloaded through intake")
    manifest = intake.manifest_for_tender(tender_code)
    return {
        "pdf_docx_xlsx_zip": len(imported),
        "duplicate": duplicate.outcome,
        "new_version": new_version.version,
        "mismatch_blocked": mismatch_blocked,
        "taxonomy": confirmed.status.value,
        "web_attachment_downloaded": web_downloaded,
        "persisted_documents": len(manifest.documents),
    }


def run_standalone_smoke(
    config: AppConfig,
    report_path: Path,
    *,
    include_network: bool = False,
    include_documents: bool = False,
) -> bool:
    """Exercise packaged resources and optionally permitted live crawl paths."""
    results: dict[str, object] = {
        "started_at": datetime.now(UTC).isoformat(),
        "include_network": include_network,
        "include_documents": include_documents,
        "checks": {},
    }
    checks = results["checks"]
    assert isinstance(checks, dict)
    success = True

    def run_check(name: str, function) -> None:
        nonlocal success
        try:
            value = function()
        except Exception as exc:  # noqa: BLE001 - release smoke must record every failure
            success = False
            checks[name] = {"status": "FAILED", "error": str(exc)}
        else:
            checks[name] = {"status": "PASS", "result": value}

    run_check("browser_launch", lambda: (_browser_smoke(config), "Chromium started")[1])
    run_check("search", lambda: len(run_search(config, "smoke-test")))
    run_check(
        "export",
        lambda: str(run_export(config).output),
    )
    if include_documents:
        run_check(
            "document_workspace",
            lambda: _document_intake_smoke(config, report_path.parent),
        )
    if include_network:
        run_check(
            "single_url_crawl",
            lambda: run_single_crawl(config, COTEC_DETAIL_URL),
        )
        run_check(
            "list_scan",
            lambda: asdict(run_scan(config, COTEC_LIST_URL, 1, "")),
        )

        def search_after_crawl() -> int:
            count = len(run_search(config, "goi thau"))
            if count < 1:
                raise RuntimeError("Search khong tim thay goi vua crawl")
            return count

        def export_after_crawl() -> dict[str, object]:
            result = run_export(config)
            if result.exported_records < 1:
                raise RuntimeError("Export khong co dong du lieu sau live crawl")
            return {
                "output": str(result.output),
                "exported_records": result.exported_records,
                "warning_records": result.warning_records,
            }

        run_check("search_after_crawl", search_after_crawl)
        run_check("export_after_crawl", export_after_crawl)

    results["finished_at"] = datetime.now(UTC).isoformat()
    results["status"] = "PASS" if success else "FAILED"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return success
