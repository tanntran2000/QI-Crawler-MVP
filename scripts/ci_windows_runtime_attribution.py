"""Emit bounded, module-level pytest timing evidence for Windows CI triage.

This plugin is loaded only by the Windows required-gate workflow.  It does not
alter collection, execution order, test outcomes, or application behavior.
"""

from __future__ import annotations

from collections import defaultdict
from time import perf_counter
from typing import Any


class RuntimeAttribution:
    """Report completed module timings and the module active at interruption."""

    def __init__(self) -> None:
        self._session_started = 0.0
        self._group_started = 0.0
        self._current_group: str | None = None
        self._call_seconds: dict[str, float] = defaultdict(float)
        self._completed: dict[str, int] = defaultdict(int)

    def pytest_sessionstart(self) -> None:
        self._session_started = perf_counter()
        self._emit("SESSION_START")

    def pytest_runtest_logstart(self, nodeid: str, location: tuple[str, int, str]) -> None:
        del location
        group = nodeid.split("::", 1)[0]
        if group == self._current_group:
            return
        self._close_current_group()
        self._current_group = group
        self._group_started = perf_counter()
        self._emit("GROUP_START", group=group)

    def pytest_runtest_logreport(self, report: Any) -> None:
        if report.when != "call":
            return
        group = report.nodeid.split("::", 1)[0]
        self._call_seconds[group] += report.duration
        self._completed[group] += 1

    def pytest_sessionfinish(self, exitstatus: int) -> None:
        self._close_current_group()
        for group in sorted(self._completed, key=self._call_seconds.get, reverse=True):
            self._emit(
                "GROUP_TOTAL",
                group=group,
                call_seconds=f"{self._call_seconds[group]:.3f}",
                completed=self._completed[group],
            )
        self._emit("SESSION_FINISH", exitstatus=exitstatus)

    def _close_current_group(self) -> None:
        if self._current_group is None:
            return
        self._emit(
            "GROUP_END",
            group=self._current_group,
            wall_seconds=f"{perf_counter() - self._group_started:.3f}",
            call_seconds=f"{self._call_seconds[self._current_group]:.3f}",
            completed=self._completed[self._current_group],
        )
        self._current_group = None

    def _emit(self, event: str, **fields: object) -> None:
        elapsed = perf_counter() - self._session_started if self._session_started else 0.0
        details = " ".join(f"{name}={value}" for name, value in fields.items())
        print(f"CI_WINDOWS_RUNTIME {event} elapsed_seconds={elapsed:.3f} {details}".rstrip(), flush=True)


def pytest_configure(config: object) -> None:
    """Register the observer before pytest starts the test session."""
    if not hasattr(config, "_ci_windows_runtime_attribution"):
        attribution = RuntimeAttribution()
        config._ci_windows_runtime_attribution = attribution
        config.pluginmanager.register(attribution, "ci-windows-runtime-attribution")
