#!/usr/bin/env python3
"""Run the daily GitHub trending pipeline."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = [
    "fetch_trending.py",
    "summarize_repos.py",
    "generate_report.py",
]


def main() -> int:
    for name in SCRIPTS:
        script = ROOT / name
        print(f"\n=== {name} ===")
        result = subprocess.run([sys.executable, str(script)], cwd=ROOT)
        if result.returncode != 0:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
