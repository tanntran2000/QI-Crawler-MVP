from __future__ import annotations

import os
import threading
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QEventLoop, QThreadPool, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from qi_crawler import __version__, gui
from qi_crawler.config import AppConfig
from qi_crawler.crawler import ScanSummary
from qi_crawler.gui import FunctionWorker, QICrawlerWindow


@pytest.fixture(scope="module")
def application() -> QApplication:
    return QApplication.instance() or QApplication([])


@pytest.fixture
def config(tmp_path: Path) -> AppConfig:
    value = AppConfig()
    value.storage.database_url = f"sqlite:///{tmp_path / 'gui.db'}"
    value.storage.report_dir = tmp_path / "reports"
    value.storage.rejects_dir = tmp_path / "rejects"
    return value


@pytest.fixture
def window(application: QApplication, config: AppConfig) -> QICrawlerWindow:
    widget = QICrawlerWindow(config)
    yield widget
    widget.close()


def test_gui_imports_and_starts(window: QICrawlerWindow) -> None:
    assert window.windowTitle() == f"QI-CRAWLER v{__version__}"
    assert window.navigation.count() == 6
    assert window.pages.count() == 6
    assert window.navigation.item(0).text() == "Quét gói thầu"
    assert window.navigation.item(5).text() == "Nhật ký"


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

    assert observed
    assert observed[0] != ui_thread


def test_long_job_disables_button_and_shows_progress(
    window: QICrawlerWindow,
) -> None:
    started: list[FunctionWorker] = []
    window.thread_pool = SimpleNamespace(start=lambda worker: started.append(worker))

    window._submit(
        lambda: "ok",
        on_success=lambda _result: None,
        button=window.scan_button,
        progress=window.scan_progress,
    )

    assert started
    assert not window.scan_button.isEnabled()
    assert not window.scan_progress.isHidden()

    window._worker_success(
        window.scan_button,
        lambda _result: None,
        "ok",
        window.scan_progress,
    )

    assert window.scan_button.isEnabled()
    assert window.scan_progress.isHidden()


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

    window._worker_error(window.scan_button, RuntimeError("technical detail"))

    assert messages == ["Không thể hoàn tất thao tác. Dữ liệu không bị ghi sai."]
    assert "technical detail" in window.log_output.toPlainText()
    assert "technical detail" not in window.statusBar().currentMessage()


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
