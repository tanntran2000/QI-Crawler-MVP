from __future__ import annotations

import importlib
from decimal import Decimal

import pytest

from qi_crawler.market_intelligence.khmt_normalization import normalize_search_value


def _normalization_module():
    try:
        return importlib.import_module("qi_crawler.market_intelligence.value_normalization")
    except ModuleNotFoundError as exc:
        pytest.fail(f"money normalization seam is missing: {exc}")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1000000000", Decimal(1000000000)),
        ("1.000.000.000", Decimal(1000000000)),
        ("1,000,000,000", Decimal(1000000000)),
        ("1 000 000 000", Decimal(1000000000)),
        ("1\u00a0000\u00a0000\u00a0000", Decimal(1000000000)),
    ],
)
def test_normalize_money_value_accepts_unambiguous_integer_forms(raw: str, expected: Decimal) -> None:
    module = _normalization_module()

    assert module.normalize_money_value(raw) == expected


@pytest.mark.parametrize(
    "raw",
    ["1.000.00", "1,00,000", "1.000,50", "abc", "1 tỷ", "--1000"],
)
def test_normalize_money_value_rejects_ambiguous_or_invalid_forms(raw: str) -> None:
    module = _normalization_module()

    assert module.normalize_money_value(raw) is None


def test_parse_optional_money_input_is_strict_at_ui_boundary() -> None:
    module = _normalization_module()

    assert module.parse_optional_money_input("") is None
    assert module.parse_optional_money_input("   ") is None
    assert module.parse_optional_money_input("1.000.000") == Decimal(1000000)
    with pytest.raises(ValueError, match="số hợp lệ"):
        module.parse_optional_money_input("1.000.00")


def test_numeric_text_remains_text_outside_money_schema() -> None:
    assert normalize_search_value("1.000.000") == "1.000.000"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("225.282.240", Decimal(225282240)),
        ("486.490.000", Decimal(486490000)),
        ("1.181.000.000", Decimal(1181000000)),
    ],
)
def test_existing_source_price_regressions_remain_supported(raw: str, expected: Decimal) -> None:
    from qi_crawler.market_intelligence.khmt_normalization import parse_package_price

    assert parse_package_price(raw) == expected
