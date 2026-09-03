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

python_behavior_change → qi-context-boot + qi-impact-map + qi-python-change + qi-evidence-check + qi-review-handoff
bug_or_test_failure → qi-context-boot + qi-impact-map + systematic-debugging + test-driven-development + qi-evidence-check + qi-review-handoff
migration_schema → qi-context-boot + qi-impact-map + canonical migration/data-safety contracts + qi-evidence-check + qi-review-handoff
governance_docs → qi-context-boot + qi-task-envelope + qi-evidence-check + qi-review-handoff
security_bounded → qi-context-boot + qi-impact-map + Work-Order-approved security skill/tool + qi-evidence-check + qi-review-handoff

`NO_EXTERNAL_MCP_AUTOMATION = ENTRY_HOLD`: no router path may introduce external connectors, MCP, automation, scheduling, merge, release, or a second writer.

Required output is `TASK_ENVELOPE` containing exactly the ten declared fields. Resolve any Work Order/envelope mismatch to `ENTRY_HOLD` and retain `NEXT_AUTHORITY` from the canonical authority chain.

Use [the template](../../references/task-envelope-template.md).
