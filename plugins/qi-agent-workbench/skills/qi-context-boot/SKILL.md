---
name: qi-context-boot
description: Read-only QI checkout, role, and context orientation before delegated work.
---

# QI Context Boot

Use before planning, building, or reviewing. Read the current `AGENTS.md`, Operating Model, Roadmap, Roadmap Delta, `CURRENT.md`, relevant Spine records, and live Git state. Select the required read mode; do not treat a copied handoff as Git authority.

QI_CONTEXT_BOOT = READ_ONLY
BOOT_RESULT = READY | ENTRY_HOLD

Resolve role authority only through this governed chain:

`Human explicit assignment -> approved Work Order -> governed CURRENT`.

`MODEL_NAME != AGENT_ROLE`; `RUNTIME/MODEL/VENDOR/TOOL` identity is never role evidence. If role evidence is absent, `MODEL_NAME_ROLE = ENTRY_HOLD`. Never infer authority from model/tool/runtime/vendor.

Verify canonical checkout path, Git top-level/common directory, origin, branch, declared baseline, role evidence, scope, and protected dirty paths. Preserve Human A0, Planner, Builder, and independent Reviewer authority. Missing, conflicting, or stale role/baseline/scope evidence fails closed.

If `CURRENT_HEAD != LIVE_GIT_HEAD`, treat the active handoff as stale: `STALE_CURRENT = ENTRY_HOLD`; `CURRENT_ONLY = ENTRY_HOLD`. CURRENT is not Git authority and cannot make a stale object ready.

If candidate scope includes `src/qi_crawler/`, `alembic/`, GUI, or API paths during this read-only boot, `PRODUCT_PATH_LEAKAGE = ENTRY_HOLD`.

The boot has no authority to edit, commit, push, merge, or release; it cannot perform Spine mutation or role self-assignment. A successful read-only boot reports `CONTEXT_ENTRY_READY` and `IMPLEMENTATION_AUTHORIZED = NO`.

Required output: `BOOT_REPORT` with `PASS`, `HOLD`, or `NEEDS_REPLAN`, read mode, verified identity/baseline, authority source, context sources, and exactly one next authority.
