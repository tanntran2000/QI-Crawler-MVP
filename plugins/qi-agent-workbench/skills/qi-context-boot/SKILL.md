---
name: qi-context-boot
description: Read-only QI checkout, role, and context orientation before delegated work.
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

If `CURRENT_HEAD != LIVE_GIT_HEAD`, treat the active handoff as stale: `STALE_CURRENT = ENTRY_HOLD`; `CURRENT_ONLY = ENTRY_HOLD`. CURRENT is not Git authority and cannot make a stale object ready.

If candidate scope includes `src/qi_crawler/`, `alembic/`, GUI, or API paths during this read-only boot, `PRODUCT_PATH_LEAKAGE = ENTRY_HOLD`.
FORBIDDEN_PRODUCT_PATHS = src/qi_crawler/...; alembic/...

WHAT_I_AM_ALLOWED_TO_DO = READ_CONTEXT_ONLY
WHAT_I_AM_NOT_ALLOWED_TO_DO = EDIT, COMMIT, PUSH, MERGE, RELEASE, SPINE_MUTATION, ROLE_SELF_ASSIGNMENT

Boot may not edit, commit, push, merge, or release.
The boot has no authority to edit, commit, push, merge, or release; it cannot perform Spine mutation or role self-assignment. A successful read-only boot reports `CONTEXT_ENTRY_READY` and `IMPLEMENTATION_AUTHORIZED = NO`.

Required output: `BOOT_REPORT` with `READY_STATE = READY | ENTRY_HOLD`, `WHAT_I_AM_ALLOWED_TO_DO`, `WHAT_I_AM_NOT_ALLOWED_TO_DO`, `EXACTLY_ONE_NEXT_ACTION`, and `NEXT_AUTHORITY`.
