from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import yaml
from openpyxl import Workbook
from openpyxl.styles import Font
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from .authenticated_sources import collect_authenticated_source, load_source
from .contracts_finder import collect_contracts_finder
from .crawler import CrawlerService
from .excel_safety import safe_excel_row
from .keywords import expand_keyword
from .models import CompanyEvidence, InventoryItem, Notice
from .opportunity import KeywordGroup, OpportunityAssessment, assess_opportunity


class KeywordGroupConfig(BaseModel):
    name: str
    terms: list[str] = Field(min_length=1)
    weight: float = Field(ge=0, le=30)


class MonitoringConfig(BaseModel):
    interval_minutes: int = Field(default=60, ge=5, le=1440)
    lookback_days: int = Field(default=14, ge=1, le=365)
    limit_per_keyword: int = Field(default=50, ge=1, le=200)
    contracts_finder: bool = True
    authenticated_sources: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(min_length=1)
    keyword_groups: list[KeywordGroupConfig] = Field(default_factory=list)
    required_any: list[str] = Field(default_factory=list)
    required_all: list[str] = Field(default_factory=list)
    excluded_keywords: list[str] = Field(default_factory=list)
    priority_threshold: float = Field(default=75, ge=0, le=100)
    review_threshold: float = Field(default=55, ge=0, le=100)
    closing_soon_days: int = Field(default=3, ge=1, le=30)
    new_alert_hours: int = Field(default=24, ge=1, le=168)
    output: Path = Path("data/reports/co-hoi-uu-tien.xlsx")


FeasibilityAssessment = OpportunityAssessment


@dataclass(frozen=True)
class MonitoringSummary:
    collected: int
    assessed: int
    priority: int
    review: int
    skip: int
    insufficient: int
    output: Path

    @property
    def feasible(self) -> int:
        return self.priority

    @property
    def low(self) -> int:
        return self.skip


def load_monitoring_config(path: Path) -> MonitoringConfig:
    if not path.exists():
        raise FileNotFoundError(
            f"Chua co {path}. Hay sao chep monitoring.example.yaml thanh monitoring.yaml."
        )
    return MonitoringConfig.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})


def assess_notice_feasibility(
    notice: Notice,
    keyword_terms: tuple[str, ...],
    evidence: list[CompanyEvidence],
    inventory: list[InventoryItem] | None = None,
    now: datetime | None = None,
) -> FeasibilityAssessment:
    return assess_opportunity(
        notice,
        (KeywordGroup("Configured products", keyword_terms, 30.0),),
        evidence,
        inventory or [],
        now=now,
    )


def _attachment_status(notice: Notice) -> str:
    if not notice.attachments:
        return "NO_ATTACHMENTS"
    statuses = {item.download_status for item in notice.attachments}
    if statuses <= {"downloaded"}:
        return "DOWNLOADED"
    if statuses & {"failed", "manual_review"}:
        return "FAILED_OR_REVIEW"
    if "downloaded" in statuses:
        return "PARTIAL"
    return "PENDING"


def _write_ranked_report(
    output: Path,
    rows: list[tuple[Notice, FeasibilityAssessment]],
) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Co hoi xep hang"
    sheet.append(
        [
            "priority",
            "status",
            "score",
            "notice_code",
            "notice_version",
            "title",
            "buyer",
            "investor",
            "closing_at",
            "days_left",
            "package_price",
            "currency",
            "location",
            "sector",
            "selection_method",
            "attachment_status",
            "matched_groups",
            "matched_keywords",
            "excluded_keywords",
            "matched_evidence",
            "missing_data",
            "risks",
            "score_explanation",
            "alerts",
            "next_action",
            "source_url",
        ]
    )
    for notice, assessment in rows:
        sheet.append(
            safe_excel_row([
                assessment.priority,
                assessment.status,
                assessment.score,
                notice.notice_code,
                notice.notice_version,
                notice.title,
                notice.buyer,
                notice.investor,
                notice.closing_at,
                round(assessment.days_left, 1) if assessment.days_left is not None else None,
                notice.package_price,
                notice.currency,
                notice.location,
                notice.sector,
                notice.selection_method,
                _attachment_status(notice),
                ", ".join(assessment.matched_groups),
                ", ".join(assessment.matched_keywords),
                ", ".join(assessment.excluded_keywords),
                ", ".join(assessment.matched_evidence),
                ", ".join(assessment.missing_fields),
                " | ".join(assessment.risks),
                " | ".join(
                    f"{item.name}={item.score:g}/{item.maximum:g}: {item.explanation}"
                    for item in assessment.components
                ),
                ", ".join(assessment.alerts),
                assessment.next_action,
                notice.source_url,
            ])
        )
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for column in sheet.columns:
        maximum = max(len(str(cell.value or "")) for cell in column)
        sheet.column_dimensions[column[0].column_letter].width = min(max(maximum + 2, 12), 70)
    workbook.save(output)
    return output


async def run_monitoring_cycle(
    service: CrawlerService,
    settings: MonitoringConfig,
) -> MonitoringSummary:
    expanded = [expand_keyword(keyword) for keyword in settings.keywords]
    terms = tuple(dict.fromkeys(term for item in expanded for term in item.search_terms))
    if settings.keyword_groups:
        keyword_groups = tuple(
            KeywordGroup(
                item.name,
                tuple(
                    dict.fromkeys(
                        term
                        for configured in item.terms
                        for term in expand_keyword(configured).search_terms
                    )
                ),
                item.weight,
            )
            for item in settings.keyword_groups
        )
        collection_terms = tuple(
            dict.fromkeys(term for group in keyword_groups for term in group.terms)
        )
    else:
        keyword_groups = (KeywordGroup("Configured products", terms, 30.0),)
        collection_terms = terms
    collected = 0
    if settings.contracts_finder:
        collection_batches = (
            [group.terms for group in keyword_groups]
            if settings.keyword_groups
            else [item.search_terms for item in expanded]
        )
        for batch in collection_batches:
            result = await collect_contracts_finder(
                service,
                keyword=batch,
                published_from=datetime.now(UTC).date() - timedelta(days=settings.lookback_days),
                limit=settings.limit_per_keyword,
                only_open=True,
            )
            collected += result.matched
    for source_name in settings.authenticated_sources:
        source = load_source(source_name)
        result = await collect_authenticated_source(
            service, source, keyword=collection_terms, limit=settings.limit_per_keyword
        )
        collected += result.matched

    service.db.create_all()
    with service.db.session() as session:
        evidence = list(session.scalars(select(CompanyEvidence).where(CompanyEvidence.verified)).all())
        inventory = list(session.scalars(select(InventoryItem).where(InventoryItem.verified)).all())
        notices = list(
            session.scalars(
                select(Notice)
                .options(selectinload(Notice.attachments), selectinload(Notice.tender_items))
                .order_by(Notice.id.desc())
            ).all()
        )
        session.expunge_all()
    ranked: list[tuple[Notice, FeasibilityAssessment]] = []
    for notice in notices:
        assessment = assess_opportunity(
            notice,
            keyword_groups,
            evidence,
            inventory,
            required_any=tuple(settings.required_any),
            required_all=tuple(settings.required_all),
            excluded_terms=tuple(settings.excluded_keywords),
            priority_threshold=settings.priority_threshold,
            review_threshold=settings.review_threshold,
            closing_soon_days=settings.closing_soon_days,
            new_alert_hours=settings.new_alert_hours,
        )
        if assessment.matched_keywords or assessment.excluded_keywords:
            ranked.append((notice, assessment))
    status_order = {"PRIORITY": 0, "REVIEW": 1, "INSUFFICIENT_DATA": 2, "SKIP": 3}
    ranked.sort(
        key=lambda row: (
            status_order[row[1].status],
            -(row[1].score or 0.0),
        )
    )
    output = _write_ranked_report(settings.output, ranked)
    return MonitoringSummary(
        collected=collected,
        assessed=len(ranked),
        priority=sum(item.status == "PRIORITY" for _, item in ranked),
        review=sum(item.status == "REVIEW" for _, item in ranked),
        skip=sum(item.status == "SKIP" for _, item in ranked),
        insufficient=sum(item.status == "INSUFFICIENT_DATA" for _, item in ranked),
        output=output,
    )


async def monitor_forever(service: CrawlerService, settings: MonitoringConfig) -> None:
    while True:
        try:
            summary = await run_monitoring_cycle(service, settings)
            print(
                f"Quet xong: thu thap={summary.collected}, priority={summary.priority}, "
                f"review={summary.review}, skip={summary.skip}, "
                f"thieu-du-lieu={summary.insufficient}; bao cao={summary.output}"
            )
        except (OSError, RuntimeError, ValueError) as exc:
            print(f"Luot quet gap loi: {exc}")
        print(f"Luot tiep theo sau {settings.interval_minutes} phut. Nhan Ctrl+C de dung.")
        await asyncio.sleep(settings.interval_minutes * 60)
