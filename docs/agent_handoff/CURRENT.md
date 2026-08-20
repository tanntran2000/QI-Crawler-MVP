# QI-Crawler Agent Handoff

## Task

CI-H2E — Windows Required-Gate Runtime Attribution

## Status

PARTIAL — bounded Windows-only observability is implemented locally; exact-head hosted CI is pending. This work package diagnoses runtime only and makes no performance change.

## CI Fitness Contract

```text
CURRENT WP: CI-H2E — Windows Required-Gate Runtime Attribution
CAPABILITY UNDER CHANGE: Windows serial pytest runtime observability
CRITICAL RISKS: timeout before useful attribution; accidental canonical-gate change
BASELINE GATES TO KEEP: four job names; 15-minute cap; Windows `python -m pytest -q`; Linux H2D patch
WP-SPECIFIC GATES REQUIRED: module start/end/total timing markers visible in Windows logs
GATES NOT REQUIRED YET: runtime optimization, xdist, test partitioning, timeout increase
MAX JOB RUNTIME: 15 minutes
CI CHANGE REQUIRED BEFORE IMPLEMENTATION: YES
RATIONALE: repeated runs vary between healthy and cancelled; timing attribution is needed before any tuning.
```

## Evidence and attribution boundary

- Project virtual-environment collection baseline: `307` tests, zero collection errors.
- Exact H2D implementation run `32326389686` (`ca0c1c2`): Windows cancelled after `247 passed in 776.66s`; progress reached 23%, 46%, and 70%, so no individual hanging test is proven.
- Later exact H2D documentation-head run `32327482088` (`d9fad96`): Windows serial full regression passed in `619s` (10m19s).
- Therefore the timeout is non-deterministic from current evidence. SQLAlchemy's `KeyboardInterrupt` location is interruption evidence, not root-cause attribution.

## What changed

- Added `scripts/ci_windows_runtime_attribution.py`, a Windows-CI-only pytest plugin.
- It emits flushed `CI_WINDOWS_RUNTIME` markers for session start/finish and each test module's start, end, wall time, call time, and completed test count; interrupted runs still retain completed-module markers and the active module marker.
- Windows `Full regression` remains exactly `python -m pytest -q`; only that step receives `PYTHONPATH` and `PYTEST_ADDOPTS` to load the observer.
- No collection, test order, test outcome, production source, business test, migration, dependency, Linux workflow, timeout, or xdist setting changed.

## Files changed

- `.github/workflows/ci.yml`
- `scripts/ci_windows_runtime_attribution.py`
- `docs/agent_handoff/CURRENT.md`

## Local verification

- Targeted plugin run: `tests/test_datetime_utils.py` — `10 passed`; emitted session/group/total markers.
- The first local targeted run encountered an existing permission denial in `%LOCALAPPDATA%\\Temp\\pytest-of-Admin`; rerun used approved generated path `.tmp/pytest/ci-h2e-plugin` and passed.
- Targeted Ruff: PASS. Windows workflow contract validation: PASS; job names/caps and canonical serial command are unchanged.

## Exact CI required

- Push the H2E branch and create a draft PR.
- Read the Windows job for the exact implementation head; record module markers and all four job outcomes.
- Do not rerun blindly. If the Windows job cancels again, use the final completed-module marker and active-module marker to classify the bottleneck. If it passes, preserve the module totals as healthy-run baseline evidence.

## Explicitly NOT done

- No optimization, test skip/weakening, xdist, serial-command change, timeout increase, Windows runner change, production/test/migration/dependency change, Linux H2D change, P0-B2, WP-MI, merge, installer, or release work.

## Next recommended task

After exact-head evidence, request an independent ChatGPT audit. Only then create a separate, bounded work order if a specific runtime bottleneck is proven.

## Git state

- Branch: `ci/hardening-2e-windows-runtime-attribution`.
- Base includes CI-H2D branch head `d9fad96` while PR #19 remains unmerged.
- Commit/push/PR: pending final local verification.
