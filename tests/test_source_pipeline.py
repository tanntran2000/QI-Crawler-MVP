import asyncio
import json
from dataclasses import replace
from pathlib import Path

from sqlalchemy import func, select

from qi_crawler.authenticated_sources import egp_vietnam_source, extract_source_links
from qi_crawler.config import AppConfig
from qi_crawler.contracts_finder import release_to_notice
from qi_crawler.crawler import CrawlerService
from qi_crawler.models import Attachment, Notice
from qi_crawler.parser import ParsedNotice, parse_notice_html

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "golden" / "source"

GOLDENS = (
    (
        "tender_01.html",
        "web:egp-vietnam",
        "https://muasamcong.mpi.gov.vn/vi/web/guest/contractor-selection?notifyNo=IB2600123456",
        {
            "notice_code": "IB2600123456",
            "title": "Cung cấp cáp quang và thiết bị mạng",
            "buyer": "Công ty TNHH QI Technologies",
            "package_price": 1_234_567_890.0,
            "closing_at": "10:00 15/08/2026",
            "source_url": "https://muasamcong.mpi.gov.vn/vi/web/guest/contractor-selection?notifyNo=IB2600123456",
            "attachments": ["https://muasamcong.mpi.gov.vn/attachments/hsmt-cap-quang.pdf"],
        },
    ),
    (
        "tender_02.html",
        "web:egp-vietnam",
        "https://muasamcong.mpi.gov.vn/vi/web/guest/contractor-selection?notifyNo=IB2600123457",
        {
            "notice_code": "IB2600123457",
            "title": "Cung cấp máy tính xách tay",
            "buyer": "Trung tâm Công nghệ số",
            "package_price": 2_500_000_000.0,
            "closing_at": "09:30 16/08/2026",
            "source_url": "https://muasamcong.mpi.gov.vn/vi/web/guest/contractor-selection?notifyNo=IB2600123457",
            "attachments": ["https://muasamcong.mpi.gov.vn/attachments/hsmt-may-tinh.docx"],
        },
    ),
    (
        "tender_03.json",
        "contracts_finder",
        None,
        {
            "notice_code": "ocds-b5fd17-golden-03",
            "title": "Network security and router services",
            "buyer": "North Example Council",
            "package_price": 250_000.0,
            "closing_at": "2026-08-31T12:00:00Z",
            "source_url": "https://www.contractsfinder.service.gov.uk/Notice/golden-03",
            "attachments": [
                "https://www.contractsfinder.service.gov.uk/Notice/Attachment/golden-03-spec"
            ],
        },
    ),
    (
        "tender_04.json",
        "contracts_finder",
        None,
        {
            "notice_code": "ocds-b5fd17-golden-04",
            "title": "Laboratory switching equipment",
            "buyer": "West Example University",
            "package_price": 450_000.5,
            "closing_at": "2026-09-01T17:00:00Z",
            "source_url": "https://www.contractsfinder.service.gov.uk/Notice/golden-04",
            "attachments": [
                "https://www.contractsfinder.service.gov.uk/Notice/Attachment/golden-04-boq"
            ],
        },
    ),
    (
        "tender_05.json",
        "contracts_finder",
        None,
        {
            "notice_code": "ocds-b5fd17-golden-05",
            "title": "Medical data centre cabling",
            "buyer": "Central Example Hospital",
            "package_price": 125_000.0,
            "closing_at": "2026-09-03T12:00:00Z",
            "source_url": "https://www.contractsfinder.service.gov.uk/Notice/golden-05",
            "attachments": [
                "https://www.contractsfinder.service.gov.uk/Notice/Attachment/golden-05-spec",
                "https://www.contractsfinder.service.gov.uk/Notice/Attachment/golden-05-price",
            ],
        },
    ),
    (
        "tender_06.html",
        "web:egp-vietnam",
        "https://muasamcong.mpi.gov.vn/vi/web/guest/contractor-selection?notifyNo=IB2600123458",
        {
            "notice_code": "IB2600123458",
            "title": "Bảo trì hệ thống camera an ninh",
            "buyer": "Ban quản lý tòa nhà QI",
            "package_price": 750_000_000.0,
            "closing_at": "14:00 18/08/2026",
            "source_url": "https://muasamcong.mpi.gov.vn/vi/web/guest/contractor-selection?notifyNo=IB2600123458",
            "attachments": ["https://muasamcong.mpi.gov.vn/attachments/boq-camera.xlsx"],
        },
    ),
)


def _service(tmp_path: Path) -> CrawlerService:
    config = AppConfig()
    config.storage.database_url = f"sqlite:///{tmp_path / 'source-pipeline.db'}"
    return CrawlerService(config)


def _parsed_notice(filename: str, source_url: str | None) -> ParsedNotice:
    path = FIXTURE_DIR / filename
    if path.suffix == ".json":
        notice = release_to_notice(json.loads(path.read_text(encoding="utf-8")))
        assert notice is not None
        return notice
    assert source_url is not None
    return parse_notice_html(path.read_text(encoding="utf-8"), source_url)


def _assert_critical_fields(parsed: ParsedNotice, expected: dict[str, object]) -> None:
    assert parsed.notice_code == expected["notice_code"]
    assert parsed.title == expected["title"]
    assert parsed.buyer == expected["buyer"]
    assert parsed.package_price == expected["package_price"]
    assert parsed.closing_at == expected["closing_at"]
    assert parsed.source_url == expected["source_url"]
    assert [attachment.source_url for attachment in parsed.attachments] == expected["attachments"]


def test_six_golden_sources_parse_and_persist_without_duplicates(tmp_path: Path) -> None:
    service = _service(tmp_path)
    identities: dict[str, int] = {}
    try:
        for filename, source_kind, source_url, expected in GOLDENS:
            parsed = _parsed_notice(filename, source_url)
            _assert_critical_fields(parsed, expected)
            notice, created, _ = service.upsert_parsed_notice(parsed, source_kind=source_kind)
            assert created
            identities[str(expected["notice_code"])] = notice.id

        for filename, source_kind, source_url, expected in GOLDENS:
            notice, created, changed = service.upsert_parsed_notice(
                _parsed_notice(filename, source_url), source_kind=source_kind
            )
            assert not created
            assert not changed
            assert notice.id == identities[str(expected["notice_code"])]

        with service.db.session() as session:
            assert session.scalar(select(func.count()).select_from(Notice)) == 6
            assert session.scalar(select(func.count()).select_from(Attachment)) == 7
    finally:
        asyncio.run(service.close())


def test_source_pipeline_updates_existing_notice_in_place(tmp_path: Path) -> None:
    service = _service(tmp_path)
    filename, source_kind, source_url, _ = GOLDENS[2]
    try:
        original, created, _ = service.upsert_parsed_notice(
            _parsed_notice(filename, source_url), source_kind=source_kind
        )
        updated = replace(
            _parsed_notice(filename, source_url),
            title="Network security and router services - revised",
            package_price=255_000.0,
        )
        notice, created_again, changed = service.upsert_parsed_notice(
            updated, source_kind=source_kind
        )

        assert created
        assert not created_again
        assert changed
        assert notice.id == original.id
        assert notice.title == "Network security and router services - revised"
        with service.db.session() as session:
            assert session.scalar(select(func.count()).select_from(Notice)) == 1
    finally:
        asyncio.run(service.close())


def test_egp_source_profile_extracts_only_allowed_tender_links() -> None:
    source = egp_vietnam_source(
        list_url="https://muasamcong.mpi.gov.vn/vi/web/guest/contractor-selection"
    )
    links = extract_source_links(
        (FIXTURE_DIR / "egp_listing.html").read_text(encoding="utf-8"), source
    )

    assert links == [
        "https://muasamcong.mpi.gov.vn/vi/web/guest/contractor-selection?notifyNo=IB2600123456",
        "https://muasamcong.mpi.gov.vn/vi/web/guest/contractor-selection?step=tbmt&notifyNo=IB2600123457",
        "https://muasamcong.mpi.gov.vn/vi/web/guest/contractor-selection?notifyNo=IB2600123458",
    ]


def test_realistic_egp_snapshot_parses_nested_markup_and_html_entities() -> None:
    parsed = parse_notice_html(
        (FIXTURE_DIR / "egp_real_snapshot_01.html").read_text(encoding="utf-8"),
        "https://muasamcong.mpi.gov.vn/vi/web/guest/contractor-selection?notifyNo=IB2600888800",
    )

    assert parsed.notice_code == "IB2600888800"
    assert parsed.title == "Cung cấp switch & phụ kiện mạng"
    assert parsed.buyer == "Ban quản lý dự án QI"
    assert parsed.package_price == 3_200_000_000.0
    assert parsed.closing_at == "09:00 25/08/2026"
    assert [attachment.source_url for attachment in parsed.attachments] == [
        "https://muasamcong.mpi.gov.vn/documents/hsmt-switch.pdf?download=true"
    ]


def test_missing_critical_field_is_stored_for_human_review(tmp_path: Path) -> None:
    service = _service(tmp_path)
    parsed = parse_notice_html(
        (FIXTURE_DIR / "tender_missing_field.html").read_text(encoding="utf-8"),
        "https://muasamcong.mpi.gov.vn/vi/web/guest/contractor-selection?notifyNo=IB2600123499",
    )
    try:
        notice, created, _ = service.upsert_parsed_notice(parsed, source_kind="web:egp-vietnam")

        assert created
        assert notice.notice_code == "IB2600123499"
        assert notice.title == "Gói thử nghiệm thiếu giá"
        assert notice.package_price is None
        assert notice.data_quality_status == "INSUFFICIENT_DATA"
    finally:
        asyncio.run(service.close())
