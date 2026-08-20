# QI-Crawler Agent Handoff

## Task

CI-H2D — Linux Provisioning Stability

## Status

PARTIAL — Linux provisioning is proven stable on the exact implementation head; required Windows serial regression exceeded the 15-minute job budget and was cancelled. Windows is outside this work order and was not changed or rerun.

## Baseline and evidence

- Remote `main`: `a90ffd4e17c389f2925cb5b6ce036be1530cd79a`.
- Baseline collection in the project virtual environment: `307` tests, zero collection errors.
- PR #18 run `32236391130`: Ubuntu 3.12 completed pytest (`307 passed`); Ubuntu 3.11 stalled in `apt-get` before pytest and was cancelled at the 15-minute job cap.
- The GUI suite imports PySide6 with `QT_QPA_PLATFORM=offscreen`; `libEGL.so.1` and `libGL.so.1` remain required Linux runtime libraries.

## What changed

- Preserved all four required CI job names and their `timeout-minutes: 15` cap.
- Preserved Qt offscreen coverage, Ubuntu 3.12, Ubuntu 3.11, and the serial Windows test command.
- Added a Linux `ldconfig` preflight: when both runtime libraries already exist, apt is skipped.
- When installation is needed, each `apt-get update` and `apt-get install` command has a hard `180s` foreground cap, retains the existing request retry/timeout settings, and fails explicitly on timeout/failure.
- Re-checks both libraries after installation; missing libraries fail the job before pytest rather than silently weakening GUI coverage.

## Files changed

- `.github/workflows/ci.yml`
- `docs/agent_handoff/CURRENT.md`

## Architecture / governance impact

- CI infrastructure only. No production source, tests, migrations, dependencies, runtime data, or application behavior changed.
- CI fitness before this task: `UNSTABLE` because Linux provisioning could consume the full job budget.
- Linux CI fitness after exact hosted evidence: `FIT` for Qt provisioning; overall required-CI fitness remains `UNSTABLE` because the Windows serial lane exceeds its cap.

## Local verification

- No full pytest/Ruff run: this is workflow-only and hosted Linux is the relevant environment.
- YAML CI contract: PASS; all required job names, 15-minute caps, Linux provisioning caps, and serial Windows command were checked.
- Bash is unavailable on this Windows development machine; hosted Linux is required to execute the shell block.
- `git diff --check`: PASS before the implementation commit; final documentation checkpoint verification is pending.

## GitHub verification

- Exact run: `32326389686`, implementation head `ca0c1c2cf7c64295f42e15e96f31b4b153ff696a`.
- Code Quality: PASS (`28s`).
- Tests Ubuntu 3.12: PASS (`2m42s`); Linux Qt provisioning completed and full regression passed.
- Compatibility Ubuntu 3.11: PASS (`1m52s`); Linux Qt provisioning completed and compatibility regression passed.
- Tests Windows 3.12: CANCELLED at the required `15-minute` cap while its serial full regression was running. This is a pre-existing required-CI blocker, not a Linux provisioning regression.
- No blind rerun was performed.

## Known blockers

- Windows required-CI runtime remains unresolved: its serial full regression exceeded the cap on run `32326389686`; it is not changed in CI-H2D.
- PR #13 P0-B1 remains functionally PASS but merge HOLD until required CI is stable.

## Explicitly NOT done

- No P0-B1/P0-B2/P0-C work, production/test/migration change, pytest-xdist change, timeout increase, test skip, dependency change, PR merge, installer or release work.

## PR status

- PR #13: OPEN / HOLD; untouched.
- PR #17: OPEN / HOLD; its Windows `-n 2` experiment is not continued here.
- PR #18: DRAFT; untouched.

## Next recommended task

Create a bounded Windows CI-runtime triage work order. It must diagnose the serial full-regression stall before any change; do not alter the Linux hardening patch or merge P0-B1 while the required lane is unstable.

## Git state

- Branch: `ci/hardening-2d-linux-provisioning-stability`.
- Base: `a90ffd4e17c389f2925cb5b6ce036be1530cd79a`.
- Implementation commit: `ca0c1c2cf7c64295f42e15e96f31b4b153ff696a` (`Bound Linux CI Qt provisioning`).
- Push: `origin/ci/hardening-2d-linux-provisioning-stability` complete.
- Draft PR: `#19` (`https://github.com/tanntran2000/QI-Crawler-MVP/pull/19`).
- Documentation checkpoint commit/push: pending final local verification.
