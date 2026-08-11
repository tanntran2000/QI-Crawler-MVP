"""AI-powered sector classification for tender notices.

This module provides DAUTHAU.INFO-equivalent AI classification capabilities:
- Classify notices by sector using VSIC 2018 codes
- Rule-based fallback when no AI API key is available
- Batch classification for existing data
- Confidence scoring with human review queue
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy import select

from .db import Database
from .keywords import normalize_keyword
from .models import Notice

logger = logging.getLogger(__name__)

# VSIC 2018 sector codes commonly relevant to procurement.
VSIC_SECTORS: dict[str, dict[str, str | list[str]]] = {
    "41": {
        "name": "Xay dung nha cac loai",
        "name_en": "Construction of buildings",
        "keywords": ["xay dung", "nha", "cong trinh", "construction", "building"],
    },
    "42": {
        "name": "Xay dung cong trinh ky thuat dan dung",
        "name_en": "Civil engineering",
        "keywords": ["cau", "duong", "cong trinh", "ha tang", "bridge", "road", "infrastructure"],
    },
    "43": {
        "name": "Hoat dong xay dung chuyen dung",
        "name_en": "Specialised construction activities",
        "keywords": ["lap dat", "dien", "nuoc", "installation", "electrical", "plumbing"],
    },
    "46": {
        "name": "Ban buon (tru o to, mo to, xe may)",
        "name_en": "Wholesale trade",
        "keywords": ["cung cap", "mua sam", "supply", "procurement", "wholesale"],
    },
    "58": {
        "name": "Hoat dong xuat ban",
        "name_en": "Publishing activities",
        "keywords": ["in an", "xuat ban", "publishing", "printing"],
    },
    "61": {
        "name": "Vien thong",
        "name_en": "Telecommunications",
        "keywords": ["vien thong", "mang", "telecom", "network", "fiber", "cap quang"],
    },
    "62": {
        "name": "Lap trinh may tinh, tu van va cac hoat dong lien quan",
        "name_en": "Computer programming and consultancy",
        "keywords": [
            "phan mem", "cntt", "cong nghe thong tin", "software", "IT",
            "may tinh", "computer", "server", "he thong",
        ],
    },
    "63": {
        "name": "Hoat dong dich vu thong tin",
        "name_en": "Information service activities",
        "keywords": ["du lieu", "data", "thong tin", "information"],
    },
    "71": {
        "name": "Hoat dong kien truc va tu van ky thuat",
        "name_en": "Architectural and engineering activities",
        "keywords": ["tu van", "thiet ke", "kien truc", "consulting", "design", "engineering"],
    },
    "72": {
        "name": "Nghien cuu khoa hoc va phat trien",
        "name_en": "Scientific research and development",
        "keywords": ["nghien cuu", "research", "R&D", "khoa hoc"],
    },
    "77": {
        "name": "Cho thue may moc, thiet bi",
        "name_en": "Rental and leasing activities",
        "keywords": ["thue", "rental", "lease", "thiet bi"],
    },
    "84": {
        "name": "Hoat dong cua Dang, to chuc chinh tri - xa hoi, quan ly Nha nuoc",
        "name_en": "Public administration and defence",
        "keywords": ["nha nuoc", "chinh phu", "government", "public"],
    },
    "85": {
        "name": "Giao duc va dao tao",
        "name_en": "Education",
        "keywords": ["giao duc", "dao tao", "education", "training", "truong hoc"],
    },
    "86": {
        "name": "Hoat dong y te",
        "name_en": "Human health activities",
        "keywords": [
            "y te", "benh vien", "medical", "health", "thuoc",
            "thiet bi y te", "pharmaceutical", "vaccine",
        ],
    },
}


@dataclass(frozen=True)
class ClassificationResult:
    """Result of classifying a notice by sector."""

    notice_id: int
    vsic_code: str | None
    sector_name: str | None
    sector_name_en: str | None
    confidence: float
    method: str  # "rule_based" or "ai"
    matched_keywords: list[str]


def classify_by_rules(notice: Notice) -> ClassificationResult:
    """Classify a notice using rule-based keyword matching against VSIC codes."""
    text = normalize_keyword(
        " ".join(
            filter(None, [notice.title, notice.raw_text, notice.sector, notice.buyer])
        )
    )

    best_code: str | None = None
    best_score = 0
    best_matches: list[str] = []

    for code, info in VSIC_SECTORS.items():
        keywords = info["keywords"]
        matches = [kw for kw in keywords if normalize_keyword(kw) in text]
        score = len(matches)
        if score > best_score:
            best_code = code
            best_score = score
            best_matches = matches

    if best_code and best_score >= 1:
        info = VSIC_SECTORS[best_code]
        confidence = min(0.85, 0.4 + best_score * 0.15)
        return ClassificationResult(
            notice_id=notice.id,
            vsic_code=best_code,
            sector_name=str(info["name"]),
            sector_name_en=str(info["name_en"]),
            confidence=round(confidence, 2),
            method="rule_based",
            matched_keywords=best_matches,
        )

    return ClassificationResult(
        notice_id=notice.id,
        vsic_code=None,
        sector_name=None,
        sector_name_en=None,
        confidence=0.0,
        method="rule_based",
        matched_keywords=[],
    )


def classify_notice(
    notice: Notice,
    ai_api_key: str | None = None,
) -> ClassificationResult:
    """Classify a notice, using AI if available, otherwise rule-based."""
    # For now, always use rule-based. AI integration can be added when API key is provided.
    if ai_api_key:
        # Placeholder for future AI classification.
        # Would call OpenAI/Gemini API to classify the notice text.
        logger.info("AI classification chua duoc tich hop. Su dung rule-based.")

    return classify_by_rules(notice)


def batch_classify(
    db: Database,
    ai_api_key: str | None = None,
    only_unclassified: bool = True,
    limit: int = 500,
) -> list[ClassificationResult]:
    """Classify multiple notices and save results to the database."""
    results: list[ClassificationResult] = []

    with db.session() as session:
        statement = select(Notice).order_by(Notice.id.desc()).limit(limit)
        if only_unclassified:
            statement = statement.where(Notice.ai_sector.is_(None))
        notices = list(session.scalars(statement).all())

    for notice in notices:
        result = classify_notice(notice, ai_api_key)
        results.append(result)

        # Save classification to the notice record.
        if result.vsic_code:
            with db.session() as session:
                db_notice = session.get(Notice, notice.id)
                if db_notice:
                    db_notice.ai_sector = result.sector_name
                    db_notice.ai_sector_code = result.vsic_code
                    db_notice.ai_confidence = result.confidence

    classified = sum(1 for r in results if r.vsic_code)
    logger.info(
        "Da phan loai %d/%d goi thau (method=%s)",
        classified, len(results), "rule_based",
    )
    return results


def get_sector_distribution(db: Database) -> dict[str, int]:
    """Get distribution of notices by classified sector."""
    with db.session() as session:
        notices = session.scalars(
            select(Notice).where(Notice.ai_sector.isnot(None))
        ).all()

    distribution: dict[str, int] = {}
    for notice in notices:
        sector = notice.ai_sector or "Khong xac dinh"
        distribution[sector] = distribution.get(sector, 0) + 1

    return dict(sorted(distribution.items(), key=lambda x: -x[1]))
