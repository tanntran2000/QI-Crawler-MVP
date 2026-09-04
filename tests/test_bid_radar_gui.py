from __future__ import annotations

import hashlib
import os
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QApplication, QLabel, QTextEdit

from qi_crawler import gui
from qi_crawler.config import AppConfig
from qi_crawler.db import SchemaNotReady
from qi_crawler.gui import QICrawlerWindow
from qi_crawler.market_intelligence.khmt_importer import KHMTImportError, KHMTIssueCode
from qi_crawler.market_intelligence.search import TargetedSearchValidationError
from qi_crawler.market_intelligence.source_detection import SourceType, SourceTypeDetection


def _fake_radar_item(raw_id: str = "PL260001-00") -> SimpleNamespace:
    namespace = raw_id[:2]
    base_id, revision = raw_id.rsplit("-", 1)
    return SimpleNamespace(
        identity=SimpleNamespace(raw_id=raw_id, base_id=base_id, revision=revision),
        source_type=SimpleNamespace(value="KHMT" if namespace == "PL" else "TBMT"),
        package_name="Gói thử nghiệm",
        package_price=100,
        province_city_name="Hà Nội",
        source_sha256="a" * 64,
        observation_key=f"observation-{raw_id}",
        source_filename="source.xlsx",
    )


def _fake_result(
    item: SimpleNamespace | None = None,
    *,
    path: Path = Path("khmt.xlsx"),
    source_type: str = "KHMT",
    source_sha256: str = "a" * 64,
    issues: tuple[object, ...] = (),
    disposition: str = "MATCH",
    matched_count: int = 1,
    indeterminate_count: int = 0,
    nonmatched_count: int = 0,
    unfiltered_count: int = 0,
    review_state: str = "UNREVIEWED",
) -> SimpleNamespace:
    item = item or _fake_radar_item("PL260001-00")
    row = SimpleNamespace(
        item=item,
        disposition=disposition,
        reasons=(),
        review_state=review_state,
    )
    load_result = SimpleNamespace(
        source_type=SimpleNamespace(value=source_type),
        source_path=path,
        source_sha256=source_sha256,
        items=(item,),
    )
    return SimpleNamespace(
        source_type=SimpleNamespace(value=source_type),
        load_result=load_result,
        source_path=path,
        source_sha256=source_sha256,
        items=(item,),
        rows=(row,),
        issues=issues,
        matched_count=matched_count,
        indeterminate_count=indeterminate_count,
        nonmatched_count=nonmatched_count,
        unfiltered_count=unfiltered_count,
        total_examined=1,
    )


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


def test_team_bid_workspace_is_thinly_wired_into_existing_document_page(
    window: QICrawlerWindow,
) -> None:
    assert window.workspace_zone.count() == 7
    assert window.workspace_zone.itemData(0) == "01_Source_E-HSMT"
    assert window.workspace_zone.itemData(6) == "07_Evidence_Archive"
    assert window.workspace_status.text().startswith("Chưa mở TenderCase")


def test_team_bid_workspace_open_delegates_to_service(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_submit(function, *args, **kwargs) -> None:
        captured["function"] = function
        captured["args"] = args

    monkeypatch.setattr(window, "_submit", fake_submit)
    window.workspace_case_id.setText("case-ui")
    window.workspace_release_id.setText("IB2600000202-00")
    window.start_tender_workspace_open()

    assert captured["function"] is gui.run_tender_workspace_open_or_create
    assert captured["args"] == (window.config, "case-ui", "IB2600000202-00")


def test_bid_radar_source_selector_defaults_to_automatic(window: QICrawlerWindow) -> None:
    assert window.bid_radar_source_type.currentData() is None
    assert window.bid_radar_source_type.currentText() == "TỰ ĐỘNG"


def test_bid_radar_request_normalizes_grouped_money_inputs(window: QICrawlerWindow) -> None:
    window.bid_radar_min_budget.setText("500.000.000")
    window.bid_radar_max_budget.setText("1 300 000 000")

    request = window._bid_radar_request()

    assert request.min_budget == Decimal(500000000)
    assert request.max_budget == Decimal(1300000000)

def test_bid_radar_request_normalizes_selection_method_labels(window: QICrawlerWindow) -> None:
    window.bid_radar_selection_method.setText("Đấu thầu rộng rãi, CHAO_GIA_TRUC_TUYEN")

    request = window._bid_radar_request()

    assert request.selection_methods == frozenset(
        {"DAU_THAU_RONG_RAI", "CHAO_GIA_TRUC_TUYEN"}
    )


def test_bid_radar_request_rejects_unknown_selection_method(window: QICrawlerWindow) -> None:
    window.bid_radar_selection_method.setText("Phương thức tự do")

    with pytest.raises(ValueError, match="selection method"):
        window._bid_radar_request()


def test_tbmt_source_is_recognized_and_submitted_to_source_neutral_import(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "TBMT_19_8_2026.xlsx"
    source.write_bytes(b"tbmt")
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    window.bid_radar_path.setText(str(source))
    monkeypatch.setattr(
        gui,
        "detect_source_type",
        lambda path: SourceTypeDetection(
            original_filename=source.name,
            source_sha256=source_sha,
            filename_type=SourceType.TBMT,
            content_type=SourceType.TBMT,
            identity_namespace="IB",
            identity_values=("IB2600463290-00",),
            identity_raw_values=("IB2600463290-00",),
            auto_type=SourceType.TBMT,
            requires_human=False,
            evidence=("TBMT headers",),
            reasons=(),
        ),
    )
    window._bid_radar_pending_source = window._source_session_identity(source, source_sha, SourceType.TBMT)
    window.apply_bid_radar_source()
    captured: list[object] = []
    monkeypatch.setattr(window, "_submit", lambda function, *args, **kwargs: captured.append(function))

    window.start_bid_radar_import()

    assert captured == [gui.run_bid_radar_import_search]
    assert "Work Package tiếp theo" not in window.bid_radar_status.text()



def test_bid_radar_source_summary_is_compact_and_retains_identity_details(
    window: QICrawlerWindow,
) -> None:
    detection = SourceTypeDetection(
        original_filename="TBMT_3_9_2026.xlsx",
        source_sha256="a" * 64,
        filename_type=SourceType.TBMT,
        content_type=SourceType.TBMT,
        identity_namespace="IB",
        identity_values=(
            "IB2600488839-00",
            "IB2600498410-00",
            "IB2600489267-01",
            "IB2600482068-01",
            "IB2600413629-00",
            "IB2600491729-00",
        ),
        identity_raw_values=(
            "IB2600488839-00",
            "IB2600498410-00",
            "IB2600489267-01",
            "IB2600482068-01",
            "IB2600413629-00",
            "IB2600491729-00",
        ),
        auto_type=SourceType.TBMT,
        requires_human=False,
        evidence=("TBMT headers",),
        reasons=(),
    )

    window._render_bid_radar_source_detection(detection, SourceType.TBMT)

    summary = window.bid_radar_source_summary.text()
    assert "Tên file: TBMT_3_9_2026.xlsx" in summary
    assert "Loại: TBMT" in summary
    assert "Số thông báo: 6" in summary
    assert "Revision:" in summary
    assert "Identity:" not in summary
    assert "(+5)" not in summary
    assert "IB2600488839-00" in window.bid_radar_source_summary.toolTip()

def test_bid_radar_renders_indeterminate_as_needs_review(window: QICrawlerWindow) -> None:
    item = _fake_radar_item("IB2600463290-00")
    result = _fake_result(
        item,
        path=Path("tbmt.xlsx"),
        source_type="TBMT",
        disposition="INDETERMINATE",
        matched_count=0,
        indeterminate_count=1,
    )
    result.rows[0].reasons = ("PRICE_UNKNOWN",)
    window._render_bid_radar_result(result)

    assert window.bid_radar_table.item(0, 0).text() == "IB2600463290-00"
    assert window.bid_radar_table.item(0, 6).text() == "CẦN KIỂM TRA"
    assert not window.bid_radar_legal_button.isEnabled()


def test_bid_radar_renders_unfiltered_without_suitability_claim(window: QICrawlerWindow) -> None:
    item = _fake_radar_item("IB2600463290-00")
    result = _fake_result(
        item,
        path=Path("tbmt.xlsx"),
        source_type="TBMT",
        disposition="UNFILTERED",
        matched_count=0,
        unfiltered_count=1,
    )

    window._render_bid_radar_result(result)

    assert window.bid_radar_table.item(0, 6).text() == "CHƯA LỌC"
    status = window.bid_radar_status.text().lower()
    assert "chưa áp dụng điều kiện lọc" in status
    assert "phù hợp 1" not in status


def test_unknown_source_requires_explicit_human_selection(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "opportunity.xlsx"
    source.write_bytes(b"unknown")
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    window.bid_radar_path.setText(str(source))
    monkeypatch.setattr(
        gui,
        "detect_source_type",
        lambda path: SourceTypeDetection(
            original_filename=source.name,
            source_sha256=source_sha,
            filename_type=SourceType.UNKNOWN,
            content_type=SourceType.KHMT,
            identity_namespace="PL",
            identity_values=("PL2600265077-00",),
            identity_raw_values=("PL2600265077-00",),
            auto_type=SourceType.UNKNOWN,
            requires_human=True,
            evidence=("KHMT headers",),
            reasons=("filename requires human selection",),
        ),
    )
    window._bid_radar_pending_source = window._source_session_identity(source, source_sha, SourceType.UNKNOWN)
    window.apply_bid_radar_source()
    captured: list[object] = []
    monkeypatch.setattr(window, "_submit", lambda function, *args, **kwargs: captured.append(function))

    window.start_bid_radar_import()

    assert captured == []
    assert "chọn rõ nguồn" in window.bid_radar_status.text().lower()


def test_manual_source_selection_routes_khmt_with_human_authority(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "opportunity.xlsx"
    source.write_bytes(b"unknown")
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    window.bid_radar_path.setText(str(source))
    window.bid_radar_source_type.setCurrentIndex(1)
    detection = SourceTypeDetection(
        original_filename=source.name,
        source_sha256=source_sha,
        filename_type=SourceType.UNKNOWN,
        content_type=SourceType.KHMT,
        identity_namespace="PL",
        identity_values=("PL2600265077-00",),
        identity_raw_values=("PL2600265077-00",),
        auto_type=SourceType.UNKNOWN,
        requires_human=True,
        evidence=("KHMT headers",),
        reasons=("filename requires human selection",),
    )
    monkeypatch.setattr(gui, "detect_source_type", lambda path: detection)
    window._bid_radar_pending_source = window._source_session_identity(source, source_sha, SourceType.KHMT)
    window.apply_bid_radar_source()
    window.bid_radar_reviewer.setText("Team Bid")
    captured: dict[str, object] = {}

    def fake_submit(function, *args, **kwargs) -> None:
        captured["function"] = function
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(window, "_submit", fake_submit)
    window.start_bid_radar_import()

    assert captured["function"] is gui.run_bid_radar_import_search
    assert captured["kwargs"]["source_type"] is SourceType.KHMT
    assert captured["kwargs"]["source_detection"] is detection
    assert captured["kwargs"]["source_reviewer"] == "Team Bid"


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
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    window.bid_radar_path.setText(str(source))
    monkeypatch.setattr(
        gui,
        "detect_source_type",
        lambda path: SourceTypeDetection(
            original_filename=source.name,
                source_sha256=source_sha,
            filename_type=SourceType.KHMT,
            content_type=SourceType.KHMT,
            identity_namespace="PL",
            identity_values=("PL2600265077-00",),
            identity_raw_values=("PL2600265077-00",),
            auto_type=SourceType.KHMT,
            requires_human=False,
            evidence=("KHMT headers",),
            reasons=(),
        ),
    )
    window._bid_radar_pending_source = window._source_session_identity(source, source_sha, SourceType.KHMT)
    window.apply_bid_radar_source()

    window.start_bid_radar_import()

    assert captured["function"] is gui.run_bid_radar_import_search
    assert captured["args"][0] is window.config
    assert captured["args"][1] == source
    assert captured["button"] is window.bid_radar_import_button


def test_filter_match_does_not_auto_confirm(window: QICrawlerWindow) -> None:
    window._render_bid_radar_result(_fake_result())

    assert window.bid_radar_table.item(0, 7).text() == "Chưa xem"
    assert window._bid_radar_rows[0].review_state != "CONFIRMED"


def test_selecting_row_does_not_activate_working_package(window: QICrawlerWindow) -> None:
    window._render_bid_radar_result(_fake_result())
    window.bid_radar_table.selectRow(0)

    assert window.active_tender_context is None
    assert window.bid_radar_activate_button.isEnabled()
    assert not window.bid_radar_confirm_button.isEnabled()
    assert "ĐANG XEM" in window.bid_radar_inspector_text.toPlainText()


def test_activation_requires_explicit_confirmation(window: QICrawlerWindow, monkeypatch: pytest.MonkeyPatch) -> None:
    window._render_bid_radar_result(_fake_result())
    window.bid_radar_table.selectRow(0)
    monkeypatch.setattr(
        gui.QMessageBox,
        "question",
        lambda *args, **kwargs: gui.QMessageBox.StandardButton.Cancel,
    )

    window.activate_selected_bid_radar_context()

    assert window.active_tender_context is None


def test_confirm_activation_stores_exact_revision_without_review(window: QICrawlerWindow, monkeypatch: pytest.MonkeyPatch) -> None:
    window._render_bid_radar_result(_fake_result())
    window.bid_radar_table.selectRow(0)
    monkeypatch.setattr(
        gui.QMessageBox,
        "question",
        lambda *args, **kwargs: gui.QMessageBox.StandardButton.Yes,
    )

    window.activate_selected_bid_radar_context()

    assert window.active_tender_context is not None
    assert window.active_tender_context.raw_id == "PL260001-00"
    assert window.active_tender_context.revision == "00"
    assert window._bid_radar_rows[0].review_state == "UNREVIEWED"
    assert window.bid_radar_confirm_button.isEnabled()


def test_same_base_different_revision_requires_explicit_switch(window: QICrawlerWindow, monkeypatch: pytest.MonkeyPatch) -> None:
    first = _fake_radar_item("IB12345678-00")
    second = _fake_radar_item("IB12345678-01")
    window._render_bid_radar_result(_fake_result(item=first, source_type="TBMT"))
    window.bid_radar_table.selectRow(0)
    monkeypatch.setattr(gui.QMessageBox, "question", lambda *args, **kwargs: gui.QMessageBox.StandardButton.Yes)
    window.activate_selected_bid_radar_context()

    window._render_bid_radar_result(_fake_result(item=second, source_type="TBMT"))
    window.bid_radar_table.selectRow(0)

    assert window.active_tender_context.raw_id == "IB12345678-00"
    assert "IB12345678-00" in window.bid_radar_context_warning.text()
    assert "IB12345678-01" in window.bid_radar_context_warning.text()
    assert not window.bid_radar_confirm_button.isEnabled()
    assert window.bid_radar_switch_button.isEnabled()

    monkeypatch.setattr(gui.QMessageBox, "question", lambda *args, **kwargs: gui.QMessageBox.StandardButton.Cancel)
    window.switch_selected_bid_radar_context()
    assert window.active_tender_context.raw_id == "IB12345678-00"

    monkeypatch.setattr(gui.QMessageBox, "question", lambda *args, **kwargs: gui.QMessageBox.StandardButton.Yes)
    window.switch_selected_bid_radar_context()
    assert window.active_tender_context.raw_id == "IB12345678-01"


def test_review_and_handoff_require_exact_active_revision(window: QICrawlerWindow, monkeypatch: pytest.MonkeyPatch) -> None:
    first = _fake_radar_item("IB12345678-00")
    second = _fake_radar_item("IB12345678-01")
    window._render_bid_radar_result(_fake_result(item=first, source_type="TBMT", review_state="CONFIRMED"))
    window.bid_radar_table.selectRow(0)
    monkeypatch.setattr(gui.QMessageBox, "question", lambda *args, **kwargs: gui.QMessageBox.StandardButton.Yes)
    window.activate_selected_bid_radar_context()

    window._render_bid_radar_result(_fake_result(item=second, source_type="TBMT", review_state="CONFIRMED"))
    window.bid_radar_table.selectRow(0)

    assert not window.bid_radar_workspace_button.isEnabled()
    assert "IB12345678-00" in window.bid_radar_context_warning.text()


def test_min_only_budget_summary_uses_inequality(window: QICrawlerWindow) -> None:
    window.bid_radar_min_budget.setText("800000000")
    window.bid_radar_max_budget.clear()
    window._update_bid_radar_context()
    assert "≥ 800.000.000 VNĐ" in window.bid_radar_active_filter_context.text()


def test_max_only_budget_summary_uses_inequality(window: QICrawlerWindow) -> None:
    window.bid_radar_min_budget.clear()
    window.bid_radar_max_budget.setText("1000000000")
    window._update_bid_radar_context()
    assert "≤ 1.000.000.000 VNĐ" in window.bid_radar_active_filter_context.text()


def test_refilter_same_source_preserves_active_and_marks_filtered_out(window: QICrawlerWindow, monkeypatch: pytest.MonkeyPatch) -> None:
    item = _fake_radar_item("IB12345678-00")
    window._render_bid_radar_result(_fake_result(item=item, source_type="TBMT"))
    window.bid_radar_table.selectRow(0)
    monkeypatch.setattr(gui.QMessageBox, "question", lambda *args, **kwargs: gui.QMessageBox.StandardButton.Yes)
    window.activate_selected_bid_radar_context()

    filtered = _fake_result(item=item, source_type="TBMT")
    filtered.items = ()
    filtered.rows = ()
    filtered.matched_count = 0
    filtered.total_examined = 0
    window._render_bid_radar_result(filtered)

    assert window.active_tender_context is not None
    assert window.active_tender_context.raw_id == "IB12345678-00"
    assert "Gói đang làm không nằm" in window.bid_radar_active_context_notice.text()


def test_source_change_cancel_preserves_active_context(window: QICrawlerWindow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    source_a = tmp_path / "source-a.xlsx"
    source_b = tmp_path / "source-b.xlsx"
    source_a.write_bytes(b"a")
    source_b.write_bytes(b"b")
    item = _fake_radar_item("IB12345678-00")
    window.bid_radar_path.setText(str(source_a))
    window._render_bid_radar_result(_fake_result(item=item, path=source_a, source_type="TBMT"))
    window.bid_radar_table.selectRow(0)
    monkeypatch.setattr(gui.QMessageBox, "question", lambda *args, **kwargs: gui.QMessageBox.StandardButton.Yes)
    window.activate_selected_bid_radar_context()
    monkeypatch.setattr(gui.QMessageBox, "question", lambda *args, **kwargs: gui.QMessageBox.StandardButton.Cancel)
    monkeypatch.setattr(gui.QFileDialog, "getOpenFileName", lambda *args, **kwargs: (str(source_b), "Excel"))

    window._choose_bid_radar_file()

    assert window.active_tender_context is not None
    assert window.bid_radar_path.text() == str(source_b.resolve())
    assert window._bid_radar_pending_source.path == source_b.resolve()


def test_source_change_confirm_clears_active_context(window: QICrawlerWindow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    source_a = tmp_path / "source-a.xlsx"
    source_b = tmp_path / "source-b.xlsx"
    source_a.write_bytes(b"a")
    source_b.write_bytes(b"b")
    item = _fake_radar_item("IB12345678-00")
    window.bid_radar_path.setText(str(source_a))
    window._render_bid_radar_result(_fake_result(item=item, path=source_a, source_type="TBMT"))
    window.bid_radar_table.selectRow(0)
    monkeypatch.setattr(gui.QMessageBox, "question", lambda *args, **kwargs: gui.QMessageBox.StandardButton.Yes)
    window.activate_selected_bid_radar_context()
    monkeypatch.setattr(gui.QFileDialog, "getOpenFileName", lambda *args, **kwargs: (str(source_b), "Excel"))

    window._choose_bid_radar_file()
    window._bid_radar_pending_source = window._source_session_identity(
        source_b,
        hashlib.sha256(source_b.read_bytes()).hexdigest(),
        SourceType.TBMT,
    )
    window.apply_bid_radar_source()

    assert window.active_tender_context is None
    assert window.bid_radar_path.text() == str(source_b.resolve())


def _source_detection(path: Path, source_sha256: str) -> SourceTypeDetection:
    return SourceTypeDetection(
        original_filename=path.name,
        source_sha256=source_sha256,
        filename_type=SourceType.TBMT,
        content_type=SourceType.TBMT,
        identity_namespace="IB",
        identity_values=("IB2600488839-00",),
        identity_raw_values=("IB2600488839-00",),
        auto_type=SourceType.TBMT,
        requires_human=False,
        evidence=("TBMT headers",),
        reasons=(),
    )


def test_source_selection_is_pending_and_import_waits_for_apply(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "TBMT-03-09.xlsx"
    source.write_bytes(b"source-a")
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(
        gui,
        "detect_source_type",
        lambda path: _source_detection(path, source_sha),
    )
    monkeypatch.setattr(
        gui.QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(source), "Excel"),
    )

    window._choose_bid_radar_file()

    assert window._bid_radar_pending_source is not None
    assert window._bid_radar_active_source is None
    assert window.bid_radar_source_action_button.text() == "DÙNG FILE NÀY"
    assert not window.bid_radar_import_button.isEnabled()


def test_initial_source_apply_resets_workspace_and_preserves_filters(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "TBMT-03-09.xlsx"
    source.write_bytes(b"source-a")
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(gui, "detect_source_type", lambda path: _source_detection(path, source_sha))
    monkeypatch.setattr(gui.QFileDialog, "getOpenFileName", lambda *args, **kwargs: (str(source), "Excel"))
    window._choose_bid_radar_file()
    window.bid_radar_min_budget.setText("500000000")
    window.bid_radar_include.setText("Mạng")
    window._render_bid_radar_result(_fake_result(path=source, source_type="TBMT", source_sha256=source_sha))
    window.bid_radar_table.selectRow(0)
    window._set_active_bid_radar_item(window._bid_radar_rows[0].item)

    window.apply_bid_radar_source()

    assert window._bid_radar_active_source is not None
    assert window._bid_radar_active_source.path == source.resolve()
    assert window.bid_radar_table.rowCount() == 0
    assert window.active_tender_context is None
    assert window.bid_radar_min_budget.text() == "500000000"
    assert window.bid_radar_include.text() == "Mạng"
    assert window.bid_radar_import_button.isEnabled()
    assert "CHƯA CHẠY" in window.bid_radar_status.text()


def test_source_switch_cancel_preserves_active_workspace(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source_a = tmp_path / "TBMT-03-09.xlsx"
    source_b = tmp_path / "TBMT-04-09.xlsx"
    source_a.write_bytes(b"source-a")
    source_b.write_bytes(b"source-b")
    sha_a = hashlib.sha256(source_a.read_bytes()).hexdigest()
    sha_b = hashlib.sha256(source_b.read_bytes()).hexdigest()
    detections = {source_a: _source_detection(source_a, sha_a), source_b: _source_detection(source_b, sha_b)}
    monkeypatch.setattr(gui, "detect_source_type", lambda path: detections[Path(path).resolve()])
    monkeypatch.setattr(gui.QFileDialog, "getOpenFileName", lambda *args, **kwargs: (str(source_b), "Excel"))
    window.bid_radar_path.setText(str(source_a))
    window._render_bid_radar_result(_fake_result(path=source_a, source_type="TBMT", source_sha256=sha_a))
    window._set_active_bid_radar_item(window._bid_radar_rows[0].item)
    window._bid_radar_active_source = window._source_session_identity(source_a, sha_a, SourceType.TBMT)
    window.bid_radar_table.selectRow(0)
    monkeypatch.setattr(gui.QMessageBox, "question", lambda *args, **kwargs: gui.QMessageBox.StandardButton.Cancel)

    window._choose_bid_radar_file()

    assert window._bid_radar_active_source.path == source_a.resolve()
    assert window._bid_radar_pending_source.path == source_b.resolve()
    assert window.bid_radar_table.rowCount() == 1
    assert window.active_tender_context is not None


def test_source_switch_confirm_resets_workspace_and_preserves_filters(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source_a = tmp_path / "TBMT-03-09.xlsx"
    source_b = tmp_path / "TBMT-04-09.xlsx"
    source_a.write_bytes(b"source-a")
    source_b.write_bytes(b"source-b")
    sha_a = hashlib.sha256(source_a.read_bytes()).hexdigest()
    sha_b = hashlib.sha256(source_b.read_bytes()).hexdigest()
    detections = {source_a: _source_detection(source_a, sha_a), source_b: _source_detection(source_b, sha_b)}
    monkeypatch.setattr(gui, "detect_source_type", lambda path: detections[Path(path).resolve()])
    monkeypatch.setattr(gui.QFileDialog, "getOpenFileName", lambda *args, **kwargs: (str(source_b), "Excel"))
    window.bid_radar_path.setText(str(source_a))
    window._render_bid_radar_result(_fake_result(path=source_a, source_type="TBMT", source_sha256=sha_a))
    window._set_active_bid_radar_item(window._bid_radar_rows[0].item)
    window._bid_radar_active_source = window._source_session_identity(source_a, sha_a, SourceType.TBMT)
    window.bid_radar_min_budget.setText("500000000")
    window.bid_radar_include.setText("Mạng")
    monkeypatch.setattr(gui.QMessageBox, "question", lambda *args, **kwargs: gui.QMessageBox.StandardButton.Yes)

    window._choose_bid_radar_file()
    window.apply_bid_radar_source()

    assert window._bid_radar_active_source.path == source_b.resolve()
    assert window.bid_radar_table.rowCount() == 0
    assert window.active_tender_context is None
    assert window.bid_radar_inspector_text.toPlainText().startswith("Chưa chọn cơ hội.")
    assert window.bid_radar_min_budget.text() == "500000000"
    assert window.bid_radar_include.text() == "Mạng"


def test_same_filename_with_changed_hash_is_pending_switch(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "TBMT-same.xlsx"
    source.write_bytes(b"source-a")
    sha_a = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(gui, "detect_source_type", lambda path: _source_detection(path, hashlib.sha256(Path(path).read_bytes()).hexdigest()))
    window.bid_radar_path.setText(str(source))
    window._bid_radar_active_source = window._source_session_identity(source, sha_a, SourceType.TBMT)
    source.write_bytes(b"source-b")
    monkeypatch.setattr(gui.QFileDialog, "getOpenFileName", lambda *args, **kwargs: (str(source), "Excel"))

    window._choose_bid_radar_file()

    assert window._bid_radar_pending_source.source_sha256 != sha_a
    assert window.bid_radar_source_action_button.text() == "CHUYỂN SANG FILE NÀY"


def test_import_uses_active_source_not_pending_source(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source_a = tmp_path / "TBMT-03-09.xlsx"
    source_b = tmp_path / "TBMT-04-09.xlsx"
    source_a.write_bytes(b"source-a")
    source_b.write_bytes(b"source-b")
    sha_a = hashlib.sha256(source_a.read_bytes()).hexdigest()
    sha_b = hashlib.sha256(source_b.read_bytes()).hexdigest()
    monkeypatch.setattr(gui, "detect_source_type", lambda path: _source_detection(Path(path), sha_a if Path(path).resolve() == source_a.resolve() else sha_b))
    window._bid_radar_active_source = window._source_session_identity(source_a, sha_a, SourceType.TBMT)
    window._bid_radar_pending_source = window._source_session_identity(source_b, sha_b, SourceType.TBMT)
    window.bid_radar_path.setText(str(source_b))
    captured: dict[str, object] = {}

    def fake_submit(function, *args, **kwargs) -> None:
        captured["args"] = args

    monkeypatch.setattr(window, "_submit", fake_submit)
    monkeypatch.setattr(gui, "detect_source_type", lambda path: _source_detection(Path(path), sha_a))

    window.start_bid_radar_import()

    assert captured["args"][1] == source_a.resolve()


def test_pending_source_staleness_is_revalidated_before_apply(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "TBMT-stale.xlsx"
    source.write_bytes(b"source-a")
    sha_a = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(gui, "detect_source_type", lambda path: _source_detection(Path(path), sha_a))
    monkeypatch.setattr(gui.QFileDialog, "getOpenFileName", lambda *args, **kwargs: (str(source), "Excel"))
    window._choose_bid_radar_file()
    source.write_bytes(b"source-b")
    refreshed_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(gui, "detect_source_type", lambda path: _source_detection(Path(path), refreshed_sha))

    window.apply_bid_radar_source()

    assert window._bid_radar_active_source is None
    assert window._bid_radar_pending_source.source_sha256 == refreshed_sha


def test_same_exact_source_reports_in_use_and_does_not_reset(
    window: QICrawlerWindow,
    tmp_path: Path,
) -> None:
    source = tmp_path / "TBMT-same.xlsx"
    source.write_bytes(b"source")
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    window._bid_radar_active_source = window._source_session_identity(source, source_sha, SourceType.TBMT)
    window._bid_radar_pending_source = window._source_session_identity(source, source_sha, SourceType.TBMT)
    window._render_bid_radar_source_session()

    assert window.bid_radar_source_action_button.text() == "ĐANG SỬ DỤNG"
    assert not window.bid_radar_source_action_button.isEnabled()


@pytest.mark.parametrize("review_state", ["UNREVIEWED", "REJECTED", "NEEDS_REVIEW"])
def test_workspace_handoff_button_requires_confirmed_review(
    window: QICrawlerWindow, review_state: str
) -> None:
    window._render_bid_radar_result(_fake_result(review_state=review_state))
    window.bid_radar_table.selectRow(0)

    assert hasattr(window, "bid_radar_workspace_button")
    assert not window.bid_radar_workspace_button.isEnabled()


def test_confirm_action_makes_workspace_handoff_eligible(window: QICrawlerWindow) -> None:
    window._render_bid_radar_result(_fake_result())
    window.bid_radar_table.selectRow(0)
    window._set_active_bid_radar_item(window._bid_radar_rows[0].item)

    window._render_bid_radar_review(0, "CONFIRMED")

    assert window.bid_radar_workspace_button.isEnabled()


def test_workspace_handoff_click_delegates_item_without_review_state(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window._render_bid_radar_result(_fake_result(review_state="CONFIRMED"))
    window.bid_radar_table.selectRow(0)
    window._set_active_bid_radar_item(window._bid_radar_rows[0].item)
    captured: dict[str, object] = {}

    def fake_submit(function, *args, **kwargs) -> None:
        captured["function"] = function
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(window, "_submit", fake_submit)
    window.start_bid_radar_workspace_handoff()

    assert captured["function"] is gui.run_bid_radar_workspace_handoff
    assert captured["args"] == (window.config, window._bid_radar_rows[0].item)
    assert len(captured["args"]) == 2


def test_tbmt_workspace_handoff_success_prefills_exact_case_and_revision(
    window: QICrawlerWindow,
) -> None:
    result = SimpleNamespace(
        source_type=SimpleNamespace(value="TBMT"),
        case_id="IB2600463290",
        release_raw_id="IB2600463290-01",
        release_id=9,
        human_link_required=False,
        disposition=SimpleNamespace(value="CREATED_EXACT_RELEASE"),
    )

    window._render_bid_radar_workspace_handoff(result)

    assert window.navigation.currentRow() == 4
    assert window.workspace_case_id.text() == "IB2600463290"
    assert window.workspace_release_id.text() == "IB2600463290-01"
    assert window._workspace_release_record_id == 9
    assert window._workspace_opened_case_id == "IB2600463290"
    assert window._workspace_opened_release_id == "IB2600463290-01"


def test_khmt_workspace_handoff_success_prefills_provisional_case(
    window: QICrawlerWindow,
) -> None:
    result = SimpleNamespace(
        source_type=SimpleNamespace(value="KHMT"),
        case_id="PL2600000001-00",
        release_raw_id=None,
        release_id=None,
        human_link_required=True,
        disposition=SimpleNamespace(value="CREATED_PROVISIONAL_CASE"),
    )

    window._render_bid_radar_workspace_handoff(result)

    assert window.navigation.currentRow() == 4
    assert window.workspace_case_id.text() == "PL2600000001-00"
    assert window.workspace_release_id.text() == ""
    assert window._workspace_release_record_id is None
    assert window._workspace_opened_case_id == "PL2600000001-00"
    assert window._workspace_opened_release_id is None
    assert "Chưa có IB exact revision" in window.workspace_status.text()


def test_failed_workspace_handoff_keeps_radar_selection(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window._render_bid_radar_result(_fake_result(review_state="CONFIRMED"))
    window.bid_radar_table.selectRow(0)
    selected_item = window._bid_radar_rows[0].item

    monkeypatch.setattr(gui.QMessageBox, "critical", lambda *args, **kwargs: None)
    window._worker_error(
        window.bid_radar_workspace_button,
        ValueError("latest persisted CONFIRMED review required"),
        window.bid_radar_progress,
        window.bid_radar_status,
    )

    assert window.bid_radar_table.currentRow() == 0
    assert window._bid_radar_rows[0].item is selected_item


def test_review_requires_reviewer(window: QICrawlerWindow) -> None:
    window._render_bid_radar_result(_fake_result())
    window.bid_radar_table.selectRow(0)
    window._set_active_bid_radar_item(window._bid_radar_rows[0].item)
    window.start_bid_radar_review("CONFIRMED")

    assert "reviewer" in window.bid_radar_status.text().lower()


def test_review_delegates_to_candidate_review_service(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window._render_bid_radar_result(_fake_result())
    window.bid_radar_table.selectRow(0)
    window._set_active_bid_radar_item(window._bid_radar_rows[0].item)
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
    calls: list[tuple[object, dict[str, object]]] = []

    def fake_submit(function, *args, **kwargs) -> None:
        calls.append((function, kwargs))

    monkeypatch.setattr(window, "_submit", fake_submit)
    source = tmp_path / "khmt.xlsx"
    source.write_bytes(b"khmt-source")
    window.bid_radar_path.setText(str(source))
    window._bid_radar_loaded_source = source
    window._bid_radar_loaded_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
    window._bid_radar_active_source = window._source_session_identity(
        source,
        window._bid_radar_loaded_sha256,
        SourceType.KHMT,
    )
    window._bid_radar_items = (_fake_radar_item(),)
    window._bid_radar_load_result = SimpleNamespace(
        source_type=SimpleNamespace(value="KHMT"),
        source_path=source,
        source_sha256=window._bid_radar_loaded_sha256,
        items=window._bid_radar_items,
    )
    window.bid_radar_legal_button.setEnabled(True)

    window.start_bid_radar_export()
    window.start_bid_radar_legal_docx()

    assert [call[0] for call in calls] == [
        gui.run_bid_radar_export,
        gui.run_bid_radar_legal_docx,
    ]
    for _function, kwargs in calls:
        assert kwargs["source_path"] == source
        assert kwargs["expected_source_sha256"] == window._bid_radar_loaded_sha256


def test_switching_khmt_source_clears_stale_rows_and_blocks_export(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    item = _fake_radar_item("PL260001-00")
    source_a = tmp_path / "source-a.xlsx"
    source_b = tmp_path / "source-b.xlsx"
    source_a.write_bytes(b"a")
    source_b.write_bytes(b"b")
    window.bid_radar_path.setText(str(source_a))
    window._render_bid_radar_result(_fake_result(item, path=source_a))
    assert window.bid_radar_table.rowCount() == 1

    monkeypatch.setattr(
        gui.QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(source_b), "Excel KHMT (*.xlsx)"),
    )
    monkeypatch.setattr(
        gui.QMessageBox,
        "question",
        lambda *args, **kwargs: gui.QMessageBox.StandardButton.Yes,
    )
    captured: list[object] = []
    monkeypatch.setattr(window, "_submit", lambda function, *args, **kwargs: captured.append(function))

    window._choose_bid_radar_file()
    window._bid_radar_pending_source = window._source_session_identity(
        source_b,
        hashlib.sha256(source_b.read_bytes()).hexdigest(),
        SourceType.KHMT,
    )
    window.apply_bid_radar_source()
    window.start_bid_radar_export()

    assert window.bid_radar_path.text() == str(source_b)
    assert window.bid_radar_table.rowCount() == 0
    assert window._bid_radar_items == ()
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
    item = _fake_radar_item("PL260001-00")
    window.bid_radar_path.setText(str(source))
    window._render_bid_radar_result(
        _fake_result(item, path=source, source_sha256=source_sha)
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
            items=(),
            load_result=SimpleNamespace(source_type=SimpleNamespace(value="KHMT"), source_path=Path("khmt.xlsx"), source_sha256="a" * 64, items=()),
            rows=(),
            issues=(issue,),
            matched_count=0,
            indeterminate_count=0,
            nonmatched_count=0,
            total_examined=0,
            source_type=SimpleNamespace(value="KHMT"),
            source_path=Path("khmt.xlsx"),
            source_sha256="a" * 64,
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



def _a5_evidence_result() -> SimpleNamespace:
    result = _fake_result(_fake_radar_item("IB2600462391-00"), source_type="TBMT")
    result.rows = (
        SimpleNamespace(
            item=result.items[0],
            disposition="MATCH",
            reasons=("MATCH_BUDGET",),
            review_state="UNREVIEWED",
            criteria=(
                SimpleNamespace(
                    criterion="budget",
                    outcome="PASS",
                    reason_code="MATCH_BUDGET",
                    evidence=(
                        SimpleNamespace(
                            field="package_price",
                            observed_value="SUPPLIED-EVIDENCE-VALUE",
                            expected_values=("100",),
                            matched_terms=(),
                        ),
                    ),
                ),
            ),
        ),
    )
    return result


def test_bid_radar_has_calm_three_pane_desk_with_center_stretch(
    window: QICrawlerWindow,
) -> None:
    assert window.bid_radar_splitter.count() == 3
    assert window.bid_radar_selection_desk.objectName() == "bidRadarSelectionDesk"
    assert window.bid_radar_active_canvas.objectName() == "bidRadarActiveCanvas"
    assert window.bid_radar_inspector.objectName() == "bidRadarInspector"
    window.navigation.setCurrentRow(2)
    window.resize(1440, 900)
    window.show()
    QApplication.processEvents()
    left, center, right = window.bid_radar_splitter.sizes()
    assert center > left
    assert center > right


def test_bid_radar_filter_studio_is_collapsed_and_preserves_values(
    window: QICrawlerWindow,
) -> None:
    assert window.bid_radar_filter_editor.isHidden()
    window.bid_radar_min_budget.setText("500.000.000")
    window.bid_radar_province.setText("HCM")

    window.bid_radar_filter_toggle.click()
    assert not window.bid_radar_filter_editor.isHidden()
    window.bid_radar_filter_toggle.click()

    assert window.bid_radar_filter_editor.isHidden()
    assert window.bid_radar_min_budget.text() == "500.000.000"
    assert window.bid_radar_province.text() == "HCM"


def test_bid_radar_side_collapses_are_independent_and_preserve_selection(
    window: QICrawlerWindow,
) -> None:
    window._render_bid_radar_result(_fake_result())
    window.bid_radar_table.selectRow(0)
    assert window.bid_radar_table.currentRow() == 0

    window.bid_radar_selection_toggle.click()
    assert window.bid_radar_selection_desk.isHidden()
    assert not window.bid_radar_inspector.isHidden()
    assert window.bid_radar_table.currentRow() == 0

    window.bid_radar_inspector_toggle.click()
    assert window.bid_radar_inspector.isHidden()
    window.bid_radar_selection_toggle.click()
    assert not window.bid_radar_selection_desk.isHidden()
    assert window.bid_radar_table.currentRow() == 0


def test_bid_radar_context_is_neutral_until_a_filter_is_active(window: QICrawlerWindow) -> None:
    assert "CHƯA LỌC" in window.bid_radar_active_filter_context.text()
    assert "PHÙ HỢP" not in window.bid_radar_active_filter_context.text()

    window.bid_radar_min_budget.setText("1000000")
    assert "1.000.000" in window.bid_radar_active_filter_context.text()
    assert "CHƯA LỌC" not in window.bid_radar_active_filter_context.text()


def test_bid_radar_inspector_projects_supplied_structured_evidence(window: QICrawlerWindow) -> None:
    window._render_bid_radar_result(_a5_evidence_result())
    window.bid_radar_table.selectRow(0)
    text = window.bid_radar_inspector_text.toPlainText()

    assert "IB2600462391-00" in text
    assert "Gói thử nghiệm" in text
    assert "ĐẠT" in text
    assert "SUPPLIED-EVIDENCE-VALUE" in text
    assert "MATCH_BUDGET" not in text


def test_bid_radar_review_and_export_controls_remain_reachable(window: QICrawlerWindow) -> None:
    window._render_bid_radar_result(_fake_result())
    assert window.bid_radar_confirm_button.text() == "XÁC NHẬN CƠ HỘI"
    assert window.bid_radar_export_button.isVisible() or not window.isVisible()
    assert window.bid_radar_legal_button.isEnabled() is True
    assert not window.bid_radar_workspace_button.isEnabled()


def test_bid_radar_required_geometries_have_operable_regions(window: QICrawlerWindow) -> None:
    window.navigation.setCurrentRow(2)
    for width, height in ((1180, 680), (1440, 900)):
        window.resize(width, height)
        window.show()
        QApplication.processEvents()
        assert window.bid_radar_splitter.width() > 0
        sizes = window.bid_radar_splitter.sizes()
        assert sizes[0] > 0
        assert sizes[1] > 0
        if width >= 1400:
            assert sizes[2] > 0
        assert window.bid_radar_table.viewport().width() > 0
        assert window.bid_radar_import_button.width() > 0



def _show_bid_radar(window: QICrawlerWindow, width: int, height: int) -> None:
    window.navigation.setCurrentRow(2)
    window.resize(width, height)
    window.show()
    QApplication.processEvents()


def test_bid_radar_compact_mode_collapses_inspector_and_expands_center(
    window: QICrawlerWindow,
) -> None:
    _show_bid_radar(window, 1180, 680)

    assert window.bid_radar_selection_desk.isVisible()
    assert window.bid_radar_active_canvas.isVisible()
    assert window.bid_radar_inspector.isHidden()
    left, center, right = window.bid_radar_splitter.sizes()
    assert right == 0
    assert center > left
    assert center > 400


def test_bid_radar_compact_inspector_toggle_preserves_selection(window: QICrawlerWindow) -> None:
    window._render_bid_radar_result(_fake_result())
    window.bid_radar_table.selectRow(0)
    _show_bid_radar(window, 1180, 680)

    window.bid_radar_inspector_toggle.click()
    assert window.bid_radar_inspector.isVisible()
    assert window.bid_radar_table.currentRow() == 0

    window.bid_radar_inspector_toggle.click()
    assert window.bid_radar_inspector.isHidden()
    assert window.bid_radar_table.currentRow() == 0


def test_bid_radar_side_panels_disable_horizontal_scrolling(window: QICrawlerWindow) -> None:
    assert (
        window.bid_radar_selection_scroll.horizontalScrollBarPolicy()
        == Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    )
    assert (
        window.bid_radar_inspector_scroll.horizontalScrollBarPolicy()
        == Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    )
    assert window.bid_radar_source_summary.wordWrap()
    assert window.bid_radar_inspector_text.lineWrapMode() != QTextEdit.LineWrapMode.NoWrap


def test_bid_radar_compact_collapse_does_not_recreate_filter_or_evidence(
    window: QICrawlerWindow,
) -> None:
    window.bid_radar_min_budget.setText("500.000.000")
    window._render_bid_radar_result(_a5_evidence_result())
    window.bid_radar_table.selectRow(0)
    before = window.bid_radar_inspector_text.toPlainText()

    _show_bid_radar(window, 1180, 680)
    window.bid_radar_inspector_toggle.click()
    assert window.bid_radar_inspector_text.toPlainText() == before
    assert window.bid_radar_min_budget.text() == "500.000.000"



def test_bid_radar_compact_mode_applies_when_page_is_opened_after_resize(
    window: QICrawlerWindow,
) -> None:
    window.resize(1180, 680)
    window.show()
    QApplication.processEvents()
    window.navigation.setCurrentRow(2)
    QApplication.processEvents()
    assert window.bid_radar_inspector.isHidden()


def test_schema_not_ready_offers_explicit_upgrade_with_database_identity(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(gui.QMessageBox, "critical", lambda *args, **kwargs: None)
    prompts: list[str] = []
    monkeypatch.setattr(
        gui.QMessageBox,
        "question",
        lambda _parent, title, message, *args, **kwargs: prompts.append(
            f"{title}\n{message}"
        ) or gui.QMessageBox.StandardButton.Cancel,
    )
    upgrade_calls: list[object] = []
    monkeypatch.setattr(
        window,
        "_submit",
        lambda function, *args, **kwargs: upgrade_calls.append(function),
    )

    window._worker_error(
        window.bid_radar_import_button,
        SchemaNotReady("Hay chay QI-Crawler db-upgrade"),
        window.bid_radar_progress,
        window.bid_radar_status,
    )

    assert prompts
    assert "CƠ SỞ DỮ LIỆU CẦN NÂNG CẤP" in prompts[0]
    assert "bid-radar.db" in prompts[0]
    assert "NÂNG CẤP CSDL" in prompts[0]
    assert upgrade_calls == []
    assert "NÂNG CẤP" in window.bid_radar_status.text()


def test_schema_not_ready_requires_confirmation_before_upgrade_submission(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(gui.QMessageBox, "critical", lambda *args, **kwargs: None)
    answers = iter(
        (
            gui.QMessageBox.StandardButton.Yes,
            gui.QMessageBox.StandardButton.Cancel,
        )
    )
    monkeypatch.setattr(gui.QMessageBox, "question", lambda *args, **kwargs: next(answers))
    submitted: list[tuple[object, tuple[object, ...], dict[str, object]]] = []
    monkeypatch.setattr(
        window,
        "_submit",
        lambda function, *args, **kwargs: submitted.append((function, args, kwargs)),
    )

    window._worker_error(
        window.bid_radar_import_button,
        SchemaNotReady("Hay chay QI-Crawler db-upgrade"),
        window.bid_radar_progress,
        window.bid_radar_status,
    )

    assert submitted == []


def test_database_upgrade_success_reports_verified_revision_backup_and_identity(
    window: QICrawlerWindow,
    tmp_path: Path,
) -> None:
    result = gui.DatabaseReadinessResult(
        database_path=tmp_path / "egp.db",
        revision="0020_add_tender_operational_revision_events",
        backup_path=tmp_path / "backups" / "egp-before.db",
    )

    window._render_database_upgrade_result(result)

    status = window.bid_radar_status.text()
    assert "Nâng cấp cơ sở dữ liệu hoàn tất" in status
    assert str(result.database_path) in status
    assert str(result.backup_path) in status
    assert result.revision in status
    assert "NHẬP / TÌM GÓI" in status


def test_database_upgrade_failure_retains_created_backup_path(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(gui.QMessageBox, "critical", lambda *args, **kwargs: None)
    error = RuntimeError("migration failed")
    error.backup_path = Path("backups/egp-before.db")
    window._database_upgrade_in_progress = True

    window._worker_error(
        window.bid_radar_import_button,
        error,
        window.bid_radar_progress,
        window.bid_radar_status,
    )

    assert str(error.backup_path) in window.bid_radar_status.text()

def test_database_upgrade_failure_is_user_readable_and_does_not_claim_success(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(gui.QMessageBox, "critical", lambda *args, **kwargs: None)
    window._database_upgrade_in_progress = True

    window._worker_error(
        window.bid_radar_import_button,
        RuntimeError("backup failed"),
        window.bid_radar_progress,
        window.bid_radar_status,
    )

    status = window.bid_radar_status.text()
    assert "Nâng cấp cơ sở dữ liệu thất bại" in status
    assert "backup failed" in status
    assert "hoàn tất" not in status

def test_schema_not_ready_confirmation_submits_existing_database_upgrade_seam(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(gui.QMessageBox, "critical", lambda *args, **kwargs: None)
    answers = iter(
        (
            gui.QMessageBox.StandardButton.Yes,
            gui.QMessageBox.StandardButton.Yes,
        )
    )
    monkeypatch.setattr(gui.QMessageBox, "question", lambda *args, **kwargs: next(answers))
    submitted: list[tuple[object, tuple[object, ...], dict[str, object]]] = []
    monkeypatch.setattr(
        window,
        "_submit",
        lambda function, *args, **kwargs: submitted.append((function, args, kwargs)),
    )

    window._worker_error(
        window.bid_radar_import_button,
        SchemaNotReady("Hay chay QI-Crawler db-upgrade"),
        window.bid_radar_progress,
        window.bid_radar_status,
    )

    assert len(submitted) == 1
    function, args, kwargs = submitted[0]
    assert function is gui.run_database_upgrade
    assert args == (window.config,)
    assert kwargs["long_operation"] is True


@pytest.mark.parametrize(
    ("raw", "expected"),
    (
        ("800000000", "800.000.000"),
        ("800.000.000", "800.000.000"),
        ("800,000,000", "800.000.000"),
        ("800 000 000", "800.000.000"),
        ("1000000000", "1.000.000.000"),
    ),
)
def test_bid_radar_money_display_groups_existing_money_inputs(
    window: QICrawlerWindow,
    raw: str,
    expected: str,
) -> None:
    window.bid_radar_min_budget.setText(raw)
    window.bid_radar_min_budget.editingFinished.emit()
    assert window.bid_radar_min_budget.text() == expected
    assert gui.format_vnd_amount(1000000000) == "1.000.000.000 VNĐ"


def test_bid_radar_money_display_preserves_blank_and_invalid_inputs(
    window: QICrawlerWindow,
) -> None:
    window.bid_radar_min_budget.setText("")
    window.bid_radar_min_budget.editingFinished.emit()
    assert window.bid_radar_min_budget.text() == ""
    window.bid_radar_min_budget.setText("800.00.000")
    window.bid_radar_min_budget.editingFinished.emit()
    assert window.bid_radar_min_budget.text() == "800.00.000"


def test_bid_radar_money_summary_and_budget_rows_are_explicitly_labeled(
    window: QICrawlerWindow,
) -> None:
    window.bid_radar_min_budget.setText("800000000")
    window.bid_radar_max_budget.setText("1000000000")
    window.bid_radar_min_budget.editingFinished.emit()
    window.bid_radar_max_budget.editingFinished.emit()
    summary = window.bid_radar_active_filter_context.text()
    assert "800.000.000" in summary
    assert "1.000.000.000" in summary
    assert "VNĐ" in summary
    assert window.bid_radar_min_budget.minimumWidth() >= 140
    assert window.bid_radar_max_budget.minimumWidth() >= 140
    assert [label.text() for label in window.findChildren(QLabel)].count("VNĐ") >= 2
