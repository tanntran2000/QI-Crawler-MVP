# WP-OPS-QI-INSTALLED-STARTUP-RECOVERY-01 rev2

## Mission, authority, and status

```text
WP_ID = WP-OPS-QI-INSTALLED-STARTUP-RECOVERY-01 rev2
PARENT = WP-ENG-QI-WORKBENCH-IMPACT-READINESS-01 rev3
RELATED_MICRO_WP = WP-ENG-QI-WORKBENCH-HOSTED-VERIFICATION-01
ROLE = BUILDER_SINGLE_WRITER
HUMAN_AUTHORITY = Human explicitly approved this bounded Work Order in the latest Planner task on 2026-09-28.
CURRENT_LEASE = POST_MERGE_RECONCILIATION + STAGE_0 + STAGE_1_COLD_RECOVERY_BACKUP + STAGE_2_GOVERNANCE_RECONCILIATION
CURRENT_STAGE = STAGE_2_GOVERNANCE_RECONCILIATION; BUILDER_RETURNED_TO_PLANNER
NEXT_ROLE_BOUNDARY = RETURN_TO_PLANNER_FOR_INDEPENDENT_REVIEWER_DISPATCH; no operational remediation or shortcut stage is authorized here.
```

The Human approval authorizes this exact local governance work, one finite cold
backup of the operational database/configuration, and later a Planner-routed
Tester launch. It authorizes local semantic commits. A later branch push and
one PR are permitted only after Tester and independent Reviewer PASS. It does
not authorize merge, release, source/test edits, database migration, crawl or
import, B09 work, a new EXE build, cleanup, or shortcut mutation in this stage.
The shortcut may be backed up and edited only if a later Planner reactivation
follows Tester PASS.

## Roadmap and architecture layer contract

```text
MASTER_ROADMAP = revision 1.3; baseline commit 3e9d0e8705665e71a448fb88144adae5ae6f7923
ROADMAP_NODE = Cross-cutting — Windows / Team Bid delivery; Engineering Toolbox / Plugins is supporting context
PRODUCT_FRONTIER = Unified Tender Warehouse / PARTIAL
DELTA_ALIGNMENT = ALIGNED; inspect the RD-0013 B09 history without reopening B09 scope or changing Delta
PRODUCT_CAPABILITY_MATURITY_CHANGE = NONE
```

```text
ARCHITECTURE_LAYER_CONTRACT
PRODUCT_LANE: Cross-cutting Windows / Team Bid delivery; internal installed-runtime recovery only.
HUMAN_CONSUMER: Human and Planner reconcile one installed startup report without changing product capability.
MACHINE_CONSUMER: Existing installed EXE and its operational configuration/database; no application code is changed.
DOMAIN_CORE: OUT_OF_SCOPE.
APPLICATION_BACKEND: OUT_OF_SCOPE for edits; one bounded Tester startup observation may run later.
SOURCE_ADAPTERS: OUT_OF_SCOPE; no crawl/import.
PERSISTENCE_INFRA: Read-only metadata plus one cold byte-for-byte DB/config backup; no DB open, SQL, checkpoint, journal change, migration, or intentional mutation.
DELIVERY_ADAPTERS: Read-only exact Start Menu shortcut target observation; edit only after Tester PASS and a later Planner reactivation.
DESKTOP_FRONTEND: No Builder launch; Tester may perform one direct EXE launch after Planner dispatch.
CLI: OUT_OF_SCOPE.
AI_CONSUMER: OUT_OF_SCOPE.
ENGINEERING_TOOLS: Read-only CodeGraph and governed evidence checks only.
DEPENDENCY_DIRECTION_CHECK: No product dependency or source change.
RATIONALE: This is a bounded operational recovery and handoff; it does not implement B09 or promote Product House maturity.
```

## Canonical checkout, live merge, and carried history

```text
CANONICAL_CHECKOUT_EXPECTED = D:\QI Technology\QI Crawler\egp-crawler-python
EXPECTED_ORIGIN_REPOSITORY = https://github.com/tanntran2000/QI-Crawler-MVP.git
VERIFIED_ORIGIN_MAIN = caf983691da60d4eaf990d09e9e1788692aabaac; git fetch and live ls-remote agree
PR_136 = MERGED; source e28800e946c813c8bf24b1f623fd60629fc5bb18; base 51463a1ba01af9cd499e0b7c7cc961c19771bbf4; merge caf983691da60d4eaf990d09e9e1788692aabaac; merged 2026-09-28T06:21:32Z
POST_MERGE_PYTHON_CI = Run 36386062925, push event, attempt 1, caf9836, completed success.
POST_MERGE_CODEQL = Run 36386062821, dynamic event, attempt 1, caf9836, completed success.
POST_MERGE_REQUIRED_JOBS = Code Quality, Tests Ubuntu 3.12, Tests Windows 3.12, Compatibility Ubuntu 3.11, Required CI Gate; all success on caf9836.
OLD_BRANCH = codex/workbench-impact-readiness-01 at c6571d6826e15092898f6b3cd63a88770bfbca54; preserved unchanged.
NEW_BRANCH = codex/installed-startup-recovery-01 created from caf983691da60d4eaf990d09e9e1788692aabaac.
```

The six preserved governance commits were cherry-picked in order, with no
amend, rebase, reset, or force operation:

| Old commit | Forward commit on this branch | Disposition |
| --- | --- | --- |
| `b622af03a74eee3ecdab2db634ba2c926bf1372e` | `cd4c90d5fdc2118258af159a9fe903661e73a6e6` | Preserved by forward cherry-pick |
| `f6c87dd40b9a1aca563416e06e368fb12d182a1d` | `988ee3cac91cfa252d53619d9d37fdd23d24518c` | Preserved by forward cherry-pick |
| `6f0ed6900e7ed7237a56039a47589f1955066205` | `e51f061329e643532de3fa0757646cbea1591574` | Preserved by forward cherry-pick |
| `44c30c425a2481edeabf721c2b2a1cb5fdb66c06` | `99d148b56e906fc104850bb77802740ae009ecde` | Preserved by forward cherry-pick |
| `e637e111174ada3e12a032227afb211a46eebd44` | `b2d7c81deb021613d2d616f5b80f5d93dc7fa9a6` | Preserved by forward cherry-pick |
| `c6571d6826e15092898f6b3cd63a88770bfbca54` | `7ac87c5b6330fb70f252fd2ebf5156dfb65221d5` | Preserved by forward cherry-pick |

The inherited old branch is not deleted or rewritten. The GitHub PR page was
stale in the web snapshot; authenticated `gh` read-only PR metadata and the
fresh main ref resolved the current state as merged. The exact main merge
commit and run identities above are the authority. PR-head checks for e28800e
and post-merge push checks for caf9836 are distinct evidence objects.

## Scope and exclusions

### Tracked write scope

1. `docs/superpowers/plans/WP-OPS-QI-INSTALLED-STARTUP-RECOVERY-01.md`
2. `docs/agent/PATH_REGISTRY.yaml` — one locator-only binding using existing PATH_IDs.
3. `docs/agent_handoff/CURRENT.md` — governed active/terminal handoff syncs.

The Stage 0/1 write scope above is historical. For the Planner-opened Stage 2
governance reconciliation only, the authorized tracked write scope is this
Work Order, `docs/agent_handoff/CURRENT.md`, the existing FM-049 entry in
`docs/agent/KNOWN_FAILURE_MODES.md`, one compact current entry in
`docs/agent/MASTER_ROADMAP_DELTA.md`, and `docs/agent/PROJECT_MEMORY.md` only
for the already-merged PR #130 source-contract fact. No other path is in scope.

### Exact external write scope

One directory only, resolved through existing `PATH.RUNTIME.BACKUPS` with
`QI_CRAWLER_DATA_DIR=D:\QI-Crawler\Data`:

```text
D:\QI-Crawler\Data\data\backups\startup-diagnosis-<UTC_RUN_ID>\
  egp.db
  config.yaml
  recovery-manifest.json
```

No additional destination or source files may be created. The Start Menu
shortcut is read-only in Stage 0/1. `release_staging/evidence/` may be used
only for sanitized metadata if needed; it is not created by default and must
never contain DB/config bytes or secrets.

### Read-only inputs

```text
OPERATIONAL_ROOT = D:\QI-Crawler
INSTALLED_EXE = D:\QI-Crawler\Current\QI-Crawler\QI-Crawler.exe
OPERATIONAL_CONFIG = D:\QI-Crawler\Data\config.yaml
OPERATIONAL_DB = D:\QI-Crawler\Data\data\database\egp.db
LEGACY_APPDATA_DB = C:\Users\Admin\AppData\Local\QI-Crawler\data\database\egp.db
START_MENU_LINK = C:\Users\Admin\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\QI-Crawler.lnk
```

`docs/agent/OPERATIONAL_RELEASE_CONTRACT.md` defines the stable operational
layout and exact DB/config locations. The legacy AppData DB is a metadata-only
comparison input, not a backup or mutation target. Do not inspect config
contents. Record only path, size, UTC modification time and SHA-256 for the
authorized files.

### Explicitly out of scope

- All source, tests, migrations, packaging, workflows, dependencies, plugins and build outputs.
- Any B09 source/test/engine, operational update, live promotion, DB/WAL/SHM copy set, candidate, acceptance or rollback root.
- Opening the GUI or EXE by Builder; launching, crawling, importing, migrating, checkpointing SQLite, changing journal mode or editing environment/user config.
- Shortcut mutation in this stage; it needs Tester PASS and a later Planner reactivation.
- Push, PR creation/change, merge, release, cleanup, deletion, ACL/ownership changes, or new EXE build.
- Reading, staging, deleting, moving, renaming or changing permissions on unknown untracked artifacts.

## Preserved Parent findings and exact outcomes

The Parent’s local and scratch history remains unchanged:

```text
PARENT_WIR_R03 = HOLD; WHOLE_LOCAL_PARENT = HOLD
LOCAL_FULL_RUN_1 = 136 failed / 1531 passed / 4 skipped / 8 errors
LOCAL_FULL_RUN_2 = 65 failed / 1610 passed / 4 skipped / 0 errors
RETRY_FAILURE_CAUSATION = NOT_FULLY_CLASSIFIED; 65 retry failures = 23 A3/F5 guard + 42 mixed document/intake/extraction/workspace nodes
FIRST_RUN_FAILED_OR_ERROR_IDS_ABSENT_FROM_RETRY_FAILURE_LIST = 79; not known retry failures; per-node PASS versus SKIP is not bound
SCRATCH_BUDGET = FAIL; 13,910 and 14,033 files exceed the 10,000-file cap; each byte total stayed below 2 GiB; final hidden-inclusive post-run audit detected the breaches
WINDOWS_PATH_LIMITATION = 276-character A3 path still reported; risk unresolved
REPO_RUFF = Builder-reported RED, 8 errors in preserved unknown $RECYCLE.BIN; not independently log-verified by Tester
CODEBASE_MEMORY_READINESS = HOLD_WITH_DIAGNOSIS; zero index attempts; no coverage/runtime claim
PARENT_HOSTED_CI = PASS for exact e28800e PR source; post-merge CI/CodeQL separately PASS on exact caf9836 merge commit
PARENT_FAILURE_MEMORY = FM-054 remains NOT_FULLY_CLASSIFIED / prevention pending; no new failure-memory finding is asserted here
```

These Parent limitations are retained context and are not automatically
caused by or blockers for this operational recovery candidate. No local
full-suite PASS, repeated startup stability, Codebase Memory readiness, B09
authority or product capability promotion is claimed.

Builder records these Stage 0/1 outcome fields without claiming the future
Tester result:

```text
STALE_SHORTCUT_TARGET = CONFIRMED when the observed link differs from the stable operational EXE path
DIRECT_EXE_STARTUP = PASS | FAIL | INCONCLUSIVE; Builder must leave INCONCLUSIVE because Builder does not launch
ORIGINAL_REPORTED_FAILURE = RESOLVED | NOT_REPRODUCED | UNRESOLVED; remains UNRESOLVED until later Tester evidence and Planner reconciliation
```

The current exact Start Menu shortcut was inspected read-only. Its target was
`D:\QI-Crawler\QI-Crawler.exe`; the operational layout contract locates the
installed executable at `D:\QI-Crawler\Current\QI-Crawler\QI-Crawler.exe`.
Therefore `STALE_SHORTCUT_TARGET=CONFIRMED` is a path-mismatch observation,
not authority to edit or launch either target.

## Data impact and recovery contract

```text
DATA_AUTHORITY = Human/operator; current live data is protected
OPERATIONAL_DB_AND_CONFIG = READ; hash and metadata only; byte-copy only when all cold-copy gates pass
LEGACY_APPDATA_DB = READ_METADATA_ONLY; never copy or mutate
INSTALLED_EXE = READ_METADATA_ONLY; never open by Builder
DATABASE_OPEN_OR_SQL = FORBIDDEN
WAL_OR_SHM_PRESENT = STOP; do not checkpoint or copy live sidecars
MIGRATION_OR_JOURNAL_MODE_CHANGE = FORBIDDEN
BACKUP_SOURCE_CONSISTENCY = ZERO_PROCESS_FROM_D:\QI-Crawler + DB WAL/SHM ABSENT + source metadata/hash stable before/after
BACKUP_RETENTION = KEEP pending Planner/Tester/review disposition; no cleanup authority
```

Immediately before the backup, use a path-aware Windows process census to
prove no process executable is located under `D:\QI-Crawler`. A relevant
`QI-Crawler.exe` process whose path cannot be resolved is a HOLD. Verify the
operational DB/config, legacy AppData DB and installed EXE exact paths and
record size, UTC modification time and SHA-256. Verify operational DB
`egp.db-wal` and `egp.db-shm` are absent. Do not launch the app.

Before the copy, prove every existing source and destination ancestor resolves
inside its authorized root and is not a reparse point; the exact run target
does not exist; the backup parent exists; D: retains at least 10 GiB free.
Copy `egp.db` and `config.yaml` byte-for-byte into the one run directory, then
write a sanitized JSON manifest with run ID, exact source/target paths,
pre/post source size/time/hash, copy hashes/sizes, process/sidecar results,
UTC timestamps, and verification status. Do not include file contents, YAML
values, credentials, or unrelated metadata.

After copy, repeat source size/time/hash, process census and WAL/SHM absence
checks. Copy hashes must match source hashes. Enumerate the new target only:
it must contain exactly the three named files, total no more than 5 MiB. A
changed source, process appearance, sidecar, collision, path escape/reparse,
hash mismatch, missing parent, budget breach or reserve breach means
`STOP/HOLD`; preserve the partial evidence and do not launch the EXE. No retry
or cleanup is permitted.

## Stage 0 — post-merge entry and governance

1. Re-resolve canonical cwd, top-level, git-dir/common-dir, origin, branch, HEAD, tracked/index state and unknown names.
2. Fetch `origin/main` read-only. Verify the PR #136 merge object is an ancestor of live main (or report the newer exact main head); read PR #136 and post-merge CI evidence when available.
3. Create `codex/installed-startup-recovery-01` from verified `origin/main` only if the local and remote branch names are free.
4. Preserve the old workbench branch. Carry the six named governance commits forward by sequential cherry-pick without amend/rebase/force; any conflict or semantic incompatibility is an immediate HOLD.
5. Read the required role/roadmap/operating/path/CI contracts; record the Stage 0 plugin evidence and the current startup layout/shortcut mismatch.
6. Materialize this Work Order, one locator-only registry binding using existing IDs, and the active `CURRENT.md` state. No other tracked edit is authorized.

## Stage 1 — one cold recovery backup; no application launch

The Stage 1 procedure and gates are in the Data Impact and Recovery Contract.
Complete one preflight and at most one backup run. The UTC run ID uses
`YYYYMMDDTHHMMSSZ`; reject a collision and do not retry with another name.
Do not create the optional repository evidence root unless sanitized evidence
cannot be represented by the recovery manifest and CURRENT/Work Order.

On Stage 1 success, set `DIRECT_LAUNCH_READY=YES` only to mean that Tester may
be considered by Planner for one later direct launch. It does not mean startup
passed. Keep `DIRECT_EXE_STARTUP=INCONCLUSIVE` and
`ORIGINAL_REPORTED_FAILURE=UNRESOLVED` until Tester evidence exists.

## Later Tester and conditional shortcut boundary

After Builder returns, Planner may dispatch `TESTER_MACHINE_VERIFIER` for at
most one direct launch of the exact installed EXE. Tester reports
`DIRECT_EXE_STARTUP=PASS|FAIL|INCONCLUSIVE`, exact executable identity,
timestamped result, process/sidecar/data changes and limitations. No crawl,
import, migration or second attempt. Startup success is one observed run, not
stability proof. Planner reconciles the result.

Only after Tester PASS and a new Planner reactivation may the Builder back up
and edit the exact Start Menu shortcut. That future authorized correction
must preserve the original shortcut bytes, verify target/working directory and
prove the corrected link without launching it. No shortcut backup or edit is
authorized in Stage 0/1.

## CI Fitness Contract

```text
CURRENT WP: WP-OPS-QI-INSTALLED-STARTUP-RECOVERY-01 rev2, Stage 0/1
CAPABILITY UNDER CHANGE: Operational startup recovery evidence and handoff; no product code change.
CRITICAL RISKS: Live DB inconsistency, concurrent process/write, sidecar omission, stale shortcut targeting, accidental app launch or data migration, sensitive metadata leakage.
BASELINE GATES TO KEEP: Repository CI and exact-head policy remain unchanged; no CI workflow or test is weakened.
WP-SPECIFIC GATES REQUIRED: Canonical identity/live-main/PR merge check; preserved commit ancestry; unique PATH_REGISTRY binding; process/sidecar/path/reparse/collision gates; source pre/post size-time-hash equality; exact 3-file/5-MiB backup inventory and source-copy hash equality; diff/scope/status checks.
GATES NOT REQUIRED YET: Full pytest, Ruff, hosted CI rerun, app build/install, migration, crawl/import, repeated-start stability, or Codebase Memory index.
MAX JOB RUNTIME: Stage 0 read/identity checks <=10 minutes; one Stage 1 census/hash/copy sequence <=15 minutes; documentation/static checks <=5 minutes; any later Tester direct-launch observation <=5 minutes.
CI CHANGE REQUIRED BEFORE IMPLEMENTATION: NO.
RATIONALE: This stage is a governed docs transition and one offline byte-copy. No source/test/workflow change is allowed. If source/test scope is proposed, stop and replan rather than alter CI or product files.
```

## Path and artifact budgets

`PATH_REGISTRY_BASELINE=1.0.20`; impact is `ADD_ENTRY` for one WP locator
binding, with revision incremented once. Existing IDs only:
`PATH.GOV.PLAN`, `PATH.GOV.HANDOFF`, `PATH.EVIDENCE.WP_RUN`,
`PATH.RUNTIME.BACKUPS`, `PATH.RUNTIME.DB`, `PATH.RUNTIME.CONFIG`.

| Artifact | Resolved destination | Budget | Lifecycle |
| --- | --- | --- | --- |
| Governance Work Order | `docs/superpowers/plans/WP-OPS-QI-INSTALLED-STARTUP-RECOVERY-01.md` | 1 tracked file | Durable, reviewed |
| Locator binding | `docs/agent/PATH_REGISTRY.yaml` | 1 binding; no new path ID | Durable, locator only |
| Active/terminal handoff | `docs/agent_handoff/CURRENT.md` | 1 tracked file | Durable, active authority |
| Cold recovery backup | `D:\QI-Crawler\Data\data\backups\startup-diagnosis-{UTC_RUN_ID}\` | 1 run, 3 files, 5 MiB total | Local-only protected recovery; KEEP pending review |
| Optional sanitized evidence | `release_staging/evidence/WP-OPS-QI-INSTALLED-STARTUP-RECOVERY-01-{UTC_RUN_ID}/` | At most 1 run, 20 files, 20 MiB | Local-only unless separately approved; no DB/config bytes or secrets; not created by default |

Unknown or unregistered outputs are KEEP and block further writes. Do not stage
or commit recovery bytes, optional ignored evidence, secrets or unknown files.

## Plugin applicability and evidence

Every REQUIRED plugin packet includes `PLUGIN`, `PURPOSE`, `INVOCATION`,
`RESULT`, `FALLBACK`, `IMPACT_RADIUS`, `EDIT_RADIUS`, `TEST_RADIUS`, and
`LIMITATION`. Result classifications are only
`USED_AND_SUCCEEDED`, `USED_WITH_FALLBACK`, `TOOL_UNAVAILABLE`, or
`NOT_APPLICABLE`. Availability/configuration alone is not use evidence.

| Plugin | Applicability | Required evidence / boundary |
| --- | --- | --- |
| `qi-context-boot` | REQUIRED | Read-only identity, role, Roadmap/Delta, CURRENT and authority entry. |
| CodeGraph | REQUIRED | Structural path/config/startup impact before source conclusions; evidence only. |
| `systematic-debugging` | REQUIRED | Investigate reported startup/shortcut failure before proposing any correction; no fix in this lease. |
| `verification-before-completion` | REQUIRED | Fresh command evidence before commit and handoff claims. |
| `codebase-memory` | REQUIRED_ACTION: READINESS_ONLY | Attempt the published read-only skill/readiness route; no index call is authorized. |
| `skill-creator` | NOT_APPLICABLE | No skill edit. |
| `test-driven-development` | NOT_APPLICABLE | No behavior/test edit. |
| B09 live/runtime mutation tools | NOT_APPLICABLE | No B09 operation or live mutation. |

## Verification, commit, and handoff

Stage 0/1 verification is limited to: registry JSON-compatible YAML parse and
binding/ID uniqueness; CURRENT key uniqueness and required-field completeness;
Work Order required-section checks; exact file inventory and scope; `git diff
--check`; `git diff --name-status`; `git status`; and proof that no source/test
path changed. Do not run pytest, Ruff, Codebase Memory indexing, full suite, or
CI. Do not inspect unknown untracked content. Keep separate semantic commits
for the Work Order/registry entry and terminal evidence handoff when needed.

```text
REMOTE_MUTATION = NONE IN THIS STAGE
PUSH_OR_PR = NO
MERGE_OR_RELEASE = NO
DIRECT_EXE_LAUNCH_BY_BUILDER = NO
SHORTCUT_EDIT = NO
```

Stop on any identity/ref/branch conflict, tracked dirt or concurrent writer,
unresolved authority, path/symlink/reparse ambiguity, live process, DB sidecar,
source drift, backup collision/mismatch/budget breach, required out-of-scope
edit, evidence access failure, or any need to launch/modify/migrate/clean. The
Builder returns exact commits, branch/base/head, PR/main/CI facts, carry-forward
mapping, shortcut observation, source/copy hashes and sizes, process/sidecar
checks, inventory/free-space, plugin evidence, tracked/index/untracked state,
Spine fields and `DIRECT_LAUNCH_READY=YES|NO`. Next authority is Planner.

## Stage 0 result at Work Order materialization

```text
CHECKOUT_IDENTITY_GATE = PASS
ROADMAP_ENTRY_GATE = PASS; FULL READ; ALIGNED; NO PRODUCT MATURITY CHANGE
ROLE_ENTRY_GATE = PASS; EXPLICIT HUMAN TASK + THIS WORK ORDER + CURRENT BUILDER ROLE RECONCILE
PR_136_RECONCILIATION = MERGED at caf983691da60d4eaf990d09e9e1788692aabaac; post-merge Python CI and CodeQL success at exact merge SHA
NEW_BRANCH = codex/installed-startup-recovery-01 from origin/main caf9836
SIX_GOVERNANCE_COMMITS = FORWARD_CHERRY_PICKED; original old branch preserved
STALE_SHORTCUT_TARGET = CONFIRMED; read-only target mismatch
STAGE_1_PREFLIGHT_AND_BACKUP = PASS; run 20260928T075727Z; exact backup inventory and hashes verified
DIRECT_LAUNCH_READY = YES; Planner may consider one later Tester direct launch
DIRECT_EXE_STARTUP = INCONCLUSIVE
ORIGINAL_REPORTED_FAILURE = UNRESOLVED
```

Stage 0/1 synchronized the Work Order, PATH_REGISTRY and CURRENT. After the
Tester launch and Planner-admitted root-cause reconciliation, Stage 2 updates
FM-049, a compact current Delta entry and the merged-fact-only Project Memory
entry below; it does not update product capability maturity or authorize B09.

```text
SPINE_IMPACT = MULTIPLE
SPINE_TARGET_FILES = docs/superpowers/plans/WP-OPS-QI-INSTALLED-STARTUP-RECOVERY-01.md; docs/agent/PATH_REGISTRY.yaml; docs/agent_handoff/CURRENT.md
SPINE_SYNC_STATE = PASS when the recorded stage matches observed facts; HOLD on any unresolved identity/data/backup mismatch
```

## Stage 1 result — one cold backup; Builder did not launch

```text
RUN_ID = 20260928T075727Z
BACKUP_RESULT = PASS
BACKUP_PATH = D:\QI-Crawler\Data\data\backups\startup-diagnosis-20260928T075727Z\
BACKUP_INVENTORY = egp.db 2043904 bytes; config.yaml 1835 bytes; recovery-manifest.json 3055 bytes; exactly 3 files
BACKUP_TOTAL_BYTES = 2048794; MAXIMUM=5242880
RECOVERY_MANIFEST_SHA256 = 020e7bc29875e63a267d3c4ab36f503c4dca9cc18e0ee9fac56bd0270d96be46
OPERATIONAL_DB_SOURCE_SHA256 = 33a3a5adaca15514a18714dbd9281c224c174b8471341eeb8c333c11748818ee
OPERATIONAL_DB_COPY_SHA256 = 33a3a5adaca15514a18714dbd9281c224c174b8471341eeb8c333c11748818ee
OPERATIONAL_CONFIG_SOURCE_SHA256 = bf650834422f2b59a6ce0cd61d4cc786c1f4cf89f281831cf17788d4b0ea0ebf
OPERATIONAL_CONFIG_COPY_SHA256 = bf650834422f2b59a6ce0cd61d4cc786c1f4cf89f281831cf17788d4b0ea0ebf
SOURCE_METADATA = UNCHANGED; sizes, UTC mtimes and SHA-256 match preflight after copy
PROCESS_CENSUS = CIM PATH-AWARE; ZERO D:\QI-Crawler MATCHES BEFORE/COPY/AFTER; ZERO UNRESOLVED QI-Crawler.exe PATHS
OPERATIONAL_WAL = ABSENT BEFORE AND AFTER
OPERATIONAL_SHM = ABSENT BEFORE AND AFTER
PATH_CONTAINMENT_REPARSE = PASS for authorized source/destination ancestors and new target
D_FREE_BYTES = 19367219200 BEFORE; 19324203008 AFTER; ABOVE 10 GiB RESERVE
INSTALLED_EXE_METADATA = D:\QI-Crawler\Current\QI-Crawler\QI-Crawler.exe; 19873214 bytes; 2026-09-23T01:01:48.8803075Z; SHA256 05230277bbbb2e2d0858e88cda04651dfcd75eb8ec39f83f18aa7e5fb7c691b9
LEGACY_APPDATA_DB_METADATA = C:\Users\Admin\AppData\Local\QI-Crawler\data\database\egp.db; 1945600 bytes; 2026-09-03T02:11:58.7475465Z; SHA256 70e7ae0cf7d64ef916ac56fec41be84bea533abaa229f835954edad917230477
EVIDENCE_ROOT = NOT_CREATED; sanitized recovery-manifest.json remains in the authorized operational backup
STALE_SHORTCUT_TARGET = CONFIRMED; observed target D:\QI-Crawler\QI-Crawler.exe differs from contract path D:\QI-Crawler\Current\QI-Crawler\QI-Crawler.exe
DIRECT_EXE_STARTUP = INCONCLUSIVE; NO EXE/GUI LAUNCH BY BUILDER
ORIGINAL_REPORTED_FAILURE = UNRESOLVED; Tester evidence pending
```

The first directory-creation command was rejected because `New-Item` does not
accept `-LiteralPath`; it failed before target creation. A subsequent copy
operation copied the two authorized files exactly once, then its post-check
script stopped before manifest creation because a constructed sidecar array
had no second element. The same target/run ID was rechecked read-only; only the
two expected copies existed, source metadata and copy hashes matched, the
process and sidecar gates remained clear, and D: retained its reserve. The
manifest was then written once and the exact three-file inventory/hash/budget
was verified. No second copy, alternate run, cleanup or application launch
occurred.

```text
BUILDER_RESULT = STAGE_0_AND_STAGE_1_COMPLETE
HANDOFF_READY = YES_FOR_PLANNER_REVIEW_AND_TESTER_DISPATCH
EXACTLY_ONE_NEXT_ACTION = PLANNER REVIEWS THE EXACT BUILDER CANDIDATE AND BACKUP EVIDENCE; IF ACCEPTED, DISPATCH TESTER FOR AT MOST ONE DIRECT INSTALLED-EXE LAUNCH
NEXT_AUTHORITY = PLANNER_ARCHITECT
```

## Stage 2 result — Tester failure and Planner-admitted reconciliation

The record below separates Tester observations from the Planner-admitted
causal reconciliation. Builder did not launch the application and did not
re-originate the root-cause decision.

```text
STAGE_2_AUTHORITY = PLANNER-OPENED GOVERNANCE RECONCILIATION UNDER THE EXISTING HUMAN-APPROVED WORK PACKAGE; NO NEW RUNTIME/SHORTCUT/OPERATIONAL-UPDATE AUTHORITY
TESTER_REPORT_ID = WP-OPS-QI-INSTALLED-STARTUP-RECOVERY-01-TESTER-20260928T083433Z
DIRECT_LAUNCH = 2026-09-28T08:34:28Z; PID 10112; exact installed EXE and working directory; exited itself after 4.73 seconds; exit code 1
GUI_APPEARED = NO
LOG_APPEND = NONE; APPLICATION_EVENT = NONE; FORCED_TERMINATION = NO
TESTER_CLASSIFICATIONS = DIRECT_EXE_STARTUP=FAIL; GUI_APPEARED=NO; RUNTIME_DATA_ROOT=INCONCLUSIVE; RUNTIME_DATABASE=INCONCLUSIVE; NORMAL_CLOSE=INCONCLUSIVE
MUTATION_CLASSIFICATIONS = DB_MUTATION=NONE; CONFIG_MUTATION=NONE; APPDATA_LEGACY_DB_MUTATION=NONE; SCHEMA_MIGRATION=NONE
REMAINING_TESTER_RESULTS = ORIGINAL_REPORTED_FAILURE=UNRESOLVED; SHORTCUT_EDIT_ELIGIBLE=NO
OPERATIONAL_INVARIANTS = OPERATIONAL_DB/CONFIG/LEGACY_APPDATA_DB/SHORTCUT/INVENTORIES/WAL/SHM UNCHANGED
PLANNER_ADMITTED_ROOT_CAUSE = The installed binary source SHA 79b62ec93547f210aad162dcbf926c0bd2c81ab1 calls authorize_frozen_runtime before file logging. Its old validate_operational_acceptance requires current operational DB SHA to equal receipt promotion-time database_sha256. The exact first proven failing old-source condition is OPERATIONAL_DATABASE_SHA_MISMATCH.
EXPECTED_RECEIPT_DB_SHA256 = c35e1f3618871d453ee2950f37cbcce1466435948e5692360b9d0512461a8f2a
CURRENT_LEGITIMATE_OPERATIONAL_DB_SHA256 = 33a3a5adaca15514a18714dbd9281c224c174b8471341eeb8c333c11748818ee
OTHER_PREVIOUS_GATES = OPERATIONAL_LAYOUT/RUNTIME_DIRS; EXE/MANIFEST/BUILD_INFO/MIGRATION_RECEIPT HASHES AND IDENTITIES; CONFIG PRESENCE; SCHEMA 0022_add_tender_recovery_events; SQLITE quick_check=ok — DIRECTLY CHECKED PASS
SOURCE_CORRECTION = 0d9a3c41e71d368aa4c21aefdd970dc41343e6af; PR #130 merged via 179c0712a14161ea25096e66a127f6022bf696fd; included in origin/main caf983691da60d4eaf990d09e9e1788692aabaac; Reviewer PASS per admitted evidence
SOURCE_CORRECTION_EVIDENCE = PR #130 reported 8 checks passed; targeted 186 passed/2 skipped; full 1621 passed/2 skipped. This applies to that merged source correction, not the older installed binary or this docs-only candidate.
MERGED_SOURCE_CHANGE = acceptance.database_sha256 is immutable migration-baseline evidence; config-binding guards/tests added. No further FM-049 source correction is identified.
RUNTIME_REMEDIATION = NEW_RUNTIME_BINARY_REQUIRED=YES; ONE_FILE_CONFIG_REPAIR_SUFFICIENT=NO; RERUN_ORIGINAL_PROMOTION_REQUIRED=NO; installed binary predates the merged correction.
PROHIBITED = NO RECEIPT HASH REWRITE; NO RERUN OF ORIGINAL 0020-to-0022 PROMOTION/MIGRATION; NO LIVE REMEDIATION; NO APP BUILD/REPLACEMENT OR SHORTCUT EDIT IN THIS WP
SHORTCUT_STAGE = INELIGIBLE after direct startup FAIL and under current scope
BACKUP_DISPOSITION = KEEP_RECOVERY; cleanup NOT_AUTHORIZED/NOT_EXECUTED; unknown artifacts remain KEEP
NEXT_PROPOSED_OBJECTIVE = Separately propose a bounded new runtime build from main containing 0d9a3c4, verify exact build/release identity, then use a separately Human-approved operational update/replacement contract that preserves Data and rollback. PROPOSED ONLY; NOT AUTHORIZED.
PARENT_STATE = WHOLE LOCAL PARENT HOLD AND HISTORICAL LIMITATIONS PRESERVED; no relationship to the 65 pytest failures established
SPINE_IMPACT = MULTIPLE
SPINE_TARGET_FILES = docs/superpowers/plans/WP-OPS-QI-INSTALLED-STARTUP-RECOVERY-01.md; docs/agent_handoff/CURRENT.md; docs/agent/KNOWN_FAILURE_MODES.md; docs/agent/MASTER_ROADMAP_DELTA.md; docs/agent/PROJECT_MEMORY.md
SPINE_SYNC_STATE = PASS
BUILDER_RESULT = STAGE_2_GOVERNANCE_RECONCILIATION_COMPLETE; NO OPERATIONAL FIX OR SHORTCUT STAGE
HANDOFF_READY = YES_FOR_PLANNER_INDEPENDENT_REVIEWER_DISPATCH
EXACTLY_ONE_NEXT_ACTION = PLANNER REVIEWS THIS EXACT GOVERNANCE CANDIDATE AND DISPATCHES AN INDEPENDENT REVIEWER; THE FUTURE RUNTIME-REPLACEMENT OBJECTIVE REMAINS PROPOSED ONLY
NEXT_AUTHORITY = PLANNER_ARCHITECT
```
