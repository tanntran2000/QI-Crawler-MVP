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

Extend LAW 16 concisely with the single operational root/entry point and finite technical-root lifecycle; update operational/candidate acceptance contracts; make publisher outputs incapable of creating the sibling Crawler tool installation; make clean-dev preserve durable evidence; add only synthetic archive/locator contracts, no real legacy archive; prepare consistent internal 0.10.1 source metadata and changelog without build/release. Synchronize Delta/Feedback/CURRENT at governed transitions. Audit every task-created artifact for retained bytes; cleanup is not part of this WP.

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
FALLBACK = Zero projects returned; no indexing; CodeGraph and bounded source/docs remain the permitted exploration path
IMPACT_RADIUS = Structural-discovery readiness only
EDIT_RADIUS = NONE
TEST_RADIUS = NONE
LIMITATION = MCP succeeded but no project was indexed; the prior skill-path access denial is context-specific and was not retried
```

## Artifact and path budget

PATH_REGISTRY_BASELINE = revision 1.0.21; SHA256 object 100a2e6fac99667614d67aae7c1f57c579a36e82
PATH_REGISTRY_IMPACT = ADD_ENTRY
PATH_REGISTRY_RESULT = revision 1.0.22 candidate; one ROOT.OPERATIONAL and root-local RESERVED families; old external UPDATE_VOLUME identifiers retained unchanged
ROADMAP_REF = Master Roadmap Cross-cutting Windows / Team Bid delivery; Engineering Toolbox / Plugins
WP_ID_AND_AUTHORITY = this Human-approved Work Order
PATH_IDS_USED = PATH.GOV.PLAN; PATH.GOV.HANDOFF; PATH.GOV.DOCUMENT; PATH.GOV.DOCS; PATH.REPO.SOURCE; PATH.REPO.TESTS; PATH.REPO.SCRIPTS; PATH.DEV.TEST_TEMP; PATH.EVIDENCE.WP_RUN; root-local operational single-installation families
UNREGISTERED_WRITE_PATHS = NONE
MAX_LOCAL_TEST_SCRATCH = 20,000 files / 1 GiB / one full run / 10 GiB untouched D: reserve
MAX_SYNTHETIC_RUNTIME_TEST = 10,000 files / 512 MiB / one fresh run / 10 GiB untouched D: reserve
LIVE_OPERATIONAL_MUTATION = ZERO

New root-local paths must be containment/reparse checked, collision-rejected, same-volume and path-length checked before writes. Reject projected Windows paths over 240 characters; require at least 20 characters headroom below the 260-character legacy limit for each accepted staged/old/failed file path. If any file in a candidate generation cannot meet the limit, fail closed before mutation.

## Stop conditions

Stop and return to Planner on identity/lineage drift, tracked/index dirt, branch collision, external root requirement, second updater engine, unknown path/resource authority, unresolved old-binary race, Windows file-handle behavior not provable, ambiguous journal recovery, Data/sidecar/config change, acceptance provenance mismatch, path/storage budget failure, unexplained test collection decrease, out-of-allowlist need, required gate red without authorized resolution, or any live/shortcut/migration/restore/build/release/delete operation.

## Required Builder return

Report exact base/head/branch and carried history; semantic commits; changed files; G1.0 maps and stage outcomes; pytest collection baseline/final; RED/GREEN/affected/full/Ruff/diff evidence; path and artifact inventories/budgets; plugin invocation receipts; remote checkpoint/no-PR status; root and untracked preservation; achieved/not-achieved claims; open blockers; SPINE_IMPACT, SPINE_TARGET_FILES, SPINE_SYNC_STATE; exactly one next action; NEXT_AUTHORITY=PLANNER_ARCHITECT. Stop after Builder return. Planner assigns Tester and Reviewer; no direct role messaging.
