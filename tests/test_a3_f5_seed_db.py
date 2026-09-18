from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

from tools.release.a3_f5_seed_db import (
    START_REVISION,
    _canonicalize_physical_database,
    create_seed,
    logical_database_digest,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _create_index_order_fixture(path: Path, index_order: tuple[str, ...]) -> None:
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("CREATE TABLE alembic_version (version_num TEXT NOT NULL)")
        connection.execute("INSERT INTO alembic_version VALUES ('fixture-revision')")
        connection.execute(
            "CREATE TABLE sample (id INTEGER PRIMARY KEY, alpha TEXT, beta TEXT)"
        )
        connection.executemany(
            "INSERT INTO sample VALUES (?, ?, ?)",
            [(1, "a", "z"), (2, "b", "y"), (3, "c", "x")],
        )
        for column in index_order:
            connection.execute(f"CREATE INDEX index_{column} ON sample ({column})")
        connection.commit()


def test_canonicalization_normalizes_index_order_and_is_idempotent(
    tmp_path: Path,
) -> None:
    left = tmp_path / "left.db"
    right = tmp_path / "right.db"
    _create_index_order_fixture(left, ("alpha", "beta"))
    _create_index_order_fixture(right, ("beta", "alpha"))

    logical_before = logical_database_digest(left).sha256
    assert logical_database_digest(right).sha256 == logical_before

    _canonicalize_physical_database(left)
    _canonicalize_physical_database(right)

    assert logical_database_digest(left).sha256 == logical_before
    assert logical_database_digest(right).sha256 == logical_before
    assert _sha256(left) == _sha256(right)

    repeated = tmp_path / "repeated.db"
    shutil.copyfile(left, repeated)
    before_repeat = _sha256(repeated)
    _canonicalize_physical_database(repeated)

    assert logical_database_digest(repeated).sha256 == logical_before
    assert _sha256(repeated) == before_repeat


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
    for name in ("first", "second", "third", "fourth", "fifth", "sixth"):
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
    assert {result["revision"] for result in results} == {START_REVISION}
    assert {result["size_bytes"] for result in results} == {815104}
    if sys.platform == "win32":
        assert len({result["file_sha256"] for result in results}) == 1
    assert len({result["logical_digest"] for result in results}) == 1
    assert {result["business_row_count"] for result in results} == {0}


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
