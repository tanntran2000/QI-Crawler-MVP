---
name: qi-evidence-check
description: Verify bounded QI work with fresh, truthful machine evidence.
---

# QI Evidence Check

Record pytest collection baseline before work. Run the Work Order's targeted and full pytest gates as applicable, then Ruff, `git diff --check`, and scope/name-status checks with finite per-job budgets. Investigate unexpected collection decreases and timeouts; do not mask a stall by extending a budget.

## Evidence classes

Every result is labeled as one of these distinct classes:

- `BASELINE / NEGATIVE PROOF`
- `TARGETED LOCAL`
- `FULL LOCAL`
- `RUFF / DIFF`
- `HOSTED CI`
- `UNVERIFIED CLAIM`
- `LIMITATION`

`BUILDER CLAIM != MACHINE EVIDENCE`. A narrative assertion is never promoted to a pass without the command, exact object, and captured result that can be independently checked. `UNVERIFIED_CLAIM = LIMITATION`; report the limitation explicitly instead of silently treating it as success.

Describe local evidence as local; a push is not hosted CI and no claim of completion is made without fresh evidence. Fail closed on missing role, baseline, scope, or verification contract. Human, Planner, Builder, and Reviewer authority remains separate.

Treat tool states independently: `DISCOVERED`, `CONFIGURED`, `CALLABLE`,
`SMOKE_VERIFIED`, `APPROVED_FOR_TASK`, and `USED_WITH_EVIDENCE`.
`CONFIG_SNAPSHOT != CURRENT_SESSION_CAPABILITY` and
`CONFIGURED != SMOKE_VERIFIED`.

For each material invocation record `TOOL_OR_SKILL`, `PURPOSE`,
`TOOL_APPLICABILITY`, `INVOCATION`, `RESULT`, `FALLBACK`,
`FALLBACK_AUTHORIZED`, `FALLBACK_EQUIVALENCE`, `IMPACT_RADIUS`, `EDIT_RADIUS`,
`TEST_RADIUS`, and `LIMITATIONS`. Tool success does not establish scope or
authority.

Required output: `EVIDENCE_REPORT` with commands, results, collection counts, finite budgets, local/hosted CI status, deviations, and one next authority.
