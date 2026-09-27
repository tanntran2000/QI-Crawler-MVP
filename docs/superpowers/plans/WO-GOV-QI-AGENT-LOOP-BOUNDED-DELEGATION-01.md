# WO-GOV-QI-AGENT-LOOP-BOUNDED-DELEGATION-01

**Type:** SUCCESSOR_GOVERNANCE_WORK_PACKAGE
**Status:** Stage 0 complete; Stage 1 candidate/C02 returned and Planner-reviewed; Stage 2 Tester static/scenario verification pending
**Date:** 2026-09-26
**Release impact:** NONE

## Objective and authority

Close only the confirmed gaps in the existing four-role Agent Loop: bounded helper delegation as supporting evidence, report provenance, finite non-resetting correction accounting, explicit stop states, a three-dimensional Reviewer finding shape, static and scenario verification, and one prompt-governed helper pilot. Do not build a runner, framework, new role, sandbox, or auto-merge system.

Human A0 directly authorizes Stage 0 reconciliation, registration, the four exact Stage 0 writes, and one local semantic commit. The current Builder is the Single Writer. Stage 0 has no Stage 1, test, push, PR, merge, release, cleanup, B09, operational-data, or other-file authority. After reviewing the Stage 0 commit, the Planner may issue Stage 1 to the same Builder under the unchanged canonical checkout. Later stages remain conditional on their stated gates and Planner transition.

```text
CANONICAL_CHECKOUT_EXPECTED = D:\QI Technology\QI Crawler\egp-crawler-python
EXPECTED_ORIGIN_REPOSITORY = https://github.com/tanntran2000/QI-Crawler-MVP.git
STAGE_0_BASE = 3ba8403f707de9710aff6b08d9df82c0d0a424c4
STAGE_0_BRANCH = codex/agent-loop-bounded-delegation-01
PR131 = MERGED; head ea5d84a07a34794b91fa4b42f433f3b88555264e; merge 3ba8403f707de9710aff6b08d9df82c0d0a424c4; required CI and CodeQL PASS
PR132 = MERGED; merge 360da6c88304e02f455b9880598e815b7613a525
```

## Required read-in and owners

Before each governed transition, read the applicable current authorities. Full entry read-in for this successor: `AGENTS.md`; `docs/agent/MASTER_ROADMAP.md` and `MASTER_ROADMAP_DELTA.md`; `OPERATING_MODEL.md`; `ROLE_BOOT_AND_PROMPT_PROFILES.md`; `LOCAL_STAGED_INTEGRATION.md`; `PATH_REGISTRY_CONTRACT.md`; `CI_CONTRACT.md`; `CURRENT.md`; relevant `FEEDBACK_LEDGER.md` entries; the existing Agent Loop consolidation Work Order; and the current Agent Loop and Task Envelope skill/template. Resolve live Git/GitHub state again at remote transitions.

Ownership stays with the existing authorities:

- `OPERATING_MODEL.md`: roles, report admission, delegation, correction accounting.
- `ROLE_BOOT_AND_PROMPT_PROFILES.md`: entry/read-in and prompt quality.
- `LOCAL_STAGED_INTEGRATION.md`: commits, candidate/checkpoint, PR, CI, merge lifecycle.
- `CI_CONTRACT.md`: CI contract; preserve baseline jobs.
- `qi-agent-loop`: concise workflow guide; this Work Order is the exact lease; `CURRENT.md` is active state.

The Task Envelope remains its exact ten fields: `MISSION`, `ASSIGNED_ROLE`, `BASELINE`, `SCOPE`, `EXCLUSIONS`, `INVARIANTS`, `ACCEPTANCE`, `REQUIRED_SKILLS_TOOLS`, `VERIFICATION`, `NEXT_AUTHORITY`. A helper brief is a task message derived from authority, not a new template, file, or canonical role assignment.

## Architecture layer contract

```text
ROADMAP_BASELINE = VERIFIED; MASTER_ROADMAP_AND_DELTA_READ
PRODUCT_FRONTIER = UNIFIED_TENDER_WAREHOUSE_PARTIAL; UNCHANGED
ROADMAP_NODE = ENGINEERING_TOOLBOX / PLUGINS; SUPPORTING_GOVERNANCE_ONLY
ARCHITECTURE_LAYER = ENGINEERING_TOOLS_SUPPORTING_ONLY
PRODUCT_LAYERS = NO_CHANGE; NO_PRODUCT_CAPABILITY_OR_MATURITY_CLAIM
BOUNDARY = Preserve the four distinct authorities, single Writer, independent Reviewer, Planner reconciliation, and Human merge/release authority.
```

This governance Work Order does not modify the product architecture, storage/data paths, crawler runtime, or B09 maturity.

## Contract decisions

### Helper and provenance boundary

- A helper is not a fifth role. Its only admissible result is `HELPER_RESULT=SUPPORTING_EVIDENCE_ONLY`.
- Helper output cannot advance a WP, consume a transition, open a correction, create a verdict, or grant authority. The owning role verifies evidence before citing it and remains accountable for its report.
- Approved native helper dispatch may deliver only the exact allowlisted tracked content as bounded context under the active lease; it grants no wider access. Helper-initiated network, connector, external-tool or other external transmission, plus sensitive, untracked or operational content, is forbidden unless explicitly authorized.
- A bounded helper is not canonical role/agent entry; it receives only the exact brief/read allowlist and cannot declare `READY`, `PROMPT_READY`, `START_IMPLEMENTATION`, or `START_AUDIT`.
- Sub-agent or tool identity alone grants no authority, and helper output cannot stand in for Builder, Tester or Reviewer completion or `PASS`. Canonical role/takeover assignment requires explicit assignment, exact object/scope, applicable role/read-in/independence gates (including normal FULL/DELTA Role/Roadmap entry gates), and confirmed cessation/non-conflict with the previous owner.
- Label statements as `PROMPT_GOVERNED`, `OBSERVED`, or `TOOL_ENFORCED` accurately. Do not describe prompt constraints or observations as machine enforcement.

### Finite correction and stop accounting

- The post-review correction budget follows the same authority lease across revision, name, task, session, model, and takeover. A Planner-opened correction attempt is the accounting unit.
- Development RED/GREEN iterations and one verified transient CI rerun are separate budgets. A dispatch timeout or unknown result counts as used; do not silently resend. Rename/revision does not reset any budget. Exhaustion means `HOLD_AND_REPORT`.
- Stop states are `STOP_REQUESTED | STOP_CONFIRMED | STOP_STATUS_UNKNOWN`. Do not transfer the writer or start conflicting work unless stop is confirmed.
- `DELEGATION_PILOT_BUDGET=1`; `POST_REVIEW_CORRECTION_BUDGET=1` (base); `TRANSIENT_CI_RERUN_BUDGET=1`. Human A0 authorized one additional C02 correction extension after Planner consolidation. The finite ledger is:

  ```text
  BASE_POST_REVIEW_CORRECTION_BUDGET=1
  HUMAN_A0_C02_EXTENSION_BUDGET=1
  TOTAL_AUTHORIZED_CORRECTION_ATTEMPTS=2
  C01=AGENT_LOOP_BOUNDED_C01_WO_SCRATCH_BUDGET; DISPOSITION=CONSUMED_FOR_SCRATCH_BUDGET_CORRECTION; COMMIT=d2d253de8bcf5218cd985101bc8ee35c0ffaadd5
  C02=AGENT_LOOP_BOUNDED_C02_ADMISSION_PROVENANCE_BOUNDARIES; IN_REPLY_TO=PLANNER_STAGE1_REVIEW_ADMISSION_TEST_REGRESSION; DISPOSITION=CONSUMED_BY_THIS_DISPATCH
  TOTAL_CONSUMED=2
  REMAINING=0
  ```

- Allow one primary full verification and one affected full rerun only when an authorized correction changes the candidate and the active verification contract requires it.

### Reviewer finding and verification shape

- Keep separate `SEVERITY`, `INTEGRATION_DISPOSITION`, and `FIX_AUTHORITY`, plus location, impact, evidence, and resolution condition.
- Reviewer verdict remains `PASS | HOLD | FAIL`; the Planner routes any correction.
- Report these claims distinctly: `STATIC_CONTRACT_VERIFIED`, `SCENARIO_REPLAY_VERIFIED`, `DELEGATION_PILOT_VERIFIED`, `AUTONOMOUS_ENFORCEMENT_NOT_PROVEN`. Static tests prove text contracts only, not runtime enforcement.

## Scope and exclusions

### Stage 0 exact write scope

1. `docs/superpowers/plans/WO-GOV-QI-AGENT-LOOP-BOUNDED-DELEGATION-01.md`
2. `docs/agent/PATH_REGISTRY.yaml`
3. `docs/agent/FEEDBACK_LEDGER.md`
4. `docs/agent_handoff/CURRENT.md`

Stage 0 acceptance: the four files reconcile to the verified live facts and decisions; the new locator is locator-only; the YAML parses; CURRENT active keys are unique; diff checks pass; exactly these four paths change; one semantic local commit is created with message `docs(agent-loop): open bounded delegation successor`. No tests or Ruff at Stage 0.

### Conditional Stage 1 candidate minimum

After Planner review and a Stage 1 lease, the candidate minimum is `docs/agent/OPERATING_MODEL.md`, `plugins/qi-agent-workbench/skills/qi-agent-loop/SKILL.md`, `plugins/qi-agent-workbench/skills-lock.json`, and `tests/agent_workbench/test_execution_skills_contract.py`. Other files need a concrete mismatch and Planner scope decision. Do not change the Task Envelope skill or template unless a proven contradiction requires a new decision.

### Exclusions throughout this Work Order

B09 implementation; operational data; cleanup; Crawler runtime/source/tests except the explicitly listed later Agent Workbench contract test; workflow CI changes; runner/broker/scheduler/dashboard; a new role; sandbox framework; auto-merge; release; LEAN/STANDARD/CRITICAL profiles; long-term metrics implementation. Unknown or untracked artifacts are KEEP; do not inspect their contents or stage them.

## Stages and acceptance

0. **Reconcile and register:** complete. Stage 0 was committed at `e47e531a458d7f69b35c12b9af21307ce967871b`.
1. **Minimal contract correction:** candidate returned at `f6519cfeb544a642f5506e305a852e7190bc1201`; Planner builder-result review is `PASS` for transition. This is not a Tester or Reviewer result.
2. **Static/scenario verification and one helper pilot:** Tester static/scenario verification of the exact candidate is pending. The helper pilot budget is one and the pilot has not started. The approved native dispatch may deliver only the exact tracked-file allowlist as bounded context under the active lease and grants no wider access. The helper may not initiate network, connector, external-tool, or other external transmission. No helper writes, tests, imports, database or operational-data access, untracked-content access, or child delegation; sensitive, untracked, and operational content is excluded from this pilot. Required output headings: `OBSERVED`, `INFERENCE`, `OPTION`, `EVIDENCE_LOCATORS`, `LIMITATIONS`. The owner independently verifies every cited item. No autonomous enforcement claim.
3. **Integration:** local verification, normal push of the approved feature branch, and create/update one PR only after the relevant local gates; exact-head CI and independent exact-head review; Planner reconciliation; Human manual merge; post-merge verification. Merge and release remain Human-only. Stage 0 grants none of these remote actions.

## CI fitness and plugin applicability

**CI FITNESS CONTRACT**

```text
CURRENT WP: Governance-only Agent Loop contract correction
CAPABILITY UNDER CHANGE: Role/report/delegation/correction/stop/finding text contracts and static contract tests
CRITICAL RISKS: Authority confusion, false enforcement claims, resettable budgets, unverified helper evidence, scope drift
BASELINE GATES TO KEEP: Existing required CI, CodeQL, full pytest, Ruff, collection integrity, diff/scope checks
WP-SPECIFIC GATES REQUIRED: Targeted Agent Workbench and lock checks; collection accounting; full pytest; Ruff; diff/scope checks
GATES NOT REQUIRED YET: Runtime enforcement, workflow changes, operational/B09 tests
MAX JOB RUNTIME: Existing finite per-job limits in CI_CONTRACT.md; do not raise them
CI CHANGE REQUIRED BEFORE IMPLEMENTATION: NO
RATIONALE: Governance-only; preserve all baseline jobs and add only targeted contract verification.
```

Plugin applicability and evidence use the repository fields (`PLUGIN`, `PURPOSE`, `INVOCATION`, `RESULT`, `FALLBACK`, `IMPACT_RADIUS`, `EDIT_RADIUS`, `TEST_RADIUS`, limitation).

| Plugin | Applicability and evidence |
| --- | --- |
| `ecc:living-docs-governance` | Stage 0 REQUIRED; invoked before document writes to preserve one owner per fact and the active/history lifecycle; `USED_AND_SUCCEEDED`; no fallback; impact/edit radius is the four Stage 0 paths; test radius is document/YAML/key/diff validation. |
| `qi-context-boot` | REQUIRED when available; Stage 0 availability check found it unavailable (`TOOL_UNAVAILABLE`); fallback was the explicit full read sequence above. |
| CodeGraph | Stage 0 `NOT_APPLICABLE` because this stage is docs-only. Stage 1 impact discovery is REQUIRED before any test-file edit; use the repo shell or MCP fallback and record the result. |
| `skill-creator` | REQUIRED if Stage 1 edits `qi-agent-loop/SKILL.md`. |
| `ecc:python-testing` | REQUIRED if Stage 1 edits the Agent Workbench test; tests prove text contracts only. |
| `ecc:verification-before-completion` | REQUIRED before a later stage reports PASS/DONE, if available; otherwise document availability and use only a sufficient approved fallback. |

Unavailable tools and non-applicable tools must be reported accurately; neither permits bypassing an applicable contract.

## Artifact lifecycle, stop conditions, and evidence

Use only registered path families. The WP binding is a locator and grants no write scope. Stage 0 creates one Work Order and updates three existing governance files; it creates no scratch evidence. For later authorized verification, use `PATH.DEV.TEST_TEMP` for task-owned execution scratch and `PATH.EVIDENCE.WP_RUN` for retained evidence. Execution scratch remains KEEP because cleanup is unauthorized. Apply these separate scratch ceilings: `TARGETED_RUN_ROOT_MAX_FILES=512; MAX_DIRS=256; MAX_BYTES=67,108,864`; `FULL_RUN_ROOT_MAX_FILES=48,000; MAX_DIRS=32,000; MAX_BYTES=3,221,225,472`; `CUMULATIVE_WP_SCRATCH_MAX_FILES=50,000; MAX_DIRS=33,000; MAX_BYTES=3,489,660,928`. Require `MIN_D_FREE_BYTES=10,737,418,240` before a new run. Retained evidence is capped at `RETAINED_EVIDENCE_MAX_FILES=26; MAX_BYTES=35,651,584`; this excludes task-owned pytest execution scratch, which is governed by the separate scratch ceilings and remains KEEP. The single pilot report and final evidence index are each capped at one file / 1 MiB. Exceeding an applicable ceiling or reserve means HOLD; do not prune or delete. This forward correction records self-detected post-freeze Work Order omission `CORRECTION_ATTEMPT_ID=AGENT_LOOP_BOUNDED_C01_WO_SCRATCH_BUDGET; IN_REPLY_TO=BUILDER_SELF_FINDING_STAGE1_CAP_NOT_RECORDED; CORRECTION_BUDGET_CONSUMED=1; CORRECTION_BUDGET_REMAINING=0`.

Stop and report to the Planner if checkout/origin/base/branch changes; live main conflicts; tracked changes, an owned writer/process, or branch-transition overwrite risk appears; authority, role, or scope conflicts; an out-of-scope edit or CI workflow change is needed; stop status is unknown; a finite budget is exhausted; an applicable required tool has no sufficient fallback; or any requested action crosses a Human-only boundary.

Return evidence with exact checkout identity, remote/PR facts, base and candidate heads, changed paths, commands/results, commit and tree state, untracked names only, limitations, and the applicable Spine state. Preserve evidence provenance; do not infer CI, review, merge, release, or enforcement state from a local document.

## Spine and next authority

```text
SPINE_IMPACT = CURRENT | GOVERNANCE
SPINE_TARGET_FILES = docs/agent_handoff/CURRENT.md; this successor Work Order
SPINE_SYNC_STATE = PASS for the pre-Tester transition captured at f6519cfeb544a642f5506e305a852e7190bc1201
EXACTLY_ONE_NEXT_ACTION = TESTER_MACHINE_VERIFIER_VERIFIES_EXACT_CANDIDATE_BEFORE_PILOT
NEXT_AUTHORITY = TESTER_MACHINE_VERIFIER
```
