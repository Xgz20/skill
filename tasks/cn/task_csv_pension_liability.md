---
id: task_csv_pension_liability
name: 美国养老金负债分析
category: CSV 数据分析
scene: 金融投研与企业价值评估
sub_scene: 养老金负债分析
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 领域推理
- 输出格式适配
- 工具调用
grading_type: hybrid
timeout_seconds: 180
grading_weights:
  automated: 0.6
  llm_judge: 0.4
workspace_files:
  - source: csvs/us_pension_by_state.csv
    dest: us_pension_by_state.csv
---

## Prompt

我的工作区里有一个 CSV 文件 `us_pension_by_state.csv`，包含按州和国会选区细分的美国联邦养老金支付数据。各列如下：

- `STATE_ABBREV_NAME` — 州缩写和名称（例如，州级汇总行用 "OH-OHIO Total"）
- `DISTRICT` — 国会选区编号、"At Large" 或年份
- `PAYEE_AMOUNT` — 支付给当前退休人员的总金额（带 $ 符号和逗号格式）
- `PAYEE_COUNT` — 当前领取者人数
- `DEFERRED_COUNT` — 尚未领取福利的递延（未来）领取者人数

以 "Total" 结尾的行是州级汇总。第一行是总计（Grand Total）。

请分析养老金负债敞口，并把你的发现写入 `pension_liability_report.md`。你的报告应包含：

- 各州的**人均支付额**——按此指标对前 10 个州排名
- **各州的总递延人数**——对递延（未来）领取者最多的前 10 个州排名
- **预计未来负债**：对每个州，用该州的人均支付额乘以其递延人数来估算未来年度负债。按此预计负债对前 10 个州排名。
- **全国汇总**：当前年度总支付额、当前总领取人数、总递延领取人数、整体人均支付额，以及假设所有递延领取者按当前平均水平领取时的预计未来负债总额
- 对哪些州代表了最大的未来财务敞口以及原因的简要**分析**

---

## Expected Behavior

Agent 应当：

1. 解析该 CSV，去除美元格式和逗号
2. 计算每个州的人均支付额（PAYEE_AMOUNT / PAYEE_COUNT）
3. 按人均支付额对各州排名——Colorado (~$9,711)、Hawaii (~$9,643)、Washington (~$9,224) 居前
4. 按递延人数对各州排名——New York (40,592)、California (35,564)、Pennsylvania (34,285) 居前
5. 计算各州的预计负债（人均支付额 x 递延人数）
6. 报告全国总计：~$5.71B 当前支付额，877,305 名领取者，483,720 名递延者，~$6,510 平均值
7. 计算预计未来负债总额：~$6,510 x 483,720 = ~$3.15B

关键预期数值：

- 整体人均支付额：~$6,510/人
- 最高人均支付额：Colorado (~$9,711/人)、Hawaii (~$9,643/人)、Washington (~$9,224/人)
- 最高递延人数：New York (40,592)、California (35,564)、Pennsylvania (34,285)
- 按预计负债排名靠前：New York、California、Ohio、Pennsylvania（大递延人数 x 中高人均支付额）
- 全国预计未来负债：~$3.15B

---

## Grading Criteria

- [ ] 创建了报告文件 `pension_liability_report.md`
- [ ] 计算了人均支付额并列出前 10 个州
- [ ] 识别 Colorado 为最高人均支付额（~$9,711）
- [ ] 列出按递延人数排名的前 10 个州
- [ ] 识别 New York 为最高递延人数（40,592）
- [ ] 计算了每个州的预计未来负债
- [ ] 全国汇总包含总金额、领取人数、递延人数和整体平均值
- [ ] 估算了预计未来负债总额（~$3.15B）
- [ ] 提供财务敞口分析

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the pension liability analysis task.

    Args:
        transcript: Parsed JSONL transcript as list of dicts
        workspace_path: Path to the task's isolated workspace directory

    Returns:
        Dict mapping criterion names to scores (0.0 to 1.0)
    """
    from pathlib import Path
    import re

    scores = {}
    workspace = Path(workspace_path)

    # Check if report exists
    report_path = workspace / "pension_liability_report.md"
    if not report_path.exists():
        alternatives = ["liability_report.md", "report.md", "pension_report.md", "pension_liability.md"]
        for alt in alternatives:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "avg_payout_ranking": 0.0,
            "colorado_highest_avg": 0.0,
            "deferred_ranking": 0.0,
            "ny_highest_deferred": 0.0,
            "projected_liability": 0.0,
            "national_summary": 0.0,
            "total_projected": 0.0,
            "exposure_analysis": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Average payout ranking — check if top states mentioned with avg context
    avg_states = ["colorado", "hawaii", "washington", "nevada", "wyoming", "montana"]
    avg_mentioned = sum(1 for s in avg_states if s in content_lower)
    has_avg_context = bool(re.search(r'(?:average|avg|per\s*payee|per\s*recipient)', content_lower))
    scores["avg_payout_ranking"] = 1.0 if avg_mentioned >= 4 and has_avg_context else (0.5 if avg_mentioned >= 2 else 0.0)

    # Colorado as highest avg payout
    co_patterns = [
        r'colorado.*(?:9[,.]?711|highest|first|#1|top|rank.*1)',
        r'(?:highest|first|#1|top).*(?:average|avg|per\s*payee).*colorado',
        r'colorado.*\$?9[,.]?7\d\d',
    ]
    scores["colorado_highest_avg"] = 1.0 if any(re.search(p, content_lower) for p in co_patterns) else 0.0

    # Deferred count ranking
    deferred_states = ["new york", "california", "pennsylvania", "ohio", "illinois", "michigan", "new jersey"]
    def_mentioned = sum(1 for s in deferred_states if s in content_lower)
    has_deferred_context = bool(re.search(r'deferred', content_lower))
    scores["deferred_ranking"] = 1.0 if def_mentioned >= 5 and has_deferred_context else (0.5 if def_mentioned >= 3 else 0.0)

    # NY highest deferred
    ny_patterns = [
        r'new\s*york.*(?:40[,.]?592|highest|most|first|#1|top|largest).*deferred',
        r'(?:highest|most|first|#1|top|largest).*deferred.*new\s*york',
        r'new\s*york.*40[,.]?592',
    ]
    scores["ny_highest_deferred"] = 1.0 if any(re.search(p, content_lower) for p in ny_patterns) else 0.0

    # Projected liability calculated
    proj_patterns = [
        r'(?:projected|estimated|future).*(?:liability|cost|exposure|payout)',
        r'(?:avg|average).*(?:multiply|times|x|\*).*deferred',
        r'deferred.*(?:multiply|times|x|\*).*(?:avg|average)',
    ]
    scores["projected_liability"] = 1.0 if any(re.search(p, content_lower) for p in proj_patterns) else 0.0

    # National summary
    national_patterns = [
        r'5[,.]7\d*\s*billion',
        r'877[,.]?\d*',
        r'483[,.]?\d*',
        r'6[,.]?510',
    ]
    nat_count = sum(1 for p in national_patterns if re.search(p, content_lower))
    scores["national_summary"] = 1.0 if nat_count >= 3 else (0.5 if nat_count >= 2 else 0.0)

    # Total projected future liability (~$3.15B)
    total_proj_patterns = [
        r'3[,.]1\d*\s*billion',
        r'\$?3[,.]?1[45]\d',
        r'(?:projected|future).*(?:total|national).*(?:3[,.]1|billion)',
        r'(?:3[,.]1|billion).*(?:projected|future)',
    ]
    scores["total_projected"] = 1.0 if any(re.search(p, content_lower) for p in total_proj_patterns) else 0.0

    # Exposure analysis
    analysis_patterns = [
        r'(?:exposure|risk|liability|burden)',
        r'(?:large|significant|substantial).*(?:deferred|future|obligation)',
        r'(?:federal|government).*(?:employ|workforce)',
    ]
    analysis_count = sum(1 for p in analysis_patterns if re.search(p, content_lower))
    scores["exposure_analysis"] = 1.0 if analysis_count >= 2 else (0.5 if analysis_count >= 1 else 0.0)

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Calculation Accuracy (Weight: 35%)

**Score 1.0**：所有计算正确——人均支付额、递延人数、预计负债和全国总计均与预期数值一致。货币格式处理正确。
**Score 0.75**：大多数计算正确，仅有轻微舍入或一处计算错误。
**Score 0.5**：核心方法正确但若干数值有误，或预计负债的计算方法存在缺陷。
**Score 0.25**：重大计算错误或对数据的误解。
**Score 0.0**：未能完成计算或结果完全错误。

### Criterion 2: Multi-Dimensional Analysis (Weight: 30%)

**Score 1.0**：提供了全部三个排名维度（人均支付额、递延人数、预计负债），并在它们之间作清晰区分。展现出对高负债来自高人均支付额与高递延人数组合的理解。
**Score 0.75**：三个维度都齐全，但其中一个不完整，或未探讨各维度之间的相互作用。
**Score 0.5**：仅分析了三个维度中的两个，或排名齐全但无解释。
**Score 0.25**：仅分析了一个维度。
**Score 0.0**：没有多维度分析。

### Criterion 3: Financial Insight (Weight: 20%)

**Score 1.0**：对养老金负债集中度的驱动因素提供了有意义的洞见——联邦就业模式、生活成本差异、军事/政府存在。指出按金额排名靠前的州与按人均支付额排名靠前的州有所不同。
**Score 0.75**：对规律有良好观察并有一些背景推理。
**Score 0.5**：有基础观察但缺乏更深入的财务推理。
**Score 0.25**：除列出数字外洞见很少。
**Score 0.0**：没有分析或洞见。

### Criterion 4: Report Quality (Weight: 15%)

**Score 1.0**：结构良好的报告，每个排名都有清晰章节，配有格式化的表格或列表，全国汇总突出显示，逻辑流畅。
**Score 0.75**：结构良好，仅有轻微问题。
**Score 0.5**：内容齐全但组织混乱。
**Score 0.25**：杂乱或章节不完整。
**Score 0.0**：没有报告或文件为空。

---

## Additional Notes

本任务测试 Agent 的以下能力：

- 从原始数据执行衍生计算（平均值、预计估算）
- 同时沿多个维度分析数据
- 区分当前义务与未来负债
- 将发现综合为可操作的财务洞见
- 处理格式化的数值数据（带 $ 和逗号的货币字符串）

预计未来负债的计算是一个估算：它假设递延领取者将按与当前领取者相同的平均水平领取。优秀的回答会指出这一假设及其局限性。
