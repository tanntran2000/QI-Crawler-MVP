# QI-Crawler candidate release contract

This contract governs the future v0.10.0 portable candidate assembly and its
first access to copied business data. It does not authorize a build, data copy,
migration, launch, installation, publication, promotion, tag, release, or merge.

## Canonical candidate layout

The future Build Work Order must resolve one fresh boundary with this pattern:

```text
D:\QI-Crawler-Candidates\
  v0.10.0-<FROZEN_SHORT_SHA>-<BUILD_ID>\
    app\
      QI-Crawler\
    data-root\
    output\
    control\
    evidence\
```

The candidate boundary, application root, and data root must be physically and
logically disjoint from `D:\QI-Crawler` and
`%LOCALAPPDATA%\QI-Crawler`. Before first business startup, the controlled gate
must validate the exact build, frozen source SHA, clone receipt, migration
receipt, migrated database, managed-document mapping, and candidate-only
configuration. Invalid evidence means the application is not launched.

## Storage budget

All values are byte ceilings for one candidate run. The managed-document limit
is a sublimit of the cloned-data limit and is not counted twice when calculating
required free space.

| Category | Ceiling |
| --- | ---: |
| Build intermediates | 6 GiB |
| Portable bundle | 3 GiB |
| Candidate cloned data, total | 12 GiB |
| Managed documents within cloned data | 10 GiB |
| Migration backup and migration evidence | 2 GiB |
| Acceptance outputs and durable evidence | 2 GiB |
| Logs | 256 MiB |
| Temporary files | 4 GiB |
| Untouched safety reserve after the run | 4 GiB |

The future Build Work Order must calculate required headroom before any material
write. The minimum is the sum of all applicable top-level ceilings plus the
4 GiB safety reserve: 33.25 GiB when every category above is needed. A category
may receive a smaller per-run lease when PRE measurements justify it; no
category may exceed its ceiling without a new Human/Planner authorization.

The run must record:

1. **PRE:** exact resolved roots, volume identity, free bytes, source DB/WAL/SHM
   bytes, managed-document bytes, planned per-category leases, and required
   safety reserve.
2. **RUN:** bytes created per category and remaining free space. Stop before the
   next write if a lease, category ceiling, or reserve would be crossed.
3. **POST:** retained bytes, reclaimed task-owned transient bytes, remaining
   free space, and disposition of every created root.

Unknown artifacts are `KEEP`. Cleanup requires an exact task-owned allowlist and
the Path Registry lifecycle rules. No working runtime or user-data bytes may be
counted as reclaimable headroom.

## Evidence stages

`CLONE_RECEIPT` is authoritative for the pre-migration candidate state.
`MIGRATION_RECEIPT` supersedes the clone database-byte identity after a
successful isolated migration. `PRE_FIRST_BUSINESS_STARTUP_ACCEPTANCE` binds the
approved initial operational state. The clone hash is not a permanent runtime
invariant after normal application writes begin.
