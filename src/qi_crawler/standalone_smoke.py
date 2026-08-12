"""Packaged-runtime smoke checks used by release engineering."""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from .browser import BrowserFetcher
from .config import AppConfig
from .gui_services import run_export, run_scan, run_search, run_single_crawl

COTEC_LIST_URL = "https://ebidding.coteccons.vn/Index"
COTEC_DETAIL_URL = "https://ebidding.coteccons.vn/Index/ChiTiet/2607301"


def _browser_smoke(config: AppConfig) -> None:
    async def execute() -> None:
        browser = BrowserFetcher(config)
        try:
            await browser.start(headed=False)
            page = await browser.new_page()
            await page.close()
        finally:
            await browser.close()

    asyncio.run(execute())


def run_standalone_smoke(
    config: AppConfig,
    report_path: Path,
    *,
    include_network: bool = False,
) -> bool:
    """Exercise packaged resources and optionally permitted live crawl paths."""
    results: dict[str, object] = {
        "started_at": datetime.now(UTC).isoformat(),
        "include_network": include_network,
        "checks": {},
    }
    checks = results["checks"]
    assert isinstance(checks, dict)
    success = True

    def run_check(name: str, function) -> None:
        nonlocal success
        try:
            value = function()
        except Exception as exc:  # noqa: BLE001 - release smoke must record every failure
            success = False
            checks[name] = {"status": "FAILED", "error": str(exc)}
        else:
            checks[name] = {"status": "PASS", "result": value}

    run_check("browser_launch", lambda: (_browser_smoke(config), "Chromium started")[1])
    run_check("search", lambda: len(run_search(config, "smoke-test")))
    run_check(
        "export",
        lambda: str(run_export(config).output),
    )
    if include_network:
        run_check(
            "single_url_crawl",
            lambda: run_single_crawl(config, COTEC_DETAIL_URL),
        )
        run_check(
            "list_scan",
            lambda: asdict(run_scan(config, COTEC_LIST_URL, 1, "")),
        )

        def search_after_crawl() -> int:
            count = len(run_search(config, "goi thau"))
            if count < 1:
                raise RuntimeError("Search khong tim thay goi vua crawl")
            return count

        def export_after_crawl() -> dict[str, object]:
            result = run_export(config)
            if result.exported_records < 1:
                raise RuntimeError("Export khong co dong du lieu sau live crawl")
            return {
                "output": str(result.output),
                "exported_records": result.exported_records,
                "warning_records": result.warning_records,
            }

        run_check("search_after_crawl", search_after_crawl)
        run_check("export_after_crawl", export_after_crawl)

    results["finished_at"] = datetime.now(UTC).isoformat()
    results["status"] = "PASS" if success else "FAILED"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return success
