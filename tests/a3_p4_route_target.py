"""Disposable process topology for the A3 route containment characterization."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=("chain", "spawn", "sleep"), required=True)
parser.add_argument("--pid-out", type=Path, required=True)
args = parser.parse_args()

if args.mode == "sleep":
    args.pid_out.write_text(str(os.getpid()), encoding="ascii")
    time.sleep(30)
else:
    next_mode = "spawn" if args.mode == "chain" else "sleep"
    child = subprocess.Popen(
        [sys.executable, __file__, "--mode", next_mode, "--pid-out", str(args.pid_out)]
    )
    args.pid_out.with_suffix(".parent").write_text(str(os.getpid()), encoding="ascii")
    args.pid_out.with_suffix(".child").write_text(str(child.pid), encoding="ascii")
