from __future__ import annotations

from qi_crawler.config import AppConfig
from qi_crawler.db import Database
from qi_crawler.export.tbmt_excel import export_tbmt
from qi_crawler.models import Notice
from qi_crawler.notice_search import search_notices
from qi_crawler.source_filter import active_source_domains, active_source_names


def _config() -> AppConfig:
    return AppConfig.model_validate(
        {
            "sources": {
                "egp": {
                    "enabled": True,
                    "priority": 1,
                    "domain": "muasamcong.mpi.gov.vn",
                    "adapter": "egp",
                },
                "coteccons": {
                    "enabled": False,
                    "priority": 2,
                    "domain": "ebidding.coteccons.vn",
                    "adapter": "coteccons",
                },
            }
        }
    )


def _database(tmp_path) -> Database:
    database = Database(f"sqlite:///{tmp_path / 'active-sources.db'}")
    database.require_current_schema()
    with database.session() as session:
        session.add_all(
            [
                Notice(
                    source_url="https://muasamcong.mpi.gov.vn/tender/IB26001",
                    url_hash="a" * 64,
                    source_name="egp",
                    source_notice_id="IB26001",
                    title="Cung cap chong tham EGP",
                    buyer="EGP buyer",
                ),
                Notice(
                    source_url="https://ebidding.coteccons.vn/Index/ChiTiet/2607301",
                    url_hash="b" * 64,
                    source_name="coteccons",
                    source_notice_id="2607301",
                    title="Cung cap chong tham Coteccons",
                    buyer="Coteccons buyer",
                ),
                Notice(
                    source_url="https://example.com/tender/1",
                    url_hash="c" * 64,
                    source_name="test",
                    source_notice_id="test-1",
                    title="Cung cap chong tham test",
                    buyer="Test buyer",
                ),
                Notice(
                    source_url="https://external.example/redirect?next=https://muasamcong.mpi.gov.vn",
                    url_hash="d" * 64,
                    title="Cung cap chong tham external URL",
                    buyer="External buyer",
                ),
                Notice(
                    source_url="https://muasamcong.mpi.gov.vn/tender/not-a-real-egp-source",
                    url_hash="e" * 64,
                    source_name="test",
                    title="Cung cap chong tham disabled test source",
                    buyer="Test buyer",
                ),
            ]
        )
    return database


def test_disabled_and_legacy_sources_are_hidden_from_search(tmp_path) -> None:
    config = _config()
    database = _database(tmp_path)

    result = search_notices(
        database,
        ("chong tham",),
        None,
        20,
        tuple(active_source_names(config)),
        active_source_domains(config),
    )

    assert [notice.source_name for notice in result.notices] == ["egp"]
    assert all(notice.source_name != "test" for notice in result.notices)


def test_all_sources_disabled_returns_no_search_results(tmp_path) -> None:
    config = _config()
    config.sources["egp"].enabled = False
    database = _database(tmp_path)

    result = search_notices(
        database,
        ("chong tham",),
        None,
        20,
        tuple(active_source_names(config)),
        active_source_domains(config),
    )

    assert result.notices == []


def test_disabled_and_legacy_sources_are_hidden_from_tbmt_export(tmp_path) -> None:
    config = _config()
    database = _database(tmp_path)

    result = export_tbmt(
        database,
        output=tmp_path / "active.xlsx",
        rejects_dir=tmp_path / "rejects",
        active_source_names=tuple(active_source_names(config)),
        active_source_domains=active_source_domains(config),
    )

    assert result.total_records == 1
    assert result.exported_records == 1
