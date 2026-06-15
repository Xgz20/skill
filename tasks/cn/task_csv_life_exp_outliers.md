---
id: task_csv_life_exp_outliers
name: 预期寿命异常值检测
category: CSV 数据分析
scene: 数据库检索、表格整理与数据分析
sub_scene: CSV 数据分析
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 输出格式适配
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

我的工作区里有一个 CSV 文件 `gapminder_life_expectancy.csv`，包含来自 Gapminder 数据集的预期寿命数据。该文件包含以下列：`country`、`year`、`pop`、`continent`、`lifeExp` 和 `gdpPercap`。它覆盖了 5 个大洲的 142 个国家，数据从 1952 年到 2007 年每 5 年记录一次。

请识别预期寿命数据中的异常值和反常现象，并把你的发现写入一个名为 `life_exp_outliers.md` 的文件。你的报告应包含：

- **2007 年的统计异常值检测**：使用 z-score 或 IQR 方法识别预期寿命异常高或异常低的国家。报告所用方法、阈值，以及哪些国家被判定为异常值。
- **大洲内异常值**：识别在 2007 年显著偏离自身所在大洲平均值的国家（例如，非洲某国预期寿命远高于非洲平均值）。
- **时间反常现象**：找出预期寿命在连续时间段（5 年间隔）之间**下降**的国家。由于预期寿命通常随时间增长，这些情况令人意外。列出国家、时间段和下降幅度。
- **最剧烈的单期下降**：识别所有国家中连续时间段之间预期寿命下降幅度最大的 5 次。
- 解释这些异常值和反常现象可能成因的简要**分析**（例如 HIV/AIDS 疫情、战争、种族灭绝）。

---

## Expected Behavior

Agent 应当：

1. 读取并解析该 CSV 文件
2. 对 2007 年数据应用统计方法（z-score 或 IQR）。使用 z-score（>2 个标准差偏离均值），找出 6 个低端异常值：Swaziland (z=-2.27)、Mozambique (z=-2.06)、Zambia (z=-2.04)、Sierra Leone (z=-2.02)、Lesotho (z=-2.02)、Angola (z=-2.01)。没有高端异常值。使用 IQR（1.5×IQR），由于分布较宽（IQR=19.556），找不到异常值。
3. 找出 2007 年的大洲内异常值——偏离所属大洲均值 >1.5 个标准差的国家：
   - Africa：Reunion (76.442, z=2.25)、Libya (73.952)、Tunisia (73.923)、Algeria (72.301)、Mauritius (72.801)、Morocco (71.164)、Egypt (71.338) 偏高；Swaziland (39.613, z=-1.58) 偏低
   - Americas：Haiti (60.916, z=-2.86) 显著偏低；Canada (80.653) 和 Bolivia (65.554) 为异常值
   - Asia：Afghanistan (43.828, z=-3.38) 为极端异常值
   - Europe：Turkey (71.777)、Romania (72.476)、Bulgaria (73.005) 为低端异常值
4. 识别时间下降——预期寿命在连续 5 年时间段之间下降的国家
5. 标记最剧烈的下降：Rwanda 1987-1992 (-20.421)、Zimbabwe 1992-1997 (-13.568)、Lesotho 1997-2002 (-10.965)、Swaziland 1997-2002 (-10.420)、Botswana 1992-1997 (-10.189)
6. 将异常值与现实世界事件联系起来（南部非洲的 HIV/AIDS、卢旺达种族灭绝、柬埔寨种族灭绝、战争）

关键预期数值：

- 2007 年 z-score 异常值 (z < -2)：Swaziland、Mozambique、Zambia、Sierra Leone、Lesotho、Angola
- 最严重的大洲内异常值：亚洲的 Afghanistan (z=-3.38)
- 最大单期下降：Rwanda 1987-1992 (-20.421 年，从 44.02 降至 23.599)
- 第二大：Zimbabwe 1992-1997 (-13.568)

---

## Grading Criteria

- [ ] 创建了报告文件 `life_exp_outliers.md`
- [ ] 描述了统计异常值方法（z-score、IQR 或类似方法）
- [ ] 识别出 2007 年的低端异常值（Swaziland、Mozambique 等）
- [ ] 分析了大洲内异常值
- [ ] 识别 Afghanistan 为亚洲内的异常值
- [ ] 识别出预期寿命的时间下降
- [ ] 识别 Rwanda 1987-1992 年的下降为极端情况（~20 年降幅）
- [ ] 列出最剧烈的下降及其幅度
- [ ] 提供现实世界的解释（HIV/AIDS、冲突等）

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the life expectancy outlier detection task.

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
    report_path = workspace / "life_exp_outliers.md"
    if not report_path.exists():
        alternatives = ["outliers.md", "report.md", "life_expectancy_outliers.md",
                        "outlier_report.md", "anomalies.md", "life_exp_anomalies.md"]
        for alt in alternatives:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "statistical_method": 0.0,
            "low_outliers_2007": 0.0,
            "continent_outliers": 0.0,
            "afghanistan_outlier": 0.0,
            "temporal_decreases": 0.0,
            "rwanda_drop": 0.0,
            "dramatic_drops": 0.0,
            "explanations": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Statistical method described
    method_patterns = [
        r'z[- ]?score',
        r'iqr',
        r'interquartile',
        r'standard\s*deviation',
        r'(?:1\.5|2).*(?:std|sigma|sd)',
    ]
    scores["statistical_method"] = 1.0 if any(re.search(p, content_lower) for p in method_patterns) else 0.0

    # Low-end outliers in 2007
    low_outlier_countries = ["swaziland", "mozambique", "zambia", "sierra leone", "lesotho", "angola"]
    found = sum(1 for c in low_outlier_countries if c in content_lower)
    scores["low_outliers_2007"] = 1.0 if found >= 4 else (0.5 if found >= 2 else 0.0)

    # Within-continent outliers discussed
    continent_outlier_patterns = [
        r'(?:within|continent).*outlier',
        r'outlier.*(?:within|continent)',
        r'deviat.*(?:continent|region)',
        r'(?:continent|region).*(?:average|mean).*(?:far|deviat|outlier|anomal)',
    ]
    continent_examples = ["haiti", "afghanistan", "reunion", "turkey", "romania"]
    example_found = sum(1 for c in continent_examples if c in content_lower)
    scores["continent_outliers"] = 1.0 if (
        any(re.search(p, content_lower) for p in continent_outlier_patterns) or example_found >= 3
    ) else (0.5 if example_found >= 2 else 0.0)

    # Afghanistan as outlier within Asia
    afghan_patterns = [
        r'afghanistan.*(?:outlier|anomal|lowest|extreme)',
        r'afghanistan.*asia.*(?:below|low|deviat)',
        r'asia.*afghanistan.*(?:outlier|anomal|lowest)',
        r'afghanistan.*43\.\d',
    ]
    scores["afghanistan_outlier"] = 1.0 if any(re.search(p, content_lower) for p in afghan_patterns) else 0.0

    # Temporal decreases identified
    decrease_countries = ["botswana", "cambodia", "rwanda", "zimbabwe", "swaziland",
                          "lesotho", "south africa", "zambia", "iraq"]
    decrease_found = sum(1 for c in decrease_countries if c in content_lower)
    has_decrease_concept = bool(re.search(r'(?:decreas|declin|drop|fell|reduc).*life\s*exp', content_lower) or
                                re.search(r'life\s*exp.*(?:decreas|declin|drop|fell|reduc)', content_lower))
    scores["temporal_decreases"] = 1.0 if (decrease_found >= 4 and has_decrease_concept) else (
        0.5 if decrease_found >= 2 else 0.0)

    # Rwanda drop specifically
    rwanda_patterns = [
        r'rwanda.*(?:1987|1992).*(?:drop|declin|decreas|fell)',
        r'rwanda.*(?:20|23\.5|44\.0|genoci)',
        r'rwanda.*(?:-20|-?20\.\d)',
        r'genoci.*rwanda',
        r'rwanda.*genoci',
    ]
    scores["rwanda_drop"] = 1.0 if any(re.search(p, content_lower) for p in rwanda_patterns) else 0.0

    # Top dramatic drops listed
    dramatic_countries = ["rwanda", "zimbabwe", "lesotho", "swaziland", "botswana", "cambodia"]
    dramatic_found = sum(1 for c in dramatic_countries if c in content_lower)
    has_magnitude = bool(re.search(r'-?\d{1,2}\.\d+\s*year', content_lower) or
                         re.search(r'(?:drop|declin|fell|decreas).*\d{1,2}\.\d', content_lower))
    scores["dramatic_drops"] = 1.0 if (dramatic_found >= 4 and has_magnitude) else (
        0.5 if dramatic_found >= 2 else 0.0)

    # Real-world explanations
    explanation_patterns = [
        r'hiv|aids',
        r'genoci',
        r'(?:civil\s*)?war',
        r'(?:khmer|rouge|pol\s*pot)',
        r'conflict',
        r'epidemic|pandemic',
        r'famine',
    ]
    explanations_found = sum(1 for p in explanation_patterns if re.search(p, content_lower))
    scores["explanations"] = 1.0 if explanations_found >= 3 else (0.5 if explanations_found >= 1 else 0.0)

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Statistical Rigor (Weight: 30%)

**Score 1.0**：清晰描述所用统计方法，报告阈值和具体数值（z-score 或 IQR 边界），正确识别异常值及其统计量，并承认局限性（例如分布较宽时 IQR 可能无法标记异常值）。
**Score 0.75**：使用了有效的统计方法并正确识别大多数异常值，但缺少阈值或方法学的部分细节。
**Score 0.5**：识别出异常值但统计依据薄弱或不清晰。
**Score 0.25**：提及异常值但没有适当的统计分析。
**Score 0.0**：未尝试统计异常值检测。

### Criterion 2: Anomaly Detection Breadth (Weight: 30%)

**Score 1.0**：覆盖全部三类反常现象：全局统计异常值、大洲内异常值和时间下降。对每一类都提供具体国家、时间段和幅度。
**Score 0.75**：以良好细节覆盖至少两类反常现象。
**Score 0.5**：很好地覆盖一类，或表面地覆盖多类。
**Score 0.25**：仅有基础异常值识别而无深度。
**Score 0.0**：没有有意义的反常现象检测。

### Criterion 3: Contextual Analysis (Weight: 25%)

**Score 1.0**：将异常值与现实世界事件（南部非洲的 HIV/AIDS 疫情、卢旺达种族灭绝、柬埔寨红色高棉、伊拉克/索马里的战争）联系起来，并有具体引用。
**Score 0.75**：为大多数异常值提供合理解释，但缺少一些关键联系。
**Score 0.5**：给出一些解释但缺乏具体性或遗漏主要成因。
**Score 0.25**：含糊或泛泛的解释。
**Score 0.0**：未尝试任何解释。

### Criterion 4: Report Quality (Weight: 15%)

**Score 1.0**：结构良好的报告，章节清晰，数据以表格或格式化列表呈现，从方法学到发现再到分析逻辑递进。
**Score 0.75**：结构良好，仅有轻微问题。
**Score 0.5**：内容齐全但组织混乱。
**Score 0.25**：难以阅读或章节缺失。
**Score 0.0**：没有报告或输出不可用。

---

## Additional Notes

本任务测试 Agent 的以下能力：

- 对真实世界数据应用统计异常值检测方法
- 跨多个维度分析数据（全局、按大洲、随时间）
- 检测时间反常现象（违背总体上升趋势的预期寿命下降）
- 将数据规律与现实世界事件联系起来
- 在清晰的报告中呈现复杂的多层次发现

Gapminder 数据集以展示全球健康差异而闻名。时间反常现象尤其引人注目：卢旺达的预期寿命在 1987-1992 年间（种族灭绝期间）从 44.0 降至 23.6，多个南部非洲国家在 1990 年代至 2000 年代因 HIV/AIDS 经历了剧烈下降。

已知正确数值：

- 2007 年平均预期寿命：67.007，标准差：12.073
- IQR 方法 (1.5×IQR)：Q1=56.867，Q3=76.423，IQR=19.556 → 边界为 27.533 和 105.757（无异常值）
- Z-score 方法 (|z|>2)：6 个低端异常值（Swaziland z=-2.27 至 Angola z=-2.01）
- 最严重的大洲内异常值：亚洲的 Afghanistan (z=-3.38)、美洲的 Haiti (z=-2.86)
- 前 5 大下降：Rwanda 87-92 (-20.4)、Zimbabwe 92-97 (-13.6)、Lesotho 97-02 (-11.0)、Swaziland 97-02 (-10.4)、Botswana 92-97 (-10.2)
