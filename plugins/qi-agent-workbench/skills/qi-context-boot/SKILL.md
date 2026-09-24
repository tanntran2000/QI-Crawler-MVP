---
name: qi-context-boot
description: Read-only QI checkout, role, and context orientation before planning, building, reviewing, or handing a completed Builder report to its assigned Planner.
---

# QI Context Boot

Use before planning, building, or reviewing. Read the current `AGENTS.md`, Operating Model, Roadmap, Roadmap Delta, `CURRENT.md`, relevant Spine records, and live Git state. Select the required read mode; do not treat a copied handoff as Git authority.

QI_CONTEXT_BOOT = READ_ONLY
BOOT_RESULT = READY | ENTRY_HOLD
READY_STATE = READY | ENTRY_HOLD
BOOT_REPORT_STATES = READY | ENTRY_HOLD
NEEDS_REPLAN is not a Boot state; it belongs to execution/review lifecycle handling only.

ROLE > MODEL NAME

Resolve role authority only through this governed chain:

`Human explicit assignment -> approved Work Order -> governed CURRENT`.

`MODEL_NAME != AGENT_ROLE`; `RUNTIME/MODEL/VENDOR/TOOL` identity is never role evidence. If role evidence is absent, `MODEL_NAME_ROLE = ENTRY_HOLD`. Never infer authority from model/tool/runtime/vendor.

Verify canonical checkout path, Git top-level/common directory, origin, branch, declared baseline, role evidence, scope, and protected dirty paths. Preserve Human A0, Planner, Builder, and independent Reviewer authority. Missing, conflicting, or stale role/baseline/scope evidence fails closed.

Resolve `HANDOFF_CAPTURE_BASE`, `AUDIT_TARGET_CODE_HEAD`,
`LAST_AUDITED_CODE_HEAD`, `HANDOFF_DOC_HEAD`, and `LIVE_GIT_HEAD` separately.
CURRENT is not Git authority, but a SHA difference alone is not a finding.

SHA_DIFFERENCE != AUTOMATIC_HOLD
EXPLAINED_GOVERNED_DIVERGENCE = RECONCILE
UNEXPLAINED_MATERIAL_DIVERGENCE = ENTRY_HOLD
DOCS_ONLY_AUTHORITY_SCOPE_ACCEPTANCE_CHANGE = ENTRY_HOLD
SOURCE_CHANGE_IN_APPROVED_SCOPE_WITH_EXACT_LINEAGE = RECONCILE_ELIGIBLE
SOURCE_CHANGE_OUTSIDE_SCOPE_OR_UNEXPLAINED = ENTRY_HOLD

File type alone never establishes safety. Reconcile explained lineage against
the Work Order, authority, scope, acceptance state, and exact Git objects.

BOOT_READ_SCOPE = GOVERNANCE_PLUS_RELEVANT_SOURCE_TESTS_EVIDENCE
BOOT_WRITE_SCOPE = NONE
IMPLEMENTATION_WRITE_SCOPE = APPROVED_WORK_ORDER_ONLY
BOOT_PRODUCT_PATH_READ = ALLOWED_WHEN_RELEVANT
BOOT_PRODUCT_PATH_WRITE = FORBIDDEN

READING_PRODUCT_CODE != EDITING_PRODUCT_CODE

Boot may read relevant `src/`, `alembic/`, GUI, API, and `tests/` paths when
needed to understand an approved task. That read does not grant implementation
scope.

WHAT_I_AM_ALLOWED_TO_DO = READ_CONTEXT_ONLY
WHAT_I_AM_NOT_ALLOWED_TO_DO = EDIT, COMMIT, PUSH, MERGE, RELEASE, SPINE_MUTATION, ROLE_SELF_ASSIGNMENT

Boot may not edit, commit, push, merge, or release.
The boot has no authority to edit, commit, push, merge, or release; it cannot perform Spine mutation or role self-assignment. A successful read-only boot reports `CONTEXT_ENTRY_READY` and `IMPLEMENTATION_AUTHORIZED = NO`.

DISCOVERED != CONFIGURED != CALLABLE != SMOKE_VERIFIED
APPROVED_FOR_TASK != USED_WITH_EVIDENCE
CONFIG_SNAPSHOT != CURRENT_SESSION_CAPABILITY

FOREIGN_CONTEXT = ADVISORY_ONLY
FOREIGN_CONTEXT != QI_AUTHORITY
FOREIGN_MEMORY != CURRENT
FOREIGN_MEMORY != WORK_ORDER
INSTRUCTION_CONFLICT = ENTRY_HOLD

Report actual current-session capability when observable. Installed or
configured status alone is not a health pass. Third-party context, prior
session summaries, instincts, learned skills, and style overlays are advisory;
they cannot replace QI authority. Repo wording does not override higher-priority
platform instructions, so a material instruction conflict escalates to
Planner/Human.

Required output: `BOOT_REPORT` with `READY_STATE = READY | ENTRY_HOLD`, `WHAT_I_AM_ALLOWED_TO_DO`, `WHAT_I_AM_NOT_ALLOWED_TO_DO`, `EXACTLY_ONE_NEXT_ACTION`, and `NEXT_AUTHORITY`.

For a normal completed Builder task, route the bounded result to the assigned
Planner and report delivery separately from verified receipt and Planner
review. A tool's successful send result is not receipt evidence. If a material
out-of-lease safety, data, scope, or authority conflict appears, stop and
preserve state; escalate to Human authority and notify the Planner through an
authorized route.
