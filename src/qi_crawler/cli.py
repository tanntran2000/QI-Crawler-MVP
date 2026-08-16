from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import UTC, date, datetime
from pathlib import Path
from urllib.parse import urlparse

import typer

from .authenticated_sources import (
    WebSource,
    allow_source_domain,
    collect_authenticated_source,
    create_login_session,
    egp_vietnam_source,
    load_source,
    save_source,
    validate_authenticated_source,
)
from .bid_intelligence import (
    analyze_bid_document,
    confirm_assessment,
    estimate_win_likelihood,
    evaluate_bid_gate,
    import_evidence_csv,
)
from .browser import BrowserFetcher
from .compliance import AccessDenied
from .config import EnvSettings, load_config
from .crawler import CrawlerService
from .db import Database, SchemaNotReady
from .export import export_tbmt
from .exporter import export_csv, export_xlsx
from .importer import import_file as import_data_file
from .inventory import import_inventory, import_tender_items
from .keywords import KeywordExpansion, expand_keyword, learn_keyword
from .legacy_cleanup import archive_legacy_notices
from .logging_utils import configure_logging
from .migrations import backup_database, upgrade_database
from .monitoring import load_monitoring_config, monitor_forever, run_monitoring_cycle
from .notice_search import search_notices
from .reporting import build_daily_report, send_report_email
from .source_filter import active_source_domains, active_source_names
from .warehouse import BACKUP_DIR, WAREHOUSE_PATH, WarehouseManager

logger = logging.getLogger(__name__)


def _show_keyword_plan(expansion: KeywordExpansion) -> None:
    typer.echo(f"Tu khoa san pham: {', '.join(expansion.product_terms)}")
    if expansion.category:
        typer.echo(
            f"Nhom nganh: {expansion.category} "
            f"({', '.join(expansion.category_terms)})"
        )


NORMAL_HELP_EPILOG = """
## QUY TRINH HANG NGAY CHO BID TEAM

### Cach de nhat: mo menu

- **Muc dich:** Chon chuc nang bang phim so, khong can nho cu phap lenh.

- **Cu phap:** `QI-Crawler menu`

- **Vi du:** Double-click `QI-Crawler.bat` tren Windows.

- **Ket qua:** Hien menu quet, tim, xuat Excel, crawl va dang nhap.

### 1. Quet mot trang danh sach goi thau

- **Muc dich:** Tim cac goi tren nhieu trang danh sach va luu vao kho du lieu.

- **Cu phap:** `QI-Crawler scan "LIST_URL" --max-pages N`

- **Vi du:** `QI-Crawler scan "https://ebidding.coteccons.vn/Index" --max-pages 3`

- **Ket qua:** Hien so goi moi, goi da co, thanh cong, loi va dang cho xu ly.

### 2. Quet danh sach va loc theo tu khoa

- **Muc dich:** Chi chon cac goi phu hop voi san pham/dich vu dang quan tam.

- **Cu phap:** `QI-Crawler scan "LIST_URL" -k "TU_KHOA_1,TU_KHOA_2"`

- **Vi du:** `QI-Crawler scan "https://ebidding.coteccons.vn/Index" -k "chong tham,son"`

- **Ket qua:** Cac goi khop tu khoa duoc dua vao hang xu ly va luu vao kho.

### 3. Doc mot URL goi thau cu the

- **Muc dich:** Luu mot goi khi ban da co san link trang chi tiet.

- **Cu phap:** `QI-Crawler crawl "DETAIL_URL"`

- **Vi du:** `QI-Crawler crawl "https://ebidding.coteccons.vn/Index/ChiTiet/2607301"`

- **Ket qua:** Thong tin goi duoc them moi hoac cap nhat trong kho du lieu.

### 4. Tim lai goi da luu

- **Muc dich:** Tim trong kho noi bo; lenh nay khong truy cap website.

- **Cu phap:** `QI-Crawler tim-goi -k "TU_KHOA"`

- **Vi du:** `QI-Crawler tim-goi -k "chong tham"`

- **Ket qua:** Hien danh sach goi phu hop kem ma, nguon va URL doi chieu.

### 5. Xuat file Excel TBMT

- **Muc dich:** Tao file 18 cot de Bid Team kiem tra va trinh noi bo.

- **Cu phap:** `QI-Crawler xuat-tbmt`

- **Vi du:** `QI-Crawler xuat-tbmt --all`

- **Ket qua:** Tao file Excel trong `data\\reports`; dong can kiem tra duoc canh bao rieng.

### 6. Dang nhap nguon co bao ve

- **Muc dich:** Mo trinh duyet de ban tu dang nhap va luu phien cuc bo.

- **Cu phap:** `QI-Crawler dang-nhap --source TEN_NGUON`

- **Vi du:** `QI-Crawler dang-nhap --source egp`

- **Ket qua:** Luu session/cookie; QI-Crawler khong luu mat khau, OTP hay CAPTCHA.

## QUY TRINH DE XUAT

`scan trang danh sach -> xem ket qua -> tim-goi -> xuat-tbmt -> kiem tra file Excel`

## Y NGHIA TRANG THAI

- **New:** Goi moi duoc them vao kho du lieu.

- **Existing:** Goi da co va duoc doi chieu/cap nhat; day **KHONG phai loi**.

- **Success:** Xu ly thanh cong.

- **Warning:** Thieu du lieu tuy chon hoac nguon khong cong bo; van duoc xem/xuat.

- **Failed:** Xu ly khong thanh cong; can xem lai URL hoac log.

- **Pending:** Dang cho xu ly hoac co the tiep tuc sau khi gian doan.

- **HUMAN_REQUIRED:** Can nguoi dung dang nhap, xac minh hoac xu ly chan truy cap.

QI-Crawler **khong bao gio** vuot CAPTCHA, HTTP 403 hoac cac bien phap bao mat cua website.

- Xem tuy chon mot lenh: `QI-Crawler TEN-LENH -help`

- Lenh cho IT/ky thuat: `QI-Crawler -adv`

- Tai lieu: `HUONG_DAN_SU_DUNG.md`
"""


app = typer.Typer(
    no_args_is_help=True,
    invoke_without_command=True,
    add_completion=False,
    rich_markup_mode="markdown",
    context_settings={"help_option_names": ["-help", "--help", "-h"]},
    help="Tro ly giup Bid Team quet, tim va xuat Excel cac goi thau.",
    epilog=NORMAL_HELP_EPILOG,
)

ADVANCED_HELP = """
LENH NANG CAO - DANH CHO IT/NGUOI VAN HANH KY THUAT

  DATABASE VA MIGRATION
  db-upgrade                 Backup va nang cap database bang Alembic
  init-db                    Kiem tra database da dung revision yeu cau
  clean-legacy-sources       Archive du lieu nguon cu sau khi da backup

  NGUON WEBSITE VA CHAN DOAN
  them-nguon                 Them cau hinh mot website duoc phep truy cap
  them-egp                   Tao cau hinh nguon e-GP Viet Nam
  kiem-tra-nguon             Kiem tra session va selector cua nguon
  tim-tren-web               Tim tren website da dang nhap
  discover URL               Quan sat API/JSON phuc vu chan doan
  collect-links URL          Kiem tra link tren trang danh sach tinh
  collect-dynamic URL        Kiem tra link tren trang JavaScript
  crawl-file TEP             Crawl danh sach URL tu file
  resume-crawl RUN_ID        Tiep tuc mot crawl run bi gian doan
  download-page URL          Tai tep dinh kem cua trang chi tiet
  retry-downloads            Thu lai cac tep tai bi loi

  THEO DOI VA BAO CAO KY THUAT
  theo-doi                   Chay chu ky theo doi tu dong
  xep-hang                   Cham diem co hoi mot lan
  report-daily               Tao bao cao van hanh hang ngay
  xuat-bao-cao               Xuat workbook kem cac sheet ky thuat
  serve                      Khoi dong API noi bo de debug/tich hop

  QUAN TRI TU KHOA
  them-tu-khoa               Them va phan loai tu khoa co chu dich

  NHAP LIEU VA CHAN DOAN NOI BO
  import-file TEP            Nhap goi thau tu CSV/Excel
  nhap-ton-kho TEP           Nhap ton kho QI da xac minh
  nhap-boq MA_GOI TEP        Nhap bang so luong cua mot goi
  import-evidence TEP        Nhap bang chung nang luc QI
  analyze-bid TEP            Phan tich compliance legacy/pilot
  warehouse-init             Khoi tao data warehouse cuc bo
  warehouse-status           Kiem tra data warehouse
  warehouse-backup           Sao luu data warehouse
  warehouse-review           Ghi nhan de xuat luu tru du lieu

Xem cu phap: QI-Crawler TEN-LENH -help
"""


@app.callback()
def main_callback(
    advanced: bool = typer.Option(
        False,
        "-adv",
        "--advanced",
        is_eager=True,
        help="Hien danh sach lenh nang cao",
    ),
) -> None:
    """Dieu huong tro giup cho nguoi moi va nguoi van hanh ky thuat."""
    if advanced:
        typer.echo(ADVANCED_HELP.strip())
        raise typer.Exit()


@app.command("help", hidden=True)
def show_help(ctx: typer.Context) -> None:
    """Xem lenh va vi du."""
    if ctx.parent is not None:
        typer.echo(ctx.parent.get_help())


def _config(path: Path | None):
    env = EnvSettings()
    configure_logging(env.log_level)
    return load_config(path)


def _date_option(value: str | None, option_name: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise typer.BadParameter(
            f"{option_name} phai co dang YYYY-MM-DD, vi du 2026-08-10"
        ) from exc


def _show_human_required(reason: str | None = None) -> None:
    """Explain a compliance stop without hiding its technical reason from logs."""
    logger.warning("HUMAN_REQUIRED: %s", reason or "Can nguoi dung xu ly")
    typer.echo("", err=True)
    typer.echo("HUMAN_REQUIRED", err=True)
    typer.echo("", err=True)
    typer.echo("Can nguoi dung xu ly:", err=True)
    typer.echo("- phien dang nhap co the da het han; hoac", err=True)
    typer.echo("- website yeu cau CAPTCHA; hoac", err=True)
    typer.echo("- website tu choi truy cap.", err=True)
    typer.echo("", err=True)
    typer.echo("Du lieu khong bi ghi sai.", err=True)
    typer.echo("Sau khi xu ly nguyen nhan, ban co the chay lai.", err=True)
    if reason:
        typer.echo(f"Chi tiet: {reason}", err=True)


def _open_windows_path(path: Path) -> bool:
    """Open a file/folder on Windows and fail safely on other environments."""
    if sys.platform != "win32":
        typer.echo(f"Khong the tu mo tren he dieu hanh nay. Duong dan: {path}", err=True)
        return False
    try:
        os.startfile(str(path.resolve()))
    except (AttributeError, OSError) as exc:
        logger.exception("Khong the mo duong dan Windows: %s", path)
        typer.echo(f"Khong the tu mo. Ban co the mo thu cong tai: {path}", err=True)
        typer.echo(f"Chi tiet: {exc}", err=True)
        return False
    return True


def _menu_max_pages() -> int:
    while True:
        value = typer.prompt("So trang muon quet", default=3, type=int)
        if 1 <= value <= 100:
            return value
        typer.echo("Vui long nhap so tu 1 den 100.", err=True)


def _show_operator_menu() -> None:
    typer.echo("")
    typer.echo("==============================")
    typer.echo("        QI-CRAWLER")
    typer.echo("==============================")
    typer.echo("")
    typer.echo("1. Quet danh sach goi thau")
    typer.echo("2. Tim goi da luu")
    typer.echo("3. Xuat Excel TBMT")
    typer.echo("4. Crawl mot goi cu the")
    typer.echo("5. Dang nhap nguon dau thau")
    typer.echo("6. Mo thu muc ket qua")
    typer.echo("0. Thoat")
    typer.echo("")


@app.command("menu", rich_help_panel="QUY TRINH BID TEAM")
def operator_menu(
    config: Path | None = typer.Option(None, "--config", exists=True, hidden=True),
) -> None:
    """Mo menu Windows de Bid Team chon chuc nang bang phim so."""
    while True:
        _show_operator_menu()
        try:
            choice = typer.prompt("Chon chuc nang").strip()
        except (EOFError, KeyboardInterrupt):
            typer.echo("\nDa thoat QI-Crawler.")
            return

        try:
            if choice == "0":
                typer.echo("Da thoat QI-Crawler.")
                return
            if choice == "1":
                list_url = typer.prompt("Dan URL danh sach").strip()
                max_pages = _menu_max_pages()
                keywords = typer.prompt(
                    "Tu khoa (Enter = tat ca)", default="", show_default=False
                ).strip()
                scan(
                    list_url=list_url,
                    tu_khoa=keywords or None,
                    max_pages=max_pages,
                    resume=False,
                    config=config,
                )
            elif choice == "2":
                keyword = typer.prompt("Nhap tu khoa can tim").strip()
                if not keyword:
                    typer.echo("Tu khoa khong duoc de trong.", err=True)
                    continue
                tim_goi(tu_khoa=keyword, tu_ngay=None, so_luong=20, config=config)
            elif choice == "3":
                output_path = xuat_tbmt(
                    output=None,
                    ngay=None,
                    tu_ngay=None,
                    den_ngay=None,
                    trang_thai=None,
                    tu_khoa=None,
                    to_canh_bao=False,
                    all_records=False,
                    run_id=None,
                    config=config,
                )
                if typer.confirm("Mo file Excel ngay?", default=True):
                    _open_windows_path(output_path)
            elif choice == "4":
                detail_url = typer.prompt("Dan URL goi thau cu the").strip()
                crawl(urls=[detail_url], source=None, config=config)
            elif choice == "5":
                source_name = typer.prompt("Ten nguon", default="egp").strip()
                dang_nhap(ten=None, source=source_name, config=config)
            elif choice == "6":
                cfg = _config(config)
                cfg.storage.report_dir.mkdir(parents=True, exist_ok=True)
                _open_windows_path(cfg.storage.report_dir)
            else:
                typer.echo("Lua chon khong hop le. Vui long chon tu 0 den 6.", err=True)
        except AccessDenied as exc:
            _show_human_required(str(exc))
        except SchemaNotReady:
            typer.echo("Database chua san sang. Hay chay QI-Crawler db-upgrade.", err=True)
        except typer.Exit:
            # Existing commands already printed the appropriate user-facing message.
            continue
        except Exception as exc:
            logger.exception("Loi khi chay menu QI-Crawler")
            typer.echo("Khong the hoan tat thao tac. Du lieu khong bi ghi sai.", err=True)
            typer.echo(f"Chi tiet: {exc}", err=True)


@app.command("init-db", hidden=True)
def init_db(config: Path | None = typer.Option(None, "--config", exists=True)) -> None:
    cfg = _config(config)
    Database(cfg.storage.database_url).require_current_schema()
    typer.echo(f"Database da san sang: {cfg.storage.database_url}")


@app.command("db-upgrade", hidden=True)
def db_upgrade(
    backup_dir: Path = typer.Option(Path("data/backups"), "--backup-dir"),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Sao luu va nang cap schema bang Alembic; khong xoa du lieu cu."""
    cfg = _config(config)
    result = upgrade_database(cfg.storage.database_url, backup_dir=backup_dir)
    if result.backup_path:
        typer.echo(f"Da sao luu database: {result.backup_path}")
    if result.adopted_legacy_database:
        typer.echo("Da dua database cu co crawl_tasks vao lich su Alembic an toan.")
    typer.echo(f"Database da o revision: {result.revision}")


@app.command("clean-legacy-sources", hidden=True)
def clean_legacy_sources(
    archive_dir: Path = typer.Option(Path("data/archive"), "--archive-dir"),
    backup_dir: Path = typer.Option(Path("data/backups"), "--backup-dir"),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Sao luu, archive va xoa record Contracts Finder/example/test cu."""
    cfg = _config(config)
    db = Database(cfg.storage.database_url)
    db.require_current_schema()
    backup = backup_database(cfg.storage.database_url, backup_dir)
    result = archive_legacy_notices(db, archive_dir=archive_dir, backup_path=backup)
    if result.backup_path:
        typer.echo(f"Da sao luu database: {result.backup_path}")
    if result.archive_path:
        typer.echo(f"Da archive {result.archived_notices} record: {result.archive_path}")
    else:
        typer.echo("Khong tim thay du lieu legacy can archive.")
    if result.backfilled_coteccons:
        typer.echo("Da chuan hoa Coteccons 2607301 voi source_name va source_notice_id.")


@app.command("crawl", rich_help_panel="QUY TRINH BID TEAM")
@app.command("doc-trang", hidden=True)
def crawl(
    urls: list[str] = typer.Argument(..., help="Mot hoac nhieu URL chi tiet duoc phep crawl"),
    source: str | None = typer.Option(
        None, "--source", help="Ten session da dang nhap, vi du egp"
    ),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Doc truc tiep mot hoac nhieu trang chi tiet thau tu URL."""
    cfg = _config(config)

    async def run() -> None:
        service = CrawlerService(cfg)
        try:
            if source:
                profile = load_source(source)
                for url in urls:
                    hostname = (urlparse(url).hostname or "").lower()
                    if hostname != profile.domain and not hostname.endswith(f".{profile.domain}"):
                        raise typer.BadParameter(
                            f"URL khong thuoc domain cua source '{profile.name}': {profile.domain}"
                        )
                service.use_authenticated_session(profile.name)
            ok, failed = await service.crawl_urls(urls)
            typer.echo(f"Hoan tat: thanh cong={ok}, loi={failed}")
            if service.human_required_reason:
                _show_human_required(service.human_required_reason)
        finally:
            await service.close()

    asyncio.run(run())


@app.command(
    "scan",
    rich_help_panel="QUY TRINH BID TEAM",
    epilog="""
## VI DU COTECONS

- Quet toi da 3 **TRANG DANH SACH**:

  `QI-Crawler scan "https://ebidding.coteccons.vn/Index" --max-pages 3`

- Quet va loc nhieu tu khoa (phan tach bang dau phay):

  `QI-Crawler scan "https://ebidding.coteccons.vn/Index" -k "chong tham,son,canh quan"`

## LUU Y

- `--max-pages` la so **TRANG DANH SACH** toi da, khong phai so luong goi thau.

- `-k/--tu-khoa` nhan mot hoac nhieu tu khoa, phan tach bang dau phay.
""",
)
def scan(
    list_url: str = typer.Argument(
        ...,
        metavar="LIST_URL",
        help="URL trang DANH SACH goi thau, khong phai URL chi tiet",
    ),
    tu_khoa: str | None = typer.Option(
        None,
        "--tu-khoa",
        "-k",
        help="Loc theo mot/nhieu tu khoa, cach nhau bang dau phay",
    ),
    max_pages: int = typer.Option(
        25,
        "--max-pages",
        min=1,
        max=100,
        help="So TRANG DANH SACH toi da se quet; khong phai so goi thau",
    ),
    resume: bool = typer.Option(False, "--resume", help="Tiep tuc scan dang do cua cung LIST_URL"),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Quet danh sach, tim link chi tiet va luu cac goi thau vao kho noi bo."""
    cfg = _config(config)
    terms: list[str] = []
    if tu_khoa:
        for raw_keyword in tu_khoa.split(","):
            keyword = raw_keyword.strip()
            if keyword:
                terms.extend(expand_keyword(keyword).search_terms)
    keyword_terms = tuple(dict.fromkeys(terms))

    async def run() -> None:
        service = CrawlerService(cfg)
        try:
            summary = await service.scan_list(
                list_url,
                keyword_terms=keyword_terms,
                max_pages=max_pages,
                resume=resume,
            )
            typer.echo("QUET DANH SACH HOAN TAT")
            typer.echo(
                f"- Da quet {summary.pages_scanned} trang danh sach, "
                f"tim thay {summary.discovered} goi thau."
            )
            typer.echo(
                f"- Phu hop bo loc: {summary.matched}; "
                f"dua vao xu ly: {summary.queued}."
            )
            typer.echo(
                f"- Goi moi: {summary.new}; goi da co: {summary.existing} "
                "(Existing khong phai loi)."
            )
            typer.echo(
                f"- Thanh cong: {summary.success}; loi: {summary.failed}; "
                f"dang cho: {summary.pending}; bo qua: {summary.skipped}."
            )
            if summary.limited:
                typer.echo(
                    f"- Canh bao: {summary.limited} goi vuot gioi han an toan va chua duoc xep hang."
                )
            typer.echo("Buoc tiep theo: QI-Crawler tim-goi -k \"TU_KHOA\"")
            typer.echo("")
            typer.echo("CHI TIET HE THONG")
            if summary.run_id is not None:
                typer.echo(f"Run: {summary.run_id}")
            typer.echo(f"Discovered: {summary.discovered}")
            typer.echo(f"Matched: {summary.matched}")
            typer.echo(f"Queued: {summary.queued}")
            typer.echo(f"Limited: {summary.limited}")
            typer.echo(f"New: {summary.new}")
            typer.echo(f"Existing: {summary.existing}")
            typer.echo(f"Success: {summary.success}")
            typer.echo(f"Failed: {summary.failed}")
            typer.echo(f"Pending: {summary.pending}")
            typer.echo(f"Skipped: {summary.skipped}")
            typer.echo(f"Pages scanned: {summary.pages_scanned}")
        except AccessDenied as exc:
            _show_human_required(str(exc))
            raise typer.Exit(code=1) from None
        finally:
            await service.close()

    asyncio.run(run())


@app.command("crawl-file", hidden=True)
def crawl_file(
    input_file: Path = typer.Argument(..., exists=True, readable=True),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    cfg = _config(config)
    urls = [line.strip() for line in input_file.read_text(encoding="utf-8-sig").splitlines()]
    urls = [url for url in urls if url and not url.startswith("#")]

    async def run() -> None:
        service = CrawlerService(cfg)
        try:
            ok, failed = await service.crawl_urls(urls, source_name=f"file:{input_file.name}")
            typer.echo(f"Hoan tat: thanh cong={ok}, loi={failed}")
        finally:
            await service.close()

    asyncio.run(run())


@app.command("resume-crawl", hidden=True)
def resume_crawl(
    run_id: int = typer.Argument(..., min=1, help="Ma crawl run can tiep tuc"),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Tiep tuc cac URL chua hoan thanh sau khi crawl bi gian doan."""
    cfg = _config(config)

    async def run() -> None:
        service = CrawlerService(cfg)
        try:
            ok, failed = await service.resume_crawl(run_id)
            typer.echo(f"Resume hoan tat: thanh cong={ok}, loi={failed}")
        finally:
            await service.close()

    asyncio.run(run())


@app.command("collect-links", hidden=True)
def collect_links(
    list_url: str = typer.Argument(...),
    output: Path = typer.Option(Path("data/urls.txt"), "--output", "-o"),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    cfg = _config(config)

    async def run() -> None:
        service = CrawlerService(cfg)
        try:
            links = await service.collect_links(list_url)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text("\n".join(links) + ("\n" if links else ""), encoding="utf-8")
            typer.echo(f"Da ghi {len(links)} URL vao {output}")
        finally:
            await service.close()

    asyncio.run(run())


@app.command("collect-dynamic", hidden=True)
def collect_dynamic(
    list_url: str = typer.Argument(..., help="Trang danh sach dong duoc phep tu dong truy cap"),
    keyword: str | None = typer.Option(None, "--keyword", "-k"),
    max_pages: int = typer.Option(10, "--max-pages", min=1, max=1000),
    output: Path = typer.Option(Path("data/urls.txt"), "--output", "-o"),
    headed: bool = typer.Option(False, "--headed/--headless"),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    cfg = _config(config)

    async def run() -> None:
        service = CrawlerService(cfg)
        try:
            links = await service.collect_dynamic_links(
                list_url=list_url,
                keyword=keyword,
                max_pages=max_pages,
                headed=headed,
            )
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text("\n".join(links) + ("\n" if links else ""), encoding="utf-8")
            typer.echo(f"Da ghi {len(links)} URL vao {output}")
        finally:
            await service.close()

    asyncio.run(run())


@app.command("download-page", hidden=True)
def download_page(
    url: str = typer.Argument(..., help="Trang chi tiet co nut tai file duoc phep tu dong hoa"),
    package_id: str | None = typer.Option(None, "--package-id"),
    headed: bool = typer.Option(False, "--headed/--headless"),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    cfg = _config(config)

    async def run() -> None:
        service = CrawlerService(cfg)
        try:
            notice, downloaded, errors = await service.download_dynamic_attachments(
                url=url,
                package_id=package_id,
                headed=headed,
            )
            typer.echo(
                f"Notice id={notice.id}: tai thanh cong={len(downloaded)}, loi={len(errors)}"
            )
            for item in downloaded:
                typer.echo(f"  OK  {item.local_path}")
            for error in errors:
                typer.echo(f"  ERR {error}", err=True)
        finally:
            await service.close()

    asyncio.run(run())


@app.command("retry-downloads", hidden=True)
def retry_downloads(
    limit: int = typer.Option(100, "--limit", min=1, max=10000),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    cfg = _config(config)

    async def run() -> None:
        service = CrawlerService(cfg)
        try:
            ok, failed = await service.retry_failed_attachments(limit=limit)
            typer.echo(f"Retry hoan tat: thanh cong={ok}, loi={failed}")
        finally:
            await service.close()

    asyncio.run(run())


@app.command("discover", hidden=True)
def discover(
    url: str = typer.Argument(..., help="Trang cong khai can quan sat JSON/XHR"),
    seconds: int = typer.Option(60, "--seconds", min=5, max=600),
    headed: bool = typer.Option(True, "--headed/--headless"),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    cfg = _config(config)

    async def run() -> None:
        browser = BrowserFetcher(cfg)
        try:
            saved = await browser.discover_json(url, seconds, headed)
            typer.echo(f"Da luu {len(saved)} phan hoi JSON vao {cfg.storage.discovery_dir}")
        finally:
            await browser.close()

    asyncio.run(run())


@app.command("import-file", hidden=True)
def import_file_command(
    input_file: Path = typer.Argument(..., exists=True, readable=True),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    cfg = _config(config)

    async def run() -> None:
        service = CrawlerService(cfg)
        try:
            summary = import_data_file(service, input_file)
            typer.echo(
                "Import hoan tat: "
                f"tong={summary.rows_found}, moi={summary.inserted}, cap nhat={summary.updated}, "
                f"khong doi={summary.unchanged}, loai={summary.rejected}"
            )
            if summary.reject_file:
                typer.echo(f"Du lieu loi: {summary.reject_file}")
        finally:
            await service.close()

    asyncio.run(run())


@app.command("export", hidden=True)
def export(
    output: Path = typer.Option(Path("data/notices.xlsx"), "--output", "-o"),
    format: str = typer.Option("xlsx", "--format", case_sensitive=False),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    cfg = _config(config)
    db = Database(cfg.storage.database_url)
    db.require_current_schema()
    fmt = format.lower()
    if fmt == "xlsx":
        path = export_xlsx(db, output)
    elif fmt == "csv":
        path = export_csv(db, output)
    else:
        raise typer.BadParameter("Format phai la xlsx hoac csv")
    typer.echo(f"Da xuat: {path}")


@app.command("report-daily", hidden=True)
def report_daily(
    output: Path | None = typer.Option(None, "--output", "-o"),
    report_date: str | None = typer.Option(None, "--date", help="YYYY-MM-DD"),
    days_ahead: int | None = typer.Option(None, "--days-ahead", min=1, max=90),
    send_email: bool = typer.Option(False, "--send-email"),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    cfg = _config(config)
    selected_date = date.fromisoformat(report_date) if report_date else datetime.now(UTC).date()
    path = output or cfg.storage.report_dir / f"bao-cao-dau-thau-{selected_date.isoformat()}.xlsx"
    db = Database(cfg.storage.database_url)
    db.require_current_schema()
    report_path = build_daily_report(
        db,
        path,
        report_date=selected_date,
        days_ahead=days_ahead or cfg.reporting.days_ahead,
    )
    typer.echo(f"Da tao bao cao: {report_path}")
    if send_email:
        send_report_email(cfg, report_path)
        typer.echo("Da gui email bao cao.")


@app.command("serve", hidden=True)
def serve(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8000, "--port", min=1, max=65535),
) -> None:
    import uvicorn

    uvicorn.run("qi_crawler.api:app", host=host, port=port, reload=False)


@app.command("import-evidence", hidden=True)
def import_evidence(
    input_file: Path = typer.Argument(..., exists=True, readable=True),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Import verified company capabilities used to support bid requirements."""
    cfg = _config(config)
    db = Database(cfg.storage.database_url)
    db.require_current_schema()
    count = import_evidence_csv(db, input_file)
    typer.echo(f"Da nhap/cap nhat {count} bang chung nang luc.")


@app.command("analyze-bid", hidden=True)
def analyze_bid(
    input_file: Path = typer.Argument(..., exists=True, readable=True),
    notice_id: int | None = typer.Option(None, "--notice-id", min=1),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Build an evidence-backed compliance matrix from a plain-text E-HSMT extract."""
    cfg = _config(config)
    db = Database(cfg.storage.database_url)
    db.require_current_schema()
    result = analyze_bid_document(db, input_file, notice_id=notice_id)
    typer.echo(
        f"Phan tich {result.total} yeu cau: dap ung={result.covered}, "
        f"mot phan={result.partial}, thieu={result.gaps}, coverage={result.coverage_percent}%"
    )


@app.command("predict-win", hidden=True)
def predict_win(
    notice_id: int | None = typer.Option(None, "--notice-id", min=1),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Estimate readiness and win likelihood with explicit low-confidence caveats."""
    cfg = _config(config)
    db = Database(cfg.storage.database_url)
    db.require_current_schema()
    result = estimate_win_likelihood(db, notice_id=notice_id)
    typer.echo(f"Cong SOP: {result.gate_status}")
    typer.echo(f"Diem san sang ho so: {result.readiness_score}%")
    typer.echo(
        f"Ty le trung thau uoc tinh: {result.estimated_win_percent}% "
        f"(do tin cay: {result.confidence_percent}%)"
    )
    typer.echo(f"Coverage yeu cau bat buoc: {result.mandatory_coverage_percent}%")
    typer.echo("Rui ro chinh:")
    for risk in result.risk_factors:
        typer.echo(f"  - {risk}")
    typer.echo("Canh bao: day la uoc tinh MVP, khong phai xac suat da kiem dinh hay bao dam trung thau.")


@app.command("bid-gate", hidden=True)
def bid_gate(
    notice_id: int | None = typer.Option(None, "--notice-id", min=1),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Apply the SOP mandatory-requirement GO/HOLD/NO-GO gate."""
    cfg = _config(config)
    db = Database(cfg.storage.database_url)
    db.require_current_schema()
    result = evaluate_bid_gate(db, notice_id)
    typer.echo(
        f"Ket luan SOP: {result.status}; bat buoc={result.mandatory_total}; "
        f"da xac nhan={result.mandatory_confirmed}"
    )
    for blocker in result.blockers:
        typer.echo(f"  - {blocker}")


@app.command("confirm-assessment", hidden=True)
def confirm_assessment_command(
    assessment_id: int = typer.Argument(..., min=1),
    reviewer: str = typer.Option(..., "--reviewer"),
    decision: str = typer.Option(..., "--decision"),
    note: str | None = typer.Option(None, "--note"),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Record an independent reviewer decision for one compliance item."""
    cfg = _config(config)
    db = Database(cfg.storage.database_url)
    db.require_current_schema()
    confirm_assessment(db, assessment_id, reviewer, decision, note)
    typer.echo(f"Da xac nhan assessment {assessment_id}: {decision} boi {reviewer}.")


# ---------------------------------------------------------------------------
# Lenh don gian cho nguoi moi. Cac lenh ky thuat phia tren van duoc giu de
# van hanh nang cao va tuong thich voi quy trinh cu.


@app.command("bat-dau", hidden=True)
def bat_dau(config: Path | None = typer.Option(None, "--config", exists=True)) -> None:
    """Chuan bi lan dau."""
    cfg = _config(config)
    try:
        Database(cfg.storage.database_url).require_current_schema()
    except SchemaNotReady:
        typer.echo("Hay chay QI-Crawler db-upgrade")
        raise typer.Exit(code=1) from None
    typer.echo("MVP QI da san sang.")
    typer.echo("1. Crawl URL:     QI-Crawler crawl \"URL_GOI_THAU\"")
    typer.echo("2. Tim trong kho: QI-Crawler tim-goi --tu-khoa \"network switch\"")
    typer.echo("3. Xuat TBMT:     QI-Crawler xuat-tbmt")


@app.command("tim-goi", rich_help_panel="QUY TRINH BID TEAM")
def tim_goi(
    tu_khoa: str = typer.Option(
        ..., "--tu-khoa", "-k", help="Ten san pham tieng Viet hoac tieng Anh"
    ),
    tu_ngay: str | None = typer.Option(None, "--tu-ngay", help="Loc du lieu da luu tu ngay YYYY-MM-DD"),
    so_luong: int = typer.Option(20, "--so-luong", min=1, max=200),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Tim goi thau da luu trong database, khong ket noi website."""
    cfg = _config(config)
    expansion = expand_keyword(tu_khoa)
    _show_keyword_plan(expansion)
    since = _date_option(tu_ngay, "--tu-ngay")
    db = Database(cfg.storage.database_url)
    db.require_current_schema()
    search_result = search_notices(
        db,
        expansion.search_terms,
        since,
        so_luong,
        tuple(active_source_names(cfg)),
        active_source_domains(cfg),
    )
    matches = search_result.notices

    typer.echo("Tim trong database da luu (khong ket noi website).")
    typer.echo(f"Tim thay {len(matches)} goi phu hop voi '{tu_khoa}'.")
    for notice in matches:
        identifier = notice.notice_code or notice.source_notice_id or f"ID {notice.id}"
        typer.echo(f"- [{identifier}] {notice.title or 'Chua co ten'}")
        typer.echo(f"  Nguon: {notice.source_name or notice.source_kind} | {notice.source_url}")
    if not matches:
        typer.echo("Hay crawl URL danh sach/chi tiet truoc, sau do chay lai tim-goi.")


@app.command("xuat-bao-cao", hidden=True)
def xuat_bao_cao(
    output: Path = typer.Option(Path("data/bao-cao-goi-thau.xlsx"), "--tep", "-o"),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Xuat Excel theo mau TBMT, kem danh sach va bang dap ung."""
    cfg = _config(config)
    db = Database(cfg.storage.database_url)
    db.require_current_schema()
    path = export_xlsx(db, output)
    typer.echo(f"Da tao bao cao: {path}")


@app.command("xuat-tbmt", rich_help_panel="QUY TRINH BID TEAM")
def xuat_tbmt(
    output: Path | None = typer.Option(
        None,
        "--tep",
        "-o",
        help="Duong dan file .xlsx; bo trong de cap nhat TBMT_Latest.xlsx",
    ),
    ngay: str | None = typer.Option(None, "--ngay", "--date", help="Ngay dang tai YYYY-MM-DD"),
    tu_ngay: str | None = typer.Option(
        None, "--tu-ngay", "--from", help="Tu ngay dang tai YYYY-MM-DD"
    ),
    den_ngay: str | None = typer.Option(
        None, "--den-ngay", "--to", help="Den ngay dang tai YYYY-MM-DD"
    ),
    trang_thai: str | None = typer.Option(
        None, "--trang-thai", "--status", help="Trang thai da duyet trong database"
    ),
    tu_khoa: str | None = typer.Option(
        None, "--tu-khoa", "--keyword", "-k", help="Loc theo cum tu trong goi thau"
    ),
    to_canh_bao: bool = typer.Option(
        False, "--to-canh-bao", "--highlight", help="To mau deadline va truong con thieu"
    ),
    all_records: bool = typer.Option(
        False,
        "--all",
        "--tat-ca-run",
        "--all-runs",
        help="Xuat tat ca goi hop le da luu, khong gioi han trong ngay hom nay",
    ),
    snapshot: bool = typer.Option(
        False,
        "--snapshot",
        help="Luu ban lich su vao data/reports/archive thay vi cap nhat TBMT_Latest.xlsx",
    ),
    run_id: int | None = typer.Option(
        None, "--run-id", min=1, help="Chi xuat mot crawl run cu the"
    ),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> Path:
    """Xuat Excel theo mau TBMT."""
    cfg = _config(config)
    db = Database(cfg.storage.database_url)
    db.require_current_schema()
    result = export_tbmt(
        db,
        report_dir=cfg.storage.report_dir,
        rejects_dir=cfg.storage.rejects_dir,
        output=output,
        snapshot=snapshot,
        on_date=_date_option(ngay, "--ngay"),
        from_date=_date_option(tu_ngay, "--tu-ngay"),
        to_date=_date_option(den_ngay, "--den-ngay"),
        status=trang_thai,
        keyword=tu_khoa,
        highlight=to_canh_bao,
        latest_run_only=False,
        crawl_run_id=run_id,
        current_day_only=not all_records and run_id is None,
        active_source_names=tuple(active_source_names(cfg)),
        active_source_domains=active_source_domains(cfg),
    )
    typer.echo(f"Da tao file TBMT: {result.output}")
    typer.echo(
        "Ket qua: "
        f"{result.exported_records} dong xuat, "
        f"{result.warning_records} canh bao, "
        f"{result.rejected_records} dong bi loai."
    )
    if result.reject_output:
        typer.echo(f"Dong bi loai duoc luu tai: {result.reject_output}")
    return result.output


@app.command("nhap-ton-kho", hidden=True)
@app.command("import-inventory", hidden=True)
def import_inventory_command(
    input_file: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        metavar="TEP_TON_KHO",
        help="File Excel/CSV ton kho QI",
    ),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Nhap ton kho Excel/CSV."""
    cfg = _config(config)
    summary = import_inventory(Database(cfg.storage.database_url), input_file)
    typer.echo(
        "Nhap ton kho xong: "
        f"tong={summary.rows}, them-moi={summary.inserted}, "
        f"cap-nhat={summary.updated}, loi={summary.rejected}."
    )
    typer.echo("Buoc tiep theo: QI-Crawler xuat-bao-cao")


@app.command("nhap-boq", hidden=True)
@app.command("import-tender-items", hidden=True)
def import_tender_items_command(
    notice_id: int = typer.Argument(
        ..., min=1, metavar="MA_GOI", help="Cot id cua goi trong sheet Notices"
    ),
    input_file: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        metavar="TEP_BOQ",
        help="File Excel/CSV bang so luong BOQ",
    ),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Nhap BOQ cua mot goi thau."""
    cfg = _config(config)
    try:
        summary = import_tender_items(
            Database(cfg.storage.database_url), notice_id, input_file
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(
        "Nhap BOQ xong: "
        f"tong={summary.rows}, them-moi={summary.inserted}, "
        f"cap-nhat={summary.updated}, loi={summary.rejected}."
    )
    typer.echo("Buoc tiep theo: QI-Crawler xuat-bao-cao")


@app.command("theo-doi", hidden=True)
def theo_doi(
    cau_hinh: Path = typer.Option(
        Path("monitoring.yaml"), "--cau-hinh", "-c", help="File cau hinh theo doi"
    ),
    mot_lan: bool = typer.Option(
        False, "--mot-lan", help="Quet mot luot roi dung; phu hop Windows Task Scheduler"
    ),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Tu dong tim va xep hang co hoi theo chu ky."""
    cfg = _config(config)
    settings = load_monitoring_config(cau_hinh)

    async def run() -> None:
        service = CrawlerService(cfg)
        try:
            if mot_lan:
                summary = await run_monitoring_cycle(service, settings)
                typer.echo(
                    f"Quet xong: thu thap={summary.collected}, "
                    f"PRIORITY={summary.priority}, REVIEW={summary.review}, "
                    f"SKIP={summary.skip}, INSUFFICIENT_DATA={summary.insufficient}."
                )
                typer.echo(f"Bao cao: {summary.output}")
            else:
                typer.echo(
                    f"Bat dau theo doi moi {settings.interval_minutes} phut. "
                    "Nhan Ctrl+C de dung."
                )
                await monitor_forever(service, settings)
        finally:
            await service.close()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        typer.echo("Da dung theo doi an toan.")


@app.command("xep-hang", hidden=True)
def xep_hang(
    cau_hinh: Path = typer.Option(
        Path("monitoring.yaml"), "--cau-hinh", "-c", help="File cau hinh sang loc"
    ),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Cham diem va xep hang co hoi mot lan, kem giai thich."""
    theo_doi(cau_hinh=cau_hinh, mot_lan=True, config=config)


@app.command("danh-gia", hidden=True)
def danh_gia(
    yeu_cau: Path = typer.Argument(..., exists=True, readable=True),
    notice_id: int | None = typer.Option(None, "--ma-noi-bo", min=1),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Kiem tra kha nang dap ung cua mot goi thau."""
    cfg = _config(config)
    db = Database(cfg.storage.database_url)
    db.require_current_schema()
    summary = analyze_bid_document(db, yeu_cau, notice_id=notice_id)
    gate = evaluate_bid_gate(db, notice_id)
    typer.echo(
        f"Da doc {summary.total} yeu cau: dap ung={summary.covered}, "
        f"can kiem tra={summary.partial}, thieu={summary.gaps}."
    )
    typer.echo(f"Ket luan hien tai: {gate.status}")
    for blocker in gate.blockers[:10]:
        typer.echo(f"  - {blocker}")
    if gate.status != "GO":
        typer.echo("Can nguoi phu trach kiem tra bang chung truoc khi trinh duyet.")


@app.command("them-nguon", hidden=True)
def them_nguon(
    ten: str = typer.Option(..., "--ten", help="Ten ngan, vi du: muasamcong"),
    url: str = typer.Option(..., "--url", help="Dia chi trang danh sach goi thau"),
    item_selector: str = typer.Option("a[href]", "--vung-ket-qua", hidden=True),
    link_selector: str = typer.Option("a", "--link", hidden=True),
    next_selector: str | None = typer.Option(None, "--trang-sau", hidden=True),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Them website co danh sach goi thau."""
    source = WebSource(
        name=ten,
        list_url=url,
        item_selector=item_selector,
        link_selector=link_selector,
        next_selector=next_selector,
    )
    config_path = config or EnvSettings().config_path
    allow_source_domain(config_path, source.domain)
    path = save_source(source)
    typer.echo(f"Da them nguon '{source.name}': {source.domain}")
    typer.echo(f"Cau hinh cuc bo: {path}")
    typer.echo(f"Buoc tiep theo: QI-Crawler dang-nhap --ten {source.name}")


@app.command("them-egp", hidden=True)
def them_egp(
    ten: str = typer.Option("egp", "--ten", help="Ten nguon de ghi nho"),
    url: str = typer.Option(
        "https://muasamcong.mpi.gov.vn/vi/web/guest/contractor-selection",
        "--url",
        help="URL trang danh sach e-GP",
    ),
    config: Path | None = typer.Option(None, "--config", exists=True, hidden=True),
) -> None:
    """Cau hinh nhanh nguon e-GP Viet Nam."""
    source = egp_vietnam_source(name=ten, list_url=url)
    config_path = config or EnvSettings().config_path
    allow_source_domain(config_path, source.domain)
    path = save_source(source)
    typer.echo(f"Da tao nguon e-GP '{source.name}': {source.domain}")
    typer.echo(f"Cau hinh cuc bo: {path}")
    typer.echo(f"Buoc 1: QI-Crawler dang-nhap --ten {source.name}")
    typer.echo(f"Buoc 2: QI-Crawler kiem-tra-nguon --ten {source.name}")
    typer.echo(f"Buoc 3: QI-Crawler tim-tren-web --ten {source.name} --tu-khoa \"cap quang\"")


@app.command("kiem-tra-nguon", hidden=True)
def kiem_tra_nguon(
    ten: str = typer.Option(..., "--ten", help="Ten nguon da khai bao"),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Kiem tra phien dang nhap va selector truoc khi thu thap."""
    cfg = _config(config)
    source = load_source(ten)
    result = asyncio.run(validate_authenticated_source(cfg, source))
    typer.echo(f"Trang dang kiem tra: {result.current_url}")
    typer.echo(f"Muc goi thau: {result.item_count}; link hop le: {result.link_count}")
    if not result.ready:
        typer.echo(
            "Chua san sang. Hay dang-nhap lai, di toi trang danh sach goi thau "
            "va luu lai phien.",
            err=True,
        )
        raise typer.Exit(code=2)
    typer.echo("Nguon da san sang de tim goi.")


@app.command("them-tu-khoa", hidden=True)
def them_tu_khoa(
    tu_khoa: str = typer.Option(..., "--tu-khoa", "-k", help="Ten san pham moi"),
    ten_khac: list[str] = typer.Option(
        [], "--ten-khac", help="Ten Anh/viet tat; co the nhap nhieu lan"
    ),
    mo_ta: str = typer.Option("", "--mo-ta", help="Mo ta ngan giup xac dinh nhom nganh"),
    nhom: str | None = typer.Option(None, "--nhom", help="Chi dinh nhom neu muon xac nhan thu cong"),
) -> None:
    """Them san pham va ten tim kiem moi."""
    result = learn_keyword(
        tu_khoa,
        aliases=tuple(ten_khac),
        description=mo_ta,
        category_name=nhom,
    )
    if result.status == "updated":
        typer.echo(f"Da cap nhat '{result.keyword}' vao nhom '{result.category}'.")
        typer.echo(f"Do tin cay phan loai: {result.confidence:.0%}")
        if result.matched_signals:
            typer.echo(f"Tin hieu nhan dien: {', '.join(result.matched_signals)}")
    else:
        typer.echo("Chua xac dinh duoc nhom nganh mot cach an toan.")
        typer.echo("Tu khoa da duoc luu vao pending_keywords trong keyword-groups.yaml.")
        typer.echo("Chay lai voi --nhom \"TEN NHOM\" sau khi nguoi phu trach xac nhan.")


@app.command("dang-nhap", rich_help_panel="QUY TRINH BID TEAM")
@app.command("login", hidden=True)
def dang_nhap(
    ten: str | None = typer.Option(None, "--ten", help="Ten nguon da khai bao"),
    source: str | None = typer.Option(None, "--source", help="Alias, vi du: egp"),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Mo trinh duyet de tu dang nhap va luu phien cuc bo."""
    if ten and source and ten != source:
        raise typer.BadParameter("Chi dung mot trong --ten hoac --source")
    selected = source or ten
    if not selected:
        raise typer.BadParameter("Can chi dinh --source egp hoac --ten TEN_NGUON")
    cfg = _config(config)
    try:
        profile = load_source(selected)
    except FileNotFoundError:
        if selected != "egp":
            raise
        profile = egp_vietnam_source(name="egp")
        save_source(profile)
    path = asyncio.run(create_login_session(cfg, profile))
    typer.echo(f"Da luu phien dang nhap cuc bo cho '{profile.name}': {path}")
    typer.echo("Khong gui file session cho nguoi khac va khong dua file nay len Git.")


@app.command("tim-tren-web", hidden=True)
def tim_tren_web(
    ten: str = typer.Option(..., "--ten"),
    tu_khoa: str = typer.Option(..., "--tu-khoa", "-k"),
    so_luong: int = typer.Option(50, "--so-luong", min=1, max=500),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Tim tren website da dang nhap."""
    cfg = _config(config)
    source = load_source(ten)
    expansion = expand_keyword(tu_khoa)
    _show_keyword_plan(expansion)

    async def run() -> None:
        service = CrawlerService(cfg)
        try:
            result = await collect_authenticated_source(
                service, source, keyword=expansion.search_terms, limit=so_luong
            )
            typer.echo(
                f"Da xem {result.scanned} muc, luu {result.matched} goi phu hop "
                f"(moi={result.inserted}, cap nhat={result.updated})."
            )
            typer.echo("Buoc tiep theo: QI-Crawler xuat-bao-cao")
        finally:
            await service.close()

    asyncio.run(run())


@app.command("warehouse-init", hidden=True)
def warehouse_init(
    path: Path = typer.Option(WAREHOUSE_PATH, "--path", help="DuckDB warehouse file"),
) -> None:
    """Create the local DuckDB warehouse and governance tables."""
    manager = WarehouseManager(path)
    manager.initialize()
    typer.echo(f"Warehouse ready: {path.resolve()}")


@app.command("warehouse-status", hidden=True)
def warehouse_status(
    path: Path = typer.Option(WAREHOUSE_PATH, "--path", help="DuckDB warehouse file"),
) -> None:
    """Check the local warehouse structure and review queue."""
    status = WarehouseManager(path).status()
    typer.echo(f"Warehouse: {status.path}")
    typer.echo(f"Size: {status.size_bytes / (1024 * 1024):.2f} MB")
    typer.echo(f"Schemas: {', '.join(status.schemas)}")
    typer.echo(f"Tables: {len(status.tables)}")
    typer.echo(f"Registered datasets: {status.datasets}")
    typer.echo(f"Pending retention reviews: {status.pending_reviews}")


@app.command("warehouse-backup", hidden=True)
def warehouse_backup(
    path: Path = typer.Option(WAREHOUSE_PATH, "--path", help="DuckDB warehouse file"),
    output_dir: Path = typer.Option(BACKUP_DIR, "--output-dir", "-o"),
) -> None:
    """Create a timestamped local warehouse backup."""
    backup = WarehouseManager(path).backup(output_dir)
    typer.echo(f"Backup created: {backup}")


@app.command("warehouse-review", hidden=True)
def warehouse_review(
    dataset_name: str = typer.Argument(..., help="Stable dataset name"),
    decision: str = typer.Argument(..., help="KEEP, REVIEW, QUARANTINE or DROP_PROPOSED"),
    reason: str = typer.Argument(..., help="Evidence-based reason for the decision"),
    path: Path = typer.Option(WAREHOUSE_PATH, "--path", help="DuckDB warehouse file"),
) -> None:
    """Record a retention recommendation; this command never deletes data."""
    try:
        WarehouseManager(path).record_decision(dataset_name, decision, reason)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"Recorded {decision.upper()} for dataset '{dataset_name}'. No data was deleted.")


if __name__ == "__main__":
    app()
