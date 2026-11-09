#!/usr/bin/env python3
"""Daily GitHub trending report pipeline.

Runs fetch, optional AI summaries, then HTML report generation.
"""
import runpy
from pathlib import Path

BASE = Path(__file__).resolve().parent


def run(script: str) -> None:
    print(f"\n=== {script} ===")
    runpy.run_path(str(BASE / script), run_name="__main__")


if __name__ == "__main__":
    run("fetch_trending.py")
    run("summarize_repos.py")
    run("generate_report.py")
