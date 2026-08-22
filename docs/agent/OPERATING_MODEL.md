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
