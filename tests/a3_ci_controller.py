"""Synthetic F4/F5 handshake actor; never release acceptance or a real controller.

Only disposable Windows utility bytes are moved. The real probe owns process
containment, observation, fault injection, recovery and aggregate validation.
The CLI deliberately matches the historical controller's handshake interface.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import time
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: dict[str, object]) -> None:
    raw = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if len(raw) > 1048576:
        raise RuntimeError("MATERIAL_WRITE_BOUND_EXCEEDED: TX_STATE")
    temporary = path.with_suffix(".tmp")
    with temporary.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ("install-root", "tx-root", "stub", "db-root"):
        parser.add_argument("--" + argument, type=Path, required=True)
    parser.add_argument("--failpoint", choices=["A3-F4-F5"], required=True)
    args = parser.parse_args()
    canonical = args.install_root / "QI-Crawler" / "QI-Crawler.exe"
    markers = args.tx_root / "markers"
    markers.mkdir(parents=True)
    recovery = args.tx_root / "legacy" / "QI-Crawler.exe"
    recovery.parent.mkdir()
    state: dict[str, object] = {
        "synthetic": True, "pid": os.getpid(), "canonical_path": str(canonical),
        "legacy_sha256": sha256(canonical), "stub_sha256": sha256(args.stub),
    }
    shutil.copy2(canonical, recovery)
    shutil.copy2(args.stub, canonical)
    for phase, checkpoint in (("BARRIER_CANDIDATE", "A3-F4"), ("BARRIER_CONFIRMED", "A3-F5")):
        state["phase"] = phase
        write_json(args.tx_root / "cutover.json", state)
        (markers / f"{checkpoint}.ready").write_text(checkpoint, encoding="utf-8")
        deadline = time.monotonic() + 60
        while not (markers / f"continue-{checkpoint}").exists():
            if time.monotonic() > deadline:
                raise RuntimeError("SYNTHETIC_HANDSHAKE_TIMEOUT")
            time.sleep(0.05)


if __name__ == "__main__":
    main()
