from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import StrEnum
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

from .config import AppConfig

logger = logging.getLogger(__name__)

CAPTCHA_MARKERS = (
    "captcha",
    "recaptcha",
    "hcaptcha",
    "xac minh ban khong phai ro-bot",
    "verify you are human",
    "access denied",
)


class AccessDenied(RuntimeError):
    pass


class SessionExpired(AccessDenied):
    """A permitted site redirected an authenticated browser back to login."""


class RobotsStatus(StrEnum):
    ALLOW = "ALLOW"
    ROBOTS_ABSENT = "ROBOTS_ABSENT"
    DISALLOW = "DISALLOW"
    UNAVAILABLE = "UNAVAILABLE"


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
        self._robots_status: dict[str, RobotsStatus] = {}

    def validate_domain(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise AccessDenied(f"Scheme khong duoc phep: {parsed.scheme}")
        host = (parsed.hostname or "").lower()
        if not any(host == d or host.endswith(f".{d}") for d in self.config.allowed_domains):
            raise AccessDenied(f"Domain ngoai allowlist: {host}")

    async def robots_status(self, client: httpx.AsyncClient, url: str) -> RobotsStatus:
        if not self.config.compliance.obey_robots_txt:
            return RobotsStatus.ALLOW
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if origin in self._robots:
            parser = self._robots[origin]
            return (
                RobotsStatus.ALLOW
                if parser.can_fetch(self.config.compliance.identify_user_agent, url)
                else RobotsStatus.DISALLOW
            )
        if origin in self._robots_status:
            return self._robots_status[origin]
        if origin not in self._robots_status:
            robots_url = f"{origin}/robots.txt"
            parser = RobotFileParser()
            parser.set_url(robots_url)
            try:
                response = await client.get(robots_url, follow_redirects=True)
                if response.status_code == 200:
                    parser.parse(response.text.splitlines())
                    self._robots[origin] = parser
                    return (
                        RobotsStatus.ALLOW
                        if parser.can_fetch(self.config.compliance.identify_user_agent, url)
                        else RobotsStatus.DISALLOW
                    )
                elif response.status_code in {404, 410}:
                    # A missing robots.txt is not an access restriction.
                    self._robots_status[origin] = RobotsStatus.ROBOTS_ABSENT
                elif response.status_code in {401, 403}:
                    logger.warning("robots.txt bi tu choi; can nguoi kiem tra: %s", robots_url)
                    self._robots_status[origin] = RobotsStatus.UNAVAILABLE
                else:
                    logger.warning("robots.txt khong san sang HTTP %s: %s", response.status_code, robots_url)
                    self._robots_status[origin] = RobotsStatus.UNAVAILABLE
            except httpx.HTTPError as exc:
                logger.warning("Khong doc duoc robots.txt (%s); can nguoi kiem tra", exc)
                self._robots_status[origin] = RobotsStatus.UNAVAILABLE
        return self._robots_status[origin]

    async def allowed_by_robots(self, client: httpx.AsyncClient, url: str) -> bool:
        """Compatibility wrapper: unavailable access fails closed, never as DISALLOW."""
        return (await self.robots_status(client, url)) in {
            RobotsStatus.ALLOW,
            RobotsStatus.ROBOTS_ABSENT,
        }

    async def require_robots_access(self, client: httpx.AsyncClient, url: str) -> None:
        status = await self.robots_status(client, url)
        if status is RobotsStatus.UNAVAILABLE:
            raise AccessDenied(
                f"ROBOTS_UNAVAILABLE: khong the xac minh robots.txt cho {url}; HUMAN_REQUIRED"
            )
        if status is RobotsStatus.DISALLOW:
            raise AccessDenied(f"robots.txt khong cho phep crawl URL: {url}")

    def detect_block_page(self, content: str) -> None:
        if not self.config.compliance.stop_on_captcha:
            return
        lowered = content.lower()
        found = next((marker for marker in CAPTCHA_MARKERS if marker in lowered), None)
        if found:
            raise AccessDenied(f"Phat hien trang CAPTCHA/chan truy cap ({found}); crawler da dung.")
