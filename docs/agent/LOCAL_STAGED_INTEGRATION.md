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
  diff, test adequacy, and the validity of supplied evidence.
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
→ LOCAL_REVIEW_PACKET
→ STOP_FOR_INDEPENDENT_LOCAL_AUDIT
→ Reviewer PASS / HOLD / FAIL
→ on PASS: push feature branch as remote checkpoint, without PR
→ refresh active checkpoint handoff
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

## 4. Micro-WP sizing and Parent-WP split review

Target **4–6 independently auditable micro-WPs** per Parent WP. This is a
heuristic, not a hard numeric law.

Trigger:

```text
SPLIT_REVIEW_REQUIRED
```

when either:

- the Parent WP exceeds six meaningful slices; or
- it crosses multiple major architectural or migration boundaries such that
  cumulative integration risk is no longer bounded.

The Reviewer returns one of:

```text
CONTINUE_PARENT
SPLIT_PARENT_WP
```

with the architectural reason.

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

Every micro-WP must stop with this packet:

```text
LOCAL_REVIEW_PACKET
===================
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

PATCH:
unified diff or bounded relevant patch

NEXT:
STOP_FOR_INDEPENDENT_LOCAL_AUDIT
```

For successful commands, include the exact command, concise result, runtime
when useful, and exit code. Do not dump large successful pytest logs, binary
fixtures, databases, caches, or generated artifacts into the packet.

For a failure, include the relevant traceback/error excerpt and the command
that produced it.

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

### 8.2 Builder handoff discipline

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
