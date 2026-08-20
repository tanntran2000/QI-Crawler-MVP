# QI-Crawler Agent Handoff

## Task

WP-MI-0 — KHMT Data Contract + Sanitized Golden Fixture

## Status

LOCAL PASS — bounded contract and synthetic CI fixture only; hosted CI will run
naturally after the draft PR is pushed.

## CI Fitness Contract

```text
CURRENT WP: MI-0 Data Contract + Sanitized Golden Fixture
CAPABILITY UNDER CHANGE: import-free KHMT source-data contract and deterministic fixture
CRITICAL RISKS: PL/IB namespace confusion, revision collapse, source-data guessing, or sensitive data in CI
BASELINE GATES TO KEEP: full regression, Ruff, diff check, existing required hosted jobs
WP-SPECIFIC GATES REQUIRED: contract identity, multiple plan rows, raw/normalized coexistence, geography status, provenance, fixture determinism
GATES NOT REQUIRED YET: Excel import, persistence/migration, filtering, ranking, GUI, human confirmation, export, or legal output
MAX JOB RUNTIME: 15 minutes
CI CHANGE REQUIRED BEFORE IMPLEMENTATION: NO
RATIONALE: MI-0 freezes source facts before any operational Market Intelligence behavior exists.
```

## Baseline and locked numbering

- Base `main`: `b4db1574737872df1138a75856fa586221b97cab`.
- WP-UI-3 is merged into this base.
- `MI-0` Data Contract + Sanitized Golden Fixture.
- `MI-1` Import + Normalize + Province/City Resolution + Core Filter Engine.
- `MI-2` Discovery Buckets + Targeted Search Contract.
- `MI-3` Human Confirmation; `MI-4` Confirmed Excel Export; `MI-5` Legal DOCX;
  `MI-6` Bid Radar GUI; `PIC-MI-1` Real Business Golden Flow.

## What changed

- Added a bounded in-memory KHMT contract in `market_intelligence`; it has no
  importer, database model, business score, or UI behavior.
- `PL` and `IB` remain separate namespaces. An optional notice relation may
  only be supplied explicitly; it is never derived from a `PL` value.
- Added an entirely synthetic deterministic fixture covering multiple package
  rows for one plan revision, a plan revision change, confirmed province/city
  records, and an unresolved `NEEDS_REVIEW` location.
- Added contract documentation and regression tests for revision identity,
  provenance, raw/normalized coexistence, and no geography guessing.

## Files changed

- `src/qi_crawler/market_intelligence/__init__.py`
- `src/qi_crawler/market_intelligence/khmt_contract.py`
- `tests/fixtures/khmt/khmt_sanitized_golden.json`
- `tests/test_khmt_contract.py`
- `docs/KHMT_DATA_CONTRACT.md`
- `docs/agent_handoff/CURRENT.md`

## Verification

- Collection baseline: `316` tests, zero collection errors.
- Targeted MI-0 regression: `6 passed` (one pre-existing pytest cache permission warning).
- Full local regression: `316 passed` (one pre-existing pytest cache permission warning).
- Ruff: PASS; `git diff --check`: PASS.
- No migration, runtime-user-data, crawler, parser, extraction, warehouse, or UI change.

## Explicitly NOT done

- No real KHMT workbook read or commit; no Excel importer, filter/search,
  persistence/schema migration, Human Confirmation, export, Legal DOCX, GUI,
  PL-to-IB watcher, AI, GO/HOLD/NO-GO, vendor/model/SKU decision, or scoring.

## Next action

- ChatGPT audit of the MI-0 draft PR, then authorize MI-1 separately.

## Git state

- Branch: `wp/mi-0-khmt-data-contract`.
- Head at task start: `b4db1574737872df1138a75856fa586221b97cab`.
- Commit/push: pending final verification; no merge.
