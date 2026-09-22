const DATA_BASE = "data";
const WEEKDAYS = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"];

const els = {
    select: document.getElementById("date-select"),
    prev: document.getElementById("prev-date"),
    next: document.getElementById("next-date"),
    meta: document.getElementById("meta"),
    stats: document.getElementById("stats"),
    ranking: document.getElementById("ranking"),
    fallen: document.getElementById("fallen"),
};

let dates = [];

function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
    }[char]));
}

function repoKey(repo) {
    return `${repo.author}/${repo.name}`;
}

function dateToFile(date) {
    return date.replaceAll("-", "");
}

function formatDate(dateStr) {
    const [year, month, day] = dateStr.split("-").map(Number);
    const date = new Date(year, month - 1, day);
    const weekday = WEEKDAYS[date.getDay()];
    return `${year}年${String(month).padStart(2, "0")}月${String(day).padStart(2, "0")}日 ${weekday}`;
}

function selectedDateFromUrl(latest) {
    const params = new URLSearchParams(window.location.search);
    const fromQuery = params.get("date");
    if (fromQuery && dates.includes(fromQuery)) {
        return fromQuery;
    }
    return latest;
}

function setUrl(date, latest) {
    const url = new URL(window.location.href);
    if (date === latest) {
        url.searchParams.delete("date");
    } else {
        url.searchParams.set("date", date);
    }
    history.replaceState({}, "", url);
}

function classify(current, previous) {
    const prevMap = new Map(previous.map((repo) => [repoKey(repo), repo.rank]));
    const currentKeys = new Set(current.map(repoKey));
    const stayed = [];
    const incoming = [];

    for (const repo of current) {
        const key = repoKey(repo);
        const prevRank = prevMap.get(key);
        if (prevRank == null) {
            incoming.push({ ...repo, changeType: "新晋", prevRank: null });
        } else {
            const diff = prevRank - repo.rank;
            stayed.push({
                ...repo,
                changeType: diff >= 3 ? "大涨" : "留榜",
                prevRank,
                diff,
            });
        }
    }

    const fallen = previous
        .filter((repo) => !currentKeys.has(repoKey(repo)))
        .map((repo) => ({ ...repo, changeType: "落榜" }));

    return { incoming, stayed, fallen, rows: [...incoming, ...stayed] };
}

function changeLabel(repo) {
    if (repo.changeType === "新晋") {
        return { text: "新晋", cls: "is-new" };
    }
    if (repo.changeType === "大涨") {
        return { text: `大涨 ${repo.prevRank}→${repo.rank}`, cls: "is-up" };
    }
    if (repo.diff > 0) {
        return { text: `↑ ${repo.prevRank}→${repo.rank}`, cls: "is-up" };
    }
    if (repo.diff < 0) {
        return { text: `↓ ${repo.prevRank}→${repo.rank}`, cls: "" };
    }
    if (repo.prevRank != null) {
        return { text: `留榜 #${repo.rank}`, cls: "" };
    }
    return { text: `#${repo.rank}`, cls: "" };
}

async function loadJson(path) {
    const response = await fetch(path);
    if (!response.ok) {
        throw new Error(`无法读取 ${path}`);
    }
    return response.json();
}

function renderSelect(latest, current) {
    els.select.innerHTML = dates.map((date) => {
        const selected = date === current ? " selected" : "";
        return `<option value="${date}"${selected}>${date}</option>`;
    }).join("");
    const index = dates.indexOf(current);
    els.prev.disabled = index >= dates.length - 1;
    els.next.disabled = index <= 0;
    document.title = current === latest
        ? "GitHub Trending 日报"
        : `GitHub Trending 日报 · ${current}`;
}

function renderReport(currentData, previousData, currentDate, previousDate) {
    const currentRepos = currentData.repos || [];
    const previousRepos = previousData?.repos || [];
    const classified = classify(currentRepos, previousRepos);
    const ranked = [...classified.rows].sort((a, b) => a.rank - b.rank);

    els.meta.textContent = previousDate
        ? `${formatDate(currentDate)} · 对比 ${previousDate}`
        : `${formatDate(currentDate)} · 首次记录`;

    els.stats.hidden = false;
    els.stats.innerHTML = `
        <div class="stat">新晋 <strong>${classified.incoming.length}</strong></div>
        <div class="stat">留榜 <strong>${classified.stayed.length}</strong></div>
        <div class="stat">落榜 <strong>${classified.fallen.length}</strong></div>
    `;

    els.ranking.innerHTML = ranked.map((repo) => {
        const badge = changeLabel(repo);
        const summary = repo.summary || repo.description || "暂无简介";
        const language = repo.language
            ? `<span class="lang"><i></i>${escapeHtml(repo.language)}</span>`
            : "";
        const stars = repo.stars ? `<span>★ ${escapeHtml(repo.stars)}</span>` : "";
        const starsToday = repo.stars_today ? `<span>${escapeHtml(repo.stars_today)}</span>` : "";
        return `
            <li class="repo">
                <div class="rank">${String(repo.rank).padStart(2, "0")}</div>
                <div class="repo-head">
                    <a class="repo-name" href="${escapeHtml(repo.url)}" target="_blank" rel="noopener">${escapeHtml(repoKey(repo))}</a>
                    <span class="change ${badge.cls}">${escapeHtml(badge.text)}</span>
                </div>
                <p class="desc">${escapeHtml(summary)}</p>
                <div class="meta-row">${language}${stars}${starsToday}</div>
            </li>
        `;
    }).join("");

    if (classified.fallen.length) {
        els.fallen.hidden = false;
        els.fallen.innerHTML = `
            <h2>上一期落榜</h2>
            <div class="fallen-list">
                ${classified.fallen.map((repo) => `
                    <a class="fallen-item" href="${escapeHtml(repo.url)}" target="_blank" rel="noopener">
                        ${escapeHtml(repoKey(repo))}
                        <span>原 #${escapeHtml(repo.rank)}</span>
                    </a>
                `).join("")}
            </div>
        `;
    } else {
        els.fallen.hidden = true;
        els.fallen.innerHTML = "";
    }
}

async function showDate(date, latest) {
    const index = dates.indexOf(date);
    const previousDate = dates[index + 1] || null;
    const currentData = await loadJson(`${DATA_BASE}/${dateToFile(date)}.json`);
    const previousData = previousDate
        ? await loadJson(`${DATA_BASE}/${dateToFile(previousDate)}.json`)
        : null;

    renderSelect(latest, date);
    renderReport(currentData, previousData, date, previousDate);
    setUrl(date, latest);
}

async function init() {
    try {
        const manifest = await loadJson(`${DATA_BASE}/dates.json`);
        dates = manifest.dates || [];
        if (!dates.length) {
            els.meta.textContent = "还没有历史数据。先运行 fetch_trending.py。";
            return;
        }
        const latest = manifest.latest || dates[0];
        const current = selectedDateFromUrl(latest);
        await showDate(current, latest);

        els.select.addEventListener("change", () => showDate(els.select.value, latest));
        els.prev.addEventListener("click", () => {
            const index = dates.indexOf(els.select.value);
            if (index < dates.length - 1) {
                showDate(dates[index + 1], latest);
            }
        });
        els.next.addEventListener("click", () => {
            const index = dates.indexOf(els.select.value);
            if (index > 0) {
                showDate(dates[index - 1], latest);
            }
        });
        window.addEventListener("popstate", () => {
            showDate(selectedDateFromUrl(latest), latest);
        });
    } catch (error) {
        els.meta.textContent = error.message || "载入失败";
    }
}

init();
