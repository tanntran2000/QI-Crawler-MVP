# QI-Crawler Agent Handoff

## Task

CI-H2E — Windows Required-Gate Runtime Attribution

## Status

PASS — diagnostic capability proven; historical Windows runtime root cause remains `UNKNOWN`. This exact run was healthy, so the new markers establish a measured baseline rather than support an optimization claim. Optimization is **NOT AUTHORIZED**.

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
- Exact H2E run `32330192517` (`efc86e20fd3cf38022565f5f8e743392baa731e8`): all four required jobs PASS; Windows job `10m56s`, serial pytest `307 passed in 579.42s`.
- CI-H2E verdict: **PASS — DIAGNOSTIC CAPABILITY PROVEN**. Windows runtime root cause: **UNKNOWN**. No CI-H2F is authorized without new slow or cancelled Windows-run evidence.

## Exact-head healthy runtime baseline

- Highest test-call modules: `test_hsmt_facts.py` `76.183s`; `test_coteccons_scan.py` `43.792s`; `test_web_document_intake.py` `35.852s`; `test_tbmt_export.py` `34.492s`; `test_gui.py` `26.580s`; `test_alembic_migrations.py` `25.637s`.
- Largest **NON-CALL WALL TIME** (wall minus call): `test_document_intake.py` about `62.1s`; `test_manual_tender_workspace.py` about `45.4s`; `test_native_extraction.py` about `45.2s`; `test_document_bundle_guard.py` about `21.1s`; `test_ground_truth.py` about `15.0s`.
- FACT: the healthy baseline contains both expensive test calls and significant non-call wall time. The latter may include setup, teardown, fixtures, hooks, framework work, reporting, or other non-call execution; it is not proven setup/teardown time. INFERENCE: historical cancelled-run time cannot be assigned to any individual module because those runs predate these markers.

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
- Exact H2E hosted CI: Code Quality PASS (`26s`); Tests Ubuntu 3.12 PASS (`1m55s`); Compatibility Ubuntu 3.11 PASS (`1m53s`); Tests Windows 3.12 PASS (`10m56s`).

## Exact CI evidence

- Draft PR `#20`: `https://github.com/tanntran2000/QI-Crawler-MVP/pull/20`.
- Exact implementation-head run: `32330192517`.
- The Windows log contains module start/end/total markers, so a recurrence will retain the final completed module and active module before cancellation.
- No rerun was performed.

## Explicitly NOT done

- No optimization, test skip/weakening, xdist, serial-command change, timeout increase, Windows runner change, production/test/migration/dependency change, Linux H2D change, P0-B2, WP-MI, merge, installer, or release work.

## Next recommended task

Human / Reviewer handles merge-order reconciliation: merge PR `#19` before PR `#20`, then return to the business fast-track WP-MI. If a future instrumented Windows run exceeds the cap, use its final marker to create one bounded attribution/fix work order; do not optimize from the current healthy-run data alone.

## Git state

- Branch: `ci/hardening-2e-windows-runtime-attribution`.
- PR `#20` stacks on CI-H2D; PR `#19` must merge before PR `#20`.
- Commit: `efc86e20fd3cf38022565f5f8e743392baa731e8` (`Add Windows CI runtime attribution`).
- Push: `origin/ci/hardening-2e-windows-runtime-attribution` complete.
- Draft PR: `#20`.
- Documentation checkpoint records hosted evidence only; no CI design change, optimization, rerun, merge, or main push was performed.
