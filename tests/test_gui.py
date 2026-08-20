from __future__ import annotations

import os
import threading
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import (
    QByteArray,
    QCoreApplication,
    QEvent,
    QEventLoop,
    QSettings,
    Qt,
    QThreadPool,
    QTimer,
)
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QApplication, QGroupBox, QMessageBox

from qi_crawler import __version__, gui
from qi_crawler.config import AppConfig
from qi_crawler.crawler import ScanSummary
from qi_crawler.document_intake import (
    DocumentBatchResult,
    DocumentContentIdentity,
    DocumentIdentityMismatch,
    DocumentIntakeResult,
    DocumentManifestEntry,
    TenderDocumentManifest,
)
from qi_crawler.document_taxonomy import (
    ClassificationStatus,
    DocumentClassification,
    TenderDocumentType,
)
from qi_crawler.gui import FunctionWorker, QICrawlerWindow, _standalone_smoke_requested
from qi_crawler.gui_services import (
    DocumentExtractionInspection,
    EvidencePreview,
    HSMTFactDashboard,
    WorkspaceDocumentIntakeResult,
)
from qi_crawler.hsmt_facts import HSMTFactView
from qi_crawler.web_document_intake import WebDocumentIntakeSummary


@pytest.fixture(scope="module")
def application() -> QApplication:
    value = QApplication.instance() or QApplication([])
    yield value
    assert QThreadPool.globalInstance().waitForDone(5000)
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    value.processEvents()


@pytest.fixture
def config(tmp_path: Path) -> AppConfig:
    value = AppConfig()
    value.storage.database_url = f"sqlite:///{tmp_path / 'gui.db'}"
    value.storage.report_dir = tmp_path / "reports"
    value.storage.rejects_dir = tmp_path / "rejects"
    value.storage.document_dir = tmp_path / "documents"
    return value


@pytest.fixture
def settings(tmp_path: Path) -> QSettings:
    value = QSettings(str(tmp_path / "gui-settings.ini"), QSettings.Format.IniFormat)
    value.clear()
    return value


@pytest.fixture
def window(
    application: QApplication,
    config: AppConfig,
    settings: QSettings,
) -> QICrawlerWindow:
    widget = QICrawlerWindow(config, settings=settings)
    yield widget
    assert QThreadPool.globalInstance().waitForDone(5000)
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    application.processEvents()
    widget.close()
    widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def test_gui_imports_and_starts(window: QICrawlerWindow) -> None:
    assert window.windowTitle() == f"QI-CRAWLER v{__version__}"
    assert window.navigation.count() == 5
    assert window.pages.count() == 5
    assert [window.navigation.item(index).text() for index in range(5)] == [
        "THU THẬP",
        "Tìm kiếm",
        "Xuất TBMT",
        "HSMT / PHÂN TÍCH",
        "Nhật ký",
    ]


def test_collection_navigation_keeps_all_crawl_capabilities_reachable(
    window: QICrawlerWindow,
) -> None:
    assert window.collection_tabs.count() == 3
    assert [window.collection_tabs.tabText(index) for index in range(3)] == [
        "QUÉT DANH SÁCH",
        "CRAWL URL",
        "NGUỒN / ĐĂNG NHẬP",
    ]
    assert window.collection_tabs.widget(0) is window.collection_scan_page
    assert window.collection_tabs.widget(1) is window.collection_crawl_page
    assert window.collection_tabs.widget(2) is window.collection_login_page
    assert window.scan_button.parentWidget() is not None
    assert window.crawl_button.parentWidget() is not None
    assert window.login_button.parentWidget() is not None
    assert window.scan_advanced_options.title() == "TÙY CHỌN NÂNG CAO"


def test_window_uses_resizable_preferred_geometry(window: QICrawlerWindow) -> None:
    assert window.minimumWidth() == 1180
    assert window.minimumHeight() == 680
    assert window.maximumWidth() > window.minimumWidth()
    assert window.maximumHeight() > window.minimumHeight()


def test_window_restores_saved_geometry(
    config: AppConfig,
    settings: QSettings,
) -> None:
    original = QICrawlerWindow(config, settings=settings)
    original.resize(1240, 720)
    original.move(0, 0)
    original._save_window_geometry()

    restored = QICrawlerWindow(config, settings=settings)

    screen = QApplication.primaryScreen()
    assert settings.value("window/geometry", type=QByteArray)
    if screen is not None and screen.availableGeometry().width() >= 1240:
        assert restored.size() == original.size()
    else:
        assert restored.width() >= 1180
        assert restored.height() >= 680
    original.deleteLater()
    restored.deleteLater()


def test_invalid_saved_geometry_uses_safe_default(
    config: AppConfig,
    settings: QSettings,
    application: QApplication,
) -> None:
    settings.setValue("window/geometry", QByteArray(b"invalid-geometry"))
    window = QICrawlerWindow(config, settings=settings)
    screen = application.primaryScreen()

    assert window.width() >= 1180
    assert window.height() >= 680
    if screen is not None:
        assert window._geometry_is_usable(
            window.frameGeometry(),
            screen.availableGeometry(),
        )
    window.deleteLater()


def test_standalone_document_smoke_is_detected_before_qt_startup() -> None:
    assert _standalone_smoke_requested(["QI-Crawler.exe", "--smoke-test-documents"])
    assert not _standalone_smoke_requested(["QI-Crawler.exe"])


def test_scan_default_max_pages_is_three(window: QICrawlerWindow) -> None:
    assert window.scan_max_pages.value() == 3


def test_scan_source_selector_autofills_known_public_url(window: QICrawlerWindow) -> None:
    assert window.scan_source.currentText() == "Coteccons e-Bidding"
    assert window.scan_url.text() == "https://ebidding.coteccons.vn/Index"

    window.scan_source.setCurrentText("URL khác")

    assert window.scan_url.text() == ""


@pytest.mark.parametrize(
    ("url", "message"),
    [
        ("", "Vui lòng dán URL"),
        ("not-a-url", "URL phải bắt đầu"),
    ],
)
def test_scan_form_validation(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
    url: str,
    message: str,
) -> None:
    monkeypatch.setattr(
        window,
        "_submit",
        lambda *_args, **_kwargs: pytest.fail("invalid form must not submit a worker"),
    )
    window.scan_url.setText(url)

    window.start_scan()

    assert message in window.scan_status.text()


def test_scan_uses_existing_service_adapter(window: QICrawlerWindow, monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_submit(function, *args, **kwargs) -> None:
        captured["function"] = function
        captured["args"] = args
        captured["button"] = kwargs["button"]

    monkeypatch.setattr(window, "_submit", fake_submit)
    window.scan_url.setText("https://ebidding.coteccons.vn/Index")
    window.scan_max_pages.setValue(7)
    window.scan_keywords.setText("chong tham,son")

    window.start_scan()

    assert captured["function"] is gui.run_scan
    assert captured["args"] == (
        window.config,
        "https://ebidding.coteccons.vn/Index",
        7,
        "chong tham,son",
    )
    assert captured["button"] is window.scan_button


def test_worker_executes_outside_ui_thread(application: QApplication) -> None:
    ui_thread = threading.get_ident()
    loop = QEventLoop()
    observed: list[int] = []
    worker = FunctionWorker(threading.get_ident)
    worker.signals.finished.connect(lambda result: (observed.append(result), loop.quit()))
    worker.signals.error.connect(lambda _error: loop.quit())

    QThreadPool.globalInstance().start(worker)
    QTimer.singleShot(5000, loop.quit)
    loop.exec()
    QThreadPool.globalInstance().waitForDone(5000)

    assert observed
    assert observed[0] != ui_thread


def test_successful_worker_emits_one_finished_signal(application: QApplication) -> None:
    loop = QEventLoop()
    finished: list[object] = []
    errors: list[object] = []
    worker = FunctionWorker(lambda: "done", task_name="test_success")
    worker.signals.finished.connect(lambda result: (finished.append(result), loop.quit()))
    worker.signals.error.connect(lambda error: (errors.append(error), loop.quit()))

    QThreadPool.globalInstance().start(worker)
    QTimer.singleShot(5000, loop.quit)
    loop.exec()
    QThreadPool.globalInstance().waitForDone(5000)

    assert finished == ["done"]
    assert errors == []
    assert not worker.autoDelete()


def test_failed_worker_emits_one_error_signal(application: QApplication) -> None:
    loop = QEventLoop()
    finished: list[object] = []
    errors: list[object] = []

    def fail() -> None:
        raise RuntimeError("expected worker error")

    worker = FunctionWorker(fail, task_name="test_error")
    worker.signals.finished.connect(lambda result: (finished.append(result), loop.quit()))
    worker.signals.error.connect(lambda error: (errors.append(error), loop.quit()))

    QThreadPool.globalInstance().start(worker)
    QTimer.singleShot(5000, loop.quit)
    loop.exec()
    QThreadPool.globalInstance().waitForDone(5000)

    assert finished == []
    assert len(errors) == 1
    assert isinstance(errors[0], RuntimeError)
    assert not worker.autoDelete()


def _wait_until(predicate, timeout_ms: int = 3000) -> None:
    loop = QEventLoop()

    def check() -> None:
        if predicate():
            loop.quit()
        else:
            QTimer.singleShot(10, check)

    check()
    QTimer.singleShot(timeout_ms, loop.quit)
    loop.exec()
    assert predicate()


def test_long_job_disables_button_and_shows_progress(
    window: QICrawlerWindow,
) -> None:
    release = threading.Event()

    window._submit(
        lambda: (release.wait(5), "ok")[1],
        on_success=lambda _result: None,
        button=window.scan_button,
        progress=window.scan_progress,
    )

    assert not window.scan_button.isEnabled()
    assert not window.scan_progress.isHidden()

    release.set()
    _wait_until(lambda: window.scan_button.isEnabled())

    assert window.scan_button.isEnabled()
    assert window.scan_progress.isHidden()
    assert window._active_jobs == []


def test_window_defers_close_until_active_worker_finishes(window: QICrawlerWindow) -> None:
    release = threading.Event()
    window._submit(
        lambda: (release.wait(5), "done")[1],
        on_success=lambda _result: None,
        button=window.scan_button,
        progress=window.scan_progress,
    )

    close_event = QCloseEvent()
    window.closeEvent(close_event)

    assert not close_event.isAccepted()
    release.set()
    _wait_until(lambda: window._active_jobs == [])


def _scan_summary() -> ScanSummary:
    return ScanSummary(
        run_id=1,
        discovered=1,
        matched=1,
        queued=1,
        limited=0,
        new=1,
        existing=0,
        success=1,
        failed=0,
        pending=0,
        skipped=0,
        pages_scanned=1,
    )


def test_scan_running_blocks_single_crawl(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    release = threading.Event()
    scan_started = threading.Event()

    def run_blocking_scan(*_args) -> ScanSummary:
        scan_started.set()
        release.wait(5)
        return _scan_summary()

    monkeypatch.setattr(gui, "run_scan", run_blocking_scan)
    window.scan_url.setText("https://ebidding.coteccons.vn/Index")
    window.crawl_url.setText("https://ebidding.coteccons.vn/Index/ChiTiet/2608121")

    window.start_scan()
    _wait_until(scan_started.is_set)
    window.start_crawl()

    assert window._active_long_operation == "scan"
    assert window.crawl_status.text() == (
        "QI-Crawler đang xử lý một tác vụ. Vui lòng chờ hoàn tất."
    )
    assert all(not button.isEnabled() for button in window._long_operation_buttons)

    release.set()
    _wait_until(lambda: window._active_long_operation is None)
    assert window._active_long_operation is None
    assert all(button.isEnabled() for button in window._long_operation_buttons)


def test_crawl_running_blocks_export(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    release = threading.Event()
    crawl_started = threading.Event()

    def run_blocking_crawl(*_args) -> tuple[int, int, None]:
        crawl_started.set()
        release.wait(5)
        return 1, 0, None

    monkeypatch.setattr(gui, "run_single_crawl", run_blocking_crawl)
    window.crawl_url.setText("https://ebidding.coteccons.vn/Index/ChiTiet/2608121")

    window.start_crawl()
    _wait_until(crawl_started.is_set)
    window.start_export()

    assert window._active_long_operation == "single_crawl"
    assert window.export_status.text() == (
        "QI-Crawler đang xử lý một tác vụ. Vui lòng chờ hoàn tất."
    )

    release.set()
    _wait_until(lambda: window._active_long_operation is None)
    assert window._active_long_operation is None
    assert all(button.isEnabled() for button in window._long_operation_buttons)


def test_long_operation_error_releases_all_controls(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    release = threading.Event()
    crawl_started = threading.Event()

    def run_failing_crawl(*_args) -> None:
        crawl_started.set()
        release.wait(5)
        raise RuntimeError("expected")

    monkeypatch.setattr(gui, "run_single_crawl", run_failing_crawl)
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args: None)
    window.crawl_url.setText("https://ebidding.coteccons.vn/Index/ChiTiet/2608121")

    window.start_crawl()
    _wait_until(crawl_started.is_set)
    assert all(not button.isEnabled() for button in window._long_operation_buttons)

    release.set()
    _wait_until(lambda: window._active_long_operation is None)

    assert window._active_long_operation is None
    assert window._active_jobs == []
    assert window.crawl_progress.isHidden()
    assert all(button.isEnabled() for button in window._long_operation_buttons)


def test_submit_returns_to_ui_thread_and_clears_busy_state(window: QICrawlerWindow) -> None:
    ui_thread = threading.get_ident()
    observed: list[tuple[int, int]] = []

    def on_success(worker_thread: int) -> None:
        observed.append((worker_thread, threading.get_ident()))

    window._submit(
        threading.get_ident,
        on_success=on_success,
        button=window.scan_button,
        progress=window.scan_progress,
        status=window.scan_status,
        task_name="test_ui_delivery",
    )

    _wait_until(lambda: window.scan_button.isEnabled() and bool(observed))

    assert observed[0][0] != ui_thread
    assert observed[0][1] == ui_thread
    assert window.scan_progress.isHidden()
    assert window._active_jobs == []


def test_scan_success_is_rendered_in_vietnamese(window: QICrawlerWindow) -> None:
    summary = ScanSummary(
        run_id=7,
        discovered=25,
        matched=25,
        queued=25,
        limited=0,
        new=10,
        existing=15,
        success=25,
        failed=0,
        pending=0,
        skipped=0,
        pages_scanned=5,
    )

    window._render_scan_result(summary)

    assert window.scan_metrics["pages_scanned"].text() == "5"
    assert window.scan_metrics["discovered"].text() == "25"
    assert window.scan_metrics["new"].text() == "10"
    assert window.scan_metrics["existing"].text() == "15"
    assert window.scan_metrics["success"].text() == "25"
    assert "Quét hoàn tất" in window.scan_status.text()


def test_worker_error_renders_friendly_message(window: QICrawlerWindow, monkeypatch) -> None:
    messages: list[str] = []
    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda _parent, _title, message: messages.append(message),
    )

    window._worker_error(
        window.scan_button,
        RuntimeError("technical detail"),
        window.scan_progress,
        window.scan_status,
    )

    assert messages == ["Không thể hoàn tất thao tác. Dữ liệu không bị ghi sai."]
    assert "technical detail" in window.log_output.toPlainText()
    assert "technical detail" not in window.statusBar().currentMessage()
    assert window.scan_button.isEnabled()
    assert window.scan_progress.isHidden()
    assert "Không thể hoàn tất" in window.scan_status.text()


def test_human_required_dialog_is_friendly(window: QICrawlerWindow, monkeypatch) -> None:
    messages: list[tuple[str, str]] = []
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, title, message: messages.append((title, message)),
    )

    window.show_human_required("HTTP 403")

    assert messages[0][0] == "Cần người dùng xử lý"
    assert "CAPTCHA/OTP" in messages[0][1]
    assert "không vượt" in messages[0][1]
    assert "HTTP 403" in window.log_output.toPlainText()


def test_structured_diagnostic_log_redacts_and_copies_ai_report(
    window: QICrawlerWindow,
) -> None:
    try:
        raise RuntimeError(
            "Authorization: Bearer secret-auth Cookie: session=secret-cookie; "
            "password=secret-password otp=123456 api_key=secret-api"
        )
    except RuntimeError as error:
        window._append_log(
            "Quét lỗi: Authorization: Bearer secret-auth "
            "session_token=secret-session password=secret-password",
            level="ERROR",
            component="crawler",
            operation="scan",
            status="FAILED",
            error_code="SCAN_FAILED",
            run_id=17,
            package_id="IB2600000001",
            document_id=9,
            exception=error,
        )

    event = window._diagnostic_events[-1]
    raw = window.log_raw_output.toPlainText()
    assert window.log_events_table.rowCount() == 1
    assert event.level == "ERROR"
    assert event.operation == "scan"
    assert event.exception_type == "RuntimeError"
    assert "[REDACTED]" in raw
    for secret in (
        "secret-auth",
        "secret-cookie",
        "secret-password",
        "123456",
        "secret-api",
        "secret-session",
    ):
        assert secret not in raw

    window.copy_diagnostic_for_ai()

    report = QApplication.clipboard().text()
    assert "QI-CRAWLER DIAGNOSTIC REPORT" in report
    assert "Operation: scan" in report
    assert "Package: IB2600000001" in report
    assert "Document: 9" in report
    assert "Recent relevant events:" in report
    assert "[REDACTED]" in report
    assert "secret-auth" not in report


def test_structured_diagnostic_log_refreshes_selected_event(window: QICrawlerWindow) -> None:
    window._append_log("Quét danh sách hoàn tất.", operation="scan")
    window._append_log(
        "Cần người dùng xử lý.",
        level="WARNING",
        operation="access_check",
        status="HUMAN_REQUIRED",
    )

    window.log_events_table.selectRow(0)

    assert "Thao tác: scan" in window.log_output.toPlainText()
    assert '"operation": "scan"' in window.log_raw_output.toPlainText()
    assert window.copy_diagnostic_button.isEnabled()


def test_export_open_action_can_be_mocked_safely(
    window: QICrawlerWindow,
    monkeypatch,
    tmp_path: Path,
) -> None:
    path = tmp_path / "TBMT.xlsx"
    result = SimpleNamespace(
        output=path,
        exported_records=3,
        warning_records=1,
    )
    opened: list[Path] = []
    monkeypatch.setattr(gui, "open_path", lambda value: opened.append(value) or True)

    window._render_export_result(result)
    window.open_export()

    assert window.export_path.text() == str(path)
    assert window.open_export_button.isEnabled()
    assert opened == [path]


def test_single_crawl_returns_from_busy_state(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(gui, "run_single_crawl", lambda _config, _url: (1, 0, None))
    window.crawl_url.setText("https://ebidding.coteccons.vn/Index/ChiTiet/2608121")

    window.start_crawl()

    assert not window.crawl_button.isEnabled()
    _wait_until(lambda: window.crawl_button.isEnabled())
    assert window.crawl_progress.isHidden()
    assert "Hoàn tất: thành công 1, lỗi 0." == window.crawl_status.text()


def test_export_returns_from_busy_state(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    output = tmp_path / "TBMT.xlsx"
    monkeypatch.setattr(
        gui,
        "run_export",
        lambda _config, *, snapshot=False: SimpleNamespace(
            output=output,
            exported_records=2,
            warning_records=0,
        ),
    )

    window.start_export()

    assert not window.export_button.isEnabled()
    _wait_until(lambda: window.export_button.isEnabled())
    assert window.export_progress.isHidden()
    assert window.export_path.text() == str(output)
    assert "Đã xuất: 2" in window.export_status.text()


def test_export_snapshot_uses_existing_service_with_snapshot_flag(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    output = tmp_path / "archive" / "2026" / "2026-08" / "TBMT_2026-08-16_1030_run_7.xlsx"
    calls: list[bool] = []

    def export(_config: AppConfig, *, snapshot: bool = False) -> SimpleNamespace:
        calls.append(snapshot)
        return SimpleNamespace(output=output, exported_records=1, warning_records=0)

    monkeypatch.setattr(gui, "run_export", export)

    window.start_export_snapshot()

    _wait_until(lambda: window.export_snapshot_button.isEnabled())
    assert calls == [True]
    assert window.export_path.text() == str(output)
    assert window.export_button.text() == "XUẤT / CẬP NHẬT BẢN MỚI NHẤT"
    assert window.open_export_button.text() == "MỞ BÁO CÁO"


def test_export_failure_returns_from_busy_state(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    messages: list[str] = []

    def fail(_config: AppConfig, *, snapshot: bool = False) -> None:
        raise RuntimeError("expected export failure")

    monkeypatch.setattr(gui, "run_export", fail)
    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda _parent, _title, message: messages.append(message),
    )

    window.start_export()

    assert not window.export_button.isEnabled()
    _wait_until(lambda: window.export_button.isEnabled())
    assert window.export_progress.isHidden()
    assert messages == ["Không thể hoàn tất thao tác. Dữ liệu không bị ghi sai."]
    assert "Không thể hoàn tất" in window.export_status.text()


def _document_result(path: Path) -> DocumentBatchResult:
    return DocumentBatchResult(
        (
            DocumentIntakeResult(
                outcome="IMPORTED",
                document_id=7,
                original_filename="HSMT.pdf",
                stored_path=path,
                document_type="E_HSMT",
                mime_type="application/pdf",
                file_size=10,
                sha256="a" * 64,
                version=1,
                tender_id=10,
                tender_identifier="IB2600000001-00",
                identity_status="VERIFIED_LINKED",
                file_format="PDF",
                classification_status="CANDIDATE",
            ),
        )
    )


def _document_manifest(path: Path) -> TenderDocumentManifest:
    return TenderDocumentManifest(
        tender_id=10,
        tender_identifier="IB2600000001-00",
        tender_title="Cung cấp thiết bị mạng",
        source="egp",
        identity_status="VERIFIED_LINKED",
        documents=(
            DocumentManifestEntry(
                document_id=7,
                document_type="E_HSMT",
                file_format="PDF",
                template_code="4",
                package_type="Hàng hóa",
                selection_method=None,
                classification_status="VERIFIED",
                filename="HSMT.pdf",
                sha256="a" * 64,
                version=1,
                source="manual_upload",
                status="VERIFIED_LINKED",
                stored_path=path,
                uploaded_at=datetime.now(UTC),
            ),
            DocumentManifestEntry(
                document_id=8,
                document_type="BOQ_BOM",
                file_format="XLSX",
                template_code=None,
                package_type="Hàng hóa",
                selection_method=None,
                classification_status="CANDIDATE",
                filename="BOQ.xlsx",
                sha256="b" * 64,
                version=2,
                source="web",
                status="VERIFIED_LINKED",
                stored_path=path,
                uploaded_at=datetime.now(UTC),
            ),
        ),
    )


def test_document_page_uses_existing_intake_service_and_renders_success(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"source")
    stored = tmp_path / "documents" / "unlinked" / ("a" * 64) / "HSMT.pdf"
    captured: list[tuple[Path, str, str, str]] = []

    def fake_intake(
        _config: AppConfig,
        path: Path,
        tender: str,
        name: str,
        uploaded_by: str,
    ) -> DocumentBatchResult:
        captured.append((path, tender, name, uploaded_by))
        return _document_result(stored)

    monkeypatch.setattr(gui, "run_document_intake", fake_intake)
    window.document_path.setText(str(source))
    window.document_tender.setText("IB2600000001-00")
    window.document_name.setText("HSMT bản phát hành")

    window.start_document_intake()

    assert not window.document_import_button.isEnabled()
    _wait_until(lambda: window.document_import_button.isEnabled())
    assert captured == [
        (source, "IB2600000001-00", "HSMT bản phát hành", "")
    ]
    assert "Đã nhập tài liệu" in window.document_status.text()
    assert "Mã gói: IB2600000001-00" in window.document_status.text()
    assert "Identity: Đúng gói" in window.document_status.text()
    assert "Loại tài liệu: Hồ sơ mời thầu qua mạng" in window.document_status.text()
    assert window.document_classification_status.text() == "Nhận diện sơ bộ"
    assert window.document_confirm_type_button.isEnabled()
    assert "SHA-256" not in window.document_status.text()
    assert window.last_document_path == stored
    assert window.open_document_button.isEnabled()
    assert window.open_document_folder_button.isEnabled()
    assert window.document_progress.isHidden()
    assert window._active_long_operation is None


def test_content_verified_document_is_not_rendered_as_mismatch(
    window: QICrawlerWindow,
    tmp_path: Path,
) -> None:
    original = _document_result(tmp_path / "HSMT.pdf").results[0]
    batch = DocumentBatchResult(
        (
            replace(
                original,
                identity_status="DOCUMENT_VERIFIED",
                raw_notice_id="IB2500585490-00",
                base_notice_id="IB2500585490",
                notice_revision="00",
                identity_source="DOCUMENT_CONTENT",
                identity_match_status="SAME_TENDER",
            ),
        )
    )

    window._render_document_result(batch)

    assert "xác thực từ nội dung" in window.document_status.text()
    assert "Revision: 00" in window.document_status.text()
    assert "KHÔNG KHỚP" not in window.document_status.text()
    assert window.document_confirm_type_button.isEnabled()


def test_different_document_package_requests_confirmation_without_mutating_active_workspace(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "other-package.pdf"
    source.write_bytes(b"source")
    window._render_document_workspace(_document_manifest(tmp_path / "A.pdf"))
    window.document_path.setText(str(source))
    monkeypatch.setattr(
        gui,
        "extract_document_identity",
        lambda _path: DocumentContentIdentity(
            raw_notice_id="IB2600163730-00",
            base_notice_id="IB2600163730",
            revision="00",
            identity_source="DOCUMENT_CONTENT",
            status="FOUND",
        ),
    )
    monkeypatch.setattr(
        window,
        "_confirm_document_workspace_switch",
        lambda *_args: "cancel",
    )
    called: list[Path] = []
    monkeypatch.setattr(gui, "run_document_intake", lambda *_args: called.append(source))

    window.start_document_intake()

    assert window._document_workspace_tender == "IB2600000001-00"
    assert window.document_table.rowCount() == 2
    assert called == []


def test_same_package_different_revision_stays_in_current_workspace(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "revision-01.pdf"
    source.write_bytes(b"source")
    window._render_document_workspace(_document_manifest(tmp_path / "A.pdf"))
    window.document_path.setText(str(source))
    captured: list[str] = []
    monkeypatch.setattr(
        gui,
        "extract_document_identity",
        lambda _path: DocumentContentIdentity(
            raw_notice_id="IB2600000001-01",
            base_notice_id="IB2600000001",
            revision="01",
            identity_source="DOCUMENT_CONTENT",
            status="FOUND",
        ),
    )
    monkeypatch.setattr(
        window,
        "_confirm_document_workspace_switch",
        lambda *_args: pytest.fail("same base must not request a workspace switch"),
    )
    monkeypatch.setattr(
        gui,
        "run_document_intake",
        lambda _config, _path, tender, *_args: captured.append(tender)
        or _document_result(tmp_path / "stored.pdf"),
    )

    window.start_document_intake()

    _wait_until(lambda: window.document_import_button.isEnabled())
    assert captured == ["IB2600000001-00"]
    assert window._document_workspace_tender == "IB2600000001-00"


def test_confirmed_document_package_switch_opens_workspace_then_intakes_into_it(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "other-package.pdf"
    source.write_bytes(b"source")
    manifest_b = replace(
        _document_manifest(tmp_path / "B.pdf"),
        tender_id=20,
        tender_identifier="IB2600163730",
        tender_title="Gói B",
        documents=(),
    )
    stored = tmp_path / "documents" / "team_bid" / "IB2600163730" / "hash" / "HSMT.pdf"
    result_b = replace(
        _document_result(stored).results[0],
        tender_id=20,
        tender_identifier="IB2600163730",
        raw_notice_id="IB2600163730-00",
        base_notice_id="IB2600163730",
        notice_revision="00",
        identity_status="DOCUMENT_VERIFIED",
        identity_match_status="SAME_TENDER",
    )
    captured: list[str] = []
    window._render_document_workspace(_document_manifest(tmp_path / "A.pdf"))
    window.document_path.setText(str(source))
    window.last_document_id = 7
    monkeypatch.setattr(
        gui,
        "extract_document_identity",
        lambda _path: DocumentContentIdentity(
            raw_notice_id="IB2600163730-00",
            base_notice_id="IB2600163730",
            revision="00",
            identity_source="DOCUMENT_CONTENT",
            status="FOUND",
        ),
    )
    monkeypatch.setattr(window, "_confirm_document_workspace_switch", lambda *_args: "switch")
    def intake(
        _config: AppConfig,
        _path: Path,
        tender: str,
        *_args: str,
    ) -> WorkspaceDocumentIntakeResult:
        captured.append(tender)
        return WorkspaceDocumentIntakeResult(manifest_b, DocumentBatchResult((result_b,)))

    monkeypatch.setattr(gui, "run_workspace_document_intake", intake)
    window.start_document_intake()

    _wait_until(lambda: window.document_import_button.isEnabled())
    assert captured == ["IB2600163730"]
    assert window._document_workspace_tender == "IB2600163730"
    assert window.document_tender.text() == "IB2600163730"
    assert window.last_document_id == result_b.document_id
    assert window.document_path.text() == ""


def test_document_workspace_shows_tender_identity_documents_and_summary(
    window: QICrawlerWindow,
    tmp_path: Path,
) -> None:
    manifest = _document_manifest(tmp_path / "documents" / "HSMT.pdf")

    window._render_document_workspace(manifest)

    assert "Mã gói: IB2600000001-00" in window.document_tender_summary.text()
    assert "Tên gói: Cung cấp thiết bị mạng" in window.document_tender_summary.text()
    assert "Nguồn: egp" in window.document_tender_summary.text()
    assert not window.document_identity_banner.isHidden()
    assert window.document_table.rowCount() == 2
    assert window.document_table.item(0, 0).text() == "HSMT.pdf"
    assert window.document_table.item(0, 1).text() == "Hồ sơ mời thầu qua mạng"
    assert window.document_table.item(0, 2).text() == "4"
    assert window.document_table.item(0, 3).text() == "v1"
    assert window.document_metrics["total"].text() == "2"
    assert window.document_metrics["verified"].text() == "1"
    assert window.document_metrics["candidate"].text() == "1"
    assert not hasattr(window, "document_analyze_button")
    assert window.open_document_button.isHidden()
    assert window.open_document_folder_button.isHidden()
    assert window.document_confirm_type_button.isHidden()

    window.document_table.selectRow(0)

    assert window.last_document_id == 7
    assert window.open_document_button.isEnabled()
    assert not window.open_document_button.isHidden()
    assert window.document_confirm_type_button.isEnabled()
    assert not window.document_confirm_type_button.isHidden()


def test_document_selection_shows_persisted_native_extraction(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    inspection = DocumentExtractionInspection(
        document_id=7,
        filename="HSMT.pdf",
        file_format="PDF",
        status="NATIVE_OK",
        evidence_count=152,
        page_count=152,
        sheet_count=0,
        text_count=2,
        table_count=0,
        flags=("NATIVE_OK",),
        evidence=(
            EvidencePreview("page:1", 1, None, "TEXT", "Noi dung trang mot", None),
            EvidencePreview("page:2", 2, None, "TEXT", "Noi dung trang hai", None),
        ),
    )
    monkeypatch.setattr(
        gui,
        "run_document_extraction_inspection",
        lambda _config, _document_id: inspection,
    )

    window._render_document_workspace(_document_manifest(tmp_path / "documents" / "HSMT.pdf"))
    window.document_table.selectRow(0)

    assert "NATIVE_OK" in window.document_extraction_summary.text()
    assert "Trang: 152" in window.document_extraction_summary.text()
    assert window.document_extraction_box.title() == "D. KẾT QUẢ ĐỌC TÀI LIỆU"
    assert not window.document_evidence_button.isHidden()

    window.show_document_evidence()

    assert not window.document_evidence_view.isHidden()
    assert "page:1" in window.document_evidence_view.toPlainText()
    assert "Noi dung trang mot" in window.document_evidence_view.toPlainText()


def test_document_extraction_inspector_resets_and_refreshes_for_each_selection(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    inspections = {
        7: DocumentExtractionInspection(
            7, "HSMT.pdf", "PDF", "NATIVE_OK", 1, 1, 0, 1, 0, ("NATIVE_OK",), ()
        ),
        8: DocumentExtractionInspection(
            8, "BOQ.xlsx", "XLSX", "NEEDS_REVIEW", 4, 0, 1, 2, 2,
            ("TABLE_STRUCTURE_UNCERTAIN",), (),
        ),
    }
    monkeypatch.setattr(
        gui,
        "run_document_extraction_inspection",
        lambda _config, document_id: inspections[document_id],
    )

    window._render_document_workspace(_document_manifest(tmp_path / "documents" / "HSMT.pdf"))
    assert "Chọn một tài liệu" in window.document_extraction_summary.text()
    assert window.document_evidence_button.isHidden()
    window.document_table.selectRow(0)
    assert "Trang: 1" in window.document_extraction_summary.text()
    window.document_table.selectRow(1)
    assert "Định dạng: XLSX" in window.document_extraction_summary.text()
    assert "TABLE_STRUCTURE_UNCERTAIN" in window.document_extraction_summary.text()

    window.document_table.clearSelection()
    assert "Chọn một tài liệu" in window.document_extraction_summary.text()
    assert window.document_evidence_button.isHidden()


def test_hsmt_dashboard_cards_render_persisted_fact_counts(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    dashboard = HSMTFactDashboard(
        tender_id=10,
        facts=(
            HSMTFactView(
                1,
                "BOM_SUPPLY",
                "SUPPLY_ITEM",
                "Day mang CAT6 | 14 | thung",
                "FOUND",
                "BOQ.xlsx",
                "sheet:BOQ!A2:C2",
                "Day mang CAT6 | 14 | thung",
            ),
            HSMTFactView(
                2,
                "BOM_SUPPLY",
                "SUPPLY_ITEM",
                None,
                "NOT_FOUND_IN_AVAILABLE_SOURCES",
                None,
                None,
                None,
            ),
        ),
    )
    monkeypatch.setattr(gui, "run_hsmt_fact_dashboard", lambda _config, _tender: dashboard)

    window._render_document_workspace(_document_manifest(tmp_path / "documents" / "HSMT.pdf"))

    card = window.hsmt_fact_cards["BOM_SUPPLY"]
    assert card.isEnabled()
    assert "2 hạng mục | 1 cần kiểm tra" in card.text()
    assert window._hsmt_fact_label("SELECTION_PROCEDURE") == "Phương thức lựa chọn"
    assert window._hsmt_fact_label("SUPPLY_REQUIREMENT") == "Yêu cầu cung ứng"

def test_manual_workspace_renders_human_declared_identity(window: QICrawlerWindow, tmp_path: Path) -> None:
    manifest = replace(
        _document_manifest(tmp_path / "documents" / "HSMT.pdf"),
        source="team_bid",
        identity_status="HUMAN_DECLARED",
    )

    window._render_manual_workspace(manifest)

    assert window.manual_workspace_button.text() == "+ TẠO GÓI TỪ TEAM BID"
    assert window.document_tender.text() == "IB2600000001-00"
    assert "Team Bid cung cấp" in window.document_tender_summary.text()
    assert "Chưa xác minh từ web" in window.document_identity_banner.text()


@pytest.mark.parametrize(
    "width,height",
    [(1280, 720), (1366, 768), (1440, 900), (1920, 1080)],
)
def test_document_workspace_layout_has_three_clear_blocks(
    window: QICrawlerWindow, width: int, height: int
) -> None:
    window.navigation.setCurrentRow(3)
    window.resize(width, height)
    window.show()
    QApplication.processEvents()

    blocks = {group.title(): group for group in window.findChildren(QGroupBox)}
    assert {"A. GÓI THẦU ĐANG CHỌN", "B. THÊM TÀI LIỆU", "C. BỘ TÀI LIỆU"}.issubset(blocks)
    assert window.document_table.columnCount() == 6
    assert [
        window.document_table.horizontalHeaderItem(column).text()
        for column in range(window.document_table.columnCount())
    ] == [
        "Tên file",
        "Loại tài liệu",
        "Mẫu hồ sơ",
        "Phiên bản",
        "Identity",
        "Trạng thái phân loại",
    ]
    assert window.document_table.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAsNeeded
    assert window.document_scroll.widgetResizable()
    assert window.document_scroll.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    assert window.document_scroll.verticalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAsNeeded
    assert all(block.width() > 0 for block in blocks.values())
    assert window.document_tender.isVisible()
    assert window.document_pending_label.isVisible()
    assert window.document_name.isHidden()
    assert window.document_path.isHidden()


def test_document_workspace_hides_unavailable_context_actions(window: QICrawlerWindow) -> None:
    assert window.document_confirm_type_button.isHidden()
    assert window.open_document_button.isHidden()
    assert window.open_document_folder_button.isHidden()
    assert not hasattr(window, "document_analyze_button")


def test_document_workspace_uses_service_and_resets_busy_state(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    manifest = _document_manifest(tmp_path / "documents" / "HSMT.pdf")
    captured: list[str] = []

    def workspace(_config: AppConfig, tender: str) -> TenderDocumentManifest:
        captured.append(tender)
        return manifest

    monkeypatch.setattr(gui, "run_tender_document_workspace", workspace)
    window.document_tender.setText("IB2600000001-00")
    window.start_document_workspace()

    assert not window.document_workspace_button.isEnabled()
    _wait_until(lambda: window.document_workspace_button.isEnabled())
    assert captured == ["IB2600000001-00"]
    assert window.document_progress.isHidden()
    assert window._active_long_operation is None


def test_document_intake_error_releases_global_busy_state(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "bad.pdf"
    source.write_bytes(b"bad")

    def fail(*_args) -> None:
        raise RuntimeError("storage failure")

    monkeypatch.setattr(gui, "run_document_intake", fail)
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args: None)
    window.document_path.setText(str(source))

    window.start_document_intake()

    _wait_until(lambda: window.document_import_button.isEnabled())
    assert window.document_progress.isHidden()
    assert window._active_long_operation is None
    assert window._active_jobs == []
    assert all(button.isEnabled() for button in window._long_operation_buttons)
    assert "Không thể hoàn tất" in window.document_status.text()


def test_document_open_actions_are_mocked_safely(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    stored = tmp_path / "documents" / "unlinked" / "hash" / "HSMT.pdf"
    opened: list[Path] = []
    monkeypatch.setattr(gui, "open_path", lambda path: opened.append(path) or True)
    window._render_document_result(_document_result(stored))

    window.open_document()
    window.open_document_folder()

    assert opened == [stored, stored.parent]


def test_gui_identity_mismatch_releases_busy_state(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "wrong-tender.pdf"
    source.write_bytes(b"wrong tender")
    messages: list[str] = []

    def mismatch(*_args) -> None:
        raise DocumentIdentityMismatch("IB-EXPECTED", "IB-DETECTED")

    monkeypatch.setattr(gui, "run_document_intake", mismatch)
    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda _parent, _title, message: messages.append(message),
    )
    window.document_path.setText(str(source))

    window.start_document_intake()

    _wait_until(lambda: window.document_import_button.isEnabled())
    assert window._active_long_operation is None
    assert window.document_progress.isHidden()
    assert all(button.isEnabled() for button in window._long_operation_buttons)
    assert "TÀI LIỆU KHÔNG KHỚP GÓI" in window.document_status.text()
    assert "Expected: IB-EXPECTED" in window.document_status.text()
    assert "Detected: IB-DETECTED" in window.document_status.text()
    assert not window.document_identity_banner.isHidden()
    assert "KHÔNG KHỚP" in window.document_identity_banner.text()
    assert messages == [window.document_status.text()]


def test_document_classification_gui_uses_vietnamese_and_confirms_type(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    stored = tmp_path / "documents" / "egp" / "IB" / "hash" / "HSMT.pdf"
    window._render_document_result(_document_result(stored))
    captured: list[tuple[int, str, str, str, str]] = []

    def confirm(
        _config: AppConfig,
        document_id: int,
        document_type: str,
        template_code: str,
        package_type: str,
        selection_method: str,
    ) -> DocumentClassification:
        captured.append(
            (
                document_id,
                document_type,
                template_code,
                package_type,
                selection_method,
            )
        )
        return DocumentClassification(
            document_type=TenderDocumentType.E_HSMT,
            template_code="4",
            package_type="Hàng hóa",
            selection_method="Một giai đoạn một túi hồ sơ",
            status=ClassificationStatus.VERIFIED,
        )

    monkeypatch.setattr(gui, "run_document_classification_confirmation", confirm)
    window.document_type_combo.setCurrentIndex(
        window.document_type_combo.findData("E_HSMT")
    )
    window.document_template_combo.setCurrentIndex(
        window.document_template_combo.findData("4")
    )
    window.document_package_type.setText("Hàng hóa")
    window.document_selection_method.setText("Một giai đoạn một túi hồ sơ")

    window.confirm_document_type()

    _wait_until(lambda: window.document_confirm_type_button.isEnabled())
    assert captured == [
        (
            7,
            "E_HSMT",
            "4",
            "Hàng hóa",
            "Một giai đoạn một túi hồ sơ",
        )
    ]
    assert window.document_classification_status.text() == "Đã xác minh"
    assert "Đã xác nhận loại tài liệu" in window.document_status.text()
    assert "Hồ sơ mời thầu qua mạng" in window.document_status.text()


def test_web_document_intake_renders_summary_and_releases_busy_state(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    stored = tmp_path / "documents" / "egp" / "IB" / "hash" / "HSMT.pdf"

    def acquire(_config: AppConfig, tender: str) -> WebDocumentIntakeSummary:
        assert tender == "IB2600000001-00"
        return WebDocumentIntakeSummary(
            tender_identifier=tender,
            discovered=3,
            downloaded=3,
            duplicates=1,
            needs_review=1,
            failed=0,
            human_required=False,
            results=_document_result(stored).results,
            failures=(),
        )

    monkeypatch.setattr(gui, "run_web_document_intake", acquire)
    window.document_tender.setText("IB2600000001-00")
    window.start_web_document_intake()

    assert not window.document_web_button.isEnabled()
    _wait_until(lambda: window.document_web_button.isEnabled())
    assert "Đã phát hiện: 3" in window.document_status.text()
    assert "Đã tải: 3" in window.document_status.text()
    assert "Trùng: 1" in window.document_status.text()
    assert "Cần kiểm tra: 1" in window.document_status.text()
    assert window.document_progress.isHidden()
    assert window._active_long_operation is None
    assert all(button.isEnabled() for button in window._long_operation_buttons)


def test_web_document_intake_error_releases_busy_state(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(*_args) -> None:
        raise RuntimeError("download failure")

    monkeypatch.setattr(gui, "run_web_document_intake", fail)
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args: None)
    window.document_tender.setText("IB2600000001-00")
    window.start_web_document_intake()

    _wait_until(lambda: window.document_web_button.isEnabled())
    assert window.document_progress.isHidden()
    assert window._active_long_operation is None
    assert all(button.isEnabled() for button in window._long_operation_buttons)
