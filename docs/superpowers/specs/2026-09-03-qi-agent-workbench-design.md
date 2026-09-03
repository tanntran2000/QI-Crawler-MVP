# QI Agent Workbench — Design Contract

## Status

```text
PARENT_WP = WP-GOV-QI-WORKBENCH-01
ROLE_OWNER = PLANNER_ARCHITECT
HUMAN_A0_APPROVAL = YES / 2026-09-03
BASELINE = f5803b86452804add6da691621a6007e0dd1ff4c
BRANCH = gov/qi-agent-workbench-01
VERSION_IMPACT = NONE
PRODUCT_BEHAVIOR_CHANGE = NO
AUTOMATION = OUT
MCP = OUT
EXTERNAL_CONNECTORS = OUT
AUTO_SPINE_WRITE = OUT
MERGE_RELEASE_AUTHORITY_CHANGE = NO
```

This Parent creates a small internal agent workbench for QI-Crawler. It packages repeatable read/routing/evidence behavior without becoming a second project authority, an autonomous orchestrator, or a product feature.

## 1. Objective

When an agent receives a task, it should be able to:

1. establish the governed project/role/context state before work;
2. load only the minimum relevant skills and references;
3. derive a compact task envelope from the canonical Work Order rather than duplicating project law in every prompt;
4. preserve exact scope/authority boundaries;
5. return structured, reviewable evidence and handoff state.

The Workbench reduces repeated prompt text and context drift. It does not automate task scheduling, agent dispatch, production mutation, Spine mutation, merge, or release.

## 2. Source ideas and QI adaptation

### 2.1 Dely ideas adopted selectively

Adopt concepts only:

- discriminating acceptance: every material requirement names an instrument and a plausible present-but-wrong counterexample;
- execution envelope: exact owned scope, protected dirty paths, base/branch, verification, and authority boundaries;
- worker outcomes distinguish `DONE`, `BLOCKED`, `NEEDS_REPLAN`, and process/runtime failure;
- handoff integrity uses a terminal sentinel `END OF HANDOFF`;
- Reviewer receives the contract, exact object, diff and evidence rather than Builder reasoning;
- at most one bounded in-contract remediation before `REPLAN_OR_SPLIT`.

Explicitly not adopted:

- Orca execution plane;
- Dely as project authority;
- automatic PR/release control;
- any runtime that replaces QI's Human/Planner/Builder/Reviewer governance.

### 2.2 Agent Skills Standard ideas adopted selectively

Adopt concepts only:

- hierarchical context/skill routing;
- small on-demand skills instead of giant repeated prompts;
- readiness before implementation;
- skill-content integrity lock/hash manifest;
- negative/eval fixtures that prove a skill rejects wrong routing or authority;
- reusable review/evidence workflows.

Explicitly not adopted:

- `ags sync` over QI's canonical `AGENTS.md`;
- importing the full external skill catalog;
- MCP runtime;
- enforcing hooks;
- external tasking connectors;
- external registry governance as QI authority.

## 3. Authority model

The Workbench is subordinate to the existing authority chain:

```text
HUMAN_A0
  ↓
AGENTS.md / OPERATING_MODEL / ROLE_BOOT_AND_PROMPT_PROFILES
  ↓
MEMORY_INDEX / MASTER_ROADMAP / MASTER_ROADMAP_DELTA / CURRENT / live Git
  ↓
QI Agent Workbench skills
  ↓
assigned agent execution
```

Hard invariants:

```text
WORKBENCH != AUTHORITY
SKILL != WORK_ORDER
SKILL != ROLE_ASSIGNMENT
ROUTER != SCOPE_AUTHORITY
CODEGRAPH_IMPACT != EDIT_SCOPE
SUPERPOWERS_WORKFLOW != PRODUCT_SCOPE
BOOT_READY != IMPLEMENTATION_AUTHORIZED
MACHINE_VERIFIED != HUMAN_APPROVED
```

No skill may grant authority that is absent from Human A0, an approved Work Order, or canonical governance.

## 4. QI Boot contract

`qi-context-boot` is read-only.

### Inputs

- canonical checkout expectation;
- expected repository identity;
- Human/Work Order/CURRENT role evidence;
- read-mode selector trigger;
- task intent when supplied.

### Behavior

1. resolve repository/checkout identity before interpreting branch/head;
2. execute the existing `FULL | DELTA | NO_RE_READ` policy from `MEMORY_INDEX.md`;
3. read/reconcile the canonical authorities required by that mode;
4. resolve current phase, Product Frontier, Roadmap node/layers and relevant Delta IDs;
5. resolve role using Human → approved Work Order → CURRENT evidence; never from model/tool name;
6. verify volatile Git/GitHub state when material;
7. evaluate Roadmap Entry Gate and ROLE_ENTRY_GATE;
8. return a boot report only.

### Output

```text
QI_BOOT_REPORT
ROLE =
ROLE_SOURCE =
READ_MODE =
CANONICAL_CHECKOUT =
REPOSITORY_IDENTITY =
LIVE_BRANCH =
LIVE_HEAD =
ORIGIN_MAIN =
CURRENT_PHASE =
PRODUCT_FRONTIER =
ROADMAP_NODE =
ARCHITECTURE_LAYERS =
RELEVANT_DELTA_IDS =
CURRENT_FRESHNESS =
SPINE_FRESHNESS =
ROADMAP_ENTRY_GATE =
ROLE_ENTRY_GATE =
WHAT_I_AM_ALLOWED_TO_DO =
WHAT_I_AM_NOT_ALLOWED_TO_DO =
READY_STATE = READY | ENTRY_HOLD
HOLD_REASON =
EXACTLY_ONE_NEXT_ACTION =
NEXT_AUTHORITY =
```

`NEEDS_REPLAN` is not a boot result. It belongs to execution lifecycle after a Work Order exists.

## 5. Context router

The router is a deterministic reference map first, not an LLM authority layer.

### Base context

Always resolve only what the read mode requires from:

- `MEMORY_INDEX.md`;
- `AGENTS.md`;
- `OPERATING_MODEL.md`;
- `ROLE_BOOT_AND_PROMPT_PROFILES.md`;
- `CURRENT.md`;
- Master Roadmap / Delta;
- live Git/GitHub when relevant.

### Role context

- Planner → Roadmap/Delta/Spine/current/live evidence and Human intent;
- Builder → approved Work Order, exact code/tests/contracts, relevant failure/lesson entries;
- Reviewer → approved Work Order/challenge, exact `BASE..HEAD`, tests/evidence and relevant Roadmap/Delta/Spine/failure context.

### Task context

Routing rules identify only candidate skills/references. They do not widen scope.

Initial task families:

- Python behavior change;
- bug/test failure;
- migration/schema;
- governance/docs;
- security-bounded work.

## 6. Compact Task Envelope

The canonical 18-field Action-First Work Order remains authority. The Workbench may derive this compact runtime view:

```text
TASK_ENVELOPE
MISSION
ASSIGNED_ROLE
BASELINE
SCOPE
EXCLUSIONS
INVARIANTS
ACCEPTANCE
REQUIRED_SKILLS_TOOLS
VERIFICATION
NEXT_AUTHORITY
```

Rules:

- it must be lossless for the execution-critical information it represents;
- it never replaces the canonical Work Order until a later Human-approved governance promotion;
- omitted information remains reachable by reference to the canonical Work Order/governance;
- a material mismatch between Envelope and Work Order is `ENTRY_HOLD`.

## 7. Initial skill package

Target structure:

```text
plugins/qi-agent-workbench/
├─ .codex-plugin/plugin.json
├─ skills/
│  ├─ qi-context-boot/
│  │  └─ SKILL.md
│  ├─ qi-task-envelope/
│  │  └─ SKILL.md
│  ├─ qi-impact-map/
│  │  └─ SKILL.md
│  ├─ qi-python-change/
│  │  └─ SKILL.md
│  ├─ qi-evidence-check/
│  │  └─ SKILL.md
│  └─ qi-review-handoff/
│     └─ SKILL.md
├─ references/
│  ├─ context-map.md
│  ├─ task-envelope-template.md
│  └─ handoff-template.md
└─ skills-lock.json
```

This directory is tooling/governance support and must not be imported by `src/qi_crawler/`.

## 8. Skill responsibilities

### `qi-context-boot`

Read-only startup and gate report. It must never mutate source, Git state, CURRENT, Spine, or remote state.

### `qi-task-envelope`

Validate/derive the compact envelope from an approved canonical Work Order. It must hold on unresolved role, baseline, scope, authority or Work Order mismatch.

### `qi-impact-map`

Guide impact discovery using CodeGraph when available and governed manual fallback when unavailable. It must keep `impact radius`, `edit radius`, and `test radius` distinct.

### `qi-python-change`

Route approved Python behavior work through the existing Superpowers execution discipline: test-first/discriminating failure, minimal complete change, targeted verification, then required broader gates. It cannot brainstorm or redesign an already approved Work Order.

### `qi-evidence-check`

Classify evidence precisely: baseline/negative proof, targeted tests, full regression, Ruff/diff, local evidence, hosted CI, unverified claims and limitations.

### `qi-review-handoff`

Produce factual Builder/Reviewer handoff shape with exact Git object identity and terminal sentinel. It must not transfer Builder reasoning as Reviewer authority.

## 9. State model

Keep state families separate.

### Boot/entry

```text
READY | ENTRY_HOLD
```

### Builder execution

```text
DONE | BLOCKED | NEEDS_REPLAN | WORKER_FAILED
```

### Reviewer audit

Use existing QI Reviewer verdicts and governance. The Workbench does not invent merge authority.

## 10. Handoff integrity

Minimum runtime handoff shape:

```text
ROLE =
STATUS =
PARENT_WP =
MICRO_WP =
BASE_SHA =
HEAD_SHA =
CHANGED_PATHS =
CONTRACT_COVERAGE =
VERIFICATION =
DEVIATIONS =
UNRESOLVED_FINDINGS =
SPINE_IMPACT =
GIT_STATE =
EXACTLY_ONE_NEXT_ACTION =
NEXT_AUTHORITY =
END OF HANDOFF
```

If `END OF HANDOFF` is absent, the receiving role treats packet integrity as unknown and must not infer omitted terminal state.

## 11. Integrity manifest

`skills-lock.json` contains the approved content digest for every Workbench skill/reference included in the lock contract.

The implementation must provide a deterministic verifier that can detect:

- approved content unchanged;
- one modified skill;
- missing locked file;
- unexpected locked-path mismatch.

The lock does not make a skill authoritative; it only proves content identity against the approved manifest.

## 12. Discriminating acceptance

Every acceptance requirement must answer four questions:

| Requirement | Instrument | Present-but-wrong counterexample | Expected rejection |
| --- | --- | --- | --- |
| Boot reconciles live state | fixture/sandbox repo or deterministic test | CURRENT claims old head but Boot trusts it without checking live Git | `ENTRY_HOLD` or stale-state detection |
| Role is evidence-based | role fixture | model name `Codex`/`ChatGPT` silently determines role | reject / `ENTRY_HOLD` |
| Compact Envelope remains subordinate | contract fixture | Envelope widens scope beyond canonical Work Order | reject |
| Skill router is bounded | routing fixture | migration task loads only generic Python path and omits migration safety | reject |
| Handoff is complete | packet fixture | all tests pass but `HEAD_SHA` or sentinel is absent | reject incomplete handoff |
| Reviewer independence is preserved | review fixture | Reviewer is instructed to edit audited object | hold/refuse write |
| Integrity manifest detects drift | hash test | changed skill still passes verification | fail verification |
| Workbench is non-product | import/path check | `src/qi_crawler` imports plugin package or plugin changes runtime | reject |

A test that only proves a feature is absent before implementation is insufficient if it cannot reject a present-but-wrong implementation.

## 13. Protected dirty paths

Do not hard-code current local untracked files into this design.

At Builder entry:

```text
git status --short
→ capture pre-existing dirty/untracked paths
→ mark them PROTECTED_DIRTY_PATHS unless explicitly owned by Work Order
→ no stash/reset/clean/delete/absorb
```

If an owned path already contains protected Human changes, Builder holds for Planner/Human rather than mixing ownership.

## 14. Manual pilot

No scheduler/background trigger exists in this Parent.

Pilot fixtures:

1. approved Python behavior change;
2. migration/schema change;
3. docs-only governance change;
4. negative scope-escalation fixture;
5. Reviewer-edit request fixture;
6. stale-CURRENT/live-Git mismatch fixture;
7. wrong-role-by-model-name fixture.

The pilot passes only when the Workbench loads/references the expected bounded skill set and rejects authority/scope/context violations.

## 15. Parent decomposition

```text
Micro-A — Workbench foundation + read-only QI Boot
Micro-B — Context router + compact Task Envelope
Micro-C — Impact/Python/Evidence/Handoff skills
Micro-D — Integrity lock/verifier + negative fixtures
Micro-E — Manual pilot + governance reconciliation/closeout
```

Each Micro ends with local verification, semantic commit, Planner builder-result review, independent Reviewer audit, Spine check, then the next authorized slice under the Parent approval lease.

## 16. Out of scope

- Crawler source/product behavior;
- Warehouse/HSMT/SOP/GUI/API/database/migrations;
- autonomous agents;
- background jobs/scheduler/event bus;
- MCP server/client configuration;
- external connectors;
- `ags sync` or wholesale external skill import;
- automatic Spine mutation;
- automatic role assignment;
- automatic PR/merge/release;
- self-modifying governance;
- production decision authority.

## 17. Stop conditions

Stop and return to Planner/Human when:

- implementation requires modifying `src/qi_crawler`, migrations, product tests or product behavior;
- a skill would need to grant or infer authority;
- canonical Work Order and Task Envelope cannot reconcile;
- required context cannot be read safely;
- automation/MCP/external connector becomes necessary;
- protected dirty paths conflict with owned paths;
- Parent scope must change;
- governance authority conflict appears.

## 18. Parent exit criteria

`WP-GOV-QI-WORKBENCH-01` closes only when:

- QI Boot is read-only and discriminating stale/role/baseline failures;
- context router is bounded and token-economical;
- compact Envelope is proven subordinate to canonical Work Order;
- evidence/handoff contracts are deterministic and Reviewer-safe;
- skill integrity verification catches drift/missing files;
- all positive and negative pilot fixtures pass;
- no Crawler product/runtime behavior changed;
- no automation/MCP/external connector was introduced;
- independent integration review passes;
- required Spine reconciliation is complete;
- Human retains merge/release/material authority.
