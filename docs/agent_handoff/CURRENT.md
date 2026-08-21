# QI-Crawler Agent Handoff

## Current task — GOVERNANCE-RECONCILE-1

### Status

LOCAL PASS / NATURAL CI IN PROGRESS / NO MERGE.

### CI Fitness Contract

```text
CURRENT WP: GOVERNANCE-RECONCILE-1
CAPABILITY UNDER CHANGE: governance and handoff documentation only
CRITICAL RISKS: stale CI policy or branch history causing incorrect merge decisions
BASELINE GATES TO KEEP: canonical main, unchanged CI commands, full regression, Ruff, diff check
WP-SPECIFIC GATES REQUIRED: current finite adaptive budgets and accurate MI handoff
GATES NOT REQUIRED YET: production changes, test changes, dependency changes, workflow command changes
MAX JOB RUNTIME: finite, job-specific; current maximum is 25 minutes for Windows Python 3.12
CI CHANGE REQUIRED BEFORE IMPLEMENTATION: NO
RATIONALE: `.github/workflows/ci.yml` already contains the approved adaptive budgets.
```

### Baseline and execution discipline

- Canonical `main` HEAD/origin: `2546155685202abd8d0bae7bd3447651f4d8745b`.
- PR #32 (`ci/adaptive-runtime-budget`) is merged; one canonical `main` is authoritative.
- MI-0 through MI-4 are merged into `main`; no feature branch should be treated as canonical.
- Baseline collection: `430`; this WP changes governance documents only.
- `.codegraph/` is local-only tooling state and must never be committed.

### Implemented locally

- Removed the stale universal 15-minute CI rule from `AGENTS.md`.
- Recorded the canonical adaptive budgets: Quality 10m, Ubuntu 3.12 20m,
  Windows 3.12 25m, Ubuntu 3.11 20m.
- Refreshed this handoff to match merged main and the next MI sequence.
- PR #13 and PR #18 are stale and must not be merged as-is.

### Verification and next action

- Required local gates: pytest, Ruff, diff check, and diff name-status.
- Next roadmap: MI-5 Legal DOCX → MI-6 GUI → Real Golden validation.
- No production code, tests, migrations, dependencies, business data, plugins, or CI commands changed.
- One short-lived governance branch and one Draft PR only; do not merge.

---

## Previous completed task — WP-MI-4 Confirmed Package Excel Export (MERGED)

### CI Fitness Contract

```text
CURRENT WP: MI-4 Confirmed Package Excel Export
CAPABILITY UNDER CHANGE: derived XLSX export of MI-3 current human-confirmed candidates
CRITICAL RISKS: stale confirmation export, unreviewed/rejected row leakage,
  source-order/provenance loss, identity dedup regression, database mutation
BASELINE GATES TO KEEP: full regression, Ruff, diff check, Alembic single head
WP-SPECIFIC GATES REQUIRED: latest-state confirmed-only export, exact 13 source
  columns, audit provenance, deterministic ordering, XLSX round-trip, DB immutability
GATES NOT REQUIRED YET: Legal DOCX, GUI, AI, scoring, GO/HOLD/NO-GO
MAX JOB RUNTIME: finite, job-specific; current canonical maximum is 25 minutes for Windows Python 3.12
CI CHANGE REQUIRED BEFORE IMPLEMENTATION: NO
RATIONALE: bounded derived export consuming the already-approved MI-3 read contract.
```

### Baseline and execution discipline

- Isolated worktree: `egp-crawler-python-mi4`.
- Branch: `wp/mi-4-confirmed-package-excel-export`.
- Exact base main: `b7be77214ae1885bb43e66c19407c5cccbd23db9` (MI-3 merged).
- Baseline collection: `423`; MI-3 targeted baseline: `16 passed`.
- CodeGraph was freshly initialized/synchronized at the exact checkout. The impact
  radius includes MI-3 current-state review and Excel conventions; the edit radius
  is limited to a new MI exporter, its tests, and this handoff.
- No MI-5 consumer exists yet; the new exporter is the bounded future input boundary.
- TDD evidence: the new targeted suite first failed on the missing exporter module,
  then passed after the minimal implementation.
- Systematic debugging was not needed after baseline sync.
- Verification-before-completion and internal review executed. The review's formula
  injection finding was fixed by reusing the canonical Excel sanitizer for both
  source and audit cells; focused RED/GREEN coverage was added.

### Implemented locally

- Added `export_confirmed_packages()` as a read-only derived XLSX boundary.
- It consumes `CandidateReviewService.current_confirmed()` directly; no second
  confirmation/filter engine exists.
- The first 13 columns are `OBSERVED_KHMT_HEADERS` in source order; missing raw
  values remain blank and formula-like source strings are written as safe text.
- Audit columns retain decision, reviewer, event ID/time, source filename/SHA,
  sheet/row, plan base ID, and revision.
- Rows sort deterministically by exact source identity and remain independent by
  SHA, sheet, source row, raw plan identity, and review event.

### Identity/history contract

- Only the latest `CONFIRMED` event exports. `UNREVIEWED`, `REJECTED`, and
  `NEEDS_REVIEW` never export.
- Historical `CONFIRMED -> REJECTED` disappears on the next export.
- Same SHA under a renamed source file reattaches; changed SHA remains unreviewed.
- Exact duplicate input appears once; revisions and source rows stay independent.
- Export/reopen does not mutate `PlanPackage`, event history, or the database.

### Schema, Golden checks and verification

- Migration/schema change: NONE.
- Intended files: `src/qi_crawler/market_intelligence/confirmed_package_export.py`,
  `tests/test_confirmed_package_export.py`, and this handoff.
- Collection after implementation: `430`; no decrease or collection error.
- MI-3 + MI-4 targeted: `23 passed`.
- Synthetic Golden: three human-confirmed rows export/reopen with exact headers and
  provenance; rejecting one yields exactly two on the next export.
- Real Golden: `NOT EXECUTED / FILE UNAVAILABLE`; the unrelated TBMT workbook was
  not substituted.
- Full regression: `430 passed`.
- Full Ruff: PASS; diff check: PASS.

### Safety, known issues and next action

- Runtime/user database, documents, sessions, cookies and secrets: NOT MODIFIED.
- Real KHMT workbook: NOT MODIFIED / unavailable. Existing `TBMT_19_8_2026.xlsx`
  and old `.gitignore` change remain untouched.
- `.codegraph/` is local untracked tool state and must not be committed.
- Draft PR: `#31` (`Add confirmed package Excel export`) to `main`; natural
  exact-head CI is pending and has not been manually rerun.
- Known issue: historical Windows runtime variance remains governed by LAW8.
- Explicitly not done: MI-5 Legal DOCX, MI-6 GUI, AI,
  ranking/scoring, GO/HOLD/NO-GO, and PL→IB linking.
- Commit/push: bounded implementation is on the feature branch; `main` untouched.
- Next action: allow natural CI, then ChatGPT independent audit. NO MERGE.

---

## Historical MI-2 handoff

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
MAX JOB RUNTIME: finite, job-specific; current canonical maximum is 25 minutes for Windows Python 3.12
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
