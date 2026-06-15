---
id: task_meeting_council_votes
name: 坦帕市议会 – 列出动议和投票结果
category: 会议分析
scene: 数据库检索、表格整理与数据分析
sub_scene: 会议投票提取
difficulty: L3
capabilities:
- 数据提取与处理
- 指令遵循与约束理解
- 多步推理
- 输出格式适配
- 自然语言生成
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

我有一份 2026 年 4 月 2 日举行的坦帕市议会会议的记录，保存在 `transcript.md` 中。这是一份实时字幕记录，不是逐字记录。

请分析该记录并生成一个名为 `votes_report.md` 的文件，列出会议期间发生的每一项动议和投票。对于每次投票，请包括：

- **项目或主题**（例如，议程项目编号、议题）
- **动议人**（谁提出）
- **附议人**（谁附议）
- **投票结果**（一致通过、唱名表决明细或口头表决结果）
- **任何弃权、回避或反对票**

按时间顺序组织报告。最后包括一个**摘要统计**：总投票次数、有多少次是一致通过的、有多少次存在反对意见。

---

## Expected Behavior

Agent 应识别所有动议和投票，提取动议人和附议人，注意口头和唱名表决，并识别反对票/回避（Carlson 在第 12 项弃权，Carlson 和 Clendenin 在第 14/15 项投反对票，Carlson 在第 25 项投反对票）。

关键投票：会议记录通过（Miranda/Maniscalco）、第 12 项（Carlson 弃权）、第 14/15 项 Rome Yard（5-2）、第 19 项重新分区（一致通过）、第 22 项退伍军人委员会（延续到 4 月 16 日）、第 23 项容量费（第一读）、第 25 项（6-1 Carlson 反对）、第 26-28 项（重新考虑，移至 4 月 16 日）。

议会成员：Alan Clendenin（主席）、Charlie Miranda、Guido Maniscalco、Lynn Hurtak、Naya Young、Luis Viera、Bill Carlson。

---

## Grading Criteria

- [ ] 报告文件 `votes_report.md` 已创建
- [ ] 识别了会议记录通过投票（Miranda 提议，Maniscalco 附议）
- [ ] 第 12 项正确注明 Carlson 弃权
- [ ] 捕获了第 14/15 项唱名表决（5-2，Carlson 和 Clendenin 投反对票）
- [ ] 捕获了第 19 项重新分区投票为一致通过
- [ ] 注明了第 22 项退伍军人委员会延续到 4 月 16 日
- [ ] 捕获了第 23 项水/废水容量费第一读
- [ ] 捕获了第 25 项决议，Carlson 投反对票（6-1）
- [ ] 捕获了第 26-28 项的重新考虑和重新安排
- [ ] 包括了总投票次数的摘要统计

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    from pathlib import Path
    import re
    scores = {}
    workspace = Path(workspace_path)
    report_path = workspace / "votes_report.md"
    if not report_path.exists():
        for alt in ["votes.md", "motions.md", "vote_report.md"]:
            if (workspace / alt).exists():
                report_path = workspace / alt
                break
    if not report_path.exists():
        return {k: 0.0 for k in ["report_created", "minutes_vote", "item12_abstain", "item14_15_rollcall", "item19_unanimous", "item22_continued", "item23_first_reading", "item25_carlson_no", "item26_28_reconsider", "summary_count"]}
    scores["report_created"] = 1.0
    content = report_path.read_text()
    cl = content.lower()
    scores["minutes_vote"] = 1.0 if re.search(r'miranda', cl) and re.search(r'minut', cl) else 0.0
    scores["item12_abstain"] = 1.0 if (re.search(r'(?:item\s*(?:#?\s*)?12|twelve)', cl) and re.search(r'carlson.*(?:abstain|recus)', cl)) else 0.0
    scores["item14_15_rollcall"] = 1.0 if (re.search(r'(?:14|15|rome\s*yard)', cl) and re.search(r'5[\s-]*2', cl)) else 0.0
    scores["item19_unanimous"] = 1.0 if (re.search(r'(?:item\s*(?:#?\s*)?19|rez[\s-]*25[\s-]*126|4102)', cl) and re.search(r'unanimou', cl)) else 0.0
    scores["item22_continued"] = 1.0 if (re.search(r'(?:item\s*(?:#?\s*)?22|veteran)', cl) and re.search(r'(?:continu|defer|april\s*16|first\s*reading)', cl)) else 0.0
    scores["item23_first_reading"] = 1.0 if (re.search(r'(?:item\s*(?:#?\s*)?23|capacity\s*fee|water.*wastewater)', cl) and re.search(r'(?:first\s*read|pass|approv)', cl)) else 0.0
    scores["item25_carlson_no"] = 1.0 if (re.search(r'(?:item\s*(?:#?\s*)?25)', cl) and re.search(r'(?:carlson.*(?:no|nay|dissent)|6[\s-]*1)', cl)) else 0.0
    scores["item26_28_reconsider"] = 1.0 if (re.search(r'(?:26|27|28|howard|annex|forensic)', cl) and re.search(r'(?:reconsider|rescind|second\s*read|april\s*16)', cl)) else 0.0
    scores["summary_count"] = 1.0 if re.search(r'(?:total|summary|count).*(?:\d+\s*vote|\d+\s*motion)', cl) else 0.0
    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Vote Identification Completeness (Weight: 40%)
**Score 1.0**: 识别 20+ 个不同的投票。**Score 0.75**: 15-19 个。**Score 0.5**: 10-14 个。**Score 0.0**: 无。

### Criterion 2: Vote Detail Accuracy (Weight: 30%)
**Score 1.0**: 正确的动议人、附议人、结果。捕获反对/弃权。**Score 0.5**: 部分错误。**Score 0.0**: 大部分错误。

### Criterion 3: Organization (Weight: 15%)
**Score 1.0**: 按时间顺序，清晰。**Score 0.5**: 组织混乱。**Score 0.0**: 不可读。

### Criterion 4: Summary (Weight: 15%)
**Score 1.0**: 准确的统计总数。**Score 0.5**: 存在但不准确。**Score 0.0**: 无。
