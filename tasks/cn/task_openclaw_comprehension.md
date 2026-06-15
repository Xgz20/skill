---
id: task_openclaw_comprehension
name: OpenClaw 报告理解
category: 综合分析
scene: 数据库检索、表格整理与数据分析
sub_scene: PDF 信息提取
difficulty: L2
capabilities:
- 数据提取与处理
- 多模态感知
- 指令遵循与约束理解
- 输出格式适配
grading_type: automated
timeout_seconds: 300
workspace_files:
  - source: "OpenClaw Agent Use Cases and Gap Analysis for PinchBench.pdf"
    dest: "openclaw_report.pdf"
---

## Prompt

我的工作区里有一份关于 OpenClaw agent 使用场景的研究报告，文件名为 `openclaw_report.pdf`。我需要你从中提取若干信息并写入 `answer.txt`。请回答下列问题，每行一个答案：

1. 在过滤之前，公共注册表里有多少个社区构建的 skill？
2. 在过滤掉垃圾内容、重复项、非英文、加密货币/金融/交易以及恶意内容之后，还剩下多少个 skill？
3. 按数量计，最大的 skill 类别是什么，它有多少个 skill？（格式："Category Name: count"）
4. 按数量计，第二大的 skill 类别是什么，它有多少个 skill？（格式："Category Name: count"）
5. 定义一个 OpenClaw skill 的文件名是什么？
6. OpenClaw 网关暴露的是哪种类型的 API？
7. skill 注册表数据是在哪个日期采集的？
8. 这篇论文提出了多少个新的基准任务？（只要数字）

## Expected Behavior

Agent 应当：

1. 读取并解析 PDF 文件 `openclaw_report.pdf`
2. 找到 skill 生态系统统计部分，识别出总计 5,705 个、过滤后 2,999 个 skill
3. 定位 skill 类别表格，识别出 "AI & LLMs"（287）为最大类别、"Search & Research"（253）为第二大
4. 找到 skill 由 `SKILL.md` 文件定义
5. 识别出网关使用 "typed WebSocket API"
6. 找到数据采集日期为 February 7, 2026
7. 数出 6 个被提出的基准任务
8. 将所有答案写入 `answer.txt`，每行一个

## Grading Criteria

- [ ] Agent 读取了该 PDF 文件
- [ ] 创建了输出文件 `answer.txt`
- [ ] skill 总数（5705）正确
- [ ] 过滤后 skill 数（2999）正确
- [ ] 最大类别（AI & LLMs: 287）正确
- [ ] 第二大类别（Search & Research: 253）正确
- [ ] 识别出 skill 文件名（SKILL.md）
- [ ] 识别出 API 类型（typed WebSocket）
- [ ] 数据采集日期（February 7, 2026）正确
- [ ] 被提出的任务数（6）正确

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    from pathlib import Path
    import re

    scores = {}
    workspace = Path(workspace_path)
    answer_file = workspace / "answer.txt"

    if not answer_file.exists():
        return {
            "file_created": 0.0,
            "total_skills_correct": 0.0,
            "filtered_skills_correct": 0.0,
            "top_category_correct": 0.0,
            "second_category_correct": 0.0,
            "skill_filename_correct": 0.0,
            "api_type_correct": 0.0,
            "date_correct": 0.0,
            "proposed_tasks_correct": 0.0,
        }

    scores["file_created"] = 1.0
    content = answer_file.read_text().strip()
    lines = [l.strip() for l in content.splitlines() if l.strip()]
    full_text = content.lower()

    # Helper to extract numbers from text.
    # Strips leading list markers ("1. ", "2) ", etc.) so that agents which
    # number their answers ("1. 5705") don't have the line prefix returned
    # instead of the actual value.
    def extract_number(text):
        cleaned = re.sub(r'^\s*\d+[.)]\s+', '', text)
        numbers = re.findall(r'[\d,]+', cleaned)
        for n in numbers:
            val = int(n.replace(',', ''))
            if val > 0:
                return val
        return None

    # Line 1: Total skills (5705)
    line1 = lines[0] if len(lines) >= 1 else ""
    total = extract_number(line1)
    scores["total_skills_correct"] = 1.0 if total == 5705 else 0.0

    # Line 2: Filtered skills (2999)
    line2 = lines[1] if len(lines) >= 2 else ""
    filtered = extract_number(line2)
    scores["filtered_skills_correct"] = 1.0 if filtered == 2999 else 0.0

    # Line 3: Top category (AI & LLMs: 287)
    line3 = lines[2].lower() if len(lines) >= 3 else ""
    has_ai_llm = "ai" in line3 and "llm" in line3
    has_287 = extract_number(line3) == 287
    scores["top_category_correct"] = 1.0 if (has_ai_llm and has_287) else (0.5 if has_ai_llm or has_287 else 0.0)

    # Line 4: Second category (Search & Research: 253)
    line4 = lines[3].lower() if len(lines) >= 4 else ""
    has_search_research = "search" in line4 and "research" in line4
    has_253 = extract_number(line4) == 253
    scores["second_category_correct"] = 1.0 if (has_search_research and has_253) else (0.5 if has_search_research or has_253 else 0.0)

    # Line 5: Skill filename (SKILL.md)
    line5 = lines[4] if len(lines) >= 5 else ""
    scores["skill_filename_correct"] = 1.0 if "skill.md" in line5.lower() else 0.0

    # Line 6: API type (typed WebSocket)
    line6 = lines[5].lower() if len(lines) >= 6 else ""
    has_websocket = "websocket" in line6 or "web socket" in line6
    has_typed = "typed" in line6
    scores["api_type_correct"] = 1.0 if (has_websocket and has_typed) else (0.5 if has_websocket else 0.0)

    # Line 7: Date (February 7, 2026)
    line7 = lines[6].lower() if len(lines) >= 7 else ""
    date_patterns = [
        r"february\s+7[,\s]+2026",
        r"feb\.?\s+7[,\s]+2026",
        r"2026[-/]02[-/]07",
        r"02[-/]07[-/]2026",
        r"7\s+february[,\s]+2026",
        r"7\s+feb\.?[,\s]+2026",
    ]
    scores["date_correct"] = 1.0 if any(re.search(pattern, line7) for pattern in date_patterns) else 0.0

    # Line 8: Proposed tasks count (6)
    line8 = lines[7] if len(lines) >= 8 else ""
    task_count = extract_number(line8)
    scores["proposed_tasks_correct"] = 1.0 if task_count == 6 else 0.0

    return scores
```
