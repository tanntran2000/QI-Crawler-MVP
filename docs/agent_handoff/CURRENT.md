# QI-Crawler Agent Handoff

## Task

CI-H2D — Linux Provisioning Stability

## Status

PARTIAL — bounded Linux provisioning patch prepared; exact-head GitHub CI is pending after feature-branch push.

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
- CI fitness after local workflow review: `FIT_WITH_ADDITION`, pending hosted exact-head proof.

## Local verification

- No full pytest/Ruff run: this is workflow-only and hosted Linux is the relevant environment.
- YAML CI contract: PASS; all required job names, 15-minute caps, Linux provisioning caps, and serial Windows command were checked.
- Bash is unavailable on this Windows development machine; hosted Linux is required to execute the shell block.
- `git diff --check` and scope review pending final verification.

## GitHub verification

- Exact GitHub CI run/head SHA: pending feature-branch push.
- Required outcomes to record: Code Quality; Tests Ubuntu 3.12; Tests Windows 3.12; Compatibility Ubuntu 3.11.
- A repeated Linux provisioning timeout is a stop condition; no blind reruns.

## Known blockers

- Windows required-CI runtime remains unresolved and is not changed in CI-H2D.
- PR #13 P0-B1 remains functionally PASS but merge HOLD until required CI is stable.

## Explicitly NOT done

- No P0-B1/P0-B2/P0-C work, production/test/migration change, pytest-xdist change, timeout increase, test skip, dependency change, PR merge, installer or release work.

## PR status

- PR #13: OPEN / HOLD; untouched.
- PR #17: OPEN / HOLD; its Windows `-n 2` experiment is not continued here.
- PR #18: DRAFT; untouched.

## Next recommended task

Read exact-head CI evidence for CI-H2D; if all four required jobs pass under 15 minutes, request independent audit before any P0-B1 integration decision.

## Git state

- Branch: `ci/hardening-2d-linux-provisioning-stability`.
- Base: `a90ffd4e17c389f2925cb5b6ce036be1530cd79a`.
- Commit: pending.
- Push: pending.
