from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qi_crawler.candidate_data import CandidateDataError, prepare_candidate_data


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create an isolated candidate-data snapshot without mutating the source."
    )
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--destination-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = prepare_candidate_data(args.source_root, args.destination_root)
    except (CandidateDataError, OSError, sqlite3.Error) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
