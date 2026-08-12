from __future__ import annotations

import asyncio
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


def _show_keyword_plan(expansion: KeywordExpansion) -> None:
    typer.echo(f"Tu khoa san pham: {', '.join(expansion.product_terms)}")
    if expansion.category:
        typer.echo(
            f"Nhom nganh: {expansion.category} "
            f"({', '.join(expansion.category_terms)})"
        )


app = typer.Typer(
    no_args_is_help=True,
    invoke_without_command=True,
    add_completion=False,
    context_settings={"help_option_names": ["-help", "--help", "-h"]},
    help="Cong cu QI tim, theo doi, kiem tra va xuat bao cao goi thau.",
    epilog="""
BAT DAU NHANH

  1. QI-Crawler bat-dau

  2. QI-Crawler crawl "URL_GOI_THAU"

  3. QI-Crawler tim-goi --tu-khoa "network switch"

  4. QI-Crawler xuat-tbmt

Chi tiet: QI-Crawler TEN-LENH -help

Lenh ky thuat: QI-Crawler -adv

Tai lieu: HUONG_DAN_SU_DUNG.md | Cap nhat: CHANGELOG.md
""",
)

ADVANCED_HELP = """
LENH NANG CAO - DANH CHO NGUOI VAN HANH KY THUAT

  Nguon website
  them-nguon                Them website co danh sach goi thau
  them-egp                  Cau hinh nhanh nguon e-GP Viet Nam
  kiem-tra-nguon            Kiem tra phien dang nhap va selector
  crawl URL                 Doc mot trang chi tiet duoc phep crawl
  crawl-file TEP            Doc danh sach URL tu file
  resume-crawl RUN_ID       Tiep tuc cac URL chua hoan thanh cua mot lan crawl bi gian doan
  collect-links URL         Lay link chi tiet tu trang danh sach
  collect-dynamic URL       Lay link tu website JavaScript
  them-tu-khoa              Them tu khoa va phan loai nhom nganh

  Theo doi va xuat bao cao
  theo-doi                  Tu dong tim, loc va xep hang theo chu ky
  xep-hang                  Chay mot luot cham diem co hoi
  xuat-bao-cao              Xuat Excel danh sach va bang dap ung

  init-db                    Khoi tao hoac cap nhat database
  db-upgrade                 Backup va nang cap database bang Alembic
  clean-legacy-sources       Archive va loai du lieu Contracts Finder/example/test cu
  download-page URL          Tai tep dinh kem tu trang chi tiet
  retry-downloads            Tai lai cac tep bi loi
  discover URL               Quan sat API/JSON cua website
  import-file TEP            Nhap du lieu goi thau CSV/Excel
  export                     Xuat Excel co sheet TBMT va cac sheet ky thuat
  report-daily               Tao bao cao van hanh hang ngay
  import-evidence TEP        Nhap bang chung nang luc QI
  analyze-bid TEP            Phan tich compliance ky thuat (legacy/pilot sau)
  warehouse-init             Khoi tao data warehouse cuc bo
  warehouse-status           Kiem tra data warehouse
  warehouse-backup           Sao luu data warehouse
  warehouse-review           Ghi nhan de xuat luu tru du lieu

Xem chi tiet: QI-Crawler TEN-LENH -help
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


@app.command("help", rich_help_panel="LENH CHO NGUOI MOI")
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


@app.command("crawl", hidden=True)
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
                typer.echo(f"HUMAN_REQUIRED: {service.human_required_reason}", err=True)
        finally:
            await service.close()

    asyncio.run(run())


@app.command("scan", rich_help_panel="LENH CHO NGUOI MOI")
def scan(
    list_url: str = typer.Argument(..., metavar="LIST_URL", help="Trang danh sach Coteccons"),
    tu_khoa: str | None = typer.Option(
        None, "--tu-khoa", "-k", help="Loc theo tu khoa, cach nhau bang dau phay"
    ),
    max_pages: int = typer.Option(25, "--max-pages", min=1, max=100),
    resume: bool = typer.Option(False, "--resume", help="Tiep tuc scan dang do cua cung LIST_URL"),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Doc trang danh sach, phan trang va crawl cac trang chi tiet Coteccons."""
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
            if summary.run_id is not None:
                typer.echo(f"Run: {summary.run_id}")
            typer.echo(f"Discovered: {summary.discovered}")
            typer.echo(f"Matched: {summary.matched}")
            typer.echo(f"New: {summary.new}")
            typer.echo(f"Existing: {summary.existing}")
            typer.echo(f"Success: {summary.success}")
            typer.echo(f"Failed: {summary.failed}")
            typer.echo(f"Skipped: {summary.skipped}")
        except AccessDenied as exc:
            typer.echo(f"HUMAN_REQUIRED: {exc}", err=True)
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


@app.command("bat-dau", rich_help_panel="LENH CHO NGUOI MOI")
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


@app.command("tim-goi", rich_help_panel="LENH CHO NGUOI MOI")
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


@app.command("xuat-tbmt", rich_help_panel="LENH CHO NGUOI MOI")
def xuat_tbmt(
    output: Path | None = typer.Option(
        None,
        "--tep",
        "-o",
        help="Duong dan file .xlsx; bo trong de dat ten TBMT_ngay_thang_nam",
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
    run_id: int | None = typer.Option(
        None, "--run-id", min=1, help="Chi xuat mot crawl run cu the"
    ),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Xuat Excel theo mau TBMT."""
    cfg = _config(config)
    db = Database(cfg.storage.database_url)
    db.require_current_schema()
    result = export_tbmt(
        db,
        report_dir=cfg.storage.report_dir,
        rejects_dir=cfg.storage.rejects_dir,
        output=output,
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


@app.command("nhap-ton-kho", rich_help_panel="LENH CHO NGUOI MOI")
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


@app.command("nhap-boq", rich_help_panel="LENH CHO NGUOI MOI")
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


@app.command("dang-nhap", rich_help_panel="LENH CHO NGUOI MOI")
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


@app.command("tim-tren-web", rich_help_panel="LENH CHO NGUOI MOI")
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
