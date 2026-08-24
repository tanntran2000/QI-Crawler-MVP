# QI-Crawler Memory Index

This is the universal entry point for a new Work Package or agent handoff.
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
10. Relevant entries in `docs/agent/LESSONS.md`.
11. Referenced entries in `docs/agent/FEEDBACK_LEDGER.md`.

## Read-in modes

- **FULL READ-IN**: a new Work Package, a new agent, or a writer takeover;
  fully read `MASTER_ROADMAP.md` before architecture/layer readiness.
- **DELTA READ-IN**: the same Work Package resumes after an interruption; read
  the changed handoff and live Git state, then only the referenced deltas.
- **NO RE-READ**: continuous execution under an active Approval Lease with no
  material scope, baseline, writer, blocker, or material roadmap change.

DELTA/NO-RE-READ is valid only while the Product House / Architecture README
has not materially changed and the same approved Work Package remains active.

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
