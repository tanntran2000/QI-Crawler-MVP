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


@pytest.mark.parametrize("status_code", [404, 410])
def test_missing_robots_allows_crawl(status_code: int) -> None:
    def missing(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code)

    policy = AccessPolicy(_config())

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(missing)) as client:
            assert (
                await policy.robots_status(client, "https://example.test/tender/1")
                is RobotsStatus.ROBOTS_ABSENT
            )
            await policy.require_robots_access(client, "https://example.test/tender/1")

    asyncio.run(run())


def test_robots_403_requires_human_review() -> None:
    def forbidden(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(403)

    policy = AccessPolicy(_config())

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(forbidden)) as client:
            with pytest.raises(AccessDenied, match="ROBOTS_UNAVAILABLE.*HUMAN_REQUIRED"):
                await policy.require_robots_access(client, "https://example.test/tender/1")

    asyncio.run(run())


def test_robots_500_requires_human_review() -> None:
    def unavailable(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    policy = AccessPolicy(_config())

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(unavailable)) as client:
            with pytest.raises(AccessDenied, match="ROBOTS_UNAVAILABLE.*HUMAN_REQUIRED"):
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
            with pytest.raises(AccessDenied, match="robots.txt khong cho phep"):
                await policy.require_robots_access(client, "https://example.test/tender/1")

    asyncio.run(run())


def test_robots_explicit_allow_permits_crawl() -> None:
    def allow(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="User-agent: *\nAllow: /tender")

    policy = AccessPolicy(_config())

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(allow)) as client:
            assert (
                await policy.robots_status(client, "https://example.test/tender/1")
                is RobotsStatus.ALLOW
            )
            await policy.require_robots_access(client, "https://example.test/tender/1")

    asyncio.run(run())
