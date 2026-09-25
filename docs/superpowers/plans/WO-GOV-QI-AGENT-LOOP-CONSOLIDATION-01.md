# WO-GOV-QI-AGENT-LOOP-CONSOLIDATION-01

## Control block

```text
WORK_ORDER_ID = WO-GOV-QI-AGENT-LOOP-CONSOLIDATION-01
TITLE = QI Agent Loop role, routing, handoff and skill consolidation
STATE = APPROVED_FOR_LOCAL_BUILDER_EXECUTION
APPROVAL_SCOPE = DESIGN_B09_PRESERVATION_GOVERNANCE_BRANCH_AND_LOCAL_EXECUTION
HUMAN_DESIGN_DECISION = APPROVED
HUMAN_DESIGN_DECISION_DATE = 2026-09-25
ACTIVE_PARENT_WP = GOVERNANCE_AGENT_LOOP_CONSOLIDATION
ACTIVE_MICRO_WP = NOT_STARTED
CURRENT_AUTHORITY = PLANNER_ARCHITECT
NEXT_AUTHORITY = BUILDER_SINGLE_WRITER
HANDOFF_READY = YES_FOR_BUILDER_ENTRY
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

### 3.1 Execution-control poles

The three execution-control poles under Human A0 are:

1. `PLANNER_ARCHITECT`
2. `BUILDER_SINGLE_WRITER`
3. `INDEPENDENT_REVIEWER_AUDITOR`

The Machine Verifier/Tester is evidence-only and is not a fourth authority
pole.

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
| Product strategy and layer classification | `docs/agent/MASTER_ROADMAP.md` | Read-only authority for this Work Order |
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
RELEASE_IMPACT = DOCS_SKILL_INTERNAL_ONLY
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

### 10.2 Read-only authorities and verification inputs

- `AGENTS.md`
- `docs/agent/MASTER_ROADMAP.md`
- `docs/agent/MASTER_ROADMAP_DELTA.md`
- `docs/agent/CI_CONTRACT.md`
- `docs/agent/PATH_REGISTRY_CONTRACT.md`
- `plugins/qi-agent-workbench/skills/qi-context-boot/SKILL.md`
- `tests/agent_workbench/test_skills_lock.py`
- directly relevant existing Agent Workbench tests

If meeting acceptance requires editing a read-only or unlisted file, the Builder
returns `SCOPE_EXPANSION_REQUIRED` and stops. The Work Order does not
automatically expand.

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

### Stage 1: role, routing and integration contract

The Builder shall:

1. establish the three execution-control poles and evidence-only Tester;
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

Both stages belong to one lease only after Human execution approval. A stage
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
2. Planner, Builder and Reviewer are the three execution-control poles.
3. Tester/Machine Verifier is consistently evidence-only.
4. No governed file presents Tester as a fourth authority pole.
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
| `qi-agent-loop` | REQUIRED | Workflow under change |
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
- two internal stages;
- at most two in-lease correction attempts;
- at most two implementation commits and one terminal handoff sync commit;
- at most one new governed file, this Work Order;
- two targeted verification attempts and one full local run unless root-cause
  evidence requires a bounded repeat;
- no cleanup;
- no scope expansion by implication; and
- stop when the correction budget is exhausted.

## 21. Proposed integration lifecycle

```text
HUMAN APPROVES DESIGN
  -> HUMAN SEPARATELY AUTHORIZES B09 LOCAL PRESERVATION
  -> B09 OWNER PRESERVES EXACT TWO FILES
  -> PLANNER VERIFIES CLEAN TRACKED ENTRY
  -> HUMAN AUTHORIZES GOVERNANCE BRANCH
  -> PLANNER RECORDS FINAL WO/LEASE OBJECT
  -> HUMAN AUTHORIZES BUILDER EXECUTION
  -> BUILDER EXECUTES STAGES 1 AND 2
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
SPINE_IMPACT = GOVERNANCE | CURRENT | FEEDBACK
SPINE_TARGET_FILES =
  docs/agent/OPERATING_MODEL.md
  docs/agent/ROLE_BOOT_AND_PROMPT_PROFILES.md
  docs/agent/LOCAL_STAGED_INTEGRATION.md
  docs/agent/FEEDBACK_LEDGER.md
  docs/agent/PATH_REGISTRY.yaml
  docs/agent_handoff/CURRENT.md
SPINE_SYNC_STATE = HOLD_UNTIL_IMPLEMENTED_REVIEWED_AND_RECONCILED
PROJECT_MEMORY_PROMOTION = NOT_BEFORE_MERGE
```

`AGENTS.md` and the Master Roadmap must be inspected at reconciliation but are
not automatically modified. Material conflict returns to Planner/Human rather
than being silently resolved by the Builder.

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
WO_FILE = READY_FOR_PLANNER_COMMIT
B09_PRESERVATION = COMPLETE_LOCAL_ONLY; 9bc64942f35c41d002ef80a74c7a02851422b0e8
GOVERNANCE_BRANCH = CREATED_FROM_EXACT_ORIGIN_MAIN; 179c0712a14161ea25096e66a127f6022bf696fd
BUILDER_EXECUTION = HUMAN_AUTHORIZED_LOCAL_ONLY
PUSH = NOT_AUTHORIZED
PULL_REQUEST = NOT_AUTHORIZED
MERGE = NOT_AUTHORIZED
EXACTLY_ONE_NEXT_ACTION = PLANNER_COMMITS_WO_THEN_ASSIGN_BUILDER_SINGLE_WRITER
NEXT_AUTHORITY = PLANNER_THEN_BUILDER_SINGLE_WRITER
```
