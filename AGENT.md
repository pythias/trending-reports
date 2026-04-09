# GitHub Trending Report - Agent 使用说明

## 项目简介

这是一个面向「GitHub Trending 日报」的自动化项目：

- 每日抓取 GitHub Trending TOP 10
- 自动生成中文总结（可选，依赖 API key）
- 对比昨日榜单变化（新晋 / 留榜 / 落榜）
- 产出可直接查看的静态 HTML 报告（支持日期切换）

## 一句话总结

> 用最小维护成本，持续追踪开源趋势并生成可分享的中文日报页面。

## 推荐使用场景

1. **技术团队晨会速览**：每天快速浏览新晋热门仓库，辅助技术选型与学习。
2. **内容创作者选题**：发现近期热度上升项目，作为文章、视频或直播素材来源。
3. **开源情报跟踪**：观察某段时间内的语言、框架和工具趋势变化。
4. **社区运营周报**：将每日数据沉淀为可回看页面，用于周/月度复盘。
5. **个人学习雷达**：自动筛选高关注项目，避免错过潜在高价值仓库。

## Schedule (北京时间)

每天 **08:50** 自动执行。

---

## 每日流程

```bash
python3 fetch_trending.py
python3 summarize_repos.py    # AI 生成项目简介（如已配置 API key）
python3 generate_report.py
```

**完整流程：**
1. 抓取当天 GitHub Trending TOP 10
2. **（需 API key）** AI 为每个项目生成一句话中文简介
3. 与昨天数据进行对比（新晋 / 留榜 / 落榜）
4. 生成带日期导航的 HTML 报告，写入 `docs/index.html`

> ⚠️ **Python 版本**：必须使用 **Python 3.11**（项目使用类型联合语法 `Path | None`），路径：
> `/opt/homebrew/opt/python@3.11/bin/python3.11`
>
> 本地测试时需安装依赖：
> ```bash
> /opt/homebrew/opt/python@3.11/bin/python3.11 -m pip install requests beautifulsoup4 lxml
> ```

---

## 数据存储

| 文件位置 | 说明 |
|---------|------|
| `data/YYYY-MM-DD.json` | 当日抓取原始数据 |
| `data/history/YYYYMMDD.json` | 历史归档（每日生成） |
| `docs/index.html` | 最新报告（含日期导航） |

> 注意：两个文件由脚本自动维护，不要手动合并或删除任一路径。

---

## OpenClaw Cron 配置

### 任务: 每日 08:50 (北京时间)

- **schedule**: `0 50 8 * * *`（UTC 00:50）
- **sessionTarget**: `isolated`
- **payload.kind**: `agentTurn`

### 环境变量（可选）

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `MINIMAX_API_KEY` | MiniMax API Key（优先） | — |
| `MINIMAX_MODEL` | MiniMax 模型 | `MiniMax-Text-01` |
| `MINIMAX_BASE_URL` | MiniMax API 地址 | `https://api.minimax.chat/v1` |
| `OPENAI_API_KEY` | OpenAI API Key（备用） | — |
| `OPENAI_MODEL` | OpenAI 模型 | `gpt-4o-mini` |
| `OPENAI_BASE_URL` | OpenAI API 地址 | `https://api.openai.com/v1` |

---

## 报告功能

- **新晋**：首次上榜的项目
- **留榜**：连续在榜的项目
- **落榜**：上期在榜但本期下榜的项目
- **日期导航**：首页可切换查看历史报告

---

## 项目结构

```
trending-reports/
├── docs/
│   └── index.html              # 报告首页（含日期导航）
├── data/
│   ├── YYYY-MM-DD.json        # 当日原始数据
│   └── history/
│       └── YYYYMMDD.json      # 历史归档
├── fetch_trending.py           # 数据抓取
├── summarize_repos.py          # AI 摘要生成
├── generate_report.py          # 报告生成
├── templates/
│   └── report.html             # HTML 模板
└── README.md
```

---

## 本地测试

```bash
cd /Users/chenjie5/Desktop/claw/code/trending-reports

# 抓取 + 生成（如无 API key，summarize_repos.py 会跳过摘要）
/opt/homebrew/opt/python@3.11/bin/python3.11 fetch_trending.py
# 手动补充摘要（如未配置 API key）
/opt/homebrew/opt/python@3.11/bin/python3.11 generate_report.py

# 预览报告
open docs/index.html
```
