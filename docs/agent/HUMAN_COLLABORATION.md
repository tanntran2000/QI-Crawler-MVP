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
BLUEPRINT CONTEXT → BASE → WORKSPACE IDENTITY → PLUGINS → OBJECTIVE → SCOPE → ACCEPTANCE → VERIFY → DELIVERY
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

For Builder and Reviewer prompts, use the canonical role-specific profiles in
`docs/agent/OPERATING_MODEL.md`. A Builder prompt must make the authorized
scope, read mode, exclusions, acceptance/evidence contract and stop conditions
explicit; every listed plugin/tool must be classified
`REQUIRED | OPTIONAL | NOT_APPLICABLE`;
a Reviewer prompt must challenge the resulting object and evidence without
prescribing a verdict. A `LARGE_BOUNDED_BATCH` may group coherent stages under
one Approval Lease, but it does not erase stage verification, semantic commit
boundaries or independent review.

The detailed role-boot and action-first standard is canonical in
`docs/agent/ROLE_BOOT_AND_PROMPT_PROFILES.md`. Material prompts are
ACTION-FIRST and must orient the assigned role before requesting execution.
Planner, Builder and Reviewer are independent execution-control poles beneath
Human A0; mutual challenge is evidence and escalation, not voting, and
`challenge != override`. The receiving agent should not need to ask what action
is wanted when the prompt satisfies the quality gate.

`CURRENT.md` remains conditionally writable only by the active
`BUILDER_SINGLE_WRITER` when it is in the approved scope and a governed
transition trigger with evidence exists. The Builder may record facts and
resolved external decisions from exact authority evidence, but may not
originate them: `RECORD_AUTHORITY != ORIGINATE_AUTHORITY`. For technical
Builder and Reviewer Work Orders, `WORKSPACE IDENTITY` must name
`CANONICAL_CHECKOUT_EXPECTED` and `EXPECTED_ORIGIN_REPOSITORY`. The active
role must prove the resolved working directory, Git top-level, Git
directory/common directory and origin before interpreting branch or object
state; a mismatch is `WRONG_CHECKOUT` and requires `ENTRY_HOLD`. An Approval Lease
does not implicitly authorize destructive actions, history rewrite, force push,
PR/merge/release or Human/Reviewer/Planner decisions.

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

When the Human asks for a Codex/Builder prompt, the agent must read before
prompting and run the repository `READ_MODE_SELECTOR` before expensive context
loads:

```text
PROMPT REQUEST
→ read MEMORY_INDEX / CURRENT
→ verify live Git/GitHub when relevant
→ run READ_MODE_SELECTOR
→ select FULL / DELTA / NO_RE_READ
→ read only required authority/context
→ reconcile active WP, audited head, scope and blockers
→ reconcile Roadmap / Delta entry
→ ROLE_ENTRY_GATE
→ PROMPT_READY or ENTRY_HOLD
```

`READ-BEFORE-PROMPT = MANDATORY`; `FULL-READ-BEFORE-EVERY-PROMPT = NOT
REQUIRED`; `CHAT MEMORY ALONE = NOT SUFFICIENT`. A same-Parent Micro prompt
normally uses `DELTA` unless a full-read trigger exists. Read the complete
`MASTER_ROADMAP.md` when the selector chooses FULL, not automatically for
every prompt. Read only relevant lessons and feedback, then produce the
shortest complete prompt.

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
MASTER_ROADMAP_DELTA     READ when relevant

LIVE_GIT                 VERIFIED
LIVE_GITHUB              VERIFIED when relevant

ACTIVE_PARENT_WP         RESOLVED
LAST_AUDITED_MICRO_WP    RESOLVED
LAST_AUDITED_CODE_HEAD   RESOLVED
NEXT_MICRO_WP            RESOLVED
NEXT_AUTHORITY           RESOLVED

ROLE_ENTRY_GATE          PASS when triggered
ROLE_SOURCE_EVIDENCE     RESOLVED when triggered
ROLE_CONFLICT             NO when triggered

RESULT                    PROMPT_READY / ENTRY_HOLD
```

Never generate an implementation prompt from this document alone. If current
state cannot be reconciled, return `ENTRY_HOLD` instead of inventing facts.
Chat history may explain context, but it is not a substitute for reconciling
the active handoff with live Git/GitHub. The canonical role-entry contract is
defined in `docs/agent/OPERATING_MODEL.md`; prompt readiness cannot bypass it.

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
BASE → WORKSPACE IDENTITY → PLUGINS → OBJECTIVE → SCOPE → RELEASE IMPACT → VERSION IMPACT → ACCEPTANCE → VERIFY → DELIVERY
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

For a normal implementation micro-WP, the Single Writer must stop after local
verification and local commit with a `REVIEWER_HANDOFF_CHECKPOINT` and the
explicit next state:

```text
STOP_FOR_INDEPENDENT_LOCAL_AUDIT
```

The handoff must include the Parent WP and micro-WP identifiers, base/head SHA,
changed-file list, exact verification commands, concise results, exit codes,
collection before/after, migration/data-safety result, known risks, and tree
status. The Reviewer directly inspects the exact Git objects when available.
Use `AUDIT_OBJECT: BASE_SHA..HEAD_SHA`; a `PATCH` is an optional fallback only
when direct object access is unavailable.

Do not paste large successful logs merely to prove activity. For a successful
run, prefer exact command + concise summary + exit code. For a failure, include
the relevant traceback/error excerpt needed for diagnosis.

The independent Reviewer returns `LOCAL_AUDIT_PASS`, `LOCAL_AUDIT_HOLD`, or
`LOCAL_AUDIT_FAIL`. The Single Writer must not proceed to the next micro-WP on
HOLD/FAIL.

When the Planner has approved a `LARGE_BOUNDED_BATCH`, the same checkpoint
discipline applies at the batch boundary rather than after every safe internal
stage. Internal stages still require explicit entry/exit criteria, targeted
verification and semantic local commits. A material architecture, data-safety,
authority or scope boundary remains an immediate stop and requires Planner or
Human reapproval; the larger batch never creates implicit permission for the
next Work Package.

Every Reviewer handoff also reports:

```text
SPINE_IMPACT:
SPINE_TARGET_FILES:
SPINE_SYNC_STATE: PASS / HOLD
```

A Builder finding that creates durable organizational knowledge must not remain
only in chat or a local review packet. If required Spine routing is missing,
the Reviewer returns `SPINE_AUDIT = HOLD`; this does not require copying chat
transcripts into the Context Spine.

After `LOCAL_AUDIT_PASS`, the audited feature-branch commit may be pushed as a
remote checkpoint without opening a PR. That checkpoint is backup/provenance,
not hosted-CI evidence.

After the remote checkpoint, refresh `CURRENT.md` before cross-agent/session
handoff. The snapshot must identify the last audited micro-WP/code SHA and the
next authorized slice. If a docs-only handoff commit advances the branch, keep
`LAST_AUDITED_CODE_HEAD` distinct from live branch `HEAD` and require the next
agent to verify both.

Each Work Package carries context continuity across its PRE and POST state.
Use tiered updates: a Parent or material event may require a history snapshot;
a Micro-WP normally needs only lightweight `CURRENT.md` state. Do not rewrite
every governance document for each edit, test run, unaudited progress update,
or chat narration. Before a new session or agent takeover, reconcile the
required read-in, live Git/GitHub and the active handoff; after the governed
transition, leave one concise, factual, actionable POST handoff.

A merge performed while hosted CI is verified unavailable must be reported as
`CI_WAIVER = ACTIVE` and `PENDING_RETRO_CI = YES`, never as hosted `CI PASS`.
Official Team Bid release remains blocked while retro-CI debt is open unless
the Human later approves a separate bounded release exception.

## 15. Blueprint and organizational-memory readiness

Before a Builder or Prompt Writer is `READY`, reconcile the roadmap baseline,
frontier, roadmap node, architecture layers and selected read mode. A new
agent/Parent, takeover or material architecture/governance change requires a
FULL roadmap read; a same-Parent Micro-WP uses DELTA; unchanged same-lease work
may use NO-RE-READ. A changed roadmap SHA or blueprint revision invalidates
NO-RE-READ.

Governed documentation freshness transitions are:

```text
PARENT PRE → MICRO PRE → AUDITED REMOTE CHECKPOINT → MICRO POST
→ AGENT/SESSION HANDOFF → PARENT POST → PR/MERGE TRANSITION
→ POST-MERGE RECONCILIATION → NEXT PARENT ENTRY
```

After `PR MERGED`, verify live `main`, reconcile `CURRENT`, close the merged
Parent state, check roadmap maturity and project-memory promotion, then set
one next action. If `CURRENT` still says not merged, the handoff is stale and
the next technical entry is held. Check applicable `KNOWN_FAILURE_MODES`,
`FEEDBACK_LEDGER` and `LESSONS` triggers while preserving
`ALWAYS CHECK != ALWAYS MODIFY`.

Minimum cross-agent/session handoff fields are:
`ROADMAP_REVISION`, `ROADMAP_BASELINE_SHA`, `HANDOFF_CAPTURE_BASE`,
`AUDIT_TARGET_CODE_HEAD`, `LIVE_GIT_HEAD`, `ACTIVE_PARENT_WP`, `ACTIVE_MICRO_WP`,
`LAST_AUDITED_CODE_HEAD`, `LAST_AUDITED_DOC_HEAD`, `REMOTE_CHECKPOINT`,
`PR_STATE`, `MERGE_STATE`, `VERIFICATION_STATE`, `HOSTED_CI_STATE`,
`DOC_SYNC_STATE`, `PROVEN_COMPLETE`, `OPEN_BLOCKERS`, `SCOPE_BOUNDARIES`,
`EXACTLY_ONE_NEXT_ACTION`, `NEXT_AUTHORITY`. Missing answers mean
`HANDOFF_READY = NO`; handoffs are not transcripts.

```text
CHAT = collaboration medium
FILES = organizational memory
GIT/GITHUB = repository truth
```

## 16. Material Human input and Planner intent protocol

Trivial chat does not require a formal packet. When a Human statement can
materially affect scope, architecture, governance, product sequence,
business/domain behavior, authority or risk, classify it as one or more of:

```text
PROBLEM
IDEA
REQUIREMENT
PRIORITY
CONSTRAINT
ASSUMPTION
BUSINESS_DECISION
FACTUAL_CLAIM
FUTURE_DIRECTION
```

`HUMAN BUSINESS / PRIORITY DECISION = A0 MATERIAL AUTHORITY`. A Human
technical or factual assumption is not automatically a verified fact. The
Planner may challenge it with verified Git/source evidence, the Roadmap, Delta,
Project Memory, Failure Memory, Lessons and relevant domain evidence, but must
not silently override an A0 decision. If an A0 decision conflicts with a
technical safety or dependency constraint, report the risk and return it to the
Human.

### HUMAN_INTENT_RECONCILIATION — canonical material contract

```text
HUMAN_INTENT_RECONCILIATION
===========================
HUMAN_INPUT = <material request / idea / decision>
INPUT_CLASSIFICATION = <one or more canonical classes>
UNDERLYING_PROBLEM = <resolved / unknown>
INTENDED_OUTCOME = <resolved>
CURRENT_SCOPE_RELATION = IN_SCOPE / FUTURE / OUT_OF_SCOPE / CONFLICT
AUTHORITY_CLASS = HUMAN_DECISION / FACTUAL_CLAIM / PROPOSAL / MIXED
EVIDENCE_REQUIRED = YES / NO
EVIDENCE_STATUS = VERIFIED / PARTIAL / UNKNOWN / NOT_APPLICABLE
MATERIAL_CONSTRAINTS = <resolved>
INTENT_PRESERVED = YES / NO
UNRESOLVED_AMBIGUITY = NONE / <description>
```

This contract is required for material Planner decisions, not ordinary low-risk
conversation. It preserves the underlying Human intent while distinguishing
facts, assumptions and proposed solutions.

### PLANNER_STRATEGIC_ASSESSMENT — canonical material contract

For material intent, the Planner checks the applicable Delta, Roadmap, Context
Spine, live state, evidence, authority boundary, dependencies, risk and timing
before recommending implementation:

The assessment explicitly records the applicable `DELTA_CHECK`,
`ROADMAP_CHECK`, `SPINE_CHECK`, `LIVE_STATE_CHECK`, `EVIDENCE_CHECK`,
`AUTHORITY_CHECK`, `DEPENDENCY_CHECK`, `RISK_CHECK` and
`TIMING / SEQUENCING_CHECK`.

```text
PLANNER_STRATEGIC_ASSESSMENT
============================
RELEVANT_DELTA_IDS = <resolved>
DELTA_ALIGNMENT = ALIGNED / PARTIAL / CONFLICT / NEW_DELTA_CANDIDATE / N/A
PRODUCT_FRONTIER = <resolved>
ROADMAP_ALIGNMENT = ALIGNED / PARTIAL / CONFLICT / N/A
SPINE_EVIDENCE = <checked authorities>
LIVE_STATE = VERIFIED / NOT_REQUIRED / HOLD
DEPENDENCIES = SATISFIED / PARTIAL / BLOCKED / N/A
AUTHORITY_BOUNDARY = PASS / HOLD
MATERIAL_RISKS = <list / NONE>
STRATEGIC_FIT = PASS / ADAPT / HOLD
```

`PLANNER_IDEA_EVALUATION` compares Human intent ↔ evidence ↔ Delta ↔ Roadmap
↔ Context Spine ↔ live state ↔ authority boundary. The Planner preserves the
intent, tests the proposed solution, presents the strongest evidence-based
recommendation, and neither blindly obeys nor casually opposes the Human.

The only canonical material Planner dispositions are:

```text
ACCEPT
ADAPT
PARK
CHALLENGE
REJECT
NEEDS_HUMAN_CLARIFICATION
```

`ACCEPT` means the intent and direction are aligned and eligible. `ADAPT` means
the intent is valid but the solution, scope or sequence must change. `PARK`
means valuable intent is deferred by dependency, timing or current scope.
`CHALLENGE` means material evidence or authority conflict requires Human
reconsideration. `REJECT` is reserved for a proposal that violates a durable
architecture, safety or authority contract and has no bounded valid adaptation.
`NEEDS_HUMAN_CLARIFICATION` means material intent or authority is genuinely
ambiguous. `REJECT` never overrides a valid A0 decision; accepted A0 risk is
recorded and returned to the Human.

### PLANNER_CHALLENGE — evidence-oriented shape

```text
PLANNER_CHALLENGE
=================
HUMAN_PROPOSAL =
WHAT_IS_VALID_IN_THE_INTENT =
CONFLICTING_EVIDENCE =
DELTA_CONFLICT =
ROADMAP_CONFLICT =
SPINE_CONFLICT =
AUTHORITY_CONFLICT =
LOGICAL_OR_SAFETY_RISK =
ALTERNATIVE_A =
ALTERNATIVE_B =
PLANNER_RECOMMENDATION =
HUMAN_DECISION_REQUIRED = YES / NO
```

Alternatives are included when useful; the purpose is an evidence-backed
challenge, not ceremonial verbosity.

### PLANNER_DECISION_PACKET — material routing

```text
PLANNER_DECISION_PACKET
=======================
HUMAN_INTENT_SUMMARY =
INPUT_CLASSIFICATION =
VERIFIED_FACTS =
UNVERIFIED_ASSUMPTIONS =
RELEVANT_DELTA_IDS =
MASTER_ROADMAP_ALIGNMENT =
SPINE_CHECK =
LIVE_STATE =
DEPENDENCIES =
AUTHORITY_BOUNDARY =
MATERIAL_RISKS =
PLANNER_DISPOSITION = ACCEPT / ADAPT / PARK / CHALLENGE / REJECT / NEEDS_HUMAN_CLARIFICATION
PLANNER_RECOMMENDATION =
ROUTING = WORK_ORDER / DELTA / SPINE / HUMAN / PARK / NO_ACTION
HUMAN_DECISION_REQUIRED = YES / NO
EXACTLY_ONE_NEXT_ACTION =
```

This packet is for material decisions only. Before producing a material Builder
Work Order, `HUMAN_INTENT_RECONCILIATION = COMPLETE` and
`PLANNER_STRATEGIC_ASSESSMENT = COMPLETE`; only `ACCEPT` or `ADAPT` permits the
Work Order. `PARK`, `CHALLENGE`, `REJECT` and
`NEEDS_HUMAN_CLARIFICATION` require the corresponding routing or Human
clarification instead. Roadmap Entry Gate and Role Entry Gate remain mandatory.

### Reviewer continuity and post-review Human loop

For material work, carry the following intent into the existing WP-specific
`REVIEWER_CHALLENGE_CONTRACT` from `OPERATING_MODEL.md`:

```text
HUMAN_INTENT_TO_PROTECT
MATERIAL_CONSTRAINTS
ASSUMPTIONS_TO_CHALLENGE
AUTHORITY_BOUNDARIES
KNOWN_RISKS
SUCCESS / ACCEPTANCE INTENT
```

This reuses the existing Reviewer contract; the Planner must not tell the
Reviewer which verdict to return. `REVIEWER_VERDICT !=
PLANNER_POST_REVIEW_RECONCILIATION != HUMAN_MATERIAL_AUTHORITY`. After review,
the Planner explicitly reports:

```text
WHAT_THE_WP_ACTUALLY_ACHIEVED
WHAT_IT_DID_NOT_ACHIEVE
MATERIAL_REVIEWER_FINDINGS
REMAINING_RISKS
WHETHER_HUMAN_INTENT_WAS_PRESERVED
WHAT_DECISION_IS_NOW_REQUIRED
```

The Planner uses the existing post-review reconciliation contract, maps the
result back to Human intent, and escalates material decisions to the Human. This
protocol does not implement the M4 latest-WP Spine sync or Builder Integrity.
