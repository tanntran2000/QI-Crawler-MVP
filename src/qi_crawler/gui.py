"""PySide6 desktop prototype for QI-Crawler Team Bid workflows."""

from __future__ import annotations

import logging
import os
import sys
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
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


class WorkerSignals(QObject):
    finished = Signal(object)
    error = Signal(object)


class FunctionWorker(QRunnable):
    """Execute one application-service call away from the Qt UI thread."""

    def __init__(self, function: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            result = self.function(*self.args, **self.kwargs)
        except Exception as exc:
            logger.exception("GUI worker failed")
            self.signals.error.emit(exc)
        else:
            self.signals.finished.emit(result)


class QICrawlerWindow(QMainWindow):
    def __init__(self, config: AppConfig | None = None) -> None:
        super().__init__()
        self.config = config or load_config()
        self.thread_pool = QThreadPool.globalInstance()
        self.last_export_path: Path | None = None
        self._login_ready: threading.Event | None = None
        self._login_confirmed: threading.Event | None = None
        self.setWindowTitle(f"QI-CRAWLER v{__version__}")
        self.resize(1000, 680)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self._build_scan_tab()
        self._build_search_tab()
        self._build_export_tab()
        self._build_crawl_tab()
        self._build_login_tab()
        self._build_log_tab()
        self.statusBar().showMessage("QI-Crawler da san sang")
        version_label = QLabel(f"QI-Crawler v{__version__}")
        self.statusBar().addPermanentWidget(version_label)

    def _build_scan_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        form = QFormLayout()
        self.scan_url = QLineEdit()
        self.scan_url.setPlaceholderText("https://ebidding.coteccons.vn/Index")
        self.scan_max_pages = QSpinBox()
        self.scan_max_pages.setRange(1, 100)
        self.scan_max_pages.setValue(3)
        self.scan_keywords = QLineEdit()
        self.scan_keywords.setPlaceholderText("De trong = tat ca; vi du: chong tham,son")
        form.addRow("URL danh sach:", self.scan_url)
        form.addRow("So trang toi da:", self.scan_max_pages)
        form.addRow("Tu khoa tuy chon:", self.scan_keywords)
        layout.addLayout(form)
        self.scan_button = QPushButton("Bat dau quet")
        self.scan_button.clicked.connect(self.start_scan)
        layout.addWidget(self.scan_button)
        self.scan_status = QTextEdit()
        self.scan_status.setReadOnly(True)
        self.scan_status.setPlaceholderText("Ket qua quet se hien tai day.")
        layout.addWidget(self.scan_status)
        self.tabs.addTab(tab, "Quet goi thau")

    def _build_search_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        row = QHBoxLayout()
        self.search_keyword = QLineEdit()
        self.search_keyword.setPlaceholderText("Nhap tu khoa, vi du: chong tham")
        self.search_button = QPushButton("Tim kiem")
        self.search_button.clicked.connect(self.start_search)
        row.addWidget(self.search_keyword)
        row.addWidget(self.search_button)
        layout.addLayout(row)
        self.search_table = QTableWidget(0, 5)
        self.search_table.setHorizontalHeaderLabels(
            ["Ma goi", "Ten goi", "Ben moi thau", "Nguon", "URL"]
        )
        self.search_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.search_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        layout.addWidget(self.search_table)
        self.tabs.addTab(tab, "Tim kiem")

    def _build_export_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.export_button = QPushButton("Xuat Excel TBMT")
        self.export_button.clicked.connect(self.start_export)
        self.export_path = QLineEdit()
        self.export_path.setReadOnly(True)
        self.open_export_button = QPushButton("Mo file")
        self.open_export_button.setEnabled(False)
        self.open_export_button.clicked.connect(self.open_export)
        layout.addWidget(self.export_button)
        layout.addWidget(QLabel("File da xuat:"))
        layout.addWidget(self.export_path)
        layout.addWidget(self.open_export_button)
        layout.addStretch()
        self.tabs.addTab(tab, "Xuat TBMT")

    def _build_crawl_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.crawl_url = QLineEdit()
        self.crawl_url.setPlaceholderText("Dan URL chi tiet mot goi thau")
        self.crawl_button = QPushButton("Crawl mot goi")
        self.crawl_button.clicked.connect(self.start_crawl)
        self.crawl_status = QLabel("Chua chay")
        self.crawl_status.setWordWrap(True)
        layout.addWidget(QLabel("URL goi thau:"))
        layout.addWidget(self.crawl_url)
        layout.addWidget(self.crawl_button)
        layout.addWidget(self.crawl_status)
        layout.addStretch()
        self.tabs.addTab(tab, "Crawl mot URL")

    def _build_login_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.login_source = QLineEdit("egp")
        self.login_button = QPushButton("Mo trinh duyet dang nhap")
        self.login_button.clicked.connect(self.start_login)
        layout.addWidget(QLabel("Ten nguon:"))
        layout.addWidget(self.login_source)
        layout.addWidget(
            QLabel(
                "Ban tu nhap tai khoan, OTP/CAPTCHA neu website yeu cau. "
                "QI-Crawler khong luu mat khau va khong vuot bien phap bao mat."
            )
        )
        layout.addWidget(self.login_button)
        layout.addStretch()
        self.tabs.addTab(tab, "Dang nhap nguon")

    def _build_log_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)
        self.tabs.addTab(tab, "Nhat ky / ket qua")

    def _append_log(self, message: str) -> None:
        self.log_output.append(message)
        self.statusBar().showMessage(message, 10000)

    def _submit(
        self,
        function: Callable[..., Any],
        *args: Any,
        on_success: Callable[[Any], None],
        button: QPushButton,
    ) -> None:
        button.setEnabled(False)
        worker = FunctionWorker(function, *args)
        worker.signals.finished.connect(lambda result: self._worker_success(button, on_success, result))
        worker.signals.error.connect(lambda error: self._worker_error(button, error))
        self.thread_pool.start(worker)

    def _worker_success(
        self,
        button: QPushButton,
        callback: Callable[[Any], None],
        result: Any,
    ) -> None:
        button.setEnabled(True)
        callback(result)

    def _worker_error(self, button: QPushButton, error: Exception) -> None:
        button.setEnabled(True)
        if isinstance(error, AccessDenied):
            self.show_human_required(str(error))
            return
        if isinstance(error, SchemaNotReady):
            message = "Database chua san sang. IT can chay QI-Crawler db-upgrade."
        else:
            message = "Khong the hoan tat thao tac. Du lieu khong bi ghi sai."
        self._append_log(f"LOI: {message} Chi tiet ky thuat: {error}")
        QMessageBox.critical(self, "QI-Crawler", message)

    @Slot()
    def start_scan(self) -> None:
        url = self.scan_url.text().strip()
        if not url:
            self.scan_status.setPlainText("Vui long dan URL danh sach goi thau.")
            return
        if not url.lower().startswith(("http://", "https://")):
            self.scan_status.setPlainText("URL phai bat dau bang http:// hoac https://")
            return
        self.scan_status.setPlainText("Dang quet. Ban van co the di chuyen/click trong ung dung...")
        self._submit(
            run_scan,
            self.config,
            url,
            self.scan_max_pages.value(),
            self.scan_keywords.text().strip(),
            on_success=self._render_scan_result,
            button=self.scan_button,
        )

    def _render_scan_result(self, summary: ScanSummary) -> None:
        self.scan_status.setPlainText(
            "\n".join(
                [
                    f"Da quet: {summary.pages_scanned} trang",
                    f"Tim thay: {summary.discovered} goi",
                    f"Goi moi: {summary.new}",
                    f"Da co/cap nhat: {summary.existing}",
                    f"Thanh cong: {summary.success}",
                    f"Loi: {summary.failed}",
                    f"Cho xu ly: {summary.pending}",
                ]
            )
        )
        self._append_log(f"Quet xong run {summary.run_id or '-'}: {summary.success} thanh cong")

    @Slot()
    def start_search(self) -> None:
        keyword = self.search_keyword.text().strip()
        if not keyword:
            QMessageBox.information(self, "QI-Crawler", "Vui long nhap tu khoa can tim.")
            return
        self._submit(
            run_search,
            self.config,
            keyword,
            on_success=self._render_search_results,
            button=self.search_button,
        )

    def _render_search_results(self, rows: list[SearchRow]) -> None:
        self.search_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column, value in enumerate(
                (row.identifier, row.title, row.buyer, row.source, row.source_url)
            ):
                self.search_table.setItem(row_index, column, QTableWidgetItem(value))
        self._append_log(f"Tim thay {len(rows)} goi phu hop.")

    @Slot()
    def start_export(self) -> None:
        self._submit(
            run_export,
            self.config,
            on_success=self._render_export_result,
            button=self.export_button,
        )

    def _render_export_result(self, result: Any) -> None:
        self.last_export_path = Path(result.output)
        self.export_path.setText(str(self.last_export_path))
        self.open_export_button.setEnabled(True)
        self._append_log(
            f"Da xuat {result.exported_records} dong; canh bao {result.warning_records}: "
            f"{result.output}"
        )

    @Slot()
    def open_export(self) -> None:
        if not self.last_export_path:
            return
        if not open_path(self.last_export_path):
            QMessageBox.warning(
                self,
                "QI-Crawler",
                f"Khong the tu mo file. Ban co the mo thu cong tai:\n{self.last_export_path}",
            )

    @Slot()
    def start_crawl(self) -> None:
        url = self.crawl_url.text().strip()
        if not url:
            self.crawl_status.setText("Vui long dan URL mot goi thau.")
            return
        self.crawl_status.setText("Dang crawl...")
        self._submit(
            run_single_crawl,
            self.config,
            url,
            on_success=self._render_crawl_result,
            button=self.crawl_button,
        )

    def _render_crawl_result(self, result: tuple[int, int, str | None]) -> None:
        success, failed, human_required = result
        if human_required:
            self.show_human_required(human_required)
            return
        self.crawl_status.setText(f"Hoan tat: thanh cong {success}, loi {failed}.")
        self._append_log(self.crawl_status.text())

    @Slot()
    def start_login(self) -> None:
        source_name = self.login_source.text().strip() or "egp"
        self._login_ready = threading.Event()
        self._login_confirmed = threading.Event()
        self._append_log("Dang mo trinh duyet dang nhap...")
        self._submit(
            run_login,
            self.config,
            source_name,
            self._login_ready,
            self._login_confirmed,
            on_success=lambda path: self._append_log(f"Da luu phien cuc bo: {path}"),
            button=self.login_button,
        )
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
            "Dang nhap nguon",
            "Trinh duyet da mo. Hay tu dang nhap va xu ly OTP/CAPTCHA neu website yeu cau.\n\n"
            "Khi da vao trang danh sach goi thau, quay lai day va bam OK.",
        )
        self._login_confirmed.set()

    def show_human_required(self, technical_detail: str) -> None:
        logger.warning("HUMAN_REQUIRED: %s", technical_detail)
        self._append_log(f"HUMAN_REQUIRED: {technical_detail}")
        QMessageBox.warning(
            self,
            "Can nguoi dung xu ly",
            "Phien dang nhap co the da het han, website yeu cau CAPTCHA/OTP, "
            "hoac website tu choi truy cap.\n\n"
            "QI-Crawler khong vuot bien phap bao mat. Du lieu khong bi ghi sai. "
            "Sau khi xu ly nguyen nhan, ban co the chay lai.",
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
