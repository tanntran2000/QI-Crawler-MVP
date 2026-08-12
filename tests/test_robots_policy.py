from __future__ import annotations

import asyncio

import httpx
import pytest

from qi_crawler.compliance import AccessDenied, AccessPolicy, RobotsStatus
from qi_crawler.config import AppConfig


def _config() -> AppConfig:
    return AppConfig(allowed_domains=["example.test"])


def test_robots_unavailable_requires_human_review() -> None:
    async def unavailable(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("TLS unavailable")

    policy = AccessPolicy(_config())
    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(unavailable)) as client:
            status = await policy.robots_status(client, "https://example.test/tender/1")
            assert status is RobotsStatus.UNAVAILABLE
            with pytest.raises(AccessDenied, match="ROBOTS_UNAVAILABLE"):
                await policy.require_robots_access(client, "https://example.test/tender/1")

    asyncio.run(run())


def test_robots_explicit_disallow_stops_crawl() -> None:
    def disallow(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="User-agent: *\nDisallow: /tender")

    policy = AccessPolicy(_config())
    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(disallow)) as client:
            assert (
                await policy.robots_status(client, "https://example.test/tender/1")
                is RobotsStatus.DISALLOW
            )

    asyncio.run(run())
