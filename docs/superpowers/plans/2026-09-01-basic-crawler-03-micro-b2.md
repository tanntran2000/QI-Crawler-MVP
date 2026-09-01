# Micro-B2 correction plan — operational revision transition

## Scope

This forward-only correction addresses the failed Micro-B2 implementation
audit at `6b71180c3f1c9c0c5cfbe93558bcb0f4cd204be8`. The initial audit found
`BC03-B02` partial, `BC03-B03` failed because acceptance advanced latest
immediately, `BC03-B04` failed because previous-only slots were classified as
removed without completeness evidence, and operational integration failed.

## Required contracts

- Human acceptance of a newer revision records an unresolved pending
  transition; `ACCEPTED_PENDING` never advances the operational latest.
- Pending transitions persist across restart and conflicting unresolved
  pending transitions fail closed.
- Explicit activation requires the exact pending candidate, an adjacent
  comparison artifact for the exact previous/candidate pair, and a newer
  candidate. Activation appends an immutable activation event.
- Adjacent comparison classifies previous-only slots as `UNKNOWN_RELATION`
  unless a complete new-source observation and non-empty completeness evidence
  are supplied; only then is `REMOVED_FROM_NEW_REVISION` allowed.
- Workspace and thin GUI/service adapters expose operational latest, relation,
  pending state, comparison, and explicit activation without becoming business
  authority. Existing Micro-B1 controlled intake is reused.

## TDD correction evidence

The granular RED evidence for the historical implementation was not captured
by the failed audit and must not be fabricated. During this correction each
behavior below will be added as a focused regression and run against the
failed head before its production fix; the plan records the required evidence
slots rather than claiming historical results:

`FIX-B03-01` pending acceptance; `FIX-B03-02` pending restart;
`FIX-B03-03` activation without comparison fails closed;
`FIX-B03-04` explicit activation advances latest;
`FIX-B04-01` incomplete previous-only is unknown;
`FIX-B04-02` complete previous-only with evidence is removed;
`FIX-INT-01` workspace latest; `FIX-INT-02` workspace relation;
`FIX-INT-03` GUI accept remains pending; `FIX-INT-04` GUI compare then
explicit activate.

For each behavior the implementation record must include the behavior ID,
exact RED command, expected and observed failure, root cause, and GREEN
command/result. Historical RED remains `FAIL / NOT_CAPTURED` where applicable.

## Verification and boundaries

The migration remains the single append-only operational revision event table
(`0020`); no `0021` is allowed unless the existing schema is proven
insufficient, in which case execution stops. Preserve exact releases and
previous documents, reuse B1 intake, and never infer or inherit Human or
source authority. No Micro-C, completeness, recovery, API or Team Bid pilot
work is included.

Required focused tests, full pytest, Ruff, pip check, diff check, and a clean
tracked tree are recorded in the final handoff. No push, PR, or merge is part
of this correction.