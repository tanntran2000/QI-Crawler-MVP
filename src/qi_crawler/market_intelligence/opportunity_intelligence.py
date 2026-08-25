"""Source-neutral Opportunity Intelligence application facade.

This module composes the existing source importers, radar projections, search
authority, and Human Review service.  It owns no persistence or delivery
logic and deliberately keeps KHMT (PL) and TBMT (IB) routing explicit.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .khmt_importer import import_khmt_workbook
from .opportunity_contract import OpportunitySourceType
from .opportunity_radar import (
    OpportunityRadarItem,
    radar_item_from_opportunity_candidate,
    radar_item_from_plan_package,
)
from .opportunity_review import (
    OpportunityReviewDecision,
    OpportunityReviewRecord,
    OpportunityReviewService,
)
from .search import (
    TargetedOpportunitySearchResult,
    TargetedSearchRequest,
    search_opportunities,
)
from .tbmt_importer import import_tbmt_workbook


class OpportunityIntelligenceError(ValueError):
    """Raised when the source-neutral facade contract cannot be satisfied."""


@dataclass(frozen=True, slots=True)
class OpportunityImportIssue:
    """Normalized issue shape shared by KHMT and TBMT workbook adapters."""

    source_type: OpportunitySourceType
    code: str
    message: str
    source_row: int | None = None
    source_field: str | None = None

    @property
    def field(self) -> str | None:
        """Compatibility alias for callers that use the shorter field name."""

        return self.source_field


@dataclass(frozen=True, slots=True)
class OpportunityLoadResult:
    """One immutable, source-neutral workbook observation."""

    source_type: OpportunitySourceType
    source_path: Path
    source_filename: str
    source_sha256: str
    sheet: str
    schema_version: str
    source_row_count: int
    items: tuple[OpportunityRadarItem, ...]
    issues: tuple[OpportunityImportIssue, ...]
    headers: tuple[str, ...]


class OpportunityIntelligenceService:
    """Application facade for source routing, search, and explicit review."""

    def __init__(self, review_service: OpportunityReviewService) -> None:
        self.review_service = review_service

    def load_workbook(
        self,
        path: str | Path,
        source_type: OpportunitySourceType | str,
        *,
        sheet_name: str | None = None,
        imported_at: datetime | None = None,
    ) -> OpportunityLoadResult:
        """Route one workbook through its declared source adapter."""

        source = _source_type(source_type)
        source_path = Path(path).resolve()
        if source is OpportunitySourceType.KHMT:
            imported = import_khmt_workbook(
                source_path,
                sheet_name=sheet_name,
                imported_at=imported_at,
            )
            items = tuple(radar_item_from_plan_package(package) for package in imported.packages)
            issues = tuple(_normalize_issue(source, issue) for issue in imported.issues)
        else:
            imported = import_tbmt_workbook(
                source_path,
                sheet_name=sheet_name,
                imported_at=imported_at,
            )
            items = tuple(
                radar_item_from_opportunity_candidate(candidate)
                for candidate in imported.candidates
            )
            issues = tuple(_normalize_issue(source, issue) for issue in imported.issues)
        batch = imported.batch
        return OpportunityLoadResult(
            source_type=source,
            source_path=source_path,
            source_filename=batch.source_filename,
            source_sha256=batch.source_sha256,
            sheet=batch.sheet,
            schema_version=batch.schema_version,
            source_row_count=imported.source_row_count,
            items=items,
            issues=issues,
            headers=tuple(imported.headers),
        )

    def import_workbook(
        self,
        path: str | Path,
        source_type: OpportunitySourceType | str,
        *,
        sheet_name: str | None = None,
        imported_at: datetime | None = None,
    ) -> OpportunityLoadResult:
        """Explicit alias for callers that describe loading as an import."""

        return self.load_workbook(
            path,
            source_type,
            sheet_name=sheet_name,
            imported_at=imported_at,
        )

    def load(
        self,
        path: str | Path,
        source_type: OpportunitySourceType | str,
        *,
        sheet_name: str | None = None,
        imported_at: datetime | None = None,
    ) -> OpportunityLoadResult:
        """Short alias for application callers."""

        return self.load_workbook(
            path,
            source_type,
            sheet_name=sheet_name,
            imported_at=imported_at,
        )

    @staticmethod
    def search_opportunities(
        items: tuple[OpportunityRadarItem, ...] | list[OpportunityRadarItem],
        request: TargetedSearchRequest,
    ) -> TargetedOpportunitySearchResult:
        """Delegate matching to the existing source-neutral search authority."""

        return search_opportunities(items, request)

    def current_review(self, item: OpportunityRadarItem) -> OpportunityReviewRecord | None:
        """Read the latest explicit review state for one source observation."""

        return self.review_service.current_event(item)

    def current_event(self, item: OpportunityRadarItem) -> OpportunityReviewRecord | None:
        """Alias matching the underlying review service terminology."""

        return self.current_review(item)

    def record_review(
        self,
        item: OpportunityRadarItem,
        *,
        decision: OpportunityReviewDecision | str,
        reviewer: str,
        note: str | None = None,
    ) -> OpportunityReviewRecord:
        """Record one explicit human decision through the review authority."""

        return self.review_service.record_decision(
            item,
            decision=decision,
            reviewer=reviewer,
            note=note,
        )

    def record_decision(
        self,
        item: OpportunityRadarItem,
        *,
        decision: OpportunityReviewDecision | str,
        reviewer: str,
        note: str | None = None,
    ) -> OpportunityReviewRecord:
        """Alias for callers using the review service's method name."""

        return self.record_review(item, decision=decision, reviewer=reviewer, note=note)

    def current_confirmed(
        self, items: tuple[OpportunityRadarItem, ...] | list[OpportunityRadarItem]
    ) -> tuple[OpportunityReviewRecord, ...]:
        """Return only the latest explicitly CONFIRMED observations."""

        return self.review_service.current_confirmed(items)


def _source_type(value: OpportunitySourceType | str) -> OpportunitySourceType:
    try:
        return OpportunitySourceType(value)
    except (TypeError, ValueError) as exc:
        raise OpportunityIntelligenceError(
            "source_type must be explicitly KHMT or TBMT"
        ) from exc


def _normalize_issue(
    source_type: OpportunitySourceType,
    issue: Any,
) -> OpportunityImportIssue:
    code = getattr(issue, "code", "UNKNOWN")
    code_value = getattr(code, "value", code)
    return OpportunityImportIssue(
        source_type=source_type,
        code=str(code_value),
        message=str(getattr(issue, "message", issue)),
        source_row=getattr(issue, "source_row", None),
        source_field=getattr(issue, "source_field", None),
    )


__all__ = [
    "OpportunityImportIssue",
    "OpportunityIntelligenceError",
    "OpportunityIntelligenceService",
    "OpportunityLoadResult",
]
