# GitHub Trending Report

每日 GitHub Trending 报告，自动追踪开源项目趋势。

## 报告功能

- **新晋**: 首次上榜的项目
- **留榜**: 连续在榜的项目
- **落榜**: 本期下榜的项目
- **日期导航**: 可切换查看历史报告

## OpenClaw 调度配置

### 每日任务 (08:00 北京时间)

**命令**:
```bash
cd /path/to/trending-reports && python3 fetch_trending.py && python3 generate_report.py
```

## 本地运行

```bash
python3 fetch_trending.py
python3 generate_report.py
open docs/index.html
```

## 项目结构

```
trending-reports/
├── docs/index.html        # 报告首页
├── data/history/          # 每日历史数据
├── fetch_trending.py      # 抓取数据
├── generate_report.py      # 生成报告
└── templates/report.html  # HTML 模板
```
