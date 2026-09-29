# WP-OPS-QI-SINGLE-INSTALLATION-AND-LEGACY-ROOT-RETIREMENT-01 rev2-corr1

## Authority and status

STATUS = HUMAN_APPROVED; BUILDER G1 AUTHORIZED
PARENT = THIS WORK ORDER; NO NEW PARENT
ROLE = BUILDER_SINGLE_WRITER
HUMAN_APPROVAL = Direct Human approval in the Builder assignment dated 2026-09-28
APPROVAL_LEASE = G1.0 / G1.1 / G1.2; semantic local commits; one remote branch checkpoint after a coherent local candidate or material HOLD; one later PR only after Planner, Tester and Reviewer transitions
HUMAN_ONLY = MERGE; RELEASE; TAG; OFFICIAL PUBLISH; G2 BUILD; OPERATIONAL INSTALL OR UPDATE

The approved Human intent is one operational installation rooted at D:\QI-Crawler, preservation of its Data and recovery lineage, and a governed app-only update/recovery capability. The approval does not authorize a live update, installed EXE launch, shortcut mutation, database migration or restore, crawl/import, B09 Bridge work, release, or deletion.

## Identity, baseline and carry-forward

CANONICAL_CHECKOUT_EXPECTED = D:\QI Technology\QI Crawler\egp-crawler-python
EXPECTED_ORIGIN_REPOSITORY = https://github.com/tanntran2000/QI-Crawler-MVP.git
INTEGRATION_BASE = origin/main caf983691da60d4eaf990d09e9e1788692aabaac
PARENT_ENTRY_HEAD = 211c0ddbfdcfc7fb249cebd2b449f65d6ea91186
ACTIVE_BRANCH = codex/single-installation-legacy-root-retirement-01
CARRIED_GOVERNANCE_RANGE = caf983691da60d4eaf990d09e9e1788692aabaac..211c0ddbfdcfc7fb249cebd2b449f65d6ea91186
CARRIED_COMMIT_COUNT = 10; PRESERVED IN ORDER; NO CHERRY-PICK, RESET, REBASE OR AMEND
OLD_BRANCH = codex/installed-startup-recovery-01 at 211c0ddbfdcfc7fb249cebd2b449f65d6ea91186; PRESERVE

The carried commits are the installed-startup recovery and local-verification governance history already present on the verified Planner-returned head. The earlier six-commit count applied to a prior transition and does not apply to this Parent. Do not rewrite that history.

At execution entry, re-resolve cwd, Git top-level, git-dir, common-dir, origin, active branch, HEAD, origin/main, live origin/main, tracked/index status and target branch. Stop on identity drift, remote-main movement, tracked dirt, branch conflict, or any need to rewrite history. Unknown untracked artifacts are KEEP and must not be inspected, staged, renamed, cleaned or overwritten.

## Roadmap, architecture and release impact

ROADMAP_REVISION = 1.3
ROADMAP_BASELINE_SHA = 7e092f02ce646ca7e4336b4a9b005b30229745b7
ROADMAP_DELTA_BASELINE_SHA = 77bba2be7bec628ce7f014a20ff02a564f4f2ffc
ROADMAP_NODE = Cross-cutting Windows / Team Bid delivery; Engineering Toolbox / Plugins supports execution
RELATED_DELTA = QI-INSTALLED-STARTUP-RECOVERY-FM049-20260928-01; this G1 delivery follow-up is recorded separately; RD-0013 B09 history remains separately governed and out of scope
PRODUCT_FRONTIER = Unified Tender Warehouse; PARTIAL
PRODUCT_CAPABILITY_OR_MATURITY_PROMOTION = NONE
ARCHITECTURE_LAYERS = Windows desktop delivery surface; application startup/backend; operational release infrastructure and persistent Data; no product-house capability change
RELEASE_IMPACT = Internal PATCH candidate 0.10.1; not a release, build, installer, publication, tag or deployment
ROADMAP_ENTRY_GATE = PASS; FULL READ
ROLE_ENTRY_GATE = PASS; current Human assignment, approved Work Order and CURRENT reconcile

ARCHITECTURE_LAYER_CONTRACT
===========================
PRODUCT_LANE = Cross-cutting Windows / Team Bid delivery; Engineering Toolbox / Plugins support
HUMAN_CONSUMER = Team Bid operator; no new user-facing capability is exposed by G1
MACHINE_CONSUMER = Operational startup validator and separately authorized updater
DOMAIN_CORE = OUT_OF_SCOPE; no business-domain or tender semantics change
APPLICATION_BACKEND = IN_SCOPE; startup acceptance and app-only update/recovery contract
SOURCE_ADAPTERS = OUT_OF_SCOPE
PERSISTENCE_INFRA = IN_SCOPE; exact identity, snapshot, and preservation checks only; no live database write, migration, or restore
DELIVERY_ADAPTERS = IN_SCOPE; thin inspection CLI and governed update entry boundary
DESKTOP_FRONTEND = OUT_OF_SCOPE
CLI = IN_SCOPE; inspection remains default and non-mutating
API = OUT_OF_SCOPE
AI_CONSUMER = OUT_OF_SCOPE
ENGINEERING_TOOLS = REQUIRED; CodeGraph, Superpowers, pytest and Ruff
DEPENDENCY_DIRECTION_CHECK = PASS; existing capability-owned modules; no new dependency or cross-layer inversion
RATIONALE = Internal Windows delivery/recovery support; Product Frontier and capability maturity remain unchanged

The one supported installed entry point remains D:\QI-Crawler\Current\QI-Crawler\QI-Crawler.exe. Mutable business data remains at D:\QI-Crawler\Data. No sibling Crawler tool, candidate root, update-state volume or rollback volume is created. This is operational architecture support only; it does not advance the Product Frontier.

## Objective and non-objectives

Implement a fail-closed, synthetic-testable G1 contract for replacing only the application generation inside the existing installation while preserving operational Data, migration provenance, rollback evidence and exact recovery state. Preserve legacy acceptance-v1 validation and support acceptance-v2 with distinct application and migration identities. Prepare internal patch metadata for 0.10.1.

This Work Order stops before a new EXE build, live installation/update, runtime launch, Start Menu shortcut edit, real legacy-root archive, G2, G3, migration, database restore, crawl/import, B09, merge or release. Do not modify operational or AppData contents. Do not create a second updater or a second operational root.

### Prior installed-startup evidence motivating G1

The preceding authorized direct launch of the installed executable exited with code 1 before a GUI, file-log append or Windows application event. Planner-admitted reconciliation identifies the first failing old-source gate as `OPERATIONAL_DATABASE_SHA_MISMATCH`: the installed source commit `79b62ec93547f210aad162dcbf926c0bd2c81ab1` validates the mutable current DB against the receipt's promotion-time database SHA before file logging. The receipt SHA was `c35e1f3618871d453ee2950f37cbcce1466435948e5692360b9d0512461a8f2a`; the current legitimate operational DB SHA was `33a3a5adaca15514a18714dbd9281c224c174b8471341eeb8c333c11748818ee`.

The source correction `0d9a3c41e71d368aa4c21aefdd970dc41343e6af` was merged via PR #130 at `179c0712a14161ea25096e66a127f6022bf696fd` and is contained in the verified `origin/main` base `caf983691da60d4eaf990d09e9e1788692aabaac`. The installed runtime predates that correction. This is the admitted cause for the old executable's silent exit signature, not proof of later startup behavior or permission to rewrite the migration receipt. G1 preserves the merged source fix and designs the next app-only contract; no new fix to the installed executable, build or live remediation is in scope.

## G1.0 existing-primitive and contract resolution

### Existing primitive map

operational_update.classify_operational_update_state:
  EXISTING_OWNER = read-only Bridge A classifier and Windows DB/WAL/SHM observation
  DECISION = PRESERVE; do not turn its observation classifier into a second engine or weaken its existing evidence

operational_release._promote_staged_root / _atomic_directory_replace:
  EXISTING_OWNER = whole-root copy, Data/config rewrite, SQLite migration, acceptance generation, and synthetic whole-root rotation
  DECISION = synthetic-only precedent; it is not an app-only updater and must not be reused for live app-only mutation

update_transaction._ExclusiveFileLock / _write_json_durable:
  EXISTING_OWNER = generic cross-process lock and atomic durable JSON write used by a DB migration transaction
  DECISION = G1 may promote/reuse these generic primitives; the SQLite transaction, BEGIN IMMEDIATE, migration phases and database writes are not updater barriers and are not reused

MaintenanceTransaction:
  DECISION = database-migration ownership only; do not use as the app updater engine or mutate the operational DB

_live_preflight process census:
  EXISTING_OWNER = CIM exact-path census with a tasklist image-name fallback whose executable-path authority is unknown
  DECISION = reuse only when exact path authority is available; unknown path authority fails closed

scripts/publish_windows_release.ps1:
  EXISTING_OWNER = staged Current/Previous rotation defaults to a sibling directory named Crawler tool
  DECISION = G1 must remove that second-installation destination behavior; it must never create the sibling root

scripts/clean_dev.ps1:
  EXISTING_OWNER = repo-generated cleanup allowlist
  DECISION = preserve governed evidence and runtime data; no cleanup is run by this WP

CodeGraph 1.5.0 was invoked before bounded source fallback in prior Planner read-in and independently by this Builder with `mcp__codegraph__codegraph_explore` using `D:\QI Technology\QI Crawler\egp-crawler-python`. Builder queries covered `operational_release.py`, `operational_update.py`, `update_transaction.py`, the publisher, and clean-dev. The current query returned OperationalPaths callers in the read-only classifier and release code, the classifier test owner, the synthetic whole-root promotion chain, and the independent MaintenanceTransaction caller/test. Direct source fallback was limited to CodeGraph gaps in the PowerShell publisher/clean-dev scripts, path registry and governed docs. This is impact evidence, not edit authority or completeness proof.

### Journal authority map

D:\QI-Crawler\control\update_marker.json is only the pointer to one active attempt. D:\QI-Crawler\control\updates\<update_id>\state.json is the authority. The journal has an immutable update ID, monotonically increasing transition sequence, retained prior transitions, exact old/new application and acceptance identities, first operational mutation time, pending action, and terminal disposition. A journal transition is durably and atomically recorded before each dangerous filesystem operation. Cryptographic hash chaining is not required and is not added.

The canonical transient generation is root-local at D:\QI-Crawler\.update\<update_id>\{stage,old,failed}. Marker and journal remain until the terminal journal and evidence are durable. A terminal historical journal is not an active update and must not block every later startup. Marker without a valid matching journal, a nonterminal journal without its marker, or an unreferenced transient directory fails closed.

### Old-binary protection decision

The installed 0.10.0 binary is non-cooperative and does not honor the new marker or updater lock. A cooperative lock alone is insufficient. The G1 barrier combines the existing exact executable-path process census with a Windows Restart Manager resource query (`RmRegisterResources` / `RmGetList`) over the exact old application image and Data/config/database/WAL/SHM paths. Every reported process must be correlated to an exact executable image path; missing, inaccessible or mismatched path authority is HOLD. Tasklist image-name-only fallback is forbidden. In addition, G1 holds deny-share Windows handles for the active config/database and any present WAL/SHM across cutover, then moves only the app directory on the same volume and repeats the process/resource query before v2 acceptance can be committed. The census is a fail-closed safety barrier, not a claim that Windows exposes every possible handle or proves absence beyond these queried paths.

No census is described as exact when path authority is unknown. Tasklist image-name-only fallback, an inaccessible process image, a resource-census error, a sharing violation, a remaining process/resource holder, an unexpected sidecar, or an identity mismatch is HOLD. No process is killed. Tests must inject old-process/resource appearance before the first mutation, between census and rotation, while an executable/image or Data file is held open, after rotation, on the DB open attempt while exclusive handles are held, on rename sharing violation and after partial mutation. No acceptance commit is permitted while an old process/resource holder remains.

### Filesystem intent/confirmation contract

For each dangerous app, acceptance, marker or recovery operation: append durable INTENT with sequence and exact expected before/after identities; execute exactly one filesystem mutation; observe the affected identities and existence; append CONFIRMED. A crash after mutation but before confirmation is APPLIED_NOT_CONFIRMED, never presumed success. Before the first operational installation mutation, a failure is FAILED_NO_MUTATION only when unchanged identity is proved. After it, interference/error is RECOVERY_REQUIRED, never NO UPDATE. Atomic JSON replacement may implement durability, but it may not discard prior transitions.

Staging the new app and making recovery/LKG copies are pre-mutation preparation. first_mutation_at identifies the first change to the active installed app or active acceptance. No database write, checkpoint, migration, restore or Data/config rewrite is part of this updater.

### Recovery decision matrix

| Observed journal/filesystem state | Required result |
| --- | --- |
| Before active mutation; prior app and acceptance identities unchanged | FAILED_NO_MUTATION; preserve attempt evidence |
| Pending operation; exact prior app and acceptance still present | Resume only by appending a new recovery intent; otherwise fail closed |
| Active mutation started; exact new application plus exact v2 acceptance observed | Forward completion is eligible only after read-only postcheck and zero old process/resource holders |
| Active mutation started; acceptance not committed; exact prior application and acceptance are available | Restore only those exact prior app/acceptance identities; retain failed new generation; never restore DB |
| Any missing, corrupt, mismatched, ambiguous or inaccessible identity | RECOVERY_REQUIRED / HOLD; preserve all generations and evidence |

Recovery records append new RECOVERY_INTENT, RECOVERY_CONFIRMED or ATTEMPT_FAILED_RECOVERED transitions. Historical transitions are retained.

### Database sentinel query set

The supported schema authority is Alembic 0022_add_tender_recovery_events and the existing SQLAlchemy model/migration definitions. A private captured snapshot is checked read-only with:

1. PRAGMA quick_check, requiring exactly ok;
2. PRAGMA foreign_key_check, requiring no violations;
3. alembic_version, requiring exactly 0022_add_tender_recovery_events;
4. required-table and required-column checks for notices, attachments, documents, document_extractions, document_evidence, tender_cases, tender_releases, tender_document_memberships, tender_operational_revision_events and tender_recovery_events;
5. one deterministic bounded primary-key row sample from each core table family and exact aggregate row counts for notices, documents, cases/releases/memberships and recovery events, with values kept out of public logs.

These are data-compatibility sentinels, not proof that every business record is semantically valid. The source DB/config/WAL/SHM identities must remain unchanged across the updater interval. Snapshot restore is never authorized.

### Acceptance v2 and LKG

Acceptance v1 behavior is preserved for v1 receipts. V2 binds the current application source/build/executable independently from the immutable migration source, migration receipt bytes/hash, original 0020 to 0022 revisions, and the data-root/config path contract. The migration receipt and its baseline meaning are never rewritten to match a newer application SHA. Runtime writes to the mutable operational DB do not invalidate v2 by requiring its current bytes to match the migration-time DB hash.

The LAST_KNOWN_GOOD manifest binds one exact application generation and an immutable pre-update DB/config snapshot with their hashes, the migration/acceptance identities, a runtime-verification reference, and restore-rehearsal status. Any runtime verification in G1 is synthetic/test evidence only; no live launch or restore is performed.

### Path Registry disposition

D:\QI-Crawler-Update-State and D:\QI-Crawler-Update-Rollback were rechecked and are absent. Preserve their existing B09 RESERVED path IDs and historical resolver; those external UPDATE_VOLUME IDs remain reserved only under their prior B09 authority, are not selected by this Parent, and are not materialized. Add a distinct fixed ROOT.OPERATIONAL for the Human-approved D:\QI-Crawler installation and register marker, journal, lock, stage, old, failed, acceptance/LKG, and immutable snapshot families under that root. The new Parent binding selects only these root-local operational IDs. All new runtime paths start RESERVED until independently observed. Registration remains locator-only and grants no live-update authority.

## Exact write allowlist

Only these tracked paths may change in this WP:

src/qi_crawler/__init__.py
src/qi_crawler/operational_release.py
src/qi_crawler/operational_update.py
src/qi_crawler/standalone.py
src/qi_crawler/update_transaction.py only for a proved generic lock/durable-writer reuse
scripts/update_operational_release.py
scripts/generate_release_metadata.py
scripts/publish_windows_release.ps1
scripts/clean_dev.ps1
tests/test_operational_release.py
tests/test_operational_update.py
tests/test_standalone.py
tests/test_update_transaction.py only if its generic primitive changes
tests/test_release_governance.py
tests/test_windows_installer.py
AGENTS.md
CHANGELOG.md
HUONG_DAN_SU_DUNG.md
docs/agent/OPERATIONAL_RELEASE_CONTRACT.md
docs/agent/CANDIDATE_RELEASE_CONTRACT.md
docs/agent/PATH_REGISTRY_CONTRACT.md
docs/agent/PATH_REGISTRY.yaml
docs/agent/MASTER_ROADMAP_DELTA.md
docs/agent/FEEDBACK_LEDGER.md
docs/agent/KNOWN_FAILURE_MODES.md only on a proved material trigger
docs/agent_handoff/CURRENT.md only at a governed transition
docs/agent_handoff/history/<exact-parent-snapshot>.md
docs/superpowers/plans/WP-OPS-QI-SINGLE-INSTALLATION-AND-LEGACY-ROOT-RETIREMENT-01.md

PROJECT_MEMORY.md is not writable for unmerged G1 facts. tools/release/**, all other B09 bridges, workflow/dependency files, hooks/configuration, operational data, AppData, shortcut, candidate, backup and release artifacts are out of scope.

## G1 stages and acceptance

### G1.0 — resolve and freeze design

Complete the maps above, path registrations, Work Order and governed entry handoff before behavior edits. Reuse capability-owned modules. Do not create another updater engine. Run pytest collection-only before the first test change and record the baseline with zero collection errors.

Initial collection baseline, before any test edit:

```text
COMMAND = .venv/Scripts/python.exe -m pytest --collect-only -q --basetemp .tmp/WP-OPS-QI-SINGLE-INSTALLATION-AND-LEGACY-ROOT-RETIREMENT-01/20260928T151949Z/p
EXIT = 0
RESULT = 1,679 TESTS COLLECTED IN 7.71s; ZERO COLLECTION ERRORS; NO TESTS EXECUTED
RUN_ROOT = .tmp/WP-OPS-QI-SINGLE-INSTALLATION-AND-LEGACY-ROOT-RETIREMENT-01/20260928T151949Z
RETAINED_LOG = collection-baseline.log; 165,024 BYTES
RUN_ROOT_INVENTORY = 1 FILE; 165,024 BYTES; 0 SUBDIRECTORIES
D_FREE_BYTES = 19,382,415,360 BEFORE; 19,382,247,424 AFTER; ABOVE 10 GiB RESERVE
RUNTIME = REPOSITORY .venv; NO INSTALL OR RUNTIME CHANGE
```

### G1.1 — application update, acceptance and recovery

TDD RED then GREEN for acceptance v2, append-only state, same-volume app-only staging/rotation, Windows old-binary resource/process protection, DB/config/sidecar byte and existence preservation, exact recovery classification, startup guard and failure injection. Preserve the read-only Bridge A classifier. Use synthetic/private roots only. Never execute the installed EXE or any live update.

The CLI in scripts/update_operational_release.py remains thin and defaults to non-mutating inspection; any future live execution entry must require the separately governed explicit guard and exact root/bundle identity. G1 does not execute that path.

### G1.2 — lifecycle, governance and cumulative verification

Extend LAW 16 concisely with the single operational root/entry point and finite technical-root lifecycle. The root-local `.update/<update_id>` stage/old/failed family is finite transient state: after terminal success and durable journal/evidence, it requires a mandatory cleanup disposition and next action; deletion occurs only in a separately authorized cleanup step. Failure or `RECOVERY_REQUIRED` content remains retained until recovery/disposition. `control/updates` journals and LKG remain durable. Update operational/candidate acceptance contracts; make publisher outputs incapable of creating the sibling Crawler tool installation; make clean-dev preserve durable evidence; add only synthetic archive/locator contracts, no real legacy archive; prepare consistent internal 0.10.1 source metadata and changelog without build/release. Synchronize Delta/Feedback/CURRENT at governed transitions. Audit every task-created artifact for retained bytes; cleanup is not part of this WP.

## Verification contract and budgets

CI FITNESS CONTRACT
CURRENT WP: WP-OPS-QI-SINGLE-INSTALLATION-AND-LEGACY-ROOT-RETIREMENT-01
CAPABILITY UNDER CHANGE: One-installation Windows app-only update and recovery support
CRITICAL RISKS: old non-cooperative process races; DB/config/WAL/SHM mutation; false acceptance; crash ambiguity; data loss; duplicate roots
BASELINE GATES TO KEEP: Existing pytest and Ruff; existing CI required jobs; collection integrity
WP-SPECIFIC GATES REQUIRED: v1 compatibility; v2 provenance; all transition/recovery failures; Windows exclusive handle/process/resource tests; exact DB/config/sidecar invariants; synthetic-only update; publisher/clean-dev root lifecycle; path budget; locator consistency
GATES NOT REQUIRED YET: G2 binary build; G3 real archive; installer; live update; operational launch; shortcut; real migration/restore
MAX JOB RUNTIME: Targeted contract family 10 minutes; affected suites 15 minutes; one full sequential pytest run 30 minutes; Ruff 10 minutes; docs/static checks 5 minutes
CI CHANGE REQUIRED BEFORE IMPLEMENTATION: NO
RATIONALE: Existing required tests and Windows/Ubuntu jobs cover current code; this Work Order adds only exact local acceptance tests and does not modify CI.

Use the repository .venv without installing or altering runtime dependencies. Initial and final collection-only runs must have zero collection errors and no unexplained decrease. Run targeted behavior tests RED/GREEN, affected tests, the full sequential suite exactly once with a fresh short task-owned PATH.DEV.TEST_TEMP basetemp, python -m ruff check ., git diff --check, exact name-status/scope, no source deletion, and tracked/index status. Full-suite budget is 30 minutes. Scratch cap is 20,000 files and 1 GiB per run, based on the retained previous full-run maxima of 14,033 files and 621,941,751 bytes; preserve at least 10 GiB free on D:. Check file count/bytes during and after execution when possible; stop/hold on the first cap breach and retain exact logs. No retry of the full suite, no cleanup, no skip/xfail/assertion weakening or gate reduction.

Synthetic operational fixture/run ceiling: 10,000 files, 512 MiB, one fresh run root; preserve at least 10 GiB free. Do not stage ignored operational/runtime data or secrets in Git.

## Plugin applicability and evidence

Every invocation record must contain PLUGIN, PURPOSE, INVOCATION, RESULT, FALLBACK, IMPACT_RADIUS, EDIT_RADIUS, TEST_RADIUS, LIMITATION. Use USED_AND_SUCCEEDED, USED_WITH_FALLBACK, TOOL_UNAVAILABLE, or NOT_APPLICABLE; installed/configured is not evidence of use.

qi-context-boot = REQUIRED
CodeGraph = REQUIRED before relevant structural edits; seed queries cover OperationalPaths, read-only classifier, existing promotion, reusable file-lock/journal helper, standalone gate, publisher and clean-dev; source fallback is bounded
systematic-debugging = REQUIRED before incident/defect fixes
test-driven-development = REQUIRED before every behavior change
verification-before-completion = REQUIRED before PASS/DONE/commit/handoff claims
codebase-memory = REQUIRED_ACTION_READINESS_ONLY; no index is authorized
computer-use = NOT_APPLICABLE

G1.0 invocation evidence:

```text
PLUGIN = qi-context-boot
PURPOSE = Canonical role, roadmap, and handoff read-in
INVOCATION = Checked the available skill catalog; qi-context-boot was not exposed in this execution context; read AGENTS.md, full MASTER_ROADMAP.md, MASTER_ROADMAP_DELTA.md, OPERATING_MODEL.md, ROLE_BOOT_AND_PROMPT_PROFILES.md, LOCAL_STAGED_INTEGRATION.md and CURRENT.md directly
RESULT = TOOL_UNAVAILABLE
FALLBACK = Full canonical governance read-in and live identity/authority reconciliation
IMPACT_RADIUS = Current roadmap, role and WP entry authority
EDIT_RADIUS = NONE DURING READ-IN
TEST_RADIUS = NONE
LIMITATION = The missing skill exposure does not imply the governance documents or other contexts are unavailable
```

Codebase Memory skill read access previously returned an access denial in this execution context; that exact skill read was not retried. This Builder made one published read-only readiness call, `mcp__codebase_memory_mcp__list_projects(detail="identity", limit=25, offset=0)`: the MCP call succeeded and returned zero indexed projects. No index attempt was made. Route structural questions through CodeGraph and bounded governed source/docs fallback; do not describe Codebase Memory as operationally ready. Graph/tool evidence never grants scope.

### G1.0 Builder tool receipts

```text
PLUGIN = CodeGraph
PURPOSE = Discover operational-update/source impact and avoid duplicating the read-only classifier or database-migration transaction engine
INVOCATION = mcp__codegraph__codegraph_explore(projectPath="D:\\QI Technology\\QI Crawler\\egp-crawler-python", query="operational_release.py acceptance receipt path operational root app-only update; update_transaction.py _ExclusiveFileLock _write_json_durable; publish_windows_release.ps1 output roots; clean_dev.ps1 deletion targets")
RESULT = USED_WITH_FALLBACK
FALLBACK = Bounded source fallback only for unindexed PowerShell, registry and contract details
IMPACT_RADIUS = OperationalPaths callers, read-only classifier, synthetic whole-root promotion, MaintenanceTransaction, publisher and clean-dev
EDIT_RADIUS = Approved G1 source/script/governance allowlist only
TEST_RADIUS = Approved operational-release/update/standalone/transaction/release-governance/Windows-installer tests
LIMITATION = Graph is structural evidence; no live path, process, DB, startup or mutation proof

PLUGIN = codebase-memory
PURPOSE = Read-only index readiness check; no index attempt authorized
INVOCATION = mcp__codebase_memory_mcp__list_projects(detail="identity", limit=25, offset=0)
RESULT = USED_WITH_FALLBACK
FALLBACK = Zero projects returned in the Builder readiness call; Builder made no index call; CodeGraph and bounded source/docs remain the permitted exploration path
IMPACT_RADIUS = Structural-discovery readiness only
EDIT_RADIUS = NONE
TEST_RADIUS = NONE
LIMITATION = This receipt records Builder's call only; Planner-side index deviation is documented below; the prior skill-path access denial is context-specific and was not retried
```

Codebase Memory was readiness-only for this Work Order; Builder did not call
`index_repository`. During G1.2, Planner accidentally issued three
`index_repository` calls. Each returned `aborted_previous_preserved`; a later
project list still returned zero projects, and no project, index, or repository
artifact was published. This is a Planner-side procedural deviation, not
successful Codebase Memory use. No retry is authorized.

## Artifact and path budget

PATH_REGISTRY_BASELINE = revision 1.0.21; SHA256 object 100a2e6fac99667614d67aae7c1f57c579a36e82
PATH_REGISTRY_IMPACT = ADD_ENTRY
PATH_REGISTRY_RESULT = revision 1.0.23 candidate; 65 unique PATH_IDs and 21 unique WP bindings; new root-local ROOT.OPERATIONAL families plus exact ROOT.REPO candidate/published artifact families; reserved future G3 locators; prior B09 UPDATE_VOLUME identifiers retained unchanged
ROADMAP_REF = Master Roadmap Cross-cutting Windows / Team Bid delivery; Engineering Toolbox / Plugins
WP_ID_AND_AUTHORITY = this Human-approved Work Order
PATH_IDS_USED = PATH.GOV.PLAN; PATH.GOV.HANDOFF; PATH.GOV.DOCUMENT; PATH.GOV.DOCS; PATH.REPO.SOURCE; PATH.REPO.TESTS; PATH.REPO.SCRIPTS; PATH.DEV.TEST_TEMP; PATH.EVIDENCE.WP_RUN; root-local operational single-installation families
UNREGISTERED_WRITE_PATHS = NONE
MAX_LOCAL_TEST_SCRATCH = 20,000 files / 1 GiB / one full run / 10 GiB untouched D: reserve
MAX_SYNTHETIC_RUNTIME_TEST = 10,000 files / 512 MiB / one fresh run / 10 GiB untouched D: reserve
LIVE_OPERATIONAL_MUTATION = ZERO
COMPACT_SCRATCH_TOKEN = `w3` maps `.tmp/w3/<six-hex-run-id>/t` to this Parent under PATH.DEV.TEST_TEMP; exact G1.2 runs `d29f6c` and `e36fc2` are Builder-owned verification roots.

New root-local paths must be containment/reparse checked, collision-rejected, same-volume and path-length checked before writes. Reject projected Windows paths over 240 characters; require at least 20 characters headroom below the 260-character legacy limit for each accepted staged/old/failed file path. If any file in a candidate generation cannot meet the limit, fail closed before mutation.

## Stop conditions

Stop and return to Planner on identity/lineage drift, tracked/index dirt, branch collision, external root requirement, second updater engine, unknown path/resource authority, unresolved old-binary race, Windows file-handle behavior not provable, ambiguous journal recovery, Data/sidecar/config change, acceptance provenance mismatch, path/storage budget failure, unexplained test collection decrease, out-of-allowlist need, required gate red without authorized resolution, or any live/shortcut/migration/restore/build/release/delete operation.

## Required Builder return

Report exact base/head/branch and carried history; semantic commits; changed files; G1.0 maps and stage outcomes; pytest collection baseline/final; RED/GREEN/affected/full/Ruff/diff evidence; path and artifact inventories/budgets; plugin invocation receipts; remote checkpoint/no-PR status; root and untracked preservation; achieved/not-achieved claims; open blockers; SPINE_IMPACT, SPINE_TARGET_FILES, SPINE_SYNC_STATE; exactly one next action; NEXT_AUTHORITY=PLANNER_ARCHITECT. Stop after Builder return. Planner assigns Tester and Reviewer; no direct role messaging.

## G1.2 Builder execution evidence — 2026-09-29

```text
G1.2_SCOPE = REPOSITORY ARTIFACT PUBLISHER; CLEAN-DEV ROOT GUARD; ACCEPTANCE/METADATA CONTRACTS; LAW 16; PATH REGISTRY; SYNTHETIC G3 LOCATORS ONLY
OPERATIONAL_ROOT = D:\QI-Crawler; NO SECOND ROOT; NO DATA CLONE; NO LIVE UPDATE, BUILD, PUBLISH, LAUNCH, ARCHIVE OR CLEANUP
INTERNAL_SOURCE_VERSION = 0.10.1; NOT BUILT, PACKAGED, TAGGED, RELEASED, INSTALLED OR DEPLOYED
HISTORICAL_LIVE_VERSION = 0.10.0; LIVE PROMOTION GATE UNCHANGED; SOURCE FIX DOES NOT UPDATE THE INSTALLED BINARY
CODEBASE_MEMORY = READINESS_ONLY; BUILDER_INDEX_CALLS=0; PLANNER_SIDE_DEVIATION=3 index_repository calls, all aborted_previous_preserved; zero projects and no project/index/repository artifact published; no retry
BASELINE_COLLECTION = 1,775; ZERO COLLECTION ERRORS; BEFORE G1.2 TEST EDITS
TDD_INITIAL_RED = 7 FAILED / 2 PASSED OF 9 TARGET NODES; WINDOWS PUBLISHER, CLEAN-DEV, VERSION AND LOCATOR CONTRACTS
PUBLISHER_TARGETED = 3 PASSED / 1 SKIPPED; PATH/IMMUTABILITY/SOURCE IDENTITY COVERAGE; REPARSE TEST SKIPPED BECAUSE SYMLINK CREATION WAS UNAVAILABLE
INVALID_AFFECTED_RUN = 159 COLLECTED; 147 PASSED / 3 SKIPPED / 9 FAILED; 146.27s; INVALID_FOR_ACCEPTANCE because long basetemp caused Windows path-limit failures (SQLite backup open, projected publisher path, nested test fixture). No assertion or 240-char gate was weakened.
VALID_SHORT_AFFECTED_RUN = 159 COLLECTED; 155 PASSED / 3 SKIPPED / 1 FAILED; 153.63s; sole failure was the legacy 0.10.0 test calling the new default 0.10.1 validator.
EXACT_NODE_CORRECTION = test_live_promotion_success_is_coherent_and_preserves_source; explicit LIVE_VERSION expectation; 1 PASSED / 1 WARNING; 3.03s. The legacy fixture explicitly asserts LIVE_VERSION remains 0.10.0. No production gate was relaxed. The entire affected family was not rerun after this test-only expectation correction.
PYTEST_WARNING = PytestCacheWarning WinError 5 writing repository .pytest_cache; non-failing, retained as environment limitation
FULL_SEQUENTIAL_PYTEST = NOT RUN BY BUILDER; RESERVED FOR INDEPENDENT TESTER
RUFF = SCOPED PYTHON FILES PASS, exit 0; initial command incorrectly included clean_dev.ps1 and Ruff reported PowerShell parse errors; corrected Python-only invocation passed. REPO-WIDE RUFF NOT RUN.
COLLECTION_FINAL = 1,781; ZERO COLLECTION ERRORS; 2.84s; `.tmp/w3/fb4a10/t`; +6 from the 1,775 baseline; no unexplained decrease
COMPACT_SCRATCH_MAPPING = PATH.DEV.TEST_TEMP token `w3` maps `.tmp/w3/<six-hex-run-id>/t` to this Parent. Runs: `d29f6c` affected family, `e36fc2` exact-node correction.
SCRATCH_INVALID_RUN = `.tmp/WP-OPS-QI-SINGLE-INSTALLATION-AND-LEGACY-ROOT-RETIREMENT-01/20260929T1Z/affected`; 1,721 files / 29,135,568 bytes; retained; test output was returned in the execution transcript, not separately redirected.
SCRATCH_VALID_RUN = `.tmp/w3/d29f6c/t` plus its captured affected.log; 1,757 files / 31,850,472 bytes; retained.
SCRATCH_EXACT_NODE = `.tmp/w3/e36fc2/t` plus failing-node.log; 16 files / 3,659,972 bytes; retained.
D_FREE_AFTER_TESTS = 18,849,906,688 bytes; minimum 10 GiB reserve preserved
G3_ARCHIVE_AND_RECEIPT = RESERVED LOCATORS ONLY; NO REAL ARCHIVE; UNKNOWN REMAINS KEEP
CLEANUP = NOT AUTHORIZED OR EXECUTED; NO ARTIFACT DELETED
FEEDBACK = EXISTING HUMAN A0 FB-0058 REMAINS AUTHORITATIVE; NO NEW HUMAN DECISION IS ORIGINATED BY THIS BUILDER RESULT
SPINE_IMPACT = MULTIPLE
SPINE_TARGET_FILES = AGENTS.md; docs/superpowers/plans/WP-OPS-QI-SINGLE-INSTALLATION-AND-LEGACY-ROOT-RETIREMENT-01.md; docs/agent/CANDIDATE_RELEASE_CONTRACT.md; docs/agent/OPERATIONAL_RELEASE_CONTRACT.md; docs/agent/PATH_REGISTRY_CONTRACT.md; docs/agent/PATH_REGISTRY.yaml; docs/agent/MASTER_ROADMAP_DELTA.md; docs/agent_handoff/CURRENT.md; CHANGELOG.md; HUONG_DAN_SU_DUNG.md
SPINE_SYNC_STATE = PASS AFTER FINAL CURRENT/DIFF VALIDATION
EXACTLY_ONE_NEXT_ACTION = PLANNER REVIEWS THIS BUILDER RESULT AND ASSIGNS TESTER/REVIEWER UNDER THE EXISTING LEASE
NEXT_AUTHORITY = PLANNER_ARCHITECT
```

The valid short-root affected run plus the exact-node correction is the complete
Builder evidence for the touched test families; it does not replace the one
full sequential suite reserved for Tester. No Product release or maturity
promotion is claimed. The three Planner-side index calls are recorded as an
administrative deviation only and do not establish Codebase Memory readiness.

```text
PLUGIN = test-driven-development
PURPOSE = G1.2 publisher, clean-dev, version and locator behavior contracts
INVOCATION = Wrote the discriminating Windows/release-governance tests before implementation; initial targeted RED was 7 failed / 2 passed of 9 nodes, followed by focused and affected-family GREEN evidence above
RESULT = USED_AND_SUCCEEDED
FALLBACK = None
IMPACT_RADIUS = Candidate artifact publication, repo cleanup boundary and metadata/locator checks
EDIT_RADIUS = G1.2 implementation and test allowlist only
TEST_RADIUS = Windows installer/repo hygiene/release governance/operational release tests
LIMITATION = Reparse-link test skipped because host symlink creation was unavailable; test-only exact legacy version expectation was corrected after the short affected run

PLUGIN = systematic-debugging
PURPOSE = Diagnose the first archive visibility/path observation before assertion changes
INVOCATION = Inspected the exact archive identity/path, parent enumeration and recursive listing, then direct stat/open after publisher exit; confirmed the entry was the final archive, not `.stage-*`, and retained archive contents were readable on a short registered root
RESULT = USED_AND_SUCCEEDED
FALLBACK = None
IMPACT_RADIUS = Synthetic repository archive observation only
EDIT_RADIUS = Publisher test assertion and bounded task scratch
TEST_RADIUS = Focused Windows publisher test
LIMITATION = Synthetic temporary-root evidence only; no archive was published into the repository or operational root

PLUGIN = verification-before-completion
PURPOSE = Final evidence gate before Builder return/commit
INVOCATION = Read the installed skill and ran exact collection, scoped Python Ruff, registry/static, scope, diff-check and Git status checks before the final claim
RESULT = USED_AND_SUCCEEDED
FALLBACK = None
IMPACT_RADIUS = G1.2 Builder result
EDIT_RADIUS = Authorized G1 paths only
TEST_RADIUS = Affected test families plus collection and scoped lint
LIMITATION = No full sequential pytest, full-repository Ruff, build, hosted CI or operational execution by Builder
```

## G1-C01 — full-suite setup failure diagnosis

Planner assigned this bounded diagnostic after the independent Tester consumed the Work Order's single full sequential run. The exact Tester command was `.venv\Scripts\python.exe -m pytest -n 0 --basetemp=.tmp/w3/d9e71b/t`; it exited 1 with 1,780 setup errors, one skip, two warnings, and 52.63 seconds. Collection was 1,781 with zero collection errors. The captured output lost the shared setup traceback, so the root cause is `UNKNOWN`; do not infer a cause from the error count.

The run directory `.tmp/w3/d9e71b` was absent after the run, with zero files/bytes, and D: free space was 18,849,390,592 bytes. Tester performed no retry, Ruff, further statics, edits or cleanup. The live remote `origin/main` could not be verified because `git ls-remote` could not connect; the local `origin/main` remains the expected `caf983691da60d4eaf990d09e9e1788692aabaac`.

This correction authorizes at most one simple collected test node that necessarily traverses common setup, using `-x -vv --tb=long`, one fresh compact registered `.tmp/w3/<six-hex>/t` basetemp, and a retained full stdout/stderr log outside the `t` child but inside the same run directory. Maximum runtime is five minutes, 5,000 files, and 256 MiB; preserve more than 10 GiB free. No retry, full-suite rerun, cleanup, or other test command is authorized by this correction. Trace the recovered setup exception through its bounded caller/fixture chain before deciding whether any fix is warranted. A code change requires evidence that the cause lies inside the existing exact G1 allowlist; anything outside it is a Planner scope-expansion hold.

```text
MICRO_CORRECTION = G1-C01-FULL-SUITE-SETUP-DIAGNOSIS
AUTHORITY = PLANNER-ASSIGNED UNDER EXISTING HUMAN-APPROVED PARENT LEASE; NO NEW HUMAN OR REVIEWER DECISION
TESTER_REPORT_ID = NOT_SUPPLIED_IN_PLANNER_PACKET; SOURCE=PLANNER-ADMITTED TESTER SUMMARY
TESTER_RESULT = 1,781 COLLECTED; 1,780 SETUP ERRORS; 1 SKIP; 2 WARNINGS; EXIT 1; 52.63s
TESTER_TRACEBACK = LOST FROM CAPTURED OUTPUT; ROOT CAUSE UNKNOWN
TESTER_SCRATCH = .tmp/w3/d9e71b ABSENT AFTER RUN; 0 FILES / 0 BYTES; D: FREE 18,849,390,592 BYTES
DIAGNOSTIC_BUDGET = AT MOST ONE TEST NODE; 5 MINUTES; 5,000 FILES; 256 MiB; ONE FRESH RUN; ZERO RETRIES; >10 GiB FREE
FULL_SUITE_REPLACEMENT = NOT AUTHORIZED
REMOTE_MAIN = UNVERIFIED LIVE; git ls-remote COULD NOT CONNECT; LOCAL origin/main = caf983691da60d4eaf990d09e9e1788692aabaac
SCOPE_EXPANSION_REQUIRED = NOT YET DETERMINED; DO NOT EDIT OUTSIDE EXISTING G1 ALLOWLIST
```

Plugin evidence for this diagnosis: `systematic-debugging` was read and applied before diagnosis. CodeGraph was queried for pytest fixture/setup relationships but returned broad unrelated symbols and did not isolate the common setup path; bounded direct source/test reading is the fallback. No Codebase Memory index is authorized or used. `test-driven-development` is required only if evidence establishes an in-scope behavior correction; a harness diagnosis alone does not justify a code edit.

### G1-C01 diagnostic outcome — one node did not reproduce

The single authorized diagnostic used the simple collected node `tests/test_parser.py::test_parse_money_vnd`. It passed: one passed, one non-failing `PytestCacheWarning`, 1.31 seconds, exit 0. The node exercised `tests/conftest.py`'s session `_alembic_template` setup and autouse `_prepare_database_for_tests` setup; the session template database was created successfully. This does not reproduce or explain the Tester run's 1,780 setup errors, and it does not establish an environment-only or product cause. The root cause remains `UNKNOWN` because the Tester traceback was lost and this diagnostic did not recover it.

The exact command was `.venv\Scripts\python.exe -m pytest -n 0 -x -vv --tb=long --basetemp=.tmp/w3/fce7de/t tests/test_parser.py::test_parse_money_vnd`. Full stdout/stderr was retained at `.tmp/w3/fce7de/diagnostic.log` (1,190 bytes; SHA-256 `374738A04811028D068CB02710CB14DBA6FAAE158822F4D5317779F8A21D9A49`). The fresh run root contained two files totaling 914,598 bytes: the log and the pytest-created `t/alembic-template0/template.db`. D: free space afterward was 18,848,382,976 bytes. The run stayed within the one-node, five-minute, 5,000-file, 256-MiB and >10-GiB-reserve limits. No cleanup occurred.

The one-node diagnostic budget is consumed (1/1); no retry or second node is authorized by G1-C01. No code/test correction was made, and no TDD behavior change was activated. Scope expansion is not established because no root cause or fix was found. The full sequential run remains consumed and RED; a replacement full-suite run is not authorized by this assignment. Return the unresolved setup cause to Planner for disposition.

```text
DIAGNOSTIC_NODE = tests/test_parser.py::test_parse_money_vnd
DIAGNOSTIC_COMMAND = `.venv\Scripts\python.exe -m pytest -n 0 -x -vv --tb=long --basetemp=.tmp/w3/fce7de/t tests/test_parser.py::test_parse_money_vnd`
DIAGNOSTIC_RESULT = EXIT 0; 1 PASSED; 1 NON-FAILING PytestCacheWarning; 1.31s
COMMON_SETUP_PATH = SESSION _alembic_template AND AUTOSETUP _prepare_database_for_tests RAN SUCCESSFULLY FOR THIS NODE; ROOT ERROR NOT REPRODUCED
ROOT_CAUSE = UNKNOWN; NO PRODUCT/ENVIRONMENT CLASSIFICATION
DIAGNOSTIC_LOG = `.tmp/w3/fce7de/diagnostic.log`; 1,190 BYTES; SHA256 374738A04811028D068CB02710CB14DBA6FAAE158822F4D5317779F8A21D9A49
SCRATCH_INVENTORY = 2 FILES / 914,598 BYTES; `t/alembic-template0/template.db` AND `diagnostic.log`; RETAINED; NO CLEANUP
D_FREE_AFTER_DIAGNOSTIC = 18,848,382,976 BYTES; >10 GiB RESERVE
DIAGNOSTIC_BUDGET = 1 OF 1 CONSUMED; NO RETRY OR SECOND NODE AUTHORIZED
REPLACEMENT_FULL_SUITE = NOT AUTHORIZED
CODE_OR_TEST_EDIT = NONE; TDD BEHAVIOR CHANGE NOT ACTIVATED
SCOPE_EXPANSION_REQUIRED = NOT ESTABLISHED; NO ROOT CAUSE OR FIX FOUND
NEXT = PLANNER DISPOSES THE NON-REPRODUCING DIAGNOSTIC HOLD AND DECIDES WHETHER NEW AUTHORITY IS WARRANTED
```

### G1-C01 Planner root-cause reconciliation — command contract failure confirmed

After the Builder return, Planner independently resolved the setup failure from
the admitted Tester invocation and repository pytest 8.4.2 runtime behavior.
With explicit `--basetemp`, `TempPathFactory.getbasetemp` removes the target if
present, then calls `basetemp.mkdir(mode=0o700)` without creating missing
parents. Tester correctly required fresh parent `.tmp/w3/d9e71b` to be absent
but passed child `.tmp/w3/d9e71b/t`; the parent therefore remained absent and
pytest could not create the child. `tests/conftest.py` has an autouse fixture
requiring `tmp_path`, so every executing test entered this setup path; the one
skipped test did not. The captured Tester output had lost the traceback, so
this cause is a Planner source/runtime reconciliation, not a traceback
recovered from that run.

The Builder's single-node diagnostic passed because `.tmp/w3/fce7de` had
already been created to retain `diagnostic.log`, allowing pytest to create
child `t`. That pass does not turn the Tester run into a pass or establish
product correctness. The Tester attempt remains a real failed verification
attempt with 1,780 setup errors, one skip, two warnings, exit 1. The absent
parent is a verified local runner/verification-command defect sufficient to
cause widespread setup failure. Because the old Tester tracebacks were not
retained, it is not independently proven to be the sole cause of all 1,780
setup errors. No G1 product defect is established. `CI_INFRASTRUCTURE_DEFECT`
here describes local verification infrastructure only and does not claim a
GitHub Actions failure.

Prevention for any future authorized nested compact basetemp is to create and
verify the bounded registered run parent first, retain stdout/stderr at that
parent outside the child, then invoke pytest with the absent child `t`.
Validate freshness, containment and budgets before invocation. Never precreate
`t`, because pytest owns and removes that child. This is a command-contract
correction only; no source or test file changed. The original full-suite
budget is consumed. At this initial Planner reconciliation, a replacement
full run remained unauthorized and Tester remained HOLD. The following Human
A0 authority addendum supersedes that pending-authority state.

```text
ROOT_CAUSE_CLASSIFICATION = LOCAL_VERIFICATION_COMMAND_CONTRACT_DEFECT; CI_INFRASTRUCTURE_DEFECT IS AN UMBRELLA FOR LOCAL VERIFICATION INFRASTRUCTURE ONLY, NOT GITHUB ACTIONS
PYTEST_RUNTIME = REPOSITORY .venv PYTEST 8.4.2; EXPLICIT BASETEMP CREATION USES mkdir(mode=0o700) WITHOUT parents=True
TESTER_PARENT_CHILD = FRESH PARENT .tmp/w3/d9e71b ABSENT; CHILD .tmp/w3/d9e71b/t PASSED AS --basetemp
COMMON_SETUP = tests/conftest.py AUTOSETUP FIXTURE REQUIRES tmp_path; MECHANISM IS SUFFICIENT TO CAUSE WIDESPREAD SETUP FAILURE; LOST TRACEBACKS DO NOT PROVE IT WAS THE SOLE CAUSE OF ALL 1,780; 1 SKIP DID NOT ENTER SETUP
BUILDER_DIAGNOSTIC_PARENT = .tmp/w3/fce7de ALREADY EXISTED FOR diagnostic.log; PYTEST CREATED CHILD t; NODE PASSED; DOES NOT PROVE WHOLE-SUITE CORRECTNESS
PREVENTION = CREATE/VERIFY BOUNDED RUN PARENT FIRST; RETAIN LOG OUTSIDE ABSENT CHILD t; VERIFY FRESHNESS/CONTAINMENT/BUDGET; NEVER PRECREATE t
PRODUCT_CAUSATION = NO G1 PRODUCT DEFECT ESTABLISHED; NO SOURCE/TEST CHANGE
OLD_RUN = CONSUMED AND RED; PRESERVE AS FAILED VERIFICATION, NOT PASS OR ABSENT
INITIAL_REPLACEMENT_RUN_AUTHORITY = NOT AUTHORIZED AT THIS INITIAL PLANNER RECONCILIATION; SUPERSEDED BY FOLLOWING HUMAN A0 ADDENDUM
INITIAL_TESTER_STATE = HOLD PENDING HUMAN AUTHORITY AT THAT RECONCILIATION; CURRENT AUTHORITY IS RECORDED IN FOLLOWING ADDENDUM
REMOTE_OR_OPERATIONAL_AUTHORITY = NONE; NO PUSH/PR/MERGE/RELEASE/LIVE OPERATION/CLEANUP
INITIAL_NEXT = PLANNER REQUESTS HUMAN AUTHORITY FOR ONE REPLACEMENT RUN; SUPERSEDED BY FOLLOWING HUMAN A0 DECISION
```

### G1-C01 replacement full-run authority — Human A0, 2026-09-29

Human A0 has now authorized exactly one replacement full sequential pytest
run, on the exact Git HEAD recorded at Tester preflight and with no code or
test change. This is a new verification authority; the original failed run
remains consumed RED history. Tester must resolve and record the exact HEAD at
entry, use a fresh absent registered `.tmp/w3/<new-six-hex>` run parent, verify
containment, reparse status, freshness and ownership, create that parent and
retain a writability proof there, and verify child `t` remains absent before
launch. Pytest alone owns creation/removal of child `t`.

Tester must retain complete stdout/stderr, traceback, true pytest exit code,
start/end times, summary, exact invocation and working directory outside
`t`, preserving the pytest exit code through any pipeline. Limits are 30
minutes, 20,000 files, 1 GiB scratch and at least 10 GiB free on D:, one run,
no retry and no cleanup. Only if pytest passes may Tester run exactly one
full `python -m ruff check .` plus the Work Order's prescribed read-only static
gates. Any required gate failure returns to Planner with evidence; this lease
does not authorize a fix or scope expansion. No push, PR, merge, release, live
operation or cleanup is authorized.

```text
HUMAN_AUTHORITY_SOURCE = DIRECT HUMAN A0 APPROVAL RELAYED IN PLANNER TASK `/root`, 2026-09-29; NO NEW DECISION ID INVENTED
REPLACEMENT_FULL_SEQUENTIAL_PYTEST = AUTHORIZED EXACTLY ONCE; RUN SEQUENTIALLY (`-n 0`); TESTER RESOLVES EXACT HEAD AT PREFLIGHT; NO CODE/TEST CHANGE
RUN_PARENT = FRESH ABSENT REGISTERED `.tmp/w3/<new-six-hex>/`; VERIFY CONTAINMENT/REPARSE/FRESHNESS/OWNERSHIP; CREATE/PRESERVE WRITABILITY PROOF
PYTEST_CHILD = `t` MUST BE ABSENT BEFORE LAUNCH; PYTEST ALONE CREATES/REMOVES IT
RETAINED_EVIDENCE = COMPLETE STDOUT/STDERR/TRACEBACK; TRUE EXIT CODE; START/END; SUMMARY; EXACT COMMAND AND WORKING DIRECTORY; ALL OUTSIDE `t`; PIPELINE MUST PRESERVE PYTEST EXIT
BUDGET = 30 MINUTES; 20,000 FILES; 1 GiB; >=10 GiB D: FREE; ONE RUN; NO RETRY; NO CLEANUP
FOLLOW_ON = IF FULL PYTEST PASS ONLY, ONE FULL `python -m ruff check .` AND PRESCRIBED READ-ONLY STATICS; ANY REQUIRED FAILURE => RETAIN EVIDENCE AND RETURN PLANNER; NO FIX/SCOPE EXPANSION
OLD_TESTER_RUN = EXIT 1; 1,780 SETUP ERRORS / 1 SKIP / 2 WARNINGS; CONSUMED RED HISTORY; NOT REWRITTEN
CAUSE_CONCLUSION = VERIFIED LOCAL COMMAND DEFECT SUFFICIENT TO CAUSE WIDESPREAD SETUP FAILURE; LOST TRACEBACKS MEAN NOT PROVEN SOLE CAUSE OF ALL 1,780
CI_INFRASTRUCTURE_LABEL = LOCAL VERIFICATION INFRASTRUCTURE ONLY; NO GITHUB ACTIONS FAILURE CLAIM
REMOTE_AND_LIVE_AUTHORITY = NONE
NEXT = PLANNER REVIEWS THIS AUTHORITY SYNC AND ASSIGNS TESTER THE ONE AUTHORIZED REPLACEMENT FULL RUN ON THE EXACT HEAD RESOLVED AT PREFLIGHT
NEXT_AUTHORITY = PLANNER_ARCHITECT
```

### G1-C02 version-document synchronization — Tester RED and bounded correction

At candidate HEAD `90806b72df381334632ae7b760cba53216409d6c`, the Human-authorized replacement sequential run collected 1,781 tests and reported 1,775 passed, 5 skipped, 1 failed, and 2 warnings in 879.33 seconds. The admitted failure is `tests/test_cli_help.py::test_release_version_is_synchronized_across_user_documents` at line 163. The test requires the exact version headings in both the changelog and Vietnamese user guide: `## 0.10.1` and `Co gi moi trong 0.10.1`. The first current heading is only `## Unreleased`; the second is `## Ghi chu noi bo chua phat hanh - 0.10.1`.

Planner classified this as a documentation synchronization `WP_CODE_DEFECT`, not a runtime or release defect. The native pytest process exit code is not independently established: the Tester wrapper reused reserved PowerShell `$PID` after launch. The retained stdout contains the full failure result, but no claim is made that the wrapper preserved the process exit code. This is not evidence of a GitHub Actions failure. The run remains consumed RED history; do not rerun RED or the full suite.

The approved minimal correction changes only those two headings, retaining explicit internal/unreleased/not-released wording and all existing explanatory text. No test, source, version constant, build, tag, release, installation, or capability changes are authorized. After this governance sync is committed, Builder may run exactly one targeted GREEN for the failing node, with a fresh registered compact run parent created and verified before launch, absent child `t` for pytest to own, complete logs outside `t`, and the native process object's `ExitCode` captured directly. Do not use reserved `$PID`. Stop after that one targeted run; there is no full-suite, Ruff, or retry authority in this correction.

```text
G1_C02_CANDIDATE_HEAD = 90806b72df381334632ae7b760cba53216409d6c
G1_C02_TESTER_FULL_RUN = 1,781 COLLECTED; 1,775 PASSED; 5 SKIPPED; 1 FAILED; 2 WARNINGS; 879.33s; RETAINED RED
G1_C02_FAILURE = tests/test_cli_help.py::test_release_version_is_synchronized_across_user_documents; BOTH DOCUMENT HEADINGS MUST MATCH INTERNAL 0.10.1 SOURCE METADATA
G1_C02_CLASSIFICATION = PLANNER WP_CODE_DEFECT; DOCUMENT SYNCHRONIZATION; NO RUNTIME/RELEASE DEFECT
G1_C02_NATIVE_EXIT = NOT_PROVEN; POWERSHELL WRAPPER REUSED RESERVED `$PID`; RETAINED TESTER STDOUT CONTAINS FAILURE SUMMARY; NO GITHUB ACTIONS CLAIM
G1_C02_SCRATCH = `.tmp/w3/f2a913`; 15,791 FILES / 621,117,062 BYTES; RETAINED; NO CLEANUP
G1_C02_PREVENTION = USE NON-RESERVED `$pytestProcessId`; CAPTURE PROCESS OBJECT `.ExitCode` DIRECTLY BEFORE ANY OTHER COMMAND
G1_C02_EDIT_SCOPE = CHANGELOG.md AND HUONG_DAN_SU_DUNG.md HEADINGS ONLY; NO TEST/SOURCE/VERSION-CONSTANT CHANGE
G1_C02_VERIFICATION = ONE TARGETED GREEN ONLY AFTER GOVERNANCE SYNC; NO RED RERUN, FULL SUITE, RUFF OR RETRY
G1_C02_RELEASE_IMPACT = INTERNAL SOURCE METADATA REMAINS 0.10.1; NO VERSION INCREMENT, BUILD, TAG, RELEASE, INSTALLATION OR CAPABILITY CHANGE
G1_C02_NEXT = BUILDER COMMITS GOVERNANCE SYNC, APPLIES THE TWO AUTHORIZED HEADING EDITS, RUNS ONE TARGETED GREEN AND RETURNS EVIDENCE TO PLANNER
```

### G1-C02 Builder result — targeted document contract GREEN

After governance commit `8d6eeac0bcacc8a443c9bc27548fb8b197be7a47`, Builder changed only the two authorized headings. The exact failing node passed once with the native `Start-Process` object's exit code captured directly before other commands. The run began at HEAD `8d6eeac`; the working tree contained only the two heading changes now committed as `38ab35d0362379ae64b19bba3f06ee0c9fabf732`.

```text
G1_C02_TARGETED_COMMAND = `.venv\Scripts\python.exe -m pytest -n 0 --basetemp=.tmp/w3/c02f29/t tests/test_cli_help.py::test_release_version_is_synchronized_across_user_documents`
G1_C02_TARGETED_RESULT = EXIT 0 FROM PROCESS OBJECT; 1 PASSED; 1 NON-FAILING PytestCacheWarning (WinError 5 writing repository `.pytest_cache`); pytest-reported 2.47s; wall 4.43s
G1_C02_TARGETED_HEAD = 8d6eeac0bcacc8a443c9bc27548fb8b197be7a47; WORKTREE HAD ONLY CHANGELOG/GUIDE HEADING EDITS; COMMITTED AS 38ab35d0362379ae64b19bba3f06ee0c9fabf732
G1_C02_TARGETED_TIMES = START 2026-09-29T06:11:25.6348784+07:00; END 2026-09-29T06:11:30.0641843+07:00
G1_C02_TARGETED_LOGS = `.tmp/w3/c02f29/targeted.stdout.log`; `.tmp/w3/c02f29/targeted.stderr.log`; metadata and parent-writable proof retained outside pytest-owned `t`
G1_C02_TARGETED_SCRATCH = `.tmp/w3/c02f29`; 5 FILES / 915,100 BYTES; child `t` created by pytest and retained; D: free after run 18,171,588,608 bytes; no cleanup
G1_C02_TARGETED_SCOPE = CHANGELOG.md AND HUONG_DAN_SU_DUNG.md ONLY; exact assertions now pass; no test/source/version-constant change
G1_C02_WHOLE_SUITE = STILL CONSUMED RED WITH 1 DOCUMENT FAILURE; NATIVE EXIT OF THE FULL RUN NOT INDEPENDENTLY PROVEN; NO SECOND FULL RUN, RUFF OR RETRY AUTHORIZED
G1_C02_TERMINAL_RELEASE_IMPACT = INTERNAL SOURCE METADATA REMAINS 0.10.1; NO VERSION INCREMENT, BUILD, TAG, RELEASE, INSTALLATION OR CAPABILITY CHANGE
G1_C02_BUILDER_NEXT = RETURN EXACT GOVERNANCE/DOC COMMITS AND BOUNDED TEST EVIDENCE TO PLANNER; NO REMOTE OR OPERATIONAL EFFECTS
```

### G1-C03 — preserve both changelog heading contracts

At exact candidate HEAD a1096bb2f80bc89adb52883765df498acceb1309, Tester used the Human-authorized replacement full-run allowance once, with a directly captured native process exit. The run collected 1,781 tests and reported 1,775 passed, 5 governed skips, 1 failed and 2 cache warnings in 1,112.01 seconds. The exact failure was tests/test_release_governance.py::test_changelog_has_target_release_section: the prior G1-C02 edit had replaced ## Unreleased with ## 0.10.1 - Internal, unreleased, satisfying the CLI synchronization test but violating this separate retained CHANGELOG contract. The run was one launch, exit 1, with the stated resource caps passing. Its RED history and .tmp/w3/78fe92/t evidence remain retained.

The Human A0 authority for that exact post-C02 full sequential run is recorded in Feedback entry FB-0060. This does not authorize another full run. The bounded G1-C03 correction is to restore an exact ## Unreleased heading above the existing ## 0.10.1 - Internal, unreleased section, preserving all 0.10.1 content and historical release headings. Both exact heading consumers must remain satisfied together. No test, Vietnamese guide, source, version constant, runtime, build, release, installation or capability change is authorized. After the governance sync, one targeted invocation may run both exact heading tests together; there is no full-suite rerun, Ruff, retry or remote authority.

~~~text
G1_C03_TESTER_REPORT = PLANNER-ADMITTED TESTER EVIDENCE; REPORT ID NOT SUPPLIED
G1_C03_FULL_RUN_HEAD = a1096bb2f80bc89adb52883765df498acceb1309
G1_C03_FULL_RUN = .venv\Scripts\python.exe -m pytest -n 0 -ra --basetemp=.tmp/w3/78fe92/t; PID 26204; NATIVE PROCESS EXIT 1; ONE LAUNCH / NO RETRY
G1_C03_RESULT = 1,781 COLLECTED; 1,775 PASSED; 5 GOVERNED SKIPS WITH CAPTURED REASONS; 1 FAILED; 2 CACHE WARNINGS; 1,112.01s
G1_C03_FAILED_NODE = tests/test_release_governance.py::test_changelog_has_target_release_section; exact required heading ## Unreleased missing
G1_C03_ROOT_CAUSE = G1-C02 PRESERVED THE 0.10.1 INTERNAL/UNRELEASED HEADING BUT REMOVED A SEPARATE REQUIRED ## Unreleased CONTRACT; BOTH MUST COEXIST
G1_C03_SCRATCH = .tmp/w3/78fe92/t; resource caps PASS; retained; no cleanup; unknown/untracked artifacts KEEP
G1_C03_HUMAN_AUTHORITY = HUMAN A0 AUTHORIZED THIS EXACT POST-C02 FULL RUN; ROUTED AS FB-0060; NO FURTHER FULL-RUN AUTHORITY
G1_C03_EDIT_SCOPE = CHANGELOG.md ONLY; RESTORE ## Unreleased ABOVE ## 0.10.1 - Internal, unreleased; preserve all section content/order
G1_C03_TDD = RETAINED FULL-RUN RED IS THE DISCRIMINATING EVIDENCE; DO NOT RERUN RED; ONE TARGETED GREEN INVOCATION CONTAINS BOTH EXACT CONTRACT NODES
G1_C03_TARGET_NODES = tests/test_cli_help.py::test_release_version_is_synchronized_across_user_documents; tests/test_release_governance.py::test_changelog_has_target_release_section
G1_C03_TARGETED_BUDGET = ONE INVOCATION; MAX 5 MINUTES / 5,000 FILES / 256 MiB; >=10 GiB D: FREE; FRESH REGISTERED PARENT, ABSENT PYTEST-OWNED CHILD t; RETAIN COMPLETE STDOUT/STDERR/METADATA AND NATIVE PROCESS EXIT; NO RETRY
G1_C03_FAILURE_MEMORY = SHARED DOCUMENT CONTRACT PARTIAL-EDIT FINDING; FM-055; PRESERVE BOTH INDEPENDENT HEADING REQUIREMENTS AND RUN BOTH EXACT NODES TOGETHER
G1_C03_RELEASE_IMPACT = SOURCE METADATA REMAINS 0.10.1 INTERNAL/UNRELEASED; NO VERSION INCREMENT, OFFICIAL RELEASE, BUILD, TAG, INSTALLATION, RUNTIME, CAPABILITY OR MATURITY CHANGE
G1_C03_WHOLE_SUITE = FULL-RUN RED PRESERVED; TARGETED GREEN DOES NOT PROMOTE WHOLE WP; NO FURTHER FULL RUN OR RUFF AUTHORIZED
G1_C03_NEXT = BUILDER RESTORES THE MISSING UNRELEASED HEADING, RUNS ONE TWO-NODE TARGETED GREEN AND RETURNS EXACT EVIDENCE TO PLANNER
~~~

### G1-C03 Builder result — paired heading contracts passed

After governance commit cadbaab7ae945a06a2ef7b1ff22a3e13a6730652, Builder restored the exact ## Unreleased heading immediately above the unchanged ## 0.10.1 - Internal, unreleased section. This was committed as da3496838b4b320aca50a4f60e331397113c8916 with CHANGELOG.md as the only changed path.

One invocation then ran both exact heading consumers together. Native Start-Process exit was 0; both tests passed. Pytest reported one non-failing PytestCacheWarning (WinError 5 writing repository .pytest_cache), 3.81 seconds; wall time was 6.63 seconds. The fresh run root .tmp/w3/c03a61 contains five files totaling 915,725 bytes, including complete stdout/stderr, metadata, parent-writability proof and pytest-owned child t. D: free space after the run was 17,410,375,680 bytes. All task budgets passed; all evidence remains retained, with no cleanup.

The full sequential run remains consumed RED with one documentation failure. The paired targeted pass proves the two exact heading assertions only; it does not replace or promote the full run. No full-suite rerun, Ruff, source/test change, version increment, build, tag, release, installation, runtime, capability or maturity change occurred.

~~~text
G1_C03_GOVERNANCE_COMMIT = cadbaab7ae945a06a2ef7b1ff22a3e13a6730652; EXACT FIVE GOVERNANCE PATHS
G1_C03_TARGETED_HEAD = cadbaab7ae945a06a2ef7b1ff22a3e13a6730652; only uncommitted CHANGELOG heading correction; no source/test change
G1_C03_DOC_COMMIT = da3496838b4b320aca50a4f60e331397113c8916; exactly CHANGELOG.md; parent cadbaab7ae945a06a2ef7b1ff22a3e13a6730652
G1_C03_TARGETED_COMMAND = .venv\Scripts\python.exe -m pytest -n 0 -ra --basetemp=.tmp/w3/c03a61/t tests/test_cli_help.py::test_release_version_is_synchronized_across_user_documents tests/test_release_governance.py::test_changelog_has_target_release_section
G1_C03_TARGETED_RESULT = PROCESS OBJECT EXIT 0; 2 PASSED; 1 NON-FAILING PytestCacheWarning WinError 5; pytest 3.81s; wall 6.63s
G1_C03_TARGETED_PID = 15884; START 2026-09-29T08:58:40.2388217+07:00; END 2026-09-29T08:58:46.8710124+07:00
G1_C03_TARGETED_LOGS = .tmp/w3/c03a61/targeted.stdout.log; .tmp/w3/c03a61/targeted.stderr.log; .tmp/w3/c03a61/targeted-run-metadata.txt
G1_C03_TARGETED_SCRATCH = .tmp/w3/c03a61; 5 FILES / 915,725 BYTES; pytest child t created by pytest and retained; D: free after 17,410,375,680 bytes; no cleanup
G1_C03_TARGETED_SCOPE = BOTH EXACT HEADING CONTRACT NODES PASSED; CHANGELOG.md ONLY TEST EDIT INPUT; NO TEST/GUIDE/SOURCE/VERSION CONSTANT CHANGE
G1_C03_WHOLE_SUITE = FULL SEQUENTIAL RED PRESERVED; NO SECOND FULL RUN OR RUFF AUTHORIZED; PAIRED TARGETED PASS DOES NOT MEAN WHOLE-SUITE PASS
G1_C03_RELEASE_IMPACT = INTERNAL SOURCE VERSION REMAINS 0.10.1 UNRELEASED; NO VERSION INCREMENT, BUILD, TAG, OFFICIAL RELEASE, INSTALLATION, RUNTIME, CAPABILITY OR MATURITY CHANGE
G1_C03_NEXT = RETURN GOVERNANCE, CHANGELOG AND TARGETED EVIDENCE TO PLANNER; NO REMOTE/OPERATIONAL EFFECTS
~~~

### G1-C04 — final verification and scope disposition

Tester report WP-OPS-QI-SINGLE-INSTALLATION-AND-LEGACY-ROOT-RETIREMENT-01-TESTER-20260929-04 verified exact candidate HEAD ec0d4af193711957876764a0681c441ccbb8a87a from a clean tracked/index state. The one authorized full sequential run exited 0: 1,781 collected, 1,776 passed, 5 governed skips, zero failures, one PytestCacheWarning, 1,143.19 seconds pytest time and 1,148.401 seconds wall time. The retained .tmp/w3/9541a1 run had 15,796 files and 621,125,467 bytes after pytest plus Ruff; all declared run budgets passed. There was no retry or cleanup.

The authorized follow-on command .venv\Scripts\python.exe -m ruff check . returned native exit 1 with 8 findings exclusively beneath preserved unknown untracked $RECYCLE.BIN\...\School.py. Tester did not open or alter that file and did not narrow the command. No candidate path was reported. Local full Ruff is FAIL; candidate causation is NOT_ESTABLISHED. Planner classifies the persistent local workspace Ruff fitness as OVERBROAD because the command traverses preserved untracked content; a clean-checkout hosted Ruff check remains required later. This classification does not convert the failed invocation to PASS or authorize a replacement invocation.

Static gates passed: git diff --check; registry revision 1.0.23 with 65 unique PATH_IDs and 21 WP bindings and no unresolved references; CURRENT had 142 unique mandatory keys; changelog/guide markers were present; no deletion was recorded; tracked/index state was clean.

A scope hold remains. G1 commit 795c554246c13b838e4cb9a6d434159ab09efbfe modified tests/test_repo_hygiene.py, which is absent from the exact G1 write allowlist. Its tests directly check the authorized clean-dev behavior: exact Git root, rejection of operational/non-repository roots, and preservation of release_staging evidence and published candidates. Record this as both PLAN_ALLOWLIST_OMISSION and BUILDER_SCOPE_BREACH. The useful test delta is not retroactively authorized by recording it. No amend, rebase or history rewrite is permitted.

The Planner-recommended bounded Human A0 disposition is to authorize a forward governance correction retaining exactly the existing tests/test_repo_hygiene.py delta from 795c554 as the accepted G1 correction baseline while preserving the recorded deviation, and to authorize exactly one replacement Ruff verification over the immutable list of all tracked .py, .pyi and .ipynb paths (currently 255 paths, with path list/count/SHA and native exit captured). This is a recommendation only; it is not an authorization. No replacement Ruff, test rerun, fix, Reviewer handoff or remote transition is authorized by this sync.

Human authority for the exact ec0d4af full run, Ruff/static follow-on and terminal docs-only evidence rule is routed in Feedback entry FB-0061. Its verification allowance is consumed. Preserve unknown untracked content; no cleanup. The candidate remains HOLD pending Human A0 disposition after Planner review.

~~~text
G1_C04_TESTER_REPORT_ID = WP-OPS-QI-SINGLE-INSTALLATION-AND-LEGACY-ROOT-RETIREMENT-01-TESTER-20260929-04
G1_C04_TESTED_CANDIDATE_HEAD = ec0d4af193711957876764a0681c441ccbb8a87a; CLEAN TRACKED/INDEX STATE AT ENTRY AND END
G1_C04_PYTEST_COMMAND = .venv\Scripts\python.exe -m pytest -n 0 -ra --basetemp=.tmp/w3/9541a1/t
G1_C04_PYTEST_RESULT = NATIVE EXIT 0; 1,781 COLLECTED; 1,776 PASSED; 5 GOVERNED SKIPS; 0 FAILED; 1 PytestCacheWarning; 1,143.19s PYTEST / 1,148.401s WALL; ONE RUN / NO RETRY
G1_C04_SCRATCH = .tmp/w3/9541a1; 15,796 FILES / 621,125,467 BYTES AFTER PYTEST AND RUFF; ALL DECLARED BUDGETS PASS; RETAINED; NO CLEANUP
G1_C04_RUFF_COMMAND = .venv\Scripts\python.exe -m ruff check .
G1_C04_RUFF_RESULT = NATIVE EXIT 1; 8 FINDINGS EXCLUSIVELY UNDER PRESERVED UNKNOWN UNTRACKED $RECYCLE.BIN\...\School.py; TESTER DID NOT OPEN/ALTER FILE OR NARROW COMMAND
G1_C04_LOCAL_RUFF_GATE = FAIL; LOCAL DIRTY-WORKSPACE CI FITNESS = OVERBROAD; CLEAN-CHECKOUT HOSTED RUFF REMAINS REQUIRED LATER; FAILED INVOCATION IS NOT PASS
G1_C04_CANDIDATE_CAUSATION = NOT_ESTABLISHED; NO CANDIDATE PATH REPORTED BY RUFF
G1_C04_STATIC_GATES = PASS; git diff --check; registry rev 1.0.23 / 65 unique PATH_IDs / 21 bindings / no unresolved refs; CURRENT 142 unique mandatory keys; changelog/guide markers; no deletion; tracked/index clean
G1_C04_SCOPE_GATE = HOLD; PLAN_ALLOWLIST_OMISSION = YES; BUILDER_SCOPE_BREACH = YES
G1_C04_OUT_OF_ALLOWLIST_PATH = tests/test_repo_hygiene.py in commit 795c554246c13b838e4cb9a6d434159ab09efbfe; exact G1 write allowlist omitted this path
G1_C04_TEST_RATIONALE = EXISTING TEST DELTA DIRECTLY CHECKS AUTHORIZED clean_dev.ps1 BEHAVIOR: EXACT GIT ROOT; REJECT OPERATIONAL/NONREPO ROOTS; PRESERVE release_staging EVIDENCE/PUBLISHED CANDIDATE
G1_C04_NO_RETROACTIVE_AUTHORITY = RECORDING THE DEVIATION DOES NOT AUTHORIZE IT; NO AMEND/REBASE/HISTORY REWRITE
G1_C04_PLANNER_RECOMMENDATION = HUMAN A0 MAY AUTHORIZE A FORWARD GOVERNANCE CORRECTION RETAINING EXACT EXISTING tests/test_repo_hygiene.py DELTA AS G1 BASELINE WHILE PRESERVING THE DEVIATION; AND EXACTLY ONE REPLACEMENT RUFF OVER IMMUTABLE TRACKED .py/.pyi/.ipynb LIST (CURRENTLY 255; CAPTURE LIST/COUNT/SHA/NATIVE EXIT); RECOMMENDATION ONLY, NO ACTION AUTHORITY
G1_C04_REPLACEMENT_RUFF = NOT_AUTHORIZED; NO TEST RERUN; NO FIX/SCOPE EXPANSION
G1_C04_HUMAN_AUTHORITY = EXACT ec0d4af FULL SEQUENTIAL RUN, RUFF/STATIC FOLLOW-ON AND TERMINAL DOCS-ONLY EVIDENCE RULE; ROUTED AS FB-0061; RUN AUTHORITY CONSUMED
G1_C04_WHOLE_CANDIDATE = HOLD; REVIEWER_HANDOFF_READY=NO; REMOTE_READY=NO
G1_C04_NEXT = PLANNER REVIEWS THE EVIDENCE AND PRESENTS THE BOUNDED SCOPE/RUFF DISPOSITION RECOMMENDATION TO HUMAN A0
~~~


### G1-C05 — Human forward disposition and tracked-manifest Ruff authority

Human A0 explicitly approved G1-C05 in the Planner task after reviewing the concrete G1-C04 scope/Ruff disposition. No separate decision ID was supplied. This is a forward disposition: from this decision onward, retain exactly the existing tests/test_repo_hygiene.py delta from commit 795c554246c13b838e4cb9a6d434159ab09efbfe as the accepted G1 correction baseline. Preserve both historical PLAN_ALLOWLIST_OMISSION and BUILDER_SCOPE_BREACH; the original allowlist is not rewritten and the earlier edit is not described as authorized when made. The retained delta directly tests authorized G1.2 scripts/clean_dev.ps1 behavior: exact Git top-level, rejection of D:\QI-Crawler/nonrepo/nested roots, and preservation of release_staging evidence and published candidates.

The exact retained test-file diff is identified by SHA-256 e7f68da20c6afa6e619150f519384734bc81509b93294c8794745faa263ac027 over 4,428 bytes from this deterministic command: `git -c core.quotePath=true diff --no-ext-diff --no-color --binary 795c554246c13b838e4cb9a6d434159ab09efbfe^ 795c554246c13b838e4cb9a6d434159ab09efbfe -- tests/test_repo_hygiene.py`. The commit changed seven paths; this identity covers only the retained tests/test_repo_hygiene.py delta (59 added lines), not the complete commit.

Human A0 authorizes the canonical Tester to run exactly one replacement Ruff verification over an immutable manifest produced by `git ls-files -- '*.py' '*.pyi' '*.ipynb'` at Tester preflight (expected 255 paths). Tester must retain the exact manifest bytes, path count, manifest SHA-256, exact Git/code identity and proof that no tracked Python path differs from tested candidate ec0d4af193711957876764a0681c441ccbb8a87a, plus native exit, stdout and stderr. Run Ruff only against those listed tracked paths; do not inspect or modify unknown files, alter Ruff configuration or pyproject.toml, retry, or rerun pytest. Budget: 10 minutes; scratch at most 20,000 files / 1 GiB; retain at least 10 GiB free on D:; no cleanup.

If the replacement Ruff and prescribed static identity/scope checks pass, Tester returns evidence to Planner for Reviewer handoff. Tester does not declare the whole WP PASS or contact Human. The prior repository-wide Ruff failure remains a failed historical command; its eight findings were under unknown untracked content and candidate causation is not established. The original pytest PASS at ec0d4af remains valid. No push, PR, merge, release, build, live operation or cleanup is authorized.

Feedback entry FB-0062 routes this Human decision. The earlier allowlist omission and scope breach remain historical facts; this forward acceptance does not rewrite history.

~~~text
G1_C05_HUMAN_AUTHORITY = HUMAN A0 APPROVED G1-C05 IN PLANNER TASK AFTER REVIEWING G1-C04 DISPOSITION; NO SEPARATE DECISION ID SUPPLIED; ROUTED AS FB-0062
G1_C05_RETAINED_TEST_COMMIT = 795c554246c13b838e4cb9a6d434159ab09efbfe; PATH tests/test_repo_hygiene.py; 59 INSERTIONS
G1_C05_TEST_DELTA_IDENTITY_COMMAND = git -c core.quotePath=true diff --no-ext-diff --no-color --binary 795c554246c13b838e4cb9a6d434159ab09efbfe^ 795c554246c13b838e4cb9a6d434159ab09efbfe -- tests/test_repo_hygiene.py
G1_C05_TEST_DELTA_IDENTITY = SHA256 e7f68da20c6afa6e619150f519384734bc81509b93294c8794745faa263ac027; 4,428 DIFF BYTES
G1_C05_RETENTION_REASON = DIRECT CLEAN-DEV REGRESSION COVERAGE: EXACT GIT TOP-LEVEL; REJECT D:\QI-CRAWLER/NONREPO/NESTED ROOTS; PRESERVE release_staging EVIDENCE/PUBLISHED CANDIDATE
G1_C05_HISTORICAL_DEVIATION = PLAN_ALLOWLIST_OMISSION=YES; BUILDER_SCOPE_BREACH=YES; ORIGINAL ALLOWLIST UNCHANGED; OLD EDIT NOT CLAIMED AUTHORIZED WHEN MADE
G1_C05_FORWARD_BASELINE = HUMAN A0 ACCEPTS EXACT EXISTING tests/test_repo_hygiene.py DELTA AS G1 CORRECTION BASELINE FROM THIS DECISION FORWARD
G1_C05_TESTER_AUTHORITY = EXACTLY ONE REPLACEMENT RUFF OVER IMMUTABLE GIT-TRACKED PYTHON MANIFEST; NO PYTEST RERUN; NO UNKNOWN-FILE INSPECTION/MUTATION; NO RUFF CONFIG CHANGE; NO RETRY
G1_C05_MANIFEST_COMMAND = git ls-files -- '*.py' '*.pyi' '*.ipynb'; EXPECTED 255 PATHS; RETAIN EXACT MANIFEST BYTES/COUNT/SHA256
G1_C05_CODE_IDENTITY_GATE = RECORD EXACT TESTER HEAD AND PROVE NO TRACKED PYTHON PATH DIFF FROM TESTED CANDIDATE ec0d4af193711957876764a0681c441ccbb8a87a
G1_C05_TESTER_EVIDENCE = NATIVE RUFF EXIT; STDOUT/STDERR; EXACT GIT/ CODE IDENTITY; MANIFEST COUNT/SHA; STATIC IDENTITY/SCOPE CHECKS
G1_C05_RUFF_BUDGET = 10 MINUTES; <=20,000 SCRATCH FILES; <=1 GiB; >=10 GiB D: FREE; NO RETRY/CLEANUP
G1_C05_HANDOFF = IF RUFF AND STATIC IDENTITY/SCOPE PASS, RETURN TO PLANNER FOR REVIEWER HANDOFF; TESTER DOES NOT DECLARE WHOLE WP PASS OR CONTACT HUMAN
G1_C05_AUTHORIZATION_TIME_STATE = AT C05 AUTHORIZATION: HOLD PENDING THE REPLACEMENT RUFF AND REVIEW; PRIOR FULL PYTEST PASS AND ORIGINAL FULL RUFF FAILURE PRESERVED; THE LATER TESTER RESULT BELOW RECORDS RUFF COMPLETION, WITH REVIEW STILL PENDING
G1_C05_NEXT = PLANNER REVIEWS THIS FORWARD DISPOSITION AND DISPATCHES CANONICAL TESTER; NO OTHER ACTION
~~~


### G1-C05 — Tester tracked-manifest Ruff result and terminal handoff

Canonical Tester report `WP-OPS-QI-SINGLE-INSTALLATION-AND-LEGACY-ROOT-RETIREMENT-01-TESTER-20260929-G1-C05-01` returns `PASS_FOR_PLANNER_REVIEWER_HANDOFF` for the G1-C05 tracked-manifest Ruff/static gate only. Ruff tested governance HEAD `bd423085611bd70b3f23629d20bcdb0f25fb4365`. The original full sequential pytest PASS at `ec0d4af193711957876764a0681c441ccbb8a87a` remains the exact pytest evidence; no pytest rerun occurred. `AUDIT_TARGET_CODE_HEAD` remains `795c554246c13b838e4cb9a6d434159ab09efbfe`. No tracked Python path changed between `ec0d4af193711957876764a0681c441ccbb8a87a` and `bd423085611bd70b3f23629d20bcdb0f25fb4365`. The retained test delta still matches commit `795c554246c13b838e4cb9a6d434159ab09efbfe`, path `tests/test_repo_hygiene.py`, 4,428-byte diff SHA-256 `e7f68da20c6afa6e619150f519384734bc81509b93294c8794745faa263ac027`.

The captured `git ls-files -- '*.py' '*.pyi' '*.ipynb'` manifest is `.tmp/w3/c780f5/tracked-python-manifest.bin`, 9,412 bytes, 255 paths, no duplicates/missing paths, SHA-256 `83b1283f2c425a6a402b3228d006ad911f5bb7db14f49ab160daac81eb2b97ca`. One Ruff invocation passed all 255 discrete manifest paths: PID 16948, native exit 0, 0.284 seconds; stdout `All checks passed!` (19 bytes, SHA-256 `82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18`); stderr empty (SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`). Scratch was 7 files / 35,454 bytes; D: reserve passed; no retry, cleanup, pytest, edit or remote action.

Prescribed statics passed: manifest rehash; no tracked-Python delta from the tested candidate; diff check; forward C05 scope disposition with zero unexplained paths; no deletions; registry revision 1.0.23 with 65 PATH_IDs / 21 bindings / no unresolved refs; CURRENT had 164 unique mandatory keys; changelog/guide markers; tracked/index clean. The historical broad `ruff check .` failure remains recorded and candidate causation is not established; a clean-checkout hosted Ruff check remains required later.

Planner reconciliation is `MACHINE_VERIFICATION_STATE=PASS_FOR_REVIEWER_HANDOFF`, `G1_C05_SCOPE_DISPOSITION=PASS_FORWARD` with historical omission/breach preserved, and `LOCAL_CANDIDATE_GATES=PASS_WITH_RECORDED_LIMITATIONS`. The whole WP is not complete: independent Reviewer audit and Planner post-review reconciliation remain required. Remote readiness remains NO until those gates reconcile. No push, PR, merge, release, build, live operation or cleanup is authorized by this sync.

~~~text
G1_C05_TESTER_REPORT_ID = WP-OPS-QI-SINGLE-INSTALLATION-AND-LEGACY-ROOT-RETIREMENT-01-TESTER-20260929-G1-C05-01
G1_C05_TESTER_VERDICT = PASS_FOR_PLANNER_REVIEWER_HANDOFF; TRACKED-MANIFEST RUFF/STATIC GATE ONLY
G1_C05_RUFF_GOVERNANCE_HEAD = bd423085611bd70b3f23629d20bcdb0f25fb4365
G1_C05_TESTED_CANDIDATE_HEAD = ec0d4af193711957876764a0681c441ccbb8a87a; ORIGINAL FULL PYTEST PASS REMAINS VALID; NO PYTEST RERUN
G1_C05_AUDIT_TARGET_CODE_HEAD = 795c554246c13b838e4cb9a6d434159ab09efbfe
G1_C05_TRACKED_PYTHON_DELTA = NONE FROM ec0d4af193711957876764a0681c441ccbb8a87a TO bd423085611bd70b3f23629d20bcdb0f25fb4365
G1_C05_RETAINED_TEST_DELTA = 795c554246c13b838e4cb9a6d434159ab09efbfe; tests/test_repo_hygiene.py; 4,428 DIFF BYTES; SHA256 e7f68da20c6afa6e619150f519384734bc81509b93294c8794745faa263ac027; 59 INSERTIONS
G1_C05_MANIFEST = .tmp/w3/c780f5/tracked-python-manifest.bin; 9,412 BYTES; 255 TRACKED PATHS; 0 DUPLICATES; 0 MISSING; SHA256 83b1283f2c425a6a402b3228d006ad911f5bb7db14f49ab160daac81eb2b97ca
G1_C05_RUFF_RESULT = ONE INVOCATION; 255 DISCRETE MANIFEST PATHS; PID 16948; NATIVE EXIT 0; 0.284s; STDOUT 19 BYTES `All checks passed!` SHA256 82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18; STDERR EMPTY SHA256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
G1_C05_SCRATCH = .tmp/w3/c780f5; 7 FILES / 35,454 BYTES; D: RESERVE PASS; NO RETRY/CLEANUP/PYTEST/EDIT/REMOTE ACTION
G1_C05_STATIC_GATES = PASS; MANIFEST REHASH; PYTHON IDENTITY; DIFF CHECK; ZERO UNEXPLAINED SCOPE PATHS; NO DELETIONS; REGISTRY 1.0.23/65 PATH_ID/21 BINDING/NO UNRESOLVED; CURRENT 164 UNIQUE KEYS; MARKERS; TRACKED/INDEX CLEAN
G1_C05_BROAD_RUFF_HISTORY = ORIGINAL `ruff check .` NATIVE EXIT 1 PRESERVED; CANDIDATE CAUSATION NOT_ESTABLISHED; CLEAN-CHECKOUT HOSTED RUFF REQUIRED LATER
G1_C05_PLANNER_RECONCILIATION = MACHINE_VERIFICATION_STATE=PASS_FOR_REVIEWER_HANDOFF; SCOPE_DISPOSITION=PASS_FORWARD; LOCAL_CANDIDATE_GATES=PASS_WITH_RECORDED_LIMITATIONS
G1_C05_WHOLE_WP = NOT COMPLETE; INDEPENDENT REVIEWER AUDIT AND PLANNER POST-REVIEW RECONCILIATION REQUIRED; REMOTE_READY=NO
G1_C05_NEXT = PLANNER AUDITS EXACT TERMINAL SYNC/SCOPE THEN DISPATCHES INDEPENDENT REVIEWER; NO REMOTE ACTION
~~~


### G1 post-review reconciliation — governed integration pending

Reviewer report `WP-OPS-QI-SINGLE-INSTALLATION-G1-REVIEWER-20260929-01` returns `AUDIT_VERDICT=PASS`, `CANDIDATE_CONTRACT_VERDICT=PASS`, `LOCAL_INTEGRATION_READINESS=PASS_WITH_RECORDED_LIMITATIONS`, `CI_FITNESS_CLASSIFICATION=FIT_WITH_ADDITION`, `LOCAL_REVIEW_FITNESS=FIT`, `CLEAN_CHECKOUT_HOSTED_CI=REQUIRED_AND_PENDING`, and `FINDINGS=NONE`. The exact audited identities remain distinct: code/test head `795c554246c13b838e4cb9a6d434159ab09efbfe`; full-pytest candidate `ec0d4af193711957876764a0681c441ccbb8a87a`; tracked-manifest Ruff governance head `bd423085611bd70b3f23629d20bcdb0f25fb4365`; audited documentation head `0491e5c31c06514b1ed47635a83793c2e4bac2ea`. Planner accepts the Reviewer PASS for that exact object.

Local evidence remains bounded: the exact full sequential pytest run at `ec0d4af` collected 1,781, passed 1,776, skipped 5 governed tests, and had zero failures. Tracked-manifest Ruff passed once over 255 tracked Python paths at `bd423085`. The earlier broad local Ruff command remains failed under preserved unknown `$RECYCLE.BIN` content; candidate causation is not established. A clean-checkout hosted CI run is still required. This does not establish live/runtime/release readiness, authorize a build, or promote roadmap maturity or `PROJECT_MEMORY` before merge. The historical plan-allowlist omission and Builder scope deviation remain recorded; the exact test delta is retained only under the later Human-approved forward disposition.

This transition authorizes the previously approved remote integration sequence only after fresh remote identity and open-PR checks. In this Builder session, both `git ls-remote` and `gh pr list` failed because network access was unavailable. The local cached `origin/main` remains `caf983691da60d4eaf990d09e9e1788692aabaac`, which is not a fresh live ref. Current live main, feature-ref and PR state are therefore unverified; no push or PR mutation occurred. Stage B must wait for Planner-provided fresh remote evidence and explicit release to proceed. If compatible, only a normal fast-forward push and one PR into `main` are authorized; hosted checks must then bind to the exact PR head. Human retains manual merge authority. No merge, release, build, live update, cleanup or other operational action is authorized.

~~~text
G1_REVIEWER_REPORT_ID = WP-OPS-QI-SINGLE-INSTALLATION-G1-REVIEWER-20260929-01
G1_REVIEWER_VERDICT = PASS; CANDIDATE_CONTRACT=PASS; LOCAL_INTEGRATION_READINESS=PASS_WITH_RECORDED_LIMITATIONS; CI_FITNESS=FIT_WITH_ADDITION; LOCAL_REVIEW_FITNESS=FIT; FINDINGS=NONE
G1_REVIEWED_HEADS = CODE/TEST 795c554246c13b838e4cb9a6d434159ab09efbfe; PYTEST ec0d4af193711957876764a0681c441ccbb8a87a; TRACKED RUFF bd423085611bd70b3f23629d20bcdb0f25fb4365; DOCS 0491e5c31c06514b1ed47635a83793c2e4bac2ea
G1_LOCAL_PYTEST = 1,781 COLLECTED; 1,776 PASSED; 5 GOVERNED SKIPS; 0 FAILED; EXACT CANDIDATE ec0d4af; NO RERUN
G1_TRACKED_RUFF = PASS ON 255 TRACKED PYTHON PATHS AT bd423085; HISTORICAL BROAD `ruff check .` FAILURE UNDER PRESERVED UNKNOWN `$RECYCLE.BIN` CONTENT RETAINED; CANDIDATE CAUSATION NOT_ESTABLISHED
G1_HOSTED_CI = REQUIRED_AND_PENDING; CLEAN-CHECKOUT CHECKS HAVE NOT BEEN OBSERVED FOR THIS CANDIDATE
G1_PLANNER_POST_REVIEW = ACCEPTED INDEPENDENT REVIEWER PASS FOR THE EXACT OBJECT; NO ROADMAP MATURITY OR PROJECT_MEMORY PROMOTION BEFORE MERGE
G1_REMOTE_PREFLIGHT = `git ls-remote` AND `gh pr list` FAILED DUE NETWORK ACCESS; LIVE main/feature REF AND OPEN-PR STATE UNVERIFIED; LOCAL CACHED origin/main=caf983691da60d4eaf990d09e9e1788692aabaac IS NOT FRESH LIVE EVIDENCE
G1_REMOTE_EFFECTS = NONE; NO PUSH OR PR MUTATION
G1_NEXT = PLANNER PROVIDES FRESH REMOTE FEATURE/MAIN/OPEN-PR EVIDENCE AND RELEASES STAGE B ONLY IF COMPATIBLE; THEN FAST-FORWARD PUSH AND ONE PR MAY PROCEED
G1_MERGE_RELEASE = HUMAN MANUAL MERGE ONLY; NO MERGE/RELEASE/BUILD/LIVE OPERATION/CLEANUP AUTHORITY
~~~


## G1-C06 — PR #137 hosted Linux CI correction attempt 1

Hosted run `36520514587` tested source `ab1b5667438066d2104ed7505c626e3035e8c32f` with merge preview `d75673ec4d441ebe8bfb825ade1aa4f3085fb7f0`. Ubuntu 3.12 and Ubuntu 3.11 each failed with 86 failed / 1,593 passed / 102 skipped; Windows 3.12 and Code Quality passed. The retained log is `.tmp/w3/ci137a1/failed.log`, 2,782,097 bytes, SHA-256 `DA7D49545C14D9A3248DBFCE58324BDEF6F14DB54A827D7086B9389F26B70280`. No CI retry occurred.

The bounded diagnosis identified three portability seams without finding a production Python defect: G1 synthetic tests called public APIs that correctly require Windows protection; two projected-path fixtures used POSIX `Path` for Windows drive-root semantics; and PowerShell publisher path composition used Windows-only separators. The correction kept the public non-Windows guard fail-closed, confined the synthetic platform stand-in to tests, used host-independent projected paths, and made publisher containment/path composition platform-neutral while retaining the path/reparse/archive gates.

The first local targeted invocation in `.tmp/w3/c06d9f` exited 4 before collection because `Start-Process -ArgumentList` flattened the basetemp argument containing the repository's spaces (`Technology\QI`). Planner classified this as `COMMAND_HARNESS_DEFECT`, not a test or hosted-CI retry. The one authorized corrected invocation used PowerShell's call operator and a fresh precreated run parent with absent pytest-owned child `t`: `.venv\Scripts\python.exe -m pytest -ra --basetemp .tmp/w3/c06e18/t tests/test_operational_update.py tests/test_windows_installer.py`. Native exit was 0: 170 passed, 3 skipped, 0 failed, one non-failing cache warning; pytest 212.47s / wall 215.26s. The skips were two symlink-creation limitations and one unsupported-non-Windows-only assertion. Scratch was 2,749 files / 13,039,696 bytes; D: free bytes were 15,896,924,160 before and 15,873,998,848 after. No retry or cleanup occurred.

Scoped Ruff on the two changed Python test files passed. Final collection-only passed with 1,782 tests and zero errors (baseline 1,781); `git diff --check` passed. Implementation commits are `2e55285b898f604a1e1a993040b282b8fc62cc3c` (`test(update): make synthetic Windows checks portable`) and `36073ac0d7cd4999869d45541fe26627bbc2df8e` (`fix(release): use native path separators for publishing`). They are local and unpushed. The correction head has not received hosted CI or independent Tester/Reviewer audit; attempt 1 remains RED history. No source Python, workflow, dependency, operational, release, or remote change was made.

~~~text
G1_C06_HOSTED_RED = RUN 36520514587; SOURCE ab1b5667438066d2104ed7505c626e3035e8c32f; MERGE PREVIEW d75673ec4d441ebe8bfb825ade1aa4f3085fb7f0; BOTH UBUNTU JOBS 86 FAILED / 1,593 PASSED / 102 SKIPPED; WINDOWS 3.12 AND CODE QUALITY PASS; NO RETRY
G1_C06_LOG = .tmp/w3/ci137a1/failed.log; 2,782,097 BYTES; SHA256 DA7D49545C14D9A3248DBFCE58324BDEF6F14DB54A827D7086B9389F26B70280
G1_C06_ROOT_CAUSES = TEST-LOCAL PLATFORM SEAM FOR SYNTHETIC WINDOWS APIS; POSIX PATH IN TWO WINDOWS-LENGTH TESTS; WINDOWS-ONLY SEPARATORS IN PUBLISHER; PRODUCTION WINDOWS GUARD PRESERVED
G1_C06_HARNESS_FAILURE = .tmp/w3/c06d9f; Start-Process ARGUMENT FLATTENING SPLIT SPACE-CONTAINING BASETEMP; EXIT 4 BEFORE COLLECTION; PLANNER CLASSIFICATION COMMAND_HARNESS_DEFECT; RETAINED; NO RETRY CLAIMED AS TEST EVIDENCE
G1_C06_TARGETED = .venv\Scripts\python.exe -m pytest -ra --basetemp .tmp/w3/c06e18/t tests/test_operational_update.py tests/test_windows_installer.py; NATIVE EXIT 0; 170 PASSED / 3 SKIPPED / 0 FAILED / 1 NON-FAILING PytestCacheWarning; 212.47s PYTEST / 215.26s WALL
G1_C06_TARGETED_SCRATCH = .tmp/w3/c06e18; 2,749 FILES / 13,039,696 BYTES; D: FREE 15,896,924,160 BEFORE / 15,873,998,848 AFTER; RETAINED; NO RETRY/CLEANUP
G1_C06_RUFF = SCOPED TO tests/test_operational_update.py AND tests/test_windows_installer.py; PASS
G1_C06_COLLECTION = BASELINE 1,781; FINAL 1,782; ZERO COLLECTION ERRORS; FINAL RUN .tmp/w3/c06f32
G1_C06_DIFF = git diff --check PASS; EXACT IMPLEMENTATION SCOPE THREE AUTHORIZED PATHS; NO DELETIONS
G1_C06_COMMITS = 2e55285b898f604a1e1a993040b282b8fc62cc3c; 36073ac0d7cd4999869d45541fe26627bbc2df8e; LOCAL ONLY / UNPUSHED
G1_C06_PLUGIN_CODEGRAPH = PLUGIN CodeGraph; PURPOSE=STRUCTURAL CALLER/PUBLISHER IMPACT; INVOCATION=`codegraph explore "apply_operational_application_update recover_operational_application_update publish_windows_release"`; RESULT=USED_WITH_FALLBACK, 35 SYMBOLS/1 SOURCE FILE AND UPDATE TEST RELATION; FALLBACK=BOUNDED HOSTED LOG + POWERSHELL SOURCE READ; IMPACT_RADIUS=UPDATE ENTRYPOINTS/PUBLISHER; EDIT_RADIUS=2 TEST FILES + PUBLISH SCRIPT; TEST_RADIUS=2 AFFECTED TEST FILES; LIMITATION=GRAPH DID NOT SUPPLY HOSTED FAILURE TRACE
G1_C06_PLUGIN_SYSTEMATIC_DEBUGGING = PLUGIN systematic-debugging; PURPOSE=CLASSIFY IDENTICAL UBUNTU FAILURES; INVOCATION=READ RETAINED RUN LOG AND COMPARE CALL GUARDS, PATH FIXTURES AND PUBLISHER PATH USE BEFORE EDIT; RESULT=USED_AND_SUCCEEDED; FALLBACK=BOUNDED SOURCE/TEST READ; IMPACT_RADIUS=THREE HOSTED FAILURE FAMILIES; EDIT_RADIUS=2 TEST FILES + PUBLISH SCRIPT; TEST_RADIUS=2 AFFECTED FILES; LIMITATION=NO PRODUCTION PYTHON DEFECT ESTABLISHED
G1_C06_PLUGIN_TDD = PLUGIN test-driven-development; PURPOSE=FIX HOSTED RED SEAMS; INVOCATION=RETAINED HOSTED RED, THEN ONE CORRECTED AFFECTED MATRIX; RESULT=USED_AND_SUCCEEDED; FALLBACK=NONE; IMPACT_RADIUS=THREE IDENTIFIED SEAMS; EDIT_RADIUS=3 AUTHORIZED IMPLEMENTATION/TEST PATHS; TEST_RADIUS=2 AFFECTED FILES; LIMITATION=LOCAL WINDOWS GREEN DOES NOT REPLACE HOSTED LINUX VERIFICATION
G1_C06_PLUGIN_VERIFICATION = PLUGIN verification-before-completion; PURPOSE=BUILDER HANDOFF; INVOCATION=CHECK NATIVE EXIT/COLLECTION/RUFF/DIFF/SCOPE/TREE; RESULT=USED_AND_SUCCEEDED; FALLBACK=NONE; IMPACT_RADIUS=G1-C06 CLAIMS; EDIT_RADIUS=AUTHORIZED DOCS ONLY FOR SYNC; TEST_RADIUS=NO ADDITIONAL RUN; LIMITATION=HOSTED CORRECTION HEAD STILL UNVERIFIED
G1_C06_PLUGIN_CODEBASE_MEMORY = PLUGIN codebase-memory; PURPOSE=STRUCTURAL INDEX READINESS; INVOCATION=NONE, NO INDEX AUTHORIZED; RESULT=TOOL_UNAVAILABLE/NOT_INDEXED PER CURRENT ZERO-PROJECT STATE; FALLBACK=CodeGraph + bounded direct reads; IMPACT_RADIUS=NONE; EDIT_RADIUS=NONE; TEST_RADIUS=NONE; LIMITATION=NO OPERATIONAL READINESS CLAIM
G1_C06_CANDIDATE = LOCAL BOUNDED CHECKS PASS; HOSTED CI ON CORRECTION HEAD NOT RUN; TESTER/REVIEWER AND PLANNER REVIEW PENDING
G1_C06_NEXT = PLANNER REVIEWS THE EXACT CANDIDATE AND ASSIGNS CANONICAL TESTER; NO PUSH/PR/CI RERUN UNTIL GOVERNED HANDOFF
~~~


## G1-C06 — Tester/Reviewer reconciliation and hosted checkpoint

Tester report `WP-OPS-QI-SINGLE-INSTALLATION-AND-LEGACY-ROOT-RETIREMENT-01-G1-C06-TESTER-20260929-01` passes the local bounded verification at candidate head `366f2ce4a6b0e1de54346228208af928903d438d`. Its fresh root `.tmp/w3/d3a1c6` ran the two affected test files with native exit 0: 170 passed, 3 skipped, 0 failed, one non-failing pytest cache warning; pytest 158.02s / wall 159.752s. Skips were two symlink-creation limitations and one test that only asserts unsupported non-Windows behavior. Scoped Ruff on the two changed test files exited 0 in 1.089s. The retained root contains 1,999 files / 12,257,808 bytes; D: free space was 16,046,854,144 bytes before and 16,027,299,840 after. No retry or cleanup occurred.

Reviewer report `WP-OPS-QI-SINGLE-INSTALLATION-AND-LEGACY-ROOT-RETIREMENT-01-G1-C06-REVIEWER-20260929-01` is `PASS` with no findings for code/test/script head `36073ac0d7cd4999869d45541fe26627bbc2df8e` and docs head `366f2ce4a6b0e1de54346228208af928903d438d`. Planner accepted both exact local dispositions and `FORWARD_HOSTED_CORRECTION_ELIGIBILITY=PASS`. The hosted Linux RED at `ab1b566` remains preserved and is not overwritten by local evidence. The prior corrected affected matrix and command-harness exit 4 remain recorded; no full suite or second correction attempt occurred.

Before the terminal governance sync, live refs were re-read: `main=caf983691da60d4eaf990d09e9e1788692aabaac`; feature branch `ab1b5667438066d2104ed7505c626e3035e8c32f`; PR #137 is the sole PR, OPEN, non-draft, unmerged, base `main` at `caf9836`. After the local governance commit, the authorized action is a normal fast-forward push of the exact terminal head to that same branch and PR; no new PR is authorized. Required hosted jobs must report against the exact resulting source head. Hosted CI remains PENDING until that evidence is observed. No merge or release follows automatically from green checks: Human retains merge authority. The whole Parent remains HOLD; release, build, live operation, DB/config mutation, and cleanup remain unauthorized.

~~~text
G1_C06_TESTER_REPORT_ID = WP-OPS-QI-SINGLE-INSTALLATION-AND-LEGACY-ROOT-RETIREMENT-01-G1-C06-TESTER-20260929-01
G1_C06_TESTER_VERDICT = PASS_LOCAL_BOUNDED_VERIFICATION; CANDIDATE 366f2ce4a6b0e1de54346228208af928903d438d
G1_C06_TESTER_PYTEST = .tmp/w3/d3a1c6; NATIVE EXIT 0; 170 PASSED / 3 SKIPPED / 0 FAILED / 1 NON-FAILING PytestCacheWarning; 158.02s PYTEST / 159.752s WALL; PID 15656
G1_C06_TESTER_SKIP_REASONS = TWO SYMLINK-CREATION LIMITATIONS; ONE TEST THAT ONLY ASSERTS UNSUPPORTED NON-WINDOWS BEHAVIOR
G1_C06_TESTER_RUFF = SCOPED TWO-FILE RUN; EXIT 0; 1.089s; 19-BYTE SUCCESS STDOUT; STDERR EMPTY
G1_C06_TESTER_SCRATCH = 1,999 FILES / 12,257,808 BYTES; D: FREE 16,046,854,144 BEFORE / 16,027,299,840 AFTER; RETAINED; NO RETRY/CLEANUP
G1_C06_REVIEWER_REPORT_ID = WP-OPS-QI-SINGLE-INSTALLATION-AND-LEGACY-ROOT-RETIREMENT-01-G1-C06-REVIEWER-20260929-01
G1_C06_REVIEWER_VERDICT = PASS; FINDINGS=NONE; CODE/TEST/SCRIPT 36073ac0d7cd4999869d45541fe26627bbc2df8e; DOCS 366f2ce4a6b0e1de54346228208af928903d438d
G1_C06_PLANNER_RECONCILIATION = ACCEPTED BOTH LOCAL REPORTS; FORWARD_HOSTED_CORRECTION_ELIGIBILITY=PASS; WHOLE_PARENT=HOLD; HOSTED_CI=PENDING
G1_C06_PRE_PUSH_REMOTE = LIVE main caf983691da60d4eaf990d09e9e1788692aabaac; FEATURE ab1b5667438066d2104ed7505c626e3035e8c32f; PR #137 OPEN/NON-DRAFT/UNMERGED; BASE main; ONE PR ONLY
G1_C06_NEXT = FAST-FORWARD PUSH TERMINAL HEAD TO EXISTING PR #137; VERIFY EXACT PR HEAD; OBSERVE REQUIRED EXACT-HEAD CHECKS; RETURN TO PLANNER
G1_C06_LIMITS = PRIOR HOSTED RED PRESERVED; LOCAL PASS DOES NOT REPLACE HOSTED CI; NO MERGE/RELEASE/BUILD/LIVE/DB/CONFIG/CLEANUP AUTHORITY
G1_C06_SPINE = IMPACT MULTIPLE; TARGET Work Order / MASTER_ROADMAP_DELTA / CURRENT; SYNC PASS
~~~
