# QI-Crawler Agent Handoff

## Task

WP-MI-2 — Discovery Buckets + Targeted Search Contract

## Status

LOCAL PASS — bounded in-memory discovery/search backend. Draft PR #27 exact-head
CI runs naturally; final DONE requires independent ChatGPT audit.

## CI Fitness Contract

```text
CURRENT WP: MI-2 Discovery Buckets + Targeted Search Contract
CAPABILITY UNDER CHANGE: in-memory discovery aggregation and reusable targeted search
CRITICAL RISKS: missing/double-counted rows, unknown values dropped, second filter engine, provenance loss, scoring
BASELINE GATES TO KEEP: full regression, Ruff, diff check, existing required hosted jobs
WP-SPECIFIC GATES REQUIRED: location/budget/selection reconciliation, request validation, MI-1 evaluator reuse, deterministic ordering
GATES NOT REQUIRED YET: persistence, GUI, human confirmation, export, Legal DOCX, AI, ranking
MAX JOB RUNTIME: 15 minutes
CI CHANGE REQUIRED BEFORE IMPLEMENTATION: NO
RATIONALE: pure in-memory contracts over the normalized MI-1 package universe.
```

## Baseline

- Base `main`: `63f5a9875ddbe377ec61b6184c6ec21f9134bb63`.
- MI-0 and MI-1 are merged into this base.
- Collection baseline: `380` tests, zero collection errors.

## What changed

- Added `DiscoverySnapshot` with province/city buckets retaining separate
  `CONFIRMED` and `INFERRED` counts plus explicit `NEEDS_REVIEW` population.
- Added mutually exclusive budget buckets: `<=100M`, `>100M..<=300M`,
  `>300M..<=500M`, `>500M..<=1B`, `>1B`, and `UNKNOWN_PRICE`.
- Added normalized selection-method counts plus explicit unsupported/unknown count.
- Added validated `TargetedSearchRequest`, complete per-row evaluations, matched
  hits, stable input ordering, and explicit examined/matched/nonmatched totals.
- Search converts the request into MI-1 `FilterProfile` and calls
  `evaluate_plan_package` once for every package. No second filter engine exists.

## Discovery contract and reconciliation

- Discovery counts `PlanPackage` rows, never unique PL bases; revisions and
  repeated rows under one plan/revision remain distinct.
- `resolved location + NEEDS_REVIEW = total_packages`.
- `all price buckets including UNKNOWN_PRICE = total_packages`.
- `known selection methods + unsupported/unknown = total_packages`.
- Invalid resolved-location identity and negative normalized price fail clearly.

## Search contract

- Supports min/max budget, province/city codes, include-ANY keywords,
  exclude-ANY keywords, and normalized selection methods.
- Negative budgets and `min > max` fail with `TargetedSearchValidationError`.
- Every input package receives one `FilterEvaluation`; no unknown value is
  pre-dropped. Results preserve the original `PlanPackage`, raw fields, and provenance.
- No score, ranking, confirmation, rejection, GO/HOLD/NO-GO, or business decision.

## Files changed

- `src/qi_crawler/market_intelligence/discovery.py`
- `src/qi_crawler/market_intelligence/search.py`
- `tests/test_khmt_discovery.py`
- `tests/test_khmt_search.py`
- `docs/KHMT_DATA_CONTRACT.md`
- `docs/agent_handoff/CURRENT.md`

## Verification

- Targeted MI-0/MI-1/MI-2: `96 passed`.
- Full local regression: `406 passed` in `258.07s`.
- Ruff: PASS; `git diff --check`: PASS.
- One pre-existing local pytest-cache permission warning; no failure.
- Tests cover empty input, row/revision preservation, all budget boundaries,
  location/method reconciliation, search validation/reasons/order/provenance,
  direct MI-1 evaluator reuse, and three synthetic Golden-shaped matches.

## Real Golden and safety

- `KHMT_19_8_2026.xlsx` was searched for under the user profile and was not found:
  `file_available = NO`; no real-Golden PASS or bucket counts are fabricated.
- Migration = NO; GUI = NO; runtime/user data modified = NO; real workbook modified = NO.
- No source row, DB, document, session, secret, or external data was committed.

## Known issues and explicitly NOT done

- Real Golden discovery/search acceptance remains pending until the workbook is
  available read-only on the Codex machine.
- No MI-3+, saved profile, persistence, GUI, Human Confirmation, confirmed Excel,
  Legal DOCX, watcher, API, AI, score, notification, or scheduled monitoring.

## Git state and next action

- Branch: `wp/mi-2-discovery-targeted-search`.
- Implementation head: `c025317334c71649177c0fdf4bbad222db632a7e`
  (`Add KHMT discovery and targeted search contract`).
- Push: implementation commit completed to the feature branch.
- Draft PR: [#27](https://github.com/tanntran2000/QI-Crawler-MVP/pull/27) to `main`.
- CI: natural PR run only; no manual rerun, workflow edit, or merge.
- Next: ChatGPT independent audit. Do not start MI-3 without authorization.
