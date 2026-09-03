---
name: qi-python-change
description: Apply bounded Python behavior changes with QI TDD and debugging discipline.
---

# QI Python Change

For an authorized behavior change, invoke Superpowers TDD: add one focused failing test, observe the expected RED failure, make the minimal production change, and observe GREEN. No production code is written before the failing test. Invoke systematic debugging for a failure or unexpected behavior before proposing a fix.

## Bounded execution contract

An `approved Work Order required` is the authority for every Python behavior change. Brainstorming, model/tool suggestions, or a plausible issue do not substitute for an approved scope.

`no architecture replan` is allowed inside an execution unit: do not redesign or replan the approved architecture. If the approved design is insufficient, hold for Planner rather than expanding it.

`minimal complete fix` is required: change only what closes the authorized behavior and its discriminating tests, while preserving existing interfaces and safety boundaries.

Use `TDD / systematic debugging only when applicable`: executable behavior changes require RED-before-production-code and a focused debugging loop for failures; documentation-only or contract-only work records why those techniques are not applicable.

Protect user-facing product boundaries and existing authority/seam contracts. Do not expand scope, self-review, or substitute test success for Human/Planner/Reviewer decisions. Missing role, baseline, scope, or RED evidence is `HOLD`.

Required output: `PYTHON_CHANGE_EVIDENCE` with RED/GREEN commands and results, changed behavior, edit/test radii, remaining risks, and one next authority.
