---
name: qi-review-handoff
description: Prepare an exact-object QI handoff for an independent reviewer.
---

# QI Review Handoff

Prepare evidence for an independent Reviewer; the Builder never audits its own work. Identify the exact canonical checkout, base and head objects, scope, invariants, risks, evidence, and claims to challenge. The reviewer directly examines the Git range rather than accepting a report as authority.

## Independent exact-object boundary

The handoff must provide the contract, exact `BASE_SHA` and `HEAD_SHA`, changed-path diff, and machine evidence so an independent Reviewer can reproduce the result. Builder reasoning and claims are context only.

`REVIEWER_INDEPENDENT = YES` and `REVIEWER_EDIT = REFUSE`: the Reviewer audits the candidate and must not edit audited source, tests, CURRENT, Spine, or remote state. Any requested repair is a `HOLD` returned to Planner.

The terminal sentinel is mandatory: `HANDOFF_SENTINEL = END OF HANDOFF`.

Use `BLOCKED` for an unresolved execution blocker and `NEEDS_REPLAN` when scope, architecture, or authority must change. Neither status may be concealed as progress. Preserve Human A0, Planner, Builder, and Reviewer boundaries.

Required output: `REVIEW_HANDOFF` with `ROLE`, `STATUS`, `PARENT_WP`, `MICRO_WP`, `BASE_SHA`, `HEAD_SHA`, `CHANGED_PATHS`, `CONTRACT_COVERAGE`, `VERIFICATION`, `DEVIATIONS`, `UNRESOLVED_FINDINGS`, `SPINE_IMPACT`, `GIT_STATE`, `EXACTLY_ONE_NEXT_ACTION`, and `NEXT_AUTHORITY`, followed by `END OF HANDOFF`. Use [the template](../../references/handoff-template.md).
