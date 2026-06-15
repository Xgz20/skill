---
id: task_csv_life_exp_ranking
name: 预期寿命国家排名
category: CSV 数据分析
scene: 数据库检索、表格整理与数据分析
sub_scene: CSV 排名分析
difficulty: L2
capabilities:
- 工具调用
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

我的工作区里有一个 CSV 文件 `gapminder_life_expectancy.csv`，包含来自 Gapminder 数据集的预期寿命数据。该文件包含以下列：`country`、`year`、`pop`、`continent`、`lifeExp` 和 `gdpPercap`。它覆盖了 5 个大洲（Africa、Americas、Asia、Europe、Oceania）的 142 个国家，数据从 1952 年到 2007 年每 5 年记录一次。

请分析各国按预期寿命的排名，并把你的发现写入一个名为 `life_exp_ranking.md` 的文件。你的报告应包含：

- 2007 年预期寿命**最高的 10 个国家**，以及它们所属的大洲和确切的预期寿命数值
- 2007 年预期寿命**最低的 10 个国家**，以及它们所属的大洲和确切的预期寿命数值
- 2007 年**各大洲的平均预期寿命**
- **排名随时间的变化**：对比 1952 年与 2007 年排名前 5 和后 5 的国家
- 对排名中关键规律的简要**总结**（例如哪些大洲主导了榜首/榜尾，是否有任何意外发现）

---

## Expected Behavior

Agent 应当：

1. 读取并解析该 CSV 文件（1704 行，142 个国家，12 个时间点）
2. 筛选出 2007 年的数据并按预期寿命排序
3. 找出最高的 10 个国家：Japan (82.603)、Hong Kong China (82.208)、Iceland (81.757)、Switzerland (81.701)、Australia (81.235)、Spain (80.941)、Sweden (80.884)、Israel (80.745)、France (80.657)、Canada (80.653)
4. 找出最低的 10 个国家：Swaziland (39.613)、Mozambique (42.082)、Zambia (42.384)、Sierra Leone (42.568)、Lesotho (42.592)、Angola (42.731)、Zimbabwe (43.487)、Afghanistan (43.828)、Central African Republic (44.741)、Liberia (45.678)
5. 计算各大洲平均值：Africa (~54.806)、Americas (~73.608)、Asia (~70.728)、Europe (~77.649)、Oceania (~80.719)
6. 对比 1952 年与 2007 年的排名，展示其如何变化
7. 注意到 2007 年最低的 10 个国家中除 Afghanistan 外全部为非洲国家

关键预期数值：

- 2007 年 #1：Japan (82.603)
- 2007 年 #142（最后一名）：Swaziland (39.613)
- 最高的大洲平均值：Oceania (~80.72)
- 最低的大洲平均值：Africa (~54.81)
- 2007 年的极差：82.603 - 39.613 = 42.99 年

---

## Grading Criteria

- [ ] 创建了报告文件 `life_exp_ranking.md`
- [ ] 正确列出 2007 年最高的 10 个国家及其预期寿命数值
- [ ] 正确识别 Japan 为 #1 (82.603)
- [ ] 正确列出 2007 年最低的 10 个国家
- [ ] 正确识别 Swaziland 为最低 (39.613)
- [ ] 计算并报告各大洲平均值
- [ ] 识别出 Africa 拥有最低的大洲平均值
- [ ] 包含历史对比（1952 年 vs 2007 年）
- [ ] 提供规律总结

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the life expectancy ranking task.

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
    report_path = workspace / "life_exp_ranking.md"
    if not report_path.exists():
        alternatives = ["ranking.md", "report.md", "life_expectancy_ranking.md",
                        "rankings.md", "life_exp_report.md"]
        for alt in alternatives:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "top_countries": 0.0,
            "japan_first": 0.0,
            "bottom_countries": 0.0,
            "swaziland_last": 0.0,
            "continent_averages": 0.0,
            "africa_lowest": 0.0,
            "historical_comparison": 0.0,
            "pattern_summary": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Check top countries (at least 5 of top 10 mentioned)
    top_countries = ["japan", "hong kong", "iceland", "switzerland", "australia",
                     "spain", "sweden", "israel", "france", "canada"]
    top_found = sum(1 for c in top_countries if c in content_lower)
    scores["top_countries"] = 1.0 if top_found >= 7 else (0.5 if top_found >= 4 else 0.0)

    # Japan as #1
    japan_patterns = [
        r'japan.*82\.6',
        r'1\.\s*japan',
        r'japan.*(?:highest|first|top|#1|number one|rank.*1)',
        r'(?:highest|first|top|#1).*japan',
    ]
    scores["japan_first"] = 1.0 if any(re.search(p, content_lower) for p in japan_patterns) else 0.0

    # Bottom countries (at least 5 of bottom 10)
    bottom_countries = ["swaziland", "mozambique", "zambia", "sierra leone", "lesotho",
                        "angola", "zimbabwe", "afghanistan", "central african republic", "liberia"]
    bottom_found = sum(1 for c in bottom_countries if c in content_lower)
    scores["bottom_countries"] = 1.0 if bottom_found >= 7 else (0.5 if bottom_found >= 4 else 0.0)

    # Swaziland as lowest
    swaziland_patterns = [
        r'swaziland.*39\.6',
        r'swaziland.*(?:lowest|last|bottom|worst)',
        r'(?:lowest|last|bottom).*swaziland',
    ]
    scores["swaziland_last"] = 1.0 if any(re.search(p, content_lower) for p in swaziland_patterns) else 0.0

    # Continent averages
    continents_mentioned = 0
    for cont in ["africa", "americas", "asia", "europe", "oceania"]:
        if cont in content_lower:
            continents_mentioned += 1
    has_averages = bool(re.search(r'(?:average|mean|avg).*(?:continent|region)', content_lower) or
                        re.search(r'(?:continent|region).*(?:average|mean|avg)', content_lower) or
                        (continents_mentioned >= 4 and re.search(r'\d{2}\.\d', content)))
    scores["continent_averages"] = 1.0 if (has_averages and continents_mentioned >= 4) else (
        0.5 if continents_mentioned >= 3 else 0.0)

    # Africa as lowest continent
    africa_low_patterns = [
        r'africa.*(?:lowest|worst|behind|last|lag|trail)',
        r'(?:lowest|worst|last).*(?:continent|region).*africa',
        r'africa.*54\.\d',
        r'africa.*55\.\d',
    ]
    scores["africa_lowest"] = 1.0 if any(re.search(p, content_lower) for p in africa_low_patterns) else 0.0

    # Historical comparison (1952 mentioned with ranking context)
    historical_patterns = [
        r'1952.*(?:rank|top|bottom|highest|lowest)',
        r'(?:rank|top|bottom|highest|lowest).*1952',
        r'(?:changed|shifted|evolved|compared).*(?:1952|over time|historically)',
        r'1952.*2007',
    ]
    scores["historical_comparison"] = 1.0 if any(re.search(p, content_lower) for p in historical_patterns) else 0.0

    # Pattern summary
    pattern_indicators = 0
    if re.search(r'africa.*(?:dominat|most|all|majority).*bottom', content_lower):
        pattern_indicators += 1
    if re.search(r'(?:europe|oceania).*(?:dominat|most|top)', content_lower):
        pattern_indicators += 1
    if re.search(r'(?:gap|disparity|inequality|range|difference)', content_lower):
        pattern_indicators += 1
    if re.search(r'(?:pattern|trend|observation|notable|key\s*finding)', content_lower):
        pattern_indicators += 1
    scores["pattern_summary"] = 1.0 if pattern_indicators >= 2 else (0.5 if pattern_indicators >= 1 else 0.0)

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Ranking Accuracy (Weight: 35%)

**Score 1.0**：最高的 10 个国家和最低的 10 个国家被正确识别，预期寿命数值准确。所有数值与数据集一致。
**Score 0.75**：大多数排名正确，仅有一两个国家位置错误或存在轻微数值误差。
**Score 0.5**：总体方向正确（榜首/榜尾的国家正确），但若干具体排名或数值有误。
**Score 0.25**：识别出部分正确的国家，但排名大多错误或不完整。
**Score 0.0**：未尝试排名或完全错误。

### Criterion 2: Analytical Depth (Weight: 30%)

**Score 1.0**：包含各大洲平均值、历史对比和有洞见的规律分析。指出诸如非洲主导榜尾排名、最高与最低之间存在 43 年差距，以及排名从 1952 年到 2007 年如何变化等关键观察。
**Score 0.75**：包含大部分分析要素并有良好观察，但缺少其中一个组成部分。
**Score 0.5**：有基础分析但缺乏深度——缺少各大洲平均值、历史对比或规律分析中的某一项。
**Score 0.25**：除列出国家外几乎没有分析。
**Score 0.0**：除原始数字外没有任何分析。

### Criterion 3: Report Structure and Presentation (Weight: 20%)

**Score 1.0**：结构良好的 markdown，章节清晰，排名以格式化的表格或列表呈现，从概览到细节逻辑流畅。
**Score 0.75**：组织良好，仅有轻微格式问题。
**Score 0.5**：内容齐全但组织混乱。
**Score 0.25**：杂乱或难以阅读。
**Score 0.0**：没有报告或输出不可用。

### Criterion 4: Completeness (Weight: 15%)

**Score 1.0**：所有要求的要素都齐全：前 10、后 10、各大洲平均值、历史对比和总结。
**Score 0.75**：大部分要素齐全，仅有一处小遗漏。
**Score 0.5**：缺少若干要求的要素。
**Score 0.25**：仅部分完成。
**Score 0.0**：报告缺失或几乎为空。

---

## Additional Notes

本任务测试 Agent 的以下能力：

- 解析含 1704 行的多列 CSV
- 按特定列筛选、排序并排名数据
- 按类别（大洲）分组并聚合数据
- 跨时间段对比数据
- 识别并阐述排名数据中的规律

该数据集是经典的 Gapminder 数据，覆盖了 142 个国家从 1952 年至 2007 年的人口、大洲、预期寿命和人均 GDP。本任务只需关注预期寿命列。

已知正确数值：

- 142 个国家，12 个时间点（1952-2007，每 5 年一次），共 1704 行
- 2007 年 #1：Japan (82.603)，#2：Hong Kong China (82.208)
- 2007 年最后一名：Swaziland (39.613)，倒数第二：Mozambique (42.082)
- 2007 年各大洲平均值：Africa 54.806、Americas 73.608、Asia 70.728、Europe 77.649、Oceania 80.719
