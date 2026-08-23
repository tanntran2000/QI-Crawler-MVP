# Human Collaboration Contract

## 1. Purpose and authority

This document describes how agents collaborate with the Human. It is a
communication contract, not project truth. It never overrides the latest
explicit Human decision, an approved Work Order, `AGENTS.md`, or verified
Git/source/evidence. A material conflict must be reported and held when
required.

## 2. Language policy

- Human-facing communication uses Vietnamese by default.
- Agent-to-agent explanatory prose should prefer Vietnamese.
- Stable technical identifiers remain English: `PASS`, `HOLD`, `BLOCKED`,
  `ENTRY_CLEAR`, `ENTRY_NOTE`, `ENTRY_HOLD`, `STOP_FOR_REVIEW`, branch/SHA,
  path, class/function/API/schema/error/test/job names.
- Do not invent model-specific shorthand that another human or agent cannot
  understand.
- Machine-readable keys and enums remain stable English.

## 3. Human–agent conversation protocol

Agents must distinguish:

```text
FACT
INTERPRETATION
PROPOSAL
```

1. Do not ask the Human for repository facts the Agent can verify itself.
2. Use `NEEDS_HUMAN_CLARIFICATION` for genuine domain ambiguity.
3. A proposal is not approval; silence is not approval.
4. When challenging a Human request, report:

```text
CONCERN
EVIDENCE
RISK
OPTIONS
RECOMMENDATION
HUMAN DECISION REQUIRED
```

5. A Builder discovery outside the Work Order must be reported as:

```text
BUILDER_FINDING
original assumption
observed evidence
scope impact
scope expansion required YES/NO
NEXT = STOP_FOR_REVIEW when material
```

The Builder must not silently expand scope. When agents disagree, state:

```text
CLAIM A + EVIDENCE
CLAIM B + EVIDENCE
→ governance / roadmap / project memory / live evidence
```

Use evidence when it resolves the disagreement. If it remains an
architecture or business choice, the Human decides; agents do not vote.

## 4. Shortest complete prompt

Prompts should be concise, non-repetitive, and token-efficient without omitting
information needed for safe execution. The default Work Order shape is:

```text
BLUEPRINT CONTEXT → BASE → WORKSPACE → PLUGINS → OBJECTIVE → SCOPE → ACCEPTANCE → VERIFY → DELIVERY
```

For technical work, prepend a concise `BLUEPRINT CONTEXT` identifying the
Product Frontier, Capability Lane, Roadmap Node, current maturity, target
increment, dependencies and why this Work Package exists:

Blueprint Context aligns the work with `MASTER_ROADMAP.md`; it does not copy
the full roadmap or grant implementation authority.

Prefer repository references over copying stable governance text. Do not dump
superseded history, unrelated roadmap items, resolved defects, stale test
counts, or information that the repository can reliably provide. The shortest
complete prompt is not the shortest possible prompt.

## 5. Context economy

Prefer targeted read, then delta read, then repository reference over repeated
full-history reloads. Use `FULL`, `DELTA`, and `NO RE-READ` modes from the
Memory Index. If `CURRENT.md`, `PROJECT_MEMORY.md`, and live Git/GitHub are
sufficient, do not request old chat history. Optimize tokens without
sacrificing evidence, scope, or safety.

## 6. Tool complementarity

- The Work Order decides **what** may change.
- CodeGraph identifies **where** impact exists.
- Superpowers governs **how** approved work is executed.

CodeGraph impact radius is not edit authority. Superpowers must not reopen an
approved scope or architecture. If a tool is unavailable, use the documented
manual fallback and report `TOOL_UNAVAILABLE`; never disable or delete the
tooling.

### PROMPT PLUGIN-AWARENESS

When generating a technical Builder/Codex prompt, determine whether CodeGraph
and/or Superpowers apply. If applicable, name each required plugin and skill,
state when it is invoked, describe the expected CodeGraph analysis, require
execution evidence in the return, and define the fallback when unavailable.
Generic wording such as "Use CodeGraph + Superpowers" is not auditable.
Keep PLUGINS in the shortest-complete prompt template.

## 7. Quality over speed

Context, correctness, evidence, and business safety outrank speed. When
uncertain, inspect, verify, and use `HOLD` instead of guessing. Prefer slower
verified progress over fast false-safe conclusions. Consider context,
authority, blast radius, edge cases, failure modes, stale assumptions, and
known limitations.

## 8. Verified code quality

For implementation Work Packages, prefer code that is correct, simple,
maintainable, bounded, testable, and efficient enough. Avoid premature
optimization, unrequested refactors, and cleverness without measurable
benefit. Performance work requires evidence such as a benchmark, bottleneck,
runtime issue, or explicit Work Order. Minimal complete fix remains preferred.

## 9. Testing and reporting

Never report `PASS` or `DONE` without verification evidence. Reports should
state the exact tests, result, Ruff/lint result, diff checks, CI status when
relevant, what was not verified, and known limitations or blockers.

Appropriate runtime tests are mandatory for code changes. Tests must not be
weakened merely to obtain a green result.

## 10. Prompt filter

When the Human asks for a Codex/Builder prompt, the agent must first follow
the Memory Index, including `LOCAL_STAGED_INTEGRATION.md`, read
`MASTER_ROADMAP.md`, verify `CURRENT.md` and live Git/GitHub, identify the
active and next Work Package, confirm the exact baseline, and identify scope,
risks, and stop conditions. Read only relevant lessons and feedback. Then
reconcile the current frontier and roadmap node and produce the shortest
complete prompt. Blueprint alignment is required before emitting an
implementation Work Order.

Before emitting an implementation Work Order, record or internally prove:

```text
HANDOFF_READINESS
=================
MEMORY_INDEX             READ
AGENTS                   READ
OPERATING_MODEL          READ
HUMAN_COLLABORATION      READ
LOCAL_STAGED_INTEGRATION READ
PROJECT_MEMORY           READ
CURRENT                  READ
MASTER_ROADMAP           READ

LIVE_GIT                 VERIFIED
LIVE_GITHUB              VERIFIED when relevant

ACTIVE_PARENT_WP         RESOLVED
LAST_AUDITED_MICRO_WP    RESOLVED
LAST_AUDITED_CODE_HEAD   RESOLVED
NEXT_MICRO_WP            RESOLVED
NEXT_AUTHORITY           RESOLVED

RESULT                    PROMPT_READY / ENTRY_HOLD
```

Never generate an implementation prompt from this document alone. If current
state cannot be reconciled, return `ENTRY_HOLD` instead of inventing facts.
Chat history may explain context, but it is not a substitute for reconciling
the active handoff with live Git/GitHub.

## 11. Release-aware prompt generation

When generating a prompt for a user-visible change, first determine:

```text
RELEASE IMPACT: YES / NO / TBD
VERSION IMPACT: NONE / PATCH / MINOR / MAJOR / HUMAN_DECISION_REQUIRED
```

If `RELEASE IMPACT` is not `NO`, release-awareness extends the base template;
it does not replace the required `WORKSPACE` or `PLUGINS` sections. The
shortest-complete prompt must include:

```text
BASE → WORKSPACE → PLUGINS → OBJECTIVE → SCOPE → RELEASE IMPACT → VERSION IMPACT → ACCEPTANCE → VERIFY → DELIVERY
```

The prompt must not silently omit version consistency, GUI version display,
`CHANGELOG.md`, release metadata, Team Bid compatibility, or release/build
verification when applicable. Never instruct a Builder to publish without
explicit Human authority.

## 12. Role examples

Role determines authority, not model name. Examples only:

- Human/Team Bid → `HUMAN_AUTHORITY` for domain decisions.
- ChatGPT → often `PLANNER_ARCHITECT` or `REVIEWER_AUDITOR`.
- Codex → often `BUILDER_SINGLE_WRITER`.
- GitHub CI → `MACHINE_VERIFIER`.

Future agents may occupy different roles; the approved Work Order and role
authority remain the source of truth.

## 13. SA EXCEL SOURCE INTAKE & HUMAN CORRECTION

- SA normally supplies `TBMT-<date>.xlsx` or
  `KHMT-<date>.xlsx`; underscore and case variants are tolerated.
- The filename prefix is checked first as a source hint, then confirmed or
  rejected against workbook schema and embedded PL/IB identity evidence.
- Filename is a source hint only; workbook schema and embedded PL/IB identity
  are the evidence used for automatic classification.
- A compatible KHMT or TBMT filename/schema pair may be classified
  automatically. Dual-schema/mixed-namespace workbooks, conflicts and unknown
  filenames require an explicit Team Bid source selection.
- Human source corrections are append-only, require a named reviewer, become
  the source-type Ground Truth for that source SHA, and do not rewrite PL/IB
  identity or convert one source namespace into another.
- Source-type corrections do not enable self-learning or automatic production
  rule promotion; any learning remains a separately approved Work Package.
- **Source classification and downstream capability maturity are separate.**
  Prompt Writers must consult `PROJECT_MEMORY.md` and `MASTER_ROADMAP.md` to
  determine the currently supported recognition, intake, filter/search,
  review, export and GUI capabilities for each source. A source classification
  result does not itself authorize downstream import or workflow behavior.

## 14. LOCAL STAGED INTEGRATION COLLABORATION

The detailed operating procedure is
`docs/agent/LOCAL_STAGED_INTEGRATION.md`.

For each implementation micro-WP, the Single Writer must stop after local
verification and local commit with a `LOCAL_REVIEW_PACKET` and the explicit
next state:

```text
STOP_FOR_INDEPENDENT_LOCAL_AUDIT
```

The packet must include the Parent WP and micro-WP identifiers, base/head SHA,
changed-file list, bounded patch/diff, CodeGraph impact/edit/test radii when
applicable, exact verification commands, concise results, exit codes,
collection before/after, migration/data-safety result, known risks, and tree
status.

Do not paste large successful logs merely to prove activity. For a successful
run, prefer exact command + concise summary + exit code. For a failure, include
the relevant traceback/error excerpt needed for diagnosis.

The independent Reviewer returns `LOCAL_AUDIT_PASS`, `LOCAL_AUDIT_HOLD`, or
`LOCAL_AUDIT_FAIL`. The Single Writer must not proceed to the next micro-WP on
HOLD/FAIL.

After `LOCAL_AUDIT_PASS`, the audited feature-branch commit may be pushed as a
remote checkpoint without opening a PR. That checkpoint is backup/provenance,
not hosted-CI evidence.

After the remote checkpoint, refresh `CURRENT.md` before cross-agent/session
handoff. The snapshot must identify the last audited micro-WP/code SHA and the
next authorized slice. If a docs-only handoff commit advances the branch, keep
`LAST_AUDITED_CODE_HEAD` distinct from live branch `HEAD` and require the next
agent to verify both.

A merge performed while hosted CI is verified unavailable must be reported as
`CI_WAIVER = ACTIVE` and `PENDING_RETRO_CI = YES`, never as hosted `CI PASS`.
Official Team Bid release remains blocked while retro-CI debt is open unless
the Human later approves a separate bounded release exception.
