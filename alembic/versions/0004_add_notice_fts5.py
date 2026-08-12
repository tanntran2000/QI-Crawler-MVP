"""Add an optional SQLite FTS5 index for notice search.

Revision ID: 0004_add_notice_fts5
Revises: 0003_complete_core_schema
Create Date: 2026-08-12

FTS5 is optional because it depends on the SQLite build.  The revision is
recorded even when unavailable; runtime search then uses its safe fallback.
"""

from __future__ import annotations

import re
import unicodedata

import sqlalchemy as sa

from alembic import op

revision = "0004_add_notice_fts5"
down_revision = "0003_complete_core_schema"
branch_labels = None
depends_on = None


def _normalize(value: object) -> str:
    text = str(value or "").replace("đ", "d").replace("Đ", "D")
    text = "".join(
        character
        for character in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(character)
    )
    return re.sub(r"\s+", " ", text.casefold()).strip()


def _register_normalizer() -> None:
    connection = op.get_bind().connection
    connection.create_function("qi_normalize", 1, _normalize)


def _fts5_available() -> bool:
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        return False
    return bool(bind.scalar(sa.text("SELECT sqlite_compileoption_used('ENABLE_FTS5')")))


def _has_table(table_name: str) -> bool:
    return table_name in sa.inspect(op.get_bind()).get_table_names()


def _notice_values(notice_id: str) -> str:
    return f"""
        SELECT
            id,
            id,
            qi_normalize(title),
            qi_normalize(buyer),
            qi_normalize(package_description || ' ' || raw_text),
            qi_normalize(COALESCE((
                SELECT group_concat(
                    COALESCE(product_name, '') || ' ' || COALESCE(specification, ''), ' '
                )
                FROM tender_items
                WHERE tender_items.notice_id = notices.id
            ), ''))
        FROM notices
        WHERE id = {notice_id}
    """


def _rebuild_notice_fts(notice_id: str) -> None:
    op.execute(f"DELETE FROM notice_fts WHERE rowid = {notice_id}")
    op.execute(
        """
        INSERT INTO notice_fts (rowid, notice_id, title, buyer, description, items)
        """
        + _notice_values(notice_id)
    )


def upgrade() -> None:
    if not _fts5_available() or _has_table("notice_fts"):
        return
    _register_normalizer()
    op.execute(
        """
        CREATE VIRTUAL TABLE notice_fts USING fts5(
            notice_id UNINDEXED,
            title,
            buyer,
            description,
            items,
            tokenize = 'unicode61 remove_diacritics 2'
        )
        """
    )
    op.execute(
        """
        INSERT INTO notice_fts (rowid, notice_id, title, buyer, description, items)
        """
        + _notice_values("id")
    )
    op.execute(
        """
        CREATE TRIGGER notice_fts_after_insert
        AFTER INSERT ON notices BEGIN
            DELETE FROM notice_fts WHERE rowid = NEW.id;
            INSERT INTO notice_fts (rowid, notice_id, title, buyer, description, items)
            """
        + _notice_values("NEW.id")
        + "; END"
    )
    op.execute(
        """
        CREATE TRIGGER notice_fts_after_update
        AFTER UPDATE OF title, buyer, package_description, raw_text ON notices BEGIN
            DELETE FROM notice_fts WHERE rowid = NEW.id;
            INSERT INTO notice_fts (rowid, notice_id, title, buyer, description, items)
            """
        + _notice_values("NEW.id")
        + "; END"
    )
    op.execute(
        """
        CREATE TRIGGER notice_fts_after_delete
        AFTER DELETE ON notices BEGIN
            DELETE FROM notice_fts WHERE rowid = OLD.id;
        END
        """
    )
    op.execute(
        """
        CREATE TRIGGER notice_fts_item_after_insert
        AFTER INSERT ON tender_items BEGIN
            DELETE FROM notice_fts WHERE rowid = NEW.notice_id;
            INSERT INTO notice_fts (rowid, notice_id, title, buyer, description, items)
            """
        + _notice_values("NEW.notice_id")
        + "; END"
    )
    op.execute(
        """
        CREATE TRIGGER notice_fts_item_after_update
        AFTER UPDATE ON tender_items BEGIN
            DELETE FROM notice_fts WHERE rowid = OLD.notice_id;
            INSERT INTO notice_fts (rowid, notice_id, title, buyer, description, items)
            """
        + _notice_values("OLD.notice_id")
        + "; END"
    )
    op.execute(
        """
        CREATE TRIGGER notice_fts_item_after_delete
        AFTER DELETE ON tender_items BEGIN
            DELETE FROM notice_fts WHERE rowid = OLD.notice_id;
            INSERT INTO notice_fts (rowid, notice_id, title, buyer, description, items)
            """
        + _notice_values("OLD.notice_id")
        + "; END"
    )


def downgrade() -> None:
    if not _has_table("notice_fts"):
        return
    for trigger_name in (
        "notice_fts_item_after_delete",
        "notice_fts_item_after_update",
        "notice_fts_item_after_insert",
        "notice_fts_after_delete",
        "notice_fts_after_update",
        "notice_fts_after_insert",
    ):
        op.execute(f"DROP TRIGGER IF EXISTS {trigger_name}")
    op.execute("DROP TABLE notice_fts")
