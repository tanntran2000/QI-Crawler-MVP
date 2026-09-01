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
  TBMT is recognized with source-neutral candidate intake; source-neutral
  filter/search, Human Review persistence, confirmed output and thin GUI
  integration are merged in the 02C delivery closure. See MEM-014 for the
  current capability boundary and remaining API/TBMT Legal DOCX gaps.
- **Evidence:** merged PR #44 / WP-MI-SRC-01 plus later Opportunity
  Intelligence merges recorded in MEM-010 and MEM-012.
- **Last verified:** `bba21071d3a6b42ea87c845e44413a08d863644a`.

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
  Source-neutral Human-review persistence is merged in WP-MI-TBMT-02B; the
  confirmed output and thin GUI delivery closure are merged in WP-MI-TBMT-02C.
  KHMT Legal DOCX remains compatible, while TBMT Legal DOCX and API
  integration remain explicitly unsupported/future scope. Source-neutral
  Bid Radar filter/search is covered by MEM-010 and review persistence by
  MEM-012; the consolidated closure is MEM-014.
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
  compatibility remain intact. FILTER MATCH is not Human CONFIRMED; confirmed
  output and thin GUI integration are merged in MEM-014, while API integration
  remains future scope. Human-review persistence is covered by MEM-012.
  `IB...-00` Human Review does not imply `IB...-01` review.
- **Evidence:** PR #52, merge commit
  `d2aa8a9bded931d54aaa50c398b701b1598024ec`, branch head
  `3e27c9c17d257cd91c544eaf6e5bb201087c0729`.
- **Last verified:** `d2aa8a9bded931d54aaa50c398b701b1598024ec`.

## MEM-012 — Source-neutral Opportunity Human Review persistence

- **State:** ACTIVE
- **Since main commit:** `cbda73692dfe6b99c6a2045b2306b57e1e4136fb`.
- **Contract:** Merged WP-MI-TBMT-02B-3 provides source-neutral KHMT/TBMT
  Human Review through a separated Domain Core, Application Backend,
  Repository Port and Persistence layer. PL and IB namespaces remain distinct;
  the exact review identity is `(base_id, revision)` with no review inheritance
  across revisions. SHA/source-row provenance isolates candidates, review
  events are append-only, latest-event state is authoritative, and exact
  duplicate decisions are idempotent. Alembic head is
  `0015_add_opportunity_review_events`. The pre-migration backup is WAL-safe
  through `sqlite3.Connection.backup()`.
- **Compatibility:** Legacy KHMT `CandidateReviewService` behavior remains
  compatible. FILTER/SEARCH/RADAR matches are not Human CONFIRMED, and no
  implicit review is created.
- **Evidence:** PR #55 merge commit
  `cbda73692dfe6b99c6a2045b2306b57e1e4136fb`, merged feature head
  `6513acfe7397467d1588fb3d404938ac04c8c00c`, audited code head
  `b5043e8396b43306d09c1c0b0ca9cad8b58cfd3a`.
- **Scope gap:** Confirmed XLSX, backend source-integrity, thin GUI delivery and
  KHMT Legal DOCX compatibility are merged in MEM-014; TBMT Legal DOCX remains
  unsupported and API integration remains future scope.
- **Last verified:** `cbda73692dfe6b99c6a2045b2306b57e1e4136fb`.

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

## MEM-013 — QI-KVS blueprint and strict handoff continuity

- **State:** ACTIVE
- **Since main commit:** `bba21071d3a6b42ea87c845e44413a08d863644a`.
- **Contract:** Blueprint revision 1.2 defines QI Knowledge & Verification
  System (QI-KVS) as a cross-cutting target architecture, not a new product
  lane and not an active Knowledge DB/API/MCP/AI runtime. `RULE CONTRACT = DATA`
  while evaluator implementation remains code; Knowledge Rule, Source Truth,
  Human Ground Truth, SOP Decision Record and Engineering Failure Memory remain
  distinct authorities. Durable governance now requires the Roadmap Entry Gate,
  FULL/DELTA/NO_RE_READ selection, strict cross-agent handoff fields and a
  mandatory post-merge reconciliation. A merged PR with stale `CURRENT.md`
  produces `HANDOFF_STALE / ENTRY_HOLD` before the next technical Work Package.
- **Evidence:** merged PR #58, merge commit
  `bba21071d3a6b42ea87c845e44413a08d863644a`, Blueprint revision 1.2,
  `AGENTS.md`, `MASTER_ROADMAP.md`, `MEMORY_INDEX.md`, operating/handoff
  governance and independent documentation audit.
- **Boundary:** QI-KVS runtime implementation remains NOT_ACTIVE. Product
  Frontier is now Unified Tender Warehouse after the merged
  `WP-MI-TBMT-02C — Opportunity Intelligence Delivery Closure`.
- **Last verified:** `bba21071d3a6b42ea87c845e44413a08d863644a`.

## MEM-014 — Opportunity Intelligence Delivery Closure

- **State:** ACTIVE
- **Since main commit:** `82013b0bc1a4b3a62a12567d3d4cc02974f93ec9`.
- **Contract:** The merged WP-MI-TBMT-02C delivery closure provides KHMT/TBMT
  source-neutral backend routing with PL/IB preservation, tri-state
  filter/search, explicit Human Review authority, review persistence and
  revision isolation, source-neutral confirmed XLSX, backend SHA fail-closed
  export integrity, thin existing Bid Radar GUI integration and vertical
  KHMT/TBMT acceptance. KHMT Legal DOCX remains compatible; TBMT Legal DOCX is
  explicitly unsupported. API integration and broader lifecycle expansion are
  not claimed.
- **Evidence:** PR #60, merge commit
  `82013b0bc1a4b3a62a12567d3d4cc02974f93ec9`, merged feature head
  `d5fecd3cc95e55f825e83e75321a3182da633384`, audited code/acceptance head
  `513becf3fc9a24d9ff8d26df37fee320486fd0de`, Parent local verification
  628 passed with 628 collected and 63 targeted, and independent Parent and
  Spine audits PASS.
- **Boundary:** SQLite/review history remains authoritative; no implicit
  Human confirmation, release publication or hosted-CI PASS is implied.
  `CI_WAIVER = ACTIVE` and `PENDING_RETRO_CI = YES` remain current operational
  state in `CURRENT.md`.
- **Last verified:** `82013b0bc1a4b3a62a12567d3d4cc02974f93ec9`.

## MEM-015 — Roadmap Delta and Reviewer continuity governance

- **State:** ACTIVE
- **Since main commit:** `e1e7f80e7a41cc4ed402b23966a0583d8eb89a53`.
- **Contract:** PR #62 merged the mandatory `MASTER_ROADMAP_DELTA.md`
  companion and LAW 14. The independent Reviewer now reports three relevant
  dimensions: implementation, roadmap fit and Spine freshness.
  `MASTER_ROADMAP_DELTA.md` does not silently override `MASTER_ROADMAP.md`;
  material Roadmap/Delta conflict routes to Planner/Human authority with
  `ENTRY_HOLD`.
- **Boundary:** This is governance continuity only. It does not claim a
  product-runtime, HSMT, Warehouse or CI capability change.
- **Evidence:** PR #62, merge commit
  `e1e7f80e7a41cc4ed402b23966a0583d8eb89a53`, audited feature head
  `1b68007d1cd57b8763231a84367e9289064a9843`.
- **Last verified:** `e1e7f80e7a41cc4ed402b23966a0583d8eb89a53`.

## MEM-016 — Planner continuity and governed Human→Planner→Builder→Reviewer loop

- **State:** ACTIVE
- **Since main commit:** `d10445fc2ffc92e810f0d6258160151efc1c846f`.
- **Contract:** PR #64 merged the Planner Continuity governance contract. The
  Planner preserves material Human intent, prepares bounded Builder contracts,
  keeps the independent Reviewer separate, reconciles Reviewer findings after
  audit, and prepares the next Human decision packet. `ROLE_ENTRY_GATE` and
  `LATEST_WP_SPINE_SYNC_AUDIT` are mandatory continuity checks; role is
  authority, not model name. Hosted CI is available again for normal required
  gates.
- **Evidence:** PR #64, merged feature head
  `db19f42985030f2b154804f959fca615c523a06e`, merge commit
  `d10445fc2ffc92e810f0d6258160151efc1c846f`, and Python CI run
  `32987119489` with all four required jobs passing; independent final audit
  PASS.
- **Boundary:** Governance continuity only. This does not claim a product,
  Warehouse, HSMT or AI capability change, and it does not authorize
  implementation outside a separately approved Work Package.
- **Last verified:** `d10445fc2ffc92e810f0d6258160151efc1c846f`.

## MEM-017 — Role-specific agent prompt profiles and large bounded execution

- **State:** ACTIVE
- **Since main commit:** `5e7b478d75662b979bed1688262374ba0d60220b`.
- **Contract:** PR #67 merged the M1 governance prompt-profile contracts.
  Planner-generated Builder and Reviewer profiles preserve role separation,
  bounded Approval Leases, large coherent batches, staged self-verification,
  independent review and explicit stop conditions. `CURRENT.md` remains an
  active transition authority with governed write frequency; handoffs are
  short, factual and evidence-backed rather than diaries. Plugin execution,
  exact-object review and post-merge reconciliation remain explicit contract
  requirements.
- **Evidence:** PR #67, merged feature head
  `59bb04ad751360a7db9415982cde87f48f947994`, merge commit
  `5e7b478d75662b979bed1688262374ba0d60220b`, exact-head Python CI run
  `33057122566` with all four required jobs passing, and independent final
  audit PASS with non-blocking findings.
- **Boundary:** Governance/process only. This does not claim Warehouse,
  HSMT, AI, release or other product capability implementation, and it does
  not authorize WP-WH-MIN-01/M1.
- **Last verified:** `5e7b478d75662b979bed1688262374ba0d60220b`.

## MEM-018 — Minimum Safe Tender Package Warehouse

- **State:** ACTIVE
- **Since main commit:** `0154e87a12558f3c199414d3747811a419ae003d`.
- **Architecture:** `OPTION_B_DOMAIN_FIRST_TENDERCASE`.
- **Contract:** WP-WH-MIN-01 merged the Minimum Safe Warehouse slice.
- **Proven:** TenderCase identity; exact IB revision identity; `PL != IB`;
  document identity separated from package membership; managed DocumentIntake
  reuse; external-source deletion survival; restart/reopen; SHA-verified
  retrieval; seven logical Team Bid zones; seven physical derived export
  folders; empty export zones materialized; exact release isolation;
  source/working/final/reference separation; Bài 2
  `IB2500585490-00` Real Golden PASS.
- **Schema:** `0017_add_tender_workspace_entries`.
- **Evidence:** PR #69, feature head
  `acfcbe26becce69d6ea21177af227386b4ca207f`, merge commit
  `0154e87a12558f3c199414d3747811a419ae003d`, Python CI
  `33135412689` PASS, CodeQL `33135411050` PASS, independent audit PASS and
  Real Golden Bài 2 PASS.
- **Not claimed:** full package completeness/reconciliation; full
  Vault/recovery/archive; deep HSMT intelligence; full SOP decision
  intelligence; autonomous Human/business authority; or the entire Unified
  Tender Warehouse complete.
- **Last verified:** `0154e87a12558f3c199414d3747811a419ae003d`.

Do not add RD-0011 as implemented memory.

## MEM-019 — Operational Tender Warehouse controls

- **State:** ACTIVE
- **Since main commit:** `fcb394a6ee0926c1a355c486a72dc001e07d0096`.
- **Contract:** WP-WH-OPS-01 extends the Minimum Safe Warehouse with exact
  TenderCase/revision retrieval and mutation targeting, semantic replacement
  slots, append-only supersession/source-correction history, same-SHA
  idempotence, a named source-correction boundary, and zone-by-authority
  enforcement. `SOURCE_E_HSMT` cannot be replaced by generic upload; working
  E-HSDT and final submission remain distinct.
- **Operational controls:** Exact-release dashboards and active-only exports;
  integrity states `NOT_CHECKED`, `VERIFIED`, `MISSING` and `MISMATCH`;
  deterministic Windows-safe collision naming; thin GUI delegation; and
  controlled Team Bid workspace operations across the seven logical zones.
- **Evidence:** PR #72 feature head
  `196a693e4765be0bcde7460a27685d031553c92d`, merge commit
  `fcb394a6ee0926c1a355c486a72dc001e07d0096`, post-merge Python CI run
  `33156777447` with all four required jobs passing, CodeQL run
  `33156777544` passing, independent implementation/Spine/final remote audit
  PASS, and Real Bài 2 `IB2500585490-00` acceptance PASS.
- **Schema:** `0018_add_tender_workspace_transitions`.
- **Boundary:** This promotes operational retrieval, mutation, history,
  integrity and workspace controls only. Full package completeness,
  Vault/recovery/archive, deep HSMT, full SOP decision intelligence,
  autonomous Human/business authority, pilot/release approval and the entire
  Unified Tender Warehouse remain unclaimed and require later approved work.
- **Last verified:** `fcb394a6ee0926c1a355c486a72dc001e07d0096`.

## MEM-020 — Source integrity hardening

- **State:** ACTIVE
- **Contract:** Raw HTML source evidence is immutable and content-addressed.
  The same bytes may reuse the same immutable object, while different bytes
  produce a different raw object; existing raw evidence is never silently
  truncated or overwritten. Notice identity is source-scoped: `notice_code`
  is not a global identity. Source identity combines the source, its
  business/source-local identity and revision semantics.
- **Semantic change detection:** Parsed semantic change detection uses
  deterministic canonical serialization covering the persisted source-derived
  Notice, Attachment and TenderItem state.
- **Evidence:** BUG-04, BUG-02 and BUG-11 were independently audited and
  merged in PR #74 (feature head
  `faebb2d8a113a0a8d56d10d4021e68b974c1e3fe`, merge commit
  `bcf5ca60fe933a82c097c6575fd50de63acfca4c`). PR-head Python CI
  `33191769012` PASS and CodeQL `33191767610` PASS; post-merge Python CI
  `33196201630` PASS and CodeQL `33196201430` PASS.
- **Boundary:** This does not claim full source-history reconciliation,
  stale-child deletion or reconciliation, Warehouse completeness/recovery/
  archive, deep HSMT, release, or Team Bid pilot.
- **Last verified:** `bcf5ca60fe933a82c097c6575fd50de63acfca4c`.

## MEM-021 — Source child lifecycle reconciliation

- **State:** ACTIVE
- **Since main commit:** `823e33dd34c43dccece8a2d70d248db12c9ee516`.
- **Contract:** PR #76 merged source-child lifecycle reconciliation. Exact
  source snapshot membership is represented by active child state for both
  `Attachment` and `TenderItem`; source removal deactivates current membership
  without hard-deleting historical rows. Downloaded attachment evidence is
  preserved, and reappearance reactivates the same logical child rather than
  creating duplicate state. Automatic download/retry paths operate only on
  active source attachments, and exact Notice/source/revision boundaries remain
  isolated.
- **Schema:** `0019_add_source_child_lifecycle`.
- **Evidence:** TDD RED test commit
  `b232f0d9e4108155d786fcdaea9a276555ff75ce`; code/fix head
  `1020ad2b7ab706e586ad3983cd8f7703185f992c`; merged feature head
  `ad25adf2939fd54f36d4411a1dff526c21dcff76`; merge commit
  `823e33dd34c43dccece8a2d70d248db12c9ee516`; PR-head Python CI
  `33238798500` PASS and CodeQL `33238797624` PASS; post-merge Python CI
  `33240243556` PASS and CodeQL `33240243744` PASS.
- **Boundary:** `PACKAGE_COMPLETENESS != SOURCE_CHILD_LIFECYCLE`;
  `WP-WH-COMPLETE-01` remains future/candidate only. Full
  `FULL_VAULT_RECOVERY_ARCHIVE != COMPLETE`, deep HSMT is not implemented,
  and `RELEASE = NO` / `TEAM_BID_PILOT = NO` remain in force.
- **Last verified:** `823e33dd34c43dccece8a2d70d248db12c9ee516`.

## MEM-022 — Team Bid confirmed-opportunity workspace handoff

- **State:** ACTIVE
- **Since main commit:** `5e4c1ad682e62b29077f5a67954c65caf8d07746`.
- **Contract:** WP-TB-BASIC-CRAWLER-01 merged PR #79 and the bounded
  confirmed-opportunity to TenderCase workspace handoff. Persisted latest
  Human review is the handoff authority; a cached GUI confirmation cannot
  override a later persisted `REJECTED` or `NEEDS_REVIEW` state. TBMT
  handoff preserves the exact IB revision identity without collapsing
  revisions. KHMT may open a provisional PL-context TenderCase but never
  fabricates IB identity. Ambiguous mapping fails closed without mutation.
- **Delivery:** The path remains thin GUI → Application Backend, and
  restart/reopen behavior is proven for the handoff.
- **Evidence:** Independent audit PASS; PR-head CI PASS; post-merge Python CI
  `33302244508` PASS; post-merge CodeQL `33302244269` PASS.
- **Boundary:** This does not prove package completeness, Vault/recovery/
  archive, deep HSMT, legacy GO/HOLD authority, API evolution, release, Team
  Bid pilot, or the entire Unified Tender Warehouse complete.
- **Last verified:** `5e4c1ad682e62b29077f5a67954c65caf8d07746`.

## MEM-023 — Role Boot, Prompt Continuity & Canonical Checkout Recovery

- **State:** ACTIVE
- **Since main commit:** 2826f8c6735fcf68f405a01386d6ab4e63476e57.
- **Contract:** PR #81 merged the canonical Role Boot / Prompt Continuity
  governance contract. It defines Action-First role prompts, Planner/Builder/
  Reviewer mutual challenge, mandatory Roadmap/Delta reconciliation cadence,
  and canonical checkout authority independent of Git-object freshness.
- **Canonical checkout:** D:\QI Technology\QI Crawler\egp-crawler-python;
  the former C checkout was physically removed.
- **Evidence:** Audited head 41b7a1056b9bb2d69922a60282bba9846e7e2128;
  merge commit 2826f8c6735fcf68f405a01386d6ab4e63476e57; canonical-D
  retrospective and D4 forward-correction audits PASS; PR #72–#80 were
  revalidated on D; post-merge Python CI run 33322155713 and CodeQL passed.
- **Boundary:** FB-0024's generic checkout identity law remains valid;
  FB-0029 corrects only its C/D authority interpretation. No product
  capability, release or Team Bid pilot authority is promoted by this memory.
- **Last verified:** 2826f8c6735fcf68f405a01386d6ab4e63476e57.

## MEM-024 — Basic Crawler Real Operational Acceptance

- **State:** ACTIVE
- **Since main commit:** `2826f8c6735fcf68f405a01386d6ab4e63476e57`.
- **Contract:** WP-TB-BASIC-CRAWLER-02 Micro-A Gate-A independently proves
  the Ground Truth case `IB2600462391-00`: a source-backed observation
  persists a Human `CONFIRMED` decision, survives a fresh re-read, and
  hands off to the exact IB TenderCase/release; a newer persisted
  `REJECTED` decision blocks a stale confirmation. The separate document
  lane for `IB2500585490-00` proves genuine PDF intake, exact release
  membership, `SOURCE_E_HSMT` authority, managed-copy survival after
  disposable-input deletion, SHA/byte identity, restart/search/reopen and
  isolated controlled export; observed cross-tender contamination is zero.
- **Storage boundary:** `manual_upload/unlinked` is storage-layout naming,
  not package-membership authority. Database membership and workspace zone
  remain authoritative. Live data is untouched; acceptance writes use an
  isolated database and document root.
- **Micro-C boundary:** Micro-B was skipped because no material blocker was
  proven. DOCX role/authority, reference-authority separation, multi-revision
  operational proof and same-package end-to-end proof remained `NOT_PROVEN`
  at Parent-02 closure.
- **Evidence:** Micro-A and the separate real PDF document lane were
  independently exercised against the merged Minimum Safe Warehouse
  behavior; Micro-C closure was independently audited and merged with Parent
  02. PR #82 merged at `54a0c53fdb5d38e208c4fd66d126b20e971f00f5` from audited
  head `03056fe147c3263cf8fb2ea39e63dc239e35fffe`.
- **Post-merge verification:** Python CI run `33384009634 / PASS` and CodeQL
  run `33384009691 / PASS` are recorded for the merged main state.
- **Later status:** Parent-03 subsequently implemented the bounded revision
  transition and controlled-folder capability; see MEM-025. This entry remains
  the durable Parent-02 acceptance boundary.
- **Last verified:** `54a0c53fdb5d38e208c4fd66d126b20e971f00f5`.

## MEM-025 — Basic Crawler controlled folder and operational revision closure

- **State:** ACTIVE
- **Since main commit:** `3ebea845589fedf860afb94f69959413a819b176`.
- **Contract:** WP-TB-BASIC-CRAWLER-03 adds recursive read-only folder
  candidate discovery, explicit Human confirmation before intake, TOCTOU
  SHA revalidation, exact package/revision guards and package-scoped short
  managed naming while preserving original filenames and bytes. Operational
  revision transitions are append-only through Alembic
  `0020_add_tender_operational_revision_events`: Human acceptance creates a
  persisted pending transition rather than advancing latest; explicit
  activation requires the exact pending newer revision plus an adjacent
  previous/latest comparison; downgrade is forbidden; older revisions remain
  readable; membership and Human review do not inherit across revisions.
- **Diff boundary:** Adjacent comparison reports `UNCHANGED`, `CHANGED`,
  `ADDED`, `UNKNOWN_RELATION`, and only reports
  `REMOVED_FROM_NEW_REVISION` when completeness evidence supports removal.
  Source diff is evidence and potential work impact is not a Team Bid business
  decision.
- **Real operational evidence:** For `IB2500585490-00`, same-package PDF/DOCX
  intake, source authority, managed-copy identity, restart/reopen, exact-release
  retrieval and controlled export were proven with zero false-safe results,
  zero fabricated identity and zero cross-tender source contamination.
- **Preserved evidence gaps:** `REAL_MULTI_REVISION_EVIDENCE = EVIDENCE_GAP`
  and `REAL_REFERENCE_OPERATIONAL_EVIDENCE = EVIDENCE_GAP`. No genuine second
  revision or genuine foreign reference asset was substituted with synthetic
  authority; `EVIDENCE_GAP != PRODUCT_DEFECT`.
- **Evidence:** PR #83 exact audited head
  `0d48abc87693643fb668fd8900c970d7b3315620`, independently audited code head
  `d7a2cfdeb68f08a558a1f4cc165d0a8ad7b0ab34`, merge commit
  `3ebea845589fedf860afb94f69959413a819b176`, PR-head Python CI
  `33495936550 / PASS 4/4`, and post-merge CodeQL
  `33498315904 / PASS`. Post-merge Python CI `33498316251` was running at the
  initial reconciliation capture and must be read from live GitHub for final
  state.
- **Boundary:** Unified Tender Warehouse remains `PARTIAL`. Package
  completeness/reconciliation, Vault/recovery/archive, deep HSMT, API
  evolution, Team Bid pilot and release publication remain unauthorized. The
  approved Team Bid release remains `0.8.0`; Parent-03 is an Unreleased
  capability and would have MINOR version impact if later included in an
  approved release.
- **Last verified:** `3ebea845589fedf860afb94f69959413a819b176`.

## Explicitly not promoted

Vault/Shelf/Recovery, future storage hardening, HSNL, AI/Learning, legal
judgement, scoring, GO/HOLD/NO-GO, and future extraction work remain pending
unless a later Work Package is merged and verified.