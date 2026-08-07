import json
import os

file_path = '/Users/chenjie5/Desktop/claw/code/trending-reports/data/history/20260807.json'

summaries = {
    "TencentDB-Agent-Memory": "一个团队级的 AI 智能体记忆枢纽，能够将对话、文档和代码转化为可在各个智能体及框架间共享的记忆资产（包含对话记忆、技能、LLM百科、代码图谱等）。",
    "agent-skills": "面向 AI 代码助手的生产级工程开发技能集。",
    "computer": "为你的 AI 智能体提供一个可以操作的计算机环境。",
    "skills": "适用于真正的工程师的技能工具集合，直接服务于 `.agents` 目录。",
    "authentik": "一款功能强大的身份认证与授权“胶水”平台。",
    "loopx": "针对长期运行 AI 分工团队设计的轻量级循环状态内核，在各大编码助手之间通用，并且支持持久目标记录、额度自适应唤醒以及任务交接等功能。",
    "guava": "Google 著名的 Java 版核心公共类库，提供了极多实用的常用工具。",
    "ChinaTextbook": "收录了小学、初中、高中直至大学的各类全面 PDF 电子教材资源。",
    "AutoGPT": "旨在实现“人人可及的自动 AI”愿景，帮助开发者专注于更核心的事项而无需过多干预底层调用的自主智能体项目。",
    "code-review-graph": "专为 MCP 与 CLI 打造的本地优先代码智能知识图谱平台，为 AI 编程工具构建具有针对性的精准内容投喂与上下文缩减功能。"
}

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

for repo in data.get('repos', []):
    name = repo.get('name')
    if name in summaries:
        repo['summary'] = summaries[name]
    else:
        repo['summary'] = repo.get('description', '')

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("Updated successfully!")