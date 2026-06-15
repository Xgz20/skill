---
id: task_csv_life_exp_change
name: 预期寿命随时间的变化
category: CSV 数据分析
scene: 数据库检索、表格整理与数据分析
sub_scene: CSV 数据分析
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 输出格式适配
- 工具调用
- 自然语言生成
grading_type: hybrid
timeout_seconds: 180
grading_weights:
  automated: 0.6
  llm_judge: 0.4
workspace_files:
  - source: csvs/gapminder_life_expectancy.csv
    dest: gapminder_life_expectancy.csv
---

## Prompt

我的工作区中有一个 CSV 文件 `gapminder_life_expectancy.csv`，包含来自 Gapminder 数据集的预期寿命数据。文件有以下列：`country`、`year`、`pop`、`continent`、`lifeExp` 和 `gdpPercap`。它涵盖 5 个大洲的 142 个国家，从 1952 年到 2007 年每 5 年提供一次数据。

请分析预期寿命随时间如何变化，并将你的发现写入一个名为 `life_exp_change.md` 的文件。你的报告应包含：

- **全球趋势**：计算每一年（1952 年至 2007 年）的全球平均预期寿命，并描述总体走势
- **大洲层级趋势**：计算每个大洲每一年的平均预期寿命，并比较不同大洲的进展
- **进步最大者**：识别从 1952 年到 2007 年预期寿命绝对增幅最大的 10 个国家，附起始值、结束值和总变化
- **进步最慢者 / 下降者**：识别从 1952 年到 2007 年预期寿命改善最小（或下降）的 10 个国家
- **趋同还是分化**：分析最高与最低大洲平均值之间的差距是随时间收窄还是扩大
- 一个简短的关键要点**总结**

---

## Expected Behavior

The agent should:

1. 读取并解析 CSV 文件
2. 计算每年的全球平均值：1952 (49.058)、1957 (51.507)、1962 (53.609)、1967 (55.678)、1972 (57.647)、1977 (59.570)、1982 (61.533)、1987 (63.213)、1992 (64.160)、1997 (65.015)、2002 (65.695)、2007 (67.007)
3. 计算大洲平均值，显示 Europe/Oceania 居于顶端、Africa 居于底部，而 Asia 取得最大涨幅
4. 识别进步最大的前 10 个国家：Oman (+38.062)、Vietnam (+33.837)、Indonesia (+33.182)、Saudi Arabia (+32.902)、Libya (+31.229)、Korea Rep. (+31.170)、Nicaragua (+30.585)、West Bank and Gaza (+30.262)、Yemen Rep. (+30.150)、Gambia (+29.448)
5. 识别后 10 名：Norway (+7.526)、Congo Dem. Rep. (+7.319)、Liberia (+7.198)、Rwanda (+6.242)、South Africa (+4.330)、Botswana (+3.106)、Lesotho (+0.454)、Zambia (+0.346)、Swaziland (-1.794)、Zimbabwe (-4.964)
6. 分析趋同/分化：指出最高（Oceania/Europe）与最低（Africa）大洲平均值之间的差距持续存在，并可能因 HIV/AIDS 在 1990 至 2000 年代略有扩大

预期关键值：

- 全球平均 1952：~49.06，2007：~67.01
- 全球总增幅：~17.95 岁
- 进步最大者：Oman (+38.062，从 37.578 到 75.640)
- 下降最大者：Zimbabwe (-4.964，从 48.451 到 43.487)
- 只有 2 个国家在 1952-2007 年间净变化为负：Swaziland (-1.794)、Zimbabwe (-4.964)

---

## Grading Criteria

- [ ] 创建了报告文件 `life_exp_change.md`
- [ ] 计算了每年（或大多数年份）的全球平均预期寿命
- [ ] 正确描述了全球上升趋势（55 年间从 ~49 到 ~67）
- [ ] 计算并比较了大洲层级趋势
- [ ] 识别出进步最大者，且 Oman 为 #1（+38 岁）
- [ ] 识别出进步最慢者 / 下降者
- [ ] 将 Zimbabwe 和 Swaziland 识别为仅有的净下降国家
- [ ] 包含趋同/分化分析
- [ ] 提供了带有关键要点的总结

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the life expectancy change over time task.

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
    report_path = workspace / "life_exp_change.md"
    if not report_path.exists():
        alternatives = ["change.md", "report.md", "life_expectancy_change.md",
                        "life_exp_trends.md", "trends.md", "life_exp_over_time.md"]
        for alt in alternatives:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "global_averages": 0.0,
            "global_trend": 0.0,
            "continent_trends": 0.0,
            "top_improvers": 0.0,
            "oman_first": 0.0,
            "decliners": 0.0,
            "convergence_analysis": 0.0,
            "summary": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Global averages computed (check for year-average pairs)
    year_avg_patterns = [
        r'1952.*49\.\d',
        r'1977.*59\.\d',
        r'2007.*67\.\d',
    ]
    avg_found = sum(1 for p in year_avg_patterns if re.search(p, content))
    scores["global_averages"] = 1.0 if avg_found >= 2 else (0.5 if avg_found >= 1 else 0.0)

    # Global upward trend described
    trend_patterns = [
        r'(?:increas|ris|improv|grew|gain).*(?:49|50).*(?:67|68)',
        r'(?:49|50).*(?:to|→|->).*(?:67|68)',
        r'(?:upward|positive|steady|consistent).*(?:trend|trajectory|increase)',
        r'(?:17|18).*year.*(?:gain|increase|improv)',
    ]
    scores["global_trend"] = 1.0 if any(re.search(p, content_lower) for p in trend_patterns) else 0.0

    # Continent-level trends
    continents_with_data = 0
    for cont in ["africa", "americas", "asia", "europe", "oceania"]:
        if cont in content_lower:
            continents_with_data += 1
    has_temporal = bool(re.search(r'(?:1952|1977|1982).*(?:africa|europe|asia)', content_lower) or
                        re.search(r'(?:africa|europe|asia).*(?:1952|1977|1982)', content_lower))
    scores["continent_trends"] = 1.0 if (continents_with_data >= 4 and has_temporal) else (
        0.5 if continents_with_data >= 3 else 0.0)

    # Top improvers (at least 5 of top 10)
    top_improvers = ["oman", "vietnam", "indonesia", "saudi arabia", "libya",
                     "korea", "nicaragua", "west bank", "yemen", "gambia"]
    improver_found = sum(1 for c in top_improvers if c in content_lower)
    scores["top_improvers"] = 1.0 if improver_found >= 6 else (0.5 if improver_found >= 3 else 0.0)

    # Oman as biggest improver
    oman_patterns = [
        r'oman.*(?:38|37\.\d|largest|biggest|most|#1|first|top)',
        r'(?:largest|biggest|most|#1|first|top).*oman',
        r'oman.*37\.578.*75\.640',
        r'oman.*\+?38',
    ]
    scores["oman_first"] = 1.0 if any(re.search(p, content_lower) for p in oman_patterns) else 0.0

    # Decliners identified
    decliner_patterns = [
        r'zimbabwe.*(?:declin|decreas|negative|drop|fell|lost|\-)',
        r'swaziland.*(?:declin|decreas|negative|drop|fell|lost|\-)',
        r'(?:only|two|2).*(?:countr|nation).*(?:declin|decreas|negative)',
    ]
    decliner_found = sum(1 for p in decliner_patterns if re.search(p, content_lower))
    scores["decliners"] = 1.0 if decliner_found >= 2 else (0.5 if decliner_found >= 1 else 0.0)

    # Convergence/divergence analysis
    convergence_patterns = [
        r'(?:converg|diverg)',
        r'(?:gap|dispar|inequal).*(?:narrow|widen|persist|grew|shrank)',
        r'(?:narrow|widen).*(?:gap|dispar|inequal)',
        r'africa.*(?:lag|behind|gap|slow)',
        r'(?:hiv|aids).*(?:widen|revers|set\s*back)',
    ]
    scores["convergence_analysis"] = 1.0 if any(re.search(p, content_lower) for p in convergence_patterns) else 0.0

    # Summary / takeaways
    summary_patterns = [
        r'(?:summary|conclusion|takeaway|key\s*finding|in\s*summary)',
        r'(?:overall|in\s*conclusion|to\s*summarize)',
    ]
    has_summary = any(re.search(p, content_lower) for p in summary_patterns)
    has_insight = bool(re.search(r'(?:despite|although|however|notably|remarkably)', content_lower))
    scores["summary"] = 1.0 if (has_summary and has_insight) else (0.5 if has_summary or has_insight else 0.0)

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Data Analysis Accuracy (Weight: 35%)

**Score 1.0**：所有计算值正确——全球平均值与数据吻合，进步最大/最小者正确识别且幅度准确，大洲趋势准确。
**Score 0.75**：大多数值正确，仅有一两处小的数值错误。
**Score 0.5**：总体趋势正确，但若干具体值错误或缺失。
**Score 0.25**：重大计算错误或大多数值不正确。
**Score 0.0**：无正确计算。

### Criterion 2: Trend Analysis Depth (Weight: 30%)

**Score 1.0**：在全球、大洲和国家层级进行了全面分析。指出 1990 年后全球涨幅放缓、Africa 因 HIV/AIDS 进展停滞、Asia 戏剧性追赶，以及少数倒退的国家。讨论了大洲之间的趋同/分化。
**Score 0.75**：良好的多层级分析，但缺少某个维度或对原因缺乏细节。
**Score 0.5**：在一两个层级上的基本趋势描述，缺乏深度。
**Score 0.25**：分析肤浅，洞察很少。
**Score 0.0**：无趋势分析。

### Criterion 3: Comparative Insight (Weight: 20%)

**Score 1.0**：有效地对比进步最大者与下降者，解释为什么中东/亚洲国家改善最多（从低基数起步、快速发展）而南部非洲国家下降（HIV/AIDS）。指出 Norway 的小幅增长（+7.5）是因为它起点已经很高（1952 年为 72.7）。
**Score 0.75**：良好的比较，但缺少一些细微之处。
**Score 0.5**：尝试了一些比较，但缺乏深度。
**Score 0.25**：比较分析极少。
**Score 0.0**：未在分组间进行比较。

### Criterion 4: Completeness and Presentation (Weight: 15%)

**Score 1.0**：所有所需元素齐全（全球趋势、大洲趋势、进步最大者、下降者、趋同分析、总结），组织良好，带有表格或格式化数据。
**Score 0.75**：大多数元素齐全且组织良好。
**Score 0.5**：缺少若干元素或组织较差。
**Score 0.25**：不完整或组织混乱。
**Score 0.0**：报告缺失或无法使用。

---

## Additional Notes

This task tests the agent's ability to:

- 跨多个分组维度（年份、大洲）计算聚合统计
- 识别随时间变化的极值而非绝对值
- 分析多分组时间序列中的趋同/分化模式
- 区分改善、停滞和下降的国家
- 将多个分析层级的发现综合为连贯的叙述

Gapminder 数据集特别适合此分析，因为它既捕捉了全球健康革命（平均预期寿命上升 ~18 岁），也捕捉了其失败（HIV/AIDS 重创南部非洲，战争导致急剧下降）。

已知正确值：

- 全球平均：49.058 (1952) → 67.007 (2007)，增幅约 ~17.95 岁
- 最大增幅：Oman +38.062 (37.578 → 75.640)
- 仅有的净下降者：Zimbabwe -4.964 (48.451 → 43.487)、Swaziland -1.794 (41.407 → 39.613)
- Africa 大洲平均：39.136 (1952) → 54.806 (2007)，增幅约 ~15.67
- Europe 大洲平均：64.409 (1952) → 77.649 (2007)，增幅约 ~13.24
- Asia 大洲平均：46.314 (1952) → 70.728 (2007)，增幅约 ~24.41（大洲中最大增幅）
