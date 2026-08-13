import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

from qi_crawler.authenticated_sources import (
    WebSource,
    collect_authenticated_source,
    egp_vietnam_source,
    safe_source_name,
    session_path,
)
from qi_crawler.compliance import AccessDenied


def test_web_source_extracts_domain():
    source = WebSource(name="QI Portal", list_url="https://example.gov.vn/tenders")
    assert source.domain == "example.gov.vn"


def test_safe_source_name():
    assert safe_source_name("  QI Vi\u1ec7t Nam  ") == "qi-viet-nam"
    with pytest.raises(ValueError):
        safe_source_name("***")


def test_egp_vietnam_profile_uses_stable_detail_url_markers() -> None:
    source = egp_vietnam_source()

    assert source.domain == "muasamcong.mpi.gov.vn"
    assert "notifyNo=" in source.item_selector
    assert "contractor-selection" in source.item_selector
    assert source.page_ready == "main, body"


def test_authenticated_collection_stops_on_detail_access_denied(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A protected detail page must not be saved as incomplete list metadata."""
    monkeypatch.chdir(tmp_path)
    source = WebSource(
        name="portal",
        list_url="https://portal.example/tenders",
        item_selector=".tender",
        link_selector="a",
        page_ready="body",
    )
    state = session_path(source.name)
    state.parent.mkdir(parents=True)
    state.write_text("{}", encoding="utf-8")

    class Ready:
        first = None

        def __init__(self) -> None:
            self.first = self

        async def wait_for(self, **_kwargs) -> None:
            return None

    class Candidate:
        first = None

        def __init__(self) -> None:
            self.first = self

        async def count(self) -> int:
            return 1

        async def get_attribute(self, name: str) -> str | None:
            return "/tenders/1" if name == "href" else None

    class Item(Candidate):
        async def inner_text(self) -> str:
            return "Network switch"

        def locator(self, _selector: str) -> Candidate:
            return Candidate()

    class Items:
        async def count(self) -> int:
            return 1

        def nth(self, _index: int) -> Item:
            return Item()

    class ListPage:
        url = source.list_url

        async def goto(self, *_args, **_kwargs) -> None:
            return None

        def locator(self, selector: str):
            return Items() if selector == source.item_selector else Ready()

        async def close(self) -> None:
            return None

    class DetailPage:
        async def goto(self, *_args, **_kwargs) -> None:
            raise AccessDenied("HTTP 403; HUMAN_REQUIRED")

        async def close(self) -> None:
            return None

    class Browser:
        def __init__(self) -> None:
            self.limiter = SimpleNamespace(wait=self._wait)
            self.policy = SimpleNamespace(detect_block_page=lambda _html: None)
            self._pages = [ListPage(), DetailPage()]

        async def _wait(self, _url: str) -> None:
            return None

        async def ensure_browser_access_allowed(self, _url: str) -> None:
            return None

        async def start(self, **_kwargs) -> None:
            return None

        async def new_page(self):
            return self._pages.pop(0)

    service = SimpleNamespace(
        browser=Browser(),
        config=SimpleNamespace(
            crawl=SimpleNamespace(render_wait_ms=0),
            storage=SimpleNamespace(allowed_attachment_extensions={".pdf"}),
        ),
        upsert_parsed_notice=lambda *_args, **_kwargs: pytest.fail(
            "AccessDenied detail must not be persisted"
        ),
    )

    with pytest.raises(AccessDenied, match="HUMAN_REQUIRED"):
        asyncio.run(collect_authenticated_source(service, source, "switch"))
