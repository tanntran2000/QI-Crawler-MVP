from __future__ import annotations

import asyncio
from datetime import date
from pathlib import Path

import typer

from .browser import BrowserFetcher
from .config import EnvSettings, load_config
from .crawler import CrawlerService
from .db import Database
from .exporter import export_csv, export_xlsx
from .importer import import_file as import_data_file
from .logging_utils import configure_logging
from .reporting import build_daily_report, send_report_email

app = typer.Typer(
    no_args_is_help=True,
    help="Crawler dữ liệu đấu thầu công khai: allowlist, robots.txt, rate limit và audit.",
)


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
    selected_date = date.fromisoformat(report_date) if report_date else date.today()
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

    uvicorn.run("egp_crawler.api:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    app()
