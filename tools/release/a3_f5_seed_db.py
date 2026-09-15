"""Build a deterministic, non-production schema-0020 database for A3 F5 tests."""

from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.metadata
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from contextlib import closing
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from alembic.config import Config
from alembic.script import ScriptDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[2]
START_REVISION = "0020_add_tender_operational_revision_events"
DIGEST_ALGORITHM = "qi-sqlite-logical-v1"
SEED_SCHEMA = "A3-F5-SYNTHETIC-SEED-V1"


@dataclass(frozen=True)
class LogicalDigest:
    algorithm: str
    sha256: str
    manifest: dict[str, Any]


@dataclass(frozen=True)
class SeedResult:
    database_path: Path
    metadata_path: Path
    revision: str
    size_bytes: int
    file_sha256: str
    logical_digest: str
    business_row_count: int


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _typed(value: Any) -> list[Any]:
    if value is None:
        return ["null", None]
    if isinstance(value, int):
        return ["integer", str(value)]
    if isinstance(value, float):
        return ["real", value.hex()]
    if isinstance(value, bytes):
        return ["blob", base64.b64encode(value).decode("ascii")]
    return ["text", str(value)]


def _quoted(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def logical_database_digest(database_path: Path) -> LogicalDigest:
    """Hash schema and rows without depending on SQLite physical page order."""

    uri = f"file:{Path(database_path).resolve().as_posix()}?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as connection:
        connection.row_factory = sqlite3.Row
        schema_rows = connection.execute(
            "SELECT type, name, tbl_name, sql FROM sqlite_master "
            "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
        ).fetchall()
        schema = [
            {
                "type": row["type"],
                "name": row["name"],
                "table": row["tbl_name"],
                "sql": row["sql"],
            }
            for row in schema_rows
        ]
        table_names = sorted(
            row["name"] for row in schema_rows if row["type"] == "table"
        )
        tables: list[dict[str, Any]] = []
        for table_name in table_names:
            columns = [
                {
                    "cid": row[0],
                    "name": row[1],
                    "declared_type": row[2],
                    "not_null": row[3],
                    "default": row[4],
                    "primary_key_position": row[5],
                    "hidden": row[6],
                }
                for row in connection.execute(
                    f"PRAGMA table_xinfo({_quoted(table_name)})"
                ).fetchall()
            ]
            visible_columns = [column["name"] for column in columns if column["hidden"] == 0]
            select_list = ", ".join(_quoted(name) for name in visible_columns)
            row_digests: list[str] = []
            if select_list:
                for row in connection.execute(
                    f"SELECT {select_list} FROM {_quoted(table_name)}"
                ).fetchall():
                    encoded = [_typed(value) for value in row]
                    row_digests.append(hashlib.sha256(_canonical_json(encoded)).hexdigest())
            tables.append(
                {
                    "name": table_name,
                    "columns": columns,
                    "row_count": len(row_digests),
                    "row_digests": sorted(row_digests),
                }
            )
        revision_row = connection.execute(
            "SELECT version_num FROM alembic_version ORDER BY version_num LIMIT 1"
        ).fetchone()
    manifest = {
        "algorithm": DIGEST_ALGORITHM,
        "alembic_revision": revision_row[0] if revision_row else None,
        "schema": schema,
        "tables": tables,
    }
    return LogicalDigest(
        algorithm=DIGEST_ALGORITHM,
        sha256=hashlib.sha256(_canonical_json(manifest)).hexdigest(),
        manifest=manifest,
    )


def _migration_identity(config: Config) -> list[dict[str, Any]]:
    scripts = ScriptDirectory.from_config(config)
    revisions = list(reversed(list(scripts.iterate_revisions(START_REVISION, "base"))))
    return [
        {
            "revision": revision.revision,
            "down_revision": revision.down_revision,
            "relative_path": Path(revision.path).resolve().relative_to(PROJECT_ROOT).as_posix(),
            "sha256": _sha256(Path(revision.path)),
        }
        for revision in revisions
    ]


def _canonicalize_physical_database(database_path: Path) -> None:
    """Replay SQLite's deterministic logical dump to stabilize page allocation."""

    canonical = database_path.with_name(database_path.name + ".canonical.tmp")
    if canonical.exists():
        raise FileExistsError(f"refusing to overwrite canonicalization target: {canonical}")
    with closing(sqlite3.connect(database_path)) as source:
        dump = "\n".join(source.iterdump()) + "\n"
    try:
        with closing(sqlite3.connect(canonical)) as destination:
            destination.executescript(dump)
            destination.commit()
        canonical.replace(database_path)
    except Exception:
        canonical.unlink(missing_ok=True)
        raise


def _create_seed_in_process(database_path: Path) -> SeedResult:
    output = Path(database_path).resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite seed output: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    work = PROJECT_ROOT / ".tmp" / "a3_f5_seed_canonical_work" / "egp.db"
    if work.exists():
        raise FileExistsError(f"canonical seed work path is already in use: {work}")
    work.parent.mkdir(parents=True, exist_ok=True)
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(PROJECT_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{work.as_posix()}")
    migrations = _migration_identity(config)
    migration_environment = os.environ.copy()
    migration_environment["QI_CRAWLER_ALEMBIC_URL"] = f"sqlite:///{work.as_posix()}"
    migration_environment["PYTHONHASHSEED"] = "0"
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", START_REVISION],
        cwd=PROJECT_ROOT,
        env=migration_environment,
        check=True,
        capture_output=True,
        text=True,
    )
    try:
        subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--canonicalize", str(work)],
            cwd=PROJECT_ROOT,
            env=os.environ | {"PYTHONHASHSEED": "0"},
            check=True,
            capture_output=True,
            text=True,
        )
        logical = logical_database_digest(work)
        shutil.copyfile(work, output)
    finally:
        work.unlink(missing_ok=True)
    business_row_count = sum(
        table["row_count"]
        for table in logical.manifest["tables"]
        if table["name"] != "alembic_version"
        and not table["name"].startswith("notice_fts")
    )
    metadata_path = output.with_name(output.name + ".seed-metadata.json")
    metadata = {
        "schema": SEED_SCHEMA,
        "target_revision": START_REVISION,
        "migration_source": migrations,
        "migration_order": [entry["revision"] for entry in migrations],
        "synthetic_rows": [],
        "business_data_required": False,
        "python_version": sys.version.split()[0],
        "sqlite_version": sqlite3.sqlite_version,
        "alembic_version": importlib.metadata.version("alembic"),
        "sqlalchemy_version": importlib.metadata.version("sqlalchemy"),
        "file_size_bytes": output.stat().st_size,
        "file_sha256": _sha256(output),
        "logical_digest_algorithm": logical.algorithm,
        "logical_digest": logical.sha256,
        "business_row_count": business_row_count,
        "expected_tables": sorted(table["name"] for table in logical.manifest["tables"]),
    }
    metadata_path.write_bytes(json.dumps(metadata, indent=2, sort_keys=True).encode("utf-8") + b"\n")
    return SeedResult(
        database_path=output,
        metadata_path=metadata_path,
        revision=START_REVISION,
        size_bytes=output.stat().st_size,
        file_sha256=_sha256(output),
        logical_digest=logical.sha256,
        business_row_count=business_row_count,
    )


def create_seed(database_path: Path) -> SeedResult:
    """Create one seed in a fresh interpreter so physical SQLite state is stable."""

    output = Path(database_path).resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite seed output: {output}")
    completed = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--create-worker", str(output)],
        cwd=PROJECT_ROOT,
        env=os.environ | {"PYTHONHASHSEED": "0"},
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    return SeedResult(
        database_path=Path(payload["database_path"]),
        metadata_path=Path(payload["metadata_path"]),
        revision=payload["revision"],
        size_bytes=int(payload["size_bytes"]),
        file_sha256=payload["file_sha256"],
        logical_digest=payload["logical_digest"],
        business_row_count=int(payload["business_row_count"]),
    )


def _cli() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--output", type=Path)
    action.add_argument("--digest", type=Path)
    action.add_argument("--canonicalize", type=Path, help=argparse.SUPPRESS)
    action.add_argument("--create-worker", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.canonicalize:
        _canonicalize_physical_database(args.canonicalize)
        return 0
    if args.create_worker:
        result = _create_seed_in_process(args.create_worker)
        payload = asdict(result)
        payload["database_path"] = str(result.database_path)
        payload["metadata_path"] = str(result.metadata_path)
        print(json.dumps(payload, sort_keys=True))
        return 0
    if args.digest:
        digest = logical_database_digest(args.digest)
        print(json.dumps({
            "algorithm": digest.algorithm,
            "sha256": digest.sha256,
            "revision": digest.manifest["alembic_revision"],
        }, sort_keys=True))
        return 0
    result = create_seed(args.output)
    payload = asdict(result)
    payload["database_path"] = str(result.database_path)
    payload["metadata_path"] = str(result.metadata_path)
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
