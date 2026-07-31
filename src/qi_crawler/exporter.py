from __future__ import annotations

import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from .db import Database
from .models import Notice

HEADERS = [
    "id",
    "notice_code",
    "title",
    "buyer",
    "investor",
    "package_price",
    "currency",
    "published_at",
    "closing_at",
    "source_url",
    "source_kind",
    "data_quality_status",
    "attachment_count",
    "attachments_downloaded",
    "attachments_failed",
    "first_seen_at",
    "last_seen_at",
]


def _rows(db: Database) -> list[list[object]]:
    with db.session() as session:
        notices = session.scalars(
            select(Notice).options(selectinload(Notice.attachments)).order_by(Notice.id.desc())
        ).all()
        return [
            [
                notice.id,
                notice.notice_code,
                notice.title,
                notice.buyer,
                notice.investor,
                notice.package_price,
                notice.currency,
                notice.published_at,
                notice.closing_at,
                notice.source_url,
                notice.source_kind,
                notice.data_quality_status,
                len(notice.attachments),
                sum(item.download_status == "downloaded" for item in notice.attachments),
                sum(item.download_status in {"failed", "manual_review"} for item in notice.attachments),
                notice.first_seen_at.isoformat() if notice.first_seen_at else None,
                notice.last_seen_at.isoformat() if notice.last_seen_at else None,
            ]
            for notice in notices
        ]


def export_csv(db: Database, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADERS)
        writer.writerows(_rows(db))
    return output


def export_xlsx(db: Database, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Notices"
    sheet.append(HEADERS)
    for row in _rows(db):
        sheet.append(row)
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for column in sheet.columns:
        max_len = max(len(str(cell.value or "")) for cell in column)
        sheet.column_dimensions[column[0].column_letter].width = min(max(max_len + 2, 12), 60)
    workbook.save(output)
    return output
