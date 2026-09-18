from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qi_crawler.candidate_data import CandidateDataError
from qi_crawler.candidate_readiness import (
    CandidateReadinessError,
    accept_pre_first_business_startup,
    create_portable_artifact_receipt,
    launch_candidate_after_acceptance,
    migrate_candidate_data,
)


def _common_acceptance_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--candidate-root", required=True, type=Path)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--expected-frozen-source-sha", required=True)
    parser.add_argument("--expected-migration-receipt-sha256", required=True)
    parser.add_argument("--expected-version", required=True)
    parser.add_argument("--forbidden-root", action="append", default=[], type=Path)


def _acceptance_kwargs(args: argparse.Namespace) -> dict[str, object]:
    return {
        "candidate_root": args.candidate_root,
        "data_root": args.data_root,
        "expected_frozen_source_sha": args.expected_frozen_source_sha,
        "expected_migration_receipt_sha256": args.expected_migration_receipt_sha256,
        "expected_version": args.expected_version,
        "forbidden_roots": tuple(args.forbidden_root),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create and validate QI-Crawler candidate readiness evidence."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    portable_receipt = commands.add_parser(
        "portable-receipt", help="Create portable bundle identity evidence."
    )
    portable_receipt.add_argument("--candidate-root", required=True, type=Path)
    portable_receipt.add_argument("--expected-frozen-source-sha", required=True)
    portable_receipt.add_argument("--expected-version", required=True)
    migrate = commands.add_parser("migrate", help="Create Stage-2 migration evidence.")
    migrate.add_argument("--data-root", required=True, type=Path)
    migrate.add_argument("--source-repository-root", required=True, type=Path)
    migrate.add_argument("--expected-frozen-source-sha", required=True)
    migrate.add_argument("--forbidden-root", action="append", default=[], type=Path)
    accept = commands.add_parser("accept", help="Create Stage-3 pre-start evidence.")
    _common_acceptance_arguments(accept)
    launch = commands.add_parser(
        "launch", help="Accept and perform the controlled first business startup."
    )
    _common_acceptance_arguments(launch)
    args = parser.parse_args(argv)
    try:
        if args.command == "portable-receipt":
            result = create_portable_artifact_receipt(
                args.candidate_root,
                expected_frozen_source_sha=args.expected_frozen_source_sha,
                expected_version=args.expected_version,
            )
        elif args.command == "migrate":
            result = migrate_candidate_data(
                args.data_root,
                source_repository_root=args.source_repository_root,
                expected_frozen_source_sha=args.expected_frozen_source_sha,
                forbidden_roots=tuple(args.forbidden_root),
            )
        elif args.command == "accept":
            result = accept_pre_first_business_startup(**_acceptance_kwargs(args))
        else:
            launch_candidate_after_acceptance(**_acceptance_kwargs(args))
            result = {"status": "STARTED"}
    except (CandidateDataError, CandidateReadinessError, OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
