from pathlib import Path

from sqlalchemy import func, select

from qi_crawler.bid_intelligence import (
    analyze_bid_document,
    estimate_win_likelihood,
    evaluate_bid_gate,
    extract_keywords,
    import_evidence_csv,
)
from qi_crawler.db import Database
from qi_crawler.models import BidRequirement, ComplianceAssessment


def test_extract_keywords_normalizes_vietnamese():
    words = extract_keywords("Nhà thầu phải có chứng chỉ kỹ thuật mạng Cisco")
    assert "chung" in words
    assert "cisco" in words


def test_evidence_backed_assessment(tmp_path: Path):
    db = Database(f"sqlite:///{tmp_path / 'warehouse.db'}")
    db.create_all()
    evidence = tmp_path / "evidence.csv"
    evidence.write_text(
        "evidence_code,title,evidence_type,description,keywords,verified\n"
        "CERT-01,Chứng chỉ kỹ thuật Cisco,certificate,Kỹ sư mạng Cisco,CCNP Cisco,true\n",
        encoding="utf-8-sig",
    )
    assert import_evidence_csv(db, evidence) == 1
    requirements = tmp_path / "requirements.txt"
    requirements.write_text(
        "Nhà thầu phải có chứng chỉ kỹ thuật mạng Cisco\n"
        "Nhà thầu phải có doanh thu tối thiểu 10 tỷ đồng\n",
        encoding="utf-8",
    )
    result = analyze_bid_document(db, requirements)
    assert result.total == 2
    assert result.covered == 1
    assert result.gaps == 1
    with db.session() as session:
        assert session.scalar(select(func.count()).select_from(BidRequirement)) == 2
        assert session.scalar(select(func.count()).select_from(ComplianceAssessment)) == 2
    prediction = estimate_win_likelihood(db)
    assert 5 <= prediction.estimated_win_percent <= 80
    assert prediction.confidence_percent <= 35
    assert prediction.readiness_score < 100
    assert prediction.gate_status == "NO-GO"
    gate = evaluate_bid_gate(db)
    assert gate.status == "NO-GO"
    assert gate.blockers
