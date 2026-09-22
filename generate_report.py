#!/usr/bin/env python3
"""
Publish history JSON for the static report page.

Daily runs only need new data. This script copies `data/history/*.json`
into `docs/data/` and writes `docs/data/dates.json`. The HTML template
is not regenerated.
"""

import json
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent
HISTORY_DIR = BASE_DIR / "data" / "history"
DOCS_DATA_DIR = BASE_DIR / "docs" / "data"


def history_dates() -> list[str]:
    dates = []
    if HISTORY_DIR.exists():
        for path in HISTORY_DIR.glob("*.json"):
            date_part = path.stem.split("_")[0]
            if date_part.isdigit() and len(date_part) == 8:
                dates.append(f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}")
    dates.sort(reverse=True)
    return dates


def publish_docs_data() -> Path:
    dates = history_dates()
    if not dates:
        raise SystemExit("No history JSON found. Run fetch_trending.py first.")

    DOCS_DATA_DIR.mkdir(parents=True, exist_ok=True)

    for date_str in dates:
        src = HISTORY_DIR / f"{date_str.replace('-', '')}.json"
        dest = DOCS_DATA_DIR / src.name
        shutil.copy2(src, dest)

    manifest = {
        "latest": dates[0],
        "dates": dates,
    }
    manifest_path = DOCS_DATA_DIR / "dates.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main():
    print("Publishing report data...")
    manifest_path = publish_docs_data()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    print(f"  dates: {len(payload['dates'])}")
    print(f"  latest: {payload['latest']}")
    print(f"  manifest: {manifest_path}")
    print("HTML template is unchanged. Open docs/index.html via a local server.")


if __name__ == "__main__":
    main()
