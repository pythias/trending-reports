# GitHub Trending Report - OpenClaw Agent Instructions

## Overview

Generate daily GitHub Trending reports. One report per day at 08:00 (Beijing time), comparing with previous day's data.

## Schedule (北京时间)

每天 08:00 执行一次完整流程。

## 每日流程

```bash
python3 fetch_trending.py
python3 generate_report.py
```

**OpenClaw 在执行时会**:
1. 抓取当天 GitHub Trending TOP 10
2. 与昨天数据进行对比（新晋/留榜/落榜）
3. 生成带日期导航的 HTML 报告
4. 保存到 `docs/index.html`

## 数据存储

| 文件位置 | 说明 |
|---------|------|
| `data/history/YYYYMMDD.json` | 每日历史数据 |
| `docs/index.html` | 最新报告（含日期导航） |

## 报告功能

- **日期导航**: 首页可切换日期查看历史报告
- **新晋**: 首次上榜的项目
- **留榜**: 连续在榜的项目
- **落榜**: 上期在榜但本期下榜的项目

## OpenClaw 调度配置

### 任务: 每日 08:00

```bash
cd /path/to/trending-reports && python3 fetch_trending.py && python3 generate_report.py
```

## 本地测试

```bash
# 抓取数据并生成报告
python3 fetch_trending.py
python3 generate_report.py

# 预览
open docs/index.html
```

## 项目结构

```
trending-reports/
├── docs/
│   └── index.html         # 报告首页（含日期导航）
├── data/
│   └── history/          # 每日历史数据 (YYYYMMDD.json)
├── fetch_trending.py      # 数据抓取
├── generate_report.py     # 报告生成
├── templates/
│   └── report.html       # HTML 模板
└── README.md
```
