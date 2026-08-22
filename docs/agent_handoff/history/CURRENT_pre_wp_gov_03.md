HISTORICAL / NON-NORMATIVE / MAY CONTAIN SUPERSEDED RULES.

Preserved as the completed WP-GOV-02 handoff snapshot. Do not use this file as
current authority; consult `docs/agent_handoff/CURRENT.md` and live Git/GitHub.

# QI-Crawler Agent Handoff

## HANDOFF_ID

WP-GOV-02

## HANDOFF_REVISION

1

## WP

WP-GOV-02 — Human Collaboration Contract

## Status

LOCAL VERIFICATION PASS / LIVE GITHUB STATE REQUIRED

## SNAPSHOT_HEAD

`5c3b90f` (WP-GOV-02 implementation commit; verify exact tip live)

## UPDATED_BY_ROLE

BUILDER_SINGLE_WRITER

## Mission

Create a durable Human Collaboration Contract so future ChatGPT, Codex, and
other agents understand communication, context filtering, token economy,
tool complementarity, verification, and reporting expectations.

## Current verified state

- Canonical checkout: `egp-crawler-python`.
- Branch: `wp/gov-human-collaboration-contract`.
- `HEAD == origin/main ==
  ffe1088cb9909896daf453646e9b9ac81c9d4f01` at entry.
- Working tree was clean before this Work Package.
- PR #40 (WP-GOV-01) is merged; its exact merge commit is
  `ffe1088cb9909896daf453646e9b9ac81c9d4f01`.
- Main contains the approved Memory v3 governance baseline and MI-0..MI-6.

## Completed in this Work Package

- Added `docs/agent/HUMAN_COLLABORATION.md`.
- Added the contract to the Memory Index read order.
- Linked the contract from the Operating Model without duplicating laws.
- Archived the completed WP-GOV-01 snapshot at
  `docs/agent_handoff/history/CURRENT_pre_wp_gov_02.md`.
- Replaced this file with the single active WP-GOV-02 snapshot.

## Contract locked by this WP

- Human-facing communication is Vietnamese by default; stable technical
  identifiers and machine-readable keys remain English.
- Prompts are shortest-complete, reference repository truth, and use targeted
  context reads rather than stale history dumps.
- Work Order decides what, CodeGraph identifies impact, and Superpowers governs
  how approved work is executed.
- Quality, evidence, fail-closed behavior, testing, and accurate reporting
  outrank speed or speculation.
- Prompt creation requires Memory Index read-in, CURRENT/live Git/GitHub
  reconciliation, baseline/scope/risk identification, and a safe stop on
  unresolved state.

## Scope / files

Documentation/governance only:

- `docs/agent/HUMAN_COLLABORATION.md`
- `docs/agent/MEMORY_INDEX.md`
- `docs/agent/OPERATING_MODEL.md`
- `docs/agent_handoff/CURRENT.md`
- `docs/agent_handoff/history/CURRENT_pre_wp_gov_02.md`

No production, tests, schema, migrations, CI workflow, dependencies,
business data, runtime data, installer, release artifact, or `.codegraph/`
state is in scope.

## Verification

- Targeted tests: NOT REQUIRED; docs-only Work Package.
- Collection baseline: `452` tests.
- Full regression: `452 passed` in `389.32s` using the approved
  `.tmp/pytest-gov-02` basetemp; no failures or collection errors.
- Ruff: PASS; `git diff --check`: PASS.
- Pytest emitted one non-blocking cache warning because the local
  `.pytest_cache` path is ACL-blocked; generated basetemp remained under the
  approved `.tmp/` area.
- Live GitHub verification at entry confirmed main exact base and PR #40
  merged; post-push CI must be read live, not inferred from this file.

## Pending / unverified

- Verify exact-head PR/CI/merge state live from GitHub.
- Independent audit and human merge decision are live workflow concerns.
- Tracked `CURRENT.md` does not own volatile PR/CI/merge truth.

## Risks / blockers

- Live GitHub state can change after this snapshot; use it as the authority for
  PR, CI, and merge status.
- No production behavior is changed.

## Explicitly NOT done

No code, tests, database/schema, migrations, GUI, crawler, extraction, CI
workflow, dependencies, business data, runtime data, installer, release
artifact, AI, Legal, scoring, or future feature WP was started.

## Next objective

### NEXT

Verify live Git/GitHub and complete independent audit/human decision.

### WHY

Volatile PR/CI/merge state changes outside tracked repository; live Git/GitHub
evidence is authoritative and must not be cached as project truth.

### ENTRY CONDITION

Exact WP branch/scope remains valid and live state is reconciled.

### STOP CONDITION

HOLD on scope/baseline/writer/material conflict.

### EXPECTED OUTPUT

A verified WP-GOV-02 governance contract ready for human merge decision.

## Stop conditions

Unexpected source deletion, scope expansion, baseline change, required
production/schema/CI change, or unresolved Git/GitHub state requires `HOLD`
and human review.

## Relevant files

- `AGENTS.md`
- `docs/agent/MEMORY_INDEX.md`
- `docs/agent/OPERATING_MODEL.md`
- `docs/agent/HUMAN_COLLABORATION.md`
- `docs/agent/PROJECT_MEMORY.md`
- `docs/agent/LESSONS.md`
- `docs/agent/FEEDBACK_LEDGER.md`
- `docs/agent_handoff/history/CURRENT_pre_wp_gov_01.md`

## Tool state

CodeGraph is not required for this docs-only Work Package and remains
uninitialized/local-only. Superpowers process was followed through Entry
Review and one Approval Lease. No external plugin state was added.

## Handoff instructions

Read `AGENTS.md`, then the Memory Index order including the Human Collaboration
Contract, then this snapshot and live Git/GitHub state. Treat live evidence as
newer than tracked prose. Do not start a future WP without human approval.
