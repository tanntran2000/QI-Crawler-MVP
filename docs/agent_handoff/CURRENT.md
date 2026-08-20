# QI-Crawler Agent Handoff

## Task

CI-H2F — Windows Broad Runtime Degradation Attribution

## Status

PARTIAL — bounded Windows-environment observability is implemented locally. Hosted evidence is still required; the historical Windows runtime root cause remains `UNKNOWN`. No performance optimization is authorized.

## CI Fitness Contract

```text
CURRENT WP: CI-H2F — Windows Broad Runtime Degradation Attribution
CAPABILITY UNDER CHANGE: Windows-hosted runtime attribution only
CRITICAL RISKS: changing the canonical serial gate, consuming the 15-minute budget, or treating timing as a pass/fail threshold
BASELINE GATES TO KEEP: four required job names; 15-minute caps; Windows `python -m pytest -q`; H2D Linux provisioning; H2E module markers; H3A trigger contract
WP-SPECIFIC GATES REQUIRED: bounded CPU/filesystem/SQLite/process/Qt probes before the unchanged Windows pytest command
GATES NOT REQUIRED YET: runtime optimization, xdist, test partitioning, timeout increase, runner replacement, product changes
MAX JOB RUNTIME: 15 minutes
CI CHANGE REQUIRED BEFORE IMPLEMENTATION: YES
RATIONALE: two post-H3A Windows serial runs showed broad degradation, but H2E per-module markers cannot distinguish environmental slowness from a specific shared subsystem.
```

## Preserved evidence

- CI-H2D is merged. Its exact healthy documentation-head Windows run `32327482088` (`d9fad96`) completed serial regression in `619s`.
- CI-H2E is merged. Exact healthy run `32330192517` (`efc86e20fd3cf38022565f5f8e743392baa731e8`) passed all four required jobs: Windows `307 passed in 579.42s`; pytest session about `579.35s`.
- Healthy H2E call-time leaders: `test_hsmt_facts.py` `76.183s`; `test_coteccons_scan.py` `43.792s`; `test_web_document_intake.py` `35.852s`; `test_tbmt_export.py` `34.492s`; `test_gui.py` `26.580s`; `test_alembic_migrations.py` `25.637s`.
- CI-H3A is merged in PR `#21` at main commit `9906fe4d33ee50e48719328d2fa78d1eb984d626`. Its trigger fix is functionally proven: feature branch with PR produces one `pull_request` Python CI and no separate feature-branch `push` Python CI.
- Slow run `32335767001` reached `228 passed` at about `806.32s`; `test_multisource_tbmt.py` was active for only about `2.9s` when cancellation began and is not a proven root cause. `test_document_intake.py` recorded `127.655s` wall / `8.496s` call; `test_manual_tender_workspace.py` `107.321s` wall / `14.939s` call.
- Slow exact-head run `32336889214` (`5240eca6cd5845417d5fc1bb374e118a974f9829`) reached `156 passed` at `802.85s`: `test_coteccons_scan.py` `216.743s` call; `test_alembic_migrations.py` `76.335s`; `test_crawl_resume.py` `49.474s`; `test_document_intake.py` `173.777s` wall / `7.201s` call; `test_gui.py` `90.085s` wall / `81.452s` call.
- **FACT:** the two slow runs show broad degradation across unrelated groups. **INFERENCE:** a specific product module or subsystem is not yet causally identified.
- **NON-CALL WALL TIME** means wall time minus test-call time; it may include setup, teardown, fixtures, hooks, framework work, reporting, or other non-call execution. It is not proven setup/teardown time.

## H2F diagnostic design

- `scripts/ci_windows_environment_probe.py` is CI-only and runs once immediately before Windows pytest.
- It emits flushed, human-readable `CI_WINDOWS_DIAG` records for `ENV`, `CPU`, `FILESYSTEM`, `SQLITE`, `PROCESS`, and `QT` with elapsed seconds and limited environment metadata.
- All probes use temporary/generated data; filesystem and SQLite probes clean up their own temporary directories. The process probe has a `10s` bound. No metric is a pass/fail threshold; an individual probe error is logged and pytest still runs.
- H2E `CI_WINDOWS_RUNTIME` module markers remain unchanged, so a future run can compare environmental probes and per-module call/non-call timings.

## What changed

- Windows CI adds one `Windows environment probes` step before the unchanged canonical `python -m pytest -q` command.
- No job name, trigger, timeout, test order, test outcome, dependency, production source, test, migration, Linux workflow, xdist, concurrency, or performance optimization changed.

## Files changed

- `.github/workflows/ci.yml`
- `scripts/ci_windows_environment_probe.py`
- `docs/agent_handoff/CURRENT.md`

## Local verification

- Collection baseline: `307` tests, zero collection errors.
- The probe script runs locally with isolated temporary files and exits without performance thresholds.
- Workflow inspection confirms: `push → main`; `pull_request → main`; all four required jobs retain `timeout-minutes: 15`; Windows command remains exactly `python -m pytest -q` with H2E markers enabled.

## Explicitly NOT done

- No test/module optimization, splitting, sharding, xdist, timeout increase, Windows runner change, H3A trigger change, product/test/migration/dependency change, CI rerun, merge, installer, release, P0-B2, WP-MI, or other product work.

## Next recommended task

Allow one naturally triggered CI-H2F pull-request run, compare its `CI_WINDOWS_DIAG` and H2E `CI_WINDOWS_RUNTIME` output with the healthy and two slow runs, then perform a separate evidence review. No H2F follow-up or optimization without new hosted evidence.

## Git state

- Base main: `9906fe4d33ee50e48719328d2fa78d1eb984d626` (PR `#21` merged).
- Branch: `ci/h2f-windows-broad-runtime-attribution`.
- Commit/push: pending local verification; no merge.
