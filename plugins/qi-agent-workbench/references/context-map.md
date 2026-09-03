# Context map

Canonical authority, in order of purpose:

- `MEMORY_INDEX` and `AGENTS.md`: repository guardrails and durable governance.
- `docs/agent/OPERATING_MODEL.md`: role authority and entry gate.
- `docs/agent/MASTER_ROADMAP.md` with `MASTER_ROADMAP_DELTA.md`: strategic frontier and unresolved evolution.
- `docs/agent_handoff/CURRENT.md`: active governed transition state.
- `live Git/GitHub`: volatile repository, branch, and CI facts.

QI context boot resolution:

`MEMORY_INDEX` → governance/read mode → `MASTER_ROADMAP` + `MASTER_ROADMAP_DELTA` → `CURRENT` → live Git/GitHub → role and scope reconciliation → `READY | ENTRY_HOLD`.

This map is a reading aid, never a replacement for these sources or a second Spine.

Task Envelope routing:

- `qi-task-envelope` derives the subordinate `TASK_ENVELOPE` from the approved Work Order and read-only Boot.
- The envelope has exactly ten fields and never widens scope or grants authority; mismatches are `ENTRY_HOLD`.
