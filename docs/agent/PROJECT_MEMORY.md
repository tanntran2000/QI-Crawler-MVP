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
  Human-review persistence, confirmed export, and GUI integration remain
  future WP-MI-TBMT-02B work; source-neutral Bid Radar filter/search is now
  covered by MEM-010 below.
- **Last verified:** `8e6184bc2baadb9e8b7f4056f7e104247201197c`.

## MEM-009 — Product House and builder handoff discipline

- **State:** ACTIVE
- **Since main commit:** `a44d365b48ad291aaa6e86c50adc72ed7318b883`.
- **Contract:** The merged Product House / Architecture README keeps the
  product layers and dependency direction durable, while builder handoffs are
  short, factual and evidence-backed. `LAST_AUDITED_CODE_HEAD` remains
  separate from later documentation heads; the approved flow is
  `IMPLEMENT → VERIFY → COMMIT → AUDIT → REMOTE CHECKPOINT → HANDOFF`.
- **Evidence:** merged PR #51, exact merge commit
  `a44d365b48ad291aaa6e86c50adc72ed7318b883`, `AGENTS.md`, and the Product
  House README.
- **Last verified:** `a44d365b48ad291aaa6e86c50adc72ed7318b883`.

## MEM-010 — Source-neutral Bid Radar filter/search

- **State:** ACTIVE
- **Since main commit:** `d2aa8a9bded931d54aaa50c398b701b1598024ec`.
- **Contract:** Merged 02B-1 projects KHMT and TBMT observations through the
  source-neutral `OpportunityRadarItem` contract; merged 02B-2 provides
  bounded budget, province/city, keyword and selection-method filtering/search.
  The legacy KHMT `PlanPackage` adapter and its audited exclude-keyword
  compatibility remain intact. FILTER MATCH is not Human CONFIRMED; review
  persistence, export, GUI and API are not included, and 02B-3 remains held.
  `IB...-00` Human Review does not imply `IB...-01` review.
- **Evidence:** PR #52, merge commit
  `d2aa8a9bded931d54aaa50c398b701b1598024ec`, branch head
  `3e27c9c17d257cd91c544eaf6e5bb201087c0729`.
- **Last verified:** `d2aa8a9bded931d54aaa50c398b701b1598024ec`.

## MEM-011 — Documentation lifecycle and context governance

- **State:** ACTIVE
- **Since main commit:** `9d76ca0f7ce0aba60e49a134e9a2a2d9825ac9e2`.
- **Contract:** Work Packages use tiered Parent/Micro PRE and POST lifecycle.
  `CURRENT.md` is transition authority, not diary, roadmap or history;
  history snapshots are HISTORICAL / NON-NORMATIVE; and PROJECT_MEMORY stores
  merged-main durable facts only. Read-mode selection supports FULL, DELTA and
  NO_RE_READ. Prompt construction reads authoritative state and live
  Git/GitHub when relevant; chat memory alone is insufficient. Exact Git
  objects outrank copied audit prose for concrete findings. Generic
  abstractions preserve legacy behavior at narrow compatibility seams, and one
  active machine-readable key has one semantic meaning. Unavailable hosted CI
  is not CI PASS; hosted-CI mandatory gates resume only after quota recovery
  and actual required workflow execution.
- **Evidence:** PR #53, merged governance branch head
  `514d8c3537dbda15c3b306d72e86306c3d1d0033`, final independently audited
  Parent head `17ec744cd594fd8cefec52dfde8fa39406b8f652`.
- **Last verified:** `9d76ca0f7ce0aba60e49a134e9a2a2d9825ac9e2`.

## Explicitly not promoted

Vault/Shelf/Recovery, future storage hardening, HSNL, AI/Learning, legal
judgement, scoring, GO/HOLD/NO-GO, and future extraction work remain pending
unless a later Work Package is merged and verified.
