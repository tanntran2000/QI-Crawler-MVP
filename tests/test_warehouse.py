from pathlib import Path

import pytest

from qi_crawler.warehouse import WarehouseManager


def test_initialize_status_and_backup(tmp_path: Path) -> None:
    warehouse_path = tmp_path / "warehouse.duckdb"
    manager = WarehouseManager(warehouse_path)

    manager.initialize()
    manager.record_decision("sample", "review", "Schema has not been confirmed")
    status = manager.status()
    backup = manager.backup(tmp_path / "backups")

    assert status.path == warehouse_path.resolve()
    assert status.schemas == ("governance", "mart", "raw", "staging")
    assert "governance.dataset_registry" in status.tables
    assert "governance.load_audit" in status.tables
    assert status.pending_reviews == 1
    assert backup.exists()
    assert backup.stat().st_size > 0


def test_record_decision_rejects_unsafe_value(tmp_path: Path) -> None:
    manager = WarehouseManager(tmp_path / "warehouse.duckdb")

    with pytest.raises(ValueError, match="Decision must be one of"):
        manager.record_decision("sample", "DELETE", "No longer useful")
