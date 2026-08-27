# QI-Crawler repository guardrails

## Repository map

- Production: `src/qi_crawler/`; tests: `tests/`; migrations: `alembic/versions/`
- Packaging: `packaging/`; scripts: `scripts/`; docs: `docs/`; templates: `templates/`
- Important root helpers: `evaluate_qi_crawler.py`, `pyproject.toml`, `alembic.ini`, tracked build/release scripts.
- Generated only: `.pytest_cache/`, `.ruff_cache/`, `__pycache__/`, `build/`, `dist/`, `release_staging/`, approved `.tmp/` children.

## Workspace policy

- Use one canonical checkout: `egp-crawler-python`.
- Work in place on one active short-lived feature branch at a time; never create any Git worktree anywhere, including sibling or project-local/nested `.worktrees/` or `worktrees/`, sibling clones, or WP-named folders.
- After an approved merge, return to `main`, fast-forward from `origin/main`, and delete the merged local branch.

## Release and version governance

Any change affecting a user-visible feature, GUI, packaged runtime, database
compatibility, installer behavior, or Team Bid workflow requires a
**RELEASE IMPACT ASSESSMENT**. A Team Bid release is one release, one version,
one Git SHA, and one build identity; the canonical app/package version, GUI,
installer, `BUILD_INFO`, and release manifest must agree. A mismatch is a
release-gate failure.

Use semantic versioning: PATCH for bug or stability corrections without new
capability, MINOR for new capability or significant GUI/workflow change, and
MAJOR for a breaking user/data/runtime contract. Docs-only, test-only,
CI-only, and internal refactor commits without user-visible effect do not
automatically require a version bump. Human authority approves the official
Team Bid release/publish. Git main/new commit and `CHANGELOG.md` are not, by
themselves, a Team Bid release.

Every user-visible merged change updates `CHANGELOG.md` or `Unreleased` when
appropriate. Every approved Team Bid release records the canonical application
version, exact Git SHA, immutable annotated tag `vX.Y.Z`, GitHub Release
`vX.Y.Z`, release notes, installer/EXE hashes, and `BUILD_INFO` or a release
manifest. A Git commit or `CHANGELOG.md` entry alone is not a release.
Historical tags and releases must never be silently moved.

## Safety rules

1. Unknown is **KEEP**. Never delete a tracked file without the user's exact request.
2. Never infer generated status from a `.py`, `.ps1`, `.toml`, `.ini`, `.md`, or migration filename.
3. Before deletion: check `git status`, `git ls-files`, reproducibility, and an explicit allowlist. Never recursively delete the repository root.
4. Never delete `src/`, `tests/`, `alembic/`, `packaging/`, `scripts/`, `docs/`, `templates/`, fixtures, or tracked root helpers.
5. Use `scripts/clean_dev.ps1 -WhatIf` first. Permission/ACL errors must warn and skip; never take ownership or elevate.
6. Small task: inspect only relevant source/tests. Avoid unrelated modules and speculative refactors; stop if scope expands unexpectedly.
7. Validation: targeted `python -m pytest` → `python -m pytest` → `ruff check .` → `git diff --check` → `git diff --name-status`.
8. A task fails on unexpected source deletion. Never commit/push unless explicitly asked; never alter stable tags.

## Engineering governance laws

1. **LAW 1 — PLAN-FIRST**: Planner creates the design/work-order; Planner does not code.
2. **LAW 2 — SEPARATION OF RESPONSIBILITIES**: The governed coordination flow
   is `HUMAN MATERIAL INTENT` → `PLANNER_ARCHITECT` → `BUILDER_SINGLE_WRITER`
   → `MACHINE_VERIFIER` evidence when applicable →
   `PLANNER_BUILDER_RESULT_REVIEW` → `INDEPENDENT REVIEWER_AUDITOR` →
   `PLANNER_POST_REVIEW_RECONCILIATION` → Human material, merge or release
   authority. Planner builder-result review is orchestration and evidence/scope
   analysis; it does not edit Builder output, replace Machine Verifier or
   perform the independent audit. Planner post-review reconciliation does not
   rewrite the Reviewer verdict, substitute for independent review or authorize
   Human-only decisions. These are authority roles, not model names. One
   Writer, independent review and Human final material authority remain
   mandatory.
3. **LAW 3 — SYSTEMIC LESSONS ONLY**: Record durable architectural lessons; do not pollute lessons with minor typos.
4. **LAW 4 — PROOF-GATED DEFINITION OF DONE**: Verify against the explicit Work Order contract; never claim unqualified perfection.
5. **LAW 5 — MINIMAL COMPLETE FIX**: Fix at root cause with the smallest complete change; no masking or speculative refactoring.
6. **LAW 6 — BOUNDED AUTONOMY**: Single Writer operates strictly inside the Work Order scope; stop immediately on blocker.
7. **LAW 7 — SINGLE WRITER**: Only ONE agent writes production/test code in any micro-WP.
8. **LAW 8 — ADAPTIVE VERIFICATION**: Before judging implementation correctness, the Reviewer must verify that the current CI/test contract matches the current Work Package's capability under change, risk profile, acceptance criteria, and maturity stage.

9. **LAW 9 — HANDOFF READ-IN & CONTINUITY**: `READ → VERIFY → ENTRY REVIEW → ONE APPROVAL → EXECUTE MANY`. Approval leases a bounded Work Package, not individual commands. Re-approval is required only when scope, baseline, handoff authority, writer, or a material blocker changes.

10. **LAW 10 — DOCUMENTATION LIFECYCLE**: Every Parent and Micro Work Package has a bounded PRE and POST state. `ALWAYS CHECK != ALWAYS MODIFY`: inspect the required documents at every governed transition, but update only the tier and trigger that applies. `CURRENT.md` is active handoff authority, not a diary, roadmap, review report, or chat summary; historical snapshots are non-normative after capture; durable contracts change only through approved governance.

11. **LAW 11 — AUDIT OBJECT AUTHORITY**: A review report or copied audit
    statement is evidence, not Git object authority. By default, the Reviewer
    directly inspects the exact Git range `BASE_SHA..HEAD_SHA` in the canonical
    checkout using `git diff`, `git show`, source inspection and test
    inspection. A patch is transport/fallback evidence only when exact Git
    objects are unavailable. Reviewer independence remains required.

12. **LAW 12 — COMPATIBILITY SEAMS**: Passing tests do not by themselves prove legacy compatibility. When a generic abstraction wraps a legacy path, review `OLD CONTRACT → ADAPTER / COMPATIBILITY BOUNDARY → NEW GENERIC CONTRACT` and preserve legacy behavior at the narrowest boundary.

13. **LAW 13 — SPINE IMMEDIATE PROMOTION**: A material beneficial improvement,
    newly verified project fact, approved governance/process change,
    architecture decision, systemic lesson, capability maturity change, or
    material engineering failure/prevention finding must be routed to its
    canonical Context Spine authority at the same governed transition in
    which it becomes accepted or verified. Material organizational knowledge
    must not remain chat-only.

    Before Reviewer handoff, the next Micro-WP, Parent closeout, PR/merge
    transition, or post-merge handoff, resolve:

    ```text
    SPINE_IMPACT = NONE | CURRENT | ROADMAP | PROJECT_MEMORY |
                   FAILURE_MEMORY | LESSONS | FEEDBACK | GOVERNANCE | MULTIPLE
    SPINE_TARGET_FILES = <canonical Context Spine files>
    SPINE_SYNC_STATE = PASS | HOLD
    ```

    `MATERIAL_NEW_DURABLE_INFORMATION + NOT_ROUTED` is a governance hold.
    `SPINE_SYNC_STATE != PASS` means `HANDOFF_READY = NO`. `ALWAYS CHECK !=
    ALWAYS MODIFY`: inspect the applicable authorities at every transition,
    but material new durable information must update the correct authority.

14. **LAW 14 — ROADMAP DELTA & REVIEWER CONTINUITY**: `docs/agent/MASTER_ROADMAP_DELTA.md`
    is mandatory companion context alongside `MASTER_ROADMAP.md`. New
    material product understanding that is not yet ready for permanent roadmap
    promotion must be triaged there, with PRE/MID-trigger/POST reconciliation.
    The Reviewer checks implementation alignment and documentation freshness;
    stale relevant organizational memory may block handoff. The Delta does not
    silently override the Master Roadmap; material conflict routes to the
    Planner and Human authority.

15. **LAW 15 — HUMAN INTENT & PLANNER STRATEGIC RECONCILIATION**: Human
    material intent must flow through Planner capture, interpretation and
    explicit disposition into the Work Order, handoff, Delta or Feedback
    authority, then through Builder, Planner builder-result analysis, Reviewer
    audit and Planner's direct Roadmap/Delta/Spine/live-state reconciliation
    back to Human when material. Human material intent must not be silently
    dropped. Human authority does not mean every Human technical assumption is
    a verified fact. `REVIEWER AUDIT VERDICT != PLANNER STRATEGIC INTEGRATION
    DECISION != HUMAN MATERIAL AUTHORITY`. Planner may challenge a technical
    assumption with evidence, must not silently override an A0 business
    decision, and must independently reconcile Reviewer evidence before
    recommending merge or next work.

### Canonical Context Spine routing

Route accepted or verified material knowledge to the narrowest authority:

```text
CURRENT execution/handoff/transition state
  → docs/agent_handoff/CURRENT.md
Strategic architecture/frontier/capability maturity
  → docs/agent/MASTER_ROADMAP.md
Active unresolved roadmap/product evolution
  → docs/agent/MASTER_ROADMAP_DELTA.md
Durable fact already merged to main
  → docs/agent/PROJECT_MEMORY.md
Material engineering failure/root cause/prevention
  → docs/agent/KNOWN_FAILURE_MODES.md
Durable systemic engineering lesson
  → docs/agent/LESSONS.md
Human A0 decision/material feedback
  → docs/agent/FEEDBACK_LEDGER.md
Durable agent/process/governance law
  → AGENTS.md and applicable supporting governance contract(s)
```

Do not route unmerged implementation facts into `PROJECT_MEMORY.md`, and do
not turn `CURRENT.md` into a roadmap, history, diary, or review report.

For a **NEW AGENT**, **NEW PARENT WP**, **WRITER TAKEOVER**,
**PLANNER/REVIEWER TAKEOVER**, or **MATERIAL ARCHITECTURE CHANGE**, the agent
must fully read `docs/agent/MASTER_ROADMAP.md` before declaring READY. Future
material Work Orders must include the roadmap's `ARCHITECTURE_LAYER_CONTRACT`
in addition to the CI Fitness Contract. The roadmap classifies the Product
House and its layers; the Work Order authorizes construction scope. A Builder
must not infer edit authorization from the roadmap alone.

Builder handoff discipline is governed by
`docs/agent/LOCAL_STAGED_INTEGRATION.md`: refresh `CURRENT.md` only at an
audited remote checkpoint, a material blocker or scope-invalidating finding,
an inter-agent/session handoff, or Parent merge/closeout. Normal edits, test
runs, unaudited progress, speculative ideas, and chat narration do not justify
a refresh. Handoffs are short, factual, evidence-backed, actionable snapshots
and are not diaries, roadmaps, review reports, or chat summaries.

### Roadmap entry gate and read modes

No agent may declare `READY`, `PROMPT_READY` or `START_IMPLEMENTATION` until
the following are resolved and evidenced:

```text
ROADMAP_BASELINE = VERIFIED
PRODUCT_FRONTIER = RESOLVED
ROADMAP_NODE = RESOLVED
ARCHITECTURE_LAYERS = RESOLVED
READ_MODE = RESOLVED
```

Use `FULL` read-in for a new agent, new Parent, Planner/Reviewer/Writer
takeover, or material architecture/governance change; `DELTA` for a new
Micro-WP under the same unchanged Parent/architecture; and `NO_RE_READ` only
for the same Micro-WP, session, lease and authority with no material change.
A changed roadmap SHA or blueprint revision invalidates `NO_RE_READ` and
requires at least a delta reconciliation. Do not reread the full roadmap for
every ordinary command.

### Role entry gate

Before a new agent, new Parent, agent entry, Planner/Builder/Writer/Reviewer or
Domain Reviewer takeover, material role reassignment, or material authority-
boundary change may declare `READY`, `PROMPT_READY`, `START_IMPLEMENTATION` or
`START_AUDIT`, it must pass the single canonical `ROLE_ENTRY_GATE` defined in
`docs/agent/OPERATING_MODEL.md`. The gate resolves the assigned canonical role
from the latest explicit Human assignment, approved Work Order and governed
`CURRENT.md` handoff; those sources must reconcile. `ROLE > MODEL NAME`: a
ChatGPT/Codex/CI/tool/model identity is never role evidence or business
authority. Missing, unknown, conflicting or takeover-reused role evidence fails
closed to `ENTRY_HOLD` and escalates to the Planner or Human as appropriate.
The gate checks the existing role contract; it does not replace the separate
Roadmap Entry Gate. Reuse is allowed only for the same agent/session, role,
authority and Work Order/lease with no material conflict or takeover. No role
resolution means no implementation, prompt or audit authority.

### Post-merge handoff gate

After a PR merge, the governed transition is:

```text
PR MERGED → verify live main → reconcile CURRENT → close merged Parent state
→ check roadmap maturity → check PROJECT_MEMORY promotion → resolve next action
→ HANDOFF READY
```

At that transition, check applicable `KNOWN_FAILURE_MODES`,
`FEEDBACK_LEDGER` and `LESSONS` triggers; `ALWAYS CHECK != ALWAYS MODIFY`.

If `PR MERGED + CURRENT STILL CLAIMS NOT MERGED`, the state is
`HANDOFF_STALE` and the next technical entry is `ENTRY_HOLD` until reconciled.
Live Git/GitHub remains authority for volatile state, but stale organizational
memory must be corrected before execution authority is handed off.

Cross-agent/session handoffs must carry, when applicable:
`ROADMAP_REVISION`, `ROADMAP_BASELINE_SHA`, `HANDOFF_CAPTURE_BASE`,
`AUDIT_TARGET_CODE_HEAD`, `LAST_AUDITED_CODE_HEAD`, `LAST_AUDITED_DOC_HEAD`,
`LIVE_GIT_HEAD`, `ACTIVE_PARENT_WP`, `ACTIVE_MICRO_WP`, `REMOTE_CHECKPOINT`,
`PR_STATE`, `MERGE_STATE`, `VERIFICATION_STATE`, `HOSTED_CI_STATE`,
`DOC_SYNC_STATE`, `PROVEN_COMPLETE`, `OPEN_BLOCKERS`, `SCOPE_BOUNDARIES`,
`EXACTLY_ONE_NEXT_ACTION` and `NEXT_AUTHORITY`. `HANDOFF_CAPTURE_BASE` is the
Git head verified immediately before a handoff write; `AUDIT_TARGET_CODE_HEAD`
is the exact code/test commit under review; `LAST_AUDITED_CODE_HEAD` is the
already-audited code head; `LIVE_GIT_HEAD` is always re-resolved from Git at
read-in. A later docs-only handoff commit must not be treated as a new code
audit target. Missing answers mean `HANDOFF_READY = NO`; a handoff is not a
transcript.

Organizational memory follows:

```text
CHAT = collaboration medium
FILES = organizational memory
GIT/GITHUB = repository truth
```

Material decisions, architecture and accepted systemic process rules must be
routed to the appropriate durable file rather than remaining chat-only. Do
not copy every chat message into memory.

### Adaptive verification rules

The Reviewer must not ask only *"Does the code pass CI?"*, but first *"Does this CI verify the right contracts for this WP?"*.

- **CI Fitness Classifications:** `FIT`, `FIT_WITH_ADDITION`, `OVERBROAD`, `STALE`, `UNSTABLE`.
- **Preserve baseline gates:** Retain core quality gates that protect platform integrity.
- **Minimum complete WP gates:** Add only the minimum specific gates required to prove the active Work Order.
- **No stale gate baggage:** Do not carry obsolete phase-specific gates forward indefinitely.
- **No premature future gates:** Do not activate future-phase gates before their capability is built.
- **Phase Evolution Examples:**
  - *Crawler Core:* discovery, pagination, retry/resume, dedup, persistence.
  - *Warehouse:* SHA content-addressing, Package/Revision, managed storage, Vault, Shelf, recovery, bundle integrity.
  - *HSMT Extraction:* multi-page tables, boundary rows, structured facts, completeness, fail-closed handling (`SOURCE_DOCUMENT_MISSING`, `SOURCE_CONFLICT`, `NEEDS_REVIEW`).
  - *Evidence:* evidence locators, page/sheet/row provenance.
  - *Ground Truth:* verified corrections, Golden HSMT regression.
  - *AI:* authority boundary, deterministic fallback, confidence-gated routing.

## CI runtime & triage governance

1. **Finite Adaptive Budgets:** Every required CI job must have a finite, job-specific, evidence-based runtime budget defined by the active CI Fitness Contract.
2. **Timeout / Stall Triage:** If a required job reaches its configured finite budget or stalls, HOLD verification and begin root-cause triage:
   - **HOLD** verification immediately.
   - **Root-Cause Triage:** Classify as `WP_CODE_DEFECT`, `CI_INFRASTRUCTURE_DEFECT`, `DEPENDENCY/NETWORK_DEFECT`, `PRE-EXISTING_TECH_DEBT`, or `UNKNOWN`.
   - If transient CI infrastructure: at most **ONE** rerun. If repeated, stop rerunning and create a bounded CI-hardening task.
   - A fast explicit failure is strictly preferred over an unbounded hang.
   - Never increase a budget merely to mask defects or instability.

## Local staged integration governance

Detailed micro-WP review, audited commit freeze, forward correction, remote
feature-branch checkpoints, Parent-WP integration, hosted-CI waiver, retro-CI
recovery, and release blocking are defined in
`docs/agent/LOCAL_STAGED_INTEGRATION.md`.

- A feature-branch push without an open PR is a remote checkpoint only; it is
  not CI evidence and must never be reported as `CI PASS`.
- Local machine execution may supply machine-verifier evidence when hosted CI
  is unavailable; the Independent Reviewer/Auditor remains a separate role and
  does not become a runtime runner.
- A merge performed under a verified hosted-CI infrastructure waiver accrues
  `PENDING_RETRO_CI = YES` until CI Recovery passes.
- `PENDING_RETRO_CI > 0` blocks official Team Bid release/publish unless a later
  explicit Human decision establishes a separate bounded exception.

## Work Order CI fitness contract requirement

Every future Work Order must define its CI Fitness Contract before implementation:

```text
CI FITNESS CONTRACT
-------------------
CURRENT WP:
CAPABILITY UNDER CHANGE:
CRITICAL RISKS:
BASELINE GATES TO KEEP:
WP-SPECIFIC GATES REQUIRED:
GATES NOT REQUIRED YET:
MAX JOB RUNTIME: <finite WP/job-specific budget>
CI CHANGE REQUIRED BEFORE IMPLEMENTATION: YES / NO
RATIONALE:
```

## Plugin execution contract

For technical Work Packages where applicable:

- Invoke Superpowers skills before the action they govern.
- Use CodeGraph for relevant impact discovery before edits.
- Evidence plugin execution; naming CodeGraph/Superpowers alone is insufficient.
- Incidents require systematic-debugging before a fix; behavior changes require
  TDD RED → GREEN; PASS/DONE requires verification-before-completion.
- Report CodeGraph impact radius separately from edit and test radius.
- If a plugin is unavailable, report `TOOL_UNAVAILABLE` and use the documented
  fallback; never disable or remove a plugin to bypass its workflow.

## Governed work profiles and bounded execution

Every Builder Work Order must be role-specific and must resolve the mission,
authority, mandatory reads, inputs, in-scope files, explicit exclusions,
acceptance criteria, verification contract, evidence format, stop conditions,
handoff target, and `SPINE_IMPACT`/`SPINE_TARGET_FILES`/`SPINE_SYNC_STATE`.
The Builder executes only that bounded contract as the Single Writer. A
Human-approved `APPROVAL_LEASE` authorizes the complete bounded Work Package,
including safe in-scope commands, git add, semantic local commits and normal
internal stage transitions; it does not authorize scope expansion, merge,
release or a different writer.

`LARGE_BOUNDED_BATCH` is an auditable execution shape, not a relaxation of
scope. The Planner may group coherent work when the batch has one objective,
explicit capability and risk boundaries, internal stages, semantic commits,
stage-level verification, a final cumulative verification and one clear stop
condition. The Reviewer audits the coherent batch as one object with stronger
risk-oriented challenge. There is no universal micro-WP count or automatic
permission to continue across a material architecture, data-safety, authority
or scope boundary; such a boundary requires a governed stop and reapproval.

`CURRENT_WRITE_AUTHORITY` is conditional. `CURRENT.md` is writable by the
active `BUILDER_SINGLE_WRITER` only when it is in the approved `WRITE_SCOPE`, a
governed transition trigger exists, and every recorded fact has resolved
evidence and authority provenance. The Builder may record observable facts and
already-resolved Reviewer, Planner or Human decisions from exact evidence, but
may not originate those decisions. `RECORD_AUTHORITY != ORIGINATE_AUTHORITY`.
`CURRENT_UPDATE_FREQUENCY` is governed-transition frequency, never command,
edit or test frequency; the handoff is not a diary.

An Approval Lease never implicitly authorizes scope or material architecture
expansion, destructive/data-destroying operations, audited-history rewrite,
amend, rebase, force push, unauthorized remote push, PR creation or state
change, merge, release, Human business/A0 decisions, Reviewer verdict
creation, or Planner reconciliation creation. Those actions require their own
governed authority.

The Reviewer receives a challenge contract after the Builder result is
available. It must identify the Human intent to protect, claims and critical
invariants to challenge, relevant failures and architecture boundaries,
false-safe risks, required evidence, affected Spine/Delta/Roadmap nodes and
the evidence that would disprove PASS. A Reviewer must remain independent and
must not be instructed to return PASS.

Planner follow-through is part of the governed lifecycle:

```text
PLANNED → AUTHORIZED → BUILDER_RUNNING → BUILDER_RETURNED
→ PLANNER_BUILDER_RESULT_REVIEW → REVIEWER_ASSIGNED → REVIEWER_RETURNED
→ PLANNER_POST_REVIEW_RECONCILIATION → INTEGRATION_OR_HUMAN_DECISION
→ POST_STATE_VERIFIED → CLOSED
```

The Planner must reconcile what the Work Package achieved and did not achieve,
remaining risks, Human-intent preservation, applicable organizational memory,
and the next authority. `WORK_ORDER_ISSUED != DONE`,
`AUTHORIZED != BUILDER_COMPLETE`, `BUILDER_RETURNED != REVIEWED`,
`REVIEWER_VERDICT != PLANNER_RECONCILIATION != HUMAN_AUTHORIZATION`,
`REVIEWER_PASS != MERGE_AUTHORIZATION`,
`MERGE_PERFORMED != POST_STATE_VERIFIED`, and
`POST_STATE_VERIFIED != RELEASE_AUTHORIZATION`. `CLOSED` requires terminal
evidence for the governed unit; no role may silently promote candidate
governance into merged or final truth.

Plugin evidence is a contract, not a name-drop. For each applicable plugin,
the Work Order must explicitly set `PLUGIN_APPLICABILITY = REQUIRED | OPTIONAL
| NOT_APPLICABLE`. The evidence records `PLUGIN`, `PURPOSE`, `INVOCATION`,
`RESULT`, `FALLBACK`, `IMPACT_RADIUS`, `EDIT_RADIUS`, `TEST_RADIUS` and any
limitation. `REQUIRED` needs invocation evidence; `OPTIONAL` permits non-use
without a false use claim; `NOT_APPLICABLE` must not manufacture evidence.
`PLUGIN_AVAILABLE != PLUGIN_REQUIRED`, `PLUGIN_INSTALLED != PLUGIN_USED`, and
`PLUGIN_USED_WITHOUT_EVIDENCE = USAGE_NOT_PROVEN`. When CodeGraph is required,
the Work Order resolves purpose, seed queries, expected impact/edit/test
radii, and fallback. Use result classifications honestly:
`USED_AND_SUCCEEDED`, `USED_WITH_FALLBACK`, `TOOL_UNAVAILABLE` or
`NOT_APPLICABLE`. CodeGraph is impact intelligence only; Superpowers provide
execution discipline only.

For a terminal handoff that records its own completion, apply the narrow
`SELF_REFERENTIAL_TERMINAL_SYNC_RULE`: the terminal sync may update only the
authorized handoff authority, must preserve the pre-sync audited code/document
heads and exact next action, must not claim its own future commit or live
GitHub state, and must be followed by verification of duplicate keys, scope,
diff and tree. If `PR N` is reconciled by a terminal docs `PR N+1`, that
terminal PR does not require `PR N+2` solely to record its own merge; its own
volatile identity may remain live-only until the next governed transition.
That next transition must reconcile it before new Builder authority. This
exception applies only to the terminal PR's own volatile integration identity;
materially wrong active Parent/Micro/Writer/scope/authority/completion/next
action/blocker state is `HANDOFF_STALE → ENTRY_HOLD`, and a failed audit, CI or
Human-decision boundary cannot be hidden.

## Test collection integrity

At the beginning of a coding task:
- Record current pytest collection count.

At final verification:
- Collection must not unexpectedly decrease.
- Any decrease requires root-cause investigation.
- Never add/duplicate tests merely to satisfy a numeric count.
- Historical test counts are informational unless tied to a verified commit.
- Zero collection errors and zero failing tests are mandatory.
