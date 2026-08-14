from __future__ import annotations

from hashlib import sha256

import pytest

from qi_crawler import __version__
from qi_crawler.db import CURRENT_SCHEMA_REVISION, Database
from qi_crawler.ground_truth import GroundTruthReviewError, GroundTruthReviewService
from qi_crawler.models import (
    Document,
    DocumentEvidence,
    DocumentExtraction,
    GroundTruthReview,
    Notice,
)


@pytest.fixture
def review_context(tmp_path):
    database = Database(f"sqlite:///{tmp_path / 'ground-truth.db'}")
    database.require_current_schema()
    source_url = "https://example.test/tender/IB-001"
    with database.session() as session:
        notice = Notice(
            source_url=source_url,
            url_hash=sha256(source_url.encode()).hexdigest(),
            notice_code="IB-001",
            source_name="test",
            source_notice_id="IB-001",
            title="Tender IB-001",
        )
        session.add(notice)
        session.flush()
        document = Document(
            tender_id=notice.id,
            document_source="manual_upload",
            document_type="E_HSMT",
            original_filename="hsmt.pdf",
            stored_path=str(tmp_path / "documents" / "hsmt.pdf"),
            mime_type="application/pdf",
            file_size=12,
            sha256="a" * 64,
            version=1,
            status="VERIFIED_LINKED",
        )
        session.add(document)
        session.flush()
        extraction = DocumentExtraction(
            document_id=document.id,
            extractor_version="native-v1",
            status="NATIVE_OK",
            metadata_json='{"status": "NATIVE_OK"}',
        )
        session.add(extraction)
        session.flush()
        evidence = DocumentEvidence(
            extraction_id=extraction.id,
            ordinal=1,
            source_locator="page:2",
            page_number=2,
            content_type="TEXT",
            text="Predicted requirement",
            metadata_json='{"flags": ["NATIVE_OK"]}',
        )
        session.add(evidence)
        session.flush()
        return database, extraction.id, evidence.id


def test_correct_review_appends_lineage_without_mutating_prediction(review_context) -> None:
    database, extraction_id, evidence_id = review_context
    service = GroundTruthReviewService(database)
    before = _prediction_snapshot(database, extraction_id, evidence_id)

    recorded = service.record_review(
        extraction_id=extraction_id,
        evidence_id=evidence_id,
        target_type="TEXT",
        predicted_value="Predicted requirement",
        predicted_status="NATIVE_OK",
        human_verdict="CORRECT",
        reviewer="solo.pilot",
    )

    with database.session() as session:
        review = session.get(GroundTruthReview, recorded.id)
    assert review is not None
    assert review.review_status == "SOLO_REVIEWED"
    assert review.error_type is None
    assert review.corrected_value is None
    assert review.crawler_version == __version__
    assert review.extractor_version == "native-v1"
    assert review.schema_version == CURRENT_SCHEMA_REVISION
    assert _prediction_snapshot(database, extraction_id, evidence_id) == before


def test_incorrect_review_requires_error_and_stores_correction(review_context) -> None:
    database, extraction_id, evidence_id = review_context
    service = GroundTruthReviewService(database)

    with pytest.raises(GroundTruthReviewError, match="requires error_type"):
        service.record_review(
            extraction_id=extraction_id,
            evidence_id=evidence_id,
            target_type="TEXT",
            human_verdict="INCORRECT",
            reviewer="solo.pilot",
        )

    recorded = service.record_review(
        extraction_id=extraction_id,
        evidence_id=evidence_id,
        target_type="TEXT",
        predicted_value="Predicted requirement",
        human_verdict="INCORRECT",
        corrected_value="Corrected requirement",
        corrected_locator="page:3",
        error_type="WRONG_PAGE",
        reviewer="solo.pilot",
        rule_version="manual-v1",
    )
    with database.session() as session:
        review = session.get(GroundTruthReview, recorded.id)
    assert review is not None
    assert review.error_type == "WRONG_PAGE"
    assert review.corrected_value == "Corrected requirement"
    assert review.rule_version == "manual-v1"


def test_false_safe_is_stored_and_history_is_append_only(review_context) -> None:
    database, extraction_id, evidence_id = review_context
    service = GroundTruthReviewService(database)
    first = service.record_review(
        extraction_id=extraction_id,
        evidence_id=evidence_id,
        target_type="PAGE_STATUS",
        human_verdict="INCORRECT",
        error_type="FALSE_SAFE",
        reviewer="solo.pilot",
    )
    second = service.record_review(
        extraction_id=extraction_id,
        evidence_id=evidence_id,
        target_type="PAGE_STATUS",
        human_verdict="CORRECT",
        reviewer="checker.pilot",
        review_role="CHECKER",
        review_status="VERIFIED_GROUND_TRUTH",
    )

    history = service.list_reviews_for_extraction(extraction_id)
    assert [review.id for review in history] == [first.id, second.id]
    assert history[0].error_type == "FALSE_SAFE"
    assert history[0].review_status == "SOLO_REVIEWED"
    assert history[1].review_status == "VERIFIED_GROUND_TRUTH"


def test_verified_state_requires_explicit_checker_review(review_context) -> None:
    database, extraction_id, evidence_id = review_context
    service = GroundTruthReviewService(database)

    with pytest.raises(GroundTruthReviewError, match="requires CHECKER"):
        service.record_review(
            extraction_id=extraction_id,
            evidence_id=evidence_id,
            target_type="TEXT",
            human_verdict="CORRECT",
            reviewer="solo.pilot",
            review_status="VERIFIED_GROUND_TRUTH",
        )


def test_invalid_extraction_or_evidence_reference_is_rejected_safely(review_context) -> None:
    database, extraction_id, evidence_id = review_context
    service = GroundTruthReviewService(database)

    with pytest.raises(GroundTruthReviewError, match="Unknown extraction_id"):
        service.record_review(
            extraction_id=999,
            evidence_id=None,
            target_type="TEXT",
            human_verdict="CORRECT",
            reviewer="solo.pilot",
        )
    with pytest.raises(GroundTruthReviewError, match="does not belong"):
        service.record_review(
            extraction_id=extraction_id,
            evidence_id=evidence_id + 999,
            target_type="TEXT",
            human_verdict="CORRECT",
            reviewer="solo.pilot",
        )


def _prediction_snapshot(database: Database, extraction_id: int, evidence_id: int):
    with database.session() as session:
        extraction = session.get(DocumentExtraction, extraction_id)
        evidence = session.get(DocumentEvidence, evidence_id)
    assert extraction is not None
    assert evidence is not None
    return (
        extraction.status,
        extraction.metadata_json,
        evidence.text,
        evidence.metadata_json,
    )
