# QI-Crawler Agent Handoff

## HANDOFF_ID

WP-GOV-01

## HANDOFF_REVISION

1

## WP

WP-GOV-01 — Multi-Agent Memory v3 + Handoff Continuity

## Status

LOCAL PASS / NATURAL CI IN PROGRESS / NO MERGE

## SNAPSHOT_HEAD

`e166859c21ec727e2791baf9ad84e63bba68f5ca` (docs-only implementation commit; push pending)

## UPDATED_BY_ROLE

BUILDER_SINGLE_WRITER

## Mission

Create a durable, bounded memory and handoff system so a new agent can recover
project truth, current scope, verified evidence, and the exact next objective
without relying on chat history.

## Current verified state

- Canonical checkout: `egp-crawler-python`.
- Branch: `wp/gov-multi-agent-memory-v3`.
- Baseline `main` and `origin/main`: `07ef548ee3747efd617e131880368cedc52f3bfc`.
- Working tree was clean at entry.
- Pytest collection baseline: `452` tests.
- Main contains merged MI-0..MI-6, managed Document Store/bundle guard,
  adaptive CI governance, and Windows publish mechanics.

## Completed

- Entry Review approved after fast-forwarding the stale local main.
- Legacy overloaded `CURRENT.md` archived at
  `docs/agent_handoff/history/CURRENT_pre_wp_gov_01.md`.
- Added memory index, operating model, main-only project memory, systemic
  lessons, and structured feedback ledger.
- Added LAW 9 to `AGENTS.md` without weakening LAW 1–8.

## Pending / unverified

- Push and natural CI for this branch.
- Human/reviewer audit and merge approval.

## Locked decisions

- Documentation/governance only.
- One active snapshot in `CURRENT.md`; history is archived separately.
- One canonical checkout and one short-lived branch; no Git worktrees.
- Main-only facts are the only facts promoted into `PROJECT_MEMORY.md`.
- No pending Storage, HSNL, AI, Legal, scoring, or future feature work is
  promoted to merged truth.

## Risks / blockers

- Hosted GitHub state may be unavailable from the local environment; do not
  manually rerun CI.
- Historical information must remain recoverable in the archived snapshot.

## Explicitly NOT done

No production code, tests, database/schema, migrations, GUI, crawler,
extraction, CI workflow, dependencies, business data, runtime data, installer,
or release artifact was changed.

## Verification evidence

- Entry baseline fast-forward verified: `HEAD == origin/main == 07ef548…`.
- Collection baseline recorded: `452`.
- Full regression: `452 passed` using the approved `.tmp/pytest-gov`
  basetemp; no failures or collection errors.
- Ruff: PASS; `git diff --check`: PASS.
- Implementation commit: `e166859c21ec727e2791baf9ad84e63bba68f5ca`.
- The default Windows temp root is ACL-blocked locally, so the first pytest
  attempt failed during fixture setup; this is an environment warning, not a
  test failure.

## Next objective

### NEXT

Run the canonical verification gate, commit the bounded documentation change,
push this feature branch, create one Draft PR, and stop for independent audit.

### WHY

The memory-v3 contract is useful only if its links, scope, and repository state
are machine-verified and visible to the next agent.

### ENTRY CONDITION

Only this Work Package, this branch, and the approved documentation scope are
active.

### STOP CONDITION

Any unexpected source deletion, scope expansion, baseline change, or required
production/schema/CI change causes HOLD and human review.

### EXPECTED OUTPUT

Five new `docs/agent` files, LAW 9, one archived CURRENT snapshot, one active
CURRENT snapshot, passing repository checks, and one bounded Draft PR.

## Relevant files

- `AGENTS.md`
- `docs/agent/MEMORY_INDEX.md`
- `docs/agent/OPERATING_MODEL.md`
- `docs/agent/PROJECT_MEMORY.md`
- `docs/agent/LESSONS.md`
- `docs/agent/FEEDBACK_LEDGER.md`
- `docs/agent_handoff/CURRENT.md`
- `docs/agent_handoff/history/CURRENT_pre_wp_gov_01.md`

## Tool state

CodeGraph is not required for this docs-only Work Package and was not
initialized or changed. `.codegraph/` remains local-only. No external plugin
state was added.

## Feedback needing attention

None recorded. New material feedback must use `FEEDBACK_LEDGER.md` and must
not silently change this Work Package.

## Handoff instructions

Read `AGENTS.md`, then the memory index read order, then this snapshot and the
live Git state. Treat live Git/GitHub state as newer than stale prose. Do not
merge, publish, or start a future WP without human approval.
