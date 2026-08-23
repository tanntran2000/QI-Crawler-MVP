# QI-Crawler Agent Handoff

## HANDOFF_ID

WP-MI-TBMT-02A — TBMT Opportunity Contract + Workbook Adapter

## Status

ACTIVE PARENT WP / MICRO-WP 02A-2 AUDITED + REMOTE-CHECKPOINTED /
READY FOR 02A-3 / NO PR / NO FEATURE-BRANCH CI /
HOSTED CI INFRASTRUCTURE UNAVAILABLE / NO OFFICIAL RELEASE

## Active machine-readable checkpoint

```text
ACTIVE_PARENT_WP = WP-MI-TBMT-02A
ACTIVE_BRANCH = wp/mi-tbmt-02a
MAIN_BASE = a4163e96816becbb2ce0c7009ecb9a2c9c832119

LAST_AUDITED_MICRO_WP = 02A-2
LAST_AUDITED_CODE_HEAD = 6cae3ed7bc0c7fff26edab0e92a6a4482567fe3a
LAST_AUDIT = LOCAL_AUDIT_PASS
REMOTE_CHECKPOINT = 6cae3ed7bc0c7fff26edab0e92a6a4482567fe3a

PR_STATE = NONE
FEATURE_CHECKPOINT_CI = NOT_TRIGGERED
HOSTED_CI_STATE = INFRASTRUCTURE_UNAVAILABLE

NEXT_MICRO_WP = 02A-3
NEXT_AUTHORITY = APPROVED_UNDER_PARENT_LEASE
STOP_STATE = READY_FOR_NEXT_MICRO_WP
```

A docs-only handoff/governance commit may make live branch `HEAD` newer than
`LAST_AUDITED_CODE_HEAD`. That does **not** create a new audited code head. A
new agent must verify live Git/GitHub and prove that
`6cae3ed7bc0c7fff26edab0e92a6a4482567fe3a` remains an ancestor before writing
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
02A-4 real-file/read-only + cumulative Parent Integration Gate
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

Final audited code head:

`6cae3ed7bc0c7fff26edab0e92a6a4482567fe3a`

Implemented only four new files for:

- exact observed 18-column TBMT schema;
- conservative canonical header handling;
- conservative source text normalization;
- embedded revisioned IB identity parsing;
- fail-closed PL/mixed/multiple/malformed identity behavior.

Important retained behavior:

- source value `23` is preserved, not treated as garbage;
- `PHƯƠNG THỨC LỰA CHỌN NHÀ THẦU` and
  `HÌNH THỨC LỰA CHỌN NHÀ THẦU` remain distinct;
- guarantee/schedule/issue-location/contract-duration source fields are not
  collapsed into KHMT semantics;
- malformed extended token such as `IB2600463290-00-01` is rejected rather
  than accepting the valid-looking prefix.

Local Machine Verifier evidence reported for final 02A-2 correction:

```text
focused parser correction: 11 passed
adjacent regression: 53 passed
Ruff: PASS
Diff check: PASS
collection: 505 → 506, 0 errors
Tree: clean
```

Independent audit result:

```text
LOCAL_AUDIT_PASS
```

Remote checkpoint was verified at the same code SHA. No PR existed and no
feature-checkpoint CI run was triggered.

## Next authorized slice — 02A-3

Objective:

```text
TBMT XLSX workbook importer
→ exact source provenance
→ OpportunityImportBatch(source_type=TBMT)
→ OpportunityCandidate(identity_namespace=IB)
```

The 02A-3 Work Order must be generated only after `HANDOFF_READINESS` reaches
`PROMPT_READY` using `MEMORY_INDEX.md` and live Git/GitHub.

02A-3 must preserve these stop boundaries unless a new Human decision changes
scope:

- do not fake TBMT as KHMT `PlanPackage`;
- do not generalize `CandidateReviewEvent` yet;
- do not change confirmed export yet;
- do not add DB migration yet;
- do not wire Bid Radar GUI yet;
- real business workbook access remains read-only and belongs only where the
  Work Order explicitly authorizes it;
- no production `%LOCALAPPDATA%\QI-Crawler` mutation.

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

- Protected business workbooks remain read-only.
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
