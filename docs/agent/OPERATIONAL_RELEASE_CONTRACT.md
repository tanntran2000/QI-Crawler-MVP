# Operational release contract

This contract defines the separate `INTERNAL_PILOT` runtime lane introduced by
B09. It does not convert a candidate into an installed release and it does not
authorize promotion, installation, migration of live data or release.

## Stable layout

An operational root is a stable root such as `D:\QI-Crawler` with these
boundaries:

```text
Current\QI-Crawler\QI-Crawler.exe
Current\QI-Crawler\runtime\
Current\QI-Crawler\BUILD_INFO.txt
Current\QI-Crawler\release_manifest.json
Data\config.yaml
Data\data\database\egp.db
Data\data\documents\
Data\data\downloads\
Data\data\discovery\
Data\data\raw\
Data\data\rejects\
Data\data\reports\
Data\data\sessions\
Data\data\backups\
Data\logs\
control\operational_acceptance.json
control\operational_migration_receipt.json
```

`Current\QI-Crawler` is immutable application content for the accepted bundle;
`Data` is the mutable operational root. Both must remain inside the one stable
root and must not overlap. The candidate layout and its
`pre_start_acceptance.json` remain a separate contract.

## Direct-start binding

Before configuration or database construction, a frozen executable whose
manifest declares `release_channel=INTERNAL_PILOT` must pass the operational
acceptance receipt and bind:

```text
QI_CRAWLER_DATA_DIR=D:\QI-Crawler\Data
QI_CRAWLER_CONFIG_PATH=D:\QI-Crawler\Data\config.yaml
QI_CRAWLER_DATABASE_URL=sqlite:///D:/QI-Crawler/Data/data/database/egp.db
```

The validator fails closed for a missing or substituted candidate receipt,
unexpected layout, root/path escape, metadata/hash mismatch, unsupported
schema, missing migration provenance or a database outside `Data`.

## Acceptance receipt

The canonical schema is `qi-crawler-operational-acceptance-v1` at
`control\operational_acceptance.json`. It binds the operational root,
application bundle, executable, data/config/database paths, product/version,
source SHA, build timestamp, `INTERNAL_PILOT` channel, executable/manifest/
BUILD_INFO hashes, target schema, migration receipt SHA and migration source
provenance. The companion
`qi-crawler-operational-migration-v1` receipt records the source SHA,
`0020_add_tender_operational_revision_events` input and
`0022_add_tender_recovery_events` output.

## Promotion model

Only synthetic roots are accepted by the B09 primitive. A future live
promotion must follow:

```text
read-only source
→ consistent SQLite copy
→ migration on the copy
→ staged operational receipt
→ staged validation
→ same-volume atomic root rotation
→ post-cutover validation
→ deterministic rollback on failure
```

The active AppData database and `D:\QI-Crawler` are never migrated or copied
in place by this phase. The portable operational path is preferred; the B02
Inno Setup installer remains deferred and is not required for B09.
