# Local Staged Integration + Remote Checkpoint Design

## Status

Approved by Human for immediate governance rollout under `WP-GOV-LSI-01`.
This document changes development governance only. It does not change product
behavior, runtime code, database schema, CI workflow configuration, version,
or release artifacts.

## Problem

The repository historically used GitHub-hosted CI on each PR update as both an
integration verifier and, in practice, a frequent feedback loop. That creates
quota burn and delays review when small corrections repeatedly trigger the full
matrix. It also allows architectural drift to grow before independent review.

GitHub Actions is temporarily unavailable because account billing/spending
limits prevent jobs from starting. The repository still needs a governed path
for safe development without weakening local verification or Human authority.

## Goals

1. Shift independent review left to small auditable implementation slices.
2. Preserve remote backup/checkpoints without triggering CI for every slice.
3. Keep machine execution evidence separate from independent reasoning audit.
4. Use GitHub CI primarily as a parent-work-package integration/environment
   gate rather than a debugger for every micro-change.
5. Track all merges made while hosted CI is unavailable as explicit retro-CI
   debt and block official Team Bid release until that debt is cleared.
6. Preserve a readable, non-rewritten audit trail through forward corrections.

## Non-goals

- Do not remove or weaken existing CI jobs.
- Do not change `.github/workflows/ci.yml` in this Work Package.
- Do not make ChatGPT a substitute runtime runner.
- Do not permit Codex/Single Writer to self-approve implementation.
- Do not authorize official release while retro-CI debt is open.
- Do not change product code, database schema, or version.

## Authority model

The existing laws remain authoritative.

- `HUMAN_AUTHORITY`: approves parent WP scope, merge, and release decisions.
- `PLANNER_ARCHITECT`: designs and decomposes the approved parent WP.
- `BUILDER_SINGLE_WRITER`: is the only writer for one active micro-WP.
- Local machine execution supplies temporary `MACHINE_VERIFIER` evidence when
  hosted CI is unavailable.
- `REVIEWER_AUDITOR`: independently inspects evidence, diff, scope, invariants,
  risks, and test adequacy. The Reviewer is not a runtime CI runner.
- GitHub CI remains the clean-environment/multi-platform integration verifier
  when available.

## Parent-WP flow

```text
Human approves Parent WP
→ Planner decomposes bounded micro-WPs
→ Single Writer implements one micro-WP
→ local verification
→ local commit
→ LOCAL_REVIEW_PACKET
→ STOP_FOR_INDEPENDENT_LOCAL_AUDIT
→ Reviewer PASS or HOLD
→ on PASS: push feature branch as remote checkpoint, without PR
→ next micro-WP
→ parent integration verification
→ final local audit
→ final feature-branch push
→ open Draft PR
→ hosted CI when available
→ exact-head independent audit
→ Human merge approval
```

## Remote checkpoint rule

The current CI workflow runs on pushes to `main` and pull requests targeting
`main`. A normal push to a feature branch with no PR is therefore a remote
backup/checkpoint and must not be described as CI evidence.

After `LOCAL_AUDIT_PASS`, the audited commit may be pushed to the existing
feature branch. Do not open the Parent WP PR until the Parent Integration Gate
is reached unless Human explicitly changes the plan.

## Commit freeze and forward correction

Once a commit has received `LOCAL_AUDIT_PASS`, do not silently amend, rebase,
force-rewrite, or otherwise replace that audited commit during normal parent-WP
execution.

If a later slice exposes a defect or integration need in an earlier audited
slice, create a new forward-correction commit whose purpose is explicit.
Example:

```text
micro-A
micro-B
fix(A-B integration)
```

History cleanup before PR is not the default. It requires explicit Work Order
permission and Human approval when it would rewrite audited history.

## Parent-WP sizing

Target 4–6 independently auditable slices. This is a heuristic, not a hard
limit. Trigger `SPLIT_REVIEW_REQUIRED` when either condition holds:

- the parent WP grows beyond six meaningful slices; or
- the work crosses multiple major architectural or migration boundaries such
  that integration risk is no longer bounded.

The Reviewer then returns either `CONTINUE_PARENT` or `SPLIT_PARENT_WP` with a
reasoned boundary.

## Local Review Packet

Every micro-WP stops with this evidence packet:

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

For successful commands, concise summaries plus exact command and exit code are
preferred. Do not dump large raw logs, binary fixtures, databases, or generated
artifacts. For failures, include the relevant traceback/error excerpt needed to
diagnose the failure.

## Independent local audit outcomes

The Reviewer returns exactly one primary outcome:

- `LOCAL_AUDIT_PASS`: evidence and implementation satisfy the micro-WP.
- `LOCAL_AUDIT_HOLD`: correction or missing proof is required before progress.
- `LOCAL_AUDIT_FAIL`: implementation violates the approved contract or a
  critical invariant and must be corrected before progress.

The Single Writer does not proceed to the next micro-WP after HOLD/FAIL.

## Parent Integration Gate

Before opening a PR, the Parent WP must run the minimum complete cumulative
verification appropriate to its CI Fitness Contract. The default includes:

- targeted cumulative regressions for changed capability;
- full `python -m pytest` when required by repository baseline policy;
- `python -m ruff check .`;
- `git diff --check`;
- test collection integrity;
- migration/single-head verification when schema changes exist;
- Golden/read-only real-file acceptance when the Work Order requires it;
- cumulative CodeGraph impact review;
- docs, memory, changelog, and handoff consistency appropriate to scope;
- clean-tree evidence before final delivery.

## Temporary hosted-CI waiver

When hosted CI cannot start because of a verified infrastructure/account
condition, record:

```text
HOSTED_CI = INFRASTRUCTURE_UNAVAILABLE
CI_WAIVER = ACTIVE
LOCAL_VERIFICATION = PASS
INDEPENDENT_AUDIT = PASS
PENDING_RETRO_CI = YES
```

Never relabel this state as `CI = PASS`.

A Human may approve merge under this bounded waiver after local machine
verification and independent audit. The waiver does not permit weakening tests
or bypassing material HOLD findings.

## Retro-CI debt and recovery

Every merged Parent WP under the waiver remains `PENDING_RETRO_CI = YES` until
hosted CI returns and the cumulative waiver range is re-verified.

Recovery range:

```text
LAST_KNOWN_FULLY_GREEN_HEAD
→ all waiver merges
→ current main
```

Recovery verification must include the repository's hosted matrix and the
WP-specific regressions/migration/Golden checks required by the cumulative
change set. Recovery result is one of:

- `CI_RECOVERY_PASS`
- `CI_RECOVERY_HOLD`
- `CI_RECOVERY_FAIL`

Only `CI_RECOVERY_PASS` may close the corresponding retro-CI debt.

## Release gate

`PENDING_RETRO_CI > 0` blocks official Team Bid release actions. While debt is
open, development, local verification, feature-branch checkpoints, review, PR,
and Human-approved merges may continue under the waiver, but the following are
blocked unless a later explicit Human decision establishes a different bounded
release exception:

- official version tag;
- GitHub Release;
- publish to `Crawler tool\Current`;
- Team Bid Reference publication;
- official installer release publication.

## Documentation hierarchy

Detailed procedure belongs in this operating contract, not inside the
constitutional laws. Hierarchy remains:

```text
LAW
→ Operating Model
→ Local Staged Integration Contract
→ Parent Work Order
→ Micro-WP
→ Tool/plugin procedure
```

`AGENTS.md` should reference this contract concisely rather than duplicate the
full procedure.

## Acceptance criteria

`WP-GOV-LSI-01` is accepted when repository governance clearly proves all of
the following:

- constitutional role separation remains unchanged;
- local machine execution and independent audit are distinct authorities;
- remote feature-branch checkpoints do not count as CI evidence;
- audited commits use forward correction instead of silent rewriting;
- `LOCAL_REVIEW_PACKET` carries machine-verifiable provenance;
- parent sizing uses a 4–6 slice target with `SPLIT_REVIEW_REQUIRED` heuristic;
- hosted-CI waiver is explicit and cannot be reported as CI PASS;
- retro-CI debt is tracked and recoverable;
- official release is blocked while retro-CI debt is open;
- no product/runtime/migration/CI-workflow/version changes are introduced by
  this governance Work Package.
