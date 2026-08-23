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

## 3. Shortest complete prompt

Prompts should be concise, non-repetitive, and token-efficient without omitting
information needed for safe execution. The default Work Order shape is:

```text
BASE → WORKSPACE → PLUGINS → OBJECTIVE → SCOPE → ACCEPTANCE → VERIFY → DELIVERY
```

Prefer repository references over copying stable governance text. Do not dump
superseded history, unrelated roadmap items, resolved defects, stale test
counts, or information that the repository can reliably provide. The shortest
complete prompt is not the shortest possible prompt.

## 4. Context economy

Prefer targeted read, then delta read, then repository reference over repeated
full-history reloads. Use `FULL`, `DELTA`, and `NO RE-READ` modes from the
Memory Index. If `CURRENT.md`, `PROJECT_MEMORY.md`, and live Git/GitHub are
sufficient, do not request old chat history. Optimize tokens without
sacrificing evidence, scope, or safety.

## 5. Tool complementarity

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

## 6. Quality over speed

Context, correctness, evidence, and business safety outrank speed. When
uncertain, inspect, verify, and use `HOLD` instead of guessing. Prefer slower
verified progress over fast false-safe conclusions. Consider context,
authority, blast radius, edge cases, failure modes, stale assumptions, and
known limitations.

## 7. Verified code quality

For implementation Work Packages, prefer code that is correct, simple,
maintainable, bounded, testable, and efficient enough. Avoid premature
optimization, unrequested refactors, and cleverness without measurable
benefit. Performance work requires evidence such as a benchmark, bottleneck,
runtime issue, or explicit Work Order. Minimal complete fix remains preferred.

## 8. Testing and reporting

Never report `PASS` or `DONE` without verification evidence. Reports should
state the exact tests, result, Ruff/lint result, diff checks, CI status when
relevant, what was not verified, and known limitations or blockers.

Appropriate runtime tests are mandatory for code changes. Tests must not be
weakened merely to obtain a green result.

## 9. Prompt filter

When the Human asks for a Codex/Builder prompt, the agent must first follow
the Memory Index, verify `CURRENT.md` and live Git/GitHub, identify the active
and next Work Package, confirm the exact baseline, and identify scope, risks,
and stop conditions. Read only relevant lessons and feedback. Then produce
the shortest complete prompt.

Never generate an implementation prompt from this document alone. If current
state cannot be reconciled, return `ENTRY_HOLD` instead of inventing facts.

## 10. Release-aware prompt generation

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

## 11. Role examples

Role determines authority, not model name. Examples only:

- Human/Team Bid → `HUMAN_AUTHORITY` for domain decisions.
- ChatGPT → often `PLANNER_ARCHITECT` or `REVIEWER_AUDITOR`.
- Codex → often `BUILDER_SINGLE_WRITER`.
- GitHub CI → `MACHINE_VERIFIER`.

Future agents may occupy different roles; the approved Work Order and role
authority remain the source of truth.
