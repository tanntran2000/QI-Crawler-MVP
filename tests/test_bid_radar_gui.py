from __future__ import annotations

import hashlib
import os
from decimal import Decimal
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
    window.bid_radar_path.setText(str(source))
    monkeypatch.setattr(
        gui,
        "detect_source_type",
        lambda path: SourceTypeDetection(
            original_filename=source.name,
            source_sha256="a" * 64,
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
    captured: list[object] = []
    monkeypatch.setattr(window, "_submit", lambda function, *args, **kwargs: captured.append(function))

    window.start_bid_radar_import()

    assert captured == [gui.run_bid_radar_import_search]
    assert "Work Package tiếp theo" not in window.bid_radar_status.text()


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
    window.bid_radar_path.setText(str(source))
    monkeypatch.setattr(
        gui,
        "detect_source_type",
        lambda path: SourceTypeDetection(
            original_filename=source.name,
            source_sha256="b" * 64,
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
    window.bid_radar_path.setText(str(source))
    window.bid_radar_source_type.setCurrentIndex(1)
    window.bid_radar_reviewer.setText("Team Bid")
    detection = SourceTypeDetection(
        original_filename=source.name,
        source_sha256="d" * 64,
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
    window.bid_radar_path.setText(str(source))
    monkeypatch.setattr(
        gui,
        "detect_source_type",
        lambda path: SourceTypeDetection(
            original_filename=source.name,
            source_sha256="c" * 64,
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

    window.start_bid_radar_import()

    assert captured["function"] is gui.run_bid_radar_import_search
    assert captured["args"][0] is window.config
    assert captured["args"][1] == source
    assert captured["button"] is window.bid_radar_import_button


def test_filter_match_does_not_auto_confirm(window: QICrawlerWindow) -> None:
    window._render_bid_radar_result(_fake_result())

    assert window.bid_radar_table.item(0, 7).text() == "Chưa xem"
    assert window._bid_radar_rows[0].review_state != "CONFIRMED"


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

    window._render_bid_radar_review(0, "CONFIRMED")

    assert window.bid_radar_workspace_button.isEnabled()


def test_workspace_handoff_click_delegates_item_without_review_state(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window._render_bid_radar_result(_fake_result(review_state="CONFIRMED"))
    window.bid_radar_table.selectRow(0)
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
    window.start_bid_radar_review("CONFIRMED")

    assert "reviewer" in window.bid_radar_status.text().lower()


def test_review_delegates_to_candidate_review_service(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window._render_bid_radar_result(_fake_result())
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
    calls: list[tuple[object, dict[str, object]]] = []

    def fake_submit(function, *args, **kwargs) -> None:
        calls.append((function, kwargs))

    monkeypatch.setattr(window, "_submit", fake_submit)
    source = tmp_path / "khmt.xlsx"
    source.write_bytes(b"khmt-source")
    window.bid_radar_path.setText(str(source))
    window._bid_radar_loaded_source = source
    window._bid_radar_loaded_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
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
    captured: list[object] = []
    monkeypatch.setattr(window, "_submit", lambda function, *args, **kwargs: captured.append(function))

    window._choose_bid_radar_file()
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
