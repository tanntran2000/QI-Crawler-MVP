from datetime import UTC, datetime, timedelta

from qi_crawler.models import CompanyEvidence, Notice
from qi_crawler.monitoring import assess_notice_feasibility

NOW = datetime(2026, 7, 31, tzinfo=UTC)


def _notice(deadline: datetime) -> Notice:
    return Notice(
        id=1,
        source_url="https://example.test/tender/1",
        url_hash="a" * 64,
        title="Supply of outdoor network cable and network accessories",
        raw_text="The buyer requires outdoor LAN cable for a network project.",
        buyer="Example Buyer",
        closing_at=deadline.isoformat(),
    )


def test_verified_evidence_is_required_for_preliminary_feasible_status() -> None:
    notice = _notice(NOW + timedelta(days=14))
    evidence = CompanyEvidence(
        evidence_code="EV-NET-01",
        title="Nang luc cung cap cap mang",
        keywords="network cable, LAN cable",
        verified=True,
    )

    assessment = assess_notice_feasibility(
        notice,
        ("cap mang", "network cable", "LAN cable"),
        [evidence],
        now=NOW,
    )

    assert assessment.status == "KHA_THI_SO_BO"
    assert assessment.score >= 70
    assert assessment.matched_evidence == ("EV-NET-01",)


def test_relevant_notice_without_verified_evidence_needs_review() -> None:
    assessment = assess_notice_feasibility(
        _notice(NOW + timedelta(days=14)),
        ("network cable",),
        [],
        now=NOW,
    )

    assert assessment.status == "CAN_XEM"
    assert not assessment.matched_evidence


def test_expired_notice_is_rejected() -> None:
    assessment = assess_notice_feasibility(
        _notice(NOW - timedelta(days=1)),
        ("network cable",),
        [],
        now=NOW,
    )

    assert assessment.status == "HET_HAN"
    assert assessment.score == 0
