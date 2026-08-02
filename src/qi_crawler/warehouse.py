from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import duckdb

WAREHOUSE_PATH = Path("data/warehouse/qi_warehouse.duckdb")
BACKUP_DIR = Path("data/warehouse/backups")
VALID_DECISIONS = {"KEEP", "REVIEW", "QUARANTINE", "DROP_PROPOSED"}


@dataclass(frozen=True)
class WarehouseStatus:
    path: Path
    size_bytes: int
    schemas: tuple[str, ...]
    tables: tuple[str, ...]
    datasets: int
    pending_reviews: int


class WarehouseManager:
    """Manage the local analytical warehouse without deleting source data."""

    def __init__(self, path: Path | str = WAREHOUSE_PATH):
        self.path = Path(path)

    def _connect(self) -> duckdb.DuckDBPyConnection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        return duckdb.connect(str(self.path))

    def initialize(self) -> None:
        with self._connect() as connection:
            for schema in ("raw", "staging", "mart", "governance"):
                connection.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS governance.dataset_registry (
                    dataset_name VARCHAR PRIMARY KEY,
                    source_uri VARCHAR,
                    owner VARCHAR,
                    description VARCHAR,
                    contains_personal_data BOOLEAN NOT NULL DEFAULT FALSE,
                    retention_days INTEGER,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT current_timestamp
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS governance.retention_decisions (
                    decision_id BIGINT PRIMARY KEY,
                    dataset_name VARCHAR NOT NULL,
                    decision VARCHAR NOT NULL,
                    reason VARCHAR NOT NULL,
                    decided_by VARCHAR NOT NULL,
                    decided_at TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
                    approved_at TIMESTAMPTZ,
                    CHECK (decision IN ('KEEP', 'REVIEW', 'QUARANTINE', 'DROP_PROPOSED'))
                )
                """
            )
            connection.execute(
                """
                CREATE SEQUENCE IF NOT EXISTS governance.retention_decision_seq START 1
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS governance.load_audit (
                    load_id VARCHAR PRIMARY KEY,
                    dataset_name VARCHAR NOT NULL,
                    source_uri VARCHAR,
                    started_at TIMESTAMPTZ NOT NULL,
                    completed_at TIMESTAMPTZ,
                    status VARCHAR NOT NULL,
                    rows_read BIGINT NOT NULL DEFAULT 0,
                    rows_loaded BIGINT NOT NULL DEFAULT 0,
                    rows_rejected BIGINT NOT NULL DEFAULT 0,
                    source_hash VARCHAR,
                    message VARCHAR
                )
                """
            )

    def record_decision(
        self,
        dataset_name: str,
        decision: str,
        reason: str,
        decided_by: str = "codex-with-user-review",
    ) -> None:
        normalized = decision.strip().upper()
        if normalized not in VALID_DECISIONS:
            raise ValueError(f"Decision must be one of: {', '.join(sorted(VALID_DECISIONS))}")
        if not dataset_name.strip() or not reason.strip():
            raise ValueError("dataset_name and reason are required")
        self.initialize()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO governance.retention_decisions
                    (decision_id, dataset_name, decision, reason, decided_by)
                VALUES (nextval('governance.retention_decision_seq'), ?, ?, ?, ?)
                """,
                [dataset_name.strip(), normalized, reason.strip(), decided_by.strip()],
            )

    def status(self) -> WarehouseStatus:
        self.initialize()
        with self._connect() as connection:
            schemas = tuple(
                row[0]
                for row in connection.execute(
                    """
                    SELECT schema_name FROM information_schema.schemata
                    WHERE schema_name IN ('raw', 'staging', 'mart', 'governance')
                    ORDER BY schema_name
                    """
                ).fetchall()
            )
            tables = tuple(
                f"{row[0]}.{row[1]}"
                for row in connection.execute(
                    """
                    SELECT table_schema, table_name FROM information_schema.tables
                    WHERE table_schema IN ('raw', 'staging', 'mart', 'governance')
                    ORDER BY table_schema, table_name
                    """
                ).fetchall()
            )
            datasets = connection.execute(
                "SELECT count(*) FROM governance.dataset_registry"
            ).fetchone()[0]
            pending = connection.execute(
                """
                SELECT count(*) FROM governance.retention_decisions
                WHERE decision IN ('REVIEW', 'QUARANTINE', 'DROP_PROPOSED')
                  AND approved_at IS NULL
                """
            ).fetchone()[0]
            connection.execute("CHECKPOINT")
        return WarehouseStatus(
            path=self.path.resolve(),
            size_bytes=self.path.stat().st_size,
            schemas=schemas,
            tables=tables,
            datasets=datasets,
            pending_reviews=pending,
        )

    def backup(self, backup_dir: Path | str = BACKUP_DIR) -> Path:
        self.initialize()
        with self._connect() as connection:
            connection.execute("CHECKPOINT")
        destination_dir = Path(backup_dir)
        destination_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        destination = destination_dir / f"qi_warehouse_{timestamp}.duckdb"
        counter = 1
        while destination.exists():
            destination = destination_dir / f"qi_warehouse_{timestamp}_{counter}.duckdb"
            counter += 1
        shutil.copy2(self.path, destination)
        return destination.resolve()
