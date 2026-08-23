# QI-Crawler Agent Handoff

## HANDOFF_ID

WP-MI-TBMT-02A — TBMT Opportunity Contract + Workbook Adapter

## Status

ACTIVE PARENT WP / MICRO-WP 02A-3 AUDITED + REMOTE-CHECKPOINTED /
READY FOR 02A-4 / NO PR / NO FEATURE-BRANCH CI /
HOSTED CI INFRASTRUCTURE UNAVAILABLE / NO OFFICIAL RELEASE

## Active machine-readable checkpoint

```text
ACTIVE_PARENT_WP = WP-MI-TBMT-02A
ACTIVE_BRANCH = wp/mi-tbmt-02a
MAIN_BASE = a4163e96816becbb2ce0c7009ecb9a2c9c832119

LAST_AUDITED_MICRO_WP = 02A-3
LAST_AUDITED_CODE_HEAD = 513ebbd6437ee2afbb02d91f6fd0975de70c773e
LAST_AUDIT = LOCAL_AUDIT_PASS
REMOTE_CHECKPOINT = 513ebbd6437ee2afbb02d91f6fd0975de70c773e

PR_STATE = NONE
FEATURE_CHECKPOINT_CI = NOT_TRIGGERED
HOSTED_CI_STATE = INFRASTRUCTURE_UNAVAILABLE

NEXT_MICRO_WP = 02A-4
NEXT_AUTHORITY = APPROVED_UNDER_PARENT_LEASE
STOP_STATE = READY_FOR_NEXT_MICRO_WP
```

A docs-only handoff/governance commit may make live branch `HEAD` newer than
`LAST_AUDITED_CODE_HEAD`. That does **not** create a new audited code head. A
new agent must verify live Git/GitHub and prove that
`513ebbd6437ee2afbb02d91f6fd0975de70c773e` remains an ancestor before writing
or executing the next Work Order.

## Main truth at Parent-WP entry

- `main` is `a4163e96816becbb2ce0c7009ecb9a2c9c832119`.
- `WP-GOV-LSI-01` is merged and Local Staged Integration is active governance.
- `WP-MI-SRC-01` source routing is merged; TBMT recognition must not route into
  the KHMT importer.
- Runtime/package version remains `0.8.0`.
- Full TBMT Bid Radar review/export/GUI support remains NOT implemented.
- Official Team Bid release remains blocked while retro-CI debt is open.

## Parent WP architecture

`WP-MI-TBMT-02` is intentionally split. Current Parent WP `02A` owns the
source-backed TBMT opportunity contract and workbook-adapter boundary only.

Planned 02A slices:

```text
02A-1 Source-neutral Opportunity identity/candidate contract
02A-2 TBMT schema + IB parser/normalization
02A-3 TBMT workbook importer → OpportunityCandidate
02A-4 real-file/read-only acceptance + cumulative Parent Integration Gate
```

Future Parent `02B` owns Bid Radar integration concerns such as generalized
filter/search, review persistence/migration, confirmed export, and GUI wiring.
Those concerns are not authorized in 02A unless a later Human-approved Work
Order changes scope.

## Completed and audited slices

### 02A-1 — Source-Neutral Opportunity Identity & Candidate Contract

Audited code introduced an import-free opportunity contract with separate:

- `OpportunitySourceType`: `KHMT` / `TBMT`;
- `OpportunityIdentityNamespace`: `PL` / `IB`;
- source-backed `OpportunityIdentity`;
- `OpportunityImportBatch`;
- `OpportunityCandidate`.

Hard invariants include:

```text
PL != IB
KHMT → PL only
TBMT → IB only
no PL↔IB conversion
raw/base/revision consistency
source_row > 0
valid source SHA-256
candidate provenance source_sha256/sheet/source_row must match authority
```

A forward correction was required to make candidate provenance fail closed.
The audited 02A-1 checkpoint is ancestor history and must not be rewritten.

### 02A-2 — TBMT Schema + IB Identity Parser / Normalization

Audited code head:

`6cae3ed7bc0c7fff26edab0e92a6a4482567fe3a`

Implemented the exact observed 18-column TBMT schema, conservative header/text
normalization, and fail-closed embedded revisioned IB identity parsing.
Important retained behavior includes preserving raw source identity text,
keeping TBMT-specific fields distinct, retaining unexplained values such as
`23`, and rejecting ambiguous/malformed identity-like tokens.

### 02A-3 — TBMT Workbook Importer → OpportunityCandidate

Final audited code head and remote checkpoint:

`513ebbd6437ee2afbb02d91f6fd0975de70c773e`

Implemented:

- bounded read-only `.xlsx` TBMT importer with header scanning up to row 50;
- `OpportunityImportBatch(source_type=TBMT)` with file SHA-256/sheet/time/schema
  provenance;
- source-backed `OpportunityCandidate` construction using IB identity only;
- exact source-row provenance through `source_sha256`, `sheet`, and
  `source_row`;
- preservation of full TBMT `raw_fields`, including TBMT-only schedule,
  guarantee, issue-location, bidder-address, and selection fields;
- conservative TBMT package-price parsing with invalid non-empty prices
  recorded as issues instead of coerced to zero;
- fail-closed handling for empty package names, malformed/multiple/mixed IB/PL
  identity evidence, missing/duplicate headers, unsupported workbooks, and
  missing sheets;
- no silent source-row deduplication;
- no mapping of `ĐỊA CHỈ BÊN MỜI THẦU` or `ĐỊA ĐIỂM PHÁT HÀNH` to generic
  execution location semantics.

02A-3 explicitly did **not** add DB persistence, review, filtering, confirmed
export, GUI wiring, source-routing changes, or `PlanPackage` reuse.

Local Machine Verifier evidence reported for 02A-3:

```text
focused importer + normalization: 31 passed
adjacent regression: 73 passed
full regression: 526 passed, 0 failed, 0 collection errors
Ruff: PASS
Diff check: PASS
collection: 526, 0 errors
Tree: clean
audited-code ancestry: PASS / exit 0
```

Independent audit result:

```text
LOCAL_AUDIT_PASS
```

Remote checkpoint was verified at the same code SHA. No PR existed and no
feature-checkpoint CI run was triggered.

## Next authorized slice — 02A-4

02A-4 is the final Parent-WP slice and owns two bounded responsibilities:

```text
1. Real TBMT workbook acceptance in strictly read-only mode.
2. Cumulative Parent Integration Gate for WP-MI-TBMT-02A.
```

The Work Order must require `HANDOFF_READINESS = PROMPT_READY` before execution
and explicitly authorize only read-only access to the protected real TBMT
workbook required for acceptance. No real workbook mutation, rewrite, rename,
move, normalization, or derived overwrite is authorized.

Acceptance must verify, at minimum:

- the real TBMT workbook schema/header row is recognized through the audited
  TBMT importer;
- real IB identities remain source-backed and preserve raw identity text;
- candidate/import-batch provenance refers to the exact real source SHA,
  sheet, and row;
- importer issues are reported as evidence rather than silently repaired;
- source file hash/size remain unchanged before and after acceptance;
- `PL != IB` and TBMT does not enter the KHMT `PlanPackage` path;
- cumulative targeted regression plus full pytest, Ruff, diff-check, collection
  integrity, cumulative CodeGraph impact review, and clean-tree evidence;
- relevant docs/handoff/changelog consistency is reviewed before Parent-WP
  delivery.

02A-4 must not generalize `CandidateReviewEvent`, add persistence/migrations,
change confirmed export, wire Bid Radar GUI, or publish a release. Those remain
outside Parent 02A.

After 02A-4 local verification, the Single Writer must return a Parent
Integration review packet and stop for independent final local audit. Draft PR
creation is not authorized until that audit passes and the Human/Work Order
allows the Parent integration step.

## Active operating contract

Required read-in:

- `AGENTS.md`
- `docs/agent/MEMORY_INDEX.md`
- `docs/agent/OPERATING_MODEL.md`
- `docs/agent/HUMAN_COLLABORATION.md`
- `docs/agent/LOCAL_STAGED_INTEGRATION.md`
- `docs/agent/PROJECT_MEMORY.md`
- this `CURRENT.md`
- live Git and relevant live GitHub state.

A prompt writer must resolve the active Parent WP, last audited code head, live
branch head, next micro-WP, and authority before returning `PROMPT_READY`.

## Hosted CI / retro-CI state

The last hosted matrix known to have actually executed and passed before the
account blocker remains run `32620166882`.

Subsequent affected runs were prevented from starting by the GitHub account
billing/spending-limit condition and must not be described as product-test
failures.

```text
CI_WAIVER = ACTIVE
HOSTED_CI = INFRASTRUCTURE_UNAVAILABLE
PENDING_RETRO_CI = YES
OFFICIAL_TEAM_BID_RELEASE = BLOCKED
```

The retro-CI recovery range begins with the first main change not fully covered
by executable hosted CI and will extend through then-current `main` at recovery
time. Only `CI_RECOVERY_PASS` closes that debt.

## Data safety

- Protected business workbooks remain read-only unless a Work Order explicitly
  authorizes bounded read-only acceptance.
- No production DB migration/downgrade/stamp/repair is authorized by this
  handoff.
- `%LOCALAPPDATA%\QI-Crawler` must not be deleted or mutated without an explicit
  authorized Work Order.
- Unknown backup/release artifacts remain KEEP.
- v0.8.0 approved Team Bid release artifacts remain immutable known-good
  baseline artifacts.

## Delivery authority

This file is the active snapshot, not an alternative source of Git truth. The
next agent must reconcile it against live Git/GitHub. If the branch, audited
code head ancestry, PR state, or authority does not reconcile, return
`ENTRY_HOLD` rather than inferring continuation from chat history.
