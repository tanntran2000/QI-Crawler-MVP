# QI-Crawler repository guardrails

## Repository map

- Production: `src/qi_crawler/`; tests: `tests/`; migrations: `alembic/versions/`
- Packaging: `packaging/`; scripts: `scripts/`; docs: `docs/`; templates: `templates/`
- Important root helpers: `evaluate_qi_crawler.py`, `pyproject.toml`, `alembic.ini`, tracked build/release scripts.
- Generated only: `.pytest_cache/`, `.ruff_cache/`, `__pycache__/`, `build/`, `dist/`, `release_staging/`, approved `.tmp/` children.

## Safety rules

1. Unknown is **KEEP**. Never delete a tracked file without the user's exact request.
2. Never infer generated status from a `.py`, `.ps1`, `.toml`, `.ini`, `.md`, or migration filename.
3. Before deletion: check `git status`, `git ls-files`, reproducibility, and an explicit allowlist. Never recursively delete the repository root.
4. Never delete `src/`, `tests/`, `alembic/`, `packaging/`, `scripts/`, `docs/`, `templates/`, fixtures, or tracked root helpers.
5. Use `scripts/clean_dev.ps1 -WhatIf` first. Permission/ACL errors must warn and skip; never take ownership or elevate.
6. Small task: inspect only relevant source/tests. Avoid unrelated modules and speculative refactors; stop if scope expands unexpectedly.
7. Validation: targeted `python -m pytest` → `python -m pytest` → `ruff check .` → `git diff --check` → `git diff --name-status`.
8. A task fails on unexpected source deletion. Never commit/push unless explicitly asked; never alter stable tags.

TOKEN MODE: LOW

Follow AGENTS.md strictly.

Task:
<việc cần làm>

Scope:
<file/module cho phép>

Do not modify outside scope unless required.
If scope expansion is required, STOP and report first.

Minimal diff.
Targeted tests first.
Full verification gate at end.
TEST SAFETY

At the beginning of a coding task:
- record current pytest collection count.

At final verification:
- collection must not unexpectedly decrease.
- any decrease requires root-cause investigation.
- never add/duplicate tests merely to satisfy a numeric count.
- historical test counts are informational unless tied to a verified commit.
- zero collection errors and zero failing tests are mandatory.
