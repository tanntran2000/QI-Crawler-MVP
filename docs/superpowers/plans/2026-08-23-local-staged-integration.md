# Local Staged Integration Governance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `Local Staged Integration + Remote Checkpoint + Parent-WP CI` the documented operating contract for QI-Crawler development while preserving existing laws and release authority.

**Architecture:** Keep `AGENTS.md` constitutional and place detailed procedure in a dedicated operating contract. Reference that contract from the Operating Model and Human Collaboration docs, normalize the stale WP-MI-SRC-01 memory/handoff state, and record the temporary hosted-CI waiver without modifying the CI workflow itself.

**Tech Stack:** Markdown governance documents, Git/GitHub repository metadata.

**Spec:** `docs/superpowers/specs/2026-08-23-local-staged-integration-design.md`

## Global Constraints

- One canonical checkout; no worktrees, sibling clones, or WP folders.
- Governance/docs only: no production code, tests, migrations, CI workflow changes, version bump, build, tag, release, publish, or Team Bid Reference mutation.
- Existing LAW hierarchy and Human merge/release authority remain unchanged.
- Feature-branch remote checkpoints without a PR are backup points, not CI evidence.
- Hosted CI billing/spending-limit failure is `INFRASTRUCTURE_UNAVAILABLE`, never `CI PASS`.
- Official release remains blocked while `PENDING_RETRO_CI > 0`.

---

### Task 1: Establish the operating contract

**Files:**
- Create: `docs/agent/LOCAL_STAGED_INTEGRATION.md`

**Interfaces:**
- Consumes: constitutional laws in `AGENTS.md` and role definitions in `docs/agent/OPERATING_MODEL.md`.
- Produces: the canonical procedure for micro-WP review packets, remote checkpoints, parent integration, CI waiver, retro-CI, and release blocking.

- [ ] **Step 1: Create the contract from the approved design**

Write the approved authority model, parent flow, `LOCAL_REVIEW_PACKET`, audit outcomes, forward-correction rule, parent sizing heuristic, parent integration gate, hosted-CI waiver, retro-CI recovery, and release gate exactly enough to be executable by future agents.

- [ ] **Step 2: Check for contradictions with existing laws**

Read `AGENTS.md` and `docs/agent/OPERATING_MODEL.md`; verify that the contract does not make the Reviewer a runtime verifier, does not authorize multiple writers, and does not weaken Human authority.

- [ ] **Step 3: Commit**

Commit message:

```text
docs: add local staged integration contract
```

### Task 2: Connect the contract to repository governance

**Files:**
- Modify: `AGENTS.md`
- Modify: `docs/agent/OPERATING_MODEL.md`
- Modify: `docs/agent/HUMAN_COLLABORATION.md`

**Interfaces:**
- Consumes: `docs/agent/LOCAL_STAGED_INTEGRATION.md`.
- Produces: concise references and role/reporting rules without duplicating the full contract.

- [ ] **Step 1: Add a concise AGENTS.md reference**

Add a short Local Staged Integration governance section beneath the adaptive verification/CI governance area. Preserve all existing LAW text. State that detailed procedure lives in `docs/agent/LOCAL_STAGED_INTEGRATION.md`, that feature-branch checkpoint pushes are not CI evidence, and that CI waivers create retro-CI debt and block official release until cleared.

- [ ] **Step 2: Update the Operating Model**

Add the parent-WP/micro-WP execution sequence and clarify that local machine execution may temporarily supply machine-verifier evidence while hosted CI is unavailable, while Reviewer/Auditor authority remains independent.

- [ ] **Step 3: Update Human Collaboration**

Add the expected `LOCAL_REVIEW_PACKET` reporting behavior, concise PASS logs, relevant failure excerpts, and the rule that the Single Writer stops at `STOP_FOR_INDEPENDENT_LOCAL_AUDIT` before continuing.

- [ ] **Step 4: Commit**

Commit message:

```text
docs: wire staged integration into governance
```

### Task 3: Normalize merged source-routing truth and active handoff

**Files:**
- Modify: `docs/agent/PROJECT_MEMORY.md`
- Modify: `docs/agent_handoff/CURRENT.md`

**Interfaces:**
- Consumes: merged PR #44 at `fc4d68cbeb9e5f27a91039e264e3906d1ee8f1c7` and the new governance contract.
- Produces: main-truth memory and a current handoff that does not describe PR #44 as unmerged.

- [ ] **Step 1: Normalize MEM-006**

Change MEM-006 from branch-only/proposed to `ACTIVE`, record merge commit `fc4d68cbeb9e5f27a91039e264e3906d1ee8f1c7`, preserve the source-routing contract, and explicitly retain the limitation that full TBMT Bid Radar intake is not implemented.

- [ ] **Step 2: Replace stale CURRENT handoff**

Set `WP-GOV-LSI-01` as the active handoff. Record PR #44 as merged, the temporary hosted-CI billing/spending-limit blocker, `PENDING_RETRO_CI = YES` for the post-last-green merge range, the governance-only scope, and the next product objective as Full TBMT Intake after governance acceptance.

- [ ] **Step 3: Commit**

Commit message:

```text
docs: normalize handoff after source routing merge
```

### Task 4: Verify the governance WP and create the remote checkpoint

**Files:**
- Verify all files changed from `fc4d68cbeb9e5f27a91039e264e3906d1ee8f1c7` to the final branch head.

**Interfaces:**
- Consumes: Tasks 1–3.
- Produces: bounded governance evidence and a remote checkpoint without opening a PR until the parent integration gate.

- [ ] **Step 1: Verify changed-file scope**

Expected allowed paths are Markdown governance/spec/plan files only. Any production/test/migration/workflow/version/release-script path is `LOCAL_AUDIT_HOLD`.

- [ ] **Step 2: Verify textual invariants**

Confirm that the final docs state all of the following without contradiction:

```text
ChatGPT/Reviewer != runtime Machine Verifier
feature push without PR != CI evidence
LOCAL_AUDIT_PASS freezes audited history by default
later corrections are forward commits
>6 slices => SPLIT_REVIEW_REQUIRED, not automatic failure
CI waiver != CI PASS
PENDING_RETRO_CI > 0 => official release blocked
```

- [ ] **Step 3: Verify no CI workflow modification**

Compare changed filenames and confirm `.github/workflows/ci.yml` is untouched.

- [ ] **Step 4: Record delivery state**

Update `CURRENT.md` with exact branch/head and the verification performed. Keep the branch as the remote checkpoint. Do not claim hosted CI PASS while account billing prevents job execution.

- [ ] **Step 5: Commit**

Commit message:

```text
docs: finalize staged integration governance handoff
```

## Self-review

- Spec coverage: every approved requirement is assigned to Tasks 1–4.
- Placeholder scan: no `TBD`, `TODO`, or unspecified implementation step remains.
- Type/interface consistency: governance identifiers use stable names from the approved design (`LOCAL_REVIEW_PACKET`, `LOCAL_AUDIT_PASS`, `SPLIT_REVIEW_REQUIRED`, `PENDING_RETRO_CI`, `CI_RECOVERY_PASS`).
