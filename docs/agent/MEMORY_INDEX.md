# QI-Crawler Memory Index

This is the universal entry point for a new Work Package or agent handoff.
Memory records are guidance and evidence, not a replacement for live Git or
the merged codebase.

## Read order

1. `AGENTS.md` — durable laws and workspace safety.
2. `docs/agent/OPERATING_MODEL.md` — roles, authority, and handoff protocol.
3. `docs/agent/HUMAN_COLLABORATION.md` — Human-facing collaboration
   preferences and context contract.
4. `docs/agent/PROJECT_MEMORY.md` — durable facts verified on `main` only.
5. `docs/agent_handoff/CURRENT.md` — the single active snapshot.
6. Live Git state: branch, `HEAD`, status, and relevant history.
7. Live GitHub state when the Work Package involves a branch, PR, or CI.
8. Relevant entries in `docs/agent/LESSONS.md`.
9. Referenced entries in `docs/agent/FEEDBACK_LEDGER.md`.

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
