"""Preflight or explicitly execute the fixed-root INTERNAL_PILOT promotion."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from qi_crawler.operational_release import (
    OperationalReleaseError,
    promote_live_operational_root,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-root", required=True, type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--preflight", action="store_true", help="validate only (the default)")
    mode.add_argument("--execute-live-promotion", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = promote_live_operational_root(
            args.bundle_root,
            source_checkout_root=ROOT,
            execute=bool(args.execute_live_promotion),
        )
    except OperationalReleaseError as exc:
        print(json.dumps({"status": "HOLD", "error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
