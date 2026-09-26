# WO-GOV-QI-AGENT-LOOP-CONSOLIDATION-01

## Control block

```text
WORK_ORDER_ID = WO-GOV-QI-AGENT-LOOP-CONSOLIDATION-01
TITLE = QI Agent Loop role, routing, handoff and skill consolidation
STATE = CORRECTION_07_PR_READINESS_DOC_FRESHNESS
APPROVAL_SCOPE = FIFTEEN_PATH_AGGREGATE_AGENT_LOOP; THREE_PATH_CORRECTION_07
HUMAN_DESIGN_DECISION = APPROVED
HUMAN_DESIGN_DECISION_DATE = 2026-09-25
ACTIVE_PARENT_WP = GOVERNANCE_AGENT_LOOP_CONSOLIDATION
ACTIVE_MICRO_WP = CORRECTION_07_PR_READINESS_DOC_FRESHNESS
CURRENT_AUTHORITY = BUILDER_SINGLE_WRITER
NEXT_AUTHORITY = TESTER_MACHINE_VERIFIER
HANDOFF_READY = YES_FOR_CORRECTION_07_MACHINE_VERIFICATION_AFTER_BUILDER_COMMIT
CANONICAL_CHECKOUT_EXPECTED = D:\QI Technology\QI Crawler\egp-crawler-python
EXPECTED_ORIGIN_REPOSITORY = https://github.com/tanntran2000/QI-Crawler-MVP.git
PATH_ID = PATH.GOV.PLAN
```

Human A0 approved the design direction, the exact local B09 preservation action,
the governance-branch transition and Planner execution of the Agent Loop. That
authority permits bounded local Builder execution and semantic local commits
inside this Work Order. It does not authorize push, Pull Request creation, merge
or release. Those remote and terminal permissions remain separate.

## 1. Mission

Consolidate the overlapping QI Agent Loop role, reporting, checkpoint/PR and
active-handoff contracts into one governed operating model with one canonical
owner for each fact.

The smallest complete outcome is:

1. one unambiguous authority and reporting model;
2. one canonical owner per contract;
3. a compact active `CURRENT.md` with verifiable history locators;
4. an aligned `qi-agent-loop` skill and skill lock; and
5. exact-object local, CI and independent-review evidence before Human merge.

This Work Order does not create an agent runner, model router, queue, daemon,
hook, MCP server, autonomous control plane or other runtime system. Existing
Codex tasks remain the execution medium and the Planner remains the coordinator.

## 2. Human intent to protect

- Human works directly with the Planner in the coordinating task.
- Normal Builder, Tester and Reviewer reports return to the Planner.
- Critical events outside an assigned role's authority are escalated through
  the Planner to Human A0.
- Role authority must not be inferred from a model name.
- One Builder is the Single Writer.
- Testing, independent review, Planner reconciliation and Human authority remain
  separate.
- Agent Loop governance must not alter or silently absorb B09 implementation.
- Active handoff files must remain short, factual and actionable rather than
  accumulating chat history.

## 3. Authority model

```text
HUMAN A0
  -> PLANNER_ARCHITECT
       -> BUILDER_SINGLE_WRITER
       -> MACHINE_VERIFIER / TESTER
       -> INDEPENDENT_REVIEWER_AUDITOR
```

### 3.1 Four operational roles

The supervised Agent Loop has four operational roles beneath Human A0:

1. `PLANNER_ARCHITECT`
2. `BUILDER_SINGLE_WRITER`
3. `MACHINE_VERIFIER` / Tester
4. `INDEPENDENT_REVIEWER_AUDITOR`

Role membership does not imply equal authority. Tester is a full operational
role for machine evidence while remaining evidence-only: it has no scope,
acceptance, WP-closure, routing-policy, merge or release authority. The active
governance model does not maintain a second structural abstraction over these
roles.

### 3.2 Planner

The Planner:

- translates Human intent into a bounded Work Order;
- coordinates role entry, routing and evidence;
- reviews Builder results for scope and evidence;
- reconciles Tester evidence and Reviewer verdicts;
- reports material decisions and unresolved matters to Human; and
- does not edit Builder implementation, replace machine verification or rewrite
  the independent Reviewer verdict.

### 3.3 Builder

The Builder:

- is the only Writer during the approved execution lease;
- writes only within the exact allowlist;
- follows the approved Work Order and finite correction budget;
- returns results, blockers and scope findings to the Planner; and
- cannot expand scope, change acceptance, merge, release or originate Human,
  Planner or Reviewer decisions.

### 3.4 Machine Verifier / Tester

The Tester:

- executes the approved verification contract;
- reports exact commands, environment, Git object, result and limitation;
- may classify an individual verification attempt as `PASS`, `FAIL`,
  `BLOCKED` or `INCONCLUSIVE`; and
- returns evidence to the Planner.

The Tester cannot:

- edit code or governance documents;
- change acceptance criteria;
- close a Work Package;
- decide routing, policy, merge or release;
- replace the independent Reviewer; or
- rewrite the Reviewer verdict or Planner reconciliation.

### 3.5 Independent Reviewer

The Reviewer:

- independently audits the exact authorized Git range in the canonical checkout;
- challenges scope, authority, evidence, CI fitness and false-safe claims;
- returns an independent verdict to the Planner; and
- cannot be instructed to return `PASS`, merge or release.

### 3.6 Human A0

Human A0 retains material business, architecture, merge and release authority.
Design approval, execution authority, remote mutation and merge authority are
distinct decisions.

## 4. Canonical reporting flow

```text
HUMAN MATERIAL INTENT
  -> PLANNER WORK ORDER
  -> BUILDER EXECUTION
  -> PLANNER BUILDER-RESULT REVIEW
  -> TESTER MACHINE EVIDENCE WHEN APPLICABLE
  -> PLANNER EVIDENCE REVIEW
  -> INDEPENDENT REVIEWER AUDIT
  -> PLANNER POST-REVIEW RECONCILIATION
  -> HUMAN MATERIAL / MERGE / RELEASE DECISION
```

Normal role reports go to the Planner in the coordinating task. A critical
authority, safety, data-integrity, scope or evidence conflict is reported to the
Planner for Human escalation. A role must not bypass this route to start work in
another Planner task.

## 5. Canonical owner map

| Fact or contract | Canonical owner | Dependent-document rule |
|---|---|---|
| Repository laws and authority boundaries | `AGENTS.md` | Reference; do not duplicate the full law |
| Role contract and reporting flow | `docs/agent/OPERATING_MODEL.md` | Canonical operational definition |
| Boot, read-in and role prompt profile | `docs/agent/ROLE_BOOT_AND_PROMPT_PROFILES.md` | Reference role and Git lifecycle owners |
| Commit, checkpoint, push, PR, audit and merge lifecycle | `docs/agent/LOCAL_STAGED_INTEGRATION.md` | Canonical integration definition |
| Human A0 decisions | `docs/agent/FEEDBACK_LEDGER.md` | Record decision and disposition once |
| Active handoff state | `docs/agent_handoff/CURRENT.md` | One current actionable snapshot only |
| Product strategy and layer classification | `docs/agent/MASTER_ROADMAP.md` | Update only the active Agent Loop role terminology authorized by Correction 04 |
| Agent Workbench overview and artifact count | `docs/agent/QI_AGENT_WORKBENCH.md` | Update only the stale approved-artifact count from nine to ten |
| Unresolved strategic/product change | `docs/agent/MASTER_ROADMAP_DELTA.md` | Update only on an actual Delta trigger |
| Agent Loop operational workflow | `plugins/qi-agent-workbench/skills/qi-agent-loop/SKILL.md` | Workflow only; cannot originate authority |
| Skill content identity | `plugins/qi-agent-workbench/skills-lock.json` | Generated from actual governed skill content |
| Work Order/path locator | `docs/agent/PATH_REGISTRY.yaml` | Locator only; does not expand scope |

Dependent documents use a short reference to the canonical owner rather than
repeating a competing contract.

## 6. Architecture layer contract

```text
PRODUCT_HOUSE_IMPACT = NONE
ARCHITECTURE_LAYER = GOVERNANCE_AND_AGENT_WORKBENCH
PRODUCTION_RUNTIME_CHANGE = NO
DATABASE_CHANGE = NO
GUI_CHANGE = NO
PACKAGING_CHANGE = NO
RELEASE_IMPACT = GOVERNANCE_DOCS_SKILL_AND_GOVERNANCE_TEST_ONLY
MODEL_RUNTIME_OR_RUNNER = OUT_OF_SCOPE
```

The Master Roadmap remains the product architecture authority. This Work Order
aligns governance and skill workflow only and cannot declare a new product
capability.

## 7. Verified baseline at design capture

```text
CANONICAL_TOPLEVEL = D:/QI Technology/QI Crawler/egp-crawler-python
GIT_DIR = .git
GIT_COMMON_DIR = .git
ORIGIN = https://github.com/tanntran2000/QI-Crawler-MVP.git
CURRENT_BRANCH = codex/b09-bridge-a-wal-coherence
CURRENT_HEAD = 26ef4a2476b923b456ac7df3f1e93f603dcb138b
ORIGIN_MAIN = 179c0712a14161ea25096e66a127f6022bf696fd
AGENT_LOOP_REFERENCE_COMMIT = 17532fc544f8ae5c9b8c1ed131af40e81e02b5de
```

The reference commit is semantic input only. It must not be blindly
cherry-picked because it overlaps handoff/governance state from another
baseline.

## 8. Entry prerequisite: preserve B09 without broadening this Work Order

The canonical checkout currently contains two tracked B09 changes:

```text
src/qi_crawler/operational_update.py
SHA256 = 87DD4D680C716CDB0FC54AE03DF18FCDD3ED82EB6A0F98E4621F0D565C824ED9

tests/test_operational_update.py
SHA256 = 7A49CEA99CE9F994C81199C646E0B867FCE7FCD48B4148D76E0EF0C945AA1559

COMBINED_BINARY_DIFF_ID = 411b558f64ef14b75ec5182bca46d5682adb51f2
```

Before governance execution, the B09 owner must receive separate Human A0
permission to create one local preservation commit containing exactly these two
tracked files.

The preservation action must:

- preserve the exact files and identities;
- make no claim that B09, Bridge A or verification passed;
- avoid push and hosted CI;
- avoid governance-document changes;
- exclude every untracked artifact;
- record B09 as `PARKED_PRESERVED_LOCAL`; and
- leave the tracked tree clean before branch transition.

It must not use stash, reset, clean, worktree, a sibling clone or deletion.
Unknown and untracked artifacts remain `KEEP`.

The prior permission for an Agent Loop docs checkpoint does not authorize this
B09 source/test preservation commit.

## 9. Proposed governance baseline after the prerequisite

```text
BASE_REF = origin/main
BASE_SHA = 179c0712a14161ea25096e66a127f6022bf696fd
PROPOSED_BRANCH = codex/agent-loop-consolidation-01
REFERENCE_ONLY = 17532fc544f8ae5c9b8c1ed131af40e81e02b5de
```

Human separately authorized this branch transition. The Builder must reapply
only the semantics that match this Work Order and the live authority documents.

### 9.1 Entry realization

```text
B09_TRANSITION_DOC_COMMIT = f2fa21592f58a481347996f94d2b0d583dbb87c9
B09_PRESERVATION_COMMIT = 9bc64942f35c41d002ef80a74c7a02851422b0e8
B09_PRESERVATION_PATHS = src/qi_crawler/operational_update.py;
  tests/test_operational_update.py
B09_PRESERVATION_HASHES =
  87DD4D680C716CDB0FC54AE03DF18FCDD3ED82EB6A0F98E4621F0D565C824ED9;
  7A49CEA99CE9F994C81199C646E0B867FCE7FCD48B4148D76E0EF0C945AA1559
B09_STATE = PARKED_PRESERVED_LOCAL; BRIDGE_A_HOLD; NOT_PUSHED
GOVERNANCE_BRANCH = codex/agent-loop-consolidation-01
GOVERNANCE_BASE = 179c0712a14161ea25096e66a127f6022bf696fd
TRACKED_ENTRY_TREE = CLEAN
UNTRACKED = KEEP
LIVE_QI_AGENT_LOOP_SKILL = ABSENT_ON_ORIGIN_MAIN
REFERENCE_QI_AGENT_LOOP_SKILL =
  17532fc544f8ae5c9b8c1ed131af40e81e02b5de:plugins/qi-agent-workbench/skills/qi-agent-loop/SKILL.md
REFERENCE_USE = SEMANTIC_INPUT_ONLY; NO_BLIND_CHERRY_PICK
```

These facts were verified by the Planner after the Builder returned the local
preservation checkpoint. The branch transition is complete; the Builder must
still repeat canonical checkout and entry-gate verification before writing.

## 10. Minimum write scope

### 10.1 Required write allowlist

1. `docs/superpowers/plans/WO-GOV-QI-AGENT-LOOP-CONSOLIDATION-01.md`
2. `docs/agent/OPERATING_MODEL.md`
3. `docs/agent/ROLE_BOOT_AND_PROMPT_PROFILES.md`
4. `docs/agent/LOCAL_STAGED_INTEGRATION.md`
5. `docs/agent/FEEDBACK_LEDGER.md`
6. `docs/agent/PATH_REGISTRY.yaml`
7. `docs/agent_handoff/CURRENT.md`
8. `plugins/qi-agent-workbench/skills/qi-agent-loop/SKILL.md`
9. `plugins/qi-agent-workbench/skills-lock.json`
10. `tests/agent_workbench/test_skills_lock.py`
11. `AGENTS.md`
12. `docs/agent/MASTER_ROADMAP.md`
13. `docs/agent/HUMAN_COLLABORATION.md`
14. `docs/agent/QI_AGENT_WORKBENCH.md`

### 10.2 Mandatory authorities and verification inputs

- `docs/agent/MASTER_ROADMAP_DELTA.md`
- `docs/agent/CI_CONTRACT.md`
- `docs/agent/PATH_REGISTRY_CONTRACT.md`
- `plugins/qi-agent-workbench/skills/qi-context-boot/SKILL.md`
- directly relevant existing Agent Workbench tests

If meeting acceptance requires editing a read-only or unlisted file, the Builder
returns `SCOPE_EXPANSION_REQUIRED` and stops. The Work Order does not
automatically expand.

### 10.3 Correction 02: exact lock-test scope proposal

Stage 2 added the approved tenth lock artifact,
`skills/qi-agent-loop/SKILL.md`. The existing canonical lock test still hard-
codes the previous nine-artifact set and the assertion
`len(manifest["files"]) == 9`. The lock verifier and skill validator pass, while
the targeted test returns 12 PASS and one failure at this obsolete expectation.

Correction 03 incorporates the Human-directed minimum test correction, limited
to:

1. add `skills/qi-agent-loop/SKILL.md` to `EXPECTED_ARTIFACTS`; and
2. change the exact expected count from `9` to `10`.

No test abstraction, verifier change, skip, xfail, gate weakening or unrelated
test edit is authorized. After correction, run the exact targeted file once and,
if green, continue the existing full sequential verification contract.

The first measured registered targeted run created 156 files, 87 directories
and 1,443,266 bytes. The earlier 64-file/eight-directory estimate is therefore
superseded by measured evidence; it is not represented as having passed. Revise
the uncommitted WP artifact budget using the measured targeted ceiling and the
separate proposed full-WP ceiling below:

```text
TARGETED_RUN_ROOT_MAX_FILES = 256
TARGETED_RUN_ROOT_MAX_DIRS = 128
TARGETED_RUN_ROOT_MAX_BYTES = 16777216
# Proposed finite full-WP ceiling; not a measured targeted limit.
CUMULATIVE_WP_TEMP_MAX_FILES = 10000
CUMULATIVE_WP_TEMP_MAX_DIRS = 5000
CUMULATIVE_WP_TEMP_MAX_BYTES = 1073741824
MIN_D_FREE_BYTES = 10737418240
```

Existing test artifacts remain `KEEP`; this correction grants no cleanup.

### 10.4 Correction 03: four-role and report-admission forward correction

Human A0 requested one supervised four-role model without the additional
three-authority-layer interpretation. Direct inspection confirmed the obsolete
layer language in
`AGENTS.md`, the Master Roadmap, Operating Model, Role Boot, Human Collaboration,
this Work Order and the new skill. Historical Feedback entries may retain the
wording as contemporaneous evidence; add a new decision entry that supersedes
their active operational effect rather than rewriting history.

The final active contract shall state:

```text
HUMAN_A0 = MATERIAL_AUTHORITY_ABOVE_THE_LOOP
OPERATIONAL_ROLES = PLANNER; BUILDER; TESTER_MACHINE_VERIFIER; REVIEWER
TESTER = OPERATIONAL_ROLE_WITH_EVIDENCE_ONLY_AUTHORITY
FOUR_ROLES != FOUR_EQUAL_AUTHORITIES
ROLE > MODEL_NAME
```

Forward-correct the existing Stage 1 commit; do not amend or rewrite it. Remove
the obsolete structural-layer terminology from the exact active canonical files
in the allowlist. Use role, cross-role challenge and authority-boundary wording. Do not
rewrite historical Feedback text; record the new Human decision and its
supersession boundary in a new Feedback entry.

The Operating Model is the single canonical owner of report identity and
admission. Restore the minimum complete supervised report contract:

```text
TASK_ENVELOPE = existing ten fields
REPORT_METADATA = WO_ID, RUN_OR_ATTEMPT_ID, REPORT_ID, SOURCE_TASK_ID,
                  DESTINATION_TASK_ID, OBJECT_ID, IN_REPLY_TO
EXPECTED_PENDING_TRANSITION = WO_ID, SOURCE_TASK_ID, DESTINATION_TASK_ID,
                              OBJECT_ID, RUN_OR_ATTEMPT_ID, IN_REPLY_TO
```

Required behavior:

- missing, truncated, stale, wrong-route, wrong-object or wrong-attempt reports
  are `HOLD` and cannot advance state;
- one consumed transition cannot advance or redispatch again;
- a repeated `REPORT_ID` or later report for a consumed binding is a duplicate;
- a correction proceeds only after Planner opens a new expected attempt and
  `IN_REPLY_TO` identifies the superseded report/finding;
- candidate drift requires a new `OBJECT_ID`; and
- this is supervised admission tracking, not exactly-once transport and not a
  runner, broker, database or scheduler.

The skill shall link to that canonical contract and carry only the workflow
summary needed to use it. It must not duplicate the entire Operating Model.

Correction 03 supersedes Correction 02 as the active forward correction and
includes its exact two-line lock-test change. It does not reopen Stage 0, amend
Stage 1, continue B09, modify product/runtime code, alter workflows, install a
plugin, create new scaffolding or authorize a remote action.

```text
CORRECTION_03_BASE_HEAD = a794a13ff5c229e436f21b47a2d52db05a671dd8
STAGE_2_CANDIDATE_BASE = 9557b63a977037c7de8356f66eadbd65e53fc394
PRODUCT_OR_RUNTIME_CODE_CHANGE = NO
GOVERNANCE_TEST_CHANGE = EXACT_TWO_LINE_LOCK_EXPECTATION_ONLY
```

### 10.5 Correction 04: entry sync and complete active-doc scope

The Builder's Correction 03 FULL read-in correctly returned `ENTRY_HOLD` before
writing because the uncommitted active `CURRENT.md` still binds Correction 02,
the former nine-path lease and Planner disposition. Planner now resolves that
handoff as stale relative to Human A0's approved Agent Loop execution and the
forward Work Order. This finding does not authorize bypassing the gate.

Before any other Correction 04 edit or test, the same Builder task may perform
one narrow pre-entry transition:

1. enter only as `BUILDER_SINGLE_WRITER; ENTRY_RECONCILIATION_ONLY`;
2. edit only `docs/agent_handoff/CURRENT.md`;
3. bind the latest Work Order commit and SHA supplied by Planner, the fourteen-
   path scope, `CORRECTION_04_ENTRY_SYNC_AND_FORWARD_STAGE_2`, the local-only
   boundary, `NO_PRODUCT_OR_RUNTIME_CODE_CHANGE`, the pending exact governance-
   test correction and the exact next action;
4. preserve Stage 0/1 evidence, Stage 2 candidate evidence, B09 parked state,
   scratch accounting and all unknown/untracked `KEEP` dispositions;
5. create one local semantic commit containing exactly `CURRENT.md`; and
6. rerun the canonical Role Entry Gate against that new local head.

The entry-sync record uses the verified Work Order head as
`HANDOFF_CAPTURE_BASE` and must not claim its own future commit. If the gate is
not `PASS`, stop without editing another file. If it passes, continue Correction
04 under the complete allowlist.

The read-in also verified that active
`docs/agent/QI_AGENT_WORKBENCH.md` still says the lock contains nine approved
artifacts. That sentence is active documentation, not historical evidence.
Correction 04 therefore adds this file to the allowlist and authorizes only the
minimum count correction from nine to ten. Update the existing
`PATH_REGISTRY.yaml` binding so its `scope_paths` exactly matches all fourteen
allowed paths. No other Workbench overview edit is authorized.

Correction 04 supersedes Correction 03 only for entry reconciliation and the
newly discovered active-document scope omission. All four-role, report-
admission, lock-test, finite-budget, B09 exclusion and remote-action boundaries
from Correction 03 remain mandatory.

```text
CORRECTION_04_BASE_HEAD = 58ecd5650e7ea534a1fa3bac3feafd3a33233e9b
CORRECTION_03_WO_SHA256 = 89BD44DB3B21348EDDDBD6D6818C79F04D9ED19F29680227C1859482FB977A78
ENTRY_SYNC_WRITE_SCOPE = docs/agent_handoff/CURRENT.md ONLY
POST_ENTRY_WRITE_SCOPE = EXACT_FOURTEEN_PATHS_IN_SECTION_10_1
```

### 10.6 Correction 05: independent-review HOLD forward correction

Correction 04 implementation commit
`c674f77b65cc38987f201229e0efe9e79d98acf5` and terminal evidence commit
`e9b6f62c30ee46054c0d617b639831baa8e9fba5` were inspected by the Tester and
independent Reviewer. The Tester classified scope, lock identity and the
targeted gate `PASS`, full machine evidence `FAIL`, and Windows path causation
`INCONCLUSIVE`. The independent Reviewer returned `HOLD` in report
`QI-AGENT-LOOP-C04-REVIEW-C674-01`.

The review found four in-scope defects:

1. active canonical authorities still preserve the competing three-pole layer;
2. report admission does not explicitly separate six binding comparisons from
   `REPORT_ID` freshness or define the initial `IN_REPLY_TO` value;
3. active `CURRENT.md` still lists the now-tracked Agent Loop skill as
   untracked; and
4. required plugin invocation evidence is not bound to a complete Builder
   report.

The existing 14-path allowlist already contains every required correction
target. No scope expansion, new Parent, product/runtime edit or workflow edit is
authorized.

#### 10.6.1 Four-role correction

Forward-correct these active authorities:

- `AGENTS.md`;
- `docs/agent/MASTER_ROADMAP.md`;
- `docs/agent/OPERATING_MODEL.md`;
- `docs/agent/ROLE_BOOT_AND_PROMPT_PROFILES.md`;
- `docs/agent/HUMAN_COLLABORATION.md`;
- `plugins/qi-agent-workbench/skills/qi-agent-loop/SKILL.md`; and
- the active block of `docs/agent_handoff/CURRENT.md`.

They shall use one structural model only:

```text
HUMAN_A0 = MATERIAL_AUTHORITY_ABOVE_THE_LOOP
OPERATIONAL_ROLES = PLANNER; BUILDER; TESTER_MACHINE_VERIFIER; REVIEWER
TESTER = EVIDENCE_ONLY_AUTHORITY
FOUR_ROLES != FOUR_EQUAL_AUTHORITIES
```

Remove active `three-pole`, `execution-control pole`, `not a fourth pole` and
equivalent second-layer claims. Express unequal authority directly per role.
Do not rewrite historical Feedback entries. Append one new Feedback decision
that records Human's four-role supersession of the old active structural effect.

#### 10.6.2 Report-admission correction

The Operating Model remains the single canonical owner. It shall state:

- all seven `REPORT_METADATA` fields are present;
- the six binding fields are compared with
  `EXPECTED_PENDING_TRANSITION`;
- `REPORT_ID` is non-empty and unseen for the pending transition;
- an initial attempt uses the canonical value `IN_REPLY_TO = NONE` in both the
  report and expected binding;
- a correction uses the exact superseded report or finding ID, never `NONE`;
- a correction still requires a Planner-opened new attempt;
- a consumed binding and duplicate `REPORT_ID` cannot advance or redispatch;
  and
- candidate drift requires a new `OBJECT_ID`.

The skill keeps a short workflow summary and names the canonical owner. Update
its lock digest after final content.

#### 10.6.3 Active inventory and plugin evidence

Refresh the active `CURRENT.md` inventory from live Git. The tracked
`plugins/qi-agent-workbench/skills/qi-agent-loop/SKILL.md` must not remain in
`UNTRACKED_KEEP` or be described as pending untracked staging. Do not inspect,
stage, delete or reclassify unrelated unknown artifacts.

Before the action each required skill governs, invoke/read it and report:

```text
PLUGIN
PURPOSE
INVOCATION
RESULT
FALLBACK
IMPACT_RADIUS
EDIT_RADIUS
TEST_RADIUS
LIMITATION
```

This applies to `ecc:living-docs-governance`,
`ecc:agent-architecture-audit`, `qi-context-boot` and `skill-creator`. If an
invocation cannot be proven, report `USAGE_NOT_PROVEN`; do not fabricate it.
The final Builder packet must include complete `REPORT_METADATA` and bind the
plugin evidence to the exact correction object.

#### 10.6.4 Verification correction

The prior full run used an absolute basetemp root of 118 characters; retained
children reached 254 characters before deeper managed writes. This supports
path-pressure risk but does not prove the cause of all 136 failures and eight
errors. The prior red run remains evidence and is not converted to PASS.

Register `.tmp/al05` in `PATH_REGISTRY.yaml` as an exact task-owned short-path
verification alias for this WP only. It is not a new general temp family and
grants no cleanup or reuse authority. Planner verified the alias does not exist
at Correction 05 design time. Before running, prove it remains absent, resolve
its absolute path inside the canonical repository, and create only the required
fresh parents.

Run once, in order:

```powershell
.venv\Scripts\python.exe -m pytest tests/agent_workbench/test_skills_lock.py `
  -p no:cacheprovider --basetemp=.tmp/al05/t/p

.venv\Scripts\python.exe -m pytest `
  -p no:cacheprovider --basetemp=.tmp/al05/f/p

$agentLoopTrackedPython = @(git ls-files '*.py')
.venv\Scripts\python.exe -m ruff check -- $agentLoopTrackedPython

git diff --check e9b6f62c30ee46054c0d617b639831baa8e9fba5..<CORRECTION_05_HEAD>
git diff --name-status e9b6f62c30ee46054c0d617b639831baa8e9fba5..<CORRECTION_05_HEAD>
```

Create `.tmp/al05/t` before targeted and `.tmp/al05/f` before full. Run full
only when targeted is green. A red targeted/full/Ruff result stops without
retry or content change.

The tracked-only Ruff invocation preserves all tracked Python coverage while
excluding unknown untracked `KEEP` artifacts that are outside this WP. Hosted
CI on a clean checkout remains required before integration.

Revised finite scratch limits, based on the retained measured run, are:

```text
CORRECTION_05_FULL_RUN_MAX_FILES = 20000
CORRECTION_05_FULL_RUN_MAX_DIRS = 15000
CORRECTION_05_FULL_RUN_MAX_BYTES = 1073741824
CUMULATIVE_RETAINED_MAX_FILES = 32000
CUMULATIVE_RETAINED_MAX_DIRS = 26000
CUMULATIVE_RETAINED_MAX_BYTES = 2147483648
MIN_D_FREE_BYTES = 10737418240
```

No retained artifact may be cleaned. Exceeding any revised ceiling is `HOLD`.

#### 10.6.5 Correction 05 budget and stop

```text
CORRECTION_05_BASE_HEAD = e9b6f62c30ee46054c0d617b639831baa8e9fba5
IMPLEMENTATION_AUDIT_TARGET = c674f77b65cc38987f201229e0efe9e79d98acf5
REVIEW_REPORT_ID = QI-AGENT-LOOP-C04-REVIEW-C674-01
REVIEW_VERDICT = HOLD
BUILDER_CORRECTION_COMMITS = ONE
TERMINAL_CURRENT_SYNC_COMMITS = ONE_IF_REQUIRED
TARGETED_RUNS = ONE
FULL_RUNS = ONE_ONLY_AFTER_TARGETED_PASS
RUFF_RUNS = ONE_TRACKED_ONLY
RETRY = NONE
```

After Builder return, Planner reviews the result, Tester verifies the exact new
object and a new independent Reviewer audits the final range. No prior Tester
classification or Reviewer verdict carries forward as acceptance.

### 10.7 Correction 06: host-suspension recovery and final completeness

Correction 05 content commit
`b0d905a7ecf09a2307ee8eb642e09021a042ddc0` and terminal HOLD commit
`e748646a9fe40f2eb2f43e58fffd7b42d47407c8` remain preserved evidence.
The Tester verified the exact content range and classified scope, report
admission, skill lock and inventory `PASS`. It identified one remaining active
completeness defect: the `MASTER_ROADMAP.md` engineering-toolbox row for AI
coding agents names Planner, Builder and Reviewer but omits Tester. The
Operating Model takeover list omission is not a functional bypass because its
general new-agent, agent-entry and material-reassignment triggers cover Tester.

The Correction 05 full sequential run is invalid verification evidence. Windows
System events prove that the host entered a low-power state during the run:

```text
FULL_RUN_START_LOCAL = 2026-09-25T16:59:35+07:00
HOST_SLEEP_UTC = 2026-09-25T10:12:39.568821000Z
HOST_WAKE_UTC = 2026-09-25T12:31:00.247312800Z
POWER_EVIDENCE = Power-Troubleshooter Event 1; Kernel-Power Events 42 and 107;
                 Kernel-General clock synchronization after resume
ROOT_CAUSE_CLASS = CI_INFRASTRUCTURE_DEFECT
MECHANISM = HOST_SUSPENSION_DURING_LOCAL_FULL_RUN
RESULT = HOLD_INCONCLUSIVE; NO_FINAL_PYTEST_SUMMARY
```

This evidence replaces the earlier `UNKNOWN` timeout classification. It does
not convert the run to PASS or FAIL, does not prove a product defect and does
not authorize a timeout increase. The global transient-infrastructure rule
permits at most one bounded rerun; Correction 06 grants exactly that rerun under
an execution-state guard and event-log continuity check.

#### 10.7.1 Exact write scope and commits

The Builder receives a narrow forward lease after one `CURRENT.md`-only entry
transition. The complete Correction 06 write scope is:

```text
docs/agent_handoff/CURRENT.md
docs/agent/MASTER_ROADMAP.md
docs/agent/KNOWN_FAILURE_MODES.md
docs/agent/PATH_REGISTRY.yaml
```

The entry transition may change only `CURRENT.md`, bind this Correction 06
object and return authority to the same Builder. After its Role Entry Gate
passes, one content commit shall:

1. change the Roadmap AI-coding-agents row to name Planner, Builder, Tester and
   Reviewer without adding a new structural model;
2. append `FM-050` to `KNOWN_FAILURE_MODES.md` using its existing schema, with
   `STATE = OPEN`, root cause `HOST_SUSPENSION_DURING_LOCAL_FULL_RUN`, the exact
   event evidence above, no product-defect inference, and prevention through a
   bounded execution-state guard plus post-run sleep-event check; and
3. register `.tmp/al06` in the existing WP binding as an exact one-run alias for
   `.tmp/al06/f/p`, with no general reuse, cleanup or other authority.

One terminal `CURRENT.md`-only commit is permitted if needed to record the
exact verification result and next authority. No other file may change.

#### 10.7.2 Plugin and boot evidence

Before the governed action, the Builder shall invoke/read and apply:

```text
qi-context-boot = REQUIRED_FOR_ENTRY
ecc:living-docs-governance = REQUIRED_BEFORE_DOCUMENT_ROUTING
ecc:agent-architecture-audit = REQUIRED_BEFORE_FINAL_AGENT_STACK_CLAIM
ecc:systematic-debugging = REQUIRED_FOR_TIMEOUT_INCIDENT_CLASSIFICATION
skill-creator = REQUIRED_FOR_POST_CREATION_SKILL_CONTRACT_VALIDATION
qi-agent-loop = REQUIRED_AS_OUTPUT_AND_POST_CREATION_VALIDATION
CodeGraph = NOT_APPLICABLE; NO_SOURCE_OR_PRODUCT_TEST_IMPACT_DISCOVERY
```

The final Builder report records, for every applicable item, `PLUGIN`,
`PURPOSE`, `INVOCATION`, `RESULT`, `FALLBACK`, `IMPACT_RADIUS`, `EDIT_RADIUS`,
`TEST_RADIUS` and `LIMITATION`. Reading an installed-file path is acceptable
invocation evidence when the skill is instruction-only; installation or a lock
entry alone is not. Validate the existing Agent Loop skill once with the
current `skill-creator` validator. Do not edit the skill or lock in Correction
06.

#### 10.7.3 One guarded verification run

Correction 05's targeted lock result remains valid for the unchanged skill and
lock object: `13 passed in 2.79s`. Do not rerun it. Before the new full run:

- prove at least 10 GiB free on drive D;
- prove `.tmp/al06` is absent, resolves inside the canonical repository, then
  create only `.tmp/al06/f`;
- record start time and the latest relevant Windows System power-event record;
- obtain a Windows `SetThreadExecutionState(ES_CONTINUOUS |
  ES_SYSTEM_REQUIRED)` guard in the same PowerShell process that waits for
  pytest; fail closed if the API returns zero; and
- do not alter global power-plan or lid/power-button settings.

Run the sequential suite once at the exact candidate head:

```powershell
.venv\Scripts\python.exe -m pytest `
  -p no:cacheprovider --basetemp=.tmp/al06/f/p
```

The supervising PowerShell process shall enforce a 25-minute wall-clock limit,
terminate only its exact owned pytest process tree when that limit expires, and
restore `SetThreadExecutionState(ES_CONTINUOUS)` in `finally`. After exit,
inspect Windows System events covering the run interval. Any sleep/resume event,
missing final pytest summary, non-zero exit, collection decrease/error, guard
failure or timeout is `HOLD`; no further rerun is permitted.

Only after a valid green full summary, run once:

```powershell
$agentLoopTrackedPython = @(git ls-files '*.py')
.venv\Scripts\python.exe -m ruff check -- $agentLoopTrackedPython
```

Then run `git diff --check` and `git diff --name-status` for the exact
Correction 06 range. No test, Ruff or command may inspect, stage, modify or
delete unknown untracked KEEP artifacts.

#### 10.7.4 Scratch and stop budget

The individual full-run ceilings remain 20,000 files, 15,000 directories and
1 GiB. Because all prior evidence must remain and cleanup is forbidden, the
cumulative retained ceilings for the additional one-run alias are:

```text
CORRECTION_06_CUMULATIVE_MAX_FILES = 48000
CORRECTION_06_CUMULATIVE_MAX_DIRECTORIES_ROOT_INCLUSIVE = 38000
CORRECTION_06_CUMULATIVE_MAX_BYTES = 3221225472
MIN_D_FREE_BYTES = 10737418240
```

Count descendant directories and run roots separately; do not mix conventions.
Reparse points are counted and reported without following their targets. Any
ceiling breach is `HOLD`; no cleanup is authorized.

```text
CORRECTION_06_BASE_HEAD = e748646a9fe40f2eb2f43e58fffd7b42d47407c8
ENTRY_CURRENT_COMMITS = ONE
CONTENT_CORRECTION_COMMITS = ONE
TERMINAL_CURRENT_COMMITS = ONE_IF_REQUIRED
SKILL_VALIDATION_RUNS = ONE
TARGETED_PYTEST_RUNS = ZERO
FULL_SEQUENTIAL_RUNS = ONE
RUFF_RUNS = ONE_ONLY_AFTER_VALID_FULL_PASS
RETRY = NONE
```

Stop on any role-entry conflict, path drift, plugin-evidence failure, guard
failure, power event, timeout, invalid/missing summary, red verification,
scratch breach, scope expansion or unexpected tracked deletion. Return the
complete result to Planner. Tester then verifies the exact new object and a new
independent Reviewer audits the stable final range before any remote action.

### 10.8 Correction 07: PR-readiness document freshness

The admitted full-branch Independent Reviewer report
`QI-AGENT-LOOP-FULL-BRANCH-REVIEW-774327D-01` returned `HOLD` on the exact
range `179c0712a14161ea25096e66a127f6022bf696fd..774327d7e809571b523c2a1d78f8f3381c0bebb4`
for two documentation-freshness findings only:

1. The active Work Order control and terminal state still described C05 and a
   fourteen-path aggregate after C06 completion and registration of the final
   fifteen-path aggregate.
2. `FM-050` said the C06 guarded rerun was pending after its accepted result.

The review passed the exact fifteen-path aggregate, B09 exclusion, four-role
model, report admission, skill/lock, registry and forward-history contracts.
Correction 07 forward-corrects only these three files:

```text
docs/superpowers/plans/WO-GOV-QI-AGENT-LOOP-CONSOLIDATION-01.md
docs/agent/KNOWN_FAILURE_MODES.md
docs/agent_handoff/CURRENT.md
```

This is a documentation-only correction. No behavioral test or product
verification is rerun. After the Builder commit, Tester verifies that exact
object, an independent Reviewer re-audits it, and Planner reconciles both
results before any remote action. Prior review evidence is not promoted to
acceptance of the corrected object.

## 11. Explicit exclusions

- `src/**`
- product tests, including `tests/test_operational_update.py`
- B09, Bridge A/B/C/D and WAL snapshot behavior
- PR #131 implementation or CI correction
- `.github/workflows/**`
- CI redesign or timeout expansion
- GUI, packaging, version and release work
- database or migration work
- runner, automation, hook, MCP or model-router implementation
- new dependency or plugin installation
- broad plugin inventory
- cleanup or deletion
- stash, reset, rebase, amend, force push, worktree or clone
- merge and release

## 12. Internal stages under one future execution lease

### Stage 0: governed entry reconciliation

The `origin/main` baseline contains a stale B09 active block in `CURRENT.md`.
The first Builder entry therefore has a known Work Order/CURRENT conflict and
cannot declare general implementation readiness. Human A0's approved Agent Loop
transition and this Planner correction authorize one narrow pre-entry action:

1. enter as `BUILDER_SINGLE_WRITER` with
   `ENTRY_RECONCILIATION_ONLY`, not general implementation authority;
2. update only `docs/agent_handoff/CURRENT.md` and
   `docs/agent/FEEDBACK_LEDGER.md`;
3. record the approved governance Parent/WP, canonical branch/base/WO object,
   B09 `PARKED_PRESERVED_LOCAL` disposition, exact role model, write allowlist,
   local-only execution boundary and next action;
4. retain the displaced B09 active state through a verifiable Git locator and
   preserve its technical HOLD without copying its history into the new active
   block;
5. commit exactly those two files as a local semantic entry-transition commit;
   and
6. re-run the canonical `ROLE_ENTRY_GATE` against the new local head before any
   Stage 1 or Stage 2 edit.

This Stage 0 exception exists only to repair the stale handoff that blocks the
normal entry gate. It does not allow the Builder to originate Human or Planner
decisions. If the post-commit gate still conflicts, return `ENTRY_HOLD` without
starting Stage 1.

### Stage 1: role, routing and integration contract

The Builder shall:

1. establish the four operational roles beneath Human A0 and Tester as the
   evidence-only role;
2. align all normal reporting to the Planner;
3. preserve the distinct meanings of Builder result, Tester evidence, Reviewer
   verdict, Planner reconciliation and Human decision;
4. distinguish a remote checkpoint from a Pull Request and CI evidence;
5. require every checkpoint without a PR to record its reason, integration
   target, PR-opening trigger, owner and exactly one next action; and
6. replace competing definitions with references to the canonical owner.

### Stage 2: skill, lock and active handoff

The Builder shall:

1. align `qi-agent-loop/SKILL.md` with Stage 1;
2. preserve progressive disclosure, positive triggers, negative triggers,
   functional checks, evidence fields and stop conditions;
3. regenerate/update the skill lock from actual governed content;
4. reduce `CURRENT.md` to one active Parent/WP state, one authority/writer state,
   one blocker set and one exactly-one-next-action; and
5. preserve removed active-history content through verified locators.

All three stages belong to one lease under Human execution approval. A stage
boundary does not require repeat approval when baseline, scope, writer and
authority remain unchanged.

## 13. Current-history retention contract

Every section removed from the active body of `CURRENT.md` must have a retention
record containing:

```text
HISTORICAL_SECTION
SOURCE_GIT_SHA
RETAINED_AUTHORITY_OR_REPORT
WHY_INFORMATION_IS_PRESERVED
WHY_SAFE_TO_REMOVE_FROM_ACTIVE_HANDOFF
```

Age, length or duplication alone is not deletion authority. Feedback decisions,
Delta items and audit evidence remain in their canonical owners.

## 14. Acceptance contract

The Work Order passes only when all statements below are true:

1. Human A0 is authority above the Agent Loop.
2. Planner, Builder, Tester/Machine Verifier and Reviewer are the four
   operational roles.
3. Tester/Machine Verifier is consistently evidence-only and has no acceptance,
   WP-closure, merge, release, scope or routing-policy authority.
4. No active canonical file keeps a second structural abstraction over the four roles;
   historical Feedback remains historical evidence only.
5. Builder, Tester and Reviewer normal reports return to the Planner.
6. Critical matters outside role authority route through Planner to Human.
7. Planner cannot edit Builder output or replace machine verification.
8. Planner cannot rewrite the Reviewer verdict.
9. Tester cannot change acceptance, close the WP, route work, merge or release.
10. Reviewer independently audits the exact Git object/range.
11. Checkpoint and Pull Request are explicitly distinct.
12. A checkpoint without a PR records reason, target, trigger, owner and next
    action.
13. CI green does not erase an independent blocker or Human decision boundary.
14. CI red does not silently expand this Work Order into B09 or workflow repair.
15. Each fact class has one canonical owner.
16. Dependent documents reference rather than duplicate the owner contract.
17. `CURRENT.md` contains one active actionable state without contradictory
    duplicate keys.
18. Removed active-history material has a verifiable retention locator.
19. `qi-agent-loop` does not originate authority.
20. Skill content and lock identity match.
21. The Work Order has a locator-only binding in `PATH_REGISTRY.yaml`.
22. No B09 source/test file is changed by the governance branch.
23. No CI workflow is changed.
24. No runner, hook, MCP, dependency or speculative scaffolding is added.
25. No untracked or unknown artifact is deleted or committed.
26. Targeted and full verification meet the contract below.
27. Hosted CI is evaluated on the exact governance PR head.
28. Reviewer audits the exact final head after any correction.
29. Human performs or explicitly authorizes merge.
30. Operating Model owns the seven-field `REPORT_METADATA` and six-field
    `EXPECTED_PENDING_TRANSITION` contracts.
31. Wrong object, attempt or route and stale, truncated or duplicate reports
    cannot advance or redispatch a consumed transition.
32. A correction requires a Planner-opened attempt with `IN_REPLY_TO`, and
    supervised admission never claims exactly-once transport.
33. `QI_AGENT_WORKBENCH.md` and `skills-lock.json` both identify exactly ten
    approved artifacts, while the lock test preserves exact set and hash checks.
34. The final registered fifteen-path aggregate exactly matches the governance
    branch diff and contains no unapproved path.
35. The pre-entry `CURRENT.md` sync is a one-file forward commit, preserves the
    previous evidence and produces a subsequent Role Entry Gate `PASS` before
    any other write or test.
36. No active authority retains a competing pole-based structural model over
    the four operational roles.
37. Report admission distinguishes six expected-binding comparisons from a
    present, non-empty, unseen `REPORT_ID` and defines `IN_REPLY_TO = NONE` for
    initial attempts.
38. Active `CURRENT.md` does not list a tracked governed artifact as untracked.
39. Required plugin evidence is bound to the exact Builder report or honestly
    classified `USAGE_NOT_PROVEN`.
40. Short-path full verification, tracked-only Ruff, revised finite scratch
    ceilings, Tester verification and new independent review satisfy their
    exact-object contracts before any remote action.

### Allowed claims

- the governance contract is internally aligned;
- role reporting is consistent within the changed authorities;
- the skill and lock are consistent;
- the enumerated tests/scenarios passed on the named object; and
- the exact governance head passed the reported gates.

### Forbidden claims

- the Agent Loop is fully autonomous;
- delivery is generally exactly-once;
- every model/runtime was smoke tested;
- B09 or Bridge A passed;
- PR #131 was corrected;
- a product release occurred.

## 15. Required scenario checks

The contract review must exercise or statically prove these scenarios:

1. Builder returns a normal result to Planner.
2. Tester returns a failing finding and Builder correction remains bounded by
   the existing lease.
3. Reviewer returns `HOLD` independently.
4. CI is red for an in-scope defect.
5. CI is green while a non-CI blocker remains.
6. A report names the wrong Git object, attempt or duplicate delivery.
7. A critical matter exceeds the active role's authority.
8. A remote checkpoint is created without a PR.
9. A skill instruction conflicts with repository authority.
10. A terminal sync records completion without claiming its own future commit.
11. Every active canonical file in the correction scope uses the four-role
    model and contains no obsolete structural-layer terminology.
12. Report admission rejects missing, truncated, stale, duplicate, wrong-route,
    wrong-object and wrong-attempt inputs without advancing or redispatching.
13. A correction report is admitted only for a Planner-opened attempt with an
    `IN_REPLY_TO` binding to the superseded report or finding.

## 16. CI fitness contract

```text
CI FITNESS CONTRACT
-------------------
CURRENT WP: WO-GOV-QI-AGENT-LOOP-CONSOLIDATION-01
CAPABILITY UNDER CHANGE: Governance documents, Agent Loop skill and skill lock
CRITICAL RISKS: Role conflict; hidden authority; stale CURRENT state; duplicated
  contract; checkpoint/PR confusion; B09 contamination; lock drift; history loss;
  claim overreach
BASELINE GATES TO KEEP: Existing required quality, supported-platform, collection,
  test and final-gate protections
WP-SPECIFIC GATES REQUIRED: Scope allowlist; role-matrix consistency; CURRENT
  active-state/retention audit; B09 exclusion; skill-lock verification; exact-head
  Reviewer audit
GATES NOT REQUIRED YET: Runtime agent loop; autonomous delivery; model smoke;
  B09/Bridge; packaging; release; live update
MAX JOB RUNTIME: skill-lock 2m; targeted Agent Workbench 5m; static inspections
  3m; Ruff 5m; full sequential pytest 25m; hosted quality 10m; hosted Ubuntu 20m;
  hosted Windows 45m; required final gate 3m
CI CHANGE REQUIRED BEFORE IMPLEMENTATION: NO
RATIONALE: The capability is governed documentation and an existing skill/lock.
  Existing CI policy remains; this WP adds exact scope and contract checks without
  modifying workflows.
```

An unrelated/pre-existing hosted failure is reported separately as:

```text
HOSTED_CI_STATE = HOLD
TRIAGE = PRE_EXISTING_TECH_DEBT | CI_INFRASTRUCTURE_DEFECT |
         DEPENDENCY_NETWORK_DEFECT | UNKNOWN
SCOPE_EXPANSION = NOT_AUTHORIZED
```

The governance Builder must not repair B09 or CI workflows under this Work
Order. One rerun is allowed only for verified transient CI infrastructure under
the existing CI contract.

## 17. Verification contract

### Entry

- verify canonical checkout, origin, branch and exact base;
- record `pytest --collect-only` count;
- prove the tracked tree is clean after B09 preservation;
- inventory untracked artifacts as `KEEP` without reading unrelated sensitive
  content; and
- record all authority and roadmap entry-gate fields.

### Targeted

```powershell
python -m pytest tests/agent_workbench/test_skills_lock.py
```

Run additional existing Agent Workbench tests only when directly affected by the
skill metadata or contract.

Static inspection must also prove:

- the active correction-scope authorities consistently name four operational
  roles and no secondary structural layer;
- Operating Model contains the exact `REPORT_METADATA` and
  `EXPECTED_PENDING_TRANSITION` fields and their fail-closed admission rules;
- the skill links to the Operating Model rather than duplicating the complete
  contract; and
- historical Feedback wording remains unchanged while a new Human decision
  records the supersession boundary.
- `QI_AGENT_WORKBENCH.md`, the lock manifest and the exact lock test consistently
  identify ten approved artifacts; and
- the Path Registry WP binding contains exactly the fifteen paths in the final
  registered aggregate.

### Full local

```powershell
python -m pytest
python -m ruff check .
git diff --check
git diff --name-status
```

Requirements:

- collection count does not unexpectedly decrease;
- zero collection errors;
- zero failing tests;
- diff remains inside the write allowlist;
- no B09 or workflow diff; and
- no unknown artifact is staged.

### Hosted and independent audit

- push and PR require their own Human permissions;
- hosted CI runs on the exact governance PR head;
- a feature-branch push without a PR is only a remote checkpoint;
- Tester evidence names the exact object and environment;
- Reviewer independently inspects the final exact range; and
- correction creates a forward commit and triggers exact-head re-verification.

## 18. Plugin applicability and evidence

| Plugin/skill | Applicability | Purpose |
|---|---|---|
| `ecc:living-docs-governance` | REQUIRED | One canonical owner and bounded document lifecycle |
| `ecc:agent-architecture-audit` | REQUIRED | Detect role, routing and persistence conflicts |
| `skill-creator` | REQUIRED when editing the skill | Frontmatter, triggers, progressive disclosure and checks |
| `qi-context-boot` | REQUIRED | Governed context read-in |
| `qi-agent-loop` | REQUIRED_AS_OUTPUT_AND_POST_CREATION_VALIDATION | The skill is absent on `origin/main`; create the minimum approved workflow, then invoke/validate it without claiming pre-creation use |
| CodeGraph | OPTIONAL | Use only for actual code/test impact discovery |
| Other plugins/MCPs | NOT_APPLICABLE | No inventory, install or fabricated evidence |

For every applicable invocation, record:

```text
PLUGIN
PURPOSE
INVOCATION
RESULT = USED_AND_SUCCEEDED | USED_WITH_FALLBACK | TOOL_UNAVAILABLE |
         NOT_APPLICABLE
FALLBACK
IMPACT_RADIUS
EDIT_RADIUS
TEST_RADIUS
LIMITATION
```

Availability, installation, configuration or a trusted hash does not prove use.

## 19. Models and role assignment

The intended execution preferences are:

```text
PLANNER_ARCHITECT = GPT 5.6 Sol High
BUILDER_SINGLE_WRITER = GPT 6 Lunar Max
MACHINE_VERIFIER_TESTER = GPT 6 Lunar Max
INDEPENDENT_REVIEWER_AUDITOR = GPT 5.6 Sol Medium
```

`ROLE > MODEL NAME`. Model identity does not grant entry, write, review,
business, merge or release authority.

## 20. Finite execution budget

- one Builder Single Writer;
- one entry-reconciliation stage and two implementation stages;
- at most two in-lease correction attempts;
- at most three implementation/transition commits and one terminal handoff sync
  commit;
- at most two new governed files: this Work Order and
  `plugins/qi-agent-workbench/skills/qi-agent-loop/SKILL.md`;
- no new skill reference/eval/scaffolding files; reuse existing tests and lock
  machinery;
- two targeted verification attempts and one full local run unless root-cause
  evidence requires a bounded repeat;
- Correction 04 permits one additional exact targeted lock-test run after the
  two-line expectation update, followed by the one full sequential run only if
  targeted verification is green;
- measured scratch limits are 256 files/128 directories/16 MiB per targeted
  run root; the separate proposed finite full-WP ceiling is 10,000 files/5,000
  directories/1 GiB, while preserving at least 10 GiB free on drive D;
- no cleanup;
- no scope expansion by implication; and
- stop when the correction budget is exhausted.

Correction 05 supersedes the remaining execution budget above after the
independent-review HOLD. Its exact budget is section 10.6.5; prior runs and
commits remain historical evidence and are not reset.

## 21. Proposed integration lifecycle

```text
HUMAN APPROVES DESIGN
  -> HUMAN SEPARATELY AUTHORIZES B09 LOCAL PRESERVATION
  -> B09 OWNER PRESERVES EXACT TWO FILES
  -> PLANNER VERIFIES CLEAN TRACKED ENTRY
  -> HUMAN AUTHORIZES GOVERNANCE BRANCH
  -> PLANNER RECORDS FINAL WO/LEASE OBJECT
  -> HUMAN AUTHORIZES BUILDER EXECUTION
  -> BUILDER COMMITS ONE-FILE CORRECTION 04 ENTRY SYNC
  -> BUILDER RE-RUNS ROLE ENTRY GATE
  -> BUILDER EXECUTES FORWARD CORRECTION 04 AND COMPLETES STAGE 2 ONLY ON PASS
  -> TESTER VERIFIES CORRECTION 04 EVIDENCE
  -> REVIEWER RETURNS CORRECTION 04 HOLD
  -> PLANNER ISSUES BOUNDED CORRECTION 05
  -> BUILDER EXECUTES ONE FORWARD CORRECTION AND SHORT-PATH VERIFICATION
  -> TESTER VERIFIES CORRECTION 05 EXACT OBJECT
  -> NEW INDEPENDENT REVIEWER AUDITS CORRECTION 05 EXACT RANGE
  -> PLANNER BUILDER-RESULT REVIEW
  -> TESTER MACHINE EVIDENCE
  -> PLANNER EVIDENCE REVIEW
  -> REVIEWER EXACT-OBJECT AUDIT
  -> PLANNER RECONCILIATION
  -> HUMAN AUTHORIZES PUSH
  -> REMOTE CHECKPOINT
  -> HUMAN AUTHORIZES DRAFT PR
  -> HOSTED CI AND BOUNDED FORWARD CORRECTION
  -> TESTER AND REVIEWER VERIFY FINAL HEAD
  -> PLANNER REPORTS TO HUMAN
  -> HUMAN MERGES MANUALLY
  -> POST-MERGE VERIFICATION AND SPINE RECONCILIATION
```

No step implies authority for the next material or remote step.

## 22. Stop conditions

Stop and report to Planner when any of these occurs:

- canonical checkout, origin, base or branch does not match;
- B09 tracked changes are not preserved exactly;
- branch transition would require stash, reset, cleanup, worktree or clone;
- an edit outside the allowlist is necessary;
- a role, authority or Human decision conflicts with this Work Order;
- a CI workflow change appears necessary;
- a `CURRENT.md` history section lacks a verifiable retention locator;
- a regression is outside governance scope;
- a required plugin is unavailable and the documented fallback is insufficient;
- the correction or runtime budget is exhausted;
- a secret or sensitive artifact would be exposed;
- B09 source/test or operational data would be touched; or
- an action lacks its separate Human permission.

## 23. Spine contract

```text
SPINE_IMPACT = GOVERNANCE | ROADMAP | CURRENT | FEEDBACK
SPINE_TARGET_FILES =
  AGENTS.md
  docs/agent/MASTER_ROADMAP.md
  docs/agent/OPERATING_MODEL.md
  docs/agent/ROLE_BOOT_AND_PROMPT_PROFILES.md
  docs/agent/LOCAL_STAGED_INTEGRATION.md
  docs/agent/HUMAN_COLLABORATION.md
  docs/agent/QI_AGENT_WORKBENCH.md
  docs/agent/FEEDBACK_LEDGER.md
  docs/agent/PATH_REGISTRY.yaml
  docs/agent_handoff/CURRENT.md
SPINE_SYNC_STATE = HOLD_UNTIL_IMPLEMENTED_REVIEWED_AND_RECONCILED
PROJECT_MEMORY_PROMOTION = NOT_BEFORE_MERGE
```

Every listed target is modified only when the Correction 04 trigger applies.
Material conflict outside the explicit four-role/report-admission correction
returns to Planner/Human rather than being silently resolved by the Builder.

## 24. Separate Human A0 decisions still required

### Decision A: B09 preservation — APPROVED AND COMPLETED LOCALLY

Authorize the B09 owner to create one local commit containing exactly the two
identified B09 tracked files, without push or CI.

### Decision B: governance branch — APPROVED AND COMPLETED LOCALLY

After clean entry is verified, authorize creation of
`codex/agent-loop-consolidation-01` from exact `origin/main`.

### Decision C: Builder execution lease — APPROVED FOR LOCAL EXECUTION

Authorize the named Builder Single Writer to execute this Work Order's exact
allowlist, stages, commands and bounded local commits.

### Decision C2: Correction 03 — HUMAN DIRECTED

Human A0 directed Planner to reconcile the four-role model, restore complete
report admission protection, include the exact lock-test correction and issue a
forward Work Order to Builder. This local correction expands the allowlist only
to the thirteen paths in section 10.1 and retains every remote/Human boundary.

### Decision C3: Correction 04 — PLANNER RECONCILED UNDER APPROVED LEASE

Builder's read-in proved that active `CURRENT.md` still bound Correction 02 and
that `QI_AGENT_WORKBENCH.md` retained an active nine-artifact count. Planner
reconciled the first as an entry-sync transition and the second as the minimum
active-document scope completion needed to satisfy Human's approved Agent Loop
objective. Correction 04 adds only `QI_AGENT_WORKBENCH.md`, updates the locator
to the same fourteen-path set, and preserves every remote/Human boundary.

### Decision C4: Correction 05 — PLANNER POST-REVIEW RECONCILIATION

Tester evidence and independent Reviewer report
`QI-AGENT-LOOP-C04-REVIEW-C674-01` confirm that Correction 04 stayed inside
scope and passed its targeted lock gate, but retained the forbidden competing
structural layer, left report-admission ambiguity and produced red full/Ruff
evidence. Planner accepts the Reviewer `HOLD` and issues the minimum forward
correction inside the existing fourteen-path scope. This does not rewrite the
verdict or convert prior red evidence to PASS.

### Decision D: push

Authorize push only after local evidence, Planner result review and independent
audit satisfy the approved checkpoint contract.

### Decision E: Draft Pull Request

Authorize Draft PR creation for the exact reviewed governance head. This does
not authorize merge.

### Decision F: merge

Human decides and performs or explicitly authorizes merge only after required
hosted CI, final exact-head review and Planner reconciliation.

## 25. Current terminal state

```text
DESIGN = HUMAN_APPROVED
WO_FILE = CORRECTION_07_PR_READINESS_DOC_FRESHNESS; BUILDER_RESULT_PENDING_TESTER_AND_REVIEWER
ACTIVE_PARENT_WP = GOVERNANCE_AGENT_LOOP_CONSOLIDATION
ACTIVE_MICRO_WP = CORRECTION_07_PR_READINESS_DOC_FRESHNESS
APPROVAL_SCOPE = FIFTEEN_PATH_AGGREGATE_AGENT_LOOP; THREE_PATH_CORRECTION_07
B09_PRESERVATION = COMPLETE_LOCAL_ONLY; 9bc64942f35c41d002ef80a74c7a02851422b0e8
GOVERNANCE_BRANCH = CREATED_FROM_EXACT_ORIGIN_MAIN; 179c0712a14161ea25096e66a127f6022bf696fd
C06_GUARDED_VERIFICATION = COMPLETED_WITH_LIMITATIONS; 1623_COLLECTED; 1621_PASSED; 2_SKIPPED; 0_COLLECTION_ERRORS; EXIT_0; NO_SLEEP_RESUME; TIMEOUT_NONE
C06_RECOVERY_AND_EXACT_HEAD_REVIEW = COMPLETE; C06_REVIEW_PASS_WITH_LIMITATIONS; HEAD_774327D
FULL_BRANCH_REVIEW = HOLD; QI-AGENT-LOOP-FULL-BRANCH-REVIEW-774327D-01
FULL_BRANCH_REVIEW_RANGE = 179c0712a14161ea25096e66a127f6022bf696fd..774327d7e809571b523c2a1d78f8f3381c0bebb4
FULL_BRANCH_REVIEW_FINDINGS = TWO_DOCUMENT_FRESHNESS_FINDINGS_ONLY; WORK_ORDER_C05_14_PATH_STATE; FM050_RERUN_PENDING_STATE
FINAL_REGISTERED_AGGREGATE = EXACTLY_15_PATHS; B09_EXCLUDED
C07_BUILDER_CORRECTION = THREE_DOCUMENTS_COMPLETE; PENDING_TESTER_AND_INDEPENDENT_REAUDIT
C07_WRITE_SCOPE = docs/superpowers/plans/WO-GOV-QI-AGENT-LOOP-CONSOLIDATION-01.md; docs/agent/KNOWN_FAILURE_MODES.md; docs/agent_handoff/CURRENT.md
BEHAVIORAL_RERUN = NONE; DOCUMENTATION_ONLY
REMOTE_CHECKPOINT = NOT_PUSHED; NOT_AUTHORIZED
PUSH = NOT_AUTHORIZED
PULL_REQUEST = NOT_AUTHORIZED
HOSTED_CI = NOT_RUN; NO_PR
MERGE = NOT_AUTHORIZED
RELEASE = NOT_AUTHORIZED
EXACTLY_ONE_NEXT_ACTION = TESTER_VERIFIES_EXACT_C07_COMMIT_AND_RETURNS_TO_PLANNER
NEXT_AUTHORITY = TESTER_MACHINE_VERIFIER
```
