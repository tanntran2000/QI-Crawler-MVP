---
name: qi-agent-loop
description: Coordinate approved QI Work Orders across Planner, Builder, Tester, and Reviewer; use for role routing, evidence returns, review handoffs, and checkpoint/PR/CI status.
---

# QI Agent Loop

Use this workflow for governed QI Work Orders. It explains routing; it never
grants authority or changes the approved scope.

## Authority and owners

- Resolve role from explicit Human assignment → approved Work Order → governed
  `docs/agent_handoff/CURRENT.md`. Any material conflict is `ENTRY_HOLD`.
- Human A0 is the material authority. The four operational roles are Planner,
  Builder, Tester/Machine Verifier and independent Reviewer; their authorities
  differ, and Tester is evidence-only.
- `docs/agent/OPERATING_MODEL.md` owns roles, reports and Planner follow-through.
  `docs/agent/ROLE_BOOT_AND_PROMPT_PROFILES.md` owns boot and prompt contracts.
  `docs/agent/LOCAL_STAGED_INTEGRATION.md` owns commits, audits, checkpoints,
  Pull Requests, CI and merge gates. The Work Order owns the task's exact scope.

## Route reports

```text
Human intent → Planner Work Order → Builder result → Planner review
→ Tester evidence when required → Planner evidence review
→ independent Reviewer verdict → Planner reconciliation
→ Human decision when required
```

- Include all seven report fields. The six binding fields, separate `REPORT_ID`
  check, initial `IN_REPLY_TO = NONE` and correction-ID rules are owned by
  `docs/agent/OPERATING_MODEL.md`; consumed or duplicate reports cannot advance
  or redispatch.
- This is supervised admission tracking, not exactly-once transport or an
  autonomous runner, broker, database or scheduler.

- Planner plans and reconciles; it does not write Builder output or replace
  machine verification or independent review.
- Builder is the sole writer for the approved lease and returns its result,
  blockers and out-of-scope findings to the Planner.
- Tester runs only approved checks. Return the exact command, environment,
  Git object, exit code, result and limitations to the Planner. Tester cannot
  edit, change acceptance, route work, close a WP, or decide merge/release.
- Reviewer inspects the exact authorized Git range independently and returns
  `PASS`, `HOLD` or `FAIL` to the Planner. Reviewer does not edit; any bounded
  correction is routed by the Planner to Builder.
- Critical authority, safety, scope or evidence matters go through Planner to
  Human A0. Preserve distinct states:

```text
BUILDER_RESULT != MACHINE_VERIFIER_EVIDENCE != REVIEWER_VERDICT !=
PLANNER_RECONCILIATION != HUMAN_AUTHORIZATION
```

## Git and handoff states

Use `docs/agent/LOCAL_STAGED_INTEGRATION.md` for the detailed lifecycle.
Keep these states distinct:

```text
LOCAL_COMMIT != INDEPENDENT_AUDIT != REMOTE_CHECKPOINT != PULL_REQUEST != CI
```

A feature-branch push without an open PR is a remote checkpoint, not CI
evidence. When a checkpoint has no PR, record its reason, integration target,
PR-opening trigger, owner and exactly one next action. A green CI result does
not clear an independent blocker or Human decision boundary.

For task reports, name the task, WP, branch, exact base/head, scope, verification,
findings, current Git/remote state, and one next authority/action. Distinguish
`SEND_COMPLETED`, `RECEIPT_VERIFIED` and `PLANNER_REVIEWED`; tool success alone
proves only the send attempt. Never claim exactly-once delivery from one handoff.

## Stop and functional checks

Hold and return to Planner on a wrong checkout/object, conflicting role or
handoff, missing approval, scope expansion, unverifiable evidence, or an
unapproved external/cleanup action. Route unresolved material decisions through
Planner to Human A0.

- Conflicting Work Order and `CURRENT` → `ENTRY_HOLD`.
- Tester failure → evidence to Planner; only Planner may authorize a bounded
  correction to Builder.
- Reviewer `HOLD` → preserve the verdict and return it to Planner unchanged.
- Green CI plus an unresolved blocker → remain on `HOLD`.
- CI red within scope → report it to Planner; do not expand into B09 or workflow repair.
- Checkpoint without PR → record all five checkpoint handoff fields above.
- Terminal sync → do not claim its own future commit; follow the narrow rule in
  `docs/agent/LOCAL_STAGED_INTEGRATION.md`.
- Skill text conflicting with `AGENTS.md`, Human authority or the Work Order →
  follow the higher authority and raise the conflict; this skill cannot override it.
