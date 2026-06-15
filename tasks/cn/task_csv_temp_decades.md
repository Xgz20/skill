---
id: task_csv_temp_decades
name: 全球温度十年对比
category: CSV 数据分析
scene: 数据库检索、表格整理与数据分析
sub_scene: CSV 统计分析
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 输出格式适配
- 工具调用
- 领域推理
grading_type: hybrid
timeout_seconds: 180
grading_weights:
  automated: 0.6
  llm_judge: 0.4
workspace_files:
  - source: csvs/global_temperature.csv
    dest: global_temperature.csv
---

## Prompt

我的工作区里有一个 CSV 文件 `global_temperature.csv`，包含全球温度异常数据。该文件有三列：`Source`（取值为 "GISTEMP" 或 "gcag"）、`Year`（YYYY-MM 格式）和 `Mean`（相对于基准时段的温度异常，单位 °C）。

GISTEMP 数据覆盖 1880–2023 年，gcag 数据覆盖 1850–2024 年。

请使用 GISTEMP 数据跨十年比较温度模式，并将分析结果写入一个名为 `decade_report.md` 的文件。你的报告应包含：

- **十年平均值**：计算从 1880 年代到 2010 年代每个完整十年（外加部分的 2020 年代）的年均温度异常。以表格形式呈现
- **逐个十年的变化**：计算从一个十年到下一个十年平均异常的变化。识别哪一次十年过渡的升温增幅最大
- **十年内变异性**：对每个十年，计算各年均值的标准差。哪个十年的变异性最大、哪个最小？
- **每个十年的最暖与最冷年份**：对每个十年，列出最暖和最冷的单个年份
- **两个来源的对比**：在重叠时段（1880 年代–2010 年代）比较 GISTEMP 和 gcag 的十年平均值。两者吻合程度如何？
- 一段简短的**总结**，说明变暖如何逐个十年推进

---

## Expected Behavior

Agent 应当：

1. 读取并解析 CSV，分离 GISTEMP 和 gcag 记录
2. 为每个来源从月度数据计算年均值
3. 将年均值按十年分组并计算统计量
4. 计算逐个十年的过渡
5. 比较两个数据来源在重叠时段的表现
6. 撰写一份含表格的结构化报告

关键预期数值（GISTEMP）：

- 1880 年代平均：约 -0.21°C
- 1910 年代平均：约 -0.33°C（最冷的完整十年）
- 1940 年代平均：约 0.04°C（首个平均值为正的十年）
- 1980 年代平均：约 0.25°C
- 2010 年代平均：约 0.80°C（最暖的完整十年）
- 2020 年代平均（部分）：约 0.98°C
- 最大的逐个十年升温：1970 年代→1980 年代（+0.21°C）或 2000 年代→2010 年代（+0.22°C）
- GISTEMP 和 gcag 每个十年大致吻合在约 0.1°C 以内，gcag 略低

---

## Grading Criteria

- [ ] 已创建报告文件 `decade_report.md`
- [ ] 包含十年平均值表格，含 1880 年代到 2010 年代的数值
- [ ] 正确识别 1910 年代或 1900 年代为最冷的完整十年
- [ ] 正确识别 2010 年代为最暖的完整十年
- [ ] 计算了逐个十年的变化
- [ ] 识别出最大升温过渡（1970 年代→1980 年代或 2000 年代→2010 年代，约 +0.2°C）
- [ ] 至少为部分十年计算了十年内变异性（标准差）
- [ ] 至少为若干十年识别出每个十年的最暖/最冷年份
- [ ] 包含 GISTEMP 与 gcag 的来源对比

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the decade comparison task.

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
    report_path = workspace / "decade_report.md"
    if not report_path.exists():
        alternatives = ["decades.md", "report.md", "decade_analysis.md", "decade_comparison.md", "analysis.md"]
        for alt in alternatives:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "decade_table": 0.0,
            "coldest_decade": 0.0,
            "warmest_decade": 0.0,
            "decade_changes": 0.0,
            "largest_transition": 0.0,
            "variability": 0.0,
            "per_decade_extremes": 0.0,
            "source_comparison": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Decade averages table (check for multiple decades mentioned with values)
    decade_labels = ["1880", "1890", "1900", "1910", "1920", "1930", "1940",
                     "1950", "1960", "1970", "1980", "1990", "2000", "2010"]
    decades_found = sum(1 for d in decade_labels if d in content)
    # Check for tabular format (pipe characters or consistent formatting)
    has_table = bool(re.search(r'\|.*\|.*\|', content))
    if decades_found >= 12:
        scores["decade_table"] = 1.0
    elif decades_found >= 8:
        scores["decade_table"] = 0.75 if has_table else 0.5
    elif decades_found >= 5:
        scores["decade_table"] = 0.5
    else:
        scores["decade_table"] = 0.0

    # Coldest decade: 1910s (~-0.33) or 1900s (~-0.32)
    cold_decade_patterns = [
        r'191\d.*(?:cold|cool|low)',
        r'(?:cold|cool|low).*191\d',
        r'190\d.*(?:cold|cool|low)',
        r'(?:cold|cool|low).*190\d',
        r'1910s.*-0\.3[23]',
        r'1900s.*-0\.3[12]',
    ]
    scores["coldest_decade"] = 1.0 if any(re.search(p, content_lower) for p in cold_decade_patterns) else 0.0

    # Warmest full decade: 2010s (~0.80)
    warm_decade_patterns = [
        r'2010.*(?:warm|hot|high)',
        r'(?:warm|hot|high).*2010',
        r'2010s.*0\.8[0-9]',
        r'2010s.*(?:warmest|hottest)',
    ]
    scores["warmest_decade"] = 1.0 if any(re.search(p, content_lower) for p in warm_decade_patterns) else 0.0

    # Decade-to-decade changes computed
    transition_patterns = [
        r'decade[\-\s]?to[\-\s]?decade',
        r'(?:transition|change|shift|difference).*decade',
        r'→|->|to\s+(?:the\s+)?(?:next|following)',
        r'\+0\.[012]\d+',
    ]
    transition_count = sum(1 for p in transition_patterns if re.search(p, content_lower) or re.search(p, content))
    scores["decade_changes"] = 1.0 if transition_count >= 2 else (0.5 if transition_count >= 1 else 0.0)

    # Largest warming transition (~+0.2°C in 1970s→1980s or 2000s→2010s)
    largest_patterns = [
        r'(?:197|198).*(?:larg|great|big|most)',
        r'(?:larg|great|big|most).*(?:197|198)',
        r'(?:200|201).*(?:larg|great|big|most)',
        r'(?:larg|great|big|most).*(?:200|201)',
        r'(?:\+\s*)?0\.2[012]\d*.*(?:larg|great|big|most)',
        r'(?:larg|great|big|most).*(?:\+\s*)?0\.2[012]',
    ]
    scores["largest_transition"] = 1.0 if any(re.search(p, content_lower) or re.search(p, content) for p in largest_patterns) else 0.0

    # Intra-decade variability
    variability_patterns = [
        r'(?:variab|std|standard\s*dev)',
        r'(?:most|least|high|low).*(?:variab|spread|range)',
        r'(?:variab|spread|range).*(?:most|least|high|low)',
    ]
    scores["variability"] = 1.0 if any(re.search(p, content_lower) for p in variability_patterns) else 0.0

    # Per-decade extremes (warmest/coldest year per decade)
    # Check for year mentions that look like per-decade extremes
    year_mentions = re.findall(r'(?:19|20)\d{2}', content)
    unique_years = len(set(year_mentions))
    warmest_coldest = bool(re.search(r'(?:warm|cold|hot|cool)est.*(?:year|annual)', content_lower))
    scores["per_decade_extremes"] = 1.0 if unique_years >= 20 and warmest_coldest else (0.5 if unique_years >= 15 else 0.0)

    # Source comparison (GISTEMP vs gcag)
    comparison_patterns = [
        r'gistemp.*gcag|gcag.*gistemp',
        r'(?:both|two)\s+(?:source|dataset)',
        r'(?:compar|agree|differ|consistent).*(?:source|gistemp|gcag)',
        r'(?:source|gistemp|gcag).*(?:compar|agree|differ|consistent)',
    ]
    scores["source_comparison"] = 1.0 if any(re.search(p, content_lower) for p in comparison_patterns) else 0.0

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Quantitative Accuracy (Weight: 35%)

**Score 1.0**：十年平均值、过渡和变异性度量均数值正确并清晰呈现。数值与预期范围吻合。
**Score 0.75**：大多数值正确，仅有一两个十年存在轻微偏差。
**Score 0.5**：部分数值正确，但若干十年的平均值错误。
**Score 0.25**：少量数值正确；存在根本性聚合错误。
**Score 0.0**：没有正确的计算。

### Criterion 2: Comparative Analysis Quality (Weight: 30%)

**Score 1.0**：对各十年进行透彻比较，展现渐进式变暖，清晰识别过渡和加速时段，并对 GISTEMP/gcag 的吻合度做出有意义的来源对比。
**Score 0.75**：比较良好，大多数组成部分齐全。
**Score 0.5**：做了一些比较，但缺乏深度或缺少来源对比。
**Score 0.25**：比较极少；大多只是罗列数字。
**Score 0.0**：无比较分析。

### Criterion 3: Report Structure (Weight: 20%)

**Score 1.0**：组织良好，十年数据用清晰表格呈现，过渡格式化，从数据到解读逻辑流畅。表格在 markdown 中格式规范。
**Score 0.75**：结构良好，仅有轻微格式问题。
**Score 0.5**：包含分析内容，但表格凌乱或结构较差。
**Score 0.25**：杂乱无章或缺少主要章节。
**Score 0.0**：无报告或为空。

### Criterion 4: Completeness (Weight: 15%)

**Score 1.0**：包含所有要求的要素：十年表格、过渡、变异性、每个十年的极值、来源对比和总结。
**Score 0.75**：包含大多数要素，仅有一处轻微遗漏。
**Score 0.5**：缺少若干要素。
**Score 0.25**：仅包含少数要素。
**Score 0.0**：报告缺失或几乎为空。

---

## Additional Notes

本任务测试 Agent 以下能力：

- 将月度数据聚合为年度和十年汇总
- 跨分组（十年）比较统计量
- 计算组内变异性度量
- 交叉参照两个独立数据来源
- 以清晰的表格格式呈现多维度对比

该数据集有两个重叠的来源，方法略有不同。比较两者可测试 Agent 是否能处理多来源数据并就数据吻合度得出有意义的结论。

已知正确数值（GISTEMP 十年平均值）：

- 1880 年代：-0.21，1890 年代：-0.24，1900 年代：-0.32，1910 年代：-0.33
- 1920 年代：-0.24，1930 年代：-0.12，1940 年代：+0.04，1950 年代：-0.05
- 1960 年代：-0.03，1970 年代：+0.03，1980 年代：+0.25，1990 年代：+0.38
- 2000 年代：+0.59，2010 年代：+0.80，2020 年代（部分）：+0.98
- 最大升温过渡：1970 年代→1980 年代（+0.21），2000 年代→2010 年代（+0.22）
- 大多数十年里 gcag 比 GISTEMP 低约 0.07–0.12°C
