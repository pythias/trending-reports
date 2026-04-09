#!/usr/bin/env python3
"""
AI Summarizer for GitHub Trending Repos
Generates concise, engaging one-line descriptions for each repo using LLM.
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Try to import openai / anthropic, fallback to MiniMax
try:
    from openai import OpenAI
    HAS_LLM = True
except ImportError:
    OpenAI = None  # type: ignore
    HAS_LLM = False

# Configuration
DATA_DIR = Path(__file__).parent / "data"
HISTORY_DIR = DATA_DIR / "history"
BEIJING_TZ = timezone(timedelta(hours=8))

# LLM config - use MiniMax by default (via minimax:// prefix)
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
MINIMAX_BASE_URL = os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.chat/v1")
MINIMAX_MODEL = os.environ.get("MINIMAX_MODEL", "MiniMax-Text-01")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


def get_today_file() -> Path | None:
    today = datetime.now(BEIJING_TZ).strftime("%Y%m%d")
    today_file = HISTORY_DIR / f"{today}.json"
    if today_file.exists():
        return today_file
    # find most recent
    files = sorted(HISTORY_DIR.glob("????????.json"), reverse=True)
    return files[0] if files else None


def save_enriched(data: dict, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_summary_prompt(repo: dict) -> str:
    """Build prompt for a single repo summarization."""
    desc = repo.get("description", "") or "无描述"
    return (
        f"你是一个科技记者，为中文读者写一句简短有吸引力的介绍（25-50字）。\n"
        f"项目：{repo.get('author', '')}/{repo.get('name', '')}\n"
        f"语言：{repo.get('language', '未知')}\n"
        f"官方描述：{desc}\n"
        f"要求：\n"
        f"1. 用中文\n"
        f"2. 突出这个项目做什么、为什么有趣或重要\n"
        f"3. 不要重复项目名\n"
        f"4. 不要有引号或特殊格式\n"
        f"5. 直接返回句子，不要前缀"
    )


def generate_summary_openai(client: OpenAI, model: str, prompt: str) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=80,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def generate_summary_minimax(client: OpenAI, prompt: str) -> str:
    response = client.chat.completions.create(
        model="MiniMax-Text-01",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=80,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def main():
    print(f"[{datetime.now(BEIJING_TZ).isoformat()}] Generating AI summaries for trending repos...")

    today_file = get_today_file()
    if not today_file:
        print("No today's data found. Run fetch_trending.py first.")
        return

    data = json.loads(today_file.read_text(encoding="utf-8"))
    repos = data.get("repos", [])
    if not repos:
        print("No repos found in data.")
        return

    # Initialize LLM client
    llm_client = None
    llm_type = None

    if MINIMAX_API_KEY:
        try:
            llm_client = OpenAI(api_key=MINIMAX_API_KEY, base_url=MINIMAX_BASE_URL)
            llm_type = "minimax"
            print(f"Using MiniMax LLM: {MINIMAX_MODEL}")
        except Exception as e:
            print(f"MiniMax init failed: {e}")
            llm_client = None

    if not llm_client and OPENAI_API_KEY:
        try:
            llm_client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
            llm_type = "openai"
            print(f"Using OpenAI LLM: {OPENAI_MODEL}")
        except Exception as e:
            print(f"OpenAI init failed: {e}")

    if not llm_client:
        print("WARNING: No LLM API key found. Summaries will be skipped.")
        print("Set MINIMAX_API_KEY or OPENAI_API_KEY environment variable.")
        return

    # Generate summaries
    for repo in repos:
        prompt = build_summary_prompt(repo)
        try:
            if llm_type == "minimax":
                summary = generate_summary_minimax(llm_client, prompt)
            else:
                summary = generate_summary_openai(llm_client, OPENAI_MODEL, prompt)
            repo["summary"] = summary
            print(f"  #{repo['rank']}: {repo['name']} → {summary[:40]}...")
        except Exception as e:
            print(f"  #{repo['rank']} {repo.get('name', '')} failed: {e}")
            repo["summary"] = repo.get("description", "暂无摘要")

    # Save enriched data
    save_enriched(data, today_file)
    print(f"\nEnriched data saved to: {today_file}")


if __name__ == "__main__":
    main()
