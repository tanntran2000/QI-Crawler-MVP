from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx

from .compliance import AccessDenied, AccessPolicy, DomainRateLimiter
from .config import AppConfig


@dataclass
class FetchResult:
    url: str
    status_code: int
    content_type: str
    text: str


class HttpFetcher:
    def __init__(self, config: AppConfig):
        self.config = config
        self.policy = AccessPolicy(config)
        self.limiter = DomainRateLimiter(config.crawl.requests_per_minute)
        self.client = httpx.AsyncClient(
            timeout=config.crawl.request_timeout_seconds,
            headers={"User-Agent": config.compliance.identify_user_agent},
            follow_redirects=True,
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def fetch(self, url: str) -> FetchResult:
        self.policy.validate_domain(url)
        await self.policy.require_robots_access(self.client, url)

        attempts = self.config.crawl.max_retries + 1
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                await self.limiter.wait(url)
                response = await self.client.get(url)
                if response.status_code in {401, 403, 429}:
                    raise AccessDenied(
                        f"May chu tu choi/gioi han truy cap HTTP {response.status_code}: {url}"
                    )
                response.raise_for_status()
                content_type = response.headers.get("content-type", "")
                text = response.text
                self.policy.detect_block_page(text)
                return FetchResult(str(response.url), response.status_code, content_type, text)
            except (httpx.TransportError, httpx.TimeoutException) as exc:
                last_error = exc
                if attempt + 1 >= attempts:
                    break
                await asyncio.sleep(min(2**attempt + 0.25 * attempt, 15))
        assert last_error is not None
        raise last_error
