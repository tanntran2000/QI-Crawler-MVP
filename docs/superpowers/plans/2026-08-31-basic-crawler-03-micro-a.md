# WP-TB-BASIC-CRAWLER-03 Micro-A — Evidence Plan

## Purpose

Establish, with direct code inspection, isolated runtime checks and bounded
source evidence, what already works and what materially blocks the approved
Parent-03 revision-transition and controlled-folder-intake contract. This plan
does not authorize product implementation or correction.

## Evidence gates

1. Prove the canonical D checkout, branch and audited PRE base before any
   inspection or test run.
2. Inspect the existing domain, application, source-adapter, persistence and
   delivery seams; use CodeGraph for caller/dependency paths where useful.
3. Attempt one bounded search of already-available project assets for a real
   lineage with at least two published revisions. Record `EVIDENCE_GAP` when
   none is available; never fabricate identity or membership.
4. Run the narrowest existing tests needed to establish current behavior.
5. Reproduce folder-selection behavior only in disposable temporary storage;
   label synthetic observations `TEST_MECHANISM_EVIDENCE_ONLY`.
6. Classify every observed capability as `IMPLEMENTED_AND_PROVEN`, `PARTIAL`,
   `ABSENT` or `REQUIRES_REAL_EVIDENCE`, then classify findings as
   `MATERIAL_PRODUCT_BLOCKER`, `EVIDENCE_GAP`, `ALREADY_PROVEN`,
   `PARTIAL_CAPABILITY` or `OUT_OF_SCOPE`.
7. Update only `CURRENT.md` with factual Micro-A results and keep the exactly-
   one next action directed to Planner review. Do not change Delta, memory,
   failure memory, source, tests, schema or live data.

## Required checks

- `python -m pytest tests/test_tender_workspace.py -q`
- Any additional targeted command must be recorded with its result.
- `python -m ruff check .`
- `git diff --check`
- `git status --short`

## Safety boundaries

Use only read-only source evidence and isolated temporary SQLite/document/export
roots. Do not rename, move, delete or mutate user files. Do not create Human
Review events or claim real package authority from synthetic files. Micro-A
ends at evidence and Planner review; Micro-B requires a separate authorization.
