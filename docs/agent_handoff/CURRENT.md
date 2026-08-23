# QI-Crawler Agent Handoff

## HANDOFF_ID

WP-GOV-LSI-01 — Local Staged Integration + Remote Checkpoint Contract

## Status

GOVERNANCE DOCS IMPLEMENTED / PARENT INTEGRATION REVIEW ACTIVE /
HOSTED CI INFRASTRUCTURE UNAVAILABLE / NO OFFICIAL RELEASE

## Mission

Make `Local Staged Integration + Remote Checkpoint + Parent-WP CI` the default
development operating contract while preserving existing constitutional laws,
role separation, Human merge/release authority, and the existing GitHub CI
workflow.

## Current verified state

- Main baseline at entry: `fc4d68cbeb9e5f27a91039e264e3906d1ee8f1c7`.
- Active branch: `wp/gov-lsi-01`.
- PR #44 / WP-MI-SRC-01 is merged; `main` includes SA Excel source routing,
  named Human source correction, append-only source-type Ground Truth, and the
  TBMT→KHMT routing guard.
- Full TBMT Bid Radar candidate/review/export support remains NOT implemented.
- Package/runtime version remains `0.8.0`; this governance WP has no release or
  version impact.
- The approved Team Bid v0.8.0 release remains the immutable known-good release
  identity. No release artifact is modified by this WP.

## Hosted CI state

- Last GitHub Actions run that actually executed the full PR matrix for the
  source-routing implementation: run `32620166882`; all 4 required jobs passed.
- That run used source head
  `958e52a79c77f1b38128662135f6acbe2588752d` and PR merge ref
  `7bde89510b911cbb3d336b9c02a5574dd82cab01`.
- Final PR #44 docs-only amendment head:
  `5cd5e23138df4f71060f036aef8faa8d800c5e26`.
- Subsequent Actions runs were prevented from starting by the GitHub account
  billing/spending-limit condition; affected jobs had no execution steps.
- Classification: `CI_INFRASTRUCTURE_DEFECT` /
  `HOSTED_CI = INFRASTRUCTURE_UNAVAILABLE`, not a product-test failure.
- PR #44 merge commit `fc4d68cbeb9e5f27a91039e264e3906d1ee8f1c7`
  therefore remains `PENDING_RETRO_CI = YES` until CI Recovery passes.

## Implemented governance contract

- Detailed procedure: `docs/agent/LOCAL_STAGED_INTEGRATION.md`.
- Human approves a bounded Parent WP; Planner decomposes it into auditable
  micro-WPs.
- One `BUILDER_SINGLE_WRITER` implements one micro-WP at a time.
- Local machine execution supplies Machine Verifier evidence.
- Every micro-WP ends with `LOCAL_REVIEW_PACKET` and
  `STOP_FOR_INDEPENDENT_LOCAL_AUDIT`.
- Reviewer returns `LOCAL_AUDIT_PASS`, `LOCAL_AUDIT_HOLD`, or
  `LOCAL_AUDIT_FAIL` and remains separate from runtime verification.
- After `LOCAL_AUDIT_PASS`, an audited feature-branch commit may be pushed as a
  remote checkpoint without opening a PR; that push is not CI evidence.
- Audited commits are frozen by default; later corrections use explicit
  forward-correction commits.
- Parent WP target size is 4–6 audited slices; growth beyond six or multiple
  major architecture/migration boundaries triggers `SPLIT_REVIEW_REQUIRED`.
- Before PR, the Parent Integration Gate performs cumulative verification,
  cumulative impact review, and final local audit.
- Hosted-CI waiver may be used only for verified infrastructure/account
  inability to start jobs. It never converts into `CI PASS`.
- Every Human-approved merge under the waiver accrues
  `PENDING_RETRO_CI = YES`.
- `PENDING_RETRO_CI > 0` blocks official Team Bid release/publish unless Human
  later approves a separate bounded release exception.

## Files in WP-GOV-LSI-01

- `AGENTS.md`
- `docs/agent/LOCAL_STAGED_INTEGRATION.md`
- `docs/agent/OPERATING_MODEL.md`
- `docs/agent/HUMAN_COLLABORATION.md`
- `docs/agent/PROJECT_MEMORY.md`
- `docs/agent_handoff/CURRENT.md`
- `docs/superpowers/specs/2026-08-23-local-staged-integration-design.md`
- `docs/superpowers/plans/2026-08-23-local-staged-integration.md`

## Parent Integration evidence

- GitHub compare against entry baseline confirms the WP is Markdown/governance
  only before this handoff update.
- No `src/`, `tests/`, `alembic/`, packaging, release script, version, business
  workbook, or `.github/workflows/ci.yml` change belongs to this WP.
- Runtime pytest/Ruff are not claimed by this docs-only WP; no runtime code was
  changed. Changed-file scope and governance invariants require independent
  review before merge.
- `MEM-006` is normalized from stale branch-only wording to ACTIVE merged truth
  at PR #44 merge commit.
- `MEM-007` records the Local Staged Integration contract in post-merge-valid
  form.

## Data safety

- No production `%LOCALAPPDATA%\QI-Crawler` data was accessed or modified.
- No business workbook was accessed or modified.
- No database migration, downgrade, stamp, repair, or schema mutation occurs.
- No release build, installer, tag, GitHub Release, `Crawler tool\Current`, or
  Team Bid Reference action occurs.

## CI waiver / retro-CI ledger

```text
CI_WAIVER = ACTIVE
WAIVER_REASON = GitHub Actions billing/spending-limit prevents jobs starting

PENDING_RETRO_CI:
- WP-MI-SRC-01 / main merge fc4d68cbeb9e5f27a91039e264e3906d1ee8f1c7
- WP-GOV-LSI-01 / add after Human-approved merge
```

When hosted CI returns, create a bounded CI Recovery WP covering the complete
waiver range and do not release officially until `CI_RECOVERY_PASS` closes the
ledger.

## Explicitly NOT done

- No full TBMT/IB Bid Radar intake.
- No product code or test behavior change.
- No CI workflow modification.
- No release/version change.
- No official publish.

## Next objective

After WP-GOV-LSI-01 is independently audited and merged, use this contract to
design and execute the next Market Intelligence Parent WP for full TBMT/IB Bid
Radar intake. Decompose that work before implementation and apply
`SPLIT_REVIEW_REQUIRED` if the architectural boundary becomes too broad.

## Delivery rule

This handoff is tracked evidence, not a substitute for live Git/GitHub state.
Use the live branch/commit as exact-head authority. Do not claim hosted CI PASS
while the billing/spending-limit infrastructure blocker remains active.
