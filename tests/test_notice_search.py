from __future__ import annotations

from qi_crawler.db import Database
from qi_crawler.migrations import upgrade_database
from qi_crawler.models import Notice, TenderItem
from qi_crawler.notice_search import search_notices


def _database(tmp_path) -> Database:
    database_path = tmp_path / "search.db"
    database_url = f"sqlite:///{database_path}"
    upgrade_database(database_url, backup_dir=tmp_path / "backups")
    database = Database(database_url)
    database.require_current_schema()
    with database.session() as session:
        notice = Notice(
            source_url="https://example.test/chong-tham",
            url_hash="f" * 64,
            source_name="coteccons",
            source_notice_id="2607301",
            title="Gói thầu thi công chống thấm điện nước",
            buyer="Coteccons",
            package_description="Thi công chống thấm cho công trình.",
        )
        session.add(notice)
        session.flush()
        session.add(
            TenderItem(
                notice_id=notice.id,
                item_code="ITEM-1",
                product_name="Vật tư chống thấm",
                specification="Chống thấm mái",
            )
        )
    return database


def test_fts5_search_matches_accented_and_unaccented_vietnamese(tmp_path, monkeypatch) -> None:
    database = _database(tmp_path)
    if not database.fts5_available():
        return

    def fallback_must_not_run(*_args, **_kwargs):
        raise AssertionError("FTS5 search must not load all notices through fallback")

    monkeypatch.setattr("qi_crawler.notice_search._fallback_search", fallback_must_not_run)
    accented = search_notices(database, ("chống thấm",), None, 20)
    unaccented = search_notices(database, ("chong tham",), None, 20)
    assert accented.used_fts5 is True
    assert unaccented.used_fts5 is True
    assert [notice.id for notice in accented.notices] == [notice.id for notice in unaccented.notices]
    assert accented.notices[0].title == "Gói thầu thi công chống thấm điện nước"


def test_search_uses_portable_fallback_when_fts5_is_unavailable(tmp_path, monkeypatch) -> None:
    database = _database(tmp_path)
    monkeypatch.setattr(database, "fts5_available", lambda: False)

    result = search_notices(database, ("chong tham",), None, 20)

    assert result.used_fts5 is False
    assert [notice.title for notice in result.notices] == ["Gói thầu thi công chống thấm điện nước"]


def test_fts5_triggers_follow_notice_and_item_changes(tmp_path) -> None:
    database = _database(tmp_path)
    if not database.fts5_available():
        return

    with database.session() as session:
        notice = session.query(Notice).one()
        notice.title = "Gói thầu chống cháy"
        notice.package_description = "Thi công chống cháy cho công trình."
        item = session.query(TenderItem).one()
        item.product_name = "Vật tư chống cháy"
        item.specification = "Chống cháy mái"

    assert not search_notices(database, ("chong tham",), None, 20).notices
    changed = search_notices(database, ("chong chay",), None, 20)
    assert [notice.title for notice in changed.notices] == ["Gói thầu chống cháy"]

    with database.session() as session:
        notice = session.query(Notice).one()
        session.add(
            TenderItem(
                notice_id=notice.id,
                item_code="ITEM-2",
                product_name="Thiết bị báo cháy",
            )
        )
    assert search_notices(database, ("bao chay",), None, 20).notices

    with database.session() as session:
        session.delete(session.query(Notice).one())
    assert not search_notices(database, ("chong chay",), None, 20).notices
