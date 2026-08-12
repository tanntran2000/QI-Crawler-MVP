from __future__ import annotations

import json

from qi_crawler.db import Database
from qi_crawler.legacy_cleanup import archive_legacy_notices
from qi_crawler.models import Notice


def test_cleanup_archives_only_recognised_legacy_sources(tmp_path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'cleanup.db'}")
    database.require_current_schema()
    with database.session() as session:
        session.add_all(
            [
                Notice(
                    source_url="https://muasamcong.mpi.gov.vn/tender/IB26001",
                    url_hash="a" * 64,
                    source_name="egp",
                    title="EGP notice",
                ),
                Notice(
                    source_url="https://ebidding.coteccons.vn/Index/ChiTiet/2607301",
                    url_hash="b" * 64,
                    source_name="coteccons",
                    title="Coteccons notice",
                ),
                Notice(
                    source_url="https://contractsfinder.service.gov.uk/Notice/42",
                    url_hash="c" * 64,
                    source_name="contracts_finder",
                    title="Legacy UK notice",
                ),
                Notice(
                    source_url="https://example.com/tender/1",
                    url_hash="d" * 64,
                    source_name="test",
                    title="Test notice",
                ),
                Notice(
                    source_url="https://supplier.example/contest/1",
                    url_hash="e" * 64,
                    source_name="contest_vendor",
                    title="Valid source with test-like text",
                ),
            ]
        )

    result = archive_legacy_notices(database, archive_dir=tmp_path / "archive")

    assert result.archived_notices == 2
    assert result.archive_path is not None and result.archive_path.exists()
    payload = json.loads(result.archive_path.read_text(encoding="utf-8"))
    assert {item["notice"]["source_name"] for item in payload} == {"contracts_finder", "test"}
    with database.session() as session:
        assert [notice.source_name for notice in session.query(Notice).order_by(Notice.id)] == [
            "egp",
            "coteccons",
            "contest_vendor",
        ]


def test_cleanup_backfills_coteccons_detail_and_archives_only_homepage(tmp_path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'coteccons-cleanup.db'}")
    database.require_current_schema()
    with database.session() as session:
        session.add(
            Notice(
                source_url="https://ebidding.coteccons.vn/",
                url_hash="e" * 64,
                title="DU AN",
            )
        )
        session.add(
            Notice(
                source_url="https://ebidding.coteccons.vn/Index/ChiTiet/2607301",
                url_hash="f" * 64,
                title="Chi tiet 2607301",
            )
        )
        session.add(
            Notice(
                source_url="https://ebidding.coteccons.vn/Index/ChiTiet/2607999",
                url_hash="g" * 64,
                title="Chi tiet 2607999",
            )
        )
        session.add_all(
            Notice(
                source_url=f"https://ebidding.coteccons.vn/Index/ChiTiet/{notice_id}",
                url_hash=f"{notice_id:064d}",
                source_name="coteccons",
                source_notice_id=str(notice_id),
                title=f"Tender {notice_id}",
            )
            for notice_id in range(2607302, 2607307)
        )

    result = archive_legacy_notices(database, archive_dir=tmp_path / "archive")

    assert result.archived_notices == 1
    assert result.backfilled_coteccons == 2
    with database.session() as session:
        notices = session.query(Notice).order_by(Notice.id).all()
        assert len(notices) == 7
        repaired = next(item for item in notices if item.source_url.endswith("/2607301"))
        assert (repaired.source_name, repaired.source_notice_id) == ("coteccons", "2607301")
        generalized = next(item for item in notices if item.source_url.endswith("/2607999"))
        assert (generalized.source_name, generalized.source_notice_id) == ("coteccons", "2607999")
        assert {item.source_notice_id for item in notices} == {
            "2607301",
            "2607302",
            "2607303",
            "2607304",
            "2607305",
            "2607306",
            "2607999",
        }
