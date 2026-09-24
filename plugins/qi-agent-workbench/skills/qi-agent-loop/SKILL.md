---
name: qi-agent-loop
description: Use when a bounded Builder, Tester, or Reviewer report must reach its assigned Planner, a report needs receipt/review tracking, or an in-scope correction or out-of-lease blocker must be routed; not for autonomous orchestration or granting scope or authority.
---

# QI Agent Loop

This skill coordinates one supervised task cycle. It supplies workflow
knowledge; Codex task and messaging tools supply connectivity. Neither a skill
nor a tool changes the approved Work Order, role, scope, or Human authority.

## Use it for

- Sending a completed bounded Builder, Tester, or Reviewer result to the
  assigned Planner named by the active Work Order.
- Tracking a governed handoff through receipt, Planner review, and a recorded
  disposition.
- Stopping and escalating a material safety, data, scope, or authority blocker
  discovered outside the active lease.

Examples that should trigger this skill: "Send my finished Builder packet to
the assigned Planner and track whether it was received." "A blocker appeared
outside the lease; preserve the state and route it through the governed
escalation path." Do not trigger it for "Explain what this function does."

## One supervised cycle

1. Run [QI Context Boot](../qi-context-boot/SKILL.md) and derive the exact
   ten-field `TASK_ENVELOPE` from the approved Work Order using
   [QI Task Envelope](../qi-task-envelope/SKILL.md). A missing or conflicting
   role, baseline, scope, or authority is `HOLD`.
2. Use only the existing assigned Planner task or other explicitly authorized
   destination. Do not create a task, recipient, connector, or background
   runner unless the Work Order explicitly authorizes it.
3. Send one bounded report to the assigned Planner with the exact result,
   changed paths, verification, limitations, `SPINE_IMPACT` routing, and
   exactly one next action. Keep these
   states distinct:

   ```text
   SEND_REQUESTED
   SEND_COMPLETED
   RECEIPT_VERIFIED
   PLANNER_REVIEWED
   DISPOSITION_RECORDED
   HOLD
   ```

   `SEND_COMPLETED != RECEIPT_VERIFIED != PLANNER_REVIEWED`. A successful
   tool response proves only that the send operation completed. Mark receipt
   verified only after an authorized readback matches the intended report;
   mark Planner review or disposition only when the Planner provides evidence
   of it.
4. If delivery is uncertain, inspect the authorized destination before any
   retry. Never blindly resend or claim exactly-once delivery. If receipt
   cannot be verified, report `SEND_COMPLETED` or `HOLD` as supported by the
   evidence and stop at the current authority boundary.
5. For a material out-of-lease safety, data, scope, or authority conflict,
   preserve the state and stop. The detecting role escalates to Human
   authority and notifies the Planner through an authorized route; it does not
   silently continue, broaden scope, or decide the Planner's disposition.

## Report identity and routing

Keep the ten-field `TASK_ENVELOPE` unchanged. Attach the separate seven-field
`REPORT_METADATA` defined by `SUPERVISED_AGENT_LOOP_CONTRACT` in the
[Operating Model](../../../../docs/agent/OPERATING_MODEL.md).
Before acting on a report, require the active Work Order or Planner to have
explicitly opened a pending-transition binding for `WO_ID`, source/destination
task IDs, `OBJECT_ID`, `RUN_OR_ATTEMPT_ID`, and `IN_REPLY_TO`; missing, stale,
truncated, or mismatched reports are `HOLD`. Reuse `REPORT_ID` for a transport
retry, and never advance or redispatch a consumed transition even if a later
report has a different `REPORT_ID`. A correction requires a newly opened
Planner-authorized transition with a new expected attempt and a reference to
the superseded report/finding. This is
supervised task-message tracking, not exactly-once transport; follow the
[expected-transition admission contract](../../../../docs/agent/OPERATING_MODEL.md#expected-transition-and-idempotent-admission).
If the candidate changes after audit, ask the Planner to reconcile the delta
and identify a new object.

For a Work Order using the supervised loop, normal completed Builder,
Tester/Machine Verifier, and Reviewer reports all go to the assigned Planner.
Send another copy only when the Work Order names that route. The Planner may
challenge a Reviewer finding but does not change the independent verdict.

## In-lease correction and stop

For an in-scope Tester finding, the Planner judges scope, the same sole Builder
corrects within the lease, the Tester rechecks the affected acceptance, the
independent Reviewer audits the new object, and the Planner reconciles. The
Work Order sets finite attempt and runtime/cost limits. A correction within
the lease does not require another Human approval. Stop for Planner triage
when the budget is exhausted, authority or scope changes, or a symptom repeats
without a new hypothesis or evidence.

At each Builder return and Reviewer challenge, apply the
[Minimal complete fix](../../../../docs/agent/OPERATING_MODEL.md#minimal-complete-fix)
checks: root cause, existing helper/module reuse,
need for each new file/dependency/abstraction, and mapping of changes to
acceptance. Line count alone does not decide completeness.

## Evidence boundary

A passing lock suite supports locked-artifact integrity and the static
lock/verifier contract; it does not mean that the tests ran role scenarios or
proved a real correction cycle. See `FB-0043` in the
[Feedback Ledger](../../../../docs/agent/FEEDBACK_LEDGER.md) for historical
handoff evidence and its limits. It does not establish general exactly-once
delivery, autonomous/background execution, CLI/model smoke coverage, or
Human/merge/release authority.

Use [QI Evidence Check](../qi-evidence-check/SKILL.md) for machine claims and
[QI Review Handoff](../qi-review-handoff/SKILL.md) for independent review.
Follow the canonical Operating Model, [Role Boot and Prompt Profiles](../../../../docs/agent/ROLE_BOOT_AND_PROMPT_PROFILES.md),
and active [CURRENT handoff](../../../../docs/agent_handoff/CURRENT.md). A
send, receipt, Planner review, Reviewer verdict, and Human decision are
separate states.
