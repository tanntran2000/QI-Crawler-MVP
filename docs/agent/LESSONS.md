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
