"""Config-driven adapters for tender websites.

Each new portal adds one adapter class and one entry under ``sources`` in the
YAML configuration. The crawler core only asks this registry for a supported
URL and a normalized ``ParsedNotice``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

from .config import AppConfig, SourceConfig
from .parser import ParsedNotice, extract_detail_links, parse_notice_html


@dataclass(frozen=True)
class SourceIdentity:
    source_name: str
    source_notice_id: str | None


class SourceAdapter(ABC):
    def __init__(self, source_name: str, source: SourceConfig):
        self.source_name = source_name
        self.source = source

    def supports(self, url: str) -> bool:
        hostname = (urlparse(url).hostname or "").lower()
        return hostname == self.source.domain or hostname.endswith(f".{self.source.domain}")

    @abstractmethod
    def extract_identity(self, url: str, html: str) -> SourceIdentity:
        """Return the website-local stable identifier, if the URL/page provides one."""

    def discover(self, html: str, list_url: str) -> list[str]:
        return extract_detail_links(html, list_url, "a[href]", "a[href]", [self.source.domain])

    def parse_detail(self, html: str, url: str) -> ParsedNotice:
        parsed = parse_notice_html(html, url)
        identity = self.extract_identity(url, html)
        parsed.source_name = identity.source_name
        parsed.source_notice_id = identity.source_notice_id or parsed.source_notice_id
        return parsed


class EGPAdapter(SourceAdapter):
    def extract_identity(self, url: str, html: str) -> SourceIdentity:
        query = parse_qs(urlparse(url).query)
        source_id = next(
            (query[key][0] for key in ("notifyNo", "noticeId", "notice_id") if query.get(key)),
            None,
        )
        return SourceIdentity(self.source_name, source_id)


class CotecconsAdapter(SourceAdapter):
    def extract_identity(self, url: str, html: str) -> SourceIdentity:
        parts = [part for part in urlparse(url).path.split("/") if part]
        source_id = next((part for part in reversed(parts) if part.isdigit()), None)
        return SourceIdentity(self.source_name, source_id)


_ADAPTER_TYPES: dict[str, type[SourceAdapter]] = {
    "egp": EGPAdapter,
    "coteccons": CotecconsAdapter,
}


class SourceRegistry:
    def __init__(self, config: AppConfig):
        self._adapters = tuple(
            _ADAPTER_TYPES[source.adapter](name, source)
            for name, source in sorted(
                config.sources.items(), key=lambda item: item[1].priority
            )
            if source.enabled and source.adapter in _ADAPTER_TYPES
        )

    def adapter_for_url(self, url: str) -> SourceAdapter | None:
        return next((adapter for adapter in self._adapters if adapter.supports(url)), None)

    def require_adapter(self, url: str) -> SourceAdapter:
        adapter = self.adapter_for_url(url)
        if adapter is None:
            raise ValueError("URL khong thuoc nguon dang bat trong cau hinh sources.")
        return adapter
