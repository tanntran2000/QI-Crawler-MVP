# Project Memory — `main` Truth Only

Only facts already merged to `main` belong here. Proposals and unfinished
branches must remain in their Work Package handoff.

## MEM-001 — Canonical workspace

- **State:** ACTIVE
- **Since main commit:** `311f6fb`
- **Contract:** Work in the canonical `egp-crawler-python` checkout on one
  short-lived branch. Do not create Git worktrees, sibling clones, or WP
  folders. After an approved merge, return to `main`, fast-forward from
  `origin/main`, and delete the merged local branch.
- **Evidence:** merged workspace policy and `AGENTS.md`.
- **Last verified:** `07ef548ee3747efd617e131880368cedc52f3bfc`.

## MEM-002 — Market intelligence authority

- **State:** ACTIVE
- **Since main commit:** `3f847f3`
- **Contract:** MI-0 through MI-6 are merged and accepted. KHMT import,
  targeted search, human review, confirmed XLSX, Legal DOCX, and Bid Radar
  reuse their existing authority services. Filter match is never human
  confirmation; PL and IB remain separate namespaces.
- **Evidence:** merged MI work and Real Golden acceptance on `main`.
- **Last verified:** `07ef548ee3747efd617e131880368cedc52f3bfc`.

## MEM-003 — Managed document storage boundary

- **State:** ACTIVE
- **Since main commit:** `74cab1c`
- **Contract:** The managed Document Store preserves original bytes,
  content SHA/version, tender identity, and bundle membership. Filename/path
  is metadata, not identity. Vault/Shelf/Recovery/cold-archive work is **not**
  claimed complete.
- **Evidence:** merged document-intake and bundle-guard tests.
- **Last verified:** `07ef548ee3747efd617e131880368cedc52f3bfc`.

## MEM-004 — Source of record and derived outputs

- **State:** ACTIVE
- **Since main commit:** `5592c9c`
- **Contract:** SQLite/review history is authoritative. XLSX/DOCX reports
  are derived outputs and must not mutate source packages or review history.
  `FILTER MATCH != HUMAN CONFIRMED`.
- **Evidence:** MI-3/MI-4/MI-5 regression suites and Real Golden evidence.
- **Last verified:** `07ef548ee3747efd617e131880368cedc52f3bfc`.

## MEM-005 — Windows publish boundary

- **State:** ACTIVE
- **Since main commit:** `e345256`
- **Contract:** `dist` is a generated build workspace. The user-visible
  `Crawler tool\Current` is the publish authority, updated only by an explicit
  clean-main publish after a verified candidate; failed candidates do not
  replace Current. The approved Team Bid release is `0.8.0`.
- **Release identity:** application/package `0.8.0`, source SHA
  `c1e9e16ffca3b3fd83ba7a150b16353445d7856e`, immutable annotated tag
  `v0.8.0`, and GitHub Release `v0.8.0`. The release manifest, BUILD_INFO and
  SHA256SUMS record the installer/EXE hashes. `Crawler tool\Current` and the
  Team Bid Reference are derived from this same verified identity.
- **Evidence:** merged Windows release mechanics, hosted CI, and the
  published v0.8.0 release artifacts.
- **Last verified:** `c1e9e16ffca3b3fd83ba7a150b16353445d7856e`.

## MEM-006 — SA Excel source routing

- **State:** ACTIVE
- **Since main commit:** `fc4d68cbeb9e5f27a91039e264e3906d1ee8f1c7`.
- **Contract:** Excel intake checks the `KHMT-<date>.xlsx` or
  `TBMT-<date>.xlsx` filename hint first, then validates workbook schema and
  PL/IB identity evidence. Unknown, conflicting or dual-schema workbooks
  require named Human correction; corrections are append-only Ground Truth
  for the source SHA. Human source correction does not rewrite PL/IB identity.
  TBMT is recognized and has a source-neutral candidate intake boundary, but
  full TBMT Bid Radar review/export/GUI support is not implemented yet.
- **Evidence:** merged PR #44 / WP-MI-SRC-01 implementation and regression
  suite.
- **Last verified:** `fc4d68cbeb9e5f27a91039e264e3906d1ee8f1c7`.

## MEM-007 — Local staged integration governance

- **State:** ACTIVE
- **Since main commit:** `6e8206f469497c4c073ee6030455b1db946f3479`.
- **Contract:** Development uses Local Staged Integration: one Single Writer
  implements a bounded micro-WP, local machine verification produces execution
  evidence, an independent Reviewer audits a `LOCAL_REVIEW_PACKET`, and an
  audited feature-branch commit may be pushed as a remote checkpoint without
  opening a PR. Parent WPs use an integration gate before Draft PR/hosted CI.
  Audited history uses forward correction by default. Hosted-CI infrastructure
  waiver creates `PENDING_RETRO_CI = YES`; official Team Bid release is blocked
  while retro-CI debt remains open unless the Human explicitly approves a
  separate bounded exception.
- **Evidence:** merged PR #45 / WP-GOV-LSI-01,
  `docs/agent/LOCAL_STAGED_INTEGRATION.md`, `AGENTS.md`, and
  `docs/agent/OPERATING_MODEL.md`.
- **Last verified:** `6e8206f469497c4c073ee6030455b1db946f3479`.

## MEM-008 — TBMT source-neutral Opportunity intake

- **State:** ACTIVE
- **Since main commit:** `8e6184bc2baadb9e8b7f4056f7e104247201197c`.
- **Contract:** The merged TBMT XLSX importer produces an
  `OpportunityImportBatch(source_type=TBMT)` and source-backed
  `OpportunityCandidate` values with `OpportunityIdentity` in the `IB`
  namespace. TBMT is not represented as a KHMT `PlanPackage`; `PL != IB`.
  Exact provenance retains source SHA-256, sheet, source row, and raw source
  fields. The exact identity key is `(base_id, revision)` while `base_id` is
  the lineage key: `-00` is the first HSMT publication and `-01` is a later
  publication/revision after source HSMT changes. Different revisions remain
  distinct and a newer revision must not silently erase an older one. Review
  inheritance across revisions is not implemented or authorized.
- **Evidence:** PR #47, final audited feature head
  `c89ccdf1ef5a35e70b534354fca2a155ce83d9a6`, merge commit
  `8e6184bc2baadb9e8b7f4056f7e104247201197c`, and the 02A Parent Integration
  Gate. Read-only acceptance of the real TBMT workbook recorded 72 source rows,
  72 candidates, and 0 issues. SHA-256 was
  `E4B8FF62D8FF979BD646287EB7C894B9F03D089691B9122A6A96847457A1CDB4` with
  size 120194 bytes; bytes and size were unchanged before/after acceptance.
  Full TBMT Bid Radar filter/search, human-review persistence, confirmed
  export, and GUI integration remain future WP-MI-TBMT-02B work.
- **Last verified:** `8e6184bc2baadb9e8b7f4056f7e104247201197c`.

## Explicitly not promoted

Vault/Shelf/Recovery, future storage hardening, HSNL, AI/Learning, legal
judgement, scoring, GO/HOLD/NO-GO, and future extraction work remain pending
unless a later Work Package is merged and verified.
