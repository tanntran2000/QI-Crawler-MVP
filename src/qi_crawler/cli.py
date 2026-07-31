from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime
from pathlib import Path

import typer

from .authenticated_sources import (
    WebSource,
    allow_source_domain,
    collect_authenticated_source,
    create_login_session,
    load_source,
    save_source,
)
from .bid_intelligence import (
    analyze_bid_document,
    confirm_assessment,
    estimate_win_likelihood,
    evaluate_bid_gate,
    import_evidence_csv,
)
from .browser import BrowserFetcher
from .config import EnvSettings, load_config
from .contracts_finder import collect_contracts_finder
from .crawler import CrawlerService
from .db import Database
from .exporter import export_csv, export_xlsx
from .importer import import_file as import_data_file
from .keywords import KeywordExpansion, expand_keyword, learn_keyword
from .logging_utils import configure_logging
from .reporting import build_daily_report, send_report_email


def _show_keyword_plan(expansion: KeywordExpansion) -> None:
    typer.echo(f"Từ khóa sản phẩm: {', '.join(expansion.product_terms)}")
    if expansion.category:
        typer.echo(
            f"Nhóm ngành: {expansion.category} "
            f"({', '.join(expansion.category_terms)})"
        )


def _expand_and_learn(keyword: str) -> KeywordExpansion:
    expansion = expand_keyword(keyword)
    if expansion.category is None:
        learned = learn_keyword(keyword)
        if learned.status == "updated":
            typer.echo(
                f"Đã tự phân loại từ khóa mới vào nhóm '{learned.category}' "
                f"(độ tin cậy {learned.confidence:.0%})."
            )
            expansion = expand_keyword(keyword)
        else:
            typer.echo(
                "Từ khóa mới chưa đủ thông tin để phân loại; đã đưa vào "
                "pending_keywords để người phụ trách kiểm tra."
            )
    return expansion

app = typer.Typer(
    no_args_is_help=True,
    context_settings={"help_option_names": ["-help", "--help", "-h"]},
    help="Crawler dữ liệu đấu thầu công khai: allowlist, robots.txt, rate limit và audit.",
    epilog="""
LỆNH MẪU CHO NGƯỜI MỚI:

  QI-Crawler bat-dau

  QI-Crawler tim-goi --tu-khoa "xi măng"

  QI-Crawler xuat-bao-cao

  QI-Crawler them-nguon --ten muasamcong --url "URL_TRANG_DANH_SACH"

  QI-Crawler dang-nhap --ten muasamcong

  QI-Crawler tim-tren-web --ten muasamcong --tu-khoa "xi măng"

Dùng QI-Crawler TEN-LENH -help để xem hướng dẫn riêng của một lệnh.
""",
)


@app.command("help")
def show_help(ctx: typer.Context) -> None:
    """Hiện danh sách lệnh và ví dụ sử dụng."""
    if ctx.parent is not None:
        typer.echo(ctx.parent.get_help())


def _config(path: Path | None):
    env = EnvSettings()
    configure_logging(env.log_level)
    return load_config(path)


@app.command("init-db")
def init_db(config: Path | None = typer.Option(None, "--config", exists=True)) -> None:
    cfg = _config(config)
    Database(cfg.storage.database_url).create_all()
    typer.echo(f"Đã khởi tạo/cập nhật database: {cfg.storage.database_url}")


@app.command("crawl")
def crawl(
    urls: list[str] = typer.Argument(..., help="Một hoặc nhiều URL chi tiết được phép crawl"),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    cfg = _config(config)

    async def run() -> None:
        service = CrawlerService(cfg)
        try:
            ok, failed = await service.crawl_urls(urls)
            typer.echo(f"Hoàn tất: thành công={ok}, lỗi={failed}")
        finally:
            await service.close()

    asyncio.run(run())


@app.command("crawl-file")
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
            typer.echo(f"Hoàn tất: thành công={ok}, lỗi={failed}")
        finally:
            await service.close()

    asyncio.run(run())


@app.command("collect-links")
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
            typer.echo(f"Đã ghi {len(links)} URL vào {output}")
        finally:
            await service.close()

    asyncio.run(run())


@app.command("collect-dynamic")
def collect_dynamic(
    list_url: str = typer.Argument(..., help="Trang danh sách động được phép tự động truy cập"),
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
            typer.echo(f"Đã ghi {len(links)} URL vào {output}")
        finally:
            await service.close()

    asyncio.run(run())


@app.command("download-page")
def download_page(
    url: str = typer.Argument(..., help="Trang chi tiết có nút tải file được phép tự động hóa"),
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
                f"Notice id={notice.id}: tải thành công={len(downloaded)}, lỗi={len(errors)}"
            )
            for item in downloaded:
                typer.echo(f"  OK  {item.local_path}")
            for error in errors:
                typer.echo(f"  ERR {error}", err=True)
        finally:
            await service.close()

    asyncio.run(run())


@app.command("retry-downloads")
def retry_downloads(
    limit: int = typer.Option(100, "--limit", min=1, max=10000),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    cfg = _config(config)

    async def run() -> None:
        service = CrawlerService(cfg)
        try:
            ok, failed = await service.retry_failed_attachments(limit=limit)
            typer.echo(f"Retry hoàn tất: thành công={ok}, lỗi={failed}")
        finally:
            await service.close()

    asyncio.run(run())


@app.command("discover")
def discover(
    url: str = typer.Argument(..., help="Trang công khai cần quan sát JSON/XHR"),
    seconds: int = typer.Option(60, "--seconds", min=5, max=600),
    headed: bool = typer.Option(True, "--headed/--headless"),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    cfg = _config(config)

    async def run() -> None:
        browser = BrowserFetcher(cfg)
        try:
            saved = await browser.discover_json(url, seconds, headed)
            typer.echo(f"Đã lưu {len(saved)} phản hồi JSON vào {cfg.storage.discovery_dir}")
        finally:
            await browser.close()

    asyncio.run(run())


@app.command("import-file")
def import_file_command(
    input_file: Path = typer.Argument(..., exists=True, readable=True),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    cfg = _config(config)
    service = CrawlerService(cfg)
    try:
        summary = import_data_file(service, input_file)
        typer.echo(
            "Import hoàn tất: "
            f"tổng={summary.rows_found}, mới={summary.inserted}, cập nhật={summary.updated}, "
            f"không đổi={summary.unchanged}, loại={summary.rejected}"
        )
        if summary.reject_file:
            typer.echo(f"Dữ liệu lỗi: {summary.reject_file}")
    finally:
        asyncio.run(service.close())


@app.command("export")
def export(
    output: Path = typer.Option(Path("data/notices.xlsx"), "--output", "-o"),
    format: str = typer.Option("xlsx", "--format", case_sensitive=False),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    cfg = _config(config)
    db = Database(cfg.storage.database_url)
    db.create_all()
    fmt = format.lower()
    if fmt == "xlsx":
        path = export_xlsx(db, output)
    elif fmt == "csv":
        path = export_csv(db, output)
    else:
        raise typer.BadParameter("Format phải là xlsx hoặc csv")
    typer.echo(f"Đã xuất: {path}")


@app.command("report-daily")
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
    db.create_all()
    report_path = build_daily_report(
        db,
        path,
        report_date=selected_date,
        days_ahead=days_ahead or cfg.reporting.days_ahead,
    )
    typer.echo(f"Đã tạo báo cáo: {report_path}")
    if send_email:
        send_report_email(cfg, report_path)
        typer.echo("Đã gửi email báo cáo.")


@app.command("serve")
def serve(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8000, "--port", min=1, max=65535),
) -> None:
    import uvicorn

    uvicorn.run("qi_crawler.api:app", host=host, port=port, reload=False)


@app.command("import-evidence")
def import_evidence(
    input_file: Path = typer.Argument(..., exists=True, readable=True),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Import verified company capabilities used to support bid requirements."""
    cfg = _config(config)
    db = Database(cfg.storage.database_url)
    db.create_all()
    count = import_evidence_csv(db, input_file)
    typer.echo(f"Đã nhập/cập nhật {count} bằng chứng năng lực.")


@app.command("analyze-bid")
def analyze_bid(
    input_file: Path = typer.Argument(..., exists=True, readable=True),
    notice_id: int | None = typer.Option(None, "--notice-id", min=1),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Build an evidence-backed compliance matrix from a plain-text E-HSMT extract."""
    cfg = _config(config)
    db = Database(cfg.storage.database_url)
    db.create_all()
    result = analyze_bid_document(db, input_file, notice_id=notice_id)
    typer.echo(
        f"Phân tích {result.total} yêu cầu: đáp ứng={result.covered}, "
        f"một phần={result.partial}, thiếu={result.gaps}, coverage={result.coverage_percent}%"
    )


@app.command("predict-win")
def predict_win(
    notice_id: int | None = typer.Option(None, "--notice-id", min=1),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Estimate readiness and win likelihood with explicit low-confidence caveats."""
    cfg = _config(config)
    db = Database(cfg.storage.database_url)
    db.create_all()
    result = estimate_win_likelihood(db, notice_id=notice_id)
    typer.echo(f"Cổng SOP: {result.gate_status}")
    typer.echo(f"Điểm sẵn sàng hồ sơ: {result.readiness_score}%")
    typer.echo(
        f"Tỷ lệ trúng thầu ước tính: {result.estimated_win_percent}% "
        f"(độ tin cậy: {result.confidence_percent}%)"
    )
    typer.echo(f"Coverage yêu cầu bắt buộc: {result.mandatory_coverage_percent}%")
    typer.echo("Rủi ro chính:")
    for risk in result.risk_factors:
        typer.echo(f"  - {risk}")
    typer.echo("Cảnh báo: đây là ước tính MVP, không phải xác suất đã kiểm định hay bảo đảm trúng thầu.")


@app.command("bid-gate")
def bid_gate(
    notice_id: int | None = typer.Option(None, "--notice-id", min=1),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Apply the SOP mandatory-requirement GO/HOLD/NO-GO gate."""
    cfg = _config(config)
    db = Database(cfg.storage.database_url)
    db.create_all()
    result = evaluate_bid_gate(db, notice_id)
    typer.echo(
        f"Kết luận SOP: {result.status}; bắt buộc={result.mandatory_total}; "
        f"đã xác nhận={result.mandatory_confirmed}"
    )
    for blocker in result.blockers:
        typer.echo(f"  - {blocker}")


@app.command("confirm-assessment")
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
    db.create_all()
    confirm_assessment(db, assessment_id, reviewer, decision, note)
    typer.echo(f"Đã xác nhận assessment {assessment_id}: {decision} bởi {reviewer}.")


@app.command("collect-contracts-finder")
def collect_contracts_finder_command(
    keyword: str | None = typer.Option(None, "--keyword", "-k"),
    published_from: str | None = typer.Option(None, "--from", help="YYYY-MM-DD"),
    limit: int = typer.Option(20, "--limit", min=1, max=500),
    max_pages: int = typer.Option(10, "--max-pages", min=1, max=100),
    only_open: bool = typer.Option(True, "--only-open/--include-closed"),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Collect public UK procurement notices from the official OCDS API."""
    cfg = _config(config)

    async def run() -> None:
        service = CrawlerService(cfg)
        try:
            result = await collect_contracts_finder(
                service,
                keyword=keyword,
                published_from=date.fromisoformat(published_from) if published_from else None,
                limit=limit,
                max_pages=max_pages,
                only_open=only_open,
            )
            typer.echo(
                f"Contracts Finder: đọc={result.fetched}, khớp={result.matched}, "
                f"mới={result.inserted}, cập nhật={result.updated}, "
                f"bỏ qua hết hạn={result.expired_skipped}"
            )
        finally:
            await service.close()

    asyncio.run(run())


# ---------------------------------------------------------------------------
# Lệnh đơn giản cho người mới. Các lệnh kỹ thuật phía trên vẫn được giữ để
# vận hành nâng cao và tương thích với quy trình cũ.


@app.command("bat-dau")
def bat_dau(config: Path | None = typer.Option(None, "--config", exists=True)) -> None:
    """Khởi tạo MVP và hiển thị ba bước sử dụng cơ bản."""
    cfg = _config(config)
    Database(cfg.storage.database_url).create_all()
    typer.echo("MVP QI đã sẵn sàng.")
    typer.echo("1. Tìm gói:       QI-Crawler tim-goi --tu-khoa \"network switch\"")
    typer.echo("2. Xuất báo cáo: QI-Crawler xuat-bao-cao")
    typer.echo("3. Đánh giá:     QI-Crawler danh-gia data\\yeu-cau.txt")


@app.command("tim-goi")
def tim_goi(
    tu_khoa: str = typer.Option(
        ..., "--tu-khoa", "-k", help="Tên sản phẩm tiếng Việt hoặc tiếng Anh"
    ),
    tu_ngay: str | None = typer.Option(None, "--tu-ngay", help="YYYY-MM-DD; mặc định 30 ngày"),
    so_luong: int = typer.Option(20, "--so-luong", min=1, max=200),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Tìm và lưu các gói Contracts Finder còn hạn."""
    cfg = _config(config)
    expansion = _expand_and_learn(tu_khoa)
    _show_keyword_plan(expansion)

    async def run() -> None:
        service = CrawlerService(cfg)
        try:
            result = await collect_contracts_finder(
                service,
                keyword=expansion.search_terms,
                published_from=date.fromisoformat(tu_ngay) if tu_ngay else None,
                limit=so_luong,
                only_open=True,
            )
            typer.echo(f"Đã lưu {result.matched} gói còn hạn phù hợp từ khóa '{tu_khoa}'.")
            typer.echo(f"Đã bỏ qua {result.expired_skipped} gói hết hạn.")
            typer.echo("Bước tiếp theo: QI-Crawler xuat-bao-cao")
        finally:
            await service.close()

    asyncio.run(run())


@app.command("xuat-bao-cao")
def xuat_bao_cao(
    output: Path = typer.Option(Path("data/bao-cao-goi-thau.xlsx"), "--tep", "-o"),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Xuất danh sách gói thầu ra Excel."""
    cfg = _config(config)
    db = Database(cfg.storage.database_url)
    db.create_all()
    path = export_xlsx(db, output)
    typer.echo(f"Đã tạo báo cáo: {path}")


@app.command("danh-gia")
def danh_gia(
    yeu_cau: Path = typer.Argument(..., exists=True, readable=True),
    notice_id: int | None = typer.Option(None, "--ma-noi-bo", min=1),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Phân tích file yêu cầu và trả kết luận GO/HOLD/NO-GO."""
    cfg = _config(config)
    db = Database(cfg.storage.database_url)
    db.create_all()
    summary = analyze_bid_document(db, yeu_cau, notice_id=notice_id)
    gate = evaluate_bid_gate(db, notice_id)
    typer.echo(
        f"Đã đọc {summary.total} yêu cầu: đáp ứng={summary.covered}, "
        f"cần kiểm tra={summary.partial}, thiếu={summary.gaps}."
    )
    typer.echo(f"Kết luận hiện tại: {gate.status}")
    for blocker in gate.blockers[:10]:
        typer.echo(f"  - {blocker}")
    if gate.status != "GO":
        typer.echo("Cần người phụ trách kiểm tra bằng chứng trước khi trình duyệt.")


@app.command("them-nguon")
def them_nguon(
    ten: str = typer.Option(..., "--ten", help="Tên ngắn, ví dụ: muasamcong"),
    url: str = typer.Option(..., "--url", help="Địa chỉ trang danh sách gói thầu"),
    item_selector: str = typer.Option("a[href]", "--vung-ket-qua", hidden=True),
    link_selector: str = typer.Option("a", "--link", hidden=True),
    next_selector: str | None = typer.Option(None, "--trang-sau", hidden=True),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Thêm một website có trang danh sách gói thầu."""
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
    typer.echo(f"Đã thêm nguồn '{source.name}': {source.domain}")
    typer.echo(f"Cấu hình cục bộ: {path}")
    typer.echo(f"Bước tiếp theo: QI-Crawler dang-nhap --ten {source.name}")


@app.command("them-tu-khoa")
def them_tu_khoa(
    tu_khoa: str = typer.Option(..., "--tu-khoa", "-k", help="Tên sản phẩm mới"),
    ten_khac: list[str] = typer.Option(
        [], "--ten-khac", help="Tên Anh/viết tắt; có thể nhập nhiều lần"
    ),
    mo_ta: str = typer.Option("", "--mo-ta", help="Mô tả ngắn giúp xác định nhóm ngành"),
    nhom: str | None = typer.Option(None, "--nhom", help="Chỉ định nhóm nếu muốn xác nhận thủ công"),
) -> None:
    """Tự phân loại và cập nhật một từ khóa sản phẩm mới."""
    result = learn_keyword(
        tu_khoa,
        aliases=tuple(ten_khac),
        description=mo_ta,
        category_name=nhom,
    )
    if result.status == "updated":
        typer.echo(f"Đã cập nhật '{result.keyword}' vào nhóm '{result.category}'.")
        typer.echo(f"Độ tin cậy phân loại: {result.confidence:.0%}")
        if result.matched_signals:
            typer.echo(f"Tín hiệu nhận diện: {', '.join(result.matched_signals)}")
    else:
        typer.echo("Chưa xác định được nhóm ngành một cách an toàn.")
        typer.echo("Từ khóa đã được lưu vào pending_keywords trong keyword-groups.yaml.")
        typer.echo("Chạy lại với --nhom \"TÊN NHÓM\" sau khi người phụ trách xác nhận.")


@app.command("dang-nhap")
def dang_nhap(
    ten: str = typer.Option(..., "--ten"),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Mở trình duyệt để người dùng tự đăng nhập và lưu phiên cục bộ."""
    cfg = _config(config)
    source = load_source(ten)
    path = asyncio.run(create_login_session(cfg, source))
    typer.echo(f"Đã lưu phiên đăng nhập cục bộ cho '{source.name}': {path}")
    typer.echo("Không gửi file session cho người khác và không đưa file này lên Git.")


@app.command("tim-tren-web")
def tim_tren_web(
    ten: str = typer.Option(..., "--ten"),
    tu_khoa: str = typer.Option(..., "--tu-khoa", "-k"),
    so_luong: int = typer.Option(50, "--so-luong", min=1, max=500),
    config: Path | None = typer.Option(None, "--config", exists=True),
) -> None:
    """Tìm link gói thầu bằng phiên đăng nhập đã lưu."""
    cfg = _config(config)
    source = load_source(ten)
    expansion = _expand_and_learn(tu_khoa)
    _show_keyword_plan(expansion)

    async def run() -> None:
        service = CrawlerService(cfg)
        try:
            result = await collect_authenticated_source(
                service, source, keyword=expansion.search_terms, limit=so_luong
            )
            typer.echo(
                f"Đã xem {result.scanned} mục, lưu {result.matched} gói phù hợp "
                f"(mới={result.inserted}, cập nhật={result.updated})."
            )
            typer.echo("Bước tiếp theo: QI-Crawler xuat-bao-cao")
        finally:
            await service.close()

    asyncio.run(run())


if __name__ == "__main__":
    app()
