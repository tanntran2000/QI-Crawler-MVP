#!/usr/bin/env python3
"""Read-only deterministic integrity verifier for the QI Workbench."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

# Governance boundaries: a green lock check is not authority.
READ_ONLY = True
DETERMINISTIC = True
FAIL_CLOSED = True
LOCAL = True
NO_NETWORK = True
NO_AUTO_FIX = True
NO_AUTO_SYNC = True
GOVERNANCE_BOUNDARIES = (
    "LOCK != AUTHORITY",
    "LOCK_VERIFY_PASS != HUMAN_APPROVAL",
    "MACHINE_VERIFIED != HUMAN_APPROVED",
    "FAILURE_MEMORY != SELF_MODIFYING_WORKBENCH",
    "GROUND_TRUTH != AUTOMATIC_GOVERNANCE_RULE",
)

_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
_NORMALIZATION = "utf8_text_lf"


class MalformedLock(ValueError):
    """Raised when a lock manifest is invalid or unsafe to interpret."""


def _read_manifest(lock_path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MalformedLock(f"cannot read JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise MalformedLock("manifest must be an object")
    if raw.get("schema_version") != 1:
        raise MalformedLock("unsupported schema_version")
    if raw.get("algorithm") != "sha256":
        raise MalformedLock("unsupported algorithm")
    if raw.get("normalization") != _NORMALIZATION:
        raise MalformedLock("unsupported normalization")
    files = raw.get("files")
    if not isinstance(files, dict) or not files:
        raise MalformedLock("files must be a non-empty object")
    for relative, digest in files.items():
        if not isinstance(relative, str) or not relative:
            raise MalformedLock("file paths must be non-empty strings")
        normalized = relative.replace("\\", "/")
        parts = normalized.split("/")
        if (
            normalized.startswith("/")
            or re.match(r"^[A-Za-z]:", normalized)
            or any(part in {"", ".", ".."} for part in parts)
        ):
            raise MalformedLock(f"file path must be relative and safe: {relative}")
        if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
            raise MalformedLock(f"invalid sha256 digest for {relative}")
    return raw


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    canonical = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    digest.update(canonical)
    return digest.hexdigest()


def verify(root: Path, lock_path: Path) -> int:
    root = root.resolve()
    try:
        manifest = _read_manifest(lock_path.resolve())
    except MalformedLock as exc:
        print(f"malformed lock: {exc}", file=sys.stderr)
        return 4

    for relative, expected in manifest["files"].items():
        candidate = (root / Path(*relative.replace("\\", "/").split("/"))).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            print(f"malformed lock: path escapes root: {relative}", file=sys.stderr)
            return 4
        if not candidate.is_file():
            print(f"missing locked artifact: {relative}", file=sys.stderr)
            return 2
        try:
            actual = _digest(candidate)
        except (OSError, UnicodeError) as exc:
            print(f"invalid UTF-8 artifact: {relative}: {exc}", file=sys.stderr)
            return 3
        if actual.lower() != expected.lower():
            print(
                f"digest mismatch: {relative} expected {expected} got {actual}",
                file=sys.stderr,
            )
            return 3

    print(f"INTEGRITY PASS: {len(manifest['files'])} artifacts")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify a local Workbench lock manifest")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Workbench root containing the locked relative paths",
    )
    parser.add_argument(
        "--lock",
        type=Path,
        default=None,
        help="Optional lock manifest path (defaults to ROOT/skills-lock.json)",
    )
    args = parser.parse_args(argv)
    lock_path = args.lock or args.root / "skills-lock.json"
    return verify(args.root, lock_path)


if __name__ == "__main__":
    raise SystemExit(main())
