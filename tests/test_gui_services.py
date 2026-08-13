from __future__ import annotations

from qi_crawler import gui_services
from qi_crawler.config import AppConfig


def test_single_crawl_service_logs_start_and_completion(monkeypatch, caplog) -> None:
    class StubCrawlerService:
        human_required_reason = None

        def __init__(self, _config: AppConfig) -> None:
            pass

        async def crawl_urls(self, urls: list[str]) -> tuple[int, int]:
            assert urls == ["https://ebidding.coteccons.vn/Index/ChiTiet/2608121"]
            return 1, 0

        async def close(self) -> None:
            return None

    monkeypatch.setattr(gui_services, "CrawlerService", StubCrawlerService)
    caplog.set_level("INFO", logger="qi_crawler.gui_services")

    result = gui_services.run_single_crawl(
        AppConfig(),
        "https://ebidding.coteccons.vn/Index/ChiTiet/2608121",
    )

    assert result == (1, 0, None)
    messages = "\n".join(caplog.messages)
    assert "SERVICE_START operation=single_crawl" in messages
    assert "SERVICE_DONE operation=single_crawl" in messages
