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
7. `docs/agent_handoff/CURRENT.md` — the single active handoff snapshot.
8. Live Git state: branch, `HEAD`, status, upstream refs, and relevant history.
9. Live GitHub state when the Work Package involves a branch, PR, remote
   checkpoint, or CI.
10. Relevant entries in `docs/agent/KNOWN_FAILURE_MODES.md`.
11. Relevant entries in `docs/agent/LESSONS.md`.
12. Referenced entries in `docs/agent/FEEDBACK_LEDGER.md`.

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
6. Return READY, PROMPT_READY or ENTRY_HOLD.
```

**FULL READ-IN** is required for a new agent, new Parent WP, Planner/Reviewer/
Writer takeover, material architecture or governance/blueprint change, or an
unresolved authority conflict requiring full reconciliation. Full mode reads
the complete `MASTER_ROADMAP.md` and required governance spine.

**DELTA READ-IN** is the default for a new Micro-WP within the same approved
Parent, with the same Product House/architecture baseline, no material
governance change and no unresolved conflict. Read `CURRENT.md`, live state,
changed deltas, relevant contracts and relevant lessons/feedback only. Do not
reread unchanged large documents merely because the Micro-WP number changed.

**NO RE-READ** is allowed for continuous work in the same Micro-WP, Approval
Lease, writer and authority with no material scope, baseline, blocker or file
change. Live state is still checked for destructive, write or integration
actions.

If state cannot be reconciled, escalate `DELTA → FULL` as necessary and use
`ENTRY_HOLD` when reconciliation still fails. A previously validated file SHA
or diff may support a delta decision after an eligible full read, but SHA
equality never replaces the initial full read required for a new agent or
Parent.

## Authority order

Live repository/GitHub state and merged code/tests outrank stale handoffs.
Human decisions and verified source evidence outrank proposals. Feedback may
identify risk, but it cannot silently change scope or authority.

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
CURRENT                  READ

ARCHITECTURE_LAYERS      RESOLVED for material technical work
PRODUCT_FRONTIER         RESOLVED for material technical work

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
