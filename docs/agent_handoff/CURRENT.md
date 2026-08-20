# QI-Crawler Agent Handoff

## Task

WP-MI-1 — KHMT Import + Normalization + Province/City Resolution + Core Filter Engine

## Status

LOCAL PASS — real-golden audit fix verified locally; Draft PR exact-head CI
will run naturally. The real workbook remains unavailable on this machine.

## CI Fitness Contract

```text
CURRENT WP: MI-1 KHMT Import + Normalization + Province/City Resolution + Core Filter Engine
CAPABILITY UNDER CHANGE: fail-closed XLSX intake and deterministic explainable filtering
CRITICAL RISKS: source-column loss, PL/revision collapse, fabricated prices or geography, opaque filtering
BASELINE GATES TO KEEP: full regression, Ruff, diff check, existing required hosted jobs
WP-SPECIFIC GATES REQUIRED: schema validation, raw provenance, identity/price/method normalization, location evidence, filter reason codes
GATES NOT REQUIRED YET: persistence/migration, GUI, discovery buckets, human confirmation, exports, Legal DOCX, AI or scoring
MAX JOB RUNTIME: 15 minutes
CI CHANGE REQUIRED BEFORE IMPLEMENTATION: NO
RATIONALE: MI-1 adds an isolated backend over the frozen MI-0 source contract.
```

## Baseline and locked numbering

- Base `main`: `7866eed8b4a6ac182df96d83f5b21bb6e54033e3`.
- MI-0 is merged into this base.
- `MI-1` Import + Normalize + Province/City Resolution + Core Filter Engine.
- `MI-2` Discovery Buckets + Targeted Search Contract.
- `MI-3` Human Confirmation; `MI-4` Confirmed Excel Export; `MI-5` Legal DOCX;
  `MI-6` Bid Radar GUI; `PIC-MI-1` Real Business Golden Flow.

## What changed

- Added a read-only `.xlsx` importer that validates required headers, preserves
  all 13 observed fields plus extra columns, records SHA/sheet/source-row
  provenance, and reports malformed rows without returning false-safe success.
- Added conservative normalization for raw/base/revision `PL` identity, integer
  package prices, and a bounded set of selection-method values. No `IB` is derived.
- Added an offline evidence-first province/city resolver. It uses supported source
  text only; conflicting or absent evidence remains `NEEDS_REVIEW`.
- Added deterministic filters for inclusive budget, province/city, include-ANY
  and exclude keywords, and selection method. Results include reason codes and
  matched fields; no score or bid decision exists.
- Audit fix parses only the bounded first comma-delimited selection-method
  component while preserving the complete raw source cell. Unsupported nonblank
  methods now emit an explicit import issue and cannot match a filter.
- Added a small versioned mapping for the approved `xã Châu Đức`, `xã Phú Giáo`,
  and `phường Thới An` evidence patterns. These resolve to HCM as `INFERRED`;
  generic, unknown, or conflicting units remain `NEEDS_REVIEW`.

## Files changed

- `src/qi_crawler/market_intelligence/filter_engine.py`
- `src/qi_crawler/market_intelligence/khmt_importer.py`
- `src/qi_crawler/market_intelligence/khmt_normalization.py`
- `src/qi_crawler/market_intelligence/location_resolver.py`
- `tests/test_khmt_filter_engine.py`
- `tests/test_khmt_importer.py`
- `tests/test_khmt_normalization_location.py`
- `docs/agent_handoff/CURRENT.md`

## Verification

- Collection baseline at task start: `319` tests, zero collection errors.
- Targeted MI-0/MI-1 audit regression: `70 passed`.
- Full local regression: `380 passed` in `237.96s`.
- Ruff: PASS; `git diff --check`: PASS.
- One pre-existing local pytest-cache permission warning; no test failure.
- Synthetic XLSX fixtures cover valid and malformed schemas/rows, all observed
  headers plus extras, PL revisions, real composite selection shapes, approved
  subunit evidence, price formats, location conflict, and deterministic filters.

## Real golden and data safety

- `KHMT_19_8_2026.xlsx` was searched for under the user profile and was not found;
  real golden validation is therefore unavailable, not falsely claimed as PASS.
- ChatGPT's external read-only audit reported `413` source rows and `413` valid
  PL/package rows. It identified composite selection values normalizing to `None`
  and three approved HCM subunit patterns; both defects now have sanitized tests.
- No real KHMT rows, runtime DB, documents, sessions, source fixtures, or secrets
  were read into or added to the repository.
- No migration, persistence, crawler, HSMT, GUI, export, or CI workflow change.

## Explicitly NOT done

- No MI-2+ work, persistence/schema migration, GUI, discovery bucket, ranking,
  Human Confirmation, Excel export, Legal DOCX, PL-to-IB watcher, AI, scoring,
  GO/HOLD/NO-GO, vendor/model/SKU decision, or real-data commit.

## Next action

- ChatGPT audit of Draft PR #26. Do not merge or start MI-2 without authorization.

## Git state

- Branch: `wp/mi-1-khmt-import-filter-engine`.
- Head at task start: `7866eed8b4a6ac182df96d83f5b21bb6e54033e3`.
- Implementation commit: `6c6ddb0` (`Implement KHMT import and filter engine`).
- Audit-fix implementation head: `73f21ad4314e5ed986ecc0fbdbf2802df076c7d2`
  (`Fix KHMT real golden normalization`).
- Draft PR: [#26](https://github.com/tanntran2000/QI-Crawler-MVP/pull/26) to `main`.
- Commit/push: audit-fix implementation pushed; this handoff follows on the same branch.
- Hosted CI: exact-head natural PR run only; no manual rerun and no merge.
