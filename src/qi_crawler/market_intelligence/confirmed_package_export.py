"""Derived Excel export of MI-3's current human-confirmed KHMT candidates."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from openpyxl import Workbook

from qi_crawler.excel_safety import safe_excel_row, safe_excel_value

from .candidate_review import CandidateReviewService, ReviewedCandidate
from .khmt_contract import OBSERVED_KHMT_HEADERS, PlanPackage

DEFAULT_CONFIRMED_EXPORT_FILENAME = "CÁC GÓI ĐÃ XÁC NHẬN.xlsx"
BUSINESS_HEADERS = OBSERVED_KHMT_HEADERS
AUDIT_HEADERS = (
    "QUYẾT ĐỊNH REVIEW",
    "NGƯỜI REVIEW",
    "ID SỰ KIỆN REVIEW",
    "THỜI ĐIỂM REVIEW",
    "FILE NGUỒN",
    "SHA-256 NGUỒN",
    "SHEET NGUỒN",
    "DÒNG NGUỒN",
    "MÃ KẾ HOẠCH GỐC",
    "REVISION",
)
SHEET_NAME = "Các gói đã xác nhận"


@dataclass(frozen=True, slots=True)
class ConfirmedPackageExportResult:
    output: Path
    exported_rows: int


def export_confirmed_packages(
    review_service: CandidateReviewService,
    packages: Iterable[PlanPackage],
    *,
    output: Path = Path(DEFAULT_CONFIRMED_EXPORT_FILENAME),
) -> ConfirmedPackageExportResult:
    """Export only MI-3's current latest-state confirmations without DB writes."""

    confirmed = sorted(review_service.current_confirmed(packages), key=_sort_key)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = SHEET_NAME
    sheet.append(BUSINESS_HEADERS + AUDIT_HEADERS)
    for reviewed in confirmed:
        sheet.append(_business_values(reviewed.package) + _audit_values(reviewed))

    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:W{max(sheet.max_row, 1)}"
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(output)
    return ConfirmedPackageExportResult(output=output, exported_rows=len(confirmed))


def _business_values(package: PlanPackage) -> tuple[Any, ...]:
    return tuple(safe_excel_value(package.raw_fields.get(header)) for header in BUSINESS_HEADERS)


def _audit_values(reviewed: ReviewedCandidate) -> tuple[Any, ...]:
    package = reviewed.package
    event = reviewed.event
    batch = package.plan.import_batch
    return tuple(
        safe_excel_row(
            (
                event.decision,
                event.reviewer,
                event.id,
                _utc_isoformat(event.created_at),
                batch.source_filename,
                event.source_sha256,
                event.source_sheet,
                event.source_row,
                event.plan_base_id,
                event.plan_revision,
            )
        )
    )


def _sort_key(reviewed: ReviewedCandidate) -> tuple[str, str, int, str, int]:
    event = reviewed.event
    return (
        event.source_sha256.casefold(),
        event.source_sheet.casefold(),
        event.source_row,
        event.plan_id_raw.casefold(),
        event.id,
    )


def _utc_isoformat(value: datetime) -> str:
    aware = value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
    return aware.isoformat()
