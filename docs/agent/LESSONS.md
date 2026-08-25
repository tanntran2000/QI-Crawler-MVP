# Systemic Lessons

These are durable engineering lessons, not a chat log or a list of minor
fixes.

1. **Filename is not identity.** Use content, source, SHA, revision, and
   explicit provenance; never verify a package from a filename alone.
2. **Partial output is not completeness.** A successful export or crawl must
   reconcile every input into exported, rejected, deduplicated, skipped, or
   pending accounting states.
3. **CI green is evidence, not proof of absence of all bugs.** CI must be fit
   for the active Work Package, and runtime anomalies require bounded triage.
4. **Derived XLSX/DOCX is not the source of record.** SQLite, review history,
   and immutable source evidence remain authoritative.
5. **Impact radius differs from edit radius and test radius.** Trace broadly,
   edit minimally, and verify the contracts actually affected.
6. **P0 or false-safe behavior means HOLD.** Preserve evidence, add a focused
   regression, and do not weaken a guard to make a test pass.
7. **Cross-layer Work Orders require explicit direction checks.** Classify
   changed production files by Product House layer and audit dependency
   direction explicitly; green functional tests alone do not prove layer
   separation.
8. **Review exact objects first.** Independent review should inspect the exact
   Git range directly when available; copied patches are transport evidence,
   not object authority.
9. **Handoffs cannot predict their own future SHA.** Keep capture-base,
   audit-target and live-Git identities separate; reconcile known docs-only
   ancestry instead of creating sync-of-sync claims.
