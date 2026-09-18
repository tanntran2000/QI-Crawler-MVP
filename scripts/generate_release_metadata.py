from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qi_crawler import __version__
from qi_crawler.db import CURRENT_SCHEMA_REVISION

SCHEMA_VERSION = "qi-crawler-installed-release-v1"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def generate_installed_metadata(
    bundle_root: Path,
    *,
    source_git_sha: str,
    source_branch: str,
    release_channel: str,
    build_timestamp_utc: str,
) -> dict[str, str]:
    bundle = bundle_root.resolve(strict=True)
    executable = bundle / "QI-Crawler.exe"
    if not executable.is_file():
        raise ValueError("QI-Crawler.exe is missing from the bundle")
    if not re.fullmatch(r"[0-9a-fA-F]{40}", source_git_sha):
        raise ValueError("source_git_sha must be an exact 40-character Git SHA")
    if release_channel not in {"INTERNAL_CANDIDATE", "INTERNAL_PILOT"}:
        raise ValueError("release_channel must remain an internal candidate/pilot value")

    portable_hash = _sha256(executable)
    manifest = {
        "metadata_schema_version": SCHEMA_VERSION,
        "product": "QI-Crawler",
        "version": __version__,
        "source_git_sha": source_git_sha.lower(),
        "source_branch": source_branch,
        "build_timestamp_utc": build_timestamp_utc,
        "alembic_head": CURRENT_SCHEMA_REVISION,
        "release_channel": release_channel,
        "portable_exe_sha256": portable_hash,
    }
    _write_text(
        bundle / "VERSION.txt",
        f"QI-Crawler\nVersion: {__version__}\nChannel: {release_channel.replace('_', ' ')}",
    )
    _write_text(
        bundle / "WHAT_IS_NEW.txt",
        """QI-Crawler 0.10.0 - expected cumulative changes from operational 0.9.0

- Human-Light Excel Screening
- Team Bid operational screening profile
- Tender Completeness and core HSMT readiness
- Managed-source integrity
- Exact-SHA recovery workflow
- Team Bid workspace and review workflow improvements

This metadata describes the candidate content. Runtime acceptance is not yet claimed.""",
    )
    _write_text(
        bundle / "CAPABILITIES.txt",
        """QI-Crawler 0.10.0 capability contract

State: INCLUDED / EXPECTED / NOT_YET_RUNTIME_VERIFIED

- Source intake and Bid Radar filtering
- Human Review and protected exports
- Team Bid workspace, revision and evidence inspection
- Managed document integrity and Bundle Guard
- Tender completeness and core HSMT readiness
- Exact-SHA recovery safeguards

Engineering governance and A3/F5 containment are not user capabilities.""",
    )
    _write_text(
        bundle / "BUILD_INFO.txt",
        "\n".join(f"{key}={value}" for key, value in manifest.items()),
    )
    (bundle / "release_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate installed QI-Crawler metadata.")
    parser.add_argument("--bundle-root", required=True, type=Path)
    parser.add_argument("--source-git-sha", required=True)
    parser.add_argument("--source-branch", required=True)
    parser.add_argument("--release-channel", required=True)
    parser.add_argument("--build-timestamp-utc", required=True)
    args = parser.parse_args()
    try:
        generate_installed_metadata(
            args.bundle_root,
            source_git_sha=args.source_git_sha,
            source_branch=args.source_branch,
            release_channel=args.release_channel,
            build_timestamp_utc=args.build_timestamp_utc,
        )
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
