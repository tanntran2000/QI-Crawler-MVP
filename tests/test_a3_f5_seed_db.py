from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

from tools.release.a3_f5_seed_db import (
    START_REVISION,
    create_seed,
    logical_database_digest,
)


def test_digest_cli_reports_existing_database_without_mutation(tmp_path: Path) -> None:
    database = tmp_path / "seed.db"
    result = create_seed(database)
    before = database.read_bytes()

    completed = subprocess.run(
        [sys.executable, "-m", "tools.release.a3_f5_seed_db", "--digest", str(database)],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload == {
        "algorithm": "qi-sqlite-logical-v1",
        "sha256": result.logical_digest,
        "revision": START_REVISION,
    }
    assert database.read_bytes() == before


def test_seed_generator_reproduces_physical_and_logical_0020_fixture(tmp_path: Path) -> None:
    results = []
    for name in ("first", "second"):
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "tools.release.a3_f5_seed_db",
                "--output",
                str(tmp_path / name / "egp.db"),
            ],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        results.append(json.loads(completed.stdout))
    first, second = results

    assert first["revision"] == second["revision"] == START_REVISION
    assert first["size_bytes"] == second["size_bytes"] == 815104
    assert first["file_sha256"] == second["file_sha256"]
    assert first["logical_digest"] == second["logical_digest"]
    assert first["business_row_count"] == second["business_row_count"] == 0


def test_logical_digest_is_row_order_independent_and_type_preserving(tmp_path: Path) -> None:
    left = tmp_path / "left.db"
    right = tmp_path / "right.db"
    changed_type = tmp_path / "changed-type.db"
    for path, rows in (
        (left, [(1, "alpha"), (2, "beta")]),
        (right, [(2, "beta"), (1, "alpha")]),
        (changed_type, [(1, "alpha"), ("2", "beta")]),
    ):
        with sqlite3.connect(path) as connection:
            connection.execute("CREATE TABLE alembic_version (version_num TEXT NOT NULL)")
            connection.execute("INSERT INTO alembic_version VALUES ('fixture-revision')")
            connection.execute("CREATE TABLE sample (value, label TEXT NOT NULL)")
            connection.executemany("INSERT INTO sample VALUES (?, ?)", rows)

    assert logical_database_digest(left).sha256 == logical_database_digest(right).sha256
    assert logical_database_digest(left).sha256 != logical_database_digest(changed_type).sha256


def test_seed_generator_refuses_existing_output(tmp_path: Path) -> None:
    output = tmp_path / "egp.db"
    output.write_bytes(b"do-not-overwrite")

    with pytest.raises(FileExistsError):
        create_seed(output)

    assert output.read_bytes() == b"do-not-overwrite"


def test_seed_metadata_is_self_describing(tmp_path: Path) -> None:
    result = create_seed(tmp_path / "seed" / "egp.db")
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert metadata["schema"] == "A3-F5-SYNTHETIC-SEED-V1"
    assert metadata["target_revision"] == START_REVISION
    assert metadata["business_data_required"] is False
    assert metadata["synthetic_rows"] == []
    assert metadata["file_sha256"] == result.file_sha256
    assert metadata["logical_digest"] == result.logical_digest
