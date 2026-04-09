#!/usr/bin/env python3
"""
GitHub Trending Report Generator
Generates daily report comparing with yesterday's data.
Homepage allows date navigation.
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
HISTORY_DIR = DATA_DIR / "history"
DOCS_DIR = BASE_DIR / "docs"
OUTPUT_FILE = DOCS_DIR / "index.html"

# Beijing timezone
BEIJING_TZ = timezone(timedelta(hours=8))


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_available_dates() -> list[str]:
    """Get all available report dates."""
    dates = []
    if HISTORY_DIR.exists():
        for f in HISTORY_DIR.glob("*.json"):
            date_part = f.stem.split("_")[0]  # Handle YYYYMMDD or YYYYMMDD_HHMM
            if date_part.isdigit() and len(date_part) == 8:
                dates.append(date_part)
    # Sort descending
    dates.sort(reverse=True)
    return [f"{d[:4]}-{d[4:6]}-{d[6:8]}" for d in dates]


def find_today_and_yesterday() -> tuple[Path | None, Path | None]:
    """Find today's and yesterday's data files."""
    today = datetime.now(BEIJING_TZ).strftime("%Y%m%d")
    yesterday = (datetime.now(BEIJING_TZ) - timedelta(days=1)).strftime("%Y%m%d")

    today_file = HISTORY_DIR / f"{today}.json"
    yesterday_file = HISTORY_DIR / f"{yesterday}.json"

    today_exists = today_file.exists()
    yesterday_exists = yesterday_file.exists()

    if not today_exists:
        # Try to find most recent
        available = get_available_dates()
        if len(available) >= 2:
            today_file = HISTORY_DIR / f"{available[0].replace('-', '')}.json"
            yesterday_file = HISTORY_DIR / f"{available[1].replace('-', '')}.json"
            today_exists = today_file.exists()
            yesterday_exists = yesterday_file.exists()
        elif len(available) == 1:
            today_file = HISTORY_DIR / f"{available[0].replace('-', '')}.json"
            today_exists = today_file.exists()
            yesterday_exists = False

    return (today_file if today_exists else None,
            yesterday_file if yesterday_exists else None)


def categorize_repos(current: list, previous: list) -> dict:
    """Categorize repos into 新晋/留榜/落榜."""
    prev_names = {f"{r['author']}/{r['name']}" for r in previous}
    curr_names = {f"{r['author']}/{r['name']}" for r in current}

    new_names = curr_names - prev_names
    stayed_names = curr_names & prev_names
    fallen_names = prev_names - curr_names

    return {
        "新晋": [r for r in current if f"{r['author']}/{r['name']}" in new_names],
        "留榜": [r for r in current if f"{r['author']}/{r['name']}" in stayed_names],
        "落榜": [r for r in previous if f"{r['author']}/{r['name']}" in fallen_names],
    }


def format_date(date_str: str) -> str:
    """Format YYYY-MM-DD to Chinese format."""
    if not date_str:
        return "未知"
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%Y年%m月%d日")


def generate_date_nav(available_dates: list, current_date: str) -> str:
    """Generate date navigation HTML."""
    nav_items = ""
    for d in available_dates[:14]:  # Show last 14 days
        display = d.replace("-", "")
        display_formatted = format_date(d)
        active = "bg-emerald-500/20 text-emerald-400" if d == current_date else "text-slate-400 hover:bg-slate-800"
        nav_items += f'''
            <a href="?date={d}" class="px-3 py-1.5 rounded-lg text-sm {active} transition-colors">
                {display_formatted}
            </a>
        '''
    return nav_items


def generate_repo_card(repo: dict, category: str) -> str:
    """Generate HTML card for a repository."""
    badge_colors = {
        "新晋": "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
        "留榜": "bg-blue-500/20 text-blue-400 border-blue-500/30",
        "落榜": "bg-amber-500/20 text-amber-400 border-amber-500/30",
    }
    lang_colors = {
        "Python": "bg-yellow-500",
        "JavaScript": "bg-yellow-400",
        "TypeScript": "bg-blue-400",
        "Rust": "bg-orange-500",
        "Go": "bg-cyan-500",
        "Java": "bg-red-500",
        "C++": "bg-pink-500",
        "Kotlin": "bg-purple-500",
    }
    lang_color = lang_colors.get(repo.get("language", ""), "bg-gray-500")
    badge = badge_colors.get(category, "bg-gray-500/20 text-gray-400 border-gray-500/30")

    # Get AI summary or description
    summary = repo.get("summary", "") or repo.get("description", "暂无摘要")
    if len(summary) > 100:
        summary = summary[:97] + "..."

    stars = repo.get("stars", "")
    forks = repo.get("forks", "")

    return f'''
        <article class="group relative bg-slate-800/50 border border-slate-700/50 rounded-xl p-5 hover:bg-slate-800/70 hover:border-slate-600/50 transition-all duration-200 cursor-pointer">
            <a href="{repo.get("url", "#")}" target="_blank" rel="noopener" class="absolute inset-0 z-10">
                <span class="sr-only">View {repo.get("name", "project")}</span>
            </a>

            <div class="flex items-start justify-between gap-4 mb-3">
                <div class="flex items-center gap-3">
                    <div class="flex items-center justify-center w-10 h-10 rounded-lg bg-slate-700/50 text-slate-300 font-mono text-sm font-semibold">
                        #{repo.get("rank", "?")}
                    </div>
                    <div>
                        <h3 class="font-semibold text-slate-100 group-hover:text-white transition-colors">
                            {repo.get("author", "")}/{repo.get("name", "")}
                        </h3>
                    </div>
                </div>
                <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border {badge}">
                    {category}
                </span>
            </div>

            <p class="text-slate-400 text-sm leading-relaxed mb-2 line-clamp-2">
                {summary}
            </p>
            <p class="text-slate-500 text-xs italic line-clamp-1">
                {repo.get("description", "")}
            </p>

            <div class="flex items-center gap-4 text-sm mt-3">
                {f'<span class="flex items-center gap-1.5 text-slate-400"><span class="w-2.5 h-2.5 rounded-full {lang_color}"></span>{repo.get("language", "—")}</span>' if repo.get("language") else ""}
                {f'<span class="flex items-center gap-1.5 text-slate-400"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"></path></svg>{stars}</span>' if stars else ""}
                {f'<span class="flex items-center gap-1.5 text-slate-400"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"></path></svg>{forks}</span>' if forks else ""}
            </div>
        </article>
    '''


def generate_section(title: str, icon: str, repos: list, category: str) -> str:
    if not repos:
        return f'''
        <section class="mb-10">
            <h2 class="flex items-center gap-3 text-xl font-semibold text-slate-100 mb-5">
                <span class="text-2xl">{icon}</span> {title}
                <span class="text-sm font-normal text-slate-500">(0 个项目)</span>
            </h2>
            <p class="text-slate-500 italic">暂无数据</p>
        </section>
        '''
    cards = "\n".join(generate_repo_card(r, category) for r in repos)
    return f'''
        <section class="mb-10">
            <h2 class="flex items-center gap-3 text-xl font-semibold text-slate-100 mb-5">
                <span class="text-2xl">{icon}</span> {title}
                <span class="text-sm font-normal text-slate-500">({len(repos)} 个项目)</span>
            </h2>
            <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
                {cards}
            </div>
        </section>
    '''


def generate_html(categorized: dict, current_date: str, prev_date: str | None, available_dates: list) -> str:
    """Generate complete HTML report."""
    template_path = Path(__file__).parent / "templates" / "report.html"
    html = template_path.read_text(encoding="utf-8") if template_path.exists() else ""

    # Date navigation
    date_nav = generate_date_nav(available_dates, current_date)

    # Summary
    total_new = len(categorized.get("新晋", []))
    total_stayed = len(categorized.get("留榜", []))
    total_fallen = len(categorized.get("落榜", []))

    # Replace placeholders
    html = html.replace("{{CURRENT_DATE}}", format_date(current_date))
    html = html.replace("{{PREV_DATE}}", f"（对比 {format_date(prev_date)}）" if prev_date else "（首次报告）")
    html = html.replace("{{DATE_NAV}}", date_nav)
    html = html.replace("{{SUMMARY}}", f"新晋 {total_new} · 留榜 {total_stayed} · 落榜 {total_fallen}")

    # Sections
    html = html.replace("{{NEW_REPOS_SECTION}}", generate_section("新晋 Trending", "🆕", categorized.get("新晋", []), "新晋"))
    html = html.replace("{{STAYED_REPOS_SECTION}}", generate_section("留榜 Trending", "📈", categorized.get("留榜", []), "留榜"))
    html = html.replace("{{FALLEN_REPOS_SECTION}}", generate_section("落榜 Trending", "📉", categorized.get("落榜", []), "落榜"))

    return html


def main():
    print("Generating GitHub Trending Report...")

    # Get available dates
    available_dates = get_available_dates()
    if not available_dates:
        print("No data found. Run fetch_trending.py first.")
        return

    # Find today's and yesterday's data
    today_file, yesterday_file = find_today_and_yesterday()

    if not today_file:
        print("No today's data found.")
        return

    current_data = load_json(today_file)
    current_repos = current_data.get("repos", [])
    current_date = current_data.get("date", today_file.stem)

    # Load previous data for comparison
    previous_repos = []
    prev_date = None
    if yesterday_file and yesterday_file.exists():
        prev_data = load_json(yesterday_file)
        previous_repos = prev_data.get("repos", [])
        prev_date = prev_data.get("date", yesterday_file.stem.replace("-", ""))

    # Categorize
    categorized = categorize_repos(current_repos, previous_repos)

    print(f"\nReport for {current_date}:")
    print(f"  新晋: {len(categorized['新晋'])}")
    print(f"  留榜: {len(categorized['留榜'])}")
    print(f"  落榜: {len(categorized['落榜'])}")

    # Generate HTML
    html = generate_html(categorized, current_date, prev_date, available_dates)

    # Save
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"\nReport generated: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
