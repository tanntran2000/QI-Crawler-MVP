"""Emit bounded, module-level pytest timing evidence for Windows CI triage.

This plugin is loaded only by the Windows required-gate workflow.  It does not
alter collection, execution order, test outcomes, or application behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any


@dataclass
class _GroupStats:
    setup_seconds: float = 0.0
    call_seconds: float = 0.0
    teardown_seconds: float = 0.0
    wall_seconds: float = 0.0
    completed: int = 0

    @property
    def phase_seconds(self) -> float:
        return self.setup_seconds + self.call_seconds + self.teardown_seconds

    @property
    def unattributed_seconds(self) -> float:
        return max(0.0, self.wall_seconds - self.phase_seconds)


class RuntimeAttribution:
    """Report completed module timings and the module active at interruption."""

    def __init__(self) -> None:
        self._session_started = 0.0
        self._session_started_set = False
        self._group_started = 0.0
        self._current_group: str | None = None
        self._groups: dict[str, _GroupStats] = {}

    def pytest_sessionstart(self) -> None:
        self._session_started = perf_counter()
        self._session_started_set = True
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
        if report.when not in {"setup", "call", "teardown"}:
            return
        group = report.nodeid.split("::", 1)[0]
        stats = self._groups.setdefault(group, _GroupStats())
        duration = max(0.0, float(report.duration))
        if report.when == "setup":
            stats.setup_seconds += duration
        elif report.when == "call":
            stats.call_seconds += duration
            stats.completed += 1
        else:
            stats.teardown_seconds += duration

    def pytest_sessionfinish(self, exitstatus: int) -> None:
        self._close_current_group()
        for group, stats in sorted(
            self._groups.items(), key=lambda item: (-item[1].wall_seconds, item[0])
        ):
            self._emit(
                "GROUP_TOTAL",
                group=group,
                setup_seconds=f"{stats.setup_seconds:.3f}",
                call_seconds=f"{stats.call_seconds:.3f}",
                teardown_seconds=f"{stats.teardown_seconds:.3f}",
                phase_seconds=f"{stats.phase_seconds:.3f}",
                wall_seconds=f"{stats.wall_seconds:.3f}",
                unattributed_seconds=f"{stats.unattributed_seconds:.3f}",
                completed=stats.completed,
            )
        session_wall = (
            max(0.0, perf_counter() - self._session_started) if self._session_started_set else 0.0
        )
        setup_seconds = sum(stats.setup_seconds for stats in self._groups.values())
        call_seconds = sum(stats.call_seconds for stats in self._groups.values())
        teardown_seconds = sum(stats.teardown_seconds for stats in self._groups.values())
        phase_seconds = setup_seconds + call_seconds + teardown_seconds
        self._emit(
            "SESSION_TOTAL",
            setup_seconds=f"{setup_seconds:.3f}",
            call_seconds=f"{call_seconds:.3f}",
            teardown_seconds=f"{teardown_seconds:.3f}",
            phase_seconds=f"{phase_seconds:.3f}",
            wall_seconds=f"{session_wall:.3f}",
            unattributed_seconds=f"{max(0.0, session_wall - phase_seconds):.3f}",
        )
        self._emit("SESSION_FINISH", exitstatus=exitstatus)

    def _close_current_group(self) -> None:
        if self._current_group is None:
            return
        stats = self._groups.setdefault(self._current_group, _GroupStats())
        stats.wall_seconds += max(0.0, perf_counter() - self._group_started)
        self._emit(
            "GROUP_END",
            group=self._current_group,
            setup_seconds=f"{stats.setup_seconds:.3f}",
            call_seconds=f"{stats.call_seconds:.3f}",
            teardown_seconds=f"{stats.teardown_seconds:.3f}",
            phase_seconds=f"{stats.phase_seconds:.3f}",
            wall_seconds=f"{stats.wall_seconds:.3f}",
            unattributed_seconds=f"{stats.unattributed_seconds:.3f}",
            completed=stats.completed,
        )
        self._current_group = None

    def _emit(self, event: str, **fields: object) -> None:
        elapsed = perf_counter() - self._session_started if self._session_started_set else 0.0
        details = " ".join(f"{name}={value}" for name, value in fields.items())
        print(f"CI_WINDOWS_RUNTIME {event} elapsed_seconds={elapsed:.3f} {details}".rstrip(), flush=True)


def pytest_configure(config: object) -> None:
    """Register the observer before pytest starts the test session."""
    if not hasattr(config, "_ci_windows_runtime_attribution"):
        attribution = RuntimeAttribution()
        config._ci_windows_runtime_attribution = attribution
        config.pluginmanager.register(attribution, "ci-windows-runtime-attribution")
