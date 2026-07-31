from qi_crawler.contracts_finder import release_matches, release_to_notice

SAMPLE_RELEASE = {
    "ocid": "ocds-test-123",
    "date": "2026-07-30T10:00:00Z",
    "buyer": {"name": "Example Council"},
    "tender": {
        "title": "Network security services",
        "description": "Managed firewall and monitoring service",
        "datePublished": "2026-07-30T10:00:00Z",
        "tenderPeriod": {"endDate": "2026-08-30T12:00:00Z"},
        "value": {"amount": 250000, "currency": "GBP"},
        "documents": [
            {
                "documentType": "tenderNotice",
                "url": "https://www.contractsfinder.service.gov.uk/Notice/abc",
            },
            {
                "documentType": "technicalSpecifications",
                "description": "Specification",
                "format": "application/pdf",
                "url": "https://www.contractsfinder.service.gov.uk/Notice/Attachment/xyz",
            },
        ],
    },
}


def test_release_to_notice():
    notice = release_to_notice(SAMPLE_RELEASE)
    assert notice is not None
    assert notice.notice_code == "ocds-test-123"
    assert notice.package_price == 250000
    assert notice.currency == "GBP"
    assert notice.buyer == "Example Council"
    assert notice.attachments[0].file_name == "Specification.pdf"


def test_release_keyword_matching_requires_all_terms():
    assert release_matches(SAMPLE_RELEASE, "network firewall")
    assert not release_matches(SAMPLE_RELEASE, "network cisco")
