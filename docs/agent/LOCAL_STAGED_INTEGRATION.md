# Local Staged Integration Contract

## 1. Purpose

This contract governs implementation slicing, local verification, independent
review, remote checkpoints, Parent-WP integration, temporary hosted-CI waiver,
and retro-CI recovery.

It implements the approved development model:

```text
Local Staged Integration + Remote Checkpoint + Parent-WP CI
```

This document is an operating procedure. It does not override `AGENTS.md`, an
explicit Human decision, or an approved Work Order.

## 2. Authority boundary

Roles remain separate:

- `HUMAN_AUTHORITY` approves Parent-WP scope, merge, release, and exceptions.
- `PLANNER_ARCHITECT` designs and decomposes the approved Parent WP.
- `BUILDER_SINGLE_WRITER` is the only writer for one active micro-WP.
- Local machine execution supplies `MACHINE_VERIFIER` evidence when required.
- `REVIEWER_AUDITOR` independently judges scope, logic, invariants, risks,
  diff, test adequacy, and the validity of supplied evidence after Builder and
  Machine-Verifier evidence.
- GitHub CI supplies clean-environment and multi-platform verification when
  available.

`REVIEWER_AUDITOR` is not a runtime CI runner. Local execution evidence and
independent reasoning review must not be collapsed into one authority.

## 3. Parent-WP execution flow

```text
Human approves Parent WP
→ Planner decomposes bounded micro-WPs
→ Single Writer implements one micro-WP
→ local verification
→ local commit
→ REVIEWER HANDOFF CHECKPOINT
→ INDEPENDENT REVIEW
→ PASS / HOLD / FAIL
→ SPINE PROMOTION CHECK
→ SPINE SYNC PASS
→ on PASS: push feature branch as remote checkpoint, without PR
→ MICRO POST
→ next micro-WP
→ Parent Integration Gate
→ final local audit
→ final feature-branch push
→ open Draft PR
→ hosted CI when available
→ exact-head independent audit
→ Human merge approval
```

The Human approval is an Approval Lease for the bounded Parent WP. Re-approval
is required when scope, baseline, writer, authority, or a material blocker
changes.

## 4. Work-package sizing and Parent-WP split review

Choose micro-WP or `LARGE_BOUNDED_BATCH` boundaries by capability coherence,
risk, architecture/data boundaries and independent auditability. A larger
batch is valid only when its objective, exclusions, internal stages, semantic
commits, stage verification and final stop condition are explicit. There is no
universal numeric micro-WP target.

Trigger:

```text
SPLIT_REVIEW_REQUIRED
```

when cumulative integration risk is no longer bounded, or when the work crosses
multiple major architectural or migration boundaries that require separate
authority, data-safety or audit treatment.

The Reviewer returns one of:

```text
CONTINUE_PARENT
SPLIT_PARENT_WP
```

with the architectural reason.

### 4.1 Large bounded batch and Approval Lease

`LARGE_BOUNDED_BATCH` is a coherent set of internal stages under one approved
Work Order, not a bypass around review. Before approval, the Planner records:

```text
BATCH_OBJECTIVE
BATCH_SCOPE / BATCH_EXCLUSIONS
INTERNAL_STAGES
STAGE_ENTRY / STAGE_OUTPUT / STAGE_VERIFICATION / STAGE_STOP
SEMANTIC_LOCAL_COMMITS
FINAL_CUMULATIVE_VERIFICATION
MATERIAL_BOUNDARY_ESCALATION
```

The Human `APPROVAL_LEASE` covers that bounded batch, including safe in-scope
commands, git add, semantic local commits and ordinary stage transitions. It
does not authorize another file family, writer, architecture/data boundary,
future Work Package, scope expansion, material architecture expansion,
destructive/data-destroying operation, audited-history rewrite, amend, rebase,
force push, unauthorized remote push, PR creation/state change, merge, release,
Human business/A0 decision, Reviewer verdict creation or Planner reconciliation
creation. A material blocker or boundary pauses execution for Planner/Human
reapproval. The Builder reports stage evidence as it works, but the independent
Reviewer audits the complete coherent batch at its governed handoff.

### 4.2 Planner follow-through lifecycle

Planner ownership continues through the complete governed unit:

```text
PLANNED → AUTHORIZED → BUILDER_RUNNING → BUILDER_RETURNED
→ PLANNER_BUILDER_RESULT_REVIEW → REVIEWER_ASSIGNED → REVIEWER_RETURNED
→ PLANNER_POST_REVIEW_RECONCILIATION → INTEGRATION_OR_HUMAN_DECISION
→ POST_STATE_VERIFIED → CLOSED
```

`WORK_ORDER_ISSUED != DONE`, `AUTHORIZED != BUILDER_COMPLETE`,
`BUILDER_RETURNED != REVIEWED`, `REVIEWER_PASS != MERGE_AUTHORIZATION`,
`MERGE_PERFORMED != POST_STATE_VERIFIED`, and
`POST_STATE_VERIFIED != RELEASE_AUTHORIZATION`. `CLOSED` requires terminal
evidence; Planner does not implement, audit independently or replace Human
authority.

## 5. Commit freeze and forward correction

A commit that has received `LOCAL_AUDIT_PASS` is an audited checkpoint.
During normal Parent-WP execution, do not silently amend, rebase, force-rewrite,
or replace that audited commit.

If a later slice requires a correction to earlier audited work, create a new
forward-correction commit with an explicit purpose, for example:

```text
micro-A
micro-B
fix(A-B integration)
```

Do not erase the correction trail by rewriting `micro-A`.

History cleanup before PR is not the default. Rewriting audited history
requires explicit Work Order permission and Human approval.

## 6. Local Review Packet

Every micro-WP must stop with this Builder-to-Reviewer handoff:

```text
REVIEWER_HANDOFF_CHECKPOINT
===========================
PARENT_WP:
MICRO_WP:
BASE_SHA:
HEAD_SHA:

CHANGED_FILES:
<git diff --name-status BASE..HEAD>

CODEGRAPH:
impact radius:
edit radius:
test radius:

TESTS:
command:
result:
exit code:

FULL / AFFECTED REGRESSION:
command:
result:
exit code:

RUFF:
command:
result:
exit code:

DIFF_CHECK:
command:
result:
exit code:

COLLECTION:
before:
after:

MIGRATION:
result / N/A

DATA_SAFETY:
result

KNOWN_RISKS:
...

TREE:
clean / dirty

AUDIT_OBJECT:
BASE_SHA..HEAD_SHA

PATCH:
OPTIONAL_FALLBACK — only when direct exact Git-object access is unavailable

NEXT:
STOP_FOR_INDEPENDENT_LOCAL_AUDIT
```

For successful commands, include the exact command, concise result, runtime
when useful, and exit code. Do not dump large successful pytest logs, binary
fixtures, databases, caches, or generated artifacts into the packet.

For a failure, include the relevant traceback/error excerpt and the command
that produced it.

The Reviewer must directly inspect `BASE_SHA..HEAD_SHA` with `git diff`,
`git show`, source inspection and test inspection whenever those objects are
available in the canonical checkout. A copied patch is fallback transport,
not the default audit object.

The Reviewer may run bounded verification such as targeted tests,
`git diff --check`, collection checks and architecture/import inspection. A
fresh Builder full-suite result need not be rerun by default unless risk or a
finding requires it. The Reviewer must inspect test quality and reject
tautological or weak evidence.

The standard independent packet is:

```text
INDEPENDENT_REVIEW_PACKET
ROLE
PARENT_WP
MICRO_WP
BASE_SHA
HEAD_SHA
AUDITED_RANGE
AUDIT_OBJECT_ACCESS = DIRECT_CANONICAL_GIT | FALLBACK_PATCH
CHANGED_FILES
SCOPE_AUDIT
ARCHITECTURE_AUDIT
DOMAIN_INVARIANTS
TEST_QUALITY
INDEPENDENT_TEST_COMMANDS
DIFF_CHECK
KNOWN_FAILURE_MODES
DATA_SAFETY
FINDINGS: CRITICAL / IMPORTANT / MINOR
BUILDER_EVIDENCE_VERIFIED = YES | PARTIAL | NO
AUDIT_VERDICT = PASS | HOLD | FAIL
EXACTLY_ONE_NEXT_ACTION
NEXT_AUTHORITY
```

### 7.1 Spine promotion gate

After independent review and before advancing the handoff, the packet must
contain:

```text
SPINE_AUDIT: PASS / HOLD
SPINE_IMPACT:
SPINE_TARGET_FILES:
SPINE_SYNC_STATE: PASS / HOLD
```

If `SPINE_AUDIT = HOLD` or `SPINE_SYNC_STATE != PASS`, do not advance to the
next Micro-WP and do not declare `HANDOFF_READY`. Corrections remain
forward-only; not every transition requires every Spine document to change.

### 7.2 Latest-WP Spine sync audit

`LATEST_WP_SPINE_SYNC_AUDIT` is the single continuity check for the latest
completed governed unit before a triggered transition. It reconciles the
exact Git object, active handoff, relevant Delta state and Context Spine; it
does not create an implementation ledger or replace the Roadmap, Delta,
Spine-promotion or role-entry gates.

Run it when entering the next Micro-WP or Parent-WP, during a Planner,
Reviewer or Builder takeover, at a cross-agent/session handoff, Parent
Integration Gate, PR/merge transition or post-merge reconciliation. Unchanged
continuous work inside the same Micro-WP does not require a repeat audit.

The canonical audit packet is:

```text
LATEST_WP_SPINE_SYNC_AUDIT
==========================
LATEST_GOVERNED_UNIT = <Parent WP / Micro-WP>
LATEST_COMPLETION_STATE = <resolved>
LATEST_AUDITED_HEAD = <exact SHA / N/A with reason>
LATEST_MERGED_HEAD = <exact SHA / NOT_MERGED>
LIVE_HEAD = <verified>
PROVEN_COMPLETE = <resolved>
PROVEN_NOT_COMPLETE = <resolved / NONE>
RELEVANT_DELTA_IDS = <resolved / NONE>
DELTA_STATE_RECONCILED = PASS / HOLD
SPINE_IMPACT = <resolved>
SPINE_TARGET_FILES = <resolved>
SPINE_FRESHNESS = PASS / STALE_NONBLOCKING / HOLD
MISSING_PROMOTIONS = NONE / <list>
CURRENT_FRESHNESS = PASS / HOLD
ROLE_AUTHORITY_DRIFT = NO / YES
NEXT_WORK_ALIGNMENT = PASS / HOLD
LATEST_WP_SPINE_SYNC_AUDIT_RESULT = PASS / HOLD
```

The audit uses live Git/GitHub, exact audited or merged objects, `CURRENT.md`,
and the durable Spine authorities in that order; copied audit prose is only
supporting evidence. It keeps audited distinct from merged, a remote
checkpoint distinct from CI PASS, a completed Micro-WP distinct from Parent
completion, code heads distinct from later docs heads, and partial Delta state
distinct from closed state.

Return `HOLD` when any material identity, freshness, promotion, completion,
next-work or authority fact cannot be reconciled. `ROLE_AUTHORITY_DRIFT = YES`
also requires the existing `ROLE_ENTRY_GATE` to pass again before execution
authority resumes. All required gates remain in force:

```text
READ_MODE_SELECTOR
→ ROADMAP / DELTA RECONCILIATION
→ ROLE_ENTRY_GATE
→ LATEST_WP_SPINE_SYNC_AUDIT when triggered
→ ENTRY OUTCOME
→ READY / PROMPT_READY / START...
```

For a material product or architecture WP, the Reviewer gate also requires:

```text
IMPLEMENTATION_AUDIT
ROADMAP_FIT_AUDIT
SPINE_FRESHNESS_AUDIT
```

The Reviewer compares the exact Builder output with relevant
`MASTER_ROADMAP_DELTA.md` entries, `MASTER_ROADMAP.md`, Product House layers
and applicable Spine authorities. The Reviewer reports alignment and stale or
missing promotion to the Planner; it remains a non-writer and does not enlarge
the Builder scope.

## 7. Independent local audit outcomes

The Reviewer issues one primary outcome:

- `LOCAL_AUDIT_PASS`: scope, evidence, logic, invariants, and verification are
  sufficient for this slice.
- `LOCAL_AUDIT_HOLD`: missing proof or bounded correction is required.
- `LOCAL_AUDIT_FAIL`: the implementation violates the Work Order, a critical
  invariant, or safety boundary.

After `LOCAL_AUDIT_HOLD` or `LOCAL_AUDIT_FAIL`, the Single Writer must not
proceed to the next micro-WP. Corrections use forward commits and return with a
new packet.

## 8. Remote checkpoint rule

The repository CI workflow currently runs on:

- pushes to `main`; and
- pull requests targeting `main`.

Therefore a normal push to a feature branch **without an open PR** is a remote
backup/checkpoint, not CI evidence.

After `LOCAL_AUDIT_PASS`:

```text
git push origin <feature-branch>
```

may be used to protect audited progress remotely. Do not call this `CI PASS`,
and do not open the Parent-WP PR merely to create a backup.

Once a PR exists, later feature-branch pushes may trigger the PR workflow; use
that integration event deliberately rather than as a routine micro-WP debugger.

### 8.1 Checkpoint handoff rule

A remote checkpoint is not complete as a cross-agent handoff until the active
snapshot can tell a new agent where audited work stops and what is authorized
next.

After each audited micro-WP remote checkpoint, refresh
`docs/agent_handoff/CURRENT.md` before handing prompt-writing or execution to a
different agent/session. Record at minimum:

```text
ACTIVE_PARENT_WP
ACTIVE_BRANCH
MAIN_BASE
LAST_AUDITED_MICRO_WP
LAST_AUDITED_CODE_HEAD
LAST_AUDIT
REMOTE_CHECKPOINT
PR_STATE
HOSTED_CI_STATE
NEXT_MICRO_WP
NEXT_AUTHORITY
STOP_STATE
```

`LAST_AUDITED_CODE_HEAD` and `REMOTE_CHECKPOINT` identify the code checkpoint
that passed independent audit. A later documentation-only handoff commit may
advance the feature branch beyond that SHA; it must not be misreported as a new
audited code head. The next agent resolves the exact live branch `HEAD` from
Git and verifies that the last audited code head remains an ancestor.

If the active snapshot, live Git, and live GitHub disagree materially, return
`ENTRY_HOLD` and reconcile the handoff before generating or executing the next
technical Work Order.

#### 8.1.1 Canonical checkout identity

Every Builder checkpoint and Reviewer audit must carry the same identity proof,
independent of repository name or branch label:

```text
CANONICAL_CHECKOUT_EXPECTED
EXPECTED_ORIGIN_REPOSITORY
BUILDER_GIT_TOPLEVEL
BUILDER_GIT_DIR
BUILDER_GIT_COMMON_DIR
BUILDER_ORIGIN
CHECKOUT_IDENTITY_GATE = PASS | ENTRY_HOLD
```

The Reviewer independently records `REVIEWER_GIT_TOPLEVEL`,
`REVIEWER_GIT_DIR`, `REVIEWER_GIT_COMMON_DIR` and `REVIEWER_ORIGIN`, then
cross-checks the expected path and repository identity before exact-object
claims. Distinct failure classes are `WRONG_CHECKOUT`, `WRONG_BRANCH`,
`WRONG_HEAD`, `AUDIT_OBJECT_ABSENT` and `ACTUAL_BASELINE_DRIFT`.
`WRONG_CHECKOUT` is an entry hold and must not be collapsed into the other
classes.

When the next governed unit or a takeover is about to begin, the
`LATEST_WP_SPINE_SYNC_AUDIT` packet must be complete and `PASS`; a remote
checkpoint or Micro POST alone does not establish this continuity result.

### 8.2 CURRENT write authority and Builder handoff discipline

`CURRENT.md` is the active handoff/transition authority and is conditionally
writable by the active `BUILDER_SINGLE_WRITER` only when it is in the approved
`WRITE_SCOPE`, a governed transition trigger exists, and each fact has resolved
evidence and authority provenance. The Builder may record observable execution
facts and already-resolved Reviewer, Planner or Human decisions from exact
evidence, but may not originate them:

```text
RECORD_AUTHORITY != ORIGINATE_AUTHORITY
CURRENT_UPDATE_FREQUENCY = GOVERNED_STATE_TRANSITION_FREQUENCY
CURRENT_UPDATE_FREQUENCY != COMMAND_FREQUENCY
```

CURRENT is not a command, test, edit or chat diary. Large-Batch stage progress
does not require a refresh unless a material transition, handoff or blocker
occurs.

The Builder refreshes `CURRENT.md` only at these governed state transitions:

- an audited micro-WP has received independent `PASS` and a remote checkpoint;
- a material blocker or scope-invalidating finding is discovered;
- work crosses an agent or session boundary;
- Parent merge or closeout occurs.

Do not refresh it for each file edit, test run, unaudited progress update,
speculative idea, or chat narration. A handoff must be short, factual,
evidence-backed and actionable, identifying at minimum:

```text
ACTIVE_PARENT_OR_MICRO_WP
PROVEN_COMPLETE
LAST_AUDITED_CODE_HEAD
VERIFICATION_STATE
OPEN_BLOCKERS
SCOPE_BOUNDARIES
EXACTLY_ONE_NEXT_ACTION
NEXT_AUTHORITY
```

Keep `LAST_AUDITED_CODE_HEAD` distinct from any later documentation or handoff
commit `HEAD`. The governed flow is:

```text
IMPLEMENT
→ VERIFY
→ COMMIT
→ INDEPENDENT AUDIT
→ AUDIT PASS
→ REMOTE CHECKPOINT
→ REFRESH CURRENT
→ HANDOFF READY
```

While the same Approval Lease remains active and work is ordinary editing or
testing, do not refresh `CURRENT.md`. These invariants apply:

```text
HANDOFF != DIARY
HANDOFF != ROADMAP
HANDOFF != REVIEW REPORT
HANDOFF != CHAT SUMMARY
```

## 8.3 Documentation lifecycle and tiered PRE/POST state

Every Parent WP and Micro-WP has a bounded PRE and POST state. The lifecycle
checks the required documents at each governed transition, but `ALWAYS CHECK
!= ALWAYS MODIFY`.

```text
PRE_CURRENT
→ IMPLEMENT / VERIFY / COMMIT
→ INDEPENDENT AUDIT
→ REMOTE CHECKPOINT when applicable
→ POST_CURRENT
→ HANDOFF READY
```

The document classes are:

- **CURRENT AUTHORITY** — active execution and transition state;
  `docs/agent_handoff/CURRENT.md` is the primary example.
- **HISTORICAL SNAPSHOT** — an as-of record preserved under
  `docs/agent_handoff/history/`; it is non-normative after capture.
- **DURABLE CONTRACT** — normative rules that remain in force until approved
  governance changes them, including `AGENTS.md`, `OPERATING_MODEL.md`, this
  contract, and `MASTER_ROADMAP.md`.

Strategic blueprints, merged durable memory, material feedback and systemic
lessons are distinct evidence/authority classes; none silently replaces
`CURRENT.md` or live Git/GitHub.

Parent PRE/POST requires `CURRENT.md` and a history snapshot. A Micro-WP
requires lightweight PRE/POST `CURRENT.md` state; history is not default.
Full history is required for takeover, material interruption, architecture
transition, major recovery, Parent closeout or material scope invalidation.
Roadmap and project memory are checked every Parent but changed only on their
defined lifecycle triggers. Feedback changes only for material decisions; a
systemic lesson changes `LESSONS.md` only when the lesson is durable.

Minimum state schemas are bounded, not diary formats. Micro PRE supports
`ACTIVE_PARENT_WP`, `ACTIVE_MICRO_WP`, `ACTIVE_BRANCH`, `MICRO_STATE`,
`ENTRY_HEAD`, `OBJECTIVE`, `SCOPE_BOUNDARIES`,
`ARCHITECTURE_LAYER_CONTRACT`, `OPEN_BLOCKERS`, `PRE_WP_DOC_SYNC`,
`EXACTLY_ONE_NEXT_ACTION` and `NEXT_AUTHORITY`. Micro POST supports
`ACTIVE_PARENT_WP`, `LAST_COMPLETED_MICRO_WP`, `MICRO_STATE`, `FINAL_HEAD`,
`LAST_AUDITED_CODE_HEAD`, `VERIFICATION_STATE`, `PROVEN_COMPLETE`,
`OPEN_BLOCKERS`, `REMOTE_STATE`, `HOSTED_CI_STATE`, `POST_WP_DOC_SYNC`,
`EXACTLY_ONE_NEXT_ACTION` and `NEXT_AUTHORITY`. Parent PRE/POST extends these
with `PRODUCT_FRONTIER`, `PARENT_OBJECTIVE`, `DEPENDENCIES`, `MICRO_WP_PLAN`,
`CAPABILITY_MATURITY_CHANGE`, `ROADMAP_IMPACT`,
`MEMORY_PROMOTION_REQUIRED`, `LESSON_PROMOTION_REQUIRED`, `RELEASE_IMPACT`
and `NEXT_FRONTIER`.

For a triggered Micro POST or remote checkpoint handoff, include the
`LATEST_WP_SPINE_SYNC_AUDIT` result (or record the required `HOLD`) before
opening the next governed entry; the audit supplements, rather than replaces,
the bounded Micro POST fields.

There is one semantic meaning per active machine-readable key in `CURRENT.md`.
Historical values use explicit namespaced keys and must not override the active
checkpoint for a simple parser. `LAST_AUDITED_CODE_HEAD` remains distinct from
later documentation or handoff commits.

Before `HANDOFF_READY`, the active Delta and document gates must be recorded:

```text
ROADMAP_DELTA_CHECK = PASS
DOC_FRESHNESS_STATE = PASS | accepted STALE_NONBLOCKING
SPINE_SYNC_STATE = PASS
```

The Delta is checked at three bounded points:

```text
PRE-WP  → identify relevant Delta entries and verify the Delta baseline
MID-WP  → reconcile on a material clarification, scope/architecture signal,
           source-model mismatch, or behavior that looks wrong despite green tests
POST-WP → answer relevance, satisfaction/partiality/invalidation, new Delta
           candidates, and whether promotion/removal is required
```

`MASTER_ROADMAP_DELTA.md` stages unresolved evolution and does not silently
override `MASTER_ROADMAP.md`; material conflict is `ROADMAP_CONFLICT = YES`
and routes to Planner/Human authority with `ENTRY_HOLD`.

### 8.3.1 Self-referential terminal sync

When a terminal handoff records the completion of the transition that writes
it, apply this narrow, non-recursive rule:

1. Live Git/GitHub is the volatile merge-state authority.
2. Material merge state must be reconciled before subsequent governed technical
   execution receives authority.
3. A docs-only PR whose purpose is reconciling the immediately preceding merge
   does not require another standalone docs PR solely to record its own merge.
4. The terminal-sync PR's own merge SHA/PR identity may temporarily remain
   represented only by live Git/GitHub.
5. At the next governed Parent/WP/technical-entry transition, CURRENT must
   reconcile that terminal-sync PR before new Builder authority.
6. The exception applies only to that terminal-sync PR's own volatile
   integration identity.
7. It does not permit stale ACTIVE_PARENT, ACTIVE_MICRO, WRITER, SCOPE,
   AUTHORITY, COMPLETION, NEXT_ACTION or BLOCKER state.
8. Any materially wrong active state is `HANDOFF_STALE → ENTRY_HOLD`.
9. The exception cannot hide a material merge conflict, failed CI, failed audit
   or Human-decision boundary.

The sync still writes only authorized handoff/Spine files, preserves audited
heads, records one next action and verifies key uniqueness, scope, diff and
tree. It stops rather than starting or authorizing another WP.

Concrete source findings must be reconciled against Git objects when available;
an audit report is evidence, not source-object authority. When a generic
abstraction wraps a legacy path, review the compatibility seam:

```text
OLD CONTRACT → ADAPTER / COMPATIBILITY BOUNDARY → NEW GENERIC CONTRACT
```

Passing tests alone does not prove legacy compatibility.

### 8.4 Post-merge freshness and strict handoff gate

The governed freshness transitions are:

```text
PARENT PRE → MICRO PRE → AUDITED REMOTE CHECKPOINT → MICRO POST
→ AGENT/SESSION HANDOFF → PARENT POST → PR/MERGE TRANSITION
→ POST-MERGE RECONCILIATION → NEXT PARENT ENTRY
```

During post-merge reconciliation, check applicable `KNOWN_FAILURE_MODES`,
`FEEDBACK_LEDGER` and `LESSONS` triggers. Preserve
`ALWAYS CHECK != ALWAYS MODIFY`.

Post-merge reconciliation also runs the triggered
`LATEST_WP_SPINE_SYNC_AUDIT` before selecting the next Parent or Micro-WP;
live main, the merged object, `CURRENT.md`, Delta and Spine must reconcile.

After `PR MERGED`, verify live `main`, reconcile `CURRENT.md`, close the
merged Parent state, check roadmap maturity and project-memory promotion,
resolve exactly one next action, and leave the handoff ready. If
`CURRENT.md` still claims not merged after live merge, mark
`HANDOFF_STALE` and return `ENTRY_HOLD` before technical work.

Cross-agent/session handoffs must include:

```text
ROADMAP_REVISION
ROADMAP_BASELINE_SHA
HANDOFF_CAPTURE_BASE
AUDIT_TARGET_CODE_HEAD
LIVE_GIT_HEAD
ACTIVE_PARENT_WP
ACTIVE_MICRO_WP
LAST_AUDITED_CODE_HEAD
LAST_AUDITED_DOC_HEAD
REMOTE_CHECKPOINT
PR_STATE
MERGE_STATE
VERIFICATION_STATE
HOSTED_CI_STATE
DOC_SYNC_STATE
PROVEN_COMPLETE
OPEN_BLOCKERS
SCOPE_BOUNDARIES
EXACTLY_ONE_NEXT_ACTION
NEXT_AUTHORITY
```

If any required answer is missing, `HANDOFF_READY = NO`. Chat is the
collaboration medium, files are organizational memory, and Git/GitHub is
repository truth. The handoff is not a transcript.

## 9. Parent Integration Gate

Before opening the Parent-WP PR, run the minimum complete cumulative
verification required by the Work Order and CI Fitness Contract.

Default cumulative evidence includes:

1. targeted regressions for the complete changed capability;
2. full `python -m pytest` when required by repository baseline policy;
3. `python -m ruff check .`;
4. `git diff --check` and changed-file review;
5. test collection integrity;
6. Alembic single-head/migration checks when schema changes exist;
7. Golden/read-only real-file acceptance when the Work Order requires it;
8. cumulative CodeGraph impact review;
9. docs, `CHANGELOG.md`, project memory, and handoff consistency when relevant;
10. clean-tree evidence before final delivery.

The final local audit reviews the complete Parent-WP delta, not merely the last
micro-WP.

The cumulative Parent gate includes a triggered
`LATEST_WP_SPINE_SYNC_AUDIT`; unresolved continuity or role drift is an
`ENTRY_HOLD` even when the cumulative tests pass.

## 10. Hosted-CI temporary waiver

A hosted-CI waiver is permitted only when CI cannot start because of a verified
infrastructure/account condition, not because tests are failing.

Record the state exactly:

```text
HOSTED_CI = INFRASTRUCTURE_UNAVAILABLE
CI_WAIVER = ACTIVE
LOCAL_VERIFICATION = PASS
INDEPENDENT_AUDIT = PASS
PENDING_RETRO_CI = YES
```

Never transform this state into `CI = PASS`.

The default hosted-CI gate returns only when GitHub Actions quota is restored
and the required workflow can execute normally. Until both conditions hold,
the mode is `TEMPORARY_LOCAL_STAGED_INTEGRATION`; no standing future waiver is
created. Any later exception requires explicit Human Authority.

Under the waiver:

- local verification remains mandatory;
- independent audit remains mandatory;
- Human merge approval remains mandatory;
- tests must not be weakened to compensate for missing hosted CI;
- each merged Parent WP accrues explicit retro-CI debt.

## 11. Retro-CI debt

Every Parent WP merged under the waiver remains:

```text
PENDING_RETRO_CI = YES
```

until hosted CI is restored and the cumulative waiver range has been verified.

The range is:

```text
LAST_KNOWN_FULLY_GREEN_HEAD
→ all waiver merges
→ current main
```

Track enough commit/WP evidence in `CURRENT.md` and future handoffs to identify
this range without relying on chat history.

## 12. CI recovery

When hosted CI becomes available again, execute a bounded CI Recovery Work
Package over the complete waiver range.

Recovery must include:

- current required hosted matrix;
- full regression;
- Ruff/code-quality gate;
- migration integrity for cumulative schema changes;
- WP-specific targeted regressions;
- Golden/read-only acceptance required by cumulative business changes;
- independent cumulative diff/risk audit.

Recovery result is exactly one of:

```text
CI_RECOVERY_PASS
CI_RECOVERY_HOLD
CI_RECOVERY_FAIL
```

Only `CI_RECOVERY_PASS` closes the corresponding `PENDING_RETRO_CI` debt.

## 13. Release gate

While:

```text
PENDING_RETRO_CI > 0
```

official Team Bid release is blocked.

Development, local verification, feature-branch checkpoints, review, PR, and
Human-approved merges may continue under the waiver, but the following remain
blocked unless the Human later approves a separate bounded release exception:

- official annotated version tag;
- GitHub Release;
- publish to `Crawler tool\Current`;
- Team Bid Reference publication;
- official installer release publication.

## 14. CI restored mode

When hosted CI is healthy again, keep Local Staged Integration as the normal
development model:

```text
micro-WP local verification
→ independent local audit
→ remote feature checkpoint
→ checkpoint handoff refresh
→ Parent Integration Gate
→ Draft PR
→ hosted CI
→ exact-head independent audit
→ Human merge
```

Hosted CI returns to its intended role: integration/environment verification,
not a debugging loop for every small change.

## 15. Documentation hierarchy

```text
LAW
→ Operating Model
→ Local Staged Integration Contract
→ Parent Work Order
→ Micro-WP
→ Tool/plugin procedure
```

`AGENTS.md` remains concise and constitutional. This contract owns the detailed
procedure and may evolve only without violating higher authority.
