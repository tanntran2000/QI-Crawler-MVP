"""Pytest evidence observer: preserve selection, outcomes and checkout identity.

This plugin never changes selection or turns failed tests into passing tests.
An explicit same-job collection baseline detects selection drift. Cross-commit
decreases still require review; a historical integer is not a universal floor.
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
from collections import Counter
from pathlib import Path

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--ci-evidence-dir")
    parser.addoption("--ci-collection-baseline")


def pytest_configure(config: pytest.Config) -> None:
    destination = config.getoption("--ci-evidence-dir")
    if destination:
        config.pluginmanager.register(Evidence(Path(destination), config), "ci-evidence-observer")


class Evidence:
    def __init__(self, directory: Path, config: pytest.Config) -> None:
        self.directory = directory
        self.config = config
        self.nodeids: list[str] = []
        self.outcomes: dict[str, str] = {}
        self.deselected = 0

    def write(self, filename: str, value: object) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        text = json.dumps(value, indent=2, sort_keys=True) + "\n"
        if len(text.encode("utf-8")) > 4 * 1024 * 1024:
            raise pytest.UsageError("CI_EVIDENCE_BUDGET_EXCEEDED")
        (self.directory / filename).write_text(text, encoding="utf-8")

    def pytest_deselected(self, items: list[pytest.Item]) -> None:
        self.deselected += len(items)

    def pytest_collection_finish(self, session: pytest.Session) -> None:
        self.nodeids = [item.nodeid for item in session.items]
        self.write("collection.json", {"nodeids": self.nodeids, "deselected": self.deselected})
        baseline = self.config.getoption("--ci-collection-baseline")
        if baseline:
            try:
                expected = json.loads(Path(baseline).read_text(encoding="utf-8"))["nodeids"]
            except (OSError, ValueError, KeyError) as error:
                raise pytest.UsageError("CI_COLLECTION_BASELINE_INVALID") from error
            if self.nodeids != expected or self.deselected:
                raise pytest.UsageError("CI_COLLECTION_MISMATCH: inspect baseline/run node IDs")

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        if report.failed:
            self.outcomes[report.nodeid] = "failed"
        elif report.skipped and self.outcomes.get(report.nodeid) != "failed":
            self.outcomes[report.nodeid] = "skipped"
        elif report.when == "call" and report.passed:
            self.outcomes.setdefault(report.nodeid, "passed")

    def pytest_sessionfinish(self, session: pytest.Session, exitstatus: int) -> None:
        try:
            checkout = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL,
            ).strip()
        except (OSError, subprocess.CalledProcessError):
            checkout = None
        self.write("result.json", {
            "checkout_sha": checkout, "github_sha": os.environ.get("GITHUB_SHA"),
            "source_head_sha": os.environ.get("CI_SOURCE_HEAD_SHA"),
            "run_id": os.environ.get("GITHUB_RUN_ID"),
            "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
            "python": platform.python_version(), "platform": platform.platform(),
            "collected": len(self.nodeids), "deselected": self.deselected,
            "outcomes": dict(Counter(self.outcomes.values())),
            "not_executed": len(set(self.nodeids) - self.outcomes.keys()),
            "collection_errors": session.testsfailed if self.config.option.collectonly else None,
            "exit_status": int(exitstatus),
        })
