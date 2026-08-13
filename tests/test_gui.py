from __future__ import annotations

import os
import threading
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QEventLoop, QThreadPool, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from qi_crawler import __version__, gui
from qi_crawler.config import AppConfig
from qi_crawler.crawler import ScanSummary
from qi_crawler.document_intake import (
    DocumentBatchResult,
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
from qi_crawler.web_document_intake import WebDocumentIntakeSummary


@pytest.fixture(scope="module")
def application() -> QApplication:
    return QApplication.instance() or QApplication([])


@pytest.fixture
def config(tmp_path: Path) -> AppConfig:
    value = AppConfig()
    value.storage.database_url = f"sqlite:///{tmp_path / 'gui.db'}"
    value.storage.report_dir = tmp_path / "reports"
    value.storage.rejects_dir = tmp_path / "rejects"
    value.storage.document_dir = tmp_path / "documents"
    return value


@pytest.fixture
def window(application: QApplication, config: AppConfig) -> QICrawlerWindow:
    widget = QICrawlerWindow(config)
    yield widget
    widget.close()


def test_gui_imports_and_starts(window: QICrawlerWindow) -> None:
    assert window.windowTitle() == f"QI-CRAWLER v{__version__}"
    assert window.navigation.count() == 7
    assert window.pages.count() == 7
    assert window.navigation.item(0).text() == "Quét gói thầu"
    assert window.navigation.item(5).text() == "HSMT / TÀI LIỆU"
    assert window.navigation.item(6).text() == "Nhật ký"


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
        lambda _config: SimpleNamespace(
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


def test_export_failure_returns_from_busy_state(
    window: QICrawlerWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    messages: list[str] = []

    def fail(_config: AppConfig) -> None:
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
    assert "Identity: VERIFIED" in window.document_status.text()
    assert "Loại tài liệu: Hồ sơ mời thầu qua mạng" in window.document_status.text()
    assert window.document_classification_status.text() == "Nhận diện sơ bộ"
    assert window.document_confirm_type_button.isEnabled()
    assert "SHA-256" not in window.document_status.text()
    assert window.last_document_path == stored
    assert window.open_document_button.isEnabled()
    assert window.open_document_folder_button.isEnabled()
    assert window.document_progress.isHidden()
    assert window._active_long_operation is None


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
    assert window.document_table.item(0, 3).text() == "v1"
    assert window.document_metrics["total"].text() == "2"
    assert window.document_metrics["verified"].text() == "1"
    assert window.document_metrics["candidate"].text() == "1"
    assert not window.document_analyze_button.isEnabled()
    assert "Native Extraction" in window.document_analyze_button.toolTip()

    window.document_table.selectRow(0)

    assert window.last_document_id == 7
    assert window.open_document_button.isEnabled()
    assert window.document_confirm_type_button.isEnabled()


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
