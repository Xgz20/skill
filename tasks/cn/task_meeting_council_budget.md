---
id: task_meeting_council_budget
name: 坦帕市议会 — 提取预算讨论
category: 会议分析
scene: 数据库检索、表格整理与数据分析
sub_scene: 会议记录信息提取
difficulty: L2
capabilities:
- 数据提取与处理
- 自然语言生成
- 指令遵循与约束理解
- 输出格式适配
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

我在 `transcript.md` 中有一份 2026 年 4 月 2 日召开的坦帕市议会会议记录。请生成 `budget_report.md`，提取所有与预算相关的讨论，包含金额、背景、议会行动和关切事项。请在结尾包含一份 **财务摘要**。

---

## Expected Behavior

关键财务事项：供水/污水处理容量费（30 亿美元投资、1.7 亿美元拨款、当前每单元 1,020/1,237 美元、拟议 1,530/1,847 美元、每年增加 150-200 万美元收入）、Rome Yard（第 4 阶段 9400 万美元、开发商投资 300 万美元）、Howard Avenue 附属楼（总计 3420 万美元、已花费 700 万美元、第 2 阶段 2720 万美元）、24 号消防站（GMP 5 月 15 日）、65 万美元燃气和解、Zion 公墓 800 万美元请求、管道项目每月 8+8 美元。

---

## Grading Criteria

- [ ] 创建了报告文件 `budget_report.md`
- [ ] 识别了容量费金额
- [ ] 提及 30 亿美元投资
- [ ] 指出每年增加 150-200 万美元收入
- [ ] 识别了 Rome Yard 9400 万美元
- [ ] 识别了附属楼 3420 万美元
- [ ] 指出第 1 阶段 700 万美元
- [ ] 提及 65 万美元和解
- [ ] 捕捉了 Zion 800 万美元
- [ ] 包含财务摘要

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    from pathlib import Path
    import re
    scores = {}
    workspace = Path(workspace_path)
    report_path = workspace / "budget_report.md"
    if not report_path.exists():
        for alt in ["budget.md", "financial_report.md", "finances.md"]:
            if (workspace / alt).exists():
                report_path = workspace / alt
                break
    if not report_path.exists():
        return {k: 0.0 for k in ["report_created", "capacity_fee_amounts", "three_billion", "annual_revenue_increase", "rome_yard_94m", "annex_34m", "phase1_7m", "gas_settlement_650k", "zion_8m", "financial_summary"]}
    scores["report_created"] = 1.0
    content = report_path.read_text()
    cl = content.lower()
    scores["capacity_fee_amounts"] = 1.0 if (re.search(r'1[,.]?0[12]0', content) and re.search(r'1[,.]?[58][34]\d', content)) else 0.0
    scores["three_billion"] = 1.0 if re.search(r'(?:\$?3\s*billion|3B)', cl) else 0.0
    scores["annual_revenue_increase"] = 1.0 if (re.search(r'(?:1\.5|two)\s*(?:million|m\b)', cl) and re.search(r'(?:revenue|additional|year)', cl)) else 0.0
    scores["rome_yard_94m"] = 1.0 if re.search(r'(?:\$?94\s*million|94M)', cl) else 0.0
    scores["annex_34m"] = 1.0 if re.search(r'(?:\$?34\.?2?\s*million)', cl) else 0.0
    scores["phase1_7m"] = 1.0 if (re.search(r'(?:\$?7\s*million)', cl) and re.search(r'(?:spent|phase|already)', cl)) else 0.0
    scores["gas_settlement_650k"] = 1.0 if re.search(r'(?:650[,.]?000|\$650)', cl) else 0.0
    scores["zion_8m"] = 1.0 if (re.search(r'zion', cl) and re.search(r'(?:\$?8\s*million)', cl)) else 0.0
    scores["financial_summary"] = 1.0 if re.search(r'(?:financial|fiscal|budget)\s*(?:summary|overview|total)', cl) else 0.0
    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Financial Data Extraction (Weight: 40%)
**Score 1.0**：所有主要金额均正确提取。**Score 0.5**：有所遗漏。**Score 0.0**：无。

### Criterion 2: Context (Weight: 25%)
**Score 1.0**：每个事项背景清晰。**Score 0.5**：部分。**Score 0.0**：无。

### Criterion 3: Comprehensiveness (Weight: 20%)
**Score 1.0**：涵盖会议所有部分。**Score 0.5**：仅主要部分。**Score 0.0**：不完整。

### Criterion 4: Summary (Weight: 15%)
**Score 1.0**：摘要清晰。**Score 0.5**：不完整。**Score 0.0**：无。
