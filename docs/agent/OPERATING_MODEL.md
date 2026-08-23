# Operating Model

## Roles and authority

- **HUMAN_AUTHORITY** approves scope, decisions, merges, and release actions.
- **PLANNER_ARCHITECT** turns an approved request into a bounded Work Order;
  planning does not edit production code.
- **DOMAIN_REVIEWER** checks business meaning and source evidence.
- **REVIEWER_AUDITOR** checks scope, risk, and proof against the Work Order.
- **BUILDER_SINGLE_WRITER** is the only writer for a micro-Work Package.
- **MACHINE_VERIFIER** runs the required tests, lint, and repository checks.
- **Team Bid** supplies operational observations and explicit human decisions.

Roles describe authority, not a particular model or tool.

## Tool responsibilities

- Work Order = WHAT may change.
- CodeGraph = WHERE impact and dependencies exist.
- Superpowers = HOW the approved work is executed.

For applicable technical work, the auditable flow is:

```text
READ → VERIFY → ENTRY REVIEW → APPROVAL LEASE → CodeGraph impact discovery
→ relevant Superpowers process → implementation → verification-before-completion
→ audit
```

For incidents:

```text
systematic-debugging → root cause → CodeGraph-confirmed impact
→ TDD RED → minimal GREEN → verification
```

Plugin execution evidence is part of the machine/human audit record.

## Human collaboration

`docs/agent/HUMAN_COLLABORATION.md` records communication, language, context,
and reporting preferences. It complements this operating model and does not
override `AGENTS.md`, an approved Work Order, explicit Human decisions, or
verified repository/GitHub evidence.

## Execution protocol

1. Read the required memory and live repository state.
2. Produce an Entry Review with the Work Package, baseline, risks, and scope.
3. Wait for one human approval (the **Approval Lease**).
4. Execute bounded work under that lease; do not ask for command-by-command
   approval.
5. Stop and request re-approval if scope, baseline, writer, authority, or a
   material blocker changes.
6. Verify before claiming completion and update `CURRENT.md`.

Entry outcomes are:

- `ENTRY_CLEAR`: no material conflict; approval may be requested.
- `ENTRY_NOTE`: a non-blocking observation is recorded.
- `ENTRY_HOLD`: baseline, authority, or scope is unresolved; do not write.

## Local Staged Integration

The default development procedure for Parent Work Packages is defined in
`docs/agent/LOCAL_STAGED_INTEGRATION.md`.

The operating sequence is:

```text
Human-approved Parent WP
→ Planner decomposition
→ one Single Writer micro-WP
→ local Machine Verifier evidence
→ local commit
→ LOCAL_REVIEW_PACKET
→ STOP_FOR_INDEPENDENT_LOCAL_AUDIT
→ Reviewer PASS/HOLD/FAIL
→ PASS: feature-branch remote checkpoint without PR
→ next micro-WP
→ Parent Integration Gate
→ Draft PR
→ hosted CI when available
→ exact-head audit
→ Human merge
```

A remote feature-branch checkpoint is backup/provenance, not CI evidence.
Audited commits are preserved by default; later corrections use explicit
forward-correction commits instead of silently rewriting accepted history.

Target 4–6 independently auditable micro-WPs per Parent WP. If the work grows
beyond six meaningful slices or crosses multiple major architectural/migration
boundaries, trigger `SPLIT_REVIEW_REQUIRED` and decide `CONTINUE_PARENT` or
`SPLIT_PARENT_WP` before expanding further.

## Temporary hosted-CI unavailability

When hosted CI cannot start because of a verified infrastructure/account
condition, the local machine may temporarily supply `MACHINE_VERIFIER`
execution evidence. `REVIEWER_AUDITOR` remains an independent authority and
must not be described as the runtime CI runner.

A Human-approved merge under this waiver records:

```text
HOSTED_CI = INFRASTRUCTURE_UNAVAILABLE
CI_WAIVER = ACTIVE
LOCAL_VERIFICATION = PASS
INDEPENDENT_AUDIT = PASS
PENDING_RETRO_CI = YES
```

The state must never be reported as hosted `CI PASS`. When hosted CI returns,
a CI Recovery Work Package verifies the complete waiver range from the last
known fully green head through current `main`.

`PENDING_RETRO_CI > 0` blocks official Team Bid release/publish unless a later
explicit Human decision establishes a separate bounded exception.

## Release lifecycle

For a user-visible change, use this bounded sequence:

```text
user-visible change
→ release-impact assessment
→ version decision
→ implementation
→ tests
→ exact-head CI
→ independent audit
→ verified Windows build
→ runtime/data compatibility smoke
→ Human release approval
→ Git tag/GitHub Release
→ CURRENT
→ Team Bid Reference
```

`Implementation DONE` is not the same as `Team Bid RELEASED`. Historical
tags/releases are immutable identities; only an approved, verified release may
be presented as the latest Team Bid version.

During a hosted-CI waiver, implementation and Human-approved merges may follow
the Local Staged Integration exception, but the official release lifecycle does
not complete while retro-CI debt remains open.

## Collaboration boundaries

CodeGraph provides impact intelligence only; it is not edit authority.
Superpowers define execution discipline (for example TDD and verification),
not product scope. If a plugin or MCP tool is unavailable, use the safest
documented fallback and record the limitation. No tool may override the
approved Work Order, `AGENTS.md`, or human authority.

## Workspace and data

Use only the canonical checkout and one active short-lived branch. Keep
`.codegraph/`, sessions, credentials, runtime databases, documents, and
business workbooks local unless a Work Order explicitly authorizes a safe
derived artifact. Unknown files are kept.
