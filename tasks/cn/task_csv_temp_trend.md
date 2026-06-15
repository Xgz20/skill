---
id: task_csv_temp_trend
name: 全球温度趋势分析
category: CSV 数据分析
scene: 数据库检索、表格整理与数据分析
sub_scene: CSV 数据分析
difficulty: L2
capabilities:
- 数据提取与处理
- 代码生成与理解
- 多步推理
- 输出格式适配
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

请使用 GISTEMP 数据分析长期温度趋势，并将分析结果写入一个名为 `trend_report.md` 的文件。你的报告应包含：

- **整体趋势**：计算年均异常，并拟合一条线性回归，确定整个 1880–2023 时段的升温速率（°C/十年）
- **加速分析**：将数据分为 1950 年前（1880–1949）和 1950 年后（1950–2023）两个时段。分别计算线性趋势并比较升温速率
- **最冷与最暖时段**：识别记录中最冷的连续 10 年和最暖的连续 10 年
- **里程碑跨越**：识别年均异常首次超过 +0.5°C 的年份，以及首次超过 +1.0°C 的年份
- **近期变暖背景**：最近的十年（2014–2023）与最早的十年（1880–1889）相比如何？
- 一段简短的**总结**，概括整体变暖趋势及其加速情况

---

## Expected Behavior

Agent 应当：

1. 读取并解析 CSV，筛选 GISTEMP
2. 从月度数据计算年均值（仅使用具备全部 12 个月的年份）
3. 拟合线性回归以确定升温速率
4. 比较 1950 年前后的趋势以展现加速
5. 找出最冷和最暖的连续 10 年区间
6. 识别里程碑年份
7. 撰写一份结构化报告

关键预期数值：

- 全时段线性趋势：约 0.08°C/十年（斜率约 0.008°C/年）
- 1950 年前趋势：约 0.04°C/十年
- 1950 年后趋势：约 0.15°C/十年（约为 1950 年前的 4 倍）
- 最暖十年：2010 年代（平均约 0.80°C）或部分的 2020 年代
- 最冷十年：1900 年代（约 -0.32°C）或 1910 年代（约 -0.33°C）
- 年均值首次超过 +0.5°C 的年份：1998（约 0.61°C）
- 年均值首次超过 +1.0°C 的年份：2016（约 1.01°C）
- 近期十年（2014–2023）相比最早十年（1880–1889）：差异约 1.0°C

---

## Grading Criteria

- [ ] 已创建报告文件 `trend_report.md`
- [ ] 报告整体升温速率约为 0.07–0.09°C/十年
- [ ] 计算了 1950 年前升温速率（约 0.03–0.05°C/十年）
- [ ] 计算了 1950 年后升温速率（约 0.14–0.17°C/十年）
- [ ] 指出了加速（1950 年后速率显著快于 1950 年前）
- [ ] 识别出首次超过 +0.5°C 的年份（1998 或相近）
- [ ] 识别出首次超过 +1.0°C 的年份（2015 或 2016）
- [ ] 包含近期十年与最早十年的对比
- [ ] 提供了总结或结论

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the temperature trend analysis task.

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
    report_path = workspace / "trend_report.md"
    if not report_path.exists():
        alternatives = ["trend_analysis.md", "report.md", "temperature_trend.md", "analysis.md"]
        for alt in alternatives:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "overall_rate": 0.0,
            "pre1950_rate": 0.0,
            "post1950_rate": 0.0,
            "acceleration": 0.0,
            "first_05": 0.0,
            "first_10": 0.0,
            "decade_comparison": 0.0,
            "summary": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Overall warming rate ~0.07-0.09°C per decade
    rate_patterns = [
        r'0\.0[78]\d*\s*°?C?\s*/?\s*(?:per\s*)?decade',
        r'0\.0[78]\d*\s*°?C?\s*(?:per|every)\s*(?:10|ten)\s*year',
        r'(?:per\s*decade|decade).*0\.0[78]',
        r'0\.00[78]\d*\s*°?C?\s*/?\s*(?:per\s*)?year',
    ]
    scores["overall_rate"] = 1.0 if any(re.search(p, content_lower) or re.search(p, content) for p in rate_patterns) else 0.0

    # Pre-1950 rate ~0.03-0.05°C/decade
    pre1950_patterns = [
        r'(?:pre|before|prior)[\s\-]*1950.*0\.0[345]\d*',
        r'0\.0[345]\d*.*(?:pre|before|prior)[\s\-]*1950',
        r'1880.*1949.*0\.0[345]',
        r'0\.0[345].*1880.*194[09]',
    ]
    scores["pre1950_rate"] = 1.0 if any(re.search(p, content_lower) or re.search(p, content) for p in pre1950_patterns) else 0.0

    # Post-1950 rate ~0.14-0.17°C/decade
    post1950_patterns = [
        r'(?:post|after|since)[\s\-]*1950.*0\.1[45678]\d*',
        r'0\.1[45678]\d*.*(?:post|after|since)[\s\-]*1950',
        r'1950.*2023.*0\.1[45678]',
        r'0\.1[45678].*1950.*202',
    ]
    scores["post1950_rate"] = 1.0 if any(re.search(p, content_lower) or re.search(p, content) for p in post1950_patterns) else 0.0

    # Acceleration noted
    accel_patterns = [
        r'accelerat',
        r'(?:3|4|three|four)\s*(?:times|×|x)\s*(?:fast|great)',
        r'(?:fast|great).*(?:3|4|three|four)\s*(?:times|×|x)',
        r'(?:significant|notable|substantial).*(?:increas|fast)',
        r'(?:rapid|steep).*(?:recent|post|after|since)',
    ]
    scores["acceleration"] = 1.0 if any(re.search(p, content_lower) for p in accel_patterns) else 0.0

    # First year > +0.5°C (1998)
    first_05_patterns = [
        r'199[78].*(?:first|exceed|cross|breach|surpass).*0\.5',
        r'(?:first|exceed|cross|breach|surpass).*0\.5.*199[78]',
        r'0\.5\s*°?C.*(?:first|exceed|cross).*199[78]',
        r'199[78].*0\.[56]\d*.*(?:first|milestone)',
    ]
    scores["first_05"] = 1.0 if any(re.search(p, content_lower) or re.search(p, content) for p in first_05_patterns) else 0.0

    # First year > +1.0°C (2015 or 2016)
    first_10_patterns = [
        r'201[56].*(?:first|exceed|cross|breach|surpass).*1\.0',
        r'(?:first|exceed|cross|breach|surpass).*1\.0.*201[56]',
        r'1\.0\s*°?C.*(?:first|exceed|cross).*201[56]',
        r'201[56].*1\.[01]\d*.*(?:first|milestone)',
    ]
    scores["first_10"] = 1.0 if any(re.search(p, content_lower) or re.search(p, content) for p in first_10_patterns) else 0.0

    # Decade comparison (recent vs earliest)
    decade_patterns = [
        r'(?:2010|2014|2020|recent).*(?:1880|earliest|first)',
        r'(?:1880|earliest|first).*(?:2010|2014|2020|recent)',
        r'~?1\.0\d*\s*°?C.*(?:warmer|higher|difference|increase)',
        r'(?:warmer|higher|difference|increase).*~?1\.0\d*\s*°?C',
    ]
    scores["decade_comparison"] = 1.0 if any(re.search(p, content_lower) or re.search(p, content) for p in decade_patterns) else 0.0

    # Summary
    summary_patterns = [
        r'summar',
        r'conclusion',
        r'in\s+(?:summary|conclusion)',
        r'overall.*(?:trend|warming|temperature)',
        r'(?:clear|unmistakable|evident|undeniable).*(?:warm|trend)',
    ]
    scores["summary"] = 1.0 if any(re.search(p, content_lower) for p in summary_patterns) else 0.0

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Quantitative Accuracy (Weight: 35%)

**Score 1.0**：线性回归斜率、十年速率和里程碑年份均数值正确，并附单位清晰说明。
**Score 0.75**：大多数值正确，仅在次要数字上有一两处轻微错误。
**Score 0.5**：部分数值正确，但关键数字（整体速率、里程碑年份）错误。
**Score 0.25**：少量数值正确；存在根本性计算错误。
**Score 0.0**：没有正确的计算。

### Criterion 2: Trend Analysis Depth (Weight: 30%)

**Score 1.0**：通过对 1950 年前后速率的定量比较清晰展现变暖加速。识别里程碑跨越及正确年份。提供有意义的十年对比，展现近期变暖的量级。
**Score 0.75**：加速分析良好，大多数组成部分齐全且准确。
**Score 0.5**：提及加速但缺乏定量支撑或遗漏关键组成部分。
**Score 0.25**：趋势描述肤浅，无定量分析。
**Score 0.0**：无趋势分析。

### Criterion 3: Report Quality (Weight: 20%)

**Score 1.0**：markdown 结构良好，章节清晰，适当使用表格或格式化数字，并以连贯叙述串联各项分析。
**Score 0.75**：结构良好，仅有轻微格式或组织问题。
**Score 0.5**：包含分析内容，但难以阅读或格式较差。
**Score 0.25**：杂乱无章或缺少主要章节。
**Score 0.0**：无报告或为空。

### Criterion 4: Completeness (Weight: 15%)

**Score 1.0**：包含所有要求的要素：整体趋势、分时段分析、最冷/最暖区间、里程碑跨越、十年对比和总结。
**Score 0.75**：包含大多数要素，仅有一处轻微遗漏。
**Score 0.5**：缺少若干要素。
**Score 0.25**：仅包含少数要素。
**Score 0.0**：报告缺失或几乎为空。

---

## Additional Notes

本任务测试 Agent 以下能力：

- 对时间序列数据进行线性回归
- 将数据分割为不同时段并比较趋势
- 识别序列数据中的阈值跨越
- 跨时段比较聚合统计量
- 将定量发现综合为连贯的叙述

升温速率的计算需要对年均异常拟合一条直线。Agent 必须处理 YYYY-MM 日期格式、聚合为年均值并正确计算斜率。

已知正确数值（GISTEMP）：

- 全时段斜率：约 0.008°C/年（约 0.08°C/十年），R² 约 0.77
- 1950 年前斜率：约 0.004°C/年（约 0.04°C/十年）
- 1950 年后斜率：约 0.015°C/年（约 0.15°C/十年）
- 按平均值最冷的十年：1910 年代（约 -0.33°C）
- 最暖的完整十年：2010 年代（约 0.80°C）
- 首次超过 +0.5°C 的年份：1998（约 0.61°C）
- 首次超过 +1.0°C 的年份：2016（约 1.01°C）
- 2014–2023 平均：约 0.96°C；1880–1889 平均：约 -0.21°C；差异：约 1.17°C
