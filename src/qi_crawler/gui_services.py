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
from sqlalchemy.engine import make_url

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
from .market_intelligence.confirmed_opportunity_export import ConfirmedOpportunityExportResult
from .market_intelligence.filter_engine import CriterionEvaluation, OpportunityFilterDisposition
from .market_intelligence.khmt_importer import import_khmt_workbook
from .market_intelligence.legal_docx import (
    LegalDocxExportResult,
    export_confirmed_legal_docx_records,
)
from .market_intelligence.opportunity_contract import OpportunitySourceType
from .market_intelligence.opportunity_intelligence import (
    OpportunityImportIssue,
    OpportunityIntelligenceService,
    OpportunityLoadResult,
)
from .market_intelligence.opportunity_radar import (
    OpportunityRadarItem,
    radar_item_from_plan_package,
)
from .market_intelligence.opportunity_review import OpportunityReviewService
from .market_intelligence.search import TargetedSearchRequest
from .market_intelligence.source_detection import (
    SourceType,
    SourceTypeDetection,
)
from .market_intelligence.source_integrity import verify_source_integrity
from .market_intelligence.source_type_review import SourceTypeReviewService
from .migrations import upgrade_database
from .models import Document, DocumentEvidence, DocumentExtraction, Notice
from .native_extraction import (
    SUPPORTED_FORMATS,
    NativeExtractionError,
    NativeHSMTExtractionService,
)
from .notice_search import search_notices
from .opportunity_review_persistence import SqlAlchemyOpportunityReviewRepository
from .opportunity_workspace_handoff import (
    OpportunityWorkspaceHandoffResult,
    OpportunityWorkspaceHandoffService,
)
from .source_filter import active_source_domains, active_source_names
from .tender_workspace import (
    RevisionWorkspaceStatus,
    TeamBidZone,
    TenderWorkspaceManifest,
    TenderWorkspaceService,
    WorkspaceEntry,
    WorkspaceExportResult,
)
from .web_document_intake import TenderWebDocumentService, WebDocumentIntakeSummary
from .workspace_candidate_intake import ConfirmedWorkspaceCandidate, WorkspaceCandidate

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


@dataclass(frozen=True)
class DatabaseReadinessResult:
    """Result of an explicit, operator-triggered database maintenance run."""

    database_path: Path | None
    revision: str
    backup_path: Path | None


def resolve_database_path(database_url: str) -> Path | None:
    """Resolve the database identity shown to an operator without mutating it."""
    url = make_url(database_url)
    if not url.drivername.startswith("sqlite") or not url.database:
        return None
    if url.database == ":memory:":
        return None
    path = Path(url.database)
    return path if path.is_absolute() else (Path.cwd() / path).resolve()


def run_database_upgrade(config: AppConfig) -> DatabaseReadinessResult:
    """Run the existing migration authority only after explicit human action."""
    backup_dir = config.storage.report_dir.parent / "backups"
    result = upgrade_database(config.storage.database_url, backup_dir=backup_dir)
    Database(config.storage.database_url).require_current_schema()
    return DatabaseReadinessResult(
        database_path=resolve_database_path(config.storage.database_url),
        revision=result.revision,
        backup_path=result.backup_path,
    )

@dataclass(frozen=True)
class BidRadarRow:
    """One filter evaluation plus the latest explicit human review state."""

    item: OpportunityRadarItem
    disposition: OpportunityFilterDisposition
    reasons: tuple[str, ...]
    review_state: str
    criteria: tuple[CriterionEvaluation, ...] = ()


@dataclass(frozen=True)
class BidRadarResult:
    """Source-neutral Bid Radar delivery result."""

    source_type: OpportunitySourceType
    load_result: OpportunityLoadResult
    source_path: Path
    source_sha256: str
    items: tuple[OpportunityRadarItem, ...]
    issues: tuple[OpportunityImportIssue, ...]
    rows: tuple[BidRadarRow, ...]
    matched_count: int
    indeterminate_count: int
    nonmatched_count: int
    unfiltered_count: int
    total_examined: int


def _bid_radar_rows(
    service: OpportunityIntelligenceService,
    evaluations: tuple[object, ...],
) -> tuple[BidRadarRow, ...]:
    rows: list[BidRadarRow] = []
    for evaluated in evaluations:
        item = evaluated.item
        evaluation = evaluated.evaluation
        event = service.current_event(item)
        rows.append(
            BidRadarRow(
                item=item,
                disposition=evaluation.disposition,
                reasons=tuple(criterion.reason_code.value for criterion in evaluation.criteria),
                review_state=event.decision.value if event is not None else "UNREVIEWED",
                criteria=evaluation.criteria,
            )
        )
    return tuple(rows)


def run_bid_radar_import_search(
    config: AppConfig,
    source_path: Path,
    request: TargetedSearchRequest,
    *,
    source_type: SourceType = SourceType.KHMT,
    source_detection: SourceTypeDetection | None = None,
    source_reviewer: str | None = None,
) -> BidRadarResult:
    """Import and evaluate KHMT or TBMT through the source-neutral backend."""
    source_map = {
        SourceType.KHMT: OpportunitySourceType.KHMT,
        SourceType.TBMT: OpportunitySourceType.TBMT,
    }
    try:
        opportunity_source = source_map[source_type]
    except KeyError as exc:
        raise ValueError("Chỉ nguồn KHMT hoặc TBMT được phép nhập vào Bid Radar.") from exc
    database = Database(config.storage.database_url)
    database.require_current_schema()
    service = OpportunityIntelligenceService(
        OpportunityReviewService(SqlAlchemyOpportunityReviewRepository(database))
    )
    loaded = service.load_workbook(Path(source_path), opportunity_source)
    searched = service.search_opportunities(loaded.items, request)
    if source_detection is not None and (
        source_detection.requires_human or source_reviewer
    ):
        SourceTypeReviewService(database).record_decision(
            source_detection,
            final_type=source_type,
            reviewer=source_reviewer,
        )
    return BidRadarResult(
        source_type=loaded.source_type,
        load_result=loaded,
        source_path=loaded.source_path,
        source_sha256=loaded.source_sha256,
        items=loaded.items,
        issues=loaded.issues,
        rows=_bid_radar_rows(service, searched.evaluated),
        matched_count=searched.matched_count,
        indeterminate_count=searched.indeterminate_count,
        nonmatched_count=searched.nonmatched_count,
        unfiltered_count=searched.unfiltered_count,
        total_examined=searched.total_examined,
    )


def run_bid_radar_source_review(
    config: AppConfig,
    detection: SourceTypeDetection,
    final_type: SourceType,
    reviewer: str,
    note: str = "",
) -> str:
    """Persist one explicit source-type correction without importing data."""
    database = Database(config.storage.database_url)
    database.require_current_schema()
    event = SourceTypeReviewService(database).record_decision(
        detection,
        final_type=final_type,
        reviewer=reviewer,
        note=note,
    )
    return event.final_type


def run_bid_radar_review(
    config: AppConfig,
    item: OpportunityRadarItem,
    decision: str,
    reviewer: str,
    note: str = "",
) -> str:
    """Record one explicit source-neutral human decision through MI-3."""
    database = Database(config.storage.database_url)
    database.require_current_schema()
    service = OpportunityIntelligenceService(
        OpportunityReviewService(SqlAlchemyOpportunityReviewRepository(database))
    )
    event = service.record_review(
        item,
        decision=decision,
        reviewer=reviewer,
        note=note,
    )
    return event.decision.value


def run_bid_radar_workspace_handoff(
    config: AppConfig,
    item: OpportunityRadarItem,
) -> OpportunityWorkspaceHandoffResult:
    """Open the authoritative TenderCase for a persisted confirmed opportunity."""
    database = Database(config.storage.database_url)
    database.require_current_schema()
    review_service = OpportunityReviewService(
        SqlAlchemyOpportunityReviewRepository(database)
    )
    workspace_service = TenderWorkspaceService(database, config.storage.document_dir)
    return OpportunityWorkspaceHandoffService(
        review_service,
        workspace_service,
    ).handoff(item)


def run_bid_radar_export(
    config: AppConfig,
    load_result: OpportunityLoadResult | tuple[object, ...],
    *,
    source_path: Path,
    expected_source_sha256: str,
) -> ConfirmedOpportunityExportResult:
    """Export current confirmations through the source-neutral MI facade."""
    if not isinstance(load_result, OpportunityLoadResult):
        verify_source_integrity(source_path, expected_source_sha256)
        raise TypeError("Bid Radar export requires the authoritative imported source.")
    database = Database(config.storage.database_url)
    database.require_current_schema()
    service = OpportunityIntelligenceService(
        OpportunityReviewService(SqlAlchemyOpportunityReviewRepository(database))
    )
    return service.export_confirmed(
        load_result,
        output=config.storage.report_dir / "CÁC GÓI ĐÃ XÁC NHẬN.xlsx",
    )


def run_bid_radar_legal_docx(
    config: AppConfig,
    load_result: OpportunityLoadResult | tuple[object, ...],
    *,
    source_path: Path,
    expected_source_sha256: str,
) -> tuple[LegalDocxExportResult, ...]:
    """Generate KHMT Legal DOCX from source-neutral confirmed observations."""
    if not isinstance(load_result, OpportunityLoadResult):
        verify_source_integrity(source_path, expected_source_sha256)
        raise TypeError("Legal DOCX requires the authoritative imported source.")
    if load_result.source_type is not OpportunitySourceType.KHMT:
        raise ValueError("Legal DOCX hiện chỉ hỗ trợ nguồn KHMT; TBMT chưa có mẫu DOCX.")
    verify_source_integrity(load_result.source_path, load_result.source_sha256)
    database = Database(config.storage.database_url)
    database.require_current_schema()
    service = OpportunityIntelligenceService(
        OpportunityReviewService(SqlAlchemyOpportunityReviewRepository(database))
    )
    packages = import_khmt_workbook(load_result.source_path).packages
    package_by_key = {
        radar_item_from_plan_package(package).observation_key: package
        for package in packages
    }
    confirmed = service.current_confirmed(load_result.items)
    selected = []
    for record in confirmed:
        package = package_by_key.get(record.identity.observation_key)
        if package is None:
            raise ValueError("KHMT Legal DOCX không tìm thấy đúng gói theo source identity.")
        selected.append((package, record))
    return export_confirmed_legal_docx_records(
        selected,
        output_dir=config.storage.report_dir,
    )


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


def run_export(config: AppConfig, *, snapshot: bool = False) -> TBMTExportResult:
    """Export today's active-source notices through the existing exporter."""
    database = Database(config.storage.database_url)
    database.require_current_schema()
    return export_tbmt(
        database,
        report_dir=config.storage.report_dir,
        rejects_dir=config.storage.rejects_dir,
        snapshot=snapshot,
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


def run_tender_workspace_manifest(
    config: AppConfig,
    case_id: str,
    release_id: int | None = None,
) -> TenderWorkspaceManifest:
    """Read a domain-authoritative Team Bid workspace through one thin adapter."""
    database = Database(config.storage.database_url)
    database.require_current_schema()
    return TenderWorkspaceService(database, config.storage.document_dir).manifest(case_id, release_id)


def run_tender_workspace_search(config: AppConfig, query: str):
    """Search case/release identifiers without selecting a mutable revision."""
    database = Database(config.storage.database_url)
    database.require_current_schema()
    return TenderWorkspaceService(database, config.storage.document_dir).search_cases(query)


def run_tender_workspace_dashboard(
    config: AppConfig,
    case_id: str,
    release_id: int,
    verify_integrity: bool = False,
):
    """Read one exact-release operational dashboard through the application seam."""
    database = Database(config.storage.database_url)
    database.require_current_schema()
    return TenderWorkspaceService(database, config.storage.document_dir).release_dashboard(
        case_id, release_id, verify_integrity=verify_integrity
    )


def run_tender_workspace_open_or_create(
    config: AppConfig,
    case_id: str,
    release_id: str,
) -> int:
    """Open/create one case and exact IB release through the workspace service."""
    database = Database(config.storage.database_url)
    database.require_current_schema()
    return TenderWorkspaceService(database, config.storage.document_dir).open_or_create_release(
        case_id,
        release_id,
    )


def run_tender_workspace_add_path(
    config: AppConfig,
    case_id: str,
    release_id: int,
    input_path: Path,
    zone: TeamBidZone | str,
    authority: str,
    evidence: str,
    uploaded_by: str | None = None,
) -> tuple[WorkspaceEntry, ...]:
    """Intake and explicitly assign source files to one logical workspace zone."""
    database = Database(config.storage.database_url)
    database.require_current_schema()
    return TenderWorkspaceService(database, config.storage.document_dir).add_path_to_zone(
        case_id,
        release_id,
        input_path,
        zone=zone,
        authority=authority,
        evidence=evidence,
        uploaded_by=uploaded_by,
    )


def run_tender_workspace_scan_folder(
    config: AppConfig,
    input_path: Path,
) -> tuple[WorkspaceCandidate, ...]:
    """Scan a folder read-only; no candidate is persisted by this adapter."""

    database = Database(config.storage.database_url)
    database.require_current_schema()
    return TenderWorkspaceService(database, config.storage.document_dir).scan_folder(input_path)


def run_tender_workspace_add_confirmed_candidates(
    config: AppConfig,
    case_id: str,
    release_id: int,
    confirmed_candidates: tuple[ConfirmedWorkspaceCandidate, ...],
) -> tuple[WorkspaceEntry, ...]:
    """Persist only candidates carrying an explicit Human confirmation."""

    database = Database(config.storage.database_url)
    database.require_current_schema()
    return TenderWorkspaceService(
        database, config.storage.document_dir
    ).add_confirmed_candidates(case_id, release_id, confirmed_candidates)


def run_tender_revision_status(
    config: AppConfig, case_id: str, release_id: int
) -> RevisionWorkspaceStatus:
    """Read latest/pending revision state through the workspace facade."""
    database = Database(config.storage.database_url)
    database.require_current_schema()
    return TenderWorkspaceService(database, config.storage.document_dir).revision_status(
        case_id, release_id
    )


def run_tender_revision_accept(
    config: AppConfig,
    case_id: str,
    release_id: int,
    actor: str,
    reason: str,
    evidence: str,
):
    database = Database(config.storage.database_url)
    database.require_current_schema()
    return TenderWorkspaceService(database, config.storage.document_dir).accept_revision(
        case_id, release_id, actor=actor, reason=reason, evidence=evidence
    )


def run_tender_revision_reject(
    config: AppConfig,
    case_id: str,
    release_id: int,
    actor: str,
    reason: str,
    evidence: str,
):
    database = Database(config.storage.database_url)
    database.require_current_schema()
    return TenderWorkspaceService(database, config.storage.document_dir).reject_revision(
        case_id, release_id, actor=actor, reason=reason, evidence=evidence
    )


def run_tender_revision_compare(
    config: AppConfig, case_id: str, previous_release_id: int, latest_release_id: int, **kwargs
):
    database = Database(config.storage.database_url)
    database.require_current_schema()
    return TenderWorkspaceService(database, config.storage.document_dir).compare_revisions(
        case_id, previous_release_id, latest_release_id, **kwargs
    )


def run_tender_revision_activate(
    config: AppConfig,
    case_id: str,
    release_id: int,
    actor: str,
    reason: str,
    evidence: str,
):
    database = Database(config.storage.database_url)
    database.require_current_schema()
    return TenderWorkspaceService(database, config.storage.document_dir).activate_revision(
        case_id, release_id, actor=actor, reason=reason, evidence=evidence
    )

def run_tender_workspace_export(
    config: AppConfig,
    case_id: str,
    destination: Path,
    release_id: int | None = None,
) -> WorkspaceExportResult:
    """Export immutable managed originals into a controlled logical-zone workspace."""
    database = Database(config.storage.database_url)
    database.require_current_schema()
    workspace = TenderWorkspaceService(database, config.storage.document_dir)
    if release_id is None:
        return workspace.export(case_id, destination)
    return workspace.export_release(case_id, release_id, destination)


def run_tender_workspace_replace(
    config: AppConfig,
    case_id: str,
    release_id: int,
    prior_entry_id: int,
    replacement_path: Path,
    evidence: str,
    actor: str | None = None,
):
    database = Database(config.storage.database_url)
    database.require_current_schema()
    return TenderWorkspaceService(database, config.storage.document_dir).replace_entry(
        case_id,
        release_id,
        prior_entry_id,
        replacement_path,
        evidence=evidence,
        actor=actor,
    )


def run_tender_workspace_source_correction(
    config: AppConfig,
    case_id: str,
    release_id: int,
    prior_entry_id: int,
    replacement_path: Path | None,
    operator: str,
    reason: str,
    evidence: str,
):
    database = Database(config.storage.database_url)
    database.require_current_schema()
    return TenderWorkspaceService(database, config.storage.document_dir).correct_source_entry(
        case_id,
        release_id,
        prior_entry_id,
        replacement_path,
        operator=operator,
        reason=reason,
        evidence=evidence,
    )


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
