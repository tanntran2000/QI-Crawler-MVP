# QI-Crawler Agent Handoff

## Current task — Windows Release Publish / Crawler tool

### Status

LOCAL PASS — release mechanics implemented and verified; no real
`Crawler tool\\Current` publish performed on this feature branch. Commit/push/PR
are pending final handoff.

### Contract and evidence

- Base/main before work: `3f847f366f7070f5224d572108cdab523976970f`.
- Branch: `wp/windows-crawler-tool-publish`.
- CodeGraph status/sync: index up to date; packaging/build/standalone impact
  reviewed; `.codegraph/` remains local-only.
- Collection baseline: `448` tests; final collection: `452` tests.
- Targeted packaging/standalone tests: `10 passed`.
- Full regression: `452 passed` (no failures or collection errors).
- Ruff: PASS; `git diff --check`: PASS.
- Fresh build cleans only allowlisted generated `build` and `dist\\QI-Crawler`
  paths and refuses tracked/out-of-root targets.
- `build_installer.ps1` performs onedir build, EXE verification, installer
  build, isolated `--smoke-test-documents`, then publishes only with `-Publish`.
- Publish requires clean `main`; candidate staging is validated before rotating
  `Current` to `Previous` and candidate to `Current`.
- Temporary publish behavior test verified `Current/Previous` rotation,
  `BUILD_INFO.txt` metadata and preservation of the old `Current` after an
  incomplete candidate. Real `Crawler tool\\Current` was not touched.

### Files changed

- `build_windows.ps1`
- `build_installer.ps1`
- `scripts/publish_windows_release.ps1`
- `tests/test_windows_installer.py`
- `docs/BUILD_WINDOWS_STANDALONE.md`
- `docs/agent_handoff/CURRENT.md`

### Explicitly not done

- No version bump (remains `0.7.1`), production/business/GUI/DB/MI changes,
  installer release, real publish, merge or manual CI rerun.

### Next action

Commit bounded changes, push this branch, create one Draft PR, allow natural CI,
then stop for human/ChatGPT audit. NO MERGE.

## Current task — Real Golden Team Bid Acceptance (MI-1..MI-5)

### Status

REAL GOLDEN PHASE C PASS / HUMAN DECISIONS RECORDED / NO MERGE.

### Source and Phase A evidence

- Source workbook (read-only):
  `C:\Users\Admin\Desktop\QI Technology\QI Crawler\business-data\KHMT_19_8_2026.xlsx`.
- SHA-256 before and after: `B86AF73085B639E336CA6131D72A121268B48F7989B3A70E6417020A90AF58EC`;
  unchanged.
- Sheet: `Bản tin điện tử`; source rows/imported packages: `413`.
- Import issues: `UNSUPPORTED_SELECTION_METHOD` on 12 rows and `INVALID_PRICE`
  on row 36; no rows were dropped from the read-only Golden run.
- Existing MI search preset: budget `0..500,000,000`, canonical province/city
  code `HCM`, no include/exclude keywords, no selection-method restriction.
  Search examined `413`, matched `9`, nonmatched `404`.

### Human authority and Phase C evidence

- Reviewer: `Team Bid`; exactly 9 events recorded in an isolated temporary
  acceptance DB: 3 `CONFIRMED`, 6 `NEEDS_REVIEW`, 0 `REJECTED`.
- Current confirmed identities: `PL2600263838-00` row 70,
  `PL2600263840-00` row 74, and `PL2600265077-00` row 366.
- Confirmed XLSX: `CÁC GÓI ĐÃ XÁC NHẬN.xlsx`; reopened with exactly 3 rows and
  the three confirmed PL/revision/source-row identities.
- Legal DOCX: `ThongTin_PL2600263838.docx`, `ThongTin_PL2600263840.docx`,
  `ThongTin_PL2600265077.docx`; all reopened with the existing 15-field
  contract and no cross-package contamination.
- Review event count before and after both exports: `9` → `9`; exports did not
  mutate review history or the acceptance DB. All six `NEEDS_REVIEW` packages
  were absent from both outputs.
- Generated artifacts and acceptance DB are outside the repository under the
  temporary root `C:\Users\Admin\AppData\Local\Temp\qi-real-golden-mnd424y7`;
  no business data/output was added to Git.

### Verification

- Targeted MI + GUI: `93 passed` (one non-blocking pytest cache permission warning).
- Full regression: `448 passed` (one non-blocking pytest cache permission warning),
  using a short external Windows basetemp.
- Ruff and diff checks are run after this handoff update; no production/schema/
  dependency changes are part of this acceptance.

## Current task — WP-MI-6 source-identity hardening

### Status

LOCAL PASS / NATURAL CI IN PROGRESS / NO MERGE.

### Scope and contracts

- Bid Radar remains a thin GUI/service integration over MI-1 import/search,
  MI-3 human review, MI-4 XLSX export and MI-5 Legal DOCX.
- Selecting a different KHMT source clears the loaded package universe and
  blocks derived exports until the new source imports successfully.
- A successful KHMT import retains the existing source SHA-256 contract. Before
  XLSX or Legal DOCX export, the current file is re-hashed; content changed at
  the same path clears stale Bid Radar state and requires re-import.
- Import issues show code, source row when available, and a user-readable message.
- Expected MI validation/import/review/export errors are mapped to safe Vietnamese
  messages; unexpected exceptions remain generic and redacted in the UI.
- No MI authority, schema, dependency, CI, crawler, extraction or business-data change.

### CodeGraph and verification evidence

- `codegraph sync .` and `codegraph status .`: index up to date (140 files,
  2,946 nodes, 8,061 edges).
- MCP `mcp__codegraph__codegraph_explore` succeeded for the Bid Radar GUI/service
  flow and for `_build_bid_radar_page`, source selection, render, submit and
  worker-error paths. Impact radius: GUI → gui_services → MI-1..MI-5;
  edit radius: `gui.py`, `test_bid_radar_gui.py`, this handoff; test radius:
  Bid Radar, GUI and MI-1..MI-5 suites.
- TDD RED: the same-path content-change export test failed before the SHA guard;
  GREEN after the minimal patch.
- Targeted MI + GUI verification: `117 passed`.
- Final GUI verification: `62 passed`.
- Full regression: `448 passed` with a short Windows basetemp; Ruff: PASS;
  `git diff --check`: PASS.

### Git/PR/CI handoff

- Canonical main base: `2daf4e16d7a3ef7e7bdcda48e1b36faf18bdc750`.
- Branch: `wp/mi-6-bid-radar-gui`; Draft PR #36:
  `https://github.com/tanntran2000/QI-Crawler-MVP/pull/36`.
- Amendment implementation head: `e515cad` (`Harden Bid Radar source switching and errors`).
- Source-identity hardening commit: `ac9330b9edbe3ea3dd4de767d54255c4e874aa31`.
- Natural exact-head CI run `32510703090` is in progress; no manual rerun and no
  merge.
- No merge and no manual CI rerun. Natural exact-head CI evidence will be
  recorded after push.

---

## Previous completed task — WP-MI-5 Legal DOCX Generator

### Status

LOCAL PASS / NATURAL CI IN PROGRESS / NO MERGE.

### CI Fitness Contract

```text
CURRENT WP: WP-MI-5 Legal DOCX Generator
CAPABILITY UNDER CHANGE: read-only DOCX derived from latest human CONFIRMED PlanPackage rows
CRITICAL RISKS: stale/rejected confirmation leakage, source-value loss, cross-package contamination, overwrite
BASELINE GATES TO KEEP: full regression, Ruff, diff check, unchanged MI-3/MI-4 contracts
WP-SPECIFIC GATES REQUIRED: current_confirmed-only eligibility, exact 15-field order, DOCX reopen/Unicode, collision failure, DB immutability
GATES NOT REQUIRED YET: GUI, CLI, migrations, AI, scoring, GO/HOLD/NO-GO, real golden unavailable
MAX JOB RUNTIME: finite, job-specific
CI CHANGE REQUIRED BEFORE IMPLEMENTATION: NO
RATIONALE: bounded derived output using the existing MI-3 review authority and MI-4 source contract.
```

### Baseline and execution discipline

- Canonical `main` base: `311f6fb763f4486830efeed8caa0df4b08ae3093`.
- MI-0 through MI-4 are merged into `main`; this WP is on `wp/mi-5-legal-docx`.
- Baseline collection: `430`; no unexpected collection decrease is allowed.
- `.codegraph/` is local-only tooling state and must never be committed.
- CodeGraph was initialized, synchronized, and status-verified in this checkout; MCP
  `codegraph_explore` succeeded for the MI-3 → MI-4/MI-5 flow. `.codegraph/` is local-only.
- Impact radius: `current_confirmed → ReviewedCandidate → PlanPackage →
  confirmed_package_export / legal_docx`; edit radius for this amendment is the MI-5 test only;
  test radius is `tests/test_legal_docx.py` plus the MI-3/MI-4 targeted suite.

### Implemented locally

- Added `market_intelligence/legal_docx.py`, consuming only
  `CandidateReviewService.current_confirmed()` and preserving source/raw values.
- DOCX output is `ThongTin_<PL_BASE>.docx` with the exact 15-field order;
  unsupported fields remain blank and existing targets fail without overwrite.
- Added focused MI-5 tests for latest confirmation state, rejection, Unicode,
  field order, revision isolation, collision handling, and DB/review immutability.
- Added the single allowed dependency `python-docx>=1.1,<2`; no schema migration.

### Verification and next action

- Targeted MI-3 + MI-4 + MI-5: `30 passed`.
- Full regression: `437 passed`; Ruff: PASS; `git diff --check`: PASS.
- Real Golden `ThongTin_PL*.docx`: `NOT EXECUTED / FILE UNAVAILABLE`; SOP DOCX was not substituted.
- No database migration, GUI/CLI wiring, business data, runtime data, or source documents changed.
- Latest commit: `e7cba6f156271254310cd3e231dcce50fde62693` (same PR collision regression).
- Push: completed on `wp/mi-5-legal-docx`; Draft PR #35 is open against `main`.
- Hosted CI: Code Quality, Ubuntu 3.12 and Ubuntu 3.11 PASS; Windows 3.12 PENDING.
  No manual rerun and no merge.

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
