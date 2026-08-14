"""Append-only human review capture for native extraction evidence."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from . import __version__
from .db import CURRENT_SCHEMA_REVISION, Database
from .models import DocumentEvidence, DocumentExtraction, GroundTruthReview

HUMAN_VERDICTS = frozenset({"CORRECT", "INCORRECT"})
REVIEW_ROLES = frozenset({"SOLO", "MAKER", "CHECKER"})
REVIEW_STATUSES = frozenset(
    {"SOLO_REVIEWED", "MAKER_REVIEWED", "CHECKER_REVIEWED", "VERIFIED_GROUND_TRUTH"}
)
ERROR_TYPES = frozenset(
    {
        "WRONG_PAGE",
        "WRONG_TABLE",
        "WRONG_SECTION",
        "MISSED_TEXT",
        "WRONG_TEXT",
        "WRONG_ENCODING_STATUS",
        "WRONG_OCR_STATUS",
        "VERSION_ERROR",
        "IDENTITY_ERROR",
        "FALSE_SAFE",
    }
)
_DEFAULT_REVIEW_STATUS = {
    "SOLO": "SOLO_REVIEWED",
    "MAKER": "MAKER_REVIEWED",
    "CHECKER": "CHECKER_REVIEWED",
}


class GroundTruthReviewError(ValueError):
    """A requested human review is incomplete or has an invalid lineage."""


@dataclass(frozen=True)
class RecordedReview:
    id: int
    extraction_id: int
    evidence_id: int | None
    review_status: str


class GroundTruthReviewService:
    """Store review events without changing predictions, evidence, or history."""

    def __init__(self, database: Database) -> None:
        self.database = database
        self.database.require_current_schema()

    def record_review(
        self,
        *,
        extraction_id: int,
        evidence_id: int | None,
        target_type: str,
        human_verdict: str,
        reviewer: str,
        predicted_value: str | None = None,
        predicted_status: str | None = None,
        corrected_value: str | None = None,
        corrected_locator: str | None = None,
        error_type: str | None = None,
        note: str | None = None,
        review_role: str = "SOLO",
        review_status: str | None = None,
        rule_version: str | None = None,
    ) -> RecordedReview:
        verdict = _required_choice("human_verdict", human_verdict, HUMAN_VERDICTS)
        role = _required_choice("review_role", review_role, REVIEW_ROLES)
        target = _required_text("target_type", target_type)
        reviewed_by = _required_text("reviewer", reviewer)
        normalized_error = _optional_choice("error_type", error_type, ERROR_TYPES)
        if verdict == "INCORRECT" and normalized_error is None:
            raise GroundTruthReviewError("INCORRECT requires error_type.")
        if verdict == "CORRECT" and (
            normalized_error is not None or corrected_value is not None or corrected_locator is not None
        ):
            raise GroundTruthReviewError("CORRECT reviews must not contain corrections or error_type.")

        status = review_status or _DEFAULT_REVIEW_STATUS[role]
        status = _required_choice("review_status", status, REVIEW_STATUSES)
        if status == "VERIFIED_GROUND_TRUTH" and role != "CHECKER":
            raise GroundTruthReviewError("VERIFIED_GROUND_TRUTH requires CHECKER review_role.")
        if status != "VERIFIED_GROUND_TRUTH" and status != _DEFAULT_REVIEW_STATUS[role]:
            raise GroundTruthReviewError("review_status does not match review_role.")

        with self.database.session() as session:
            extraction = session.get(DocumentExtraction, extraction_id)
            if extraction is None:
                raise GroundTruthReviewError("Unknown extraction_id.")
            if evidence_id is not None:
                evidence = session.get(DocumentEvidence, evidence_id)
                if evidence is None or evidence.extraction_id != extraction_id:
                    raise GroundTruthReviewError("evidence_id does not belong to extraction_id.")
            review = GroundTruthReview(
                extraction_id=extraction_id,
                evidence_id=evidence_id,
                target_type=target,
                predicted_value=_optional_text(predicted_value),
                predicted_status=_optional_text(predicted_status),
                human_verdict=verdict,
                corrected_value=_optional_text(corrected_value),
                corrected_locator=_optional_text(corrected_locator),
                error_type=normalized_error,
                note=_optional_text(note),
                review_role=role,
                review_status=status,
                reviewer=reviewed_by,
                crawler_version=__version__,
                extractor_version=extraction.extractor_version,
                rule_version=_optional_text(rule_version),
                schema_version=CURRENT_SCHEMA_REVISION,
            )
            session.add(review)
            session.flush()
            return RecordedReview(
                id=review.id,
                extraction_id=review.extraction_id,
                evidence_id=review.evidence_id,
                review_status=review.review_status,
            )

    def list_reviews_for_extraction(self, extraction_id: int) -> list[GroundTruthReview]:
        with self.database.session() as session:
            return list(
                session.scalars(
                    select(GroundTruthReview)
                    .where(GroundTruthReview.extraction_id == extraction_id)
                    .order_by(GroundTruthReview.reviewed_at, GroundTruthReview.id)
                )
            )


def _required_choice(name: str, value: str, allowed: frozenset[str]) -> str:
    normalized = _required_text(name, value).upper()
    if normalized not in allowed:
        raise GroundTruthReviewError(f"Invalid {name}.")
    return normalized


def _optional_choice(
    name: str, value: str | None, allowed: frozenset[str]
) -> str | None:
    if value is None or not value.strip():
        return None
    return _required_choice(name, value, allowed)


def _required_text(name: str, value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise GroundTruthReviewError(f"{name} is required.")
    return normalized


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip() or None
