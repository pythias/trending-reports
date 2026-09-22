# GitHub Trending Report

每日抓取 GitHub Trending TOP 10。页面只有一份模板，历史日期用 JSON 渲染，不再为每一天生成 HTML。

## 每日流程

```bash
python3 fetch_trending.py
python3 generate_report.py    # 把 data/history 同步到 docs/data
```

`fetch_trending.py` 抓取当天榜单并写入 `data/history/YYYYMMDD.json`，同时发布到页面数据目录。`generate_report.py` 只同步 JSON 和日期清单，不改 HTML。

预览：

```bash
python3 -m http.server 8080 --directory docs
```

打开 `http://localhost:8080/`。历史日期用页面上的选择器切换，或访问 `/?date=2026-09-22`。

## 数据

| 路径 | 说明 |
|------|------|
| `data/history/YYYYMMDD.json` | 每日原始数据 |
| `docs/data/YYYYMMDD.json` | 页面读取的副本 |
| `docs/data/dates.json` | 日期清单 |
| `docs/index.html` | 唯一页面模板 |
