"""PySide6 desktop prototype for QI-Crawler Team Bid workflows."""

from __future__ import annotations

import logging
import os
import sys
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

from PySide6.QtCore import (
    QByteArray,
    QObject,
    QRect,
    QRunnable,
    QSettings,
    Qt,
    QThreadPool,
    QTimer,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import QCloseEvent, QDesktopServices, QFont
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from . import __version__
from .compliance import AccessDenied
from .config import AppConfig, EnvSettings, load_config
from .crawler import ScanSummary
from .db import Database, SchemaNotReady
from .document_intake import (
    DocumentBatchResult,
    DocumentContentIdentity,
    DocumentIdentityMismatch,
    DocumentManifestEntry,
    TenderDocumentManifest,
    extract_document_identity,
)
from .document_taxonomy import (
    CLASSIFICATION_STATUS_LABELS,
    DOCUMENT_TYPE_LABELS,
    TEMPLATE_REGISTRY,
    ClassificationStatus,
    DocumentClassification,
    TenderDocumentType,
)
from .gui_services import (
    DocumentExtractionInspection,
    HSMTFactDashboard,
    SearchRow,
    run_create_manual_tender_workspace,
    run_document_classification_confirmation,
    run_document_extraction_inspection,
    run_document_intake,
    run_export,
    run_hsmt_fact_dashboard,
    run_login,
    run_scan,
    run_search,
    run_single_crawl,
    run_tender_document_workspace,
    run_web_document_intake,
    run_workspace_document_intake,
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
from .web_document_intake import WebDocumentIntakeSummary

logger = logging.getLogger(__name__)

WINDOW_SETTINGS_ORGANIZATION = "QiTech"
WINDOW_SETTINGS_APPLICATION = "QI-Crawler"
PREFERRED_WINDOW_SIZE = (1440, 900)
MINIMUM_WINDOW_SIZE = (1180, 680)

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
        # QRunnable defaults to auto-delete. Our terminal signal is queued to
        # the GUI thread, so Python retains the native runnable until the
        # thread-pool invocation has completely returned.
        self.setAutoDelete(False)
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
    def __init__(
        self,
        config: AppConfig | None = None,
        *,
        settings: QSettings | None = None,
    ) -> None:
        super().__init__()
        self.config = config or load_config()
        self._settings = settings or QSettings(
            WINDOW_SETTINGS_ORGANIZATION,
            WINDOW_SETTINGS_APPLICATION,
        )
        self.thread_pool = QThreadPool.globalInstance()
        self.last_export_path: Path | None = None
        self.last_document_path: Path | None = None
        self.last_document_id: int | None = None
        self._selected_extraction: DocumentExtractionInspection | None = None
        self._hsmt_fact_dashboard: HSMTFactDashboard | None = None
        self._document_workspace_tender: str | None = None
        self._document_session_duplicates = 0
        self._login_ready: threading.Event | None = None
        self._login_confirmed: threading.Event | None = None
        self._active_jobs: list[GuiTaskBridge] = []
        self._active_long_operation: str | None = None
        self.setWindowTitle(f"QI-CRAWLER v{__version__}")
        self.setMinimumSize(*MINIMUM_WINDOW_SIZE)
        self.setFont(QFont("Segoe UI", 10))
        self._apply_style()
        self._build_shell()
        self._restore_window_geometry()
        self.statusBar().showMessage("QI-Crawler đã sẵn sàng")
        version_label = QLabel(f"QI-Crawler v{__version__}")
        self.statusBar().addPermanentWidget(version_label)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Keep QObject receivers alive while a worker still owns a queued signal."""
        if self._active_jobs:
            message = "QI-Crawler đang xử lý tác vụ. Vui lòng chờ hoàn tất trước khi đóng."
            self.statusBar().showMessage(message, 10000)
            event.ignore()
            return
        self._save_window_geometry()
        super().closeEvent(event)

    def _restore_window_geometry(self) -> None:
        geometry = self._settings.value("window/geometry", type=QByteArray)
        screen = QApplication.primaryScreen()
        if (
            geometry
            and self.restoreGeometry(geometry)
            and (
                screen is None
                or self._geometry_is_usable(
                    self.frameGeometry(),
                    screen.availableGeometry(),
                )
            )
        ):
            if self._settings.value("window/maximized", False, type=bool):
                self.showMaximized()
            return
        self._apply_default_window_geometry(screen.availableGeometry() if screen else None)

    def _apply_default_window_geometry(self, available: QRect | None) -> None:
        preferred_width, preferred_height = PREFERRED_WINDOW_SIZE
        minimum_width, minimum_height = MINIMUM_WINDOW_SIZE
        if available is None:
            self.resize(preferred_width, preferred_height)
            return
        width = max(minimum_width, min(preferred_width, round(available.width() * 0.92)))
        height = max(minimum_height, min(preferred_height, round(available.height() * 0.90)))
        self.resize(width, height)
        self.move(
            available.x() + max(0, (available.width() - width) // 2),
            available.y() + max(0, (available.height() - height) // 2),
        )

    @staticmethod
    def _geometry_is_usable(geometry: QRect, available: QRect) -> bool:
        return geometry.width() >= MINIMUM_WINDOW_SIZE[0] and geometry.height() >= MINIMUM_WINDOW_SIZE[1] and geometry.intersects(available)

    def _save_window_geometry(self) -> None:
        self._settings.setValue("window/geometry", self.saveGeometry())
        self._settings.setValue("window/maximized", self.isMaximized())
        self._settings.sync()

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow { background: #f4f7fb; }
            QFrame#sidebar { background: #132238; border: 0; }
            QLabel#brand { color: white; font-size: 21px; font-weight: 700; }
            QLabel#brandCaption { color: #aebbd0; font-size: 12px; }
            QGroupBox { background: white; border: 1px solid #d8e0eb; border-radius: 8px;
                        margin-top: 12px; padding: 12px; font-weight: 700; color: #132238; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; }
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
                "THU THẬP",
                "Tìm kiếm",
                "Xuất TBMT",
                "HSMT / PHÂN TÍCH",
                "Nhật ký",
            ]
        )
        sidebar_layout.addWidget(self.navigation, 1)

        self.pages = QStackedWidget()
        self._build_collection_page()
        self._build_search_page()
        self._build_export_page()
        self._build_document_page()
        self._build_log_page()
        self._long_operation_buttons = (
            self.scan_button,
            self.crawl_button,
            self.export_button,
            self.export_snapshot_button,
            self.login_button,
            self.document_import_button,
            self.document_web_button,
            self.document_workspace_button,
        )
        self.navigation.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.navigation.setCurrentRow(0)

        shell.addWidget(sidebar)
        shell.addWidget(self.pages, 1)
        self.setCentralWidget(central)

    def _new_page(
        self,
        title: str,
        description: str,
        *,
        add_to_stack: bool = True,
    ) -> tuple[QWidget, QVBoxLayout]:
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
        if add_to_stack:
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

    @staticmethod
    def _metric_card(value: str, name: str) -> tuple[QFrame, QLabel]:
        card = QFrame()
        card.setObjectName("metricCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 11, 14, 11)
        value_label = QLabel(value)
        value_label.setObjectName("metricValue")
        name_label = QLabel(name)
        name_label.setObjectName("metricName")
        card_layout.addWidget(value_label)
        card_layout.addWidget(name_label)
        return card, value_label

    def _build_collection_page(self) -> None:
        _page, layout = self._new_page(
            "Thu thập gói thầu",
            "Chọn cách thu thập phù hợp: quét danh sách, đọc một URL hoặc đăng nhập nguồn.",
        )
        self.collection_tabs = QTabWidget()
        self.collection_tabs.setObjectName("collectionTabs")
        self.collection_scan_page = self._build_scan_page()
        self.collection_crawl_page = self._build_crawl_page()
        self.collection_login_page = self._build_login_page()
        self.collection_tabs.addTab(self.collection_scan_page, "QUÉT DANH SÁCH")
        self.collection_tabs.addTab(self.collection_crawl_page, "CRAWL URL")
        self.collection_tabs.addTab(self.collection_login_page, "NGUỒN / ĐĂNG NHẬP")
        layout.addWidget(self.collection_tabs, 1)

    def _build_scan_page(self) -> QWidget:
        _page, layout = self._new_page(
            "Quét danh sách gói thầu",
            "Chọn nguồn, giới hạn số trang danh sách và thêm từ khóa nếu chỉ muốn lọc "
            "một nhóm gói cụ thể.",
            add_to_stack=False,
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
        form.addRow("Số trang tối đa:", self.scan_max_pages)
        form.addRow("Từ khóa tùy chọn:", self.scan_keywords)
        layout.addLayout(form)
        self.scan_advanced_options = QGroupBox("TÙY CHỌN NÂNG CAO")
        advanced_form = QFormLayout(self.scan_advanced_options)
        advanced_form.addRow("URL danh sách:", self.scan_url)
        layout.addWidget(self.scan_advanced_options)
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
            card, value = self._metric_card("0", name)
            self.scan_metrics[key] = value
            metrics.addWidget(card, index // 4, index % 4)
        layout.addLayout(metrics)
        layout.addStretch()
        return _page

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
        self.export_button = self._primary_button("XUẤT / CẬP NHẬT BẢN MỚI NHẤT")
        self.export_button.clicked.connect(self.start_export)
        self.export_snapshot_button = QPushButton("LƯU SNAPSHOT")
        self.export_snapshot_button.clicked.connect(self.start_export_snapshot)
        self.export_progress = self._progress_bar()
        self.export_path = QLineEdit()
        self.export_path.setReadOnly(True)
        self.export_status = QLabel("Chưa xuất báo cáo trong phiên làm việc này.")
        self.export_status.setWordWrap(True)
        self.open_export_button = QPushButton("MỞ BÁO CÁO")
        self.open_export_button.setEnabled(False)
        self.open_export_button.clicked.connect(self.open_export)
        self.open_export_folder_button = QPushButton("MỞ THƯ MỤC")
        self.open_export_folder_button.clicked.connect(self.open_export_folder)
        actions = QHBoxLayout()
        actions.addWidget(self.export_button)
        actions.addWidget(self.export_snapshot_button)
        actions.addStretch()
        layout.addLayout(actions)
        layout.addWidget(self.export_progress)
        layout.addWidget(self.export_status)
        layout.addWidget(QLabel("File đã xuất:"))
        layout.addWidget(self.export_path)
        open_actions = QHBoxLayout()
        open_actions.addWidget(self.open_export_button)
        open_actions.addWidget(self.open_export_folder_button)
        open_actions.addStretch()
        layout.addLayout(open_actions)
        layout.addStretch()

    def _build_crawl_page(self) -> QWidget:
        _page, layout = self._new_page(
            "Crawl một gói cụ thể",
            "Dùng khi bạn đã có URL trang chi tiết của một gói thầu và muốn lưu ngay vào hệ thống.",
            add_to_stack=False,
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
        return _page

    def _build_login_page(self) -> QWidget:
        _page, layout = self._new_page(
            "Đăng nhập nguồn đấu thầu",
            "QI-Crawler mở trình duyệt để bạn tự đăng nhập. Công cụ không lưu mật khẩu, "
            "OTP hoặc CAPTCHA.",
            add_to_stack=False,
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
        return _page

    def _build_document_page(self) -> None:
        _page, page_layout = self._new_page(
            "HSMT / Phân tích",
            "Chọn một gói đã lưu để quản lý bộ HSMT, nguồn web và các phiên bản tài liệu. "
            "QI-Crawler chỉ lưu khi Identity Guard xác nhận liên kết an toàn.",
        )
        self.document_scroll = QScrollArea()
        self.document_scroll.setWidgetResizable(True)
        self.document_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.document_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.document_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        document_content = QWidget()
        layout = QVBoxLayout(document_content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        self.document_scroll.setWidget(document_content)
        page_layout.addWidget(self.document_scroll, 1)

        selected_box = QGroupBox("A. GÓI THẦU ĐANG CHỌN")
        selected_layout = QVBoxLayout(selected_box)
        form = QFormLayout()
        form.setHorizontalSpacing(20)
        form.setVerticalSpacing(12)
        self.document_tender = QLineEdit()
        self.document_tender.setPlaceholderText("Ví dụ: IB2600436179-00")
        self.document_tender.editingFinished.connect(self.start_document_workspace)
        form.addRow("Mã TBMT:", self.document_tender)
        selected_layout.addLayout(form)

        self.document_identity_banner = QLabel()
        self.document_identity_banner.setWordWrap(True)
        self.document_identity_banner.setVisible(False)
        self.document_tender_summary = QLabel(
            "Chưa chọn gói. Nhập mã TBMT rồi chọn/đổi gói để xem bộ tài liệu đã lưu."
        )
        self.document_tender_summary.setWordWrap(True)
        self.document_workspace_button = QPushButton("CHỌN / ĐỔI GÓI")
        self.document_workspace_button.clicked.connect(self.start_document_workspace)
        self.manual_workspace_button = QPushButton("+ TẠO GÓI TỪ TEAM BID")
        self.manual_workspace_button.clicked.connect(self.open_manual_workspace_dialog)
        selected_layout.addWidget(self.document_tender_summary)
        selected_actions = QHBoxLayout()
        selected_actions.addWidget(self.document_workspace_button)
        selected_actions.addWidget(self.manual_workspace_button)
        selected_actions.addStretch()
        selected_layout.addLayout(selected_actions)
        selected_layout.addWidget(self.document_identity_banner)
        layout.addWidget(selected_box)

        intake_box = QGroupBox("B. THÊM TÀI LIỆU")
        intake_layout = QVBoxLayout(intake_box)
        self.document_name = QLineEdit()
        self.document_name.hide()
        self.document_path = QLineEdit()
        self.document_path.setReadOnly(True)
        self.document_path.hide()

        picker_row = QHBoxLayout()
        self.document_file_button = QPushButton("THÊM FILE")
        self.document_file_button.clicked.connect(self._choose_document_file)
        self.document_folder_button = QPushButton("Chọn thư mục")
        self.document_folder_button.clicked.connect(self._choose_document_folder)
        picker_row.addWidget(self.document_file_button)
        picker_row.addWidget(self.document_folder_button)
        self.document_web_button = QPushButton("TÌM TRÊN WEB")
        self.document_web_button.clicked.connect(self.start_web_document_intake)
        picker_row.addWidget(self.document_web_button)
        picker_row.addStretch()
        intake_layout.addLayout(picker_row)

        self.document_pending_label = QLabel("Chờ chọn file hoặc thư mục.")
        self.document_pending_label.setObjectName("documentPending")
        self.document_pending_label.setWordWrap(True)
        intake_layout.addWidget(self.document_pending_label)

        self.document_import_button = self._primary_button("LƯU TÀI LIỆU")
        self.document_import_button.clicked.connect(self.start_document_intake)
        self.document_folder_button.setText("THÊM THƯ MỤC")
        self.document_progress = self._progress_bar()
        self.document_status = QLabel("Chưa nhập tài liệu trong phiên làm việc này.")
        self.document_status.setWordWrap(True)
        intake_layout.addWidget(self.document_import_button, alignment=Qt.AlignmentFlag.AlignLeft)
        intake_layout.addWidget(self.document_progress)
        intake_layout.addWidget(self.document_status)
        layout.addWidget(intake_box)

        collection_box = QGroupBox("C. BỘ TÀI LIỆU")
        collection_layout = QVBoxLayout(collection_box)
        self.document_metrics: dict[str, QLabel] = {}
        for key in (
            "total",
            "verified",
            "candidate",
            "needs_review",
            "unknown",
            "duplicates",
        ):
            metric = QLabel("0", collection_box)
            metric.hide()
            self.document_metrics[key] = metric
        self.document_table = QTableWidget(0, 6)
        self.document_table.setHorizontalHeaderLabels(
            (
                "Tên file",
                "Loại tài liệu",
                "Mẫu hồ sơ",
                "Phiên bản",
                "Identity",
                "Trạng thái phân loại",
            )
        )
        self.document_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.document_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.document_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self.document_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for column in range(1, 6):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
        self.document_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.document_table.setMinimumHeight(150)
        self.document_table.itemSelectionChanged.connect(self._on_document_selected)
        collection_layout.addWidget(self.document_table, 1)

        self.document_type_combo = QComboBox()
        for document_type, label in DOCUMENT_TYPE_LABELS.items():
            self.document_type_combo.addItem(label, document_type.value)
        self.document_template_combo = QComboBox()
        self.document_template_combo.addItem("Chưa xác định", "")
        for code, family in TEMPLATE_REGISTRY.items():
            self.document_template_combo.addItem(f"{code} – {family.label}", code)
        self.document_package_type = QLineEdit()
        self.document_package_type.setPlaceholderText("Không bắt buộc")
        self.document_selection_method = QLineEdit()
        self.document_classification_status = QLabel("Chưa xác định")
        for widget in (
            self.document_type_combo,
            self.document_template_combo,
            self.document_package_type,
            self.document_selection_method,
            self.document_classification_status,
        ):
            widget.hide()
        self.document_confirm_type_button = QPushButton("XÁC NHẬN LOẠI")
        self.document_confirm_type_button.setEnabled(False)
        self.document_confirm_type_button.hide()
        self.document_confirm_type_button.clicked.connect(self.confirm_document_type)

        document_actions = QHBoxLayout()
        self.open_document_button = QPushButton("MỞ FILE")
        self.open_document_button.setEnabled(False)
        self.open_document_button.hide()
        self.open_document_button.clicked.connect(self.open_document)
        self.open_document_folder_button = QPushButton("MỞ THƯ MỤC")
        self.open_document_folder_button.setEnabled(False)
        self.open_document_folder_button.hide()
        self.open_document_folder_button.clicked.connect(self.open_document_folder)
        document_actions.addWidget(self.document_confirm_type_button)
        document_actions.addWidget(self.open_document_button)
        document_actions.addWidget(self.open_document_folder_button)
        document_actions.addStretch()
        collection_layout.addLayout(document_actions)
        layout.addWidget(collection_box, 1)

        self.document_extraction_box = QGroupBox("D. KẾT QUẢ ĐỌC TÀI LIỆU")
        extraction_layout = QVBoxLayout(self.document_extraction_box)
        self.document_extraction_summary = QLabel("Chọn một tài liệu để xem kết quả đọc native.")
        self.document_extraction_summary.setWordWrap(True)
        extraction_layout.addWidget(self.document_extraction_summary)
        self.document_evidence_button = QPushButton("XEM EVIDENCE")
        self.document_evidence_button.clicked.connect(self.show_document_evidence)
        self.document_evidence_button.hide()
        extraction_layout.addWidget(
            self.document_evidence_button,
            alignment=Qt.AlignmentFlag.AlignLeft,
        )
        self.document_evidence_view = QTextEdit()
        self.document_evidence_view.setReadOnly(True)
        self.document_evidence_view.setMinimumHeight(160)
        self.document_evidence_view.hide()
        extraction_layout.addWidget(self.document_evidence_view)
        layout.addWidget(self.document_extraction_box)

        self.hsmt_dashboard_box = QGroupBox("E. TỔNG HỢP HSMT")
        dashboard_layout = QGridLayout(self.hsmt_dashboard_box)
        self.hsmt_fact_cards: dict[str, QPushButton] = {}
        for index, (group, label) in enumerate(
            (
                ("PACKAGE_OVERVIEW", "TỔNG QUAN GÓI"),
                ("CHAPTER_III_EVALUATION", "TIÊU CHUẨN ĐÁNH GIÁ"),
                ("CHAPTER_V_TECHNICAL", "YÊU CẦU KỸ THUẬT"),
                ("BOM_SUPPLY", "YÊU CẦU CUNG ỨNG"),
                ("SCHEDULE_SOW", "THỜI GIAN & SCOPE OF WORK"),
                ("REQUIRED_DOCUMENTS", "HỒ SƠ / CHỨNG TỪ"),
                ("MISSING_INFORMATION", "THÔNG TIN CÒN THIẾU"),
            )
        ):
            button = QPushButton(f"{label}\nChưa có dữ liệu")
            button.setEnabled(False)
            button.clicked.connect(lambda _checked=False, value=group: self.show_hsmt_fact_group(value))
            self.hsmt_fact_cards[group] = button
            dashboard_layout.addWidget(button, index // 2, index % 2)
        layout.addWidget(self.hsmt_dashboard_box)

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

    @Slot()
    def _choose_document_file(self) -> None:
        selected, _filter = QFileDialog.getOpenFileName(
            self,
            "Chọn HSMT / tài liệu",
            "",
            "Tài liệu hỗ trợ (*.pdf *.docx *.xlsx *.zip)",
        )
        if selected:
            self.document_path.setText(selected)
            self._render_pending_document(Path(selected), "File chờ lưu")

    @Slot()
    def _choose_document_folder(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Chọn thư mục tài liệu")
        if selected:
            self.document_path.setText(selected)
            self._render_pending_document(Path(selected), "Thư mục chờ lưu")

    def _render_pending_document(self, path: Path, kind: str) -> None:
        suffix = path.suffix.upper().lstrip(".") or "THƯ MỤC"
        self.document_pending_label.setText(
            f"{kind}: {path.name}\n{suffix} | {path}"
        )

    def _set_document_identity_banner(
        self,
        message: str | None = None,
        *,
        critical: bool = False,
    ) -> None:
        if not message:
            self.document_identity_banner.clear()
            self.document_identity_banner.setVisible(False)
            self.document_identity_banner.setStyleSheet("")
            return
        self.document_identity_banner.setText(message)
        self.document_identity_banner.setVisible(True)
        color = "#b42318" if critical else "#175cd3"
        background = "#fef3f2" if critical else "#eff8ff"
        self.document_identity_banner.setStyleSheet(
            f"color: {color}; background: {background}; border-radius: 6px; padding: 10px;"
        )

    @staticmethod
    def _identity_label(status: str) -> str:
        return {
            "VERIFIED_LINKED": "Đúng gói",
            "DOCUMENT_VERIFIED": "Đúng gói (xác thực từ nội dung)",
            "HUMAN_DECLARED": "Team Bid cung cấp (đã khai báo)",
            "UNLINKED": "Chưa liên kết",
            "NEEDS_REVIEW": "Cần kiểm tra",
            "MISMATCH": "Sai gói – đã chặn",
            "DUPLICATE": "File đã tồn tại",
        }.get(status, status or "Chưa xác định")

    @Slot()
    def open_manual_workspace_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Tạo gói từ Team Bid")
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        tender_code = QLineEdit()
        tender_code.setPlaceholderText("Ví dụ: IB2500585490")
        package_name = QLineEdit()
        shortlisted = QCheckBox("Team Bid đã sơ tuyển")
        priority = QComboBox()
        for value, label in (
            ("LOW", "Thấp"),
            ("NORMAL", "Bình thường"),
            ("HIGH", "Cao"),
            ("CRITICAL", "Khẩn cấp"),
        ):
            priority.addItem(label, value)
        reviewed_by = QLineEdit()
        note = QTextEdit()
        note.setFixedHeight(70)
        form.addRow("Mã TBMT / mã gói:", tender_code)
        form.addRow("Tên gói:", package_name)
        form.addRow("Sơ tuyển:", shortlisted)
        form.addRow("Mức ưu tiên:", priority)
        form.addRow("Người review:", reviewed_by)
        form.addRow("Ghi chú:", note)
        layout.addLayout(form)
        create_button = self._primary_button("TẠO WORKSPACE")
        cancel_button = QPushButton("Hủy")
        row = QHBoxLayout()
        row.addWidget(create_button)
        row.addWidget(cancel_button)
        row.addStretch()
        layout.addLayout(row)
        cancel_button.clicked.connect(dialog.reject)

        def create_workspace() -> None:
            code = tender_code.text().strip()
            if not code:
                QMessageBox.warning(dialog, "QI-Crawler", "Vui lòng nhập mã TBMT / mã gói.")
                return
            dialog.accept()
            self.document_status.setText("Đang tạo workspace Team Bid...")
            self._submit(
                run_create_manual_tender_workspace,
                self.config,
                code,
                package_name.text().strip(),
                shortlisted.isChecked(),
                str(priority.currentData()),
                reviewed_by.text().strip(),
                note.toPlainText().strip(),
                on_success=self._render_manual_workspace,
                button=self.manual_workspace_button,
                progress=self.document_progress,
                status=self.document_status,
                task_name="manual_tender_workspace",
                long_operation=True,
            )

        create_button.clicked.connect(create_workspace)
        dialog.exec()

    def _render_manual_workspace(self, manifest: TenderDocumentManifest) -> None:
        self.document_tender.setText(manifest.tender_identifier)
        self._render_document_workspace(manifest)
        self.document_status.setText("✓ Đã tạo workspace Team Bid. Có thể thêm tài liệu ngay.")

    def start_document_workspace(self) -> None:
        tender_reference = self.document_tender.text().strip()
        if not tender_reference:
            self.document_tender_summary.setText(
                "Nhập Tender / mã TBMT đã lưu để xem bộ HSMT."
            )
            return
        self.document_status.setText("Đang tải danh sách tài liệu của gói...")
        self._submit(
            run_tender_document_workspace,
            self.config,
            tender_reference,
            on_success=self._render_document_workspace,
            button=self.document_workspace_button,
            progress=self.document_progress,
            status=self.document_status,
            task_name="document_workspace",
            long_operation=True,
        )

    def _render_document_workspace(self, manifest: TenderDocumentManifest) -> None:
        if self._document_workspace_tender != manifest.tender_identifier:
            self._document_workspace_tender = manifest.tender_identifier
            self._document_session_duplicates = 0
        self.document_tender.setText(manifest.tender_identifier)
        _base, separator, revision = manifest.tender_identifier.rpartition("-")
        workspace_revision = revision if separator and revision.isdigit() else "—"
        self.document_tender_summary.setText(
            "\n".join(
                [
                    f"Mã gói: {manifest.tender_identifier}",
                    f"Revision: {workspace_revision}",
                    f"Tên gói: {manifest.tender_title}",
                    f"Nguồn: {manifest.source}",
                    f"Identity: {self._identity_label(manifest.identity_status)}",
                ]
            )
        )
        if manifest.identity_status == "HUMAN_DECLARED":
            self._set_document_identity_banner(
                f"✓ Team Bid cung cấp: {manifest.tender_identifier}. Chưa xác minh từ web.",
            )
        else:
            self._set_document_identity_banner(
                f"✓ Tender đã được xác minh: {manifest.tender_identifier}",
            )
        self.document_table.setRowCount(0)
        self.document_table.clearSelection()
        self._hide_document_context_actions()
        for row, item in enumerate(manifest.documents):
            self.document_table.insertRow(row)
            values = (
                item.filename,
                self._document_type_label(item.document_type),
                item.template_code or "—",
                f"v{item.version}",
                self._identity_label(item.status),
                self._classification_label(item.classification_status),
            )
            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                if column == 0:
                    cell.setData(Qt.ItemDataRole.UserRole, item)
                self.document_table.setItem(row, column, cell)
        self._update_document_metrics(manifest)
        self._refresh_hsmt_fact_dashboard(manifest.tender_id)
        self.document_status.setText(
            f"Đã tải bộ HSMT: {len(manifest.documents)} tài liệu."
        )
        if not manifest.documents:
            self.last_document_id = None
            self.last_document_path = None
            self._hide_document_context_actions()

    def _refresh_hsmt_fact_dashboard(self, tender_id: int) -> None:
        try:
            dashboard = run_hsmt_fact_dashboard(self.config, tender_id)
        except Exception:
            logger.exception("Cannot read persisted HSMT facts")
            self._hsmt_fact_dashboard = None
            for button in self.hsmt_fact_cards.values():
                button.setText("Chưa thể đọc dữ liệu HSMT")
                button.setEnabled(False)
            return
        self._hsmt_fact_dashboard = dashboard
        for group, button in self.hsmt_fact_cards.items():
            count = dashboard.count_for(group)
            review = dashboard.review_count_for(group)
            button.setText(f"{button.text().split(chr(10))[0]}\n{count} hạng mục | {review} cần kiểm tra")
            button.setEnabled(bool(count))

    @Slot()
    def show_hsmt_fact_group(self, group: str) -> None:
        dashboard = self._hsmt_fact_dashboard
        if dashboard is None:
            return
        facts = [item for item in dashboard.facts if item.fact_group == group]
        dialog = QDialog(self)
        dialog.setWindowTitle("Chi tiết thông tin HSMT")
        layout = QVBoxLayout(dialog)
        table = QTableWidget(len(facts), 3)
        table.setHorizontalHeaderLabels(("Thông tin", "Giá trị", "Trạng thái"))
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        for row, fact in enumerate(facts):
            table.setItem(row, 0, QTableWidgetItem(self._hsmt_fact_label(fact.fact_key)))
            table.setItem(row, 1, QTableWidgetItem(fact.value or "Chưa tìm thấy"))
            table.setItem(row, 2, QTableWidgetItem(fact.status))
            table.item(row, 0).setData(Qt.ItemDataRole.UserRole, fact)
        detail = QTextEdit()
        detail.setReadOnly(True)
        def render_detail() -> None:
            selected = table.selectedItems()
            if not selected:
                return
            fact = selected[0].data(Qt.ItemDataRole.UserRole)
            if fact is None:
                return
            detail.setPlainText(
                "\n".join(
                    (
                        f"Nguồn: {fact.filename or '-'}",
                        f"Vị trí: {fact.source_locator or '-'}",
                        f"Trạng thái: {fact.status}",
                        "Evidence:",
                        fact.raw_evidence_text or "Không có evidence văn bản.",
                    )
                )
            )
        table.itemSelectionChanged.connect(render_detail)
        layout.addWidget(table)
        layout.addWidget(detail)
        dialog.resize(900, 580)
        dialog.exec()

    @staticmethod
    def _hsmt_fact_label(value: str) -> str:
        return {
            "PACKAGE_PURPOSE": "Mục đích gói thầu",
            "SELECTION_METHOD": "Hình thức lựa chọn",
            "SELECTION_PROCEDURE": "Phương thức lựa chọn",
            "CONTRACT_TYPE": "Loại hợp đồng",
            "SUPPLY_REQUIREMENT": "Yêu cầu cung ứng",
            "ITEM_TECHNICAL_SPEC": "Thông số kỹ thuật",
            "EXECUTION_PERIOD": "Thời gian thực hiện",
            "WORK_SCOPE": "Phạm vi công việc",
            "WORK_QUANTITY": "Khối lượng công việc",
            "REQUIRED_DOCUMENTS": "Tài liệu yêu cầu",
            "SUPPLY_REQUIREMENT_UNCERTAIN": "Yêu cầu cung ứng cần kiểm tra",
            "TECHNICAL_SOURCE_DOCUMENT": "Tài liệu kỹ thuật được tham chiếu",
        }.get(value, "Thông tin HSMT")

    @staticmethod
    def _document_type_label(value: str) -> str:
        document_type = TenderDocumentType._value2member_map_.get(
            value,
            TenderDocumentType.OTHER,
        )
        return DOCUMENT_TYPE_LABELS[document_type]

    @staticmethod
    def _classification_label(value: str) -> str:
        status = ClassificationStatus._value2member_map_.get(
            value,
            ClassificationStatus.UNKNOWN,
        )
        return CLASSIFICATION_STATUS_LABELS[status]

    def _update_document_metrics(self, manifest: TenderDocumentManifest) -> None:
        classifications = [item.classification_status for item in manifest.documents]
        counts = {
            "total": len(manifest.documents),
            "verified": sum(value == "VERIFIED" for value in classifications),
            "candidate": sum(value == "CANDIDATE" for value in classifications),
            "needs_review": sum(value == "NEEDS_REVIEW" for value in classifications),
            "unknown": sum(value == "UNKNOWN" for value in classifications),
            "duplicates": self._document_session_duplicates,
        }
        for key, label in self.document_metrics.items():
            label.setText(str(counts[key]))

    @Slot()
    def _on_document_selected(self) -> None:
        selected = self.document_table.selectedItems()
        if not selected:
            self._hide_document_context_actions()
            return
        item = selected[0].data(Qt.ItemDataRole.UserRole)
        if not isinstance(item, DocumentManifestEntry):
            return
        self.last_document_id = item.document_id
        self.last_document_path = item.stored_path
        self.open_document_button.setEnabled(True)
        self.open_document_button.show()
        self.open_document_folder_button.setEnabled(True)
        self.open_document_folder_button.show()
        self.document_confirm_type_button.setEnabled(item.status == "VERIFIED_LINKED")
        self.document_confirm_type_button.setVisible(item.status == "VERIFIED_LINKED")
        self.document_type_combo.setCurrentIndex(
            self.document_type_combo.findData(item.document_type)
        )
        self.document_template_combo.setCurrentIndex(
            max(self.document_template_combo.findData(item.template_code or ""), 0)
        )
        self.document_classification_status.setText(
            self._classification_label(item.classification_status)
        )
        try:
            self._render_document_extraction_inspection(
                run_document_extraction_inspection(self.config, item.document_id)
            )
        except Exception:
            logger.exception("Cannot read persisted native extraction")
            self.document_extraction_summary.setText("Chưa thể đọc kết quả native. Xem Nhật ký để kiểm tra.")
            self.document_evidence_button.hide()
            self.document_evidence_view.clear()
            self.document_evidence_view.hide()
            self._selected_extraction = None

    def _hide_document_context_actions(self) -> None:
        for button in (
            self.document_confirm_type_button,
            self.document_evidence_button,
            self.open_document_button,
            self.open_document_folder_button,
        ):
            button.setEnabled(False)
            button.hide()
        self.document_extraction_summary.setText("Chọn một tài liệu để xem kết quả đọc native.")
        self.document_evidence_view.hide()
        self.document_evidence_view.clear()
        self._selected_extraction = None

    def _render_document_extraction_inspection(
        self,
        inspection: DocumentExtractionInspection,
    ) -> None:
        flags = ", ".join(inspection.flags) or (
            "-" if inspection.status == "NOT_EXTRACTED" else "NATIVE_OK"
        )
        unit_count = (
            f"Trang: {inspection.page_count}"
            if inspection.page_count
            else f"Sheet: {inspection.sheet_count}"
        )
        self.document_extraction_summary.setText(
            "Kết quả đọc native: "
            f"{inspection.status} | Định dạng: {inspection.file_format} | {unit_count} | "
            f"Text: {inspection.text_count} | Bảng: {inspection.table_count} | "
            f"Evidence: {inspection.evidence_count} | Cờ: {flags}"
        )
        self._selected_extraction = inspection
        self.document_evidence_button.setEnabled(bool(inspection.evidence))
        self.document_evidence_button.setVisible(bool(inspection.evidence))
        self.document_evidence_view.clear()
        self.document_evidence_view.hide()

    @Slot()
    def show_document_evidence(self) -> None:
        inspection = getattr(self, "_selected_extraction", None)
        if not isinstance(inspection, DocumentExtractionInspection):
            return
        lines = [f"Tài liệu: {inspection.filename}"]
        for evidence in inspection.evidence:
            location = evidence.source_locator
            if evidence.sheet_name:
                location = f"{evidence.sheet_name} | {location}"
            value = evidence.text or evidence.table_json or ""
            lines.extend((f"[{evidence.content_type}] {location}", value, ""))
        self.document_evidence_view.setPlainText("\n".join(lines))
        self.document_evidence_view.show()

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
        if isinstance(error, DocumentIdentityMismatch):
            message = "\n".join(
                [
                    "⛔ TÀI LIỆU KHÔNG KHỚP GÓI",
                    f"Expected: {error.expected}",
                    f"Detected: {error.detected}",
                ]
            )
            if status is not None:
                status.setText(message)
            if status is self.document_status:
                self._set_document_identity_banner(message, critical=True)
            self._append_log(
                f"DOCUMENT_IDENTITY_MISMATCH expected={error.expected} "
                f"detected={error.detected}"
            )
            QMessageBox.critical(self, "QI-Crawler", message)
            return
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
        self._start_export(snapshot=False)

    @Slot()
    def start_export_snapshot(self) -> None:
        self._start_export(snapshot=True)

    def _start_export(self, *, snapshot: bool) -> None:
        self.export_status.setText(
            "Đang lưu snapshot Excel TBMT..." if snapshot else "Đang cập nhật báo cáo Excel TBMT..."
        )
        self._submit(
            lambda: run_export(self.config, snapshot=snapshot),
            on_success=self._render_export_result,
            button=self.export_snapshot_button if snapshot else self.export_button,
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
    def open_export_folder(self) -> None:
        folder = self.last_export_path.parent if self.last_export_path else self.config.storage.report_dir
        if not open_path(folder):
            QMessageBox.warning(
                self,
                "QI-Crawler",
                f"Không thể tự mở thư mục. Bạn có thể mở thủ công tại:\n{folder}",
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

    @Slot()
    def start_document_intake(self) -> None:
        value = self.document_path.text().strip()
        if not value:
            self.document_status.setText("Vui lòng chọn một file hoặc thư mục tài liệu.")
            return
        input_path = Path(value)
        identity = self._document_identity_for_workspace_switch(input_path)
        if self._requires_document_workspace_switch(identity):
            self._request_document_workspace_switch(input_path, identity)
            return
        self._submit_document_intake(
            input_path,
            self.document_tender.text().strip(),
            self.document_name.text().strip(),
        )

    @staticmethod
    def _base_tender_identifier(value: str) -> str:
        normalized = value.strip().upper()
        base, separator, revision = normalized.rpartition("-")
        return base if separator and revision.isdigit() else normalized

    @staticmethod
    def _document_identity_for_workspace_switch(path: Path) -> DocumentContentIdentity:
        if not path.is_file():
            return DocumentContentIdentity()
        return extract_document_identity(path)

    def _requires_document_workspace_switch(
        self,
        identity: DocumentContentIdentity,
    ) -> bool:
        current = self._base_tender_identifier(
            self._document_workspace_tender or self.document_tender.text()
        )
        return bool(
            current
            and identity.status == "FOUND"
            and identity.base_notice_id
            and current != identity.base_notice_id
        )

    def _request_document_workspace_switch(
        self,
        input_path: Path,
        identity: DocumentContentIdentity,
    ) -> None:
        detected_base = identity.base_notice_id
        detected_raw = identity.raw_notice_id
        if not detected_base or not detected_raw:
            return
        choice = self._confirm_document_workspace_switch(
            self._document_workspace_tender or self.document_tender.text(),
            detected_raw,
            detected_base,
        )
        if choice != "switch":
            if choice == "choose_other":
                self.document_path.clear()
                self.document_name.clear()
                self.document_pending_label.setText("Chờ chọn file hoặc thư mục.")
            return
        display_name = self.document_name.text().strip()
        self._clear_document_workspace_transient_state()
        self.document_status.setText(f"Đang mở gói HSMT {detected_base}...")
        self._submit(
            run_workspace_document_intake,
            self.config,
            input_path,
            detected_base,
            display_name,
            on_success=self._render_workspace_document_intake,
            button=self.document_workspace_button,
            progress=self.document_progress,
            status=self.document_status,
            task_name="open_document_workspace",
            long_operation=True,
        )

    def _confirm_document_workspace_switch(
        self,
        current_base: str,
        detected_raw: str,
        detected_base: str,
    ) -> str:
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Warning)
        dialog.setWindowTitle("Phát hiện một gói HSMT khác")
        dialog.setText("PHÁT HIỆN MỘT GÓI HSMT KHÁC")
        dialog.setInformativeText(
            f"Gói hiện tại: {self._base_tender_identifier(current_base)}\n"
            f"Gói phát hiện: {detected_raw}\n\n"
            "Mỗi gói HSMT được lưu trong một workspace riêng."
        )
        switch = dialog.addButton(
            f"MỞ / TẠO GÓI {detected_base}",
            QMessageBox.ButtonRole.AcceptRole,
        )
        choose_other = dialog.addButton(
            "CHỌN FILE KHÁC",
            QMessageBox.ButtonRole.DestructiveRole,
        )
        cancel = dialog.addButton("HỦY", QMessageBox.ButtonRole.RejectRole)
        dialog.exec()
        if dialog.clickedButton() is switch:
            return "switch"
        if dialog.clickedButton() is choose_other:
            return "choose_other"
        assert dialog.clickedButton() is cancel or dialog.clickedButton() is None
        return "cancel"

    def _clear_document_workspace_transient_state(self) -> None:
        self.document_path.clear()
        self.document_name.clear()
        self.document_pending_label.setText("Chờ chọn file hoặc thư mục.")
        self.last_document_id = None
        self.last_document_path = None
        self._document_session_duplicates = 0
        self._set_document_identity_banner()
        self.document_table.setRowCount(0)
        self.document_table.clearSelection()
        self._hide_document_context_actions()
        self._hsmt_fact_dashboard = None
        for button in self.hsmt_fact_cards.values():
            button.setText(f"{button.text().split(chr(10))[0]}\nChưa có dữ liệu")
            button.setEnabled(False)

    def _render_workspace_document_intake(self, result: Any) -> None:
        self._render_document_workspace(result.manifest)
        self._render_document_result(result.batch)

    def _submit_document_intake(
        self,
        input_path: Path,
        tender_reference: str,
        document_name: str,
    ) -> None:
        self.last_document_id = None
        self.last_document_path = None
        self._hide_document_context_actions()
        self._set_document_identity_banner()
        self.document_status.setText("Đang kiểm tra và lưu bản gốc an toàn...")
        self._submit(
            run_document_intake,
            self.config,
            input_path,
            tender_reference,
            document_name,
            "",
            on_success=self._render_document_result,
            button=self.document_import_button,
            progress=self.document_progress,
            status=self.document_status,
            task_name="document_intake",
            long_operation=True,
        )

    @Slot()
    def start_web_document_intake(self) -> None:
        tender_reference = self.document_tender.text().strip()
        if not tender_reference:
            self.document_status.setText(
                "Vui lòng nhập Tender / mã TBMT đã lưu trước khi tìm tài liệu trên web."
            )
            return
        self.last_document_id = None
        self.last_document_path = None
        self._hide_document_context_actions()
        self._set_document_identity_banner()
        self.document_status.setText("Đang phát hiện và tải tài liệu từ trang tender...")
        self._submit(
            run_web_document_intake,
            self.config,
            tender_reference,
            on_success=self._render_web_document_result,
            button=self.document_web_button,
            progress=self.document_progress,
            status=self.document_status,
            task_name="web_document_intake",
            long_operation=True,
        )

    def _render_web_document_result(self, summary: WebDocumentIntakeSummary) -> None:
        if summary.results:
            result = summary.results[-1]
            self.last_document_path = result.stored_path
            self.last_document_id = result.document_id
            self.open_document_button.setEnabled(True)
            self.open_document_button.show()
            self.open_document_folder_button.setEnabled(True)
            self.open_document_folder_button.show()
            is_verified = result.identity_status in {"VERIFIED_LINKED", "DOCUMENT_VERIFIED"}
            self.document_confirm_type_button.setEnabled(is_verified)
            self.document_confirm_type_button.setVisible(is_verified)
        if self._document_workspace_tender != summary.tender_identifier:
            self._document_workspace_tender = summary.tender_identifier
            self._document_session_duplicates = 0
        self._document_session_duplicates += summary.duplicates
        self.document_tender.setText(summary.tender_identifier)
        self.document_status.setText(
            "\n".join(
                [
                    f"Mã gói: {summary.tender_identifier}",
                    f"Đã phát hiện: {summary.discovered}",
                    f"Đã tải: {summary.downloaded}",
                    f"Trùng: {summary.duplicates}",
                    f"Cần kiểm tra: {summary.needs_review}",
                    f"Lỗi: {summary.failed}",
                ]
            )
        )
        self._append_log(
            "Tìm tài liệu web hoàn tất: "
            f"discovered={summary.discovered} downloaded={summary.downloaded} "
            f"duplicates={summary.duplicates} needs_review={summary.needs_review} "
            f"failed={summary.failed}."
        )
        self.document_metrics["duplicates"].setText(str(self._document_session_duplicates))

    def _render_document_result(self, batch: DocumentBatchResult) -> None:
        if not batch.results:
            self.document_status.setText("Không có tài liệu hỗ trợ trong lựa chọn này.")
            return
        result = batch.results[-1]
        self.last_document_path = result.stored_path
        self.last_document_id = result.document_id
        self.open_document_button.setEnabled(True)
        self.open_document_button.show()
        self.open_document_folder_button.setEnabled(True)
        self.open_document_folder_button.show()
        is_verified = result.identity_status in {"VERIFIED_LINKED", "DOCUMENT_VERIFIED"}
        self.document_confirm_type_button.setEnabled(is_verified)
        self.document_confirm_type_button.setVisible(is_verified)
        document_type = (
            TenderDocumentType(result.document_type)
            if result.document_type in TenderDocumentType._value2member_map_
            else TenderDocumentType.OTHER
        )
        self.document_type_combo.setCurrentIndex(
            self.document_type_combo.findData(document_type.value)
        )
        template_index = self.document_template_combo.findData(result.template_code or "")
        self.document_template_combo.setCurrentIndex(max(template_index, 0))
        self.document_package_type.setText(result.package_type or "")
        self.document_selection_method.setText(result.selection_method or "")
        classification_status = ClassificationStatus._value2member_map_.get(
            result.classification_status,
            ClassificationStatus.UNKNOWN,
        )
        self.document_classification_status.setText(
            CLASSIFICATION_STATUS_LABELS[classification_status]
        )
        tender = result.tender_identifier or result.expected_identity or "Chưa liên kết"
        outcome = "Đã nhập tài liệu" if result.outcome == "IMPORTED" else "Tài liệu đã tồn tại"
        identity = self._identity_label(result.identity_status)
        lines = [
            f"✓ {outcome}",
            f"Mã gói: {tender}",
            f"Identity: {identity}",
            f"Mã trong nội dung: {result.raw_notice_id or '-'}",
            f"Revision: {result.notice_revision or '-'}",
            f"Tên file: {result.original_filename}",
            f"Loại file: {result.file_format or '-'}",
            f"Loại tài liệu: {DOCUMENT_TYPE_LABELS[document_type]}",
            f"Version: {result.version}",
            f"Tender: {tender}",
        ]
        if len(batch.results) > 1:
            lines.insert(
                1,
                f"Tổng số: {len(batch.results)}; mới: {batch.imported}; trùng: {batch.duplicates}",
            )
        if batch.extraction_warnings:
            lines.append("Bóc tách native cần kiểm tra; tài liệu gốc đã được lưu an toàn.")
        self.document_status.setText("\n".join(lines))
        self._append_log(
            f"Nhập tài liệu hoàn tất: mới {batch.imported}, trùng {batch.duplicates}."
        )
        if result.tender_identifier:
            if self._document_workspace_tender != result.tender_identifier:
                self._document_workspace_tender = result.tender_identifier
                self._document_session_duplicates = 0
            self._document_session_duplicates += batch.duplicates
            self.document_tender.setText(result.tender_identifier)
            self.document_metrics["duplicates"].setText(
                str(self._document_session_duplicates)
            )

    @Slot()
    def confirm_document_type(self) -> None:
        if self.last_document_id is None:
            self.document_status.setText("Chưa có tài liệu để xác nhận loại.")
            return
        self._submit(
            run_document_classification_confirmation,
            self.config,
            self.last_document_id,
            str(self.document_type_combo.currentData()),
            str(self.document_template_combo.currentData() or ""),
            self.document_package_type.text().strip(),
            self.document_selection_method.text().strip(),
            on_success=self._render_classification_confirmation,
            button=self.document_confirm_type_button,
            progress=self.document_progress,
            status=self.document_status,
            task_name="document_classification_confirmation",
        )

    def _render_classification_confirmation(
        self,
        classification: DocumentClassification,
    ) -> None:
        self.document_classification_status.setText(
            CLASSIFICATION_STATUS_LABELS[classification.status]
        )
        self.document_status.setText(
            "✓ Đã xác nhận loại tài liệu\n"
            f"Loại tài liệu: {DOCUMENT_TYPE_LABELS[classification.document_type]}\n"
            f"Trạng thái: {CLASSIFICATION_STATUS_LABELS[classification.status]}"
        )
        self._append_log(
            "Đã xác nhận phân loại tài liệu "
            f"document_id={self.last_document_id} type={classification.document_type.value}."
        )

    @Slot()
    def open_document(self) -> None:
        if self.last_document_path and not open_path(self.last_document_path):
            QMessageBox.warning(self, "QI-Crawler", "Không thể mở file tài liệu đã lưu.")

    @Slot()
    def open_document_folder(self) -> None:
        if self.last_document_path and not open_path(self.last_document_path.parent):
            QMessageBox.warning(self, "QI-Crawler", "Không thể mở thư mục tài liệu.")

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


def _standalone_smoke_requested(arguments: list[str]) -> bool:
    return any(
        option in arguments
        for option in ("--smoke-test", "--smoke-test-network", "--smoke-test-documents")
    )


def _run_standalone_smoke(arguments: list[str]) -> int:
    """Run release checks before Qt is initialized for headless EXE smoke tests."""
    paths = prepare_standalone_runtime()
    configure_standalone_file_logging(paths.logs_dir / "qi-crawler.log")
    config = load_config(paths.config_path)
    database = Database(config.storage.database_url)
    try:
        database.require_current_schema()
    except SchemaNotReady:
        upgrade_database(config.storage.database_url, backup_dir=paths.data_dir / "backups")
        database.require_current_schema()
    passed = run_standalone_smoke(
        config,
        paths.logs_dir / "standalone-smoke.json",
        include_network="--smoke-test-network" in arguments,
        include_documents="--smoke-test-documents" in arguments,
    )
    return 0 if passed else 2


def main() -> int:
    smoke_requested = is_frozen() and _standalone_smoke_requested(sys.argv)
    if smoke_requested:
        try:
            return _run_standalone_smoke(sys.argv)
        except Exception:
            logger.exception("Standalone smoke test failed")
            return 1

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
