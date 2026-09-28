# WP-ENG-QI-WORKBENCH-LOCAL-VERIFICATION-DISPOSITION-01 rev2

## Mission and authority

```text
WP_ID = WP-ENG-QI-WORKBENCH-LOCAL-VERIFICATION-DISPOSITION-01 rev2
PARENT = WP-ENG-QI-WORKBENCH-IMPACT-READINESS-01 rev3
RELATED_MICRO_WP = WP-ENG-QI-WORKBENCH-HOSTED-VERIFICATION-01
ROLE_ID = BUILDER_SINGLE_WRITER
ROLE = BUILDER_SINGLE_WRITER
READ_MODE = DELTA
STATUS = AUTHORIZED → BUILDER_RUNNING → BUILDER_RETURNED_FOR_PLANNER_REVIEW
CANONICAL_CHECKOUT_EXPECTED = D:\QI Technology\QI Crawler\egp-crawler-python
EXPECTED_ORIGIN_REPOSITORY = https://github.com/tanntran2000/QI-Crawler-MVP.git
EXPECTED_BRANCH = codex/workbench-impact-readiness-01
EXPECTED_ENTRY_HEAD = e28800e946c813c8bf24b1f623fd60629fc5bb18
```

Human authorized this exact evidence-disposition Micro-WP in the instruction relayed through Planner task `/root` on 2026-09-28. The authorization covers one bounded retained-log analysis pass (maximum 30 minutes), this Work Order and locator/handoff updates, semantic local commit(s), and a proposal for zero to three future one-node diagnostics. It does not authorize diagnostic execution by Builder. A separate approved Planner activation is required before Tester can execute any proposed slot. This record does not invent a separate Human product, merge, or failure-root-cause decision.

The Parent candidate remains held. This Micro-WP classifies retained local evidence and proposes diagnostic questions; it does not repair product code, change tests, change the CI workflow, or promote product maturity. Local RED and scratch-budget failures remain historical facts. Hosted CI PASS is preserved only for exact source head `e28800e946c813c8bf24b1f623fd60629fc5bb18`.

## Roadmap and architecture layer contract

```text
ROADMAP_REVISION = 1.3
ROADMAP_BASELINE_SHA = 3e9d0e8705665e71a448fb88144adae5ae6f7923
PRODUCT_FRONTIER = UNIFIED TENDER WAREHOUSE; PARTIAL
ROADMAP_NODE = ENGINEERING TOOLBOX / PLUGINS; SUPPORTS CROSS-CUTTING WINDOWS / TEAM BID
DELTA = RD-0013 / B09 remains an open promotion gate; no B09 work in this WP
PRODUCT_MATURITY_PROMOTION = NONE
```

```text
ARCHITECTURE_LAYER_CONTRACT
PRODUCT_LANE: Engineering Toolbox / Plugins; local verification disposition
HUMAN_CONSUMER: Planner, Builder, Tester, Reviewer
MACHINE_CONSUMER: retained-log parsers and existing hosted CI evidence only
DOMAIN_CORE: OUT_OF_SCOPE
APPLICATION_BACKEND: OUT_OF_SCOPE
SOURCE_ADAPTERS: OUT_OF_SCOPE
PERSISTENCE_INFRA: OUT_OF_SCOPE
DELIVERY_ADAPTERS: OUT_OF_SCOPE
DESKTOP_FRONTEND: OUT_OF_SCOPE
CLI: OUT_OF_SCOPE
API: OUT_OF_SCOPE
AI_CONSUMER: OUT_OF_SCOPE
ENGINEERING_TOOLS: IN_SCOPE for bounded evidence interpretation and governance records
DEPENDENCY_DIRECTION_CHECK: PASS; no product-layer or dependency change
RATIONALE: This Micro-WP records local verification limitations under the existing engineering-tool lane; it adds no runtime or product capability.
```

## Exact entry objects and role gates

```text
CHECKOUT = D:\QI Technology\QI Crawler\egp-crawler-python
GIT_TOP_LEVEL = D:/QI Technology/QI Crawler/egp-crawler-python
GIT_DIR = .git
GIT_COMMON_DIR = .git
ORIGIN = https://github.com/tanntran2000/QI-Crawler-MVP.git
BRANCH = codex/workbench-impact-readiness-01
ENTRY_HEAD = e28800e946c813c8bf24b1f623fd60629fc5bb18
TRACKED_TREE = CLEAN
INDEX = CLEAN
WRITER_CONFLICT = NONE OBSERVED
UNTRACKED_NAMES_PRESERVED = $RECYCLE.BIN/; .codex/; WP_GOV_BLUEPRINT_KVS_HANDOFF_01_AUDIT.patch; WP_GOV_BLUEPRINT_KVS_HANDOFF_01_CORRECTION.patch; case-repro.ini; case-repro2.ini; output/; prep_data/; tmp/; uv.lock
UNKNOWN_UNTRACKED_CONTENT = NOT INSPECTED; KEEP
ROADMAP_ENTRY_GATE = PASS; DELTA READ; SAME PARENT/ARCHITECTURE
ROLE_ENTRY_GATE = PASS; ASSIGNED ROLE/WORK ORDER/CURRENT RECONCILE; SCOPE AND STOP CONDITIONS UNDERSTOOD
QI_CONTEXT_BOOT = READ_ONLY; CONTEXT_ENTRY_READY; IMPLEMENTATION AUTHORIZED ONLY BY THIS MICRO-WP
```

`CURRENT.md` is handoff evidence, not Git authority. The current task’s capture/live identities are re-resolved at the final precommit check. No remote operation is authorized or performed in this Micro-WP. The prior accepted Feedback entry for the Parent remains unchanged; this evidence-disposition task does not alter Human A0 intent.

## Bounded scope and exclusions

Exact tracked write scope:

1. `docs/superpowers/plans/WP-ENG-QI-WORKBENCH-LOCAL-VERIFICATION-DISPOSITION-01.md`
2. `docs/agent/PATH_REGISTRY.yaml`
3. `docs/agent_handoff/CURRENT.md`
4. Conditional only: `docs/agent/KNOWN_FAILURE_MODES.md` if this bounded evidence pass materially changes FM-054’s evidence-backed disposition or an authorized role accepts a prevention condition. This trigger was evaluated; no FM-054 edit is made because root-cause and prevention states remain unchanged.

No other tracked path may change. The exact retained evidence inputs are:

- `.tmp/WP-ENG-QI-WORKBENCH-IMPACT-READINESS-01/20260927T145300Z/full-pytest.log`
- `.tmp/WP-ENG-QI-WORKBENCH-IMPACT-READINESS-01/20260927T151000Z/full-pytest-infra-retry.log`
- Admitted hosted run `36373119614` and the terminal Tester/Reviewer evidence recorded in Parent/hosted governance.

The evidence files are retained inputs, not Builder-owned scratch. This WP did not scan, inspect or clean any unknown artifact or scratch tree. Do not edit the Parent skill, implementation, test, lock, product source, CI workflow, dependencies, B09 source/tests, runtime or live data. Do not run pytest, Ruff, CI, Codebase Memory indexing, or diagnostics. Do not push, mutate the PR, merge or release.

## Inputs and evidence provenance

The two retained logs were read directly by the Builder. Their observed file sizes were 9,471,566 bytes and 2,457,087 bytes respectively. The logs contain progress output, tracebacks and pytest short summaries; they do not provide a retained per-node JUnit outcome table or original complete command line. The set comparison below uses exact `FAILED` and `ERROR` node identifiers from each short summary. It does not infer a node’s individual pass/skip state from the absence of a short-summary failure line.

Prior admitted Tester report `WP-ENG-QI-WORKBENCH-IMPACT-READINESS-01-TESTER-CORRECTION-02-20260928T0035Z-01` records the changed routing-contract test passing and no failing rerun node in that changed test. No failure in the retained 65-node rerun set names `tests/agent_workbench/test_execution_skills_contract.py`. This is no direct test-path overlap; it is not proof that every candidate effect is absent.

Prior FM-054 and admitted Tester evidence retain the two scratch audits: 13,910 files / 621,941,751 bytes and 14,033 files / 614,887,749 bytes. Each exceeded the 10,000-file cap and remained under 2 GiB. The breach was detected only by the final hidden-inclusive post-run audit. FM-054 records `TEST_FAILURE_ROOT_CAUSES = NOT_FULLY_CLASSIFIED`, `PRODUCT_DEFECT_CAUSATION = NOT_ESTABLISHED`, `CANDIDATE_CAUSATION = NOT_ESTABLISHED`, related FM-051/FM-052, and the unresolved 276-character A3 path. Prevention remains proposed/pending, not implemented. This WP neither raises the cap nor rewrites those histories.

The repository-wide Ruff result remains Builder-reported RED with 8 errors in the preserved unknown `$RECYCLE.BIN` path. Tester did not independently verify it from a saved Ruff log. No unknown contents were opened in this WP.

Hosted evidence is `HOSTED_CI=PASS_PRESERVED_FOR_e28800e_ONLY`: pull_request run `36373119614`, attempt 1, completed success; source `e28800e946c813c8bf24b1f623fd60629fc5bb18`; base `51463a1ba01af9cd499e0b7c7cc961c19771bbf4`; merge preview `f629b3f49ec204eac593abc1db0c60047df6f54b`. The admitted terminal evidence reports: Code Quality PASS (36s, job `108773354661`); Tests Ubuntu 3.12 PASS (5m20s, `108773354677`); Tests Windows 3.12 PASS (9m44s, `108773354655`); Compatibility Ubuntu 3.11 PASS (5m12s, `108773354536`); Required CI Gate PASS (6s, `108775233219`) with all four dependencies successful. This is hosted job-level evidence for that exact execution; it does not classify individual nodes or erase local RED/scratch history.

## Disposition Result

| Evidence slice | Retained result | Current classification | Merge impact |
|---|---|---|---|
| First local full run | 136 failed, 1,531 passed, 4 skipped, 8 errors; 950.61s; 144 unique failed/error nodes | `LOCAL_HISTORY=RED_PRESERVED` | Whole Parent remains held. |
| Authorized local rerun | 65 failed, 1,610 passed, 4 skipped, 0 errors; 929.33s; 65 unique failed nodes | `LOCAL_HISTORY=RED_PRESERVED`; no new failed node | Whole Parent remains held; no further full run authorized. |
| Exact failure-set comparison | 65-node intersection; 0 rerun-only failures; 79 first-run failed/error nodes absent from rerun failed/error listing | 79 IDs below are `UNKNOWN_NODES` for individual rerun pass-versus-skip disposition; no node-level report is retained | The unresolved 65 rerun failures already keep local verification RED; absence of 79 from the failure list adds no distinct known failing node but is not recorded as per-node PASS. |
| A3/F5 guard signature | 23 rerun nodes across 15 report sections; all 15 sections show `STATE_WRITE_FAILURE` / missing-path state-file writes; these nodes also recur in the first run | Path/local-state influence is consistent with the evidence; sole-cause attribution is not established. A retained 276-character A3 path shows Windows path risk was not eliminated. | 23 repeated failures remain in the local RED set. No A3 code/test change is in this WP. |
| Other repeated failures | 42 nodes in document bundle/taxonomy, manual workspace, native extraction, document smoke/completeness, recovery, workspace intake/ops, and web intake | Mixed document-storage, missing-path and assertion signatures; not fully classified by matching traceback/fixture/input conditions across all 42 nodes | 42 repeated failures remain in the local RED set. No causal attribution to product or candidate. |
| Candidate path overlap | No rerun failure ID is in the changed routing-contract test file; Tester separately reported zero failing nodes in that test | `CANDIDATE_CAUSATION=NOT_ESTABLISHED` | No direct candidate/test-file overlap was found; whole-WP HOLD remains. |
| Scratch incident | Both runs breached 10,000-file limit; bytes were under 2 GiB; only final hidden-inclusive audit detected the breach | `SCRATCH_INCIDENT_DISPOSITION=PROPOSED/PENDING`; `TEST_FAILURE_ROOT_CAUSES=NOT_FULLY_CLASSIFIED`; prevention not implemented | Local full-run acceptance remains held; no cap increase. |
| Repository Ruff | Builder-reported 8 errors under unknown `$RECYCLE.BIN`; Tester had no saved Ruff log | `RUFF=RED_REPORTED_NOT_INDEPENDENTLY_LOG_VERIFIED` | Preserve as an open Parent limitation; no unrelated artifact inspection. |
| Codebase Memory | Skill read was denied in this execution context; callable read-only `list_projects` returned 0 projects; no indexing attempted | `CODEBASE_MEMORY_READINESS=HOLD_WITH_DIAGNOSIS`; exact managed cache/runtime path and bytes UNKNOWN; no coverage claim | No index evidence and no readiness promotion. |
| Hosted CI | Five required jobs passed on run `36373119614` for exact source e288 / merge preview f629 / base 51463a1 | `HOSTED_CI=PASS_PRESERVED_FOR_e28800e_ONLY`; job-level, not per-node | Complementary hosted evidence; it does not remove local RED, scratch FAIL, or the Parent HOLD. |

### Failure-set accounting and exact unknown node set

The first log contains 144 unique `FAILED`/`ERROR` identifiers (136 failed and 8 errors). The rerun contains 65 unique `FAILED` identifiers and no `ERROR` summary. Ordinal node-ID comparison found 65 in both, 0 new in the rerun, and 79 first-run IDs not in the rerun failed/error list. The aggregate counts are 1,679 outcomes in each run, but the retained logs do not bind the four skips to exact IDs or provide per-node rerun pass/skip rows. Therefore the 79 are listed as individually unclassified here rather than promoted to per-node PASS. The exact list is the set difference `FAILED/ERROR(full-pytest.log) minus FAILED(full-pytest-infra-retry.log)`:

```text
- tests/test_document_bundle_guard.py::test_no_identity_can_link_to_official_download_batch
- tests/test_document_intake.py::test_audit_log_contains_safe_intake_stages
- tests/test_document_intake.py::test_correct_tender_link_and_storage_are_identity_isolated
- tests/test_document_intake.py::test_database_failure_cleans_stored_orphan
- tests/test_document_intake.py::test_duplicate_sha_reuses_record_and_physical_file
- tests/test_document_intake.py::test_exact_duplicate_cannot_reassign_linked_document
- tests/test_document_intake.py::test_exact_source_url_is_trusted_identity_evidence
- tests/test_document_intake.py::test_folder_upload_imports_supported_files_only
- tests/test_document_intake.py::test_manifest_is_database_backed_and_normalizes_legacy_wp1_status
- tests/test_document_intake.py::test_same_file_same_tender_is_exact_duplicate
- tests/test_document_intake.py::test_same_filename_different_tender_is_not_same_document
- tests/test_document_intake.py::test_same_tender_changed_file_creates_new_version_without_overwrite
- tests/test_document_intake.py::test_supported_document_upload_preserves_original_and_sha256[bang-khoi-luong.xlsx-PK\x03\x04xlsx-content-XLSX]
- tests/test_document_intake.py::test_supported_document_upload_preserves_original_and_sha256[hsmt.pdf-%PDF-1.7\nmanual hsmt-PDF]
- tests/test_document_intake.py::test_supported_document_upload_preserves_original_and_sha256[yeu-cau.docx-PK\x03\x04docx-content-DOCX]
- tests/test_document_intake.py::test_unlinked_and_unknown_tender_are_never_guessed
- tests/test_document_intake.py::test_zip_upload_preserves_archive_and_records_supported_entries
- tests/test_document_taxonomy.py::test_intake_classifies_only_after_identity_guard_and_user_can_confirm
- tests/test_tender_case_service.py::test_add_document_reuses_document_intake_and_separates_membership
- tests/test_tender_case_service.py::test_foreign_embedded_ib_identity_cannot_be_source_membership
- tests/test_tender_case_service.py::test_matching_embedded_ib_identity_can_become_source_membership
- tests/test_tender_case_service.py::test_missing_managed_object_fails_closed
- tests/test_tender_case_service.py::test_reference_and_working_authorities_are_explicitly_non_source
- tests/test_tender_case_service.py::test_restart_and_external_source_deletion_preserve_managed_retrieval
- tests/test_tender_case_service.py::test_retrieve_managed_original_reopens_and_detects_tamper
- tests/test_tender_completeness_gui_services.py::test_completeness_gui_adapters_expose_domain_projection_and_exact_retrieval
- tests/test_tender_completeness_persistence.py::test_core_correction_history_and_restart_are_persistent
- tests/test_tender_completeness_persistence.py::test_same_sha_can_have_separate_release_memberships
- tests/test_tender_completeness.py::test_direct_ib_without_pl_and_one_file_can_cover_all_core_roles
- tests/test_tender_completeness.py::test_exact_revision_and_membership_guard_retrieval
- tests/test_tender_completeness.py::test_filename_only_does_not_confirm_a_core_role
- tests/test_tender_completeness.py::test_missing_referenced_appendix_is_needs_supplement
- tests/test_tender_completeness.py::test_partial_core_research_remains_readable_and_does_not_block_workspace
- tests/test_tender_completeness.py::test_publication_complete_list_missing_item_is_missing
- tests/test_tender_completeness.py::test_publication_complete_list_with_all_items_is_complete
- tests/test_tender_completeness.py::test_reference_only_membership_cannot_confirm_core_content
- tests/test_tender_recovery_gui_services.py::test_recovery_gui_scan_exposes_human_readable_integrity_state
- tests/test_tender_recovery_persistence.py::test_recovery_event_history_is_append_only_and_restartable
- tests/test_tender_recovery.py::test_exact_sha_candidate_is_recoverable_before_explicit_action
- tests/test_tender_recovery.py::test_exact_sha_recovery_restores_bytes_and_is_verified
- tests/test_tender_recovery.py::test_mismatch_is_quarantined_before_exact_replacement
- tests/test_tender_recovery.py::test_orphan_is_reported_without_auto_adoption
- tests/test_tender_recovery.py::test_recovery_is_idempotent_and_history_survives_restart
- tests/test_tender_recovery.py::test_recovery_rejects_membership_from_another_release
- tests/test_tender_recovery.py::test_recovery_scan_marks_missing_managed_object_fail_closed
- tests/test_tender_workspace_gui_services.py::test_exact_release_document_projection_preserves_membership_evidence_and_integrity
- tests/test_tender_workspace_gui_services.py::test_gui_service_adapters_delegate_workspace_manifest_and_export
- tests/test_tender_workspace_gui_services.py::test_gui_service_adapters_expose_recovery_scan_and_action
- tests/test_tender_workspace_gui_services.py::test_gui_service_adapters_open_create_and_assign_explicit_zone
- tests/test_tender_workspace_gui_services.py::test_gui_service_adapters_scan_and_add_confirmed_candidates
- tests/test_tender_workspace_gui_services.py::test_gui_service_adapters_search_dashboard_and_exact_export
- tests/test_tender_workspace_intake.py::test_first_chapter_three_candidate_gets_c3_01
- tests/test_tender_workspace_intake.py::test_only_explicitly_confirmed_candidates_are_ingested
- tests/test_tender_workspace_intake.py::test_original_source_bytes_are_unchanged
- tests/test_tender_workspace_intake.py::test_reference_only_foreign_candidate_remains_non_source
- tests/test_tender_workspace_intake.py::test_restart_reopen_preserves_managed_short_name
- tests/test_tender_workspace_intake.py::test_same_role_in_another_release_starts_again_at_01
- tests/test_tender_workspace_intake.py::test_same_sha_in_different_releases_keeps_distinct_memberships
- tests/test_tender_workspace_intake.py::test_second_chapter_three_candidate_gets_c3_02
- tests/test_tender_workspace_intake.py::test_short_name_is_not_database_identity
- tests/test_tender_workspace_ops.py::test_add_cleans_document_when_membership_validation_fails_after_intake
- tests/test_tender_workspace_ops.py::test_add_is_logically_atomic_when_workspace_assignment_fails
- tests/test_tender_workspace_ops.py::test_assigning_a_second_active_entry_to_same_slot_is_forbidden
- tests/test_tender_workspace_ops.py::test_dashboard_integrity_is_not_checked_until_bytes_are_verified
- tests/test_tender_workspace_ops.py::test_exact_release_export_isolates_revision_and_materializes_active_view
- tests/test_tender_workspace_ops.py::test_export_disambiguates_windows_collisions_deterministically
- tests/test_tender_workspace_ops.py::test_generic_source_replace_is_forbidden_and_source_correction_is_explicit
- tests/test_tender_workspace_ops.py::test_replace_rejects_embedded_identity_from_another_release
- tests/test_tender_workspace_ops.py::test_replace_uses_explicit_slot_and_same_sha_is_idempotent
- tests/test_tender_workspace_ops.py::test_source_correction_rejects_new_official_revision
- tests/test_tender_workspace.py::test_controlled_export_is_zone_layout_with_manifest_and_no_source_mutation
- tests/test_tender_workspace.py::test_export_does_not_overwrite_existing_destination
- tests/test_tender_workspace.py::test_export_materializes_all_team_bid_zone_directories_when_only_source_populated
- tests/test_tender_workspace.py::test_folder_intake_assigns_explicit_zones_and_reopens
- tests/test_tender_workspace.py::test_zip_is_supported_as_one_explicit_workspace_entry
- tests/test_web_document_intake.py::test_direct_discovery_downloads_pdf_docx_xlsx_and_zip
- tests/test_web_document_intake.py::test_direct_signed_url_uses_declared_mime_type
- tests/test_web_document_intake.py::test_dynamic_playwright_download_uses_same_intake_service
- tests/test_web_document_intake.py::test_rerun_is_duplicate_and_changed_file_is_new_version
```

$unknownMarkdown

```text
CANDIDATE_MERGE_BLOCKERS = LOCAL_FULL_SUITE_RED_UNRESOLVED; SCRATCH_FILE_CAP_FAIL; REPOSITORY_RUFF_RED_REPORTED_NOT_INDEPENDENTLY_LOG_VERIFIED; CODEBASE_MEMORY_HOLD; FINAL MERGE DECISION NOT MADE BY BUILDER
LOCAL_PATH_LIMITATIONS = 23 repeated A3/F5 state-write failures; missing-path symptom; 276-character A3 path; retry shortened basetemp root but did not eliminate reported path risk; 42 other failures are mixed and not individually cause-mapped
LOCAL_STATE_OR_ISOLATION_LIMITATIONS = two local executions differ in temporary root (`pytest-tmp` versus `p`); local state/path/environment influence is plausible, not sole-cause proof; 79 set-difference nodes lack individual pass/skip records
VERIFICATION_INFRASTRUCTURE_LIMITATIONS = scratch cap exceeded twice and detected only post-run; four skip IDs unavailable; first-run eight setup errors absent as retry failed/error nodes but no per-node retry status table; original full command lines/JUnit are not present in the retained logs; Ruff result not independently log-verified
UNKNOWN_NODES = 79 exact set above; 0 new rerun failures; no direct changed routing-test overlap; no per-node pass/skip proof; existing 65 failures continue to block a whole-local-verification PASS
SCRATCH_INCIDENT_DISPOSITION = PROPOSED/PENDING; FM-054 unchanged; no prevention implementation or accepted prevention decision
CODEBASE_MEMORY_FOLLOW_UP = Planner owns any future readiness reassessment; trigger only on a separately authorized, materially new diagnostic/input; this WP performs no index; cache/runtime path and storage bytes remain UNKNOWN
LOCAL_HISTORY = RED_PRESERVED
HOSTED_CI = PASS_PRESERVED_FOR_e28800e_ONLY
MERGE_RECOMMENDATION = PROPOSED_NO; Builder does not originate the final recommendation
PARENT_STATE = EVIDENCE_ONLY; WIR-R03/whole Parent HOLD; Planner/Reviewer/Human reconciliation remains separate
```

### Proposed Tester diagnostics (not activated or run)

The bounded pass proposes two one-node questions. Planner may activate zero, one, or both under the shared three-invocation total; Tester is the only executor. Builder ran none.

| Slot | Exact node | Question this node can discriminate | Maximum authorized conditions if activated |
|---|---|---|---|
| 1 | `tests/test_a3_f5_guard.py::test_stale_running_state_blocks_reuse` | Record the exact lifecycle-state temporary path length and parent existence, captured OS error, and whether a genuinely short task-owned basetemp changes the same node’s outcome; do not infer the result from sibling tests. | One exact node, ≤10 minutes, ≤3,000 incremental files and ≤512 MiB; use `.tmp/w3/<six-hex-batch>/i1/t`; verify projected deepest path ≤240 with ≥20 characters headroom against 260 before start. |
| 2 | `tests/test_tender_workspace_intake.py::test_original_filename_is_preserved` | Record the exact temporary/destination path lengths, parent state and `os.link`/storage exception under the same prechecked short-basetemp family; distinguish missing-parent/path behavior from other local storage conditions. | One exact node, ≤10 minutes, ≤3,000 incremental files and ≤512 MiB; use `.tmp/w3/<six-hex-batch>/i2/t`; verify projected deepest path ≤240 with ≥20 characters headroom against 260 before start. |

If both are activated, cumulative limits are ≤6,000 files and ≤1 GiB, below the shared maxima of 7,500 files and 1.5 GiB; preserve ≥10 GiB D: free, allow zero retries, and do no cleanup. The exact incremental expectation is UNKNOWN until measured; these are hard upper bounds, not a promise that the nodes fit. File-budget observation is post-run only, not hard in-run enforcement. Use the existing finite timeout mechanism; on timeout, verify invocation-owned child processes have stopped before another slot. If that cannot be established, stop. No wrapper may hide a pytest invocation. A pre-run path/headroom failure is HOLD before execution.

Before creating any diagnostic scratch, the activated Tester must register the chosen six-hex batch token in the approved batch-to-WP mapping for this Micro-WP. No mapping means HOLD before scratch creation. After each invocation, compare exact file and byte deltas against the per-slot and cumulative ceilings; any breach means HOLD the batch immediately, preserve the exact logs and counts, and do not start another slot. On timeout, verify only invocation-owned child processes have stopped; never terminate processes by generic process name. If process ownership or shutdown cannot be verified, stop the batch and return the evidence to Planner.

No third node is proposed in this initial pass because the mixed 42-node group has not been split into matching traceback/fixture/input classes. A further node requires Planner activation grounded in evidence from the first one or two slots. No diagnostic is automatically authorized by this Work Order alone.

## Codebase Memory and tool evidence

`CODEBASE_MEMORY_READINESS=HOLD_WITH_DIAGNOSIS`. The Builder attempted the repository-installed skill read at `C:\Users\Admin\.codex\skills\codebase-memory\SKILL.md`; this execution returned `UnauthorizedAccessException` (`TOOL_SKILL_READ_UNAVAILABLE`). Do not generalize that result to other contexts or claim the skill was invoked. The callable read-only `mcp__codebase_memory_mcp__list_projects` call returned `projects=[]`, `total=0`; no index command was called. Indexing is not authorized by this WP. The exact tool-managed cache/runtime path and bytes remain UNKNOWN. `persistence=false` is not evidence of no disk writes. No coverage, smoke, operational readiness, or full-repository completeness claim is made.

| Plugin/tool | Purpose / invocation / result | Fallback | Impact radius | Edit radius | Test radius | Limitation |
|---|---|---|---|---|---|---|
| `qi-context-boot` | Read `plugins/qi-agent-workbench/skills/qi-context-boot/SKILL.md`; canonical checkout, role/read mode and authority were reconciled; `USED_AND_SUCCEEDED`. | None needed. | Governance, handoff, retained-log evidence. | Three authorized docs only; conditional FM-054 trigger not met. | Static integrity checks only; no test execution. | Read-only boot does not grant extra scope. |
| CodeGraph | `codegraph explore` on `test_stale_running_state_blocks_reuse`, `test_original_filename_is_preserved`, and the document-store writer; `USED_AND_SUCCEEDED`; returned 79 symbols across 4 files and a `DocumentIntakeService` caller blast-radius summary. | Exact retained-log parsing and the admitted Parent/Tester evidence. | The graph reports shared document-store callers across source and test modules; it is impact intelligence only. | No source edit; governance records only. | No test execution; two diagnostic nodes proposed for possible future Tester activation. | Static graph evidence does not establish failure cause, candidate causation, or authority. The graph’s source excerpts were bounded and did not individually classify all 65 failures. |
| `codebase-memory` skill | Attempted exact SKILL read; `TOOL_SKILL_READ_UNAVAILABLE` due `UnauthorizedAccessException`; skill not invoked. | CodeGraph, retained logs, and bounded source-evidence fallback. | No indexed graph scope. | None. | None. | MCP `list_projects` returned zero; no indexing, cache scan, or coverage claim. |
| Codebase Memory MCP | Read-only `list_projects` returned zero projects; `USED_AND_SUCCEEDED` for the inventory query only. No `index_repository` call. | No index. | Zero projects reported. | None. | None. | A listing does not establish tool-managed path or cache size and is not operational readiness. |
| `verification-before-completion` | Read the installed skill before final claims/commit; perform exact scope, parse, key uniqueness, diff-check and tree checks before commit; `USED_AND_SUCCEEDED` only if those listed checks pass. | Not applicable. | Work Order, registry and active handoff. | Exactly the three unconditional docs. | No pytest/Ruff; they are forbidden in this lease. | Static/document verification cannot overturn Parent RED. |
| skill-creator / TDD / systematic-debugging | `NOT_APPLICABLE`: no skill or behavior edit; no new index failure to debug; no diagnostic run or fix. | None. | None. | None. | None. | Do not fabricate invocation evidence. |

## Failure Memory trigger disposition

FM-054 already records both exact file/byte breaches, late detection, `TEST_FAILURE_ROOT_CAUSES = NOT_FULLY_CLASSIFIED`, FM-051/FM-052 relation, the 276-character unresolved path, and proposed/pending prevention. This pass adds a bounded set comparison and repeats the unresolved local symptoms but establishes no new root cause and accepts no prevention condition. Therefore the conditional FM-054 write trigger is not met; preserve that file unchanged. If Planner later accepts a materially different causal/prevention classification, route that decision to Failure Memory in the same governed transition.

## Path Registry and artifact lifecycle

```text
PATH_REGISTRY_BASELINE = revision 1.0.19; SHA256 53CC3C23CC4375A74BA0E26DEFA301B0F1591968AFD5936A9BA9C37FEA853171
PATH_REGISTRY_IMPACT = ADD_ENTRY
ROADMAP_REF = docs/agent/MASTER_ROADMAP.md#engineering-toolbox--plugins; RD-0013 remains read-only context
WP_ID_AND_AUTHORITY = this exact Work Order; Human authorization relayed through Planner task /root
PATH_IDS_USED = PATH.GOV.PLAN; PATH.GOV.DOCUMENT; PATH.GOV.HANDOFF; PATH.DEV.TEST_TEMP; PATH.EVIDENCE.WP_RUN
ARTIFACTS = Work Order, locator registry binding, active CURRENT; retained input logs remain read-only; proposed diagnostic scratch only after Planner activation
WRITE_SCOPE = exact three files above; FM-054 conditional trigger not met
STORAGE_BUDGET = no Builder scratch; retained inputs are pre-existing; if Planner later activates two diagnostics, aggregate hard upper bound 6,000 files / 1 GiB and ≥10 GiB D: free
UNREGISTERED_WRITE_PATHS = NONE
PATH_REGISTRY_GATE = PASS after parse/unique-ID/path-ID verification
```

The new binding is locator-only. It grants no diagnostic execution, implementation, merge, release, B09 or product authority. Unknown is KEEP; this Work Order performs no cleanup or scratch inventory.

## CI Fitness Contract

```text
CURRENT WP: Bounded local verification evidence disposition; no capability change
CAPABILITY UNDER CHANGE: None; retained outcomes only
CRITICAL RISKS: Misclassifying missing nodes; turning hosted CI into local PASS; overclaiming environmental or candidate causation; losing scratch-limit history
BASELINE GATES TO KEEP: Preserve the existing exact local RED, scratch FAIL, hosted e288 PASS, and repo-Ruff limitation as separate evidence
WP-SPECIFIC GATES REQUIRED: Exact retained-log node-set comparison; mandatory Markdown/YAML-compatible registry parse; unique WP binding/path-ID checks; mandatory CURRENT key uniqueness; exact scope/status and git diff --check
GATES NOT REQUIRED YET: No pytest, Ruff, CI, Codebase Memory index, or product test; future diagnostics require Planner activation and Tester execution
MAX JOB RUNTIME: Evidence analysis ≤30 minutes; no test job in this Builder lease
CI CHANGE REQUIRED BEFORE IMPLEMENTATION: NO; this WP contains no implementation and changes no CI contract
RATIONALE: Disposition is bounded to retained evidence and governance. Hosted five-job PASS is exact-head complementary evidence; it cannot erase the prior local RED or scratch breach.
```

## Stages and acceptance criteria

A. Entry: confirm canonical checkout, origin, branch, expected head, tracked/index state, untracked-name preservation, Roadmap DELTA, role gate, Path Registry baseline, Parent and hosted evidence. Pass.

B. Evidence: read only the two named full-suite logs plus admitted hosted/tester/reviewer and existing FM-054/current evidence; compare exact failure/error sets in one bounded pass ≤30 minutes; do not inspect unknown artifacts or run tests. Complete with 144/65/65/0/79 accounting and explicit unknowns.

C. Governance: materialize this Work Order, one locator-only registry binding, and CURRENT update for this active Micro-WP. Do not modify FM-054 unless its stated conditional trigger becomes true.

D. Verification and return: JSON-compatible YAML parse; validate one new unique WP ID and existing PATH_ID references; check required Work Order sections and mandatory handoff keys/uniqueness; exact allowed name-status; `git diff --check`; tracked/index status; semantic local commit(s); return to Planner. No pytest, Ruff, full suite, diagnostics, index, or remote action.

Acceptance is a faithful bounded disposition with preserved Parent limitations, exact unknown-node reference/list, zero fabricated root-cause claims, zero unauthorized test execution, complete path/handoff metadata, allowed-scope docs checks and exact local commit evidence. It is not a whole-Parent pass, merge recommendation, or product maturity change.

## Stop conditions

Stop and return `STOP_FOR_REVIEW` on wrong checkout/origin/branch/head; tracked/index drift; writer conflict; any need to inspect unknown untracked or scratch contents; any need to exceed 30-minute evidence analysis; any need to execute diagnostics, tests, Ruff, CI or an index; any out-of-scope edit; any source/product defect requiring implementation; any inability to preserve historical local RED/scratch evidence; any unbounded or contradictory causal claim; or any remote/destructive need.

## Builder return packet

Return exact local commit SHA(s), changed paths, entry/base/head/branch, diff and tree checks, registry parse/unique binding results, all retained evidence counts, exact unknown node list, local path/state/infra limitations, candidate overlap, hosted CI evidence and provenance, FM-054 conditional decision, CodeGraph/CBM/plugin invocation-result-fallback-radii-limitation records, diagnostics proposed but not run, scratch/free-space facts and unknowns, and:

```text
SPINE_IMPACT = CURRENT
SPINE_TARGET_FILES = docs/agent_handoff/CURRENT.md
SPINE_SYNC_STATE = PASS
ROUTING_AND_RECONCILIATION = BOUNDED_EVIDENCE_DISPOSITION_RECORDED
CODEBASE_MEMORY_READINESS = HOLD_WITH_DIAGNOSIS
LOCAL_HISTORY = RED_PRESERVED
HOSTED_CI = PASS_PRESERVED_FOR_e28800e_ONLY
SCRATCH_INCIDENT_DISPOSITION = PROPOSED/PENDING
MERGE_RECOMMENDATION = PROPOSED_NO; final recommendation not originated by Builder
EXACTLY_ONE_NEXT_ACTION = Planner reviews the exact Builder evidence and decides whether to activate zero to three Tester diagnostic slots
NEXT_AUTHORITY = PLANNER_ARCHITECT
```
