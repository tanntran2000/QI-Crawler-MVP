import asyncio
from dataclasses import replace
from pathlib import Path

from sqlalchemy import func, select

from qi_crawler.authenticated_sources import egp_vietnam_source, extract_source_links
from qi_crawler.config import AppConfig, SourceConfig
from qi_crawler.crawler import CrawlerService
from qi_crawler.models import Attachment, Notice
from qi_crawler.parser import ParsedNotice, parse_notice_html
from qi_crawler.source_adapters import CotecconsAdapter

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "golden" / "source"
COTECCONS_SOURCE = SourceConfig(
    domain="ebidding.coteccons.vn", adapter="coteccons", priority=2
)

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
    (
        "coteccons_2607301.html",
        "web:coteccons",
        "https://ebidding.coteccons.vn/Index/ChiTiet/2607301",
        {
            "notice_code": "2607301",
            "title": "GÓI THẦU: THI CÔNG CHỐNG THẤM",
            "buyer": "Công ty Cổ phần Xây dựng Coteccons",
            "package_price": None,
            "closing_at": "08:30 14/08/2026",
            "source_url": "https://ebidding.coteccons.vn/Index/ChiTiet/2607301",
            "attachments": ["https://ebidding.coteccons.vn/documents/2607301-hsmt.pdf"],
        },
    ),
    (
        "coteccons_2607302.html",
        "web:coteccons",
        "https://ebidding.coteccons.vn/Index/ChiTiet/2607302",
        {
            "notice_code": "2607302",
            "title": "GÓI THẦU: CUNG CẤP VẬT TƯ CƠ ĐIỆN",
            "buyer": "Công ty Cổ phần Xây dựng Coteccons",
            "package_price": None,
            "closing_at": "16:45 16/08/2026",
            "source_url": "https://ebidding.coteccons.vn/Index/ChiTiet/2607302",
            "attachments": [],
        },
    ),
)


def _service(tmp_path: Path) -> CrawlerService:
    config = AppConfig()
    config.storage.database_url = f"sqlite:///{tmp_path / 'source-pipeline.db'}"
    return CrawlerService(config)


def _parsed_notice(filename: str, source_url: str | None) -> ParsedNotice:
    path = FIXTURE_DIR / filename
    assert source_url is not None
    return parse_notice_html(path.read_text(encoding="utf-8"), source_url)


def _assert_critical_fields(parsed: ParsedNotice, expected: dict[str, object]) -> None:
    assert (parsed.notice_code or parsed.source_notice_id) == expected["notice_code"]
    assert parsed.title == expected["title"]
    assert parsed.buyer == expected["buyer"]
    assert parsed.package_price == expected["package_price"]
    assert parsed.closing_at == expected["closing_at"]
    assert parsed.source_url == expected["source_url"]
    assert [attachment.source_url for attachment in parsed.attachments] == expected["attachments"]


def test_five_golden_sources_parse_and_persist_without_duplicates(tmp_path: Path) -> None:
    service = _service(tmp_path)
    identities: dict[str, int] = {}
    try:
        for filename, source_kind, source_url, expected in GOLDENS:
            parsed = _parsed_notice(filename, source_url)
            if "coteccons" in source_kind:
                adapter = CotecconsAdapter("coteccons", COTECCONS_SOURCE)
                parsed = adapter.parse_detail(
                    (FIXTURE_DIR / filename).read_text(encoding="utf-8"), source_url
                )
            _assert_critical_fields(parsed, expected)
            notice, created, _ = service.upsert_parsed_notice(parsed, source_kind=source_kind)
            assert created
            identities[str(expected["notice_code"])] = notice.id

        for filename, source_kind, source_url, expected in GOLDENS:
            parsed = _parsed_notice(filename, source_url)
            if "coteccons" in source_kind:
                adapter = CotecconsAdapter("coteccons", COTECCONS_SOURCE)
                parsed = adapter.parse_detail(
                    (FIXTURE_DIR / filename).read_text(encoding="utf-8"), source_url
                )
            notice, created, changed = service.upsert_parsed_notice(parsed, source_kind=source_kind)
            assert not created
            assert not changed
            assert notice.id == identities[str(expected["notice_code"])]

        with service.db.session() as session:
            assert session.scalar(select(func.count()).select_from(Notice)) == 5
            assert session.scalar(select(func.count()).select_from(Attachment)) == 4
    finally:
        asyncio.run(service.close())


def test_source_pipeline_updates_existing_notice_in_place(tmp_path: Path) -> None:
    service = _service(tmp_path)
    filename, source_kind, source_url, _ = GOLDENS[0]
    try:
        original, created, _ = service.upsert_parsed_notice(
            _parsed_notice(filename, source_url), source_kind=source_kind
        )
        updated = replace(
            _parsed_notice(filename, source_url),
            title="Cung cap cap quang va thiet bi mang - revised",
            package_price=1_255_000_000.0,
        )
        notice, created_again, changed = service.upsert_parsed_notice(
            updated, source_kind=source_kind
        )

        assert created
        assert not created_again
        assert changed
        assert notice.id == original.id
        assert notice.title == "Cung cap cap quang va thiet bi mang - revised"
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
