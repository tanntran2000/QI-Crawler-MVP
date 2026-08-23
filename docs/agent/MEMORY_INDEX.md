# QI-Crawler Memory Index

This is the universal entry point for a new Work Package or agent handoff.
Memory records are guidance and evidence, not a replacement for live Git or
the merged codebase.

## Read order

1. `AGENTS.md` — durable laws and workspace safety.
2. `docs/agent/OPERATING_MODEL.md` — roles, authority, and handoff protocol.
3. `docs/agent/HUMAN_COLLABORATION.md` — Human-facing collaboration
   preferences and context contract.
4. `docs/agent/LOCAL_STAGED_INTEGRATION.md` — active micro-WP, checkpoint,
   independent-audit, Parent Integration, and CI-waiver procedure.
5. `docs/agent/PROJECT_MEMORY.md` — durable facts verified on `main` only.
6. `docs/agent_handoff/CURRENT.md` — the single active snapshot.
7. Live Git state: branch, `HEAD`, status, upstream refs, and relevant history.
8. Live GitHub state when the Work Package involves a branch, PR, remote
   checkpoint, or CI.
9. Relevant entries in `docs/agent/LESSONS.md`.
10. Referenced entries in `docs/agent/FEEDBACK_LEDGER.md`.

## Read-in modes

- **FULL READ-IN**: a new Work Package, a new agent, or a writer takeover.
- **DELTA READ-IN**: the same Work Package resumes after an interruption; read
  the changed handoff and live Git state, then only the referenced deltas.
- **NO RE-READ**: continuous execution under an active Approval Lease with no
  material scope, baseline, writer, or blocker change.

## Authority order

Live repository/GitHub state and merged code/tests outrank stale handoffs.
Human decisions and verified source evidence outrank proposals. Feedback may
identify risk, but it cannot silently change scope or authority.

## Handoff rule

`CURRENT.md` contains exactly one active Work Package. Historical snapshots
belong under `docs/agent_handoff/history/` and must not be appended back into
the active snapshot.

After an audited micro-WP is pushed as a remote checkpoint, the active handoff
must be refreshed before a different agent is expected to continue safely.
The handoff records the last audited **code** head separately from any later
handoff/docs-only branch head. Live Git remains authority for the exact current
branch `HEAD`.

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
CURRENT                  READ

LIVE_GIT                 VERIFIED
LIVE_GITHUB              VERIFIED when a remote branch/PR/CI is relevant

ACTIVE_PARENT_WP         RESOLVED
LAST_AUDITED_MICRO_WP    RESOLVED
LAST_AUDITED_CODE_HEAD   RESOLVED
NEXT_MICRO_WP            RESOLVED
NEXT_AUTHORITY           RESOLVED

RESULT                    PROMPT_READY / ENTRY_HOLD
```

`PROMPT_READY` is allowed only when `CURRENT.md`, live Git, and live GitHub can
be reconciled. A stale snapshot is evidence to refresh or hold, not permission
to infer missing state from chat history or model memory.
