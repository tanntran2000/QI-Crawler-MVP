"""Thin application-service adapters shared by the PySide6 GUI.

This module deliberately delegates to the existing crawler, search and export
services. It contains no parsing, crawling or persistence implementation.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from dataclasses import dataclass
from pathlib import Path

from .authenticated_sources import (
    create_login_session,
    egp_vietnam_source,
    load_source,
    save_source,
)
from .config import AppConfig
from .crawler import CrawlerService, ScanSummary
from .db import Database
from .document_intake import DocumentBatchResult, DocumentIntakeService
from .export import TBMTExportResult, export_tbmt
from .keywords import expand_keyword
from .notice_search import search_notices
from .source_filter import active_source_domains, active_source_names

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SearchRow:
    identifier: str
    title: str
    buyer: str
    source: str
    source_url: str


def _keyword_terms(value: str) -> tuple[str, ...]:
    terms: list[str] = []
    for raw_keyword in value.split(","):
        keyword = raw_keyword.strip()
        if keyword:
            terms.extend(expand_keyword(keyword).search_terms)
    return tuple(dict.fromkeys(terms))


def run_scan(
    config: AppConfig,
    list_url: str,
    max_pages: int,
    keywords: str,
) -> ScanSummary:
    """Run the existing async scan service from a worker thread."""

    async def execute() -> ScanSummary:
        service = CrawlerService(config)
        try:
            return await service.scan_list(
                list_url,
                keyword_terms=_keyword_terms(keywords),
                max_pages=max_pages,
                resume=False,
            )
        finally:
            await service.close()

    return asyncio.run(execute())


def run_single_crawl(config: AppConfig, detail_url: str) -> tuple[int, int, str | None]:
    """Run the existing single-URL crawler from a worker thread."""

    async def execute() -> tuple[int, int, str | None]:
        service = CrawlerService(config)
        try:
            success, failed = await service.crawl_urls([detail_url])
            return success, failed, service.human_required_reason
        finally:
            await service.close()

    logger.info("SERVICE_START operation=single_crawl")
    result = asyncio.run(execute())
    logger.info(
        "SERVICE_DONE operation=single_crawl success=%s failed=%s human_required=%s",
        result[0],
        result[1],
        bool(result[2]),
    )
    return result


def run_search(config: AppConfig, keyword: str, limit: int = 100) -> list[SearchRow]:
    """Search the existing database without learning or modifying keywords."""
    expansion = expand_keyword(keyword)
    database = Database(config.storage.database_url)
    database.require_current_schema()
    result = search_notices(
        database,
        expansion.search_terms,
        None,
        limit,
        tuple(active_source_names(config)),
        active_source_domains(config),
    )
    return [
        SearchRow(
            identifier=notice.notice_code
            or notice.source_notice_id
            or f"ID {notice.id}",
            title=notice.title or "Chua co ten",
            buyer=notice.buyer or "",
            source=notice.source_name or notice.source_kind or "",
            source_url=notice.source_url,
        )
        for notice in result.notices
    ]


def run_export(config: AppConfig) -> TBMTExportResult:
    """Export today's active-source notices through the existing exporter."""
    database = Database(config.storage.database_url)
    database.require_current_schema()
    return export_tbmt(
        database,
        report_dir=config.storage.report_dir,
        rejects_dir=config.storage.rejects_dir,
        current_day_only=True,
        active_source_names=tuple(active_source_names(config)),
        active_source_domains=active_source_domains(config),
    )


def run_document_intake(
    config: AppConfig,
    input_path: Path,
    tender_reference: str = "",
    document_name: str = "",
    uploaded_by: str = "",
) -> DocumentBatchResult:
    """Import a file/folder through the shared auditable intake service."""
    database = Database(config.storage.database_url)
    database.require_current_schema()
    service = DocumentIntakeService(database, config.storage.document_dir)
    return service.intake_path(
        input_path,
        tender_reference=tender_reference or None,
        document_name=document_name or None,
        document_source="manual_upload",
        uploaded_by=uploaded_by or None,
    )


def run_login(
    config: AppConfig,
    source_name: str,
    browser_ready: threading.Event | None = None,
    user_confirmed: threading.Event | None = None,
) -> Path:
    """Open the existing manual-login browser flow without storing credentials."""
    try:
        source = load_source(source_name)
    except FileNotFoundError:
        if source_name != "egp":
            raise
        source = egp_vietnam_source(name="egp")
        save_source(source)
    if user_confirmed is None:
        return asyncio.run(create_login_session(config, source))

    async def wait_for_confirmation() -> None:
        await asyncio.to_thread(user_confirmed.wait)

    return asyncio.run(
        create_login_session(
            config,
            source,
            wait_for_confirmation=wait_for_confirmation,
            browser_ready=browser_ready.set if browser_ready else None,
        )
    )
