# QI-Crawler Agent Handoff

## HANDOFF_ID

WP-MI-SRC-01 — SA Excel Source Routing + Human Override + Source-Type Ground Truth

## Status

LOCAL IMPLEMENTATION / NATURAL CI REQUIRED / NO MERGE

## Mission

Route Excel sources safely for Bid Radar: detect KHMT/TBMT from filename,
schema and PL/IB evidence; require named Human authority for ambiguity; keep
source-type corrections append-only; do not implement TBMT import.

## Current verified state

- Branch: `wp/mi-source-type-routing-ground-truth`.
- Entry baseline: `c1e9e16ffca3b3fd83ba7a150b16353445d7856e`.
- Package/runtime version remains `0.8.0`; no tag, release, publish or
  Team Bid Reference change is part of this Work Package.
- Real business workbooks were inspected read-only; source files were not
  modified or copied into the repository.
- Read-only live workbook detection: `KHMT_19_8_2026.xlsx` → KHMT/PL/AUTO;
  `TBMT_19_8_2026.xlsx` → TBMT/IB/AUTO with tolerant `IB...-00` identities.
- CodeGraph shell exploration succeeded before edits; `.codegraph/` remains
  local-only.

## Implemented contract

- KHMT/TBMT filename hints are case-insensitive and prefix-based.
- Header signatures and embedded PL/IB identities provide content evidence;
  raw identity text is retained alongside canonical identity values.
- Compatible filename + content evidence auto-classifies; unknown filenames,
  schema conflicts and mixed identity namespaces require Human selection.
- TBMT recognition stops safely with `TBMT_SOURCE_RECOGNIZED`; the KHMT
  importer is never called for TBMT.
- Human source decisions require a named reviewer and append to
  `source_type_review_events`; PL/IB identity is never rewritten.
- Existing KHMT importer/search/review/export authority remains unchanged.

## Files changed

- `src/qi_crawler/market_intelligence/source_detection.py`
- `src/qi_crawler/market_intelligence/source_type_review.py`
- `src/qi_crawler/models.py`
- `src/qi_crawler/db.py`
- `src/qi_crawler/gui.py`
- `src/qi_crawler/gui_services.py`
- `alembic/versions/0014_add_source_type_review_events.py`
- focused source/routing/review/GUI tests and migration expectation updates
- `docs/agent/HUMAN_COLLABORATION.md`
- `docs/agent/PROJECT_MEMORY.md`
- `docs/agent/FEEDBACK_LEDGER.md`
- `CHANGELOG.md`

## Verification evidence

- Entry collection baseline: `459 tests collected`.
- Focused detector/routing/GUI/migration run: `93 passed`.
- Full pytest: `475 passed` (one existing Windows PytestCacheWarning); Ruff:
  PASS; `git diff --check`: PASS.
- Migration is additive and non-destructive; current head is
  `0014_add_source_type_review_events` with one head.

## Data safety / risks

- Production `%LOCALAPPDATA%\QI-Crawler`, business workbooks, release
  artifacts and user documents were not touched.
- No TBMT importer, PlanPackage conversion, AI, learning, scoring, crawler or
  HSMT behavior was added.
- Any migration failure, source identity ambiguity, unexpected deletion or
  need for release/publish is `STOP_FOR_REVIEW`.

## Explicitly NOT done

- No TBMT Bid Radar import or TBMT PlanPackage model.
- No automatic learning or promotion of source rules.
- No tag, GitHub Release, installer build or user-visible publish.

## Next objective

Run full verification, inspect changed-file scope, commit bounded changes,
push this feature branch and create exactly one Draft PR for independent audit.

## Plugin evidence

- CodeGraph: shell `codegraph explore` succeeded for Bid Radar import path,
  `import_khmt_workbook`, source routing impact and related tests.
- Superpowers: TDD RED→GREEN, systematic-debugging of TBMT→KHMT failure, and
  verification-before-completion are required for final gates.

## Git / delivery state

- Commit/push/PR: not yet performed.
- No merge.
