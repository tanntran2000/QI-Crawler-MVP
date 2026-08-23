from __future__ import annotations

from qi_crawler.market_intelligence.opportunity_contract import OpportunityIdentityNamespace
from qi_crawler.market_intelligence.tbmt_normalization import (
    compact_source_text,
    parse_tbmt_notice_identity,
)


def test_compact_source_text_preserves_numeric_and_ordinary_values() -> None:
    assert compact_source_text(23) == "23"
    assert compact_source_text(23.0) == "23"
    assert compact_source_text("23") == "23"
    assert compact_source_text("  máy   chủ  ") == "máy chủ"


def test_compact_source_text_returns_none_only_for_empty_values() -> None:
    assert compact_source_text(None) is None
    assert compact_source_text(" \t ") is None


def test_parse_tbmt_identity_from_embedded_package_text() -> None:
    identity = parse_tbmt_notice_identity("Gói mua sắm thiết bị IB2600463290-00")

    assert identity is not None
    assert identity.raw_id == "IB2600463290-00"
    assert identity.base_id == "IB2600463290"
    assert identity.revision == "00"
    assert identity.namespace is OpportunityIdentityNamespace.IB


def test_parse_tbmt_identity_preserves_whitespace_in_raw_match() -> None:
    identity = parse_tbmt_notice_identity("Gói mua sắm IB2600463290- 00")

    assert identity is not None
    assert identity.raw_id == "IB2600463290- 00"
    assert identity.base_id == "IB2600463290"
    assert identity.revision == "00"


def test_parse_tbmt_identity_returns_none_for_pl_identity() -> None:
    assert parse_tbmt_notice_identity("Số kế hoạch PL2600245672-02") is None


def test_parse_tbmt_identity_requires_revision() -> None:
    assert parse_tbmt_notice_identity("Gói mua sắm IB2600463290") is None


def test_parse_tbmt_identity_rejects_malformed_revision() -> None:
    assert parse_tbmt_notice_identity("Gói mua sắm IB2600463290-0A") is None
    assert parse_tbmt_notice_identity("Gói mua sắm IB2600463290-000") is None


def test_parse_tbmt_identity_rejects_multiple_ib_identities() -> None:
    value = "IB2600463290-00 và IB2600463291-00"

    assert parse_tbmt_notice_identity(value) is None


def test_parse_tbmt_identity_rejects_mixed_pl_and_ib_identities() -> None:
    value = "PL2600245672-02 / IB2600463290-00"

    assert parse_tbmt_notice_identity(value) is None


def test_parse_tbmt_identity_returns_none_without_procurement_identity() -> None:
    assert parse_tbmt_notice_identity("Thiết bị mạng và phụ kiện") is None
