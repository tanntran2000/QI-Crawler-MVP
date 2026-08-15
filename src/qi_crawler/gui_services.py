"""Thin application-service adapters shared by the PySide6 GUI.

This module deliberately delegates to the existing crawler, search and export
services. It contains no parsing, crawling or persistence implementation.
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import or_, select

from .authenticated_sources import (
    create_login_session,
    egp_vietnam_source,
    load_source,
    save_source,
)
from .config import AppConfig
from .crawler import CrawlerService, ScanSummary
from .db import Database
from .document_intake import (
    DocumentBatchResult,
    DocumentIntakeService,
    DocumentValidationError,
    TenderDocumentManifest,
)
from .document_taxonomy import DocumentClassification, DocumentClassificationService
from .export import TBMTExportResult, export_tbmt
from .hsmt_facts import HSMTFactService, HSMTFactView
from .keywords import expand_keyword
from .manual_tender import ManualTenderWorkspaceService
from .models import Document, DocumentEvidence, DocumentExtraction, Notice
from .native_extraction import (
    SUPPORTED_FORMATS,
    NativeExtractionError,
    NativeHSMTExtractionService,
)
from .notice_search import search_notices
from .source_filter import active_source_domains, active_source_names
from .web_document_intake import TenderWebDocumentService, WebDocumentIntakeSummary

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SearchRow:
    identifier: str
    title: str
    buyer: str
    source: str
    source_url: str


@dataclass(frozen=True)
class EvidencePreview:
    source_locator: str
    page_number: int | None
    sheet_name: str | None
    content_type: str
    text: str | None
    table_json: str | None


@dataclass(frozen=True)
class DocumentExtractionInspection:
    document_id: int
    filename: str
    file_format: str
    status: str
    evidence_count: int
    page_count: int
    sheet_count: int
    text_count: int
    table_count: int
    flags: tuple[str, ...]
    evidence: tuple[EvidencePreview, ...]


@dataclass(frozen=True)
class HSMTFactDashboard:
    tender_id: int
    facts: tuple[HSMTFactView, ...]

    def count_for(self, group: str) -> int:
        return sum(item.fact_group == group for item in self.facts)

    def review_count_for(self, group: str) -> int:
        return sum(
            item.fact_group == group and item.status != "FOUND" for item in self.facts
        )


@dataclass(frozen=True)
class WorkspaceDocumentIntakeResult:
    """One explicit workspace switch followed by a guarded document intake."""

    manifest: TenderDocumentManifest
    batch: DocumentBatchResult


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
    batch = service.intake_path(
        input_path,
        tender_reference=tender_reference or None,
        document_name=document_name or None,
        document_source="manual_upload",
        uploaded_by=uploaded_by or None,
    )
    extractor = NativeHSMTExtractionService(database)
    warnings: list[str] = []
    for result in batch.results:
        if result.file_format not in SUPPORTED_FORMATS:
            continue
        try:
            extractor.extract_document(result.document_id)
        except NativeExtractionError as exc:
            logger.exception("Native extraction requires review document_id=%s", result.document_id)
            warnings.append(str(exc))
    return DocumentBatchResult(batch.results, tuple(warnings))


def run_document_extraction_inspection(
    config: AppConfig,
    document_id: int,
) -> DocumentExtractionInspection:
    """Read persisted native extraction/evidence without changing document state."""
    database = Database(config.storage.database_url)
    database.require_current_schema()
    with database.session() as session:
        document = session.get(Document, document_id)
        if document is None:
            raise ValueError("Khong tim thay tai lieu da chon.")
        extraction = session.scalar(
            select(DocumentExtraction)
            .where(DocumentExtraction.document_id == document_id)
            .order_by(DocumentExtraction.created_at.desc())
        )
        evidence_rows = ()
        if extraction is not None:
            evidence_rows = tuple(
                session.scalars(
                    select(DocumentEvidence)
                    .where(DocumentEvidence.extraction_id == extraction.id)
                    .order_by(DocumentEvidence.ordinal)
                )
            )

        flags: set[str] = set()
        for row in evidence_rows:
            metadata = json.loads(row.metadata_json or "{}")
            flags.update(metadata.get("flags") or ())
        evidence = tuple(
            EvidencePreview(
                source_locator=row.source_locator,
                page_number=row.page_number,
                sheet_name=row.sheet_name,
                content_type=row.content_type,
                text=row.text,
                table_json=row.table_json,
            )
            for row in evidence_rows
        )
        return DocumentExtractionInspection(
            document_id=document.id,
            filename=document.original_filename,
            file_format=document.file_format or "-",
            status=extraction.status if extraction is not None else "NOT_EXTRACTED",
            evidence_count=len(evidence),
            page_count=len({row.page_number for row in evidence_rows if row.page_number}),
            sheet_count=len({row.sheet_name for row in evidence_rows if row.sheet_name}),
            text_count=sum(row.content_type == "TEXT" for row in evidence_rows),
            table_count=sum(row.content_type != "TEXT" for row in evidence_rows),
            flags=tuple(sorted(flags)),
            evidence=evidence,
        )


def run_create_manual_tender_workspace(
    config: AppConfig,
    tender_code: str,
    package_name: str,
    shortlisted: bool,
    business_priority: str,
    reviewed_by: str,
    manual_note: str,
) -> TenderDocumentManifest:
    """Create one human-declared workspace, then read its existing manifest."""
    database = Database(config.storage.database_url)
    database.require_current_schema()
    workspace = ManualTenderWorkspaceService(database).create_workspace(
        tender_code,
        package_name=package_name or None,
        shortlisted=shortlisted,
        business_priority=business_priority,
        reviewed_by=reviewed_by or None,
        manual_note=manual_note or None,
    )
    return DocumentIntakeService(
        database,
        config.storage.document_dir,
    ).manifest_for_tender(workspace.tender_code)


def run_tender_document_workspace(
    config: AppConfig,
    tender_reference: str,
) -> TenderDocumentManifest:
    """Read one tender's document manifest without changing document state."""
    database = Database(config.storage.database_url)
    database.require_current_schema()
    manifest = DocumentIntakeService(
        database,
        config.storage.document_dir,
    ).manifest_for_tender(tender_reference)
    HSMTFactService(database).refresh_tender(manifest.tender_id)
    return manifest


def run_open_or_create_tender_document_workspace(
    config: AppConfig,
    tender_reference: str,
) -> TenderDocumentManifest:
    """Open an existing tender workspace or create an explicit Team Bid workspace."""
    database = Database(config.storage.database_url)
    database.require_current_schema()
    intake = DocumentIntakeService(database, config.storage.document_dir)
    try:
        manifest = intake.manifest_for_tender(tender_reference)
    except DocumentValidationError:
        manifest = _manifest_for_base_or_new_workspace(
            database,
            intake,
            tender_reference,
        )
    HSMTFactService(database).refresh_tender(manifest.tender_id)
    return manifest


def run_workspace_document_intake(
    config: AppConfig,
    input_path: Path,
    tender_reference: str,
    document_name: str = "",
) -> WorkspaceDocumentIntakeResult:
    """Switch only after confirmation, then intake against that isolated workspace."""
    opened = run_open_or_create_tender_document_workspace(config, tender_reference)
    batch = run_document_intake(
        config,
        input_path,
        opened.tender_identifier,
        document_name,
    )
    manifest = run_tender_document_workspace(config, opened.tender_identifier)
    return WorkspaceDocumentIntakeResult(manifest=manifest, batch=batch)


def _manifest_for_base_or_new_workspace(
    database: Database,
    intake: DocumentIntakeService,
    tender_reference: str,
) -> TenderDocumentManifest:
    """Resolve a single existing revision before creating a human workspace."""
    base = _base_tender_reference(tender_reference)
    with database.session() as session:
        candidates = tuple(
            session.scalars(
                select(Notice)
                .where(
                    or_(
                        Notice.notice_code == base,
                        Notice.source_notice_id == base,
                        Notice.notice_code.like(f"{base}-%"),
                        Notice.source_notice_id.like(f"{base}-%"),
                    )
                )
                .limit(2)
            )
        )
    if len(candidates) == 1:
        identifier = candidates[0].notice_code or candidates[0].source_notice_id
        assert identifier is not None
        return intake.manifest_for_tender(identifier)
    if len(candidates) > 1:
        raise DocumentValidationError(
            "Mã gói có nhiều revision trong dữ liệu; hãy chọn đúng gói trước khi nhập tài liệu."
        )
    workspace = ManualTenderWorkspaceService(database).create_workspace(base)
    return intake.manifest_for_tender(workspace.tender_code)


def _base_tender_reference(value: str) -> str:
    normalized = value.strip().upper()
    base, separator, revision = normalized.rpartition("-")
    return base if separator and revision.isdigit() else normalized


def run_hsmt_fact_dashboard(config: AppConfig, tender_id: int) -> HSMTFactDashboard:
    """Read persisted/derived facts for one tender; no native extraction is invoked."""
    database = Database(config.storage.database_url)
    database.require_current_schema()
    service = HSMTFactService(database)
    service.refresh_tender(tender_id)
    facts = service.facts_for_tender(tender_id)
    return HSMTFactDashboard(tender_id=tender_id, facts=facts)


def run_web_document_intake(
    config: AppConfig,
    tender_reference: str,
) -> WebDocumentIntakeSummary:
    """Discover and import web attachments through the shared intake service."""

    async def execute() -> WebDocumentIntakeSummary:
        database = Database(config.storage.database_url)
        database.require_current_schema()
        intake = DocumentIntakeService(database, config.storage.document_dir)
        service = TenderWebDocumentService(config, intake)
        try:
            return await service.acquire(tender_reference)
        finally:
            await service.close()

    return asyncio.run(execute())


def run_document_classification_confirmation(
    config: AppConfig,
    document_id: int,
    document_type: str,
    template_code: str = "",
    package_type: str = "",
    selection_method: str = "",
) -> DocumentClassification:
    """Confirm one candidate through the shared classification service."""
    database = Database(config.storage.database_url)
    database.require_current_schema()
    return DocumentClassificationService(database).confirm(
        document_id,
        document_type,
        template_code=template_code or None,
        package_type=package_type or None,
        selection_method=selection_method or None,
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
