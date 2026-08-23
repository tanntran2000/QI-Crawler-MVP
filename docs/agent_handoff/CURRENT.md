# QI-Crawler Agent Handoff

## HANDOFF_ID

WP-REL-01 — Corrective Stage A

## Status

HOLD — isolation corrective work is being verified; no release/publish.

## Mission

Prepare a verifiable local v0.8.0 Team Bid release candidate without touching
production data or publishing the official reference release.

## Current verified state

- Branch: `wp/rel-team-bid-reference`.
- Local implementation head before corrective changes: `897b4fc`.
- Canonical version target: `0.8.0`; release impact: YES; version impact: MINOR.
- Alembic has one head: `0013_add_candidate_review_events`.
- Recovery PASS: production DB restored from the verified backup; contaminated
  DB preserved at `C:\Users\Admin\AppData\Local\QI-Crawler-Recovery-WP-REL-01-20260823-002826064\egp.db`.
- Restored production DB SHA-256:
  `384FE99B58F9D26CD4649725D9359EC35F6261A6729B9080EB0CC0A147913BEB`.
- No production WAL/SHM sidecars were present; the smoke-created
  `data\reports\TBMT_Latest.xlsx` was removed under the approved recovery.

## Incident and root cause

- Team-Bid copy smoke used `QI_CRAWLER_DATA_DIR`, but the copied
  `config.yaml` retained absolute production `storage.*` paths.
- `prepare_standalone_runtime()` only generated a config when absent; it did
  not rebase persisted managed paths. DB and report consumers therefore trusted
  production paths.
- Corrective regression now rebases managed SQLite/database, document,
  download, discovery, raw, rejects, and report paths inside an explicit data
  override; non-SQLite configured databases fail closed.

## Plugin execution evidence

- CodeGraph: available; `status`, `sync`, and isolation path exploration
  completed before edits. Impact radius was separated from edit/test radius.
- Superpowers invoked: systematic-debugging (root-cause trace), TDD (RED →
  GREEN regression), verification-before-completion required for final gates.
- TDD RED: persisted foreign `storage.*` paths remained unchanged under an
  isolated data root.
- TDD GREEN: the same test now resolves every managed path inside the isolated
  root; adjacent standalone/installer tests pass.

## Files changed in corrective work

- `src/qi_crawler/standalone.py`
- `tests/test_standalone.py`
- `AGENTS.md`
- `docs/agent/HUMAN_COLLABORATION.md`
- `docs/agent/OPERATING_MODEL.md`
- `docs/agent/FEEDBACK_LEDGER.md`
- `docs/agent_handoff/CURRENT.md`

## Verification state

- Targeted standalone/installer tests: `12 passed` after corrective fix.
- Full verification, fresh build, and fresh isolated Team-Bid-copy smoke remain
  required before any PASS claim.
- `Crawler tool\Current`, official Team Bid Reference, tag, GitHub Release,
  and production mutation remain forbidden.

## Pending / unverified

- Run fresh targeted/full pytest, Ruff, diff-check, and changed-file review.
- Rebuild a fresh v0.8.0 candidate and run clean-data plus fresh Team-Bid-copy
  smoke only after proving effective paths are inside the copy.
- Compare production DB/report state before and after retest.
- Commit/push the bounded corrective branch and create one Draft PR only if all
  release gates pass; volatile PR/CI truth must be verified live.

## Risks / blockers

- Any path escaping the isolated root, production mutation, migration/schema
  need, unexpected deletion, or candidate mismatch is STOP_FOR_REVIEW.
- Stage A remains HOLD until fresh copy smoke proves the isolation contract.

## Explicitly NOT done

- No official publish, Team Bid Reference creation, tag, GitHub Release, or
  installer release publication.
- No production migration, downgrade, stamp, SQL repair, config rewrite in the
  live production root, or broad data rollback.

## Next objective

Complete corrective isolation verification; if PASS, finalize Stage A evidence
for independent audit and Human merge decision.

## Locked decisions

- Keep version `0.8.0`.
- Preserve the restored production DB and quarantine copy.
- Do not run candidate against production paths.

## Tool state

- CodeGraph remains local-only and up to date.
- Commit/push/PR/CI status is live GitHub state and is not asserted here.
