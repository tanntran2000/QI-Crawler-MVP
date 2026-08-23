from __future__ import annotations

from pathlib import Path

import pytest

from qi_crawler import gui_services
from qi_crawler.config import AppConfig
from qi_crawler.market_intelligence.search import TargetedSearchRequest
from qi_crawler.market_intelligence.source_detection import SourceType


def test_tbmt_service_route_does_not_call_khmt_importer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    called = False

    def forbidden(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("KHMT importer must not run for TBMT")

    monkeypatch.setattr(gui_services, "import_khmt_workbook", forbidden)
    config = AppConfig()
    request = TargetedSearchRequest()

    with pytest.raises(ValueError, match="TBMT"):
        gui_services.run_bid_radar_import_search(
            config,
            tmp_path / "TBMT.xlsx",
            request,
            source_type=SourceType.TBMT,
        )

    assert called is False
