import pytest

from qi_crawler.authenticated_sources import WebSource, safe_source_name


def test_web_source_extracts_domain():
    source = WebSource(name="QI Portal", list_url="https://example.gov.vn/tenders")
    assert source.domain == "example.gov.vn"


def test_safe_source_name():
    assert safe_source_name("  QI Việt Nam  ") == "qi-vi-t-nam"
    with pytest.raises(ValueError):
        safe_source_name("***")
