# Development toolchain

```text
DOCUMENT_CLASS = CURRENT DEVELOPMENT / TOOLCHAIN CONTRACT
```

The production application and Windows installer use only `[project].dependencies`.
Development checks are installed separately with:

```powershell
python -m pip install -e ".[dev]"
python -m pytest
ruff check .
```

`python -m pytest` is the canonical full Python test command. Targeted tests
may precede the full suite for implementation Work Packages. Ruff, diff checks,
CI, smoke and release checks are separate gates when applicable; the active
Work Order and CI Fitness Contract define which gates are required. Hosted CI
unavailable is not CI PASS.

`pytest-xdist` is an experimental local convenience tool; use
`python -m pytest -n 4` only after a team member has confirmed the affected
tests are safe to run in parallel. No speed-up is assumed or promised.

## Reserved future capability groups

The following are design reservations only. They are not dependencies, are not
installed by `[dev]`, and are not included in the installer:

| Group | Candidate package | Boundary |
| --- | --- | --- |
| `pdf-geometry` | `pymupdf` | Optional PDF geometry support. |
| `pdf-table` | `pdfplumber` | Optional PDF table inspection. |
| `semantic` | `fastembed` | Candidate retrieval only; never creates HSMT facts. |
| `learning` | `scikit-learn` plus `pandas` or `polars` | Candidate rules only; no automatic promotion. |
| `llm` | `litellm` | Future opt-in integration only. |

Ollama, if adopted, is an external local service rather than a Python package.
SQLite remains the system of record. DuckDB/VSS is experimental and derived
only. Raw evidence is immutable; Ground Truth must pass evaluation and
regression before any extractor change is activated. QI-Crawler surfaces source
information, while Team Bid validates and decides.

## uv

`uv` can be evaluated in a separate workflow after lockfile, CI and Windows
installer reproducibility are agreed. This repository remains pip-based today.
