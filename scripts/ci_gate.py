"""Fail closed unless every declared required CI job succeeded."""

from __future__ import annotations

import json
import os
import sys

REQUIRED_JOBS = (
    "code-quality", "tests-ubuntu-312", "tests-windows-312", "compatibility-ubuntu-311",
)


def main() -> int:
    try:
        needs = json.loads(sys.argv[1] if len(sys.argv) == 2 else os.environ["CI_NEEDS"])
    except (ValueError, KeyError):
        needs = None
    failures = [
        job for job in REQUIRED_JOBS
        if not isinstance(needs, dict)
        or not isinstance(needs.get(job), dict)
        or needs[job].get("result") != "success"
    ]
    print("CI_GATE=FAIL: " + ", ".join(failures) if failures else "CI_GATE=PASS")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
