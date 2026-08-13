"""PySide6 desktop prototype for QI-Crawler Team Bid workflows."""

from __future__ import annotations

import logging
import os
import sys
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from . import __version__
from .compliance import AccessDenied
from .config import AppConfig, EnvSettings, load_config
from .crawler import ScanSummary
from .db import Database, SchemaNotReady
from .gui_services import (
    SearchRow,
    run_export,
    run_login,
    run_scan,
    run_search,
    run_single_crawl,
)
from .logging_utils import configure_logging
from .migrations import upgrade_database
from .standalone import (
    StandaloneResourceError,
    configure_standalone_file_logging,
    is_frozen,
    prepare_standalone_runtime,
)
from .standalone_smoke import run_standalone_smoke

logger = logging.getLogger(__name__)

COTEC_LIST_URL = "https://ebidding.coteccons.vn/Index"


class WorkerSignals(QObject):
    finished = Signal(object)
    error = Signal(object)


class FunctionWorker(QRunnable):
    """Execute one application-service call away from the Qt UI thread."""

    def __init__(
        self,
        function: Callable[..., Any],
        *args: Any,
        task_name: str = "operation",
        **kwargs: Any,
    ) -> None:
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.task_name = task_name
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        result: Any = None
        error: BaseException | None = None
        terminal_signal = "error"
        logger.info("GUI_WORKER_START task=%s", self.task_name)
        try:
            result = self.function(*self.args, **self.kwargs)
            terminal_signal = "finished"
        except BaseException as exc:
            error = exc
            logger.exception("GUI worker failed")
        finally:
            # Every worker invocation has one, and only one, terminal signal.
            # The receiver is retained by QICrawlerWindow until delivery.
            logger.info(
                "GUI_WORKER_FINISHED task=%s terminal=%s",
                self.task_name,
                terminal_signal,
            )
            if error is None:
                self.signals.finished.emit(result)
            else:
                self.signals.error.emit(error)


class GuiTaskBridge(QObject):
    """Deliver one worker terminal event safely to the GUI thread."""

    def __init__(
        self,
        window: QICrawlerWindow,
        *,
        button: QPushButton,
        progress: QProgressBar | None,
        status: QLabel | None,
        on_success: Callable[[Any], None],
        long_operation: bool,
    ) -> None:
        super().__init__(window)
        self.window = window
        self.button = button
        self.progress = progress
        self.status = status
        self.on_success = on_success
        self.long_operation = long_operation
        self.worker: FunctionWorker | None = None
        self.signals: WorkerSignals | None = None
        self.terminal_received = False

    def retain_worker(self, worker: FunctionWorker) -> None:
        """Keep worker and signal emitter alive until a queued event is handled."""
        self.worker = worker
        self.signals = worker.signals

    @Slot(object)
    def handle_finished(self, result: Any) -> None:
        if self.terminal_received:
            logger.warning("Ignoring duplicate GUI terminal signal: finished")
            return
        self.terminal_received = True
        self.window._deliver_worker_success(self, result)

    @Slot(object)
    def handle_error(self, error: BaseException) -> None:
        if self.terminal_received:
            logger.warning("Ignoring duplicate GUI terminal signal: error")
            return
        self.terminal_received = True
        self.window._deliver_worker_error(self, error)

    def release(self) -> None:
        self.worker = None
        self.signals = None


class QICrawlerWindow(QMainWindow):
    def __init__(self, config: AppConfig | None = None) -> None:
        super().__init__()
        self.config = config or load_config()
        self.thread_pool = QThreadPool.globalInstance()
        self.last_export_path: Path | None = None
        self._login_ready: threading.Event | None = None
        self._login_confirmed: threading.Event | None = None
        self._active_jobs: list[GuiTaskBridge] = []
        self._active_long_operation: str | None = None
        self.setWindowTitle(f"QI-CRAWLER v{__version__}")
        self.resize(1120, 740)
        self.setMinimumSize(960, 640)
        self.setFont(QFont("Segoe UI", 10))
        self._apply_style()
        self._build_shell()
        self.statusBar().showMessage("QI-Crawler đã sẵn sàng")
        version_label = QLabel(f"QI-Crawler v{__version__}")
        self.statusBar().addPermanentWidget(version_label)

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow { background: #f4f7fb; }
            QFrame#sidebar { background: #132238; border: 0; }
            QLabel#brand { color: white; font-size: 21px; font-weight: 700; }
            QLabel#brandCaption { color: #aebbd0; font-size: 12px; }
            QListWidget#navigation {
                background: transparent; color: #d9e2ef; border: 0;
                outline: 0; padding: 8px;
            }
            QListWidget#navigation::item {
                border-radius: 7px; padding: 12px 10px; margin: 2px 0;
            }
            QListWidget#navigation::item:selected {
                background: #1f6feb; color: white; font-weight: 600;
            }
            QLabel#pageTitle { color: #172033; font-size: 23px; font-weight: 700; }
            QLabel#pageDescription { color: #5b6577; font-size: 13px; }
            QLineEdit, QSpinBox, QComboBox {
                min-height: 34px; border: 1px solid #cfd7e5; border-radius: 6px;
                padding: 2px 9px; background: white;
            }
            QPushButton { min-height: 34px; padding: 2px 16px; }
            QPushButton#primaryButton {
                background: #1666d8; color: white; border: 0; border-radius: 6px;
                font-weight: 600; min-height: 38px;
            }
            QPushButton#primaryButton:hover { background: #0d55bd; }
            QPushButton#primaryButton:disabled { background: #9fb9dc; }
            QFrame#metricCard {
                background: white; border: 1px solid #dce3ed; border-radius: 8px;
            }
            QLabel#metricValue { color: #172033; font-size: 24px; font-weight: 700; }
            QLabel#metricName { color: #667085; font-size: 12px; }
            QTableWidget { background: white; border: 1px solid #dce3ed; }
            QProgressBar { min-height: 7px; max-height: 7px; border: 0; background: #dce3ed; }
            QProgressBar::chunk { background: #1f6feb; }
            """
        )

    def _build_shell(self) -> None:
        central = QWidget()
        shell = QHBoxLayout(central)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(235)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(18, 26, 18, 20)
        sidebar_layout.setSpacing(12)
        brand = QLabel("QI-CRAWLER")
        brand.setObjectName("brand")
        caption = QLabel("Trợ lý tìm kiếm gói thầu")
        caption.setObjectName("brandCaption")
        sidebar_layout.addWidget(brand)
        sidebar_layout.addWidget(caption)
        sidebar_layout.addSpacing(14)
        self.navigation = QListWidget()
        self.navigation.setObjectName("navigation")
        self.navigation.addItems(
            [
                "Quét gói thầu",
                "Tìm kiếm",
                "Xuất TBMT",
                "Crawl một URL",
                "Đăng nhập nguồn",
                "Nhật ký",
            ]
        )
        sidebar_layout.addWidget(self.navigation, 1)

        self.pages = QStackedWidget()
        self._build_scan_page()
        self._build_search_page()
        self._build_export_page()
        self._build_crawl_page()
        self._build_login_page()
        self._build_log_page()
        self._long_operation_buttons = (
            self.scan_button,
            self.crawl_button,
            self.export_button,
            self.login_button,
        )
        self.navigation.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.navigation.setCurrentRow(0)

        shell.addWidget(sidebar)
        shell.addWidget(self.pages, 1)
        self.setCentralWidget(central)

    def _new_page(self, title: str, description: str) -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(34, 28, 34, 28)
        layout.setSpacing(14)
        title_label = QLabel(title)
        title_label.setObjectName("pageTitle")
        description_label = QLabel(description)
        description_label.setObjectName("pageDescription")
        description_label.setWordWrap(True)
        layout.addWidget(title_label)
        layout.addWidget(description_label)
        layout.addSpacing(8)
        self.pages.addWidget(page)
        return page, layout

    @staticmethod
    def _primary_button(text: str) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName("primaryButton")
        return button

    @staticmethod
    def _progress_bar() -> QProgressBar:
        progress = QProgressBar()
        progress.setRange(0, 0)
        progress.setTextVisible(False)
        progress.hide()
        return progress

    def _build_scan_page(self) -> None:
        _page, layout = self._new_page(
            "Quét danh sách gói thầu",
            "Chọn nguồn, giới hạn số trang danh sách và thêm từ khóa nếu chỉ muốn lọc "
            "một nhóm gói cụ thể.",
        )
        form = QFormLayout()
        form.setHorizontalSpacing(20)
        form.setVerticalSpacing(12)
        self.scan_source = QComboBox()
        self.scan_source.addItem("Coteccons e-Bidding", COTEC_LIST_URL)
        self.scan_source.addItem("URL khác", "")
        self.scan_source.currentIndexChanged.connect(self._on_scan_source_changed)
        self.scan_url = QLineEdit()
        self.scan_url.setText(COTEC_LIST_URL)
        self.scan_url.setPlaceholderText("Dán URL trang danh sách gói thầu")
        self.scan_max_pages = QSpinBox()
        self.scan_max_pages.setRange(1, 100)
        self.scan_max_pages.setValue(3)
        self.scan_keywords = QLineEdit()
        self.scan_keywords.setPlaceholderText("Để trống = tất cả; ví dụ: chống thấm, sơn")
        form.addRow("Nguồn đấu thầu:", self.scan_source)
        form.addRow("URL danh sách:", self.scan_url)
        form.addRow("Số trang tối đa:", self.scan_max_pages)
        form.addRow("Từ khóa tùy chọn:", self.scan_keywords)
        layout.addLayout(form)
        action_row = QHBoxLayout()
        self.scan_button = self._primary_button("Bắt đầu quét")
        self.scan_button.clicked.connect(self.start_scan)
        action_row.addWidget(self.scan_button)
        action_row.addStretch()
        layout.addLayout(action_row)
        self.scan_progress = self._progress_bar()
        layout.addWidget(self.scan_progress)
        self.scan_status = QLabel("Sẵn sàng quét danh sách gói thầu.")
        self.scan_status.setWordWrap(True)
        layout.addWidget(self.scan_status)
        metrics = QGridLayout()
        metrics.setSpacing(12)
        self.scan_metrics: dict[str, QLabel] = {}
        metric_definitions = [
            ("pages_scanned", "Trang đã quét"),
            ("discovered", "Gói tìm thấy"),
            ("new", "Gói mới"),
            ("existing", "Đã có / cập nhật"),
            ("success", "Thành công"),
            ("failed", "Lỗi"),
            ("pending", "Chờ xử lý"),
        ]
        for index, (key, name) in enumerate(metric_definitions):
            card = QFrame()
            card.setObjectName("metricCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(14, 11, 14, 11)
            value = QLabel("0")
            value.setObjectName("metricValue")
            name_label = QLabel(name)
            name_label.setObjectName("metricName")
            card_layout.addWidget(value)
            card_layout.addWidget(name_label)
            self.scan_metrics[key] = value
            metrics.addWidget(card, index // 4, index % 4)
        layout.addLayout(metrics)
        layout.addStretch()

    def _build_search_page(self) -> None:
        _page, layout = self._new_page(
            "Tìm gói đã lưu",
            "Tìm trong dữ liệu QI-Crawler đã thu thập. Việc tìm kiếm không thay đổi bộ từ khóa.",
        )
        row = QHBoxLayout()
        self.search_keyword = QLineEdit()
        self.search_keyword.setPlaceholderText("Nhập từ khóa, ví dụ: chống thấm")
        self.search_button = self._primary_button("Tìm kiếm")
        self.search_button.clicked.connect(self.start_search)
        row.addWidget(self.search_keyword)
        row.addWidget(self.search_button)
        layout.addLayout(row)
        self.search_progress = self._progress_bar()
        layout.addWidget(self.search_progress)
        self.search_status = QLabel("Nhập từ khóa để bắt đầu tìm kiếm.")
        layout.addWidget(self.search_status)
        self.search_table = QTableWidget(0, 5)
        self.search_table.setHorizontalHeaderLabels(
            ["Mã gói", "Tên gói", "Bên mời thầu", "Nguồn", "URL"]
        )
        self.search_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.search_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        layout.addWidget(self.search_table)

    def _build_export_page(self) -> None:
        _page, layout = self._new_page(
            "Xuất báo cáo Excel TBMT",
            "Xuất các gói thầu hợp lệ theo mẫu TBMT để Team Bid kiểm tra và trình duyệt.",
        )
        self.export_button = self._primary_button("Xuất Excel TBMT")
        self.export_button.clicked.connect(self.start_export)
        self.export_progress = self._progress_bar()
        self.export_path = QLineEdit()
        self.export_path.setReadOnly(True)
        self.export_status = QLabel("Chưa xuất báo cáo trong phiên làm việc này.")
        self.export_status.setWordWrap(True)
        self.open_export_button = QPushButton("Mở file Excel")
        self.open_export_button.setEnabled(False)
        self.open_export_button.clicked.connect(self.open_export)
        layout.addWidget(self.export_button)
        layout.addWidget(self.export_progress)
        layout.addWidget(self.export_status)
        layout.addWidget(QLabel("File đã xuất:"))
        layout.addWidget(self.export_path)
        layout.addWidget(self.open_export_button)
        layout.addStretch()

    def _build_crawl_page(self) -> None:
        _page, layout = self._new_page(
            "Crawl một gói cụ thể",
            "Dùng khi bạn đã có URL trang chi tiết của một gói thầu và muốn lưu ngay vào hệ thống.",
        )
        self.crawl_url = QLineEdit()
        self.crawl_url.setPlaceholderText("Dán URL chi tiết một gói thầu")
        self.crawl_button = self._primary_button("Crawl gói thầu")
        self.crawl_button.clicked.connect(self.start_crawl)
        self.crawl_progress = self._progress_bar()
        self.crawl_status = QLabel("Chưa chạy.")
        self.crawl_status.setWordWrap(True)
        layout.addWidget(QLabel("URL gói thầu:"))
        layout.addWidget(self.crawl_url)
        layout.addWidget(self.crawl_button)
        layout.addWidget(self.crawl_progress)
        layout.addWidget(self.crawl_status)
        layout.addStretch()

    def _build_login_page(self) -> None:
        _page, layout = self._new_page(
            "Đăng nhập nguồn đấu thầu",
            "QI-Crawler mở trình duyệt để bạn tự đăng nhập. Công cụ không lưu mật khẩu, "
            "OTP hoặc CAPTCHA.",
        )
        self.login_source = QLineEdit("egp")
        self.login_button = self._primary_button("Mở trình duyệt đăng nhập")
        self.login_button.clicked.connect(self.start_login)
        self.login_progress = self._progress_bar()
        self.login_status = QLabel("Chưa bắt đầu đăng nhập.")
        self.login_status.setWordWrap(True)
        layout.addWidget(QLabel("Tên nguồn:"))
        layout.addWidget(self.login_source)
        layout.addWidget(
            QLabel(
                "Bạn tự nhập tài khoản và xử lý OTP/CAPTCHA nếu website yêu cầu. "
                "QI-Crawler không vượt qua biện pháp bảo mật."
            )
        )
        layout.addWidget(self.login_button)
        layout.addWidget(self.login_progress)
        layout.addWidget(self.login_status)
        layout.addStretch()

    def _build_log_page(self) -> None:
        _page, layout = self._new_page(
            "Nhật ký kỹ thuật",
            "Thông tin chi tiết dành cho IT khi cần kiểm tra. Team Bid có thể dùng các trang "
            "chức năng mà không cần đọc phần này.",
        )
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

    def _on_scan_source_changed(self) -> None:
        known_url = str(self.scan_source.currentData() or "")
        if known_url:
            self.scan_url.setText(known_url)
        elif self.scan_url.text().strip() == COTEC_LIST_URL:
            self.scan_url.clear()
        self.scan_url.setFocus()

    def _append_log(self, message: str) -> None:
        self.log_output.append(message)
        self.statusBar().showMessage("Đã cập nhật Nhật ký kỹ thuật.", 5000)

    def _submit(
        self,
        function: Callable[..., Any],
        *args: Any,
        on_success: Callable[[Any], None],
        button: QPushButton,
        progress: QProgressBar | None = None,
        status: QLabel | None = None,
        task_name: str = "operation",
        long_operation: bool = False,
    ) -> bool:
        if long_operation and self._active_long_operation is not None:
            message = "QI-Crawler đang xử lý một tác vụ. Vui lòng chờ hoàn tất."
            if status is not None:
                status.setText(message)
            self.statusBar().showMessage(message, 10000)
            return False
        if long_operation:
            self._active_long_operation = task_name
            self._set_long_operation_controls_enabled(False)
        self._set_job_busy(button, progress, busy=True)
        bridge = GuiTaskBridge(
            self,
            button=button,
            progress=progress,
            status=status,
            on_success=on_success,
            long_operation=long_operation,
        )
        worker = FunctionWorker(function, *args, task_name=task_name)
        bridge.retain_worker(worker)
        self._active_jobs.append(bridge)
        worker.signals.finished.connect(
            bridge.handle_finished,
            Qt.ConnectionType.QueuedConnection,
        )
        worker.signals.error.connect(
            bridge.handle_error,
            Qt.ConnectionType.QueuedConnection,
        )
        try:
            self.thread_pool.start(worker)
        except (RuntimeError, TypeError) as exc:
            self._deliver_worker_error(bridge, exc)
        return True

    def _set_long_operation_controls_enabled(self, enabled: bool) -> None:
        for control in self._long_operation_buttons:
            control.setEnabled(enabled)

    @staticmethod
    def _set_job_busy(
        button: QPushButton,
        progress: QProgressBar | None,
        *,
        busy: bool,
    ) -> None:
        button.setEnabled(not busy)
        button.setProperty("busy", busy)
        if progress is not None:
            progress.setVisible(busy)

    def _release_job(self, bridge: GuiTaskBridge) -> None:
        if bridge in self._active_jobs:
            self._active_jobs.remove(bridge)
        if bridge.long_operation:
            self._active_long_operation = None
            self._set_long_operation_controls_enabled(True)
        bridge.release()
        bridge.deleteLater()

    def _deliver_worker_success(self, bridge: GuiTaskBridge, result: Any) -> None:
        try:
            self._worker_success(
                bridge.button,
                bridge.on_success,
                result,
                bridge.progress,
                bridge.status,
            )
        finally:
            self._release_job(bridge)

    def _deliver_worker_error(self, bridge: GuiTaskBridge, error: BaseException) -> None:
        try:
            self._worker_error(
                bridge.button,
                error,
                bridge.progress,
                bridge.status,
            )
        finally:
            self._release_job(bridge)

    def _worker_success(
        self,
        button: QPushButton,
        callback: Callable[[Any], None],
        result: Any,
        progress: QProgressBar | None = None,
        status: QLabel | None = None,
    ) -> None:
        self._set_job_busy(button, progress, busy=False)
        try:
            callback(result)
        except Exception as exc:
            logger.exception("GUI success handler failed")
            self._worker_error(button, exc, progress, status)

    def _worker_error(
        self,
        button: QPushButton,
        error: BaseException,
        progress: QProgressBar | None = None,
        status: QLabel | None = None,
    ) -> None:
        self._set_job_busy(button, progress, busy=False)
        if isinstance(error, AccessDenied):
            if status is not None:
                status.setText("Cần người dùng xử lý trước khi chạy lại.")
            self.show_human_required(str(error))
            return
        if isinstance(error, SchemaNotReady):
            message = "Cơ sở dữ liệu chưa sẵn sàng. IT cần chạy QI-Crawler db-upgrade."
        else:
            message = "Không thể hoàn tất thao tác. Dữ liệu không bị ghi sai."
        if status is not None:
            status.setText(message)
        self._append_log(f"LỖI: {message} Chi tiết kỹ thuật: {error}")
        QMessageBox.critical(self, "QI-Crawler", message)

    @Slot()
    def start_scan(self) -> None:
        url = self.scan_url.text().strip()
        if not url:
            self.scan_status.setText("Vui lòng dán URL danh sách gói thầu.")
            return
        if not url.lower().startswith(("http://", "https://")):
            self.scan_status.setText("URL phải bắt đầu bằng http:// hoặc https://")
            return
        self.scan_status.setText(
            "Đang quét. Bạn vẫn có thể chuyển sang chức năng khác trong ứng dụng."
        )
        self._submit(
            run_scan,
            self.config,
            url,
            self.scan_max_pages.value(),
            self.scan_keywords.text().strip(),
            on_success=self._render_scan_result,
            button=self.scan_button,
            progress=self.scan_progress,
            status=self.scan_status,
            task_name="scan",
            long_operation=True,
        )

    def _render_scan_result(self, summary: ScanSummary) -> None:
        values = {
            "pages_scanned": summary.pages_scanned,
            "discovered": summary.discovered,
            "new": summary.new,
            "existing": summary.existing,
            "success": summary.success,
            "failed": summary.failed,
            "pending": summary.pending,
        }
        for key, value in values.items():
            self.scan_metrics[key].setText(str(value))
        self.scan_status.setText(
            "Quét hoàn tất. Hãy kiểm tra các số liệu bên dưới trước khi tìm kiếm hoặc xuất Excel."
        )
        self._append_log(
            f"Quét xong run {summary.run_id or '-'}: {summary.success} thành công, "
            f"{summary.failed} lỗi, {summary.pending} chờ xử lý."
        )

    @Slot()
    def start_search(self) -> None:
        keyword = self.search_keyword.text().strip()
        if not keyword:
            QMessageBox.information(self, "QI-Crawler", "Vui lòng nhập từ khóa cần tìm.")
            return
        self.search_status.setText("Đang tìm trong dữ liệu đã lưu...")
        self._submit(
            run_search,
            self.config,
            keyword,
            on_success=self._render_search_results,
            button=self.search_button,
            progress=self.search_progress,
            status=self.search_status,
            task_name="search",
        )

    def _render_search_results(self, rows: list[SearchRow]) -> None:
        self.search_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column, value in enumerate(
                (row.identifier, row.title, row.buyer, row.source, row.source_url)
            ):
                self.search_table.setItem(row_index, column, QTableWidgetItem(value))
        self.search_status.setText(f"Tìm thấy {len(rows)} gói phù hợp.")
        self._append_log(f"Tìm thấy {len(rows)} gói phù hợp với từ khóa.")

    @Slot()
    def start_export(self) -> None:
        self.export_status.setText("Đang tạo file Excel TBMT...")
        self._submit(
            run_export,
            self.config,
            on_success=self._render_export_result,
            button=self.export_button,
            progress=self.export_progress,
            status=self.export_status,
            task_name="export",
            long_operation=True,
        )

    def _render_export_result(self, result: Any) -> None:
        self.last_export_path = Path(result.output)
        self.export_path.setText(str(self.last_export_path))
        self.open_export_button.setEnabled(True)
        deduplicated = int(getattr(result, "deduplicated_records", 0))
        rejected = int(getattr(result, "rejected_records", 0))
        skipped = int(getattr(result, "skipped_records", 0))
        self.export_status.setText(
            "\n".join(
                [
                    f"Đã xuất: {result.exported_records}",
                    f"Cảnh báo: {result.warning_records}",
                    f"Trùng đã loại: {deduplicated}",
                    f"Bị loại: {rejected}",
                    f"Bỏ qua theo bộ lọc: {skipped}",
                ]
            )
        )
        self._append_log(
            f"Đã xuất {result.exported_records}; cảnh báo {result.warning_records}; "
            f"trùng {deduplicated}; bị loại {rejected}; bỏ qua {skipped}: {result.output}"
        )

    @Slot()
    def open_export(self) -> None:
        if not self.last_export_path:
            return
        if not open_path(self.last_export_path):
            QMessageBox.warning(
                self,
                "QI-Crawler",
                f"Không thể tự mở file. Bạn có thể mở thủ công tại:\n{self.last_export_path}",
            )

    @Slot()
    def start_crawl(self) -> None:
        url = self.crawl_url.text().strip()
        if not url:
            self.crawl_status.setText("Vui lòng dán URL một gói thầu.")
            return
        if not url.lower().startswith(("http://", "https://")):
            self.crawl_status.setText("URL phải bắt đầu bằng http:// hoặc https://")
            return
        self.crawl_status.setText("Đang crawl gói thầu...")
        self._submit(
            run_single_crawl,
            self.config,
            url,
            on_success=self._render_crawl_result,
            button=self.crawl_button,
            progress=self.crawl_progress,
            status=self.crawl_status,
            task_name="single_crawl",
            long_operation=True,
        )

    def _render_crawl_result(self, result: tuple[int, int, str | None]) -> None:
        success, failed, human_required = result
        if human_required:
            self.show_human_required(human_required)
            return
        self.crawl_status.setText(f"Hoàn tất: thành công {success}, lỗi {failed}.")
        self._append_log(self.crawl_status.text())

    @Slot()
    def start_login(self) -> None:
        source_name = self.login_source.text().strip() or "egp"
        self._login_ready = threading.Event()
        self._login_confirmed = threading.Event()
        self.login_status.setText("Đang mở trình duyệt đăng nhập...")
        self._append_log("Đang mở trình duyệt đăng nhập...")
        started = self._submit(
            run_login,
            self.config,
            source_name,
            self._login_ready,
            self._login_confirmed,
            on_success=self._render_login_result,
            button=self.login_button,
            progress=self.login_progress,
            status=self.login_status,
            task_name="login",
            long_operation=True,
        )
        if started:
            QTimer.singleShot(200, self._wait_for_login_browser)

    def _wait_for_login_browser(self) -> None:
        if self._login_ready is None or self._login_confirmed is None:
            return
        if not self.login_button.isEnabled() and not self._login_ready.is_set():
            QTimer.singleShot(200, self._wait_for_login_browser)
            return
        if not self._login_ready.is_set():
            return
        QMessageBox.information(
            self,
            "Đăng nhập nguồn",
            "Trình duyệt đã mở. Hãy tự đăng nhập và xử lý OTP/CAPTCHA nếu website yêu cầu.\n\n"
            "Khi đã vào trang danh sách gói thầu, quay lại đây và bấm OK.",
        )
        self._login_confirmed.set()

    def _render_login_result(self, path: Path) -> None:
        self.login_status.setText("Đã xác nhận đăng nhập và lưu phiên cục bộ an toàn.")
        self._append_log(f"Đã lưu phiên cục bộ: {path}")

    def show_human_required(self, technical_detail: str) -> None:
        logger.warning("HUMAN_REQUIRED: %s", technical_detail)
        self._append_log(f"HUMAN_REQUIRED: {technical_detail}")
        QMessageBox.warning(
            self,
            "Cần người dùng xử lý",
            "Phiên đăng nhập có thể đã hết hạn, website yêu cầu CAPTCHA/OTP, "
            "hoặc website từ chối truy cập.\n\n"
            "QI-Crawler không vượt qua biện pháp bảo mật. Dữ liệu không bị ghi sai. "
            "Sau khi xử lý nguyên nhân, bạn có thể chạy lại.",
        )


def open_path(path: Path) -> bool:
    """Open an exported file with the operating system default application."""
    try:
        if sys.platform == "win32":
            os.startfile(str(path.resolve()))
        else:
            return QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve())))
    except OSError:
        logger.exception("Cannot open exported file: %s", path)
        return False
    return True


def main() -> int:
    application = QApplication.instance() or QApplication(sys.argv)
    try:
        if is_frozen():
            paths = prepare_standalone_runtime()
            configure_standalone_file_logging(paths.logs_dir / "qi-crawler.log")
            config = load_config(paths.config_path)
            database = Database(config.storage.database_url)
            try:
                database.require_current_schema()
            except SchemaNotReady:
                upgrade_database(
                    config.storage.database_url,
                    backup_dir=paths.data_dir / "backups",
                )
                database.require_current_schema()
            smoke_requested = "--smoke-test" in sys.argv or "--smoke-test-network" in sys.argv
            if smoke_requested:
                passed = run_standalone_smoke(
                    config,
                    paths.logs_dir / "standalone-smoke.json",
                    include_network="--smoke-test-network" in sys.argv,
                )
                return 0 if passed else 2
        else:
            env = EnvSettings()
            configure_logging(env.log_level)
            config = load_config(env.config_path)
        window = QICrawlerWindow(config)
    except StandaloneResourceError as exc:
        logger.exception("Standalone resource is missing")
        QMessageBox.critical(None, "QI-Crawler", str(exc))
        return 1
    except Exception as exc:
        logger.exception("Cannot start QI-Crawler GUI")
        QMessageBox.critical(
            None,
            "QI-Crawler",
            f"Khong the khoi dong GUI. Vui long lien he IT.\n\nChi tiet: {exc}",
        )
        return 1
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
