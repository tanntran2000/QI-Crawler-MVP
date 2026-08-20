# QI-Crawler Agent Handoff

## Task

WP-UI-3 — Structured Diagnostic Log + Copy for AI

## Status

LOCAL PASS — audit-fix hosted CI will run naturally for the new exact head after commit/push.

## CI Fitness Contract

```text
CURRENT WP: WP-UI-3 — Structured Diagnostic Log + Copy for AI
CAPABILITY UNDER CHANGE: local PySide6 diagnostic presentation and clipboard output
CRITICAL RISKS: exposing secrets, losing exception context, or breaking existing GUI log behavior
BASELINE GATES TO KEEP: full regression, Ruff, diff check, existing required hosted jobs
WP-SPECIFIC GATES REQUIRED: structured-event, redaction, copy-report, and GUI layout tests
GATES NOT REQUIRED YET: crawler, extraction, schema, migration, authentication, or CI-runtime changes
MAX JOB RUNTIME: 15 minutes
CI CHANGE REQUIRED BEFORE IMPLEMENTATION: NO
RATIONALE: diagnostics are a GUI-only view over existing GUI log call sites.
```

## Baseline and CI context

- Base `main`: `78f1934aea7472ee911e03c6c6ccd3a3fd86616c`.
- WP-UI-1 is merged. CI-H2D, CI-H2E, and CI-H3A are merged; the CI hardening phase is closed.
- Windows hosted runtime variance remains known technical debt. It is not attributed to this UI work package.
- CI-H2F is not currently authorized for this work package.

## What changed

- GUI events now retain timestamp, level, component, operation, status, error code, correlation fields, package/document IDs, exception/traceback, and app version when available.
- Nhật ký presents a readable event table, selected-event detail, and redacted JSON; `COPY CHO AI` copies a concise local report with recent context.
- Passwords, OTPs, cookies, sessions, Authorization values, API keys, and matching query values are redacted before GUI raw display or clipboard output.
- Multi-value `Cookie`/`Set-Cookie` headers are redacted as a complete header; quoted secret values are also redacted.

## Files changed

- `src/qi_crawler/gui.py`
- `tests/test_gui.py`
- `docs/agent_handoff/CURRENT.md`

## Verification

- Collection baseline: `308` tests, zero collection errors.
- Targeted GUI regression: `52 passed` (one pre-existing pytest cache permission warning).
- Full local regression: `310 passed` (one pre-existing pytest cache permission warning).
- Ruff: PASS; `git diff --check`: PASS.
- No migration, runtime-user-data, crawler, parser, extraction, identity, taxonomy, or database change.

## Explicitly NOT done

- No AI integration, automatic log sending, database migration, crawler/parser/extraction/authentication change, CI tuning, HSMT UI2, WP-MI, installer, or release work.

## Next action

- Complete local gates, push this branch, create one draft PR to `main`, then let its CI run naturally for ChatGPT review. Do not merge.

## Git state

- Branch: `wp/ui-3-structured-diagnostic-log`.
- Parent PR head: `facbbc22cb1044b3ed571b9c8b7cfc87a986d5bb`; audit-fix commit/push follows on the same branch.
- Hosted CI: pending naturally for the audit-fix exact head; no rerun/cancel/merge.
