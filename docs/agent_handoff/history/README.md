# Handoff History

`history/` preserves bounded, as-of evidence from governed transitions. These
files are **HISTORICAL SNAPSHOT / NON-NORMATIVE** after capture. The active
execution authority is `docs/agent_handoff/CURRENT.md` reconciled with live
Git/GitHub.

## When to capture

- Parent PRE and POST checkpoints;
- agent/writer takeover;
- material interruption;
- architecture transition;
- major recovery;
- Parent closeout;
- material scope invalidation.

Ordinary Micro-WP editing and testing does not create a history file by
default. A Micro-WP still receives lightweight PRE/POST state in `CURRENT.md`.

## Naming

Use `CURRENT_<stage>_<wp-or-event>.md`, with a descriptive Work Package or
event identifier. The filename should make the as-of transition clear without
pretending to be current authority.

## Preservation

Never rewrite historical facts merely to match later state. Add a new snapshot
for a new transition. Keep unknown historical files, and add only the minimum
historical/non-normative banner when an existing snapshot lacks one.
