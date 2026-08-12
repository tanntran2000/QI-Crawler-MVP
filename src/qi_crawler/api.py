from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from . import __version__
from .config import load_config
from .db import Database
from .models import (
    Attachment,
    BidPrediction,
    BidRequirement,
    ComplianceAssessment,
    CrawlRun,
    Notice,
)

config = load_config()
db = Database(config.storage.database_url)
db.require_current_schema()
app = FastAPI(title="QI Crawler API", version=__version__)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/notices")
def list_notices(
    q: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict:
    with db.session() as session:
        statement = select(Notice).order_by(Notice.id.desc())
        if q:
            pattern = f"%{q}%"
            statement = statement.where(
                Notice.title.ilike(pattern)
                | Notice.notice_code.ilike(pattern)
                | Notice.source_notice_id.ilike(pattern)
                | Notice.source_name.ilike(pattern)
                | Notice.buyer.ilike(pattern)
            )
        items = session.scalars(statement.offset(offset).limit(limit)).all()
        return {
            "items": [
                {
                    "id": item.id,
                    "notice_code": item.notice_code,
                    "source_notice_id": item.source_notice_id,
                    "source_name": item.source_name,
                    "title": item.title,
                    "buyer": item.buyer,
                    "investor": item.investor,
                    "package_price": item.package_price,
                    "currency": item.currency,
                    "published_at": item.published_at,
                    "closing_at": item.closing_at,
                    "location": item.location,
                    "sector": item.sector,
                    "selection_method": item.selection_method,
                    "notice_version": item.notice_version,
                    "source_url": item.source_url,
                    "source_kind": item.source_kind,
                    "data_quality_status": item.data_quality_status,
                }
                for item in items
            ],
            "limit": limit,
            "offset": offset,
        }


@app.get("/notices/{notice_id}")
def get_notice(notice_id: int) -> dict:
    with db.session() as session:
        notice = session.scalar(
            select(Notice)
            .options(selectinload(Notice.attachments))
            .where(Notice.id == notice_id)
        )
        if not notice:
            raise HTTPException(status_code=404, detail="Notice not found")
        return {
            "id": notice.id,
            "notice_code": notice.notice_code,
            "source_notice_id": notice.source_notice_id,
            "source_name": notice.source_name,
            "title": notice.title,
            "buyer": notice.buyer,
            "investor": notice.investor,
            "package_price": notice.package_price,
            "currency": notice.currency,
            "published_at": notice.published_at,
            "closing_at": notice.closing_at,
            "location": notice.location,
            "sector": notice.sector,
            "selection_method": notice.selection_method,
            "notice_version": notice.notice_version,
            "source_url": notice.source_url,
            "source_kind": notice.source_kind,
            "data_quality_status": notice.data_quality_status,
            "attachments": [
                {
                    "id": item.id,
                    "source_url": item.source_url,
                    "file_name": item.file_name,
                    "local_path": item.local_path,
                    "sha256": item.sha256,
                    "size_bytes": item.size_bytes,
                    "download_status": item.download_status,
                    "download_method": item.download_method,
                    "download_attempts": item.download_attempts,
                    "download_error": item.download_error,
                }
                for item in notice.attachments
            ],
        }


@app.get("/crawl-runs")
def list_crawl_runs(limit: int = Query(default=50, ge=1, le=500)) -> list[dict]:
    with db.session() as session:
        runs = session.scalars(select(CrawlRun).order_by(CrawlRun.id.desc()).limit(limit)).all()
        return [
            {
                "id": run.id,
                "source_name": run.source_name,
                "started_at": run.started_at,
                "finished_at": run.finished_at,
                "status": run.status,
                "records_found": run.records_found,
                "records_inserted": run.records_inserted,
                "records_updated": run.records_updated,
                "records_failed": run.records_failed,
                "error_message": run.error_message,
            }
            for run in runs
        ]


@app.get("/stats")
def stats() -> dict[str, int]:
    with db.session() as session:
        notices = session.scalar(select(func.count()).select_from(Notice)) or 0
        attachments = session.scalar(select(func.count()).select_from(Attachment)) or 0
        downloaded = (
            session.scalar(
                select(func.count())
                .select_from(Attachment)
                .where(Attachment.download_status == "downloaded")
            )
            or 0
        )
        failed = (
            session.scalar(
                select(func.count())
                .select_from(Attachment)
                .where(Attachment.download_status.in_(["failed", "manual_review"]))
            )
            or 0
        )
        return {
            "notices": notices,
            "attachments": attachments,
            "attachments_downloaded": downloaded,
            "attachments_failed": failed,
        }


@app.get("/bid-compliance", include_in_schema=False)
def bid_compliance(
    notice_id: int | None = None,
    status: str | None = Query(default=None, pattern="^(covered|partial|gap)$"),
) -> list[dict]:
    with db.session() as session:
        statement = (
            select(ComplianceAssessment, BidRequirement)
            .join(BidRequirement, BidRequirement.id == ComplianceAssessment.requirement_id)
            .order_by(BidRequirement.id.asc())
        )
        if notice_id is not None:
            statement = statement.where(BidRequirement.notice_id == notice_id)
        if status:
            statement = statement.where(ComplianceAssessment.status == status)
        rows = session.execute(statement).all()
        return [
            {
                "requirement_id": requirement.id,
                "requirement_code": requirement.requirement_code,
                "category": requirement.category,
                "source_text": requirement.source_text,
                "mandatory": requirement.mandatory,
                "requirement_type": requirement.requirement_type,
                "source_reference": requirement.source_reference,
                "status": assessment.status,
                "score": assessment.score,
                "evidence_id": assessment.evidence_id,
                "matched_keywords": assessment.matched_keywords,
                "explanation": assessment.explanation,
                "requires_human_confirmation": assessment.requires_human_confirmation,
                "variance_type": assessment.variance_type,
                "variance_impact": assessment.variance_impact,
                "reviewer_decision": assessment.reviewer_decision,
                "confirmed_by": assessment.confirmed_by,
                "confirmed_at": assessment.confirmed_at,
            }
            for assessment, requirement in rows
        ]


@app.get("/bid-predictions", include_in_schema=False)
def bid_predictions(notice_id: int | None = None, limit: int = Query(default=20, ge=1, le=200)) -> list[dict]:
    with db.session() as session:
        statement = select(BidPrediction).order_by(BidPrediction.id.desc()).limit(limit)
        if notice_id is not None:
            statement = statement.where(BidPrediction.notice_id == notice_id)
        items = session.scalars(statement).all()
        return [
            {
                "id": item.id,
                "notice_id": item.notice_id,
                "model_version": item.model_version,
                "readiness_score": item.readiness_score,
                "estimated_win_percent": item.estimated_win_percent,
                "confidence_percent": item.confidence_percent,
                "gate_status": item.gate_status,
                "mandatory_coverage_percent": item.mandatory_coverage_percent,
                "evidence_coverage_percent": item.evidence_coverage_percent,
                "risk_factors": item.risk_factors,
                "assumptions": item.assumptions,
                "created_at": item.created_at,
            }
            for item in items
        ]
