from __future__ import annotations

import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from .db import Database
from .excel_safety import safe_excel_row
from .models import InventoryItem, Notice
from .stock import StockCheck, check_stock

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
    "location",
    "sector",
    "selection_method",
    "notice_version",
    "source_url",
    "source_kind",
    "data_quality_status",
    "requested_item_count",
    "requested_quantity_details",
    "response_table",
    "attachment_count",
    "attachments_downloaded",
    "attachments_failed",
    "first_seen_at",
    "last_seen_at",
]

HEADER_FILL = PatternFill("solid", fgColor="17365D")
HEADER_FONT = Font(bold=True, color="FFFFFF")
STATUS_FILLS = {
    "MEETS_STOCK": PatternFill("solid", fgColor="C6EFCE"),
    "STOCK_SHORTAGE": PatternFill("solid", fgColor="FFC7CE"),
    "REVIEW_REQUIRED_QUANTITY": PatternFill("solid", fgColor="FFEB9C"),
    "REVIEW_UNIT_MISMATCH": PatternFill("solid", fgColor="FFEB9C"),
    "NOT_IN_VERIFIED_STOCK": PatternFill("solid", fgColor="FFC7CE"),
}


def _quantity_details(notice: Notice) -> str:
    if not notice.tender_items:
        return "NOT_AVAILABLE"
    return "; ".join(
        f"{item.product_name}: "
        f"{item.quantity if item.quantity is not None else 'REVIEW'}"
        f" {item.unit or ''}".rstrip()
        for item in notice.tender_items
    )


def _checks(notice: Notice, inventory: list[InventoryItem]) -> list[StockCheck]:
    return [check_stock(item, inventory) for item in notice.tender_items]


def _response_table(checks: list[StockCheck]) -> str:
    if not checks:
        return "NO_QUANTITY_DATA"
    counts: dict[str, int] = {}
    for result in checks:
        counts[result.status] = counts.get(result.status, 0) + 1
    return "; ".join(f"{status}={counts[status]}" for status in sorted(counts))


def _style_sheet(sheet, *, status_column: int | None = None) -> None:
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    sheet.sheet_view.showGridLines = False
    for cell in sheet[1]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")
    for column in sheet.columns:
        max_len = max(len(str(cell.value or "")) for cell in column)
        sheet.column_dimensions[column[0].column_letter].width = min(max(max_len + 2, 12), 60)
    if status_column:
        for row in range(2, sheet.max_row + 1):
            cell = sheet.cell(row, status_column)
            cell.fill = STATUS_FILLS.get(str(cell.value), PatternFill())


def _data(db: Database) -> tuple[list[Notice], list[InventoryItem]]:
    with db.session() as session:
        notices = session.scalars(
            select(Notice)
            .options(selectinload(Notice.attachments), selectinload(Notice.tender_items))
            .order_by(Notice.id.desc())
        ).all()
        inventory = session.scalars(select(InventoryItem).order_by(InventoryItem.sku)).all()
        session.expunge_all()
        return list(notices), list(inventory)


def _rows(db: Database) -> list[list[object]]:
    notices, inventory = _data(db)
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
                notice.location,
                notice.sector,
                notice.selection_method,
                notice.notice_version,
                notice.source_url,
                notice.source_kind,
                notice.data_quality_status,
                len(notice.tender_items),
                _quantity_details(notice),
                _response_table(_checks(notice, inventory)),
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
        writer.writerows(safe_excel_row(row) for row in _rows(db))
    return output


def export_xlsx(db: Database, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Notices"
    notices, inventory = _data(db)
    sheet.append(HEADERS)
    for notice in notices:
        checks = _checks(notice, inventory)
        row = [
            notice.id,
            notice.notice_code,
            notice.title,
            notice.buyer,
            notice.investor,
            notice.package_price,
            notice.currency,
            notice.published_at,
            notice.closing_at,
            notice.location,
            notice.sector,
            notice.selection_method,
            notice.notice_version,
            notice.source_url,
            notice.source_kind,
            notice.data_quality_status,
            len(notice.tender_items),
            _quantity_details(notice),
            _response_table(checks),
            len(notice.attachments),
            sum(item.download_status == "downloaded" for item in notice.attachments),
            sum(
                item.download_status in {"failed", "manual_review"}
                for item in notice.attachments
            ),
            notice.first_seen_at.isoformat() if notice.first_seen_at else None,
            notice.last_seen_at.isoformat() if notice.last_seen_at else None,
        ]
        sheet.append(safe_excel_row(row))

    item_sheet = workbook.create_sheet("Response Table")
    item_headers = [
        "notice_id",
        "notice_code",
        "requested_product",
        "specification",
        "required_quantity",
        "unit",
        "matched_sku",
        "available_quantity",
        "shortage_quantity",
        "response_status",
        "match_confidence",
        "quantity_source",
        "source_location",
        "extraction_confidence",
        "human_review_required",
        "note",
        "source_url",
    ]
    item_sheet.append(item_headers)
    for notice in notices:
        checks = {result.tender_item_id: result for result in _checks(notice, inventory)}
        for item in notice.tender_items:
            result = checks[item.id]
            item_sheet.append(
                safe_excel_row([
                    notice.id,
                    notice.notice_code,
                    item.product_name,
                    item.specification,
                    result.required_quantity,
                    item.unit,
                    result.inventory_sku,
                    result.available_quantity,
                    result.shortage_quantity,
                    result.status,
                    result.match_confidence,
                    item.source_document,
                    item.source_location,
                    item.extraction_confidence,
                    item.needs_human_review,
                    result.note,
                    notice.source_url,
                ])
            )

    inventory_sheet = workbook.create_sheet("QI Inventory")
    inventory_sheet.append(
        [
            "sku",
            "product_name",
            "aliases",
            "quantity_available",
            "unit",
            "warehouse",
            "verified",
            "updated_at",
            "source_file",
        ]
    )
    for item in inventory:
        inventory_sheet.append(
            safe_excel_row([
                item.sku,
                item.product_name,
                item.aliases,
                item.quantity_available,
                item.unit,
                item.warehouse,
                item.verified,
                item.updated_at.isoformat() if item.updated_at else None,
                item.source_file,
            ])
        )

    _style_sheet(sheet)
    _style_sheet(item_sheet, status_column=10)
    _style_sheet(inventory_sheet)
    workbook.save(output)
    return output
