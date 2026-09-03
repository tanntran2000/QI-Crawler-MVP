---
name: qi-impact-map
description: Map code and test impact with CodeGraph before authorized edits.
---

# QI Impact Map

Before edits, invoke CodeGraph using the relevant symbols, files, or behavioral question. Record callers, contracts, adapters, persistence or delivery seams, and tests affected. CodeGraph improves impact intelligence; it never grants scope or authority.

## Governed radius and fallback

`impact_radius != edit_radius != test_radius` is mandatory: impact discovery may be broader than the authorized edit set, and the test radius is independently chosen to discriminate the approved behavior. Never collapse these radii into one scope.

`CodeGraph = impact intelligence only`. Its callers and dependency results inform risk and test selection; they do not grant edit scope, implementation permission, or a new architecture.

If CodeGraph cannot be invoked, report `TOOL_UNAVAILABLE → governed manual fallback` and perform a bounded manual impact map from the approved files, symbols, and repository references. The fallback must preserve the same exclusions and authority checks.

`IMPACT_SCOPE_GRANT = FORBIDDEN`.

If CodeGraph is unavailable, report `TOOL_UNAVAILABLE` and use the documented repository fallback. Stop for missing scope or a material architecture conflict. Preserve Human, Planner, Builder, and Reviewer boundaries.

Required output: `IMPACT_MAP` with `IMPACT_RADIUS`, `EDIT_RADIUS`, `TEST_RADIUS`, invocation/result or fallback, risks, exclusions, and one next authority.
