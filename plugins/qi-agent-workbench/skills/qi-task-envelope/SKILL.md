---
name: qi-task-envelope
description: Construct a short, bounded QI delegation envelope without changing authority.
---

# QI Task Envelope

TASK_ENVELOPE = SUBORDINATE_DERIVED_VIEW
TASK_ENVELOPE_FIELDS = MISSION, ASSIGNED_ROLE, BASELINE, SCOPE, EXCLUSIONS, INVARIANTS, ACCEPTANCE, REQUIRED_SKILLS_TOOLS, VERIFICATION, NEXT_AUTHORITY

Derive a compact envelope only from an approved canonical Work Order and a successful read-only Boot. `TASK_ENVELOPE != WORK_ORDER`: the canonical Work Order remains authority, while this envelope is a delivery aid and never a competing plan or approval.

The envelope must preserve role, baseline, scope, authority, exclusions, invariants, acceptance, required skills/tools, verification, and next authority exactly. `ROLE_BASELINE_SCOPE_AUTHORITY_MISMATCH = ENTRY_HOLD`; missing, conflicting, or stale evidence fails closed.

`ENVELOPE_SCOPE_MISMATCH = ENTRY_HOLD`. An envelope may not widen, reinterpret, or silently absorb the Work Order scope. The router never grants edit scope; it only names candidate skills and references.

Task-family router:

governance_docs → qi-context-boot + qi-task-envelope + qi-evidence-check + qi-review-handoff; no CodeGraph/TDD by default
python_behavior_change → qi-context-boot + qi-impact-map when materially useful + qi-python-change + test-driven-development + qi-evidence-check + qi-review-handoff
bug_or_test_failure → qi-context-boot + systematic-debugging + qi-impact-map when relevant + test-driven-development + qi-evidence-check + qi-review-handoff
migration_schema → qi-context-boot + qi-impact-map when needed + canonical migration/data-safety contracts + exact copy/data boundary + qi-evidence-check + qi-review-handoff
external_public_research → qi-context-boot + Agent Reach only when external access is explicitly authorized + qi-evidence-check
review → qi-context-boot + exact Git object + qi-evidence-check + qi-review-handoff + optional specialized read-only lenses
security_bounded → qi-context-boot + qi-impact-map when relevant + Work-Order-approved security skill/tool + qi-evidence-check + qi-review-handoff

ROUTER != AUTHORITY
SKILL != WORK_ORDER
TOOL != AUTHORITY

EXTERNAL_TOOL_REQUESTED
AUTHORIZED_BY_TASK?
CAPABILITY_REQUIRED?
APPROVED_TOOL_OR_FALLBACK?
CONTINUE / HOLD_DEPENDENT_CONTRACT

Never route an external tool merely because it is installed.

TOOL_UNAVAILABLE != AUTOMATIC_WP_HOLD
TOOL_APPLICABILITY = REQUIRED / OPTIONAL / NOT_APPLICABLE
FALLBACK_AUTHORIZED = YES / NO
FALLBACK_EQUIVALENCE = SUFFICIENT / INSUFFICIENT / NOT_APPLICABLE
OPTIONAL_TOOL_FAILURE = CONTINUE_WITH_LIMITATION
REQUIRED_TOOL_WITH_SUFFICIENT_AUTHORIZED_FALLBACK = CONTINUE_WITH_LIMITATION
REQUIRED_TOOL_WITHOUT_EQUIVALENT_FALLBACK = HOLD_DEPENDENT_CONTRACT

Do not claim equivalence where capabilities differ. Bounded manual caller,
import, and source analysis may replace CodeGraph for impact mapping. Reading
a screenshot is not equivalent to executing a real GUI runtime test.

Required output is `TASK_ENVELOPE` containing exactly the ten declared fields. Resolve any Work Order/envelope mismatch to `ENTRY_HOLD` and retain `NEXT_AUTHORITY` from the canonical authority chain.

Use [the template](../../references/task-envelope-template.md).
