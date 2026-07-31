from __future__ import annotations

import csv
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import delete, select

from .db import Database
from .models import BidPrediction, BidRequirement, CompanyEvidence, ComplianceAssessment

STOPWORDS = {
    "va", "hoac", "cac", "cua", "cho", "voi", "theo", "duoc", "phai", "co", "la",
    "trong", "tu", "den", "mot", "nhung", "nay", "do", "ve", "tai", "khi",
}
MANDATORY_MARKERS = ("phải", "bắt buộc", "tối thiểu", "không thấp hơn", "đáp ứng")
CATEGORY_MARKERS = {
    "legal": ("pháp lý", "đăng ký kinh doanh", "ủy quyền"),
    "financial": ("doanh thu", "tài chính", "bảo lãnh", "tín dụng"),
    "experience": ("kinh nghiệm", "hợp đồng tương tự", "đã thực hiện"),
    "personnel": ("nhân sự", "chuyên gia", "chứng chỉ", "kỹ sư"),
    "technical": ("kỹ thuật", "thông số", "tiêu chuẩn", "giải pháp", "thiết bị"),
    "delivery": ("tiến độ", "giao hàng", "thời gian thực hiện"),
}


def fold_text(value: str) -> str:
    value = unicodedata.normalize("NFD", value.lower().replace("đ", "d"))
    value = "".join(char for char in value if unicodedata.category(char) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9+#./%-]+", " ", value)).strip()


def extract_keywords(text: str, limit: int = 20) -> list[str]:
    tokens = re.findall(r"[a-z0-9+#./%-]{2,}", fold_text(text))
    counts: dict[str, int] = {}
    for token in tokens:
        if token not in STOPWORDS and not token.isdigit():
            counts[token] = counts.get(token, 0) + 1
    return sorted(counts, key=lambda item: (-counts[item], -len(item), item))[:limit]


def classify_requirement(text: str) -> str:
    folded = fold_text(text)
    for category, markers in CATEGORY_MARKERS.items():
        if any(fold_text(marker) in folded for marker in markers):
            return category
    return "technical"


def split_requirements(text: str) -> list[str]:
    lines = [re.sub(r"^\s*(?:[-–•*]|\d+[.)])\s*", "", line).strip() for line in text.splitlines()]
    return [line for line in lines if len(line) >= 12]


@dataclass
class AssessmentSummary:
    total: int
    covered: int
    partial: int
    gaps: int
    coverage_percent: float


@dataclass
class WinEstimate:
    prediction_id: int
    readiness_score: float
    estimated_win_percent: float
    confidence_percent: float
    mandatory_coverage_percent: float
    evidence_coverage_percent: float
    risk_factors: list[str]
    model_version: str = "heuristic-mvp-1"


def import_evidence_csv(db: Database, path: Path) -> int:
    count = 0
    with path.open("r", encoding="utf-8-sig", newline="") as handle, db.session() as session:
        for row in csv.DictReader(handle):
            code = (row.get("evidence_code") or "").strip()
            title = (row.get("title") or "").strip()
            if not code or not title:
                raise ValueError("Mỗi bằng chứng cần evidence_code và title")
            item = session.scalar(select(CompanyEvidence).where(CompanyEvidence.evidence_code == code))
            if item is None:
                item = CompanyEvidence(evidence_code=code, title=title)
                session.add(item)
            item.title = title
            item.evidence_type = (row.get("evidence_type") or "other").strip()
            item.description = (row.get("description") or "").strip() or None
            item.keywords = (row.get("keywords") or "").strip() or None
            item.source_path = (row.get("source_path") or "").strip() or None
            item.valid_until = (row.get("valid_until") or "").strip() or None
            item.verified = (row.get("verified") or "").strip().lower() in {"1", "true", "yes", "có"}
            count += 1
    return count


def analyze_bid_document(
    db: Database, path: Path, notice_id: int | None = None, replace: bool = True
) -> AssessmentSummary:
    text = path.read_text(encoding="utf-8-sig")
    requirements = split_requirements(text)
    with db.session() as session:
        if replace:
            old_ids = session.scalars(
                select(BidRequirement.id).where(BidRequirement.notice_id == notice_id)
            ).all()
            if old_ids:
                session.execute(delete(ComplianceAssessment).where(ComplianceAssessment.requirement_id.in_(old_ids)))
                session.execute(delete(BidRequirement).where(BidRequirement.id.in_(old_ids)))
        evidence = session.scalars(select(CompanyEvidence)).all()
        statuses: list[str] = []
        for index, source_text in enumerate(requirements, start=1):
            normalized = fold_text(source_text)
            keywords = extract_keywords(source_text)
            requirement = BidRequirement(
                notice_id=notice_id,
                requirement_code=f"REQ-{index:04d}",
                category=classify_requirement(source_text),
                source_text=source_text,
                normalized_text=normalized,
                keywords=json.dumps(keywords, ensure_ascii=False),
                mandatory=any(marker in source_text.lower() for marker in MANDATORY_MARKERS),
                source_reference=f"{path.name}:line-{index}",
            )
            session.add(requirement)
            session.flush()
            best: tuple[float, CompanyEvidence | None, list[str]] = (0.0, None, [])
            required = set(keywords)
            for item in evidence:
                evidence_text = " ".join(filter(None, [item.title, item.description, item.keywords]))
                matched = sorted(required.intersection(extract_keywords(evidence_text, limit=100)))
                score = len(matched) / len(required) if required else 0.0
                if score > best[0]:
                    best = (score, item, matched)
            score, item, matched = best
            status = "covered" if item and item.verified and score >= 0.65 else "partial" if item and score >= 0.25 else "gap"
            statuses.append(status)
            session.add(ComplianceAssessment(
                requirement_id=requirement.id,
                evidence_id=item.id if item else None,
                status=status,
                score=round(score, 4),
                matched_keywords=json.dumps(matched, ensure_ascii=False),
                explanation=(
                    f"Khớp {len(matched)}/{len(required)} keyword với bằng chứng {item.evidence_code}."
                    if item else "Chưa tìm thấy bằng chứng nội bộ phù hợp."
                ),
                requires_human_confirmation=True,
            ))
    total = len(statuses)
    covered = statuses.count("covered")
    partial = statuses.count("partial")
    gaps = statuses.count("gap")
    return AssessmentSummary(total, covered, partial, gaps, round(100 * covered / total, 2) if total else 0.0)


def estimate_win_likelihood(db: Database, notice_id: int | None = None) -> WinEstimate:
    """Estimate bid readiness from evidence coverage, not competitor or price knowledge.

    The output is deliberately capped because this MVP has no calibrated historical outcome data.
    """
    with db.session() as session:
        statement = (
            select(ComplianceAssessment, BidRequirement)
            .join(BidRequirement, BidRequirement.id == ComplianceAssessment.requirement_id)
            .where(BidRequirement.notice_id == notice_id)
        )
        rows = session.execute(statement).all()
        if not rows:
            raise ValueError("Chưa có kết quả compliance để ước tính. Hãy chạy analyze-bid trước.")

        weights = {"covered": 1.0, "partial": 0.45, "gap": 0.0}
        evidence_coverage = 100 * sum(weights[item.status] for item, _ in rows) / len(rows)
        mandatory = [(item, requirement) for item, requirement in rows if requirement.mandatory]
        mandatory_coverage = (
            100 * sum(weights[item.status] for item, _ in mandatory) / len(mandatory)
            if mandatory else evidence_coverage
        )
        mandatory_gaps = sum(1 for item, _ in mandatory if item.status == "gap")
        partial_count = sum(1 for item, _ in rows if item.status == "partial")

        readiness = 0.7 * mandatory_coverage + 0.3 * evidence_coverage
        if mandatory_gaps:
            readiness = max(0.0, readiness - min(30.0, mandatory_gaps * 10.0))
        readiness = round(readiness, 2)

        # Conservative proxy until won/lost bids, price position and competitor data are available.
        estimated = round(min(80.0, max(5.0, 10.0 + readiness * 0.7)), 2)
        sample_confidence = min(20.0, len(rows) * 1.5)
        confidence = round(min(35.0, 15.0 + sample_confidence), 2)
        risks = [
            "Chưa có dữ liệu giá dự thầu và vị trí giá so với đối thủ.",
            "Chưa có dữ liệu lịch sử thắng/thua để hiệu chỉnh xác suất.",
        ]
        if mandatory_gaps:
            risks.insert(0, f"Có {mandatory_gaps} yêu cầu bắt buộc chưa có bằng chứng.")
        if partial_count:
            risks.append(f"Có {partial_count} yêu cầu mới chỉ đáp ứng một phần.")

        prediction = BidPrediction(
            notice_id=notice_id,
            model_version="heuristic-mvp-1",
            readiness_score=readiness,
            estimated_win_percent=estimated,
            confidence_percent=confidence,
            mandatory_coverage_percent=round(mandatory_coverage, 2),
            evidence_coverage_percent=round(evidence_coverage, 2),
            risk_factors=json.dumps(risks, ensure_ascii=False),
            assumptions=json.dumps(
                [
                    "Bằng chứng verified là hợp lệ và còn hiệu lực.",
                    "Keyword match chỉ là tín hiệu hỗ trợ, không thay thế chuyên gia đấu thầu.",
                    "Ước tính không bao gồm giá, đối thủ, quan hệ thương mại hoặc quyết định tổ chuyên gia.",
                ],
                ensure_ascii=False,
            ),
        )
        session.add(prediction)
        session.flush()
        prediction_id = prediction.id
    return WinEstimate(
        prediction_id=prediction_id,
        readiness_score=readiness,
        estimated_win_percent=estimated,
        confidence_percent=confidence,
        mandatory_coverage_percent=round(mandatory_coverage, 2),
        evidence_coverage_percent=round(evidence_coverage, 2),
        risk_factors=risks,
    )
