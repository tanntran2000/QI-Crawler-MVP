from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from .config import load_config
from .db import Database
from .models import Attachment, CrawlRun, Notice

config = load_config()
db = Database(config.storage.database_url)
db.create_all()
app = FastAPI(title="EGP Crawler API", version="0.2.0")


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
                | Notice.buyer.ilike(pattern)
            )
        items = session.scalars(statement.offset(offset).limit(limit)).all()
        return {
            "items": [
                {
                    "id": item.id,
                    "notice_code": item.notice_code,
                    "title": item.title,
                    "buyer": item.buyer,
                    "investor": item.investor,
                    "package_price": item.package_price,
                    "currency": item.currency,
                    "published_at": item.published_at,
                    "closing_at": item.closing_at,
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
            "title": notice.title,
            "buyer": notice.buyer,
            "investor": notice.investor,
            "package_price": notice.package_price,
            "currency": notice.currency,
            "published_at": notice.published_at,
            "closing_at": notice.closing_at,
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
