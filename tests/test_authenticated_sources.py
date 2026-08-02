import pytest

from qi_crawler.authenticated_sources import (
    WebSource,
    egp_vietnam_source,
    safe_source_name,
)


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
