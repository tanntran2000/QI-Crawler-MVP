HISTORICAL / NON-NORMATIVE / MAY CONTAIN SUPERSEDED RULES.

Preserved as a historical snapshot; consult CURRENT.md and live Git/GitHub for
active authority.

# QI-Crawler Agent Handoff

## HANDOFF_ID

WP-GOV-LSI-01 — Local Staged Integration + Remote Checkpoint Contract

## Status

MERGED / ACTIVE GOVERNANCE / HOSTED CI INFRASTRUCTURE UNAVAILABLE /
PENDING RETRO-CI / NO OFFICIAL RELEASE

## Mission

Use `Local Staged Integration + Remote Checkpoint + Parent-WP CI` as the
default development operating contract while preserving constitutional laws,
role separation, Human merge/release authority, and the existing GitHub CI
workflow.

## Current main truth

- WP-GOV-LSI-01 merged through PR #45.
- Governance merge commit:
  `6e8206f469497c4c073ee6030455b1db946f3479`.
- PR #44 / WP-MI-SRC-01 remains merged at
  `fc4d68cbeb9e5f27a91039e264e3906d1ee8f1c7`.
- `MEM-006` is ACTIVE merged source-routing truth.
- `MEM-007` is ACTIVE Local Staged Integration governance truth.
- Package/runtime version remains `0.8.0`; governance changes do not alter the
  approved Team Bid v0.8.0 release identity.
- Full TBMT Bid Radar candidate/review/export support is still NOT implemented.

## Active operating contract

Detailed procedure:

`docs/agent/LOCAL_STAGED_INTEGRATION.md`

Default flow:

```text
Human approves Parent WP
→ Planner decomposes bounded micro-WPs
→ one Single Writer implements one micro-WP
→ local Machine Verifier evidence
→ local commit
→ LOCAL_REVIEW_PACKET
→ STOP_FOR_INDEPENDENT_LOCAL_AUDIT
→ independent Reviewer PASS/HOLD/FAIL
→ PASS: remote feature-branch checkpoint without PR
→ next micro-WP
→ Parent Integration Gate
→ Draft PR
→ hosted CI when available
→ exact-head independent audit
→ Human merge
```

Key rules:

- Reviewer/Auditor remains independent from runtime Machine Verifier authority.
- Feature-branch push without an open PR is a remote backup/checkpoint, not CI
  evidence.
- Audited commits use commit freeze by default; later corrections use explicit
  forward-correction commits.
- Parent WP target size is 4–6 audited slices; growth beyond six meaningful
  slices or multiple major architecture/migration boundaries triggers
  `SPLIT_REVIEW_REQUIRED`.
- `LOCAL_REVIEW_PACKET` requires base/head SHA, changed-file evidence, bounded
  patch, CodeGraph radii where applicable, exact verification commands/results
  with exit codes, collection state, migration/data-safety state, known risks,
  and tree status.
- Before PR, Parent Integration Gate performs the cumulative verification and
  independent final local audit required by the active Work Order.

## Hosted CI state

- Last GitHub Actions run that actually executed the full PR matrix before the
  billing block: run `32620166882`; all 4 required jobs passed.
- That run covered source head
  `958e52a79c77f1b38128662135f6acbe2588752d` through PR merge ref
  `7bde89510b911cbb3d336b9c02a5574dd82cab01`.
- Final PR #44 docs-only amendment and later PR/main runs were prevented from
  starting by the GitHub account billing/spending-limit condition.
- PR #45 run `32629725161` also failed before execution; all four jobs had
  `steps = null`.
- Classification remains `CI_INFRASTRUCTURE_DEFECT` /
  `HOSTED_CI = INFRASTRUCTURE_UNAVAILABLE`, not product-test failure.

## Temporary CI waiver

```text
CI_WAIVER = ACTIVE
WAIVER_REASON = GitHub Actions billing/spending-limit prevents jobs starting
LOCAL_VERIFICATION = mandatory for code changes
INDEPENDENT_AUDIT = mandatory
HUMAN_MERGE_APPROVAL = mandatory
PENDING_RETRO_CI = YES
```

Do not report hosted `CI PASS` while this condition exists.

## Retro-CI ledger

Use a range instead of a self-referential list of every docs-only handoff
commit:

```text
RETRO_CI_RANGE_START = first main change not fully covered by executable hosted CI
RETRO_CI_RANGE_END = current main at recovery time
STATUS = PENDING_RETRO_CI
```

Known affected main history begins with the PR #44 final merge at
`fc4d68cbeb9e5f27a91039e264e3906d1ee8f1c7` and includes WP-GOV-LSI-01.
Any later Human-approved merge while the waiver is active automatically joins
the same open recovery range.

When hosted CI returns, create a bounded CI Recovery WP that verifies the
complete range through then-current `main`. Only `CI_RECOVERY_PASS` closes the
retro-CI debt.

## Release gate

While retro-CI debt is open:

```text
OFFICIAL TEAM BID RELEASE = BLOCKED
```

Do not create an official version tag, GitHub Release, publish
`Crawler tool\Current`, publish Team Bid Reference, or publish an official
installer release unless the Human later approves a separate bounded release
exception.

Development, local verification, remote feature checkpoints, Draft PRs, and
Human-approved merges may continue under the waiver.

## Data safety

- No production `%LOCALAPPDATA%\QI-Crawler` mutation is authorized by this
  governance state.
- Business workbooks remain read-only unless a future Work Order explicitly
  authorizes a safe derived operation.
- Unknown backup/release artifacts remain KEEP.
- No production DB migration/downgrade/stamp/repair is authorized without an
  explicit Work Order and Human authority.

## Next product objective

Design the next Market Intelligence Parent WP for full TBMT/IB Bid Radar
intake. Do not fake TBMT as KHMT `PlanPackage` data. Preserve:

```text
PL != IB
FILTER MATCH != HUMAN CONFIRMED
SQLite/review history = source of record
XLSX/DOCX = derived outputs
```

Before implementation, decompose the TBMT architecture into bounded audited
slices and trigger `SPLIT_REVIEW_REQUIRED` if the Parent WP grows beyond a
safe integration boundary.

## Delivery authority

This handoff describes durable operating state; live Git/GitHub remains the
authority for the exact current main SHA. Future Work Orders must read this
handoff plus `PROJECT_MEMORY.md`, `AGENTS.md`, and the Local Staged Integration
contract before execution.
