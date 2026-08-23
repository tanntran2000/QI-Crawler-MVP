from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

from qi_crawler.db import Database
from qi_crawler.market_intelligence.source_detection import SourceType, detect_source_type
from qi_crawler.market_intelligence.source_type_review import (
    SourceTypeReviewError,
    SourceTypeReviewService,
)


def _source(path: Path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["GÓI TIN", "SỐ KẾ HOẠCH", "TÊN DỰ ÁN", "TÊN CHỦ ĐẦU TƯ", "TÊN GÓI THẦU"])
    sheet.append(["1", "PL2600265077-00", "Dự án thử", "Chủ đầu tư thử", "Gói thử"])
    workbook.save(path)


def test_human_source_type_correction_is_append_only(tmp_path: Path) -> None:
    source = tmp_path / "unknown.xlsx"
    _source(source)
    detection = detect_source_type(source)
    service = SourceTypeReviewService(Database(f"sqlite:///{tmp_path / 'review.db'}"))

    first = service.record_decision(detection, final_type=SourceType.KHMT, reviewer="Team Bid")
    second = service.record_decision(
        detection,
        final_type=SourceType.TBMT,
        reviewer="Team Bid",
        note="Đã xác nhận lại nguồn",
    )

    history = service.list_history(detection.source_sha256)
    assert [event.id for event in history] == [first.id, second.id]
    assert [event.final_type for event in history] == ["KHMT", "TBMT"]
    assert all(event.identity_namespace == "PL" for event in history)
    assert all(event.source_sha256 == detection.source_sha256 for event in history)
    assert history[0].identity_raw_values_json is not None


def test_human_decision_requires_reviewer(tmp_path: Path) -> None:
    source = tmp_path / "unknown.xlsx"
    _source(source)
    detection = detect_source_type(source)
    service = SourceTypeReviewService(Database(f"sqlite:///{tmp_path / 'review.db'}"))

    try:
        service.record_decision(detection, final_type=SourceType.KHMT)
    except SourceTypeReviewError as exc:
        assert "người" in str(exc).lower()
    else:  # pragma: no cover - assertion keeps the contract explicit
        raise AssertionError("anonymous source-type correction was accepted")
