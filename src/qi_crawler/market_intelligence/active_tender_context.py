"""Session-scoped active working-package identity for Bid Radar."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .opportunity_contract import OpportunitySourceType

if TYPE_CHECKING:
    from .opportunity_radar import OpportunityRadarItem


@dataclass(frozen=True, slots=True)
class ActiveTenderContext:
    """Immutable identity for the package an operator is currently working on.

    The context deliberately remains session-only.  Its exact revision and source
    observation coordinates prevent a row selection or a same-lineage revision from
    silently becoming the active package.
    """

    source_type: OpportunitySourceType
    raw_id: str
    base_id: str
    revision: str | None
    source_sha256: str
    observation_key: str
    package_name: str

    def __post_init__(self) -> None:
        source_type = OpportunitySourceType(self.source_type)
        if not isinstance(self.raw_id, str) or not self.raw_id.strip():
            raise ValueError("active context requires exact identity")
        if not isinstance(self.base_id, str) or not self.base_id.strip():
            raise ValueError("active context requires exact identity")
        raw_parts = self.raw_id.rsplit("-", 1)
        if raw_parts[0].strip() != self.base_id.strip() or (
            len(raw_parts) == 2
            and self.revision is not None
            and raw_parts[1].strip() != self.revision.strip()
        ):
            raise ValueError("active context identity does not match raw_id")
        if not self.source_sha256 or not self.observation_key:
            raise ValueError("active context requires source provenance")
        if not isinstance(self.package_name, str):
            raise TypeError("active context package_name must be text")
        object.__setattr__(self, "source_type", source_type)

    @classmethod
    def from_item(cls, item: OpportunityRadarItem) -> ActiveTenderContext:
        identity = item.identity
        source_type = getattr(item.source_type, "value", item.source_type)
        return cls(
            source_type=OpportunitySourceType(source_type),
            raw_id=identity.raw_id,
            base_id=identity.base_id,
            revision=identity.revision,
            source_sha256=item.source_sha256,
            observation_key=item.observation_key,
            package_name=item.package_name,
        )

    @property
    def exact_identity(self) -> tuple[str, str, str, str | None]:
        """Return the source namespace plus the complete exact revision key."""

        return (self.source_type.value, self.raw_id, self.base_id, self.revision)

    def matches_item(self, item: OpportunityRadarItem) -> bool:
        """Require exact identity *and* unchanged source provenance."""

        identity = item.identity
        source_type = getattr(item.source_type, "value", item.source_type)
        return (
            self.source_type is OpportunitySourceType(source_type)
            and self.raw_id == identity.raw_id
            and self.base_id == identity.base_id
            and self.revision == identity.revision
            and self.source_sha256.casefold() == item.source_sha256.casefold()
            and self.observation_key == item.observation_key
        )


def active_context_from_item(item: OpportunityRadarItem) -> ActiveTenderContext:
    return ActiveTenderContext.from_item(item)


def exact_identity_matches(
    context: ActiveTenderContext | None,
    item: OpportunityRadarItem | None,
) -> bool:
    return context is not None and item is not None and context.matches_item(item)


__all__ = ["ActiveTenderContext", "active_context_from_item", "exact_identity_matches"]
