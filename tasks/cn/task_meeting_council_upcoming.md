---
id: task_meeting_council_upcoming
name: 坦帕市议会 – 提取即将到来的事件和截止日期
category: 会议分析
scene: 数据库检索、表格整理与数据分析
sub_scene: 会议记录事件提取
difficulty: L2
capabilities:
- 数据提取与处理
- 自然语言生成
- 输出格式适配
- 指令遵循与约束理解
grading_type: hybrid
timeout_seconds: 180
grading_weights:
  automated: 0.5
  llm_judge: 0.5
workspace_files:
  - source: meetings/2026-04-02-tampa-city-council-transcript.md
    dest: transcript.md
---

## Prompt

我有一份 2026 年 4 月 2 日举行的坦帕市议会会议的记录，保存在 `transcript.md` 中。请生成 `upcoming_events.md`，按时间顺序列出所有即将到来的事件、截止日期和未来日期。包括日期、事件、负责方和状态（已确认/提议/暂定）。最后附上一个**"值得关注"**的重点章节。

---

## Expected Behavior

关键项目：4 月 16 日（退伍军人委员会、第 26-28 项、65 万美元重新分配）、4 月 20 日（Fair Oaks 东坦帕市政厅）、5 月 7 日（道德报告、LDC 更新）、5 月 15 日（24 号消防站 GMP）、8 月 3/10/17 日（预算研讨会）、2027 年 3 月 1 日（容量费开始）、2027 年 9 月（24 号消防站完工）、2028 年 9 月（Rome Yard 第 4 阶段）、2030 年 3 月（费用全面实施）、下周（HART 董事会）、约 60 天（Rome Yard 结案）。

---

## Grading Criteria

- [ ] 报告文件 `upcoming_events.md` 已创建
- [ ] 识别了 4 月 16 日项目
- [ ] 4 月 20 日东坦帕市政厅
- [ ] 5 月 7 日道德报告
- [ ] 24 号消防站 GMP（5 月 15 日）
- [ ] 预算研讨会（8 月）
- [ ] 2027 年 3 月容量费
- [ ] 2028 年 9 月 Rome Yard
- [ ] 按时间顺序组织
- [ ] 重点章节

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    from pathlib import Path
    import re
    scores = {}
    workspace = Path(workspace_path)
    report_path = workspace / "upcoming_events.md"
    if not report_path.exists():
        for alt in ["events.md", "deadlines.md", "upcoming.md", "timeline.md"]:
            if (workspace / alt).exists():
                report_path = workspace / alt
                break
    if not report_path.exists():
        return {k: 0.0 for k in ["report_created", "april_16_items", "april_20_townhall", "may_7_ethics", "fire_station_gmp", "budget_workshops", "march_2027_fees", "rome_yard_sept2028", "chronological", "highlights_section"]}
    scores["report_created"] = 1.0
    content = report_path.read_text()
    cl = content.lower()
    scores["april_16_items"] = 1.0 if (re.search(r'april\s*16', cl) and re.search(r'(?:veteran|26|27|28|annex)', cl)) else 0.0
    scores["april_20_townhall"] = 1.0 if (re.search(r'april\s*20', cl) and re.search(r'(?:east\s*tampa|town\s*hall|fair\s*oaks)', cl)) else 0.0
    scores["may_7_ethics"] = 1.0 if (re.search(r'may\s*7', cl) and re.search(r'(?:ethic|conflict|ldc)', cl)) else 0.0
    scores["fire_station_gmp"] = 1.0 if (re.search(r'(?:may\s*15|gmp)', cl) and re.search(r'(?:fire\s*station|station\s*24)', cl)) else 0.0
    scores["budget_workshops"] = 1.0 if (re.search(r'august\s*(?:3|10|17)', cl) and re.search(r'(?:budget|workshop)', cl)) else 0.0
    scores["march_2027_fees"] = 1.0 if (re.search(r'march.*2027', cl) and re.search(r'(?:capacity|fee|water)', cl)) else 0.0
    scores["rome_yard_sept2028"] = 1.0 if (re.search(r'(?:september|sept).*28', cl) and re.search(r'(?:rome|phase\s*4|completion)', cl)) else 0.0
    scores["chronological"] = 1.0 if len(re.findall(r'(april|may|june|august|september|march)\s*\d{0,4}', cl)) >= 4 else 0.0
    scores["highlights_section"] = 1.0 if re.search(r'(?:watch|highlight|key|significant|important)', cl) else 0.0
    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Completeness (Weight: 35%)
**Score 1.0**: 12+ 个事件。**Score 0.75**: 9-11 个。**Score 0.5**: 5-8 个。**Score 0.0**: 无。

### Criterion 2: Accuracy (Weight: 25%)
**Score 1.0**: 所有日期正确。**Score 0.5**: 多个错误。**Score 0.0**: 错误。

### Criterion 3: Context (Weight: 25%)
**Score 1.0**: 每个事件都有清晰的上下文。**Score 0.5**: 基本。**Score 0.0**: 无。

### Criterion 4: Prioritization (Weight: 15%)
**Score 1.0**: 有效的重点标注。**Score 0.5**: 弱。**Score 0.0**: 无。
