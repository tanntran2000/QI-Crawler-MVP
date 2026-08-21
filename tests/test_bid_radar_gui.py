from __future__ import annotations

import hashlib
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
from qi_crawler.market_intelligence.khmt_importer import KHMTImportError, KHMTIssueCode
from qi_crawler.market_intelligence.search import TargetedSearchValidationError


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
    tmp_path: Path,
) -> None:
    calls: list[object] = []

    def fake_submit(function, *args, **kwargs) -> None:
        calls.append(function)

    monkeypatch.setattr(window, "_submit", fake_submit)
    source = tmp_path / "khmt.xlsx"
    source.write_bytes(b"khmt-source")
    window.bid_radar_path.setText(str(source))
    window._bid_radar_loaded_source = source
    window._bid_radar_loaded_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
    window._bid_radar_packages = (object(),)

    window.start_bid_radar_export()
    window.start_bid_radar_legal_docx()

    assert calls == [gui.run_bid_radar_export, gui.run_bid_radar_legal_docx]


def test_switching_khmt_source_clears_stale_rows_and_blocks_export(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    package = SimpleNamespace(
        plan=SimpleNamespace(plan_id_raw="PL-A", plan_base_id="PL-A", plan_revision=None),
        package_name="Gói A",
        package_price=100,
        province_city_name="Hà Nội",
    )
    row = SimpleNamespace(
        package=package,
        matched=True,
        reasons=(),
        review_state="UNREVIEWED",
    )
    source_a = tmp_path / "source-a.xlsx"
    source_b = tmp_path / "source-b.xlsx"
    source_a.write_bytes(b"a")
    source_b.write_bytes(b"b")
    window.bid_radar_path.setText(str(source_a))
    window._render_bid_radar_result(
        SimpleNamespace(
            source_path=source_a,
            packages=(package,),
            rows=(row,),
            issues=(),
            matched_count=1,
            total_examined=1,
        )
    )
    assert window.bid_radar_table.rowCount() == 1

    monkeypatch.setattr(
        gui.QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(source_b), "Excel KHMT (*.xlsx)"),
    )
    captured: list[object] = []
    monkeypatch.setattr(window, "_submit", lambda function, *args, **kwargs: captured.append(function))

    window._choose_bid_radar_file()
    window.start_bid_radar_export()

    assert window.bid_radar_path.text() == str(source_b)
    assert window.bid_radar_table.rowCount() == 0
    assert window._bid_radar_packages == ()
    assert captured == []
    assert "nhập" in window.bid_radar_status.text().lower()


def test_changed_khmt_content_at_same_path_blocks_both_exports(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "khmt.xlsx"
    source.write_bytes(b"source-a")
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    package = SimpleNamespace(
        plan=SimpleNamespace(plan_id_raw="PL-A", plan_base_id="PL-A", plan_revision=None),
        package_name="Gói A",
        package_price=100,
        province_city_name="Hà Nội",
    )
    row = SimpleNamespace(package=package, matched=True, reasons=(), review_state="UNREVIEWED")
    window.bid_radar_path.setText(str(source))
    window._render_bid_radar_result(
        SimpleNamespace(
            source_path=source,
            source_sha256=source_sha,
            packages=(package,),
            rows=(row,),
            issues=(),
            matched_count=1,
            total_examined=1,
        )
    )
    source.write_bytes(b"source-b")
    captured: list[object] = []
    monkeypatch.setattr(window, "_submit", lambda function, *args, **kwargs: captured.append(function))

    window.start_bid_radar_export()
    status_after_xlsx = window.bid_radar_status.text().lower()
    window.start_bid_radar_legal_docx()

    assert captured == []
    assert "thay đổi" in status_after_xlsx
    assert "nhập lại" in status_after_xlsx


def test_bid_radar_import_issues_show_code_row_and_message(
    window: QICrawlerWindow,
) -> None:
    issue = SimpleNamespace(
        code=SimpleNamespace(value="INVALID_PRICE"),
        source_row=27,
        message="Giá gói thầu không hợp lệ",
    )
    window._render_bid_radar_result(
        SimpleNamespace(
            source_path=Path("khmt.xlsx"),
            packages=(),
            rows=(),
            issues=(issue,),
            matched_count=0,
            total_examined=0,
        )
    )

    status = window.bid_radar_status.text()
    assert "INVALID_PRICE" in status
    assert "27" in status
    assert "Giá gói thầu không hợp lệ" in status


@pytest.mark.parametrize("error", [
    KHMTImportError(KHMTIssueCode.MISSING_REQUIRED_HEADER, "Thiếu cột TÊN GÓI THẦU"),
    TargetedSearchValidationError("ngân sách tối thiểu lớn hơn tối đa"),
])
def test_expected_bid_radar_errors_are_user_readable(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
    error: BaseException,
) -> None:
    monkeypatch.setattr(gui.QMessageBox, "critical", lambda *args, **kwargs: None)
    window._worker_error(
        window.bid_radar_import_button,
        error,
        window.bid_radar_progress,
        window.bid_radar_status,
    )

    assert str(error) in window.bid_radar_status.text()
    assert "traceback" not in window.bid_radar_status.text().lower()
