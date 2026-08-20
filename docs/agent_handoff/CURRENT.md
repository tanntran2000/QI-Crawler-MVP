# QI-Crawler Agent Handoff

## Task

WP-UI-1 — Navigation & Crawl Simplification

## Status

LOCAL PASS — hosted CI verification pending on the draft PR.

## CI Fitness Contract

```text
CURRENT WP: WP-UI-1 — Navigation & Crawl Simplification
CAPABILITY UNDER CHANGE: PySide6 navigation and presentation only
CRITICAL RISKS: hiding a reachable workflow, breaking GUI signal/handler wiring, or UI clipping
BASELINE GATES TO KEEP: full regression, Ruff, diff check, existing required hosted jobs
WP-SPECIFIC GATES REQUIRED: GUI navigation/reachability tests
GATES NOT REQUIRED YET: crawler, extraction, schema, migration, or CI-runtime changes
MAX JOB RUNTIME: 15 minutes
CI CHANGE REQUIRED BEFORE IMPLEMENTATION: NO
RATIONALE: the work is a bounded presentation regrouping that reuses existing handlers and services.
```

## Baseline and CI context

- Base `main`: `9906fe4d33ee50e48719328d2fa78d1eb984d626`.
- CI-H2D, CI-H2E, and CI-H3A are merged into `main`; the CI hardening phase is closed.
- Windows hosted runtime variance remains known technical debt. It is not attributed to this UI work package.
- CI-H2F is not currently authorized for this work package.

## What changed

- The sidebar now has one top-level `THU THẬP` workspace instead of separate scan, single-URL crawl, and login pages.
- `THU THẬP` contains `QUÉT DANH SÁCH`, `CRAWL URL`, and `NGUỒN / ĐĂNG NHẬP` tabs that reuse the existing widgets, handlers, and services.
- The scan source, page limit, and keyword remain primary controls; the list URL is a secondary `TÙY CHỌN NÂNG CAO` control.
- `HSMT / TÀI LIỆU` is renamed to `HSMT / PHÂN TÍCH`; its workspace behavior is unchanged.

## Files changed

- `src/qi_crawler/gui.py`
- `tests/test_gui.py`
- `docs/agent_handoff/CURRENT.md`

## Verification

- Collection baseline: `307` tests, zero collection errors.
- Targeted GUI regression: `50 passed`.
- Full local regression: `308 passed` (one pre-existing pytest cache permission warning).
- Ruff: `All checks passed`; `git diff --check`: PASS.
- No migration, runtime-user-data, crawler, parser, extraction, identity, taxonomy, or database change.

## Explicitly NOT done

- No new crawl/login behavior, authentication changes, HSMT redesign, UI2/UI3, WP-MI, CI workflow change, merge, installer, or release work.

## Next action

- Complete local gates, push this branch, create one draft PR to `main`, then let its CI run naturally for ChatGPT review. Do not merge.

## Git state

- Branch: `wp/ui-1-navigation-crawl-simplification`.
- HEAD at handoff preparation: `9906fe4d33ee50e48719328d2fa78d1eb984d626` plus uncommitted bounded UI/documentation changes.
- Commit/push: not yet performed.
