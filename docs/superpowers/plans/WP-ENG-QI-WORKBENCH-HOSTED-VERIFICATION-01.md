# WP-ENG-QI-WORKBENCH-HOSTED-VERIFICATION-01

## Mission and authority

- **Parent:** `WP-ENG-QI-WORKBENCH-IMPACT-READINESS-01 rev3`; the Parent remains open and `HOLD` because whole-local verification is red. This Micro-WP does not close or promote the Parent.
- **Role:** `BUILDER_SINGLE_WRITER`, assigned by Planner `/root` under the Human-authorized Stage A task on 2026-09-28.
- **Objective:** obtain and reconcile clean-checkout hosted CI evidence for the held candidate. No product behavior, capability maturity, or B09 implementation changes.
- **Human authorization:** the Stage A task explicitly authorizes the exact initial push of `e9fc731a6aa2ec2b8e6dc80a09ee9c37543ed809` as a remote checkpoint despite the Parent's whole-local `HOLD`, then local materialization of this Micro-WP. The later integration sequence is bounded to one Draft PR into `main`, only after the required Planner and independent Reviewer gates. Merge and release are forbidden.
- **Roadmap:** Engineering Toolbox / Plugins supporting Cross-cutting Windows / Team Bid delivery. Product frontier remains Unified Tender Warehouse / `PARTIAL`; no product maturity promotion.
- **Relevant Delta:** RD-0013 / `OPTION_C_OPERATIONAL_UPDATE` / B09 history. B09 remains outside this Micro-WP and its existing historical WIP/HOLD evidence is unchanged.

## Architecture layer contract

```text
ARCHITECTURE_LAYER_CONTRACT
PRODUCT_LANE: Engineering Toolbox / Plugins; supports Cross-cutting Windows / Team Bid delivery. No product capability promotion.
HUMAN_CONSUMER: Human and Planner reconcile exact-head hosted CI evidence for a held engineering-tool candidate.
MACHINE_CONSUMER: Existing GitHub Actions Python CI workflow and its Required CI Gate.
DOMAIN_CORE: OUT_OF_SCOPE; no product-domain behavior.
APPLICATION_BACKEND: OUT_OF_SCOPE; no application behavior.
SOURCE_ADAPTERS: OUT_OF_SCOPE; no crawler adapter behavior.
PERSISTENCE_INFRA: OUT_OF_SCOPE; no product storage or persistence changes.
DELIVERY_ADAPTERS: OUT_OF_SCOPE; no product delivery adapter changes.
DESKTOP_FRONTEND: OUT_OF_SCOPE.
CLI: OUT_OF_SCOPE.
API: OUT_OF_SCOPE.
AI_CONSUMER: OUT_OF_SCOPE for product AI capability; no runtime router work.
ENGINEERING_TOOLS: required; hosted verification only for the existing QI impact-routing candidate.
DEPENDENCY_DIRECTION_CHECK: no source or product-layer dependency changes are authorized.
RATIONALE: This Micro-WP adds hosted verification evidence and governance handoff only; the workflow itself is not in the edit scope.
```

## Exact entry objects and evidence

- **Canonical checkout:** `D:\QI Technology\QI Crawler\egp-crawler-python`.
- **Expected origin:** `https://github.com/tanntran2000/QI-Crawler-MVP.git`.
- **Branch:** `codex/workbench-impact-readiness-01`.
- **Initial candidate and code head:** `e9fc731a6aa2ec2b8e6dc80a09ee9c37543ed809`.
- **Live main:** `51463a1ba01af9cd499e0b7c7cc961c19771bbf4`, independently re-resolved by Planner and rechecked with `git ls-remote` immediately before and after the checkpoint push on 2026-09-28.
- **Final Reviewer evidence:** `WP-ENG-QI-WORKBENCH-IMPACT-READINESS-01-REVIEWER-TERMINAL-20260928-05`, source task `/root/workbench_impact_readiness_reviewer`, audited object `e9fc731a6aa2ec2b8e6dc80a09ee9c37543ed809`; `WIR-R01 PASS`, `WIR-R02 PASS`, `WIR-R03 HOLD`; scoped candidate `PASS`, whole Parent `HOLD`, merge `NO`.
- **Initial integration range:** `51463a1ba01af9cd499e0b7c7cc961c19771bbf4..e9fc731a6aa2ec2b8e6dc80a09ee9c37543ed809`; 11 text paths: ten Parent-WP paths plus the inherited storage-closeout plan from `51d2e9efc7d96334b629dc0ea97c6feb97966355`. The inherited plan is not attributed to this Parent. No runtime, raw-log, user-config, business-data, or binary path is in this range.
- **Initial remote checkpoint:** the exact candidate was pushed without force to `refs/heads/codex/workbench-impact-readiness-01`; `git ls-remote` confirmed the feature ref equals `e9fc731...` and `main` still equals `51463a1...`. This is a remote checkpoint only. A feature-branch push does not run this repository's workflow, which runs on pushes to `main` and pull requests targeting `main`.

## Held-candidate disclosure

Any eventual PR description and handoff must disclose all of the following without relabeling the Parent result:

- scoped static routing contract: `PASS`; this is static contract evidence only.
- whole local Parent verification: `HOLD`; full sequential pytest is `RED`.
- the scratch budget failed twice: both Builder full runs exceeded the approved 10,000-file cap (13,910 files / 621,941,751 bytes and 14,033 files / 614,887,749 bytes), while each stayed under the 2 GiB byte cap. The breach was detected only by the final hidden-inclusive post-run audit.
- repository-wide local Ruff: `RED` as Builder-reported; eight errors were reported in a preserved unknown `$RECYCLE.BIN` file and were not independently log-verified by Tester. No cleanup is authorized.
- Codebase Memory readiness: `HOLD_WITH_DIAGNOSIS`; zero index attempts and no coverage/runtime claim.
- the 65 failures in the final full run are not fully classified; neither product nor candidate causation is established.
- this work is verification-only. Merge is not requested or authorized in this Micro-WP; no capability, runtime routing, B09, or product maturity claim is added.
- the inherited storage-closeout plan in the 11-path integration range is prior work and is not part of this Parent's implementation.

## Bounded scope and authority

Stage A write scope is exactly:

1. `docs/superpowers/plans/WP-ENG-QI-WORKBENCH-HOSTED-VERIFICATION-01.md`
2. `docs/agent/PATH_REGISTRY.yaml`
3. `docs/agent_handoff/CURRENT.md`

The later CI correction implementation allowlist, if Planner opens a correction, is exactly the Parent rev3 implementation allowlist:

1. `plugins/qi-agent-workbench/skills/qi-impact-map/SKILL.md`
2. `tests/agent_workbench/test_execution_skills_contract.py`
3. `docs/agent/QI_AGENT_WORKBENCH.md`
4. `plugins/qi-agent-workbench/skills-lock.json`

Later governance-transition edits are limited to this Micro-WP plan, `docs/agent/PATH_REGISTRY.yaml`, and `docs/agent_handoff/CURRENT.md`. This locator does not grant a correction by itself. A failure requiring a B09 file, workflow, dependency, other path, or broader authority is `HOLD` to Planner. No CI workflow change is authorized. No new skip/xfail, assertion weakening, or gate reduction is allowed.

The hosted verification sequence is limited to one Draft PR into `main`, after Planner review and independent audit of the exact governance commit. Do not create a PR during Stage A. Do not merge, release, amend, rebase, force-push, or overwrite a remote ref. The Human-authorized later transition remains subject to the stated Planner/Reviewer gates and a fresh exact-ref check.

## Hosted CI contract

The existing `.github/workflows/ci.yml` must run for the exact PR candidate. Required jobs and current finite job timeouts are:

| Required job | Runtime | Timeout |
| --- | --- | ---: |
| Code Quality | Ubuntu | 10 minutes |
| Tests Ubuntu 3.12 | Ubuntu 3.12 | 20 minutes |
| Tests Windows 3.12 | Windows 3.12 | 45 minutes |
| Compatibility Ubuntu 3.11 | Ubuntu 3.11 | 20 minutes |
| Required CI Gate | Ubuntu 3.12 | 3 minutes |

`Required CI Gate` must succeed and its four dependencies must each report success on the current PR event. This workflow records `CI_SOURCE_HEAD_SHA` from the source PR head and separately binds test jobs to the event `GITHUB_SHA` merge-preview commit. Record both SHAs, the PR head, target/base state, workflow run ID/URL, and run attempt; prove the tested merge-preview corresponds to that PR event and do not relabel it as the source head. Any base/head update requires the latest event's complete result. Missing, skipped, cancelled, stale-head, or incomplete jobs are not `PASS`. A green workflow is complementary hosted evidence and does not erase local RED results, scratch-cap failures, unresolved failure classification, the Codebase Memory hold, or the Parent's whole-local `HOLD`.

No full local pytest, repository-wide Ruff, Codebase Memory index, B09 operation, or runtime action is authorized in this Micro-WP. The CI workflow and its existing artifact budget remain unchanged. If the workflow requires modification, stop and return to Planner.

## Failure classification and forward corrections

- Maximum forward CI correction attempts for this Micro-WP: **two**, each opened by Planner only after recording a failure classification and the exact proposed path set. An attempt is not permission to exceed either correction allowlist.
- For each correction, preserve the prior exact head and evidence; use a new semantic commit. No amend, rebase, force-push, or history replacement.
- Every new candidate head requires the relevant independent review and a complete exact-head CI run. Old green evidence does not transfer to a new head.
- If a job failure is classified as transient infrastructure, at most one rerun is permitted for that CI contract after evidence-based classification. No blind retry. A repeated infrastructure failure stops for Planner.
- Classify material failures as `WP_CODE_DEFECT`, `CI_INFRASTRUCTURE_DEFECT`, `DEPENDENCY/NETWORK_DEFECT`, `PRE-EXISTING_TECH_DEBT`, or `UNKNOWN`. Do not claim the historical 65 failures are all environment- or product-caused.
- Any correction needed outside the bounded allowlists, any B09/runtime need, or any unresolved material interpretation is `HOLD` to Planner. The scratch prevention proposal remains pending; this Micro-WP does not implement it or raise the historical cap.

## Stages and completion evidence

**Stage A — checkpoint and governance entry:** re-resolve canonical checkout, branch, local/live `main`, and remote feature ref; push only the exact initial candidate if the ref is absent; verify exact remote SHA; materialize this Work Order, one locator-only binding, and the active `CURRENT.md` transition. No PR or hosted-CI claim.

**Stage B — governance review:** Planner reviews the exact local Stage A commit and assigns an independent Reviewer to inspect it. Do not push the governance commit or open a PR until Planner confirms the review and next transition.

**Stage C — hosted run:** after the required gates, push the approved governance head by normal fast-forward and create exactly one Draft PR into `main`. Re-resolve the remote branch and target immediately before the operation. Collect exact PR, head SHA, run ID/URL, required-job outcomes, attempts, and available diagnostic artifact identities. The PR remains draft and unmerged.

**Stage D — bounded correction if needed:** only through a Planner-opened attempt, under the budgets and allowlists above; new head gets relevant review and a full exact-head CI rerun.

**Stage E — reconcile and stop:** Tester, independent Reviewer, and Planner report separately:

```text
SCOPED_ROUTING_VERDICT
HOSTED_CI_VERDICT
LOCAL_VERIFICATION_LIMITATIONS
SCRATCH_INCIDENT_DISPOSITION
CODEBASE_MEMORY_READINESS
MERGE_RECOMMENDATION
```

Hosted CI cannot close the Parent or authorize merge/release/B09. Human retains merge and release authority. Stop with the draft PR open; do not merge.

## CI Fitness Contract

```text
CURRENT WP: WP-ENG-QI-WORKBENCH-HOSTED-VERIFICATION-01
CAPABILITY UNDER CHANGE: Exact-head hosted verification and reconciliation for a held static engineering-tool candidate; no product capability change.
CRITICAL RISKS: Wrong-head attribution; treating a branch checkpoint as CI; accepting missing/skipped/cancelled jobs; erasing local RED/scratch history; correction scope expansion; interpreting hosted green as merge or B09 authority.
BASELINE GATES TO KEEP: Existing Code Quality, Tests Ubuntu 3.12, Tests Windows 3.12, Compatibility Ubuntu 3.11, and Required CI Gate; exact-head accounting and strict success semantics.
WP-SPECIFIC GATES REQUIRED: All four jobs succeed for the latest PR event and Required CI Gate succeeds; record source PR head plus tested GITHUB_SHA merge-preview identity, run/attempt, and target/base state; reconcile all six independent verdict/limitation fields above.
GATES NOT REQUIRED YET: New workflow gates or changes; a local full-suite/Ruff rerun; Codebase Memory indexing; runtime router verification; B09 technical/runtime verification; product acceptance; merge/release.
MAX JOB RUNTIME: Code Quality 10 min; Tests Ubuntu 3.12 20 min; Tests Windows 3.12 45 min; Compatibility Ubuntu 3.11 20 min; Required CI Gate 3 min.
CI CHANGE REQUIRED BEFORE IMPLEMENTATION: NO; no implementation change is authorized. If the existing workflow cannot prove the contract, HOLD and ask Planner to seek new authority.
RATIONALE: Existing required jobs cover the held candidate's static test and repository-quality risk; the Micro-WP adds exact-head hosted evidence without changing CI policy or product behavior.
```

## Entry and handoff requirements

Before any Stage B or later action, re-resolve canonical checkout, top-level, git-dir/common-dir, origin, branch, exact `HEAD`, local and live `origin/main`, remote feature SHA, ancestry, and tracked/index status. Stop on drift, tracked dirt, a non-fast-forward/conflicting ref, identity mismatch, or an out-of-scope need. Unknown untracked contents remain untouched.

The active handoff must retain the Parent's whole-local `HOLD`, WIR-R03 failure, scratch-cap `FAIL`, repo Ruff limitation, and Codebase Memory `HOLD`. Keep these distinct from the Micro-WP's remote checkpoint and later hosted-CI result. `SPINE_IMPACT`, `SPINE_TARGET_FILES`, and `SPINE_SYNC_STATE` must be truthful before a role handoff. Stage A next authority is Planner `/root` for governance review; no PR is opened at this stage.
