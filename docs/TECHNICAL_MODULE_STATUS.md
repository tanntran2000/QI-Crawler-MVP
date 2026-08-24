# Technical module status

```text
DOCUMENT_CLASS = TECHNICAL_STATUS_SNAPSHOT
SOURCE_STATE_AS_OF = d2aa8a9bded931d54aaa50c398b701b1598024ec
STATUS_SNAPSHOT != IMPLEMENTATION AUTHORITY
```

This is an as-of source/caller snapshot, not a roadmap or authorization. The
targeted source/CodeGraph review found the following bounded facts:

| Module | Evidence-backed status at SOURCE_STATE_AS_OF | Ownership / contract |
|---|---|---|
| `smart_filter.py` | EXISTS; `smart_search()` calls `execute_smart_filter()` internally; no external production caller found in the targeted scan | Legacy `Notice` natural-language filter; separate from MI `TargetedSearchRequest`; future integration requires verification |
| `notification.py` | EXISTS; `send_daily_digest()`/`send_email()` are module-internal in the targeted scan; no external production caller found | Notification contract and callers require verification before operational use |
| `egp_sources.py` | EXISTS; page-type registry helpers are present, but no external caller for `all_egp_sources()` was found | Relationship to `authenticated_sources.py` is partial/unproven; do not infer integration from file presence |
| `ai_classifier.py` | EXISTS; rule classifier calls are internal; no external CLI/API caller found | EXPERIMENTAL / UNWIRED; no production decision authority |
| `competitor_analysis.py` | EXISTS; no external caller found in the targeted scan | EXPERIMENTAL / UNWIRED; source data and owner require verification |
| `price_intelligence.py` | EXISTS; comparison/anomaly calls are internal; no external caller found | EXPERIMENTAL / UNWIRED; no approved pricing decision workflow |

For comparison, `authenticated_sources.py` has explicit CLI/monitoring callers
for authenticated collection, but that does not establish that every
`egp_sources.py` helper is wired into that path.

Do not delete, publicize or operationalize experimental/unwired modules until
tests, ownership, source contracts and acceptance criteria are explicitly
verified and approved.
