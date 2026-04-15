#!/usr/bin/env python3
"""
GitHub Trending Report Generator - 新版
生成含「今日榜单变化表」「亮点」「分类卡片」的报告页面。
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
HISTORY_DIR = DATA_DIR / "history"
DOCS_DIR = BASE_DIR / "docs"
OUTPUT_FILE = DOCS_DIR / "index.html"


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_available_dates() -> list[str]:
    dates = []
    if HISTORY_DIR.exists():
        for f in HISTORY_DIR.glob("*.json"):
            date_part = f.stem.split("_")[0]
            if date_part.isdigit() and len(date_part) == 8:
                dates.append(date_part)
    dates.sort(reverse=True)
    return [f"{d[:4]}-{d[4:6]}-{d[6:8]}" for d in dates]


def date_to_history_path(date_str: str) -> Path:
    return HISTORY_DIR / f"{date_str.replace('-', '')}.json"


def get_date_pair(target_date: str, available_dates: list[str]):
    if target_date not in available_dates:
        return None, None
    current_file = date_to_history_path(target_date)
    prev_file = None
    idx = available_dates.index(target_date)
    if idx + 1 < len(available_dates):
        prev_file = date_to_history_path(available_dates[idx + 1])
    return (current_file if current_file.exists() else None,
            prev_file if prev_file and prev_file.exists() else None)


def build_prev_rank_map(previous: list) -> dict:
    """Build {author/name: rank} map from previous day's data."""
    return {f"{r['author']}/{r['name']}": r.get("rank", 99) for r in previous}


def classify_repos(current: list, previous: list) -> dict:
    """
    Classify repos into 新晋/留榜/落榜/回归/大涨.
    Also compute change type for each current repo.
    """
    prev_map = build_prev_rank_map(previous)
    prev_names = set(prev_map.keys())
    curr_names = {f"{r['author']}/{r['name']}" for r in current}

    new_names = curr_names - prev_names
    stayed_names = curr_names & prev_names
    fallen_names = prev_names - curr_names

    result = {
        "新晋": [],
        "留榜": [],
        "落榜": [],
    }

    # Track which prev repos returned (for 回归 detection)
    returned_names = set()

    for r in current:
        key = f"{r['author']}/{r['name']}"
        rank = r.get("rank", 99)
        prev_rank = prev_map.get(key, None)

        r["change_type"] = ""
        r["prev_rank"] = prev_rank

        if key in new_names:
            r["change_type"] = "新晋"
            result["新晋"].append(r)
        elif prev_rank is not None:
            diff = prev_rank - rank  # positive = moved up
            if diff >= 3:
                r["change_type"] = "大涨"
            elif diff > 0:
                r["change_type"] = "留榜"
            else:
                r["change_type"] = "留榜"
            result["留榜"].append(r)
        else:
            # Was fallen before, now returned
            r["change_type"] = "回归"
            if key not in returned_names:
                returned_names.add(key)
                result["新晋"].append(r)

    for r in previous:
        key = f"{r['author']}/{r['name']}"
        if key in fallen_names:
            r["change_type"] = "退榜"
            result["落榜"].append(r)

    # Remove duplicates in 新晋 that were actually 回归
    # (keep first occurrence)
    return result


def format_date(date_str: str) -> str:
    if not date_str:
        return "未知"
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%Y年%m月%d日")


def get_output_filename(date_str: str, latest_date: str) -> str:
    if date_str == latest_date:
        return "index.html"
    return f"date-{date_str}.html"


def generate_date_nav(available_dates: list, current_date: str, latest_date: str) -> str:
    nav_items = ""
    for d in available_dates[:14]:
        display = format_date(d)
        active = "bg-emerald-500/20 text-emerald-400" if d == current_date else "text-slate-400 hover:bg-slate-800"
        href = get_output_filename(d, latest_date)
        nav_items += f'<a href="{href}" class="px-2.5 py-1 rounded-md text-xs {active} transition-colors">{display}</a>\n'
    return nav_items


# ---- Change table ----

def make_change_badge(change_type: str, rank: int, prev_rank: int = None) -> str:
    badges = {
        "蝉联": ("text-yellow-400", "👑"),
        "大涨": ("text-emerald-400", "↑"),
        "新晋": ("text-emerald-400", "🆕"),
        "回归": ("text-blue-400", "🔄"),
        "留榜": ("text-slate-400", "➡"),
        "退榜": ("text-amber-400", "↓"),
    }
    cls, icon = badges.get(change_type, ("text-slate-400", "•"))
    label = change_type
    if change_type == "大涨" and prev_rank:
        label = f"大涨 {icon} {prev_rank}→{rank}"
    elif change_type == "新晋":
        label = f"🆕 #{rank}"
    elif change_type == "回归":
        label = f"🔄 #{rank}"
    elif change_type == "留榜":
        label = f"➡ #{rank}"
    elif change_type == "退榜":
        label = f"退榜"
    return f'<span class="inline-flex items-center gap-0.5 text-xs font-medium {cls}">{label}</span>'


def generate_change_table(current: list, previous: list) -> str:
    """Generate the 今日榜单 change table rows."""
    if not current:
        return '<tr><td colspan="3" class="py-4 text-center text-slate-500">暂无数据</td></tr>'

    prev_map = {f"{r['author']}/{r['name']}": r.get("rank", 99) for r in previous}
    prev_names = set(prev_map.keys())

    # Sort: 蝉联 > 大涨 > 新晋 > 回归 > 留榜
    order = {"蝉联": 0, "大涨": 1, "新晋": 2, "回归": 3, "留榜": 4, "退榜": 5}

    def sort_key(r):
        ct = r.get("change_type", "留榜")
        return (order.get(ct, 5), -(r.get("rank", 99)))

    sorted_repos = sorted(current, key=sort_key)

    rows = ""
    for r in sorted_repos:
        key = f"{r['author']}/{r['name']}"
        rank = r.get("rank", "?")
        prev_rank = prev_map.get(key, None)
        change_type = r.get("change_type", "留榜")

        # Determine badge
        if change_type == "蝉联" or (prev_rank == 1 and rank <= 3):
            badge = "👑 蝉联"
        elif change_type == "大涨" and prev_rank:
            badge = f"↑ {prev_rank}→#{rank}"
        elif change_type == "新晋":
            badge = f"🆕 #{rank}"
        elif change_type == "回归":
            badge = f"🔄 #{rank}"
        elif change_type == "留榜":
            badge = f"➡ #{rank}"
        else:
            badge = f"#{rank}"

        badge_cls = {
            "蝉联": "text-yellow-400",
            "大涨": "text-emerald-400",
            "新晋": "text-emerald-400",
            "回归": "text-blue-400",
            "留榜": "text-slate-400",
            "退榜": "text-amber-400",
        }.get(change_type, "text-slate-400")

        # Build description
        desc = ""
        summary = r.get("summary", "") or r.get("description", "")
        if len(summary) > 60:
            summary = summary[:57] + "..."
        desc = summary

        rows += f"""
        <tr class="hover:bg-slate-800/40 transition-colors">
            <td class="py-2.5 px-3 {badge_cls} font-medium text-xs whitespace-nowrap">{badge}</td>
            <td class="py-2.5 px-3">
                <a href="{r.get('url', '#')}" target="_blank" rel="noopener" class="hover:text-white transition-colors">
                    <span class="font-mono text-slate-200">{r.get('author', '')}/{r.get('name', '')}</span>
                </a>
            </td>
            <td class="py-2.5 px-3 text-slate-400 text-xs hidden sm:table-cell line-clamp-2">{desc}</td>
        </tr>"""

    return rows


# ---- Repo cards ----

LANG_COLORS = {
    "Python": "bg-yellow-500",
    "JavaScript": "bg-yellow-400",
    "TypeScript": "bg-blue-400",
    "Rust": "bg-orange-500",
    "Go": "bg-cyan-500",
    "Java": "bg-red-500",
    "C++": "bg-pink-500",
    "Kotlin": "bg-purple-500",
    "Shell": "bg-green-500",
}

BADGE_COLORS = {
    "新晋": "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    "留榜": "bg-blue-500/20 text-blue-400 border-blue-500/30",
    "落榜": "bg-amber-500/20 text-amber-400 border-amber-500/30",
    "回归": "bg-purple-500/20 text-purple-400 border-purple-500/30",
}


def generate_repo_card(repo: dict, category: str) -> str:
    badge_cls = BADGE_COLORS.get(category, "bg-slate-500/20 text-slate-400 border-slate-500/30")
    lang = repo.get("language", "")
    lang_color = LANG_COLORS.get(lang, "bg-slate-500")
    summary = repo.get("summary", "") or repo.get("description", "暂无摘要")
    if len(summary) > 100:
        summary = summary[:97] + "..."
    stars = repo.get("stars", "")
    forks = repo.get("forks", "")

    return f'''
    <article class="group relative bg-slate-800/50 border border-slate-700/50 rounded-xl p-4 hover:bg-slate-800/70 hover:border-slate-600/50 transition-all duration-150 cursor-pointer">
        <a href="{repo.get("url", "#")}" target="_blank" rel="noopener" class="absolute inset-0 z-10">
            <span class="sr-only">View {repo.get("name", "project")}</span>
        </a>
        <div class="flex items-start justify-between gap-3 mb-2">
            <div class="flex items-center gap-2.5">
                <div class="flex items-center justify-center w-8 h-8 rounded-lg bg-slate-700/50 text-slate-300 font-mono text-xs font-semibold">
                    #{repo.get("rank", "?")}
                </div>
                <div>
                    <h3 class="font-medium text-slate-200 group-hover:text-white transition-colors text-sm leading-tight">
                        {repo.get("author", "")}/{repo.get("name", "")}
                    </h3>
                </div>
            </div>
            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs border {badge_cls}">
                {category}
            </span>
        </div>
        <p class="text-slate-400 text-xs leading-relaxed mb-2 line-clamp-2">{summary}</p>
        <div class="flex items-center gap-3 text-xs text-slate-500">
            {f'<span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full {lang_color}"></span>{lang}</span>' if lang else ""}
            {f'<span>★ {stars}</span>' if stars else ""}
            {f'<span>⑂ {forks}</span>' if forks else ""}
        </div>
    </article>'''


def generate_section(title: str, icon: str, repos: list, category: str) -> str:
    if not repos:
        return f'''
    <section>
        <h2 class="flex items-center gap-2 text-base font-semibold text-slate-100 mb-4">
            <span class="text-xl">{icon}</span> {title}
            <span class="text-xs font-normal text-slate-500">(0)</span>
        </h2>
        <p class="text-slate-600 text-sm italic">暂无数据</p>
    </section>'''
    cards = "\n".join(generate_repo_card(r, category) for r in repos)
    return f'''
    <section>
        <h2 class="flex items-center gap-2 text-base font-semibold text-slate-100 mb-4">
            <span class="text-xl">{icon}</span> {title}
            <span class="text-xs font-normal text-slate-500">({len(repos)})</span>
        </h2>
        <div class="grid gap-3 sm:grid-cols-2">
            {cards}
        </div>
    </section>'''


# ---- Highlights ----

def generate_highlights(categorized: dict, current: list, previous: list) -> str:
    """Generate the 亮点 section from AI summaries."""
    new_repos = categorized.get("新晋", [])
    stayed_repos = categorized.get("留榜", [])
    fallen_repos = categorized.get("落榜", [])

    highlights = []

    if new_repos:
        names = [f"{r['author']}/{r['name']}" for r in new_repos[:3]]
        highlights.append(f"🆕 新晋项目：{', '.join(names)} 等 {len(new_repos)} 个项目首次上榜")

    # Look for standout items in summaries
    for r in current[:5]:
        summary = r.get("summary", "") or r.get("description", "")
        if len(summary) > 20:
            highlights.append(f"• {summary[:120]}")

    if stayed_repos and stayed_repos[0].get("summary"):
        top = stayed_repos[0]
        s = top.get("summary", "")[:100]
        highlights.append(f"📈 留榜亮点：{s}")

    if not highlights:
        return ""

    body = "\n".join(f"<li class='text-slate-300 text-sm leading-relaxed'>{h}</li>" for h in highlights)

    return f'''
    <section class="mb-8 bg-slate-800/40 border border-slate-700/40 rounded-xl p-5">
        <h2 class="flex items-center gap-2 text-base font-semibold text-slate-100 mb-3">
            <span>✨</span> 亮点
        </h2>
        <ul class="space-y-2 list-disc list-inside">
            {body}
        </ul>
    </section>'''


# ---- Main HTML generation ----

def generate_html(
    categorized: dict,
    current: list,
    previous: list,
    current_date: str,
    prev_date: str | None,
    available_dates: list,
    latest_date: str,
) -> str:
    template_path = Path(__file__).parent / "templates" / "report.html"
    html = template_path.read_text(encoding="utf-8") if template_path.exists() else ""

    date_nav = generate_date_nav(available_dates, current_date, latest_date)
    change_rows = generate_change_table(current, previous)
    highlights = generate_highlights(categorized, current, previous)

    new_repos = categorized.get("新晋", [])
    stayed_repos = categorized.get("留榜", [])
    fallen_repos = categorized.get("落榜", [])

    html = html.replace("{{CURRENT_DATE}}", format_date(current_date))
    html = html.replace("{{PREV_DATE}}", f"对比 {format_date(prev_date)}" if prev_date else "首次报告")
    html = html.replace("{{DATE_NAV}}", date_nav)
    html = html.replace("{{CHANGE_TABLE_ROWS}}", change_rows)
    html = html.replace("{{HIGHLIGHTS_SECTION}}", highlights)
    html = html.replace(
        "{{NEW_REPOS_SECTION}}",
        generate_section("新晋 Trending", "🆕", new_repos, "新晋"),
    )
    html = html.replace(
        "{{STAYED_REPOS_SECTION}}",
        generate_section("留榜 Trending", "📈", stayed_repos, "留榜"),
    )
    html = html.replace(
        "{{FALLEN_REPOS_SECTION}}",
        generate_section("落榜 Trending", "📉", fallen_repos, "落榜"),
    )

    return html


def build_report_for_date(target_date: str, available_dates: list, latest_date: str):
    current_file, yesterday_file = get_date_pair(target_date, available_dates)
    if not current_file:
        raise ValueError(f"Date data not found: {target_date}")

    current_data = load_json(current_file)
    current_repos = current_data.get("repos", [])
    current_date_str = current_data.get("date", target_date)

    previous_repos = []
    prev_date_str = None
    if yesterday_file and yesterday_file.exists():
        prev_data = load_json(yesterday_file)
        previous_repos = prev_data.get("repos", [])
        prev_date_str = prev_data.get("date")

    categorized = classify_repos(current_repos, previous_repos)

    print(f"\nReport for {current_date_str}:")
    print(f"  新晋: {len(categorized['新晋'])}  留榜: {len(categorized['留榜'])}  落榜: {len(categorized['落榜'])}")

    html = generate_html(categorized, current_repos, previous_repos, current_date_str, prev_date_str, available_dates, latest_date)
    output_file = DOCS_DIR / get_output_filename(target_date, latest_date)
    output_file.write_text(html, encoding="utf-8")
    print(f"  输出: {output_file}")
    return current_date_str, output_file


def main():
    print("Generating GitHub Trending Report...")
    args = argparse.ArgumentParser().parse_args()

    available_dates = get_available_dates()
    if not available_dates:
        print("No data found. Run fetch_trending.py first.")
        return

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    latest_date = available_dates[0]

    generated = []
    for date_str in available_dates:
        _, out = build_report_for_date(date_str, available_dates, latest_date)
        generated.append(out)

    print(f"\nGenerated {len(generated)} report files.")


if __name__ == "__main__":
    main()
