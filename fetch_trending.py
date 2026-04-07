#!/usr/bin/env python3
"""
GitHub Trending Fetcher
Fetches TOP 10 trending GitHub repositories for daily report.
"""

import argparse
import json
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# Configuration
GITHUB_TRENDING_URL = "https://github.com/trending"
DATA_DIR = Path(__file__).parent / "data"
HISTORY_DIR = DATA_DIR / "history"
TOP_N = 10

# Beijing timezone (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))

# User agent
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def fetch_trending_html() -> str:
    """Fetch GitHub trending page HTML."""
    response = requests.get(GITHUB_TRENDING_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


def parse_trending(html: str) -> list[dict]:
    """Parse GitHub trending HTML using BeautifulSoup."""
    soup = BeautifulSoup(html, "lxml")
    repos = []
    articles = soup.find_all("article", class_="Box-row")

    for i, article in enumerate(articles[:TOP_N], 1):
        repo = {
            "rank": i,
            "fetched_at": datetime.now(BEIJING_TZ).isoformat(),
        }

        # Find author/name
        h2 = article.find("h2")
        if h2:
            link = h2.find("a")
            if link:
                href = link.get("href", "").strip("/")
                if "/" in href:
                    parts = href.split("/")
                    repo["author"] = parts[0]
                    repo["name"] = parts[1]
                    repo["url"] = f"https://github.com/{href}"

        # Description
        p = article.find("p")
        if p:
            repo["description"] = p.get_text(strip=True)

        # Language
        lang_span = article.find("span", itemprop="programmingLanguage")
        if lang_span:
            repo["language"] = lang_span.get_text(strip=True)

        # Stars and Forks
        for link in article.find_all("a"):
            href = link.get("href", "")
            text = link.get("text", "").strip()
            if "/stargazers" in href:
                repo["stars"] = text
            elif "/network/members" in href or "/forks" in href:
                repo["forks"] = text

        # Ensure all fields exist
        for field in ["author", "name", "url", "description", "language", "stars", "forks"]:
            repo.setdefault(field, "")

        repos.append(repo)

    return repos


def get_latest_history_file(exclude_today: bool = True) -> Path | None:
    """Get the most recent history file (yesterday's data)."""
    if not HISTORY_DIR.exists():
        return None

    files = sorted(HISTORY_DIR.glob("*.json"), reverse=True)
    today = datetime.now(BEIJING_TZ).strftime("%Y%m%d")

    for f in files:
        if f.name == ".gitkeep":
            continue
        # Extract date part (before any _)
        date_part = f.stem.split("_")[0]
        if exclude_today and date_part == today:
            continue
        return f
    return None


def save_data(repos: list, output_path: Path):
    """Save fetched data to file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(BEIJING_TZ).isoformat()

    data = {
        "timestamp": timestamp,
        "date": timestamp.split("T")[0],
        "repos": repos
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return data


def archive_to_history(data: dict):
    """Archive data to history folder."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    date_str = data["date"].replace("-", "")
    filename = HISTORY_DIR / f"{date_str}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return filename


def main():
    print(f"[{datetime.now(BEIJING_TZ).isoformat()}] Fetching GitHub trending...")

    try:
        html = fetch_trending_html()
        repos = parse_trending(html)

        if not repos:
            print("No repos found, exiting.")
            return

        # Save today's data
        today = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d")
        today_file = DATA_DIR / f"{today}.json"
        save_data(repos, today_file)

        # Archive to history
        history_file = archive_to_history({"timestamp": datetime.now(BEIJING_TZ).isoformat(), "date": today, "repos": repos})
        print(f"Archived to: {history_file}")

        print(f"\nFetched {len(repos)} repos:")
        for repo in repos[:3]:
            print(f"  #{repo['rank']}: {repo['author']}/{repo['name']} - {repo.get('language', '?')}")

        # Check for yesterday's data
        yesterday_file = get_latest_history_file()
        if yesterday_file:
            print(f"\nYesterday's data found: {yesterday_file.name}")
            print("Run generate_report.py to create the daily report.")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
