"""Emit bounded Windows-hosted environment timing evidence for CI triage.

This helper is invoked only by the Windows required CI job before pytest.  It
does not set thresholds, alter test execution, or make pass/fail decisions.
"""

from __future__ import annotations

import os
import platform
import sqlite3
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from time import perf_counter


def _safe_value(value: object) -> str:
    """Keep one-line CI output readable without exposing arbitrary text."""
    return str(value).replace("\r", " ").replace("\n", " ")[:160]


def _emit(phase: str, elapsed_seconds: float, **fields: object) -> None:
    details = " ".join(f"{name}={_safe_value(value)}" for name, value in fields.items())
    print(
        f"CI_WINDOWS_DIAG phase={phase} elapsed_seconds={elapsed_seconds:.3f} {details}".rstrip(),
        flush=True,
    )


def _probe(phase: str, operation: Callable[[], dict[str, object]]) -> None:
    started = perf_counter()
    try:
        fields = operation()
    except Exception as exc:  # noqa: BLE001 - record any probe failure, then run pytest.
        _emit(
            phase,
            perf_counter() - started,
            status="ERROR",
            exception_type=type(exc).__name__,
            message=_safe_value(exc),
        )
        return
    _emit(phase, perf_counter() - started, status="OK", **fields)


def _environment() -> dict[str, object]:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_count": os.cpu_count() or "unknown",
        "temp_drive": Path(tempfile.gettempdir()).drive or "unknown",
    }


def _cpu() -> dict[str, object]:
    checksum = 0
    for value in range(2_000_000):
        checksum = (checksum + value * value) % 1_000_003
    return {"iterations": 2_000_000, "checksum": checksum}


def _filesystem() -> dict[str, object]:
    payload = b"QI-Crawler-Windows-CI\n" * 16_384
    with tempfile.TemporaryDirectory(prefix="qi-crawler-ci-") as directory:
        path = Path(directory) / "probe.bin"
        path.write_bytes(payload)
        observed = path.read_bytes()
        if observed != payload:
            raise RuntimeError("filesystem probe read-back mismatch")
    return {"bytes": len(payload), "operations": "create_write_read_delete"}


def _sqlite() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="qi-crawler-ci-") as directory:
        path = Path(directory) / "probe.sqlite"
        connection = sqlite3.connect(path)
        try:
            connection.execute("CREATE TABLE probe (id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
            connection.executemany(
                "INSERT INTO probe (value) VALUES (?)",
                [(f"row-{index}",) for index in range(250)],
            )
            connection.commit()
            count = connection.execute("SELECT COUNT(*) FROM probe").fetchone()[0]
        finally:
            connection.close()
    if count != 250:
        raise RuntimeError(f"sqlite probe row count mismatch: {count}")
    return {"rows": count, "operations": "create_write_read_close"}


def _process() -> dict[str, object]:
    subprocess.run(
        [sys.executable, "-c", "pass"],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=10,
    )
    return {"command": "python_-c_pass", "timeout_seconds": 10}


def _qt() -> dict[str, object]:
    from PySide6.QtCore import qVersion
    from PySide6.QtWidgets import QApplication

    application = QApplication.instance() or QApplication([])
    return {"qt_version": qVersion(), "application_created": bool(application)}


def main() -> None:
    """Run small independent probes; diagnostics never set a performance gate."""
    _probe("ENV", _environment)
    _probe("CPU", _cpu)
    _probe("FILESYSTEM", _filesystem)
    _probe("SQLITE", _sqlite)
    _probe("PROCESS", _process)
    _probe("QT", _qt)


if __name__ == "__main__":
    main()
