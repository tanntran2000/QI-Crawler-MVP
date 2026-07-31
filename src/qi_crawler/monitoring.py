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

from .authenticated_sources import collect_authenticated_source, load_source
from .contracts_finder import collect_contracts_finder
from .crawler import CrawlerService
from .keywords import expand_keyword, matches_any_keyword
from .models import CompanyEvidence, Notice


class MonitoringConfig(BaseModel):
    interval_minutes: int = Field(default=60, ge=5, le=1440)
    lookback_days: int = Field(default=14, ge=1, le=365)
    limit_per_keyword: int = Field(default=50, ge=1, le=200)
    contracts_finder: bool = True
    authenticated_sources: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(min_length=1)
    output: Path = Path("data/reports/co-hoi-kha-thi.xlsx")


@dataclass(frozen=True)
class FeasibilityAssessment:
    notice_id: int
    score: float
    status: str
    matched_keywords: tuple[str, ...]
    matched_evidence: tuple[str, ...]
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class MonitoringSummary:
    collected: int
    assessed: int
    feasible: int
    review: int
    low: int
    output: Path


def load_monitoring_config(path: Path) -> MonitoringConfig:
    if not path.exists():
        raise FileNotFoundError(
            f"Chua co {path}. Hay sao chep monitoring.example.yaml thanh monitoring.yaml."
        )
    return MonitoringConfig.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})


def _parse_deadline(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
        return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)
    except ValueError:
        return None


def assess_notice_feasibility(
    notice: Notice,
    keyword_terms: tuple[str, ...],
    evidence: list[CompanyEvidence],
    now: datetime | None = None,
) -> FeasibilityAssessment:
    now = now or datetime.now(UTC)
    text = " ".join(filter(None, (notice.title, notice.raw_text, notice.buyer)))
    matched_keywords = tuple(term for term in keyword_terms if matches_any_keyword(text, [term]))
    reasons: list[str] = []
    score = 0.0

    if matched_keywords:
        score += min(45.0, 30.0 + 5.0 * len(matched_keywords))
        reasons.append(f"Khop san pham: {', '.join(matched_keywords[:5])}")
    else:
        reasons.append("Khong thay tu khoa san pham trong du lieu da thu thap")

    matched_evidence: list[str] = []
    for item in evidence:
        terms = tuple(part.strip() for part in (item.keywords or "").replace(";", ",").split(","))
        if item.verified and terms and any(matches_any_keyword(text, [term]) for term in terms):
            matched_evidence.append(item.evidence_code)
    if matched_evidence:
        score += min(30.0, 15.0 + 5.0 * len(matched_evidence))
        reasons.append(f"Co bang chung da xac minh: {', '.join(matched_evidence[:5])}")
    else:
        reasons.append("Chua thay bang chung nang luc da xac minh phu hop")

    deadline = _parse_deadline(notice.closing_at)
    if deadline is None:
        score += 4.0
        reasons.append("Chua doc duoc han nop")
    else:
        days_left = (deadline - now).total_seconds() / 86400
        if days_left <= 0:
            return FeasibilityAssessment(
                notice.id, 0.0, "HET_HAN", matched_keywords, tuple(matched_evidence),
                (*reasons, "Goi da het han"),
            )
        if days_left >= 7:
            score += 15.0
            reasons.append(f"Con {days_left:.0f} ngay chuan bi")
        elif days_left >= 3:
            score += 10.0
            reasons.append(f"Con {days_left:.0f} ngay; can xu ly som")
        else:
            score += 3.0
            reasons.append(f"Chi con {days_left:.1f} ngay")

    completeness = sum(
        bool(value)
        for value in (notice.title, notice.buyer, notice.closing_at, notice.source_url)
    )
    score += completeness * 2.5
    if completeness < 4:
        reasons.append("Thong tin goi chua day du")

    score = round(min(score, 100.0), 1)
    if score >= 70 and matched_keywords and matched_evidence:
        status = "KHA_THI_SO_BO"
    elif score >= 40 and matched_keywords:
        status = "CAN_XEM"
    else:
        status = "THAP"
    return FeasibilityAssessment(
        notice.id, score, status, matched_keywords, tuple(matched_evidence), tuple(reasons)
    )


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
            "title",
            "buyer",
            "closing_at",
            "package_price",
            "currency",
            "matched_keywords",
            "matched_evidence",
            "reasons",
            "source_url",
        ]
    )
    for priority, (notice, assessment) in enumerate(rows, start=1):
        sheet.append(
            [
                priority,
                assessment.status,
                assessment.score,
                notice.title,
                notice.buyer,
                notice.closing_at,
                notice.package_price,
                notice.currency,
                ", ".join(assessment.matched_keywords),
                ", ".join(assessment.matched_evidence),
                " | ".join(assessment.reasons),
                notice.source_url,
            ]
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
    collected = 0
    if settings.contracts_finder:
        for item in expanded:
            result = await collect_contracts_finder(
                service,
                keyword=item.search_terms,
                published_from=datetime.now(UTC).date() - timedelta(days=settings.lookback_days),
                limit=settings.limit_per_keyword,
                only_open=True,
            )
            collected += result.matched
    for source_name in settings.authenticated_sources:
        source = load_source(source_name)
        result = await collect_authenticated_source(
            service, source, keyword=terms, limit=settings.limit_per_keyword
        )
        collected += result.matched

    service.db.create_all()
    with service.db.session() as session:
        evidence = list(session.scalars(select(CompanyEvidence).where(CompanyEvidence.verified)).all())
        notices = list(session.scalars(select(Notice).order_by(Notice.id.desc())).all())
    ranked: list[tuple[Notice, FeasibilityAssessment]] = []
    for notice in notices:
        assessment = assess_notice_feasibility(notice, terms, evidence)
        if assessment.status != "HET_HAN" and assessment.matched_keywords:
            ranked.append((notice, assessment))
    ranked.sort(key=lambda row: row[1].score, reverse=True)
    output = _write_ranked_report(settings.output, ranked)
    return MonitoringSummary(
        collected=collected,
        assessed=len(ranked),
        feasible=sum(item.status == "KHA_THI_SO_BO" for _, item in ranked),
        review=sum(item.status == "CAN_XEM" for _, item in ranked),
        low=sum(item.status == "THAP" for _, item in ranked),
        output=output,
    )


async def monitor_forever(service: CrawlerService, settings: MonitoringConfig) -> None:
    while True:
        try:
            summary = await run_monitoring_cycle(service, settings)
            print(
                f"Quet xong: thu thap={summary.collected}, kha thi so bo={summary.feasible}, "
                f"can xem={summary.review}, thap={summary.low}; bao cao={summary.output}"
            )
        except (OSError, RuntimeError, ValueError) as exc:
            print(f"Luot quet gap loi: {exc}")
        print(f"Luot tiep theo sau {settings.interval_minutes} phut. Nhan Ctrl+C de dung.")
        await asyncio.sleep(settings.interval_minutes * 60)
