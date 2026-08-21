from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from qi_crawler import gui
from qi_crawler.config import AppConfig
from qi_crawler.gui import QICrawlerWindow


@pytest.fixture(scope="module")
def application() -> QApplication:
    return QApplication.instance() or QApplication([])


@pytest.fixture
def config(tmp_path: Path) -> AppConfig:
    value = AppConfig()
    value.storage.database_url = f"sqlite:///{tmp_path / 'bid-radar.db'}"
    value.storage.report_dir = tmp_path / "reports"
    return value


@pytest.fixture
def window(
    application: QApplication,
    config: AppConfig,
    tmp_path: Path,
) -> QICrawlerWindow:
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    value = QICrawlerWindow(config, settings=settings)
    yield value
    value.close()
    value.deleteLater()


def test_bid_radar_is_reachable_without_removing_existing_pages(
    window: QICrawlerWindow,
) -> None:
    labels = [window.navigation.item(index).text() for index in range(window.navigation.count())]

    assert "Bid Radar" in labels
    assert window.pages.count() == window.navigation.count()
    assert "THU THẬP" in labels
    assert "HSMT / PHÂN TÍCH" in labels


def test_import_delegates_to_existing_mi_import_and_search_service(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured: dict[str, object] = {}

    def fake_submit(function, *args, **kwargs) -> None:
        captured["function"] = function
        captured["args"] = args
        captured["button"] = kwargs["button"]

    monkeypatch.setattr(window, "_submit", fake_submit)
    source = tmp_path / "khmt.xlsx"
    source.write_bytes(b"placeholder")
    window.bid_radar_path.setText(str(source))

    window.start_bid_radar_import()

    assert captured["function"] is gui.run_bid_radar_import_search
    assert captured["args"][0] is window.config
    assert captured["args"][1] == source
    assert captured["button"] is window.bid_radar_import_button


def test_filter_match_does_not_auto_confirm(window: QICrawlerWindow) -> None:
    row = SimpleNamespace(
        package=SimpleNamespace(
            plan=SimpleNamespace(plan_base_id="PL260001", plan_revision=None),
            package_name="Gói thử nghiệm",
            package_price=100,
            province_city_name="Hà Nội",
        ),
        matched=True,
        reasons=("Từ khóa phù hợp",),
        review_state="UNREVIEWED",
    )
    window._render_bid_radar_result(
        SimpleNamespace(
            packages=(row.package,),
            rows=(row,),
            matched_count=1,
            total_examined=1,
        )
    )

    assert window.bid_radar_table.item(0, 7).text() == "Chưa xem"
    assert window._bid_radar_rows[0].review_state != "CONFIRMED"


def test_review_requires_reviewer(window: QICrawlerWindow) -> None:
    row = SimpleNamespace(
        package=SimpleNamespace(
            plan=SimpleNamespace(plan_base_id="PL260001", plan_revision=None),
            package_name="Gói thử nghiệm",
            package_price=100,
            province_city_name="Hà Nội",
        ),
        matched=True,
        reasons=(),
        review_state="UNREVIEWED",
    )
    window._render_bid_radar_result(
        SimpleNamespace(packages=(row.package,), rows=(row,), matched_count=1, total_examined=1)
    )
    window.bid_radar_table.selectRow(0)
    window.start_bid_radar_review("CONFIRMED")

    assert "reviewer" in window.bid_radar_status.text().lower()


def test_review_delegates_to_candidate_review_service(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row = SimpleNamespace(
        package=SimpleNamespace(
            plan=SimpleNamespace(plan_base_id="PL260001", plan_revision=None),
            package_name="Gói thử nghiệm",
            package_price=100,
            province_city_name="Hà Nội",
        ),
        matched=True,
        reasons=(),
        review_state="UNREVIEWED",
    )
    window._render_bid_radar_result(
        SimpleNamespace(packages=(row.package,), rows=(row,), matched_count=1, total_examined=1)
    )
    window.bid_radar_table.selectRow(0)
    window.bid_radar_reviewer.setText("Bid Team")
    captured: dict[str, object] = {}

    def fake_submit(function, *args, **kwargs) -> None:
        captured["function"] = function
        captured["args"] = args

    monkeypatch.setattr(window, "_submit", fake_submit)
    window.start_bid_radar_review("CONFIRMED")

    assert captured["function"] is gui.run_bid_radar_review
    assert captured["args"][0] is window.config
    assert captured["args"][2] == "CONFIRMED"
    assert captured["args"][3] == "Bid Team"


def test_exports_delegate_to_mi4_and_mi5_services(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []

    def fake_submit(function, *args, **kwargs) -> None:
        calls.append(function)

    monkeypatch.setattr(window, "_submit", fake_submit)
    window._bid_radar_packages = (object(),)

    window.start_bid_radar_export()
    window.start_bid_radar_legal_docx()

    assert calls == [gui.run_bid_radar_export, gui.run_bid_radar_legal_docx]
