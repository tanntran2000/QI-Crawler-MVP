"""Append-only human source-type corrections for Excel intake."""

from __future__ import annotations

import json
from dataclasses import dataclass

from qi_crawler.db import Database
from qi_crawler.models import SourceTypeReviewEvent

from .source_detection import SourceType, SourceTypeDetection


class SourceTypeReviewError(ValueError):
    """Raised when a source-type decision lacks required human authority."""


@dataclass(frozen=True, slots=True)
class SourceTypeReviewService:
    database: Database

    def __post_init__(self) -> None:
        self.database.require_current_schema()

    def record_decision(
        self,
        detection: SourceTypeDetection,
        *,
        final_type: SourceType | str,
        reviewer: str | None = None,
        note: str | None = None,
    ) -> SourceTypeReviewEvent:
        selected = SourceType(final_type)
        if selected is SourceType.UNKNOWN:
            raise SourceTypeReviewError("Không thể lưu loại nguồn UNKNOWN.")
        normalized_reviewer = reviewer.strip() if reviewer and reviewer.strip() else None
        authority = "HUMAN" if detection.requires_human or normalized_reviewer else "AUTO"
        if authority == "HUMAN" and not normalized_reviewer:
            raise SourceTypeReviewError("Tên người xác nhận nguồn là bắt buộc.")
        safe_reviewer = normalized_reviewer or "SYSTEM"
        normalized_note = note.strip() if note and note.strip() else None
        event = SourceTypeReviewEvent(
            source_sha256=detection.source_sha256,
            original_filename=detection.original_filename,
            filename_type=detection.filename_type.value,
            content_type=detection.content_type.value,
            identity_namespace=detection.identity_namespace,
            auto_type=detection.auto_type.value,
            final_type=selected.value,
            authority=authority,
            reviewer=safe_reviewer,
            note=normalized_note,
            identity_values_json=json.dumps(detection.identity_values, ensure_ascii=False),
            identity_raw_values_json=json.dumps(
                detection.identity_raw_values,
                ensure_ascii=False,
            ),
            evidence_json=json.dumps(detection.evidence, ensure_ascii=False),
        )
        with self.database.session() as session:
            session.add(event)
            session.flush()
            return event

    def list_history(self, source_sha256: str) -> tuple[SourceTypeReviewEvent, ...]:
        from sqlalchemy import select

        with self.database.session() as session:
            return tuple(
                session.scalars(
                    select(SourceTypeReviewEvent)
                    .where(SourceTypeReviewEvent.source_sha256 == source_sha256)
                    .order_by(SourceTypeReviewEvent.id.asc())
                )
            )
