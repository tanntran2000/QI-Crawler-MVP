from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from qi_crawler.compliance import SessionExpired
from qi_crawler.config import AppConfig
from qi_crawler.crawler import CrawlerService

EGP_URL = (
    "https://muasamcong.mpi.gov.vn/vi/web/guest/contractor-selection?notifyNo=IB2600123456"
)
EGP_HTML = """
<html><body>
  <h1>Ten goi thau: Cung cap thiet bi mang</h1>
  <p>Ma TBMT: IB2600123456</p>
</body></html>
"""


def test_configured_session_is_reused_for_authenticated_crawl(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    state = tmp_path / "data" / "sessions" / "egp_storage_state.json"
    state.parent.mkdir(parents=True)
    state.write_text("{}", encoding="utf-8")
    config = AppConfig.model_validate(
        {
            "sources": {
                "egp": {
                    "enabled": True,
                    "priority": 1,
                    "domain": "muasamcong.mpi.gov.vn",
                    "adapter": "egp",
                }
            },
            "storage": {
                "database_url": f"sqlite:///{tmp_path / 'authenticated.db'}",
                "raw_dir": str(tmp_path / "raw"),
                "download_attachments": False,
            },
        }
    )
    service = CrawlerService(config)
    captured: list[Path] = []

    async def authenticated_fetch(url: str, storage_state: Path) -> str:
        assert url == EGP_URL
        captured.append(storage_state)
        return EGP_HTML

    async def unexpected_http_fetch(_url: str) -> str:
        raise AssertionError("authenticated crawl must not use the plain HTTP path")

    service.browser.fetch_authenticated_html = authenticated_fetch  # type: ignore[method-assign]
    service.http.fetch = unexpected_http_fetch  # type: ignore[method-assign]
    try:
        notice = asyncio.run(service.crawl_notice(EGP_URL))
        assert captured == [Path("data/sessions/egp_storage_state.json")]
        assert notice.source_name == "egp"
        assert notice.source_notice_id == "IB2600123456"
    finally:
        asyncio.run(service.close())


def test_egp_crawl_stops_when_authenticated_session_is_missing(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    config = AppConfig.model_validate(
        {
            "sources": {
                "egp": {
                    "enabled": True,
                    "priority": 1,
                    "domain": "muasamcong.mpi.gov.vn",
                    "adapter": "egp",
                    "requires_auth": True,
                }
            },
            "storage": {"database_url": f"sqlite:///{tmp_path / 'missing-session.db'}"},
        }
    )
    service = CrawlerService(config)
    try:
        with pytest.raises(SessionExpired, match="EGP_SESSION_EXPIRED"):
            asyncio.run(service.crawl_notice(EGP_URL))
    finally:
        asyncio.run(service.close())
