---
id: task_csv_temp_anomalies
name: 全球温度异常检测
category: CSV 数据分析
scene: 数据库检索、表格整理与数据分析
sub_scene: CSV 统计分析
difficulty: L2
capabilities:
- 数据提取与处理
- 代码生成与理解
- 多步推理
- 输出格式适配
- 自然语言生成
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

请对该数据集进行温度异常分析，并将分析结果写入一个名为 `anomaly_report.md` 的文件。请聚焦 GISTEMP 来源的数据。你的报告应包含：

- **极端月度异常**：找出 GISTEMP 记录中最热和最冷的单月，附上数值
- **统计离群值**：计算每个日历月份（例如所有 1 月、所有 2 月）在所有年份上的均值和标准差。识别异常值超过月度均值 2 个标准差以上的月份（z-score > 2）。至少列出最极端的 10 个离群值及其 z-score
- **最冷年份**：按年均异常识别最冷的 5 个年份
- **最暖年份**：按年均异常识别最暖的 5 个年份
- **最大的逐年变化**：找出年均异常逐年波动最大的 5 次（正向或负向）
- 一段简短的**总结**，解读这些异常反映出怎样的温度模式

---

## Expected Behavior

Agent 应当：

1. 读取并解析 CSV 文件
2. 筛选 GISTEMP 记录（1880–2023）
3. 识别最热月份：2023 年 9 月，+1.48°C
4. 识别最冷月份：1893 年 1 月，-0.82°C
5. 计算每个日历月份的统计量并找出 z-score 离群值
6. 计算年均值并对年份排名
7. 计算年均值的逐年变化
8. 撰写一份结构化的 markdown 报告

关键预期数值：

- 最热月份（GISTEMP）：2023-09，+1.48°C
- 最冷月份（GISTEMP）：1893-01，-0.82°C
- 最暖的 5 个年份：2023（约 1.17）、2016（约 1.01）、2020（约 1.01）、2019（约 0.98）、2017（约 0.92）
- 最冷的 5 个年份：1909（约 -0.49）、1904（约 -0.48）、1917（约 -0.46）、1911（约 -0.45）、1910（约 -0.44）
- 最极端的统计离群值：2023-09，z-score 约 3.76
- 许多离群值聚集在 2015–2023 年，反映出加速变暖
- 最大的逐年跃升包括 1976→1977（+0.28）和 2022→2023（+0.28）

---

## Grading Criteria

- [ ] 已创建报告文件 `anomaly_report.md`
- [ ] 正确识别最热月份为 2023-09，数值约 1.48°C
- [ ] 正确识别最冷月份为 1893-01，数值约 -0.82°C
- [ ] 最暖年份包含 2023、2016 和 2020
- [ ] 最冷年份包含 1909 和 1904
- [ ] 包含带 z-score 的统计离群值分析
- [ ] 将 2023 年 9 月识别为最大离群值（z-score 约 3.7–3.8）
- [ ] 计算了逐年变化并识别出最大波动
- [ ] 提供了总结或解读

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the temperature anomaly detection task.

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
    report_path = workspace / "anomaly_report.md"
    if not report_path.exists():
        alternatives = ["anomalies.md", "report.md", "temperature_anomalies.md", "analysis.md"]
        for alt in alternatives:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "hottest_month": 0.0,
            "coldest_month": 0.0,
            "warmest_years": 0.0,
            "coldest_years": 0.0,
            "outlier_analysis": 0.0,
            "top_outlier_zscore": 0.0,
            "yoy_changes": 0.0,
            "summary": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Hottest month: 2023-09 at 1.48
    hottest_patterns = [
        r'2023[\-/]09.*1\.48',
        r'1\.48.*2023[\-/]09',
        r'september\s*2023.*1\.48',
        r'1\.48.*september\s*2023',
        r'sep(?:tember)?\s*2023.*1\.48',
    ]
    scores["hottest_month"] = 1.0 if any(re.search(p, content_lower) or re.search(p, content) for p in hottest_patterns) else 0.0

    # Coldest month: 1893-01 at -0.82
    coldest_patterns = [
        r'1893[\-/]01.*-0\.82',
        r'-0\.82.*1893[\-/]01',
        r'january\s*1893.*-0\.82',
        r'-0\.82.*january\s*1893',
        r'jan(?:uary)?\s*1893.*-0\.82',
    ]
    scores["coldest_month"] = 1.0 if any(re.search(p, content_lower) or re.search(p, content) for p in coldest_patterns) else 0.0

    # Warmest years include 2023, 2016, 2020
    warm_count = 0
    for year in ["2023", "2016", "2020"]:
        if re.search(rf'(?:warm|hot).*{year}|{year}.*(?:warm|hot)', content_lower) or \
           (year in content and re.search(r'warm|hot|highest', content_lower)):
            warm_count += 1
    # Also check if these years appear with high values
    for year in ["2023", "2016", "2020"]:
        if re.search(rf'{year}.*[01]\.\d{{2,4}}', content):
            warm_count += 1
    scores["warmest_years"] = 1.0 if warm_count >= 4 else (0.5 if warm_count >= 2 else 0.0)

    # Coldest years include 1909, 1904
    cold_count = 0
    for year in ["1909", "1904"]:
        if re.search(rf'(?:cold|cool).*{year}|{year}.*(?:cold|cool)', content_lower) or \
           (year in content and re.search(r'cold|cool|lowest', content_lower)):
            cold_count += 1
        if re.search(rf'{year}.*-0\.[34]\d', content):
            cold_count += 1
    scores["coldest_years"] = 1.0 if cold_count >= 3 else (0.5 if cold_count >= 1 else 0.0)

    # Outlier / z-score analysis
    outlier_patterns = [
        r'z[\-\s]?score',
        r'standard\s*deviation',
        r'outlier',
        r'sigma',
        r'statistical',
    ]
    outlier_count = sum(1 for p in outlier_patterns if re.search(p, content_lower))
    scores["outlier_analysis"] = 1.0 if outlier_count >= 2 else (0.5 if outlier_count >= 1 else 0.0)

    # Top outlier z-score ~3.7-3.8 for 2023-09
    zscore_patterns = [
        r'3\.7[0-9]',
        r'3\.8[0-9]',
        r'2023[\-/]09.*3\.[78]',
        r'september\s*2023.*3\.[78]',
    ]
    scores["top_outlier_zscore"] = 1.0 if any(re.search(p, content_lower) or re.search(p, content) for p in zscore_patterns) else 0.0

    # Year-over-year changes
    yoy_patterns = [
        r'year[\-\s]?over[\-\s]?year',
        r'year[\-\s]?to[\-\s]?year',
        r'yoy',
        r'annual.*change',
        r'(?:1976|1977).*(?:1976|1977)',
        r'(?:2022|2023).*(?:swing|jump|change|increase)',
    ]
    yoy_count = sum(1 for p in yoy_patterns if re.search(p, content_lower))
    scores["yoy_changes"] = 1.0 if yoy_count >= 2 else (0.5 if yoy_count >= 1 else 0.0)

    # Summary / interpretation
    summary_patterns = [
        r'summar',
        r'interpret',
        r'conclusion',
        r'(?:accelerat|rapid).*warm',
        r'warm.*(?:accelerat|rapid)',
        r'climate',
        r'trend',
    ]
    summary_count = sum(1 for p in summary_patterns if re.search(p, content_lower))
    scores["summary"] = 1.0 if summary_count >= 2 else (0.5 if summary_count >= 1 else 0.0)

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Data Analysis Accuracy (Weight: 35%)

**Score 1.0**：极端月份、最暖/最冷年份、z-score 和逐年变化均数值正确，并附具体数值清晰呈现。
**Score 0.75**：大多数值正确，仅有一两处轻微偏差。
**Score 0.5**：部分数值正确，但若干关键数字错误或缺失。
**Score 0.25**：少量数值正确；存在重大计算错误。
**Score 0.0**：没有正确的计算，或未尝试分析。

### Criterion 2: Statistical Rigor (Weight: 30%)

**Score 1.0**：正确计算每月统计量和 z-score，使用正确阈值识别离群值，并以适当背景呈现结果（例如解释 z-score > 2 的含义）。
**Score 0.75**：z-score 分析存在且基本正确，仅有轻微问题。
**Score 0.5**：有一些统计分析，但 z-score 缺失或计算不正确。
**Score 0.25**：统计分析极少，大多为定性观察。
**Score 0.0**：无统计分析。

### Criterion 3: Report Structure and Interpretation (Weight: 20%)

**Score 1.0**：markdown 组织良好，各分析部分章节清晰，并附一段将异常与更广泛温度模式联系起来的深入总结。
**Score 0.75**：报告组织清晰，仅有轻微结构问题；有总结但较简短。
**Score 0.5**：包含分析内容，但组织混乱或缺少总结。
**Score 0.25**：杂乱无章或缺少主要章节。
**Score 0.0**：无报告或为空。

### Criterion 4: Completeness (Weight: 15%)

**Score 1.0**：包含所有要求的要素：极端月份、带 z-score 的离群值分析、最暖/最冷年份、逐年变化和总结。
**Score 0.75**：包含大多数要素，仅有一处轻微遗漏。
**Score 0.5**：缺少若干要素。
**Score 0.25**：仅包含少数要素。
**Score 0.0**：报告缺失或几乎为空。

---

## Additional Notes

本任务测试 Agent 以下能力：

- 解析多来源 CSV 并恰当筛选
- 计算分组统计量（月度均值和标准差）
- 计算 z-score 以识别统计离群值
- 对数据排名和排序以找出极值
- 计算聚合数据的逐年差异
- 以清晰的报告呈现统计发现

该数据集包含两个来源（GISTEMP 和 gcag），覆盖范围有重叠但不完全一致。Agent 应按指示聚焦 GISTEMP。`Mean` 列表示相对于基准时段的温度异常，而非绝对温度。

已知正确数值（GISTEMP）：

- 最热月份：2023 年 9 月（+1.48°C）
- 最冷月份：1893 年 1 月（-0.82°C）
- 最暖年份：2023（约 1.17°C 平均异常）
- 最冷年份：1909（约 -0.49°C 平均异常）
- 最极端 z-score：2023 年 9 月（约 3.76）
- 最大逐年跃升：1976→1977（约 +0.28°C）和 2022→2023（约 +0.28°C）
