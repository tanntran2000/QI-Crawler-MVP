from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

from .config import AppConfig

logger = logging.getLogger(__name__)

CAPTCHA_MARKERS = (
    "captcha",
    "recaptcha",
    "hcaptcha",
    "xác minh bạn không phải rô-bốt",
    "verify you are human",
    "access denied",
)


class AccessDenied(RuntimeError):
    pass


@dataclass
class DomainRateLimiter:
    requests_per_minute: int
    _locks: dict[str, asyncio.Lock] = field(default_factory=dict)
    _last_request: dict[str, float] = field(default_factory=dict)

    async def wait(self, url: str) -> None:
        domain = urlparse(url).netloc.lower()
        lock = self._locks.setdefault(domain, asyncio.Lock())
        interval = 60.0 / self.requests_per_minute
        async with lock:
            elapsed = time.monotonic() - self._last_request.get(domain, 0.0)
            if elapsed < interval:
                await asyncio.sleep(interval - elapsed)
            self._last_request[domain] = time.monotonic()


class AccessPolicy:
    def __init__(self, config: AppConfig):
        self.config = config
        self._robots: dict[str, RobotFileParser] = {}

    def validate_domain(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise AccessDenied(f"Scheme không được phép: {parsed.scheme}")
        host = (parsed.hostname or "").lower()
        if not any(host == d or host.endswith(f".{d}") for d in self.config.allowed_domains):
            raise AccessDenied(f"Domain ngoài allowlist: {host}")

    async def allowed_by_robots(self, client: httpx.AsyncClient, url: str) -> bool:
        if not self.config.compliance.obey_robots_txt:
            return True
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if origin not in self._robots:
            robots_url = f"{origin}/robots.txt"
            parser = RobotFileParser()
            parser.set_url(robots_url)
            try:
                response = await client.get(robots_url, follow_redirects=True)
                if response.status_code == 200:
                    parser.parse(response.text.splitlines())
                elif response.status_code in {401, 403}:
                    logger.warning("robots.txt bị từ chối; mặc định không crawl: %s", robots_url)
                    parser.parse(["User-agent: *", "Disallow: /"])
                else:
                    parser.parse([])
            except httpx.HTTPError as exc:
                logger.warning("Không đọc được robots.txt (%s); mặc định không crawl", exc)
                parser.parse(["User-agent: *", "Disallow: /"])
            self._robots[origin] = parser
        return self._robots[origin].can_fetch(self.config.compliance.identify_user_agent, url)

    def detect_block_page(self, content: str) -> None:
        if not self.config.compliance.stop_on_captcha:
            return
        lowered = content.lower()
        found = next((marker for marker in CAPTCHA_MARKERS if marker in lowered), None)
        if found:
            raise AccessDenied(f"Phát hiện trang CAPTCHA/chặn truy cập ({found}); crawler đã dừng.")
