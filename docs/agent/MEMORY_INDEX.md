# QI-Crawler Memory Index

This is the universal entry point for a new Parent/Micro Work Package or agent
handoff.
Memory records are guidance and evidence, not a replacement for live Git or
the merged codebase.

`docs/agent/MASTER_ROADMAP.md` is the mandatory Product House / Architecture
README. It defines the durable product layers, dependency direction, and
frontier; it does not authorize implementation scope by itself.

## Read order

1. `AGENTS.md` — durable laws and workspace safety.
2. `docs/agent/OPERATING_MODEL.md` — roles, authority, and handoff protocol.
3. `docs/agent/HUMAN_COLLABORATION.md` — Human-facing collaboration
   preferences and context contract.
4. `docs/agent/LOCAL_STAGED_INTEGRATION.md` — active micro-WP, checkpoint,
   independent-audit, Parent Integration, and CI-waiver procedure.
5. `docs/agent/PROJECT_MEMORY.md` — durable facts verified on `main` only.
6. `docs/agent/MASTER_ROADMAP.md` — mandatory Product House / Architecture
   README, strategic capability map, and dependencies.
7. `docs/agent/MASTER_ROADMAP_DELTA.md` — active unresolved product and
   architecture evolution companion; mandatory alongside the Master Roadmap.
8. `docs/agent_handoff/CURRENT.md` — the single active handoff snapshot.
9. Live Git state: branch, `HEAD`, status, upstream refs, and relevant history.
10. Live GitHub state when the Work Package involves a branch, PR, remote
   checkpoint, or CI.
11. Relevant entries in `docs/agent/KNOWN_FAILURE_MODES.md`.
12. Relevant entries in `docs/agent/LESSONS.md`.
13. Referenced entries in `docs/agent/FEEDBACK_LEDGER.md`.

## Checkout identity gate

Before interpreting branch, head, audit range or object absence, resolve the
declared canonical checkout in this order:

```text
CANONICAL_CHECKOUT_EXPECTED = <absolute path>
→ git show-toplevel
→ git rev-parse --git-dir
→ git rev-parse --git-common-dir
→ git remote get-url origin
→ compare resolved path and repository identity
→ CHECKOUT_IDENTITY_GATE = PASS | ENTRY_HOLD
```

`WRONG_CHECKOUT` is distinct from `WRONG_BRANCH`, `WRONG_HEAD`,
`AUDIT_OBJECT_ABSENT` and `ACTUAL_BASELINE_DRIFT`; do not infer the latter
until the identity gate passes.

After read-mode selection and Roadmap/Delta reconciliation, invoke the single
canonical `ROLE_ENTRY_GATE` in `docs/agent/OPERATING_MODEL.md`. It is required
before `READY`, `PROMPT_READY`, `START_IMPLEMENTATION` or `START_AUDIT` for
new-agent/Parent entry, takeover, reassignment or material authority change.
`ROLE_ENTRY_GATE` and `ROADMAP_ENTRY_GATE` are separate; a role or model name
does not satisfy the other gate.

## Read-in mode selection

Select read depth before loading expensive context. `READ BEFORE WORK` is
mandatory, but a full read before every Micro-WP or prompt is not.

```text
READ_MODE_SELECTOR
==================
1. Identify whether the agent/session, Parent, takeover, Micro-WP or
   continuous execution state changed.
2. Read the small state authorities first: MEMORY_INDEX, CURRENT and live Git;
   read live GitHub when the branch, PR, checkpoint or CI is relevant.
3. Determine whether the roadmap, governance, baseline, scope or authority
   changed materially.
4. Select exactly one: FULL / DELTA / NO_RE_READ.
5. Read only the authority/context required by that mode.
6. Invoke the canonical ROLE_ENTRY_GATE after roadmap/delta reconciliation.
7. Return READY, PROMPT_READY or ENTRY_HOLD only when both gates pass.
```

**FULL READ-IN** is required for a new agent, new Parent WP, Planner/Reviewer/
Writer takeover, material architecture or governance/blueprint change, or an
unresolved authority conflict requiring full reconciliation. Full mode reads
the complete `MASTER_ROADMAP.md`, relevant `MASTER_ROADMAP_DELTA.md` entries,
and the required governance spine.

**DELTA READ-IN** is the default for a new Micro-WP within the same approved
Parent, with the same Product House/architecture baseline, no material
governance change and no unresolved conflict. Read `CURRENT.md`, live state,
the relevant active Delta entries, changed contracts and relevant
lessons/feedback only. Do not reread unchanged large documents merely because
the Micro-WP number changed.

**NO RE-READ** is allowed for continuous work in the same Micro-WP, Approval
Lease, writer and authority with no material scope, baseline, blocker or file
change. Live state is still checked for destructive, write or integration
actions.

If state cannot be reconciled, escalate `DELTA → FULL` as necessary and use
`ENTRY_HOLD` when reconciliation still fails. A previously validated file SHA
or diff may support a delta decision after an eligible full read, but SHA
equality never replaces the initial full read required for a new agent or
Parent.

## Roadmap entry gate

No `READY`, `PROMPT_READY` or `START_IMPLEMENTATION` is valid until
`ROADMAP_BASELINE = VERIFIED`, `PRODUCT_FRONTIER = RESOLVED`,
`ROADMAP_NODE = RESOLVED`, `ARCHITECTURE_LAYERS = RESOLVED` and
`READ_MODE = RESOLVED`. A changed roadmap SHA or blueprint revision invalidates
`NO_RE_READ` and requires a delta reconciliation. A changed Delta SHA or
material RD entry state also invalidates `NO_RE_READ`. Full roadmap read remains
mandatory for new agents, new Parents, takeovers and material architecture or
governance changes; it is not repeated for every command.

The Roadmap Entry Gate does not establish role authority. After it passes,
invoke `ROLE_ENTRY_GATE` from `OPERATING_MODEL.md`; unresolved role evidence or
conflict remains `ENTRY_HOLD` even when the Roadmap gate is clear.

## Authority order

Live repository/GitHub state and merged code/tests outrank stale handoffs.
Human decisions and verified source evidence outrank proposals. Feedback may
identify risk, but it cannot silently change scope or authority.

Independent review uses direct Git-object access by default. The audit object
is the exact `BASE_SHA..HEAD_SHA` range in the canonical checkout; a copied
patch is transport/fallback evidence only when those objects are unavailable.
Builder evidence and an independent audit are separate authorities.

## Handoff rule

`CURRENT.md` contains exactly one active handoff snapshot. Historical snapshots
belong under `docs/agent_handoff/history/` and must not be appended back into
the active snapshot. A closed Parent WP may legitimately leave
`ACTIVE_PARENT_WP = NONE` while the next Parent is only in design/planning.

After an audited micro-WP is pushed as a remote checkpoint, the active handoff
must be refreshed before a different agent is expected to continue safely.
The handoff records the last audited **code** head separately from any later
handoff/docs-only branch head. Live Git remains authority for the exact current
branch `HEAD`.

When a governed transition trigger applies, invoke the canonical
`LATEST_WP_SPINE_SYNC_AUDIT` defined in `LOCAL_STAGED_INTEGRATION.md` before
declaring the next work `READY` or `PROMPT_READY`. It audits the latest
governed transition against exact Git/live state, `CURRENT.md`, the relevant
Delta and Context Spine; it does not replace `PROJECT_MEMORY`, the Master
Roadmap, the Delta, a Spine promotion gate or implementation history. Use
`FULL`/`DELTA`/`NO_RE_READ` economically: unchanged continuous work within the
same Micro-WP does not rerun this audit unnecessarily. A material mismatch or
missing promotion is `HOLD`, not an inferred completion.

Handoff identity uses `HANDOFF_CAPTURE_BASE` (Git head verified immediately
before writing), `AUDIT_TARGET_CODE_HEAD` (the exact code/test commit under
review), `LAST_AUDITED_CODE_HEAD` (the already-audited code head), and
`LIVE_GIT_HEAD` (always re-verified at read-in). A tracked handoff must not
predict its own future docs commit SHA; known docs-only ancestry is reconciled
by Git range inspection, while unexplained material divergence is
`ENTRY_HOLD`.

## Documentation lifecycle contract

Every Parent and Micro Work Package has PRE and POST state. `ALWAYS CHECK !=
ALWAYS MODIFY`: inspect the required documents at the governed transition, but
update only the applicable tier and trigger.

```text
CURRENT AUTHORITY       = active execution/transition state
HISTORICAL SNAPSHOT     = as-of evidence under docs/agent_handoff/history/
DURABLE CONTRACT         = normative governance until approved change
```

`CURRENT.md` is not a diary, roadmap, review report or chat summary. Parent
PRE/POST requires `CURRENT.md` plus history; Micro PRE/POST is lightweight and
does not create history by default. Takeover, material interruption,
architecture transition, major recovery, Parent closeout and material scope
invalidation require full history. Roadmap, merged memory, feedback and
lessons have separate promotion triggers. Active machine-readable keys must
have one semantic meaning; historical values use explicit namespaced keys.

Engineering Failure Memory is routed organizational evidence, not current
execution state, merged product memory, Human Ground Truth, roadmap, feedback
or lessons. Read only entries relevant to the active capability or failure
path; an unrelated Micro-WP may record `N/A` without reading the whole file.

## Prompt-writer readiness gate

Before `PROMPT_READY` or `HANDOFF_READY`, resolve `SPINE_SYNC_STATE = PASS`.
Read-mode selection does not exempt an agent from routing newly accepted
durable knowledge. `NO_RE_READ` means unchanged authority may be reused; it
does not permit newly learned material information to remain unrecorded. Prompt
readiness also requires `ROLE_ENTRY_GATE = PASS` and `ROLE_CONFLICT = NO` when
the gate trigger applies.

An agent that is asked to generate the next technical Work Order must not rely
on prose memory alone. Before writing the prompt it must establish:

```text
HANDOFF_READINESS
=================
MEMORY_INDEX             READ
AGENTS                   READ
OPERATING_MODEL          READ
HUMAN_COLLABORATION      READ
LOCAL_STAGED_INTEGRATION READ
PROJECT_MEMORY           READ
MASTER_ROADMAP           READ
MASTER_ROADMAP_DELTA     READ
CURRENT                  READ

ARCHITECTURE_LAYERS      RESOLVED for material technical work
PRODUCT_FRONTIER         RESOLVED for material technical work
ROADMAP_DELTA_BASELINE   VERIFIED when a material Delta is relevant
RELEVANT_DELTA_IDS       RESOLVED when a material Delta is relevant
DOC_FRESHNESS_STATE      PASS / accepted STALE_NONBLOCKING

LIVE_GIT                 VERIFIED
LIVE_GITHUB              VERIFIED when a remote branch/PR/CI is relevant

ACTIVE_PARENT_WP         RESOLVED (may be NONE)
LAST_AUDITED_MICRO_WP    RESOLVED / N/A
LAST_AUDITED_CODE_HEAD   RESOLVED / N/A
NEXT_PARENT_OR_MICRO_WP  RESOLVED
NEXT_AUTHORITY           RESOLVED

RESULT                    PROMPT_READY / ENTRY_HOLD
```

`PROMPT_READY` is allowed only when `CURRENT.md`, live Git, and live GitHub can
be reconciled. A stale snapshot is evidence to refresh or hold, not permission
to infer missing state from chat history or model memory.

## Post-merge freshness gate

The governed post-merge sequence is:

```text
PR MERGED → verify live main → reconcile CURRENT → close merged Parent state
→ check roadmap maturity → check PROJECT_MEMORY promotion → resolve next action
→ HANDOFF READY
```

If merged live state conflicts with `CURRENT.md`, mark `HANDOFF_STALE` and use
`ENTRY_HOLD` before the next technical implementation. Cross-agent/session
handoffs must answer the bounded identity, head, audit, verification, document
sync, blocker, scope, next-action and authority fields defined by `AGENTS.md`;
missing answers mean `HANDOFF_READY = NO`. Chat is collaboration medium,
files are organizational memory, and Git/GitHub are repository truth. Check
applicable `KNOWN_FAILURE_MODES`, `FEEDBACK_LEDGER` and `LESSONS` triggers;
`ALWAYS CHECK != ALWAYS MODIFY`.
