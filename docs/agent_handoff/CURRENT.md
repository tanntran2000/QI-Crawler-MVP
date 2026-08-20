# QI-Crawler Agent Handoff

## Task

CI-H3A — Deduplicate Feature-Branch CI Triggers

## Status

PARTIAL — local trigger-only change is complete; remote PR verification is pending. Historical Windows runtime root cause remains `UNKNOWN`; no runtime optimization is performed in this work package.

## CI Fitness Contract

```text
CURRENT WP: CI-H3A — Deduplicate Feature-Branch CI Triggers
CAPABILITY UNDER CHANGE: Python CI event trigger selection
CRITICAL RISKS: accidental change to required jobs or canonical Windows/Linux behavior
BASELINE GATES TO KEEP: four job names; 15-minute cap; Windows `python -m pytest -q`; H2D Linux provisioning; H2E runtime attribution
WP-SPECIFIC GATES REQUIRED: one pull_request Python CI for the H3A PR head; push Python CI only for main
GATES NOT REQUIRED YET: runtime optimization, xdist, test partitioning, timeout increase, concurrency
MAX JOB RUNTIME: 15 minutes
CI CHANGE REQUIRED BEFORE IMPLEMENTATION: YES
RATIONALE: unrestricted push plus pull_request triggers duplicate full CI for one feature-branch commit.
```

## Evidence and attribution boundary

- Project virtual-environment collection baseline: `307` tests, zero collection errors.
- Exact H2D implementation run `32326389686` (`ca0c1c2`): Windows cancelled after `247 passed in 776.66s`; progress reached 23%, 46%, and 70%, so no individual hanging test is proven.
- Later exact H2D documentation-head run `32327482088` (`d9fad96`): Windows serial full regression passed in `619s` (10m19s).
- Therefore the timeout is non-deterministic from current evidence. SQLAlchemy's `KeyboardInterrupt` location is interruption evidence, not root-cause attribution.
- CI-H2E is now merged in PR `#20`; its exact hosted run `32330192517` (`efc86e20fd3cf38022565f5f8e743392baa731e8`) passed all four required jobs. The H2E diagnostic capability remains available; historical Windows runtime root cause remains **UNKNOWN**.

## Exact-head healthy runtime baseline

- Highest test-call modules: `test_hsmt_facts.py` `76.183s`; `test_coteccons_scan.py` `43.792s`; `test_web_document_intake.py` `35.852s`; `test_tbmt_export.py` `34.492s`; `test_gui.py` `26.580s`; `test_alembic_migrations.py` `25.637s`.
- Largest **NON-CALL WALL TIME** (wall minus call): `test_document_intake.py` about `62.1s`; `test_manual_tender_workspace.py` about `45.4s`; `test_native_extraction.py` about `45.2s`; `test_document_bundle_guard.py` about `21.1s`; `test_ground_truth.py` about `15.0s`.
- FACT: the healthy baseline contains both expensive test calls and significant non-call wall time. The latter may include setup, teardown, fixtures, hooks, framework work, reporting, or other non-call execution; it is not proven setup/teardown time. INFERENCE: historical cancelled-run time cannot be assigned to any individual module because those runs predate these markers.

## Historical H2E implementation

- `scripts/ci_windows_runtime_attribution.py` emits flushed `CI_WINDOWS_RUNTIME` session and per-module timing markers for the Windows gate.
- Windows `Full regression` remains exactly `python -m pytest -q`; only `PYTHONPATH` and `PYTEST_ADDOPTS` load the observer.
- No collection, test order, test outcome, production source, business test, migration, dependency, Linux workflow, timeout, or xdist setting changed in H2E.

## What changed

- Python CI `push` is restricted to `main`; `pull_request` is restricted to `main`.
- Feature-branch commits with an open PR now receive only the pull-request Python CI; a merge/push to `main` receives the push Python CI.
- Required jobs, job names, 15-minute caps, H2D Linux provisioning, H2E observer, and Windows `python -m pytest -q` are unchanged.
- No concurrency, path filtering, manual dispatch, test/runtime optimization, production source, test, migration, dependency, or security-workflow change was made.

## Files changed

- `.github/workflows/ci.yml`
- `docs/agent_handoff/CURRENT.md`

## Local verification

- Collection baseline: `307` tests, zero collection errors.
- Workflow inspection confirms exactly `push → main` and `pull_request → main`.
- Remote verification: pending H3A branch push and PR creation; no manual rerun will be used.

## Historical H2E evidence

- Merged PR `#20`: `https://github.com/tanntran2000/QI-Crawler-MVP/pull/20`.
- Exact implementation-head run: `32330192517`.
- The Windows log contains module start/end/total markers, so a recurrence will retain the final completed module and active module before cancellation.
- No rerun was performed.

## Explicitly NOT done

- No concurrency, optimization, test skip/weakening, xdist, serial-command change, timeout increase, Windows runner change, production/test/migration/dependency change, Linux H2D change, H2E observer change, CodeQL/AI security configuration change, P0-B2, WP-MI, merge, installer, or release work.

## Next recommended task

After remote H3A verification, request independent ChatGPT audit. If the single canonical Windows run exceeds its cap, stop and use H2E attribution evidence; do not optimize in H3A.

## Git state

- Base main: `83123cd8cc369cec32bc4cadaf8be0ef104e2a1b` (PR `#19` / CI-H2D and PR `#20` / CI-H2E merged).
- Branch: `ci/h3a-deduplicate-workflow-triggers`.
- H3A commit/push/PR: pending remote verification.
