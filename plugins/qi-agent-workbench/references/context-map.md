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

## Discovery and tool-family routing

QI_WORKBENCH_DISCOVERY_MODE = REPO_LOCAL_MANUAL_CANONICAL
QI_WORKBENCH_SKILL_ROOT = plugins/qi-agent-workbench/skills/
REPO_LOCAL = VERIFIED
MANUAL_USE = SUPPORTED
NATIVE_CODEX_DISCOVERY = NOT_REQUIRED_FOR_A1_PASS

QI_AGENT_WORKBENCH = CORE_GUIDANCE
CODEGRAPH = CONDITIONAL_CORE
SUPERPOWERS = CONDITIONAL_CORE
AGENT_REACH = CONDITIONAL_CORE_EXTERNAL_RESEARCH_ONLY
ECC = SPECIALIZED_DEFAULT_NOT_ROUTED
PONYTAIL = EXPERIMENTAL_OR_SPECIALIZED_NOT_AUTHORITY
I_HAVE_ADHD = SPECIALIZED_PRESENTATION_ONLY
OPENAI_ARTIFACT_TOOLS = SPECIALIZED
BROWSER_CUA = SPECIALIZED_HIGH_AUTHORITY_TASKS_ONLY
SPEC_KIT = NOT_ACTIVE_FOR_QI
CODEX_APP = PARKED_UNLESS_EXPLICIT_TASK

`AVAILABLE != REQUIRED`, `REQUIRED != INVOKED`, `INVOKED != SUCCEEDED`, and
`SUCCEEDED != AUTHORITY`. `ROUTER != AUTHORITY`; a routing result never grants
write scope.

## Authority by fact type

- `HUMAN_A0`: material intent, priorities, and approvals.
- `WORK_ORDER`: authorized objective, scope, and acceptance contract.
- `LIVE_GIT_GITHUB`: branch, commit, PR, and CI truth.
- `CURRENT`: governed active handoff and transition state.
- `ROADMAP_DELTA_SPINE`: architecture, product evolution, and durable context.
- `FOREIGN_PLUGIN_MEMORY`: advisory only.

Resolve conflict by fact type instead of defining one universal source winner.

Task Envelope routing:

- `qi-task-envelope` derives the subordinate `TASK_ENVELOPE` from the approved Work Order and read-only Boot.
- The envelope has exactly ten fields and never widens scope or grants authority; mismatches are `ENTRY_HOLD`.
