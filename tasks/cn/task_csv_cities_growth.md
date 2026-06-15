---
id: task_csv_cities_growth
name: 美国城市地理分布分析
category: CSV 数据分析
scene: 数据库检索、表格整理与数据分析
sub_scene: CSV 地理分布分析
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 代码生成与理解
- 输出格式适配
- 自然语言生成
grading_type: hybrid
timeout_seconds: 180
grading_weights:
  automated: 0.6
  llm_judge: 0.4
workspace_files:
  - source: csvs/us_cities_top1000.csv
    dest: us_cities_top1000.csv
---

## Prompt

我的工作区中有一个 CSV 文件 `us_cities_top1000.csv`，包含美国最大的 1000 座城市的数据。该文件的列为：`City`、`State`、`Population`、`lat`、`lon`。

请分析这些城市的地理分布，并将你的发现写入 `cities_geographic_report.md`。你的报告应包含：

1. **人口地理中心**：计算人口加权的质心（以人口为权重的纬度和经度加权平均）。将其与所有城市位置的简单非加权质心进行对比。两者的差异说明了什么？

2. **地理极值**：识别最北、最南、最东、最西的城市。包含它们的坐标和人口。

3. **纬度带分析**：将城市划分为 5° 的纬度带（30°N 以下、30-35°N、35-40°N、40-45°N、45°N 以上）。对每个带，报告城市数量、总人口和平均城市人口。哪个带城市最多？哪个总人口最多？

4. **东西分割**：以经度 -95°W 为分界线，对比全国东西两半的城市数量、总人口和平均城市规模。

5. **各州地理跨度**：对于拥有 10 座以上城市的州，用最大与最小纬度、经度的简单差值，计算该州任意两座城市之间的最大距离（以度为单位）作为地理跨度。哪些州在地理上分布最广？

---

## Expected Behavior

Agent 应当：

1. 读取并解析 CSV 文件
2. 计算加权和非加权的地理质心
3. 使用 lat/lon 列找出极值位置
4. 按纬度对城市分箱并计算每个带的统计量
5. 按经度分割并对比两半
6. 计算各州的地理范围

预期关键值：

- 人口加权质心：约 (36.99°N, 96.51°W)
- 非加权质心：约 (37.34°N, 96.48°W)
- 最北：Anchorage, Alaska (61.22°N)
- 最南：Honolulu, Hawaii (21.31°N)
- 最东：Portland, Maine (70.26°W)
- 最西：Honolulu, Hawaii (157.86°W)
- 某纬度带中城市最多：40-45°N（316 座城市）
- 某带中总人口最多：30-35°N（38,580,127）
- 95°W 以东：546 座城市，人口约 67,016,952
- 95°W 以西：454 座城市，人口约 64,115,491

---

## Grading Criteria

- [ ] 创建了报告文件 `cities_geographic_report.md`
- [ ] 计算了人口加权质心（约 37°N，96-97°W）
- [ ] 计算了非加权质心并与加权质心对比
- [ ] 正确识别了全部四个地理极值
- [ ] 含城市数量和人口的纬度带分析
- [ ] 包含东西分割对比
- [ ] 为符合条件的州计算了地理跨度
- [ ] 从地理规律中得出关键洞察
- [ ] 报告结构良好，章节清晰

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the US cities geographic distribution task.

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

    report_path = workspace / "cities_geographic_report.md"
    if not report_path.exists():
        for alt in ["geographic_report.md", "report.md", "geo_report.md", "cities_report.md",
                     "distribution_report.md", "cities_growth_report.md"]:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "weighted_centroid": 0.0,
            "geographic_extremes": 0.0,
            "latitude_bands": 0.0,
            "east_west_split": 0.0,
            "state_spread": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Weighted centroid (~37°N, ~96-97°W)
    centroid_patterns = [
        r'3[67]\.?\d*.*9[67]\.?\d*',
        r'centroid',
        r'weighted\s*(?:average|center|mean)',
        r'center\s*of\s*population',
    ]
    has_centroid_concept = any(re.search(p, content_lower) for p in centroid_patterns[1:])
    has_centroid_values = bool(re.search(r'3[67]\.\d', content))
    scores["weighted_centroid"] = 1.0 if (has_centroid_concept and has_centroid_values) else (0.5 if has_centroid_concept else 0.0)

    # Geographic extremes
    extremes = {
        "anchorage": "anchorage" in content_lower,
        "honolulu": "honolulu" in content_lower,
        "portland_me": bool(re.search(r'portland.*maine', content_lower)),
    }
    extreme_count = sum(extremes.values())
    scores["geographic_extremes"] = 1.0 if extreme_count >= 3 else (0.5 if extreme_count >= 2 else 0.0)

    # Latitude band analysis
    band_patterns = [r'30.*35', r'35.*40', r'40.*45', r'latitude.*band', r'latitude.*zone']
    band_indicators = sum(1 for p in band_patterns if re.search(p, content_lower))
    has_316 = "316" in content  # most cities in 40-45 band
    scores["latitude_bands"] = 1.0 if (band_indicators >= 2 and has_316) else (0.5 if band_indicators >= 2 else 0.0)

    # East-West split
    ew_patterns = [r'east.*west', r'95.*(?:°|degree|longitude)', r'(?:^|\D)546\s*(?:cit|\b)', r'(?:^|\D)454\s*(?:cit|\b)']
    ew_count = sum(1 for p in ew_patterns if re.search(p, content_lower))
    scores["east_west_split"] = 1.0 if ew_count >= 3 else (0.5 if ew_count >= 2 else 0.0)

    # State geographic spread
    spread_patterns = [r'spread', r'extent', r'geographic.*range', r'distance.*between',
                       r'max.*min.*lat', r'latitude.*range']
    scores["state_spread"] = 1.0 if any(re.search(p, content_lower) for p in spread_patterns) else 0.0

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Analytical Accuracy (Weight: 35%)

**Score 1.0**：质心计算正确，极值识别正确（包括 Honolulu 同时是最南和最西），纬度带与预期数量相符，东西分割准确。
**Score 0.75**：大部分计算正确，仅有一两处小错误。
**Score 0.5**：部分正确，但若干关键计算有误。
**Score 0.25**：地理计算存在重大错误。
**Score 0.0**：没有正确的分析。

### Criterion 2: Insight Quality (Weight: 30%)

**Score 1.0**：从数据中得出有意义的结论——例如人口集中在 30-45°N 走廊、人口加权质心相对非加权质心略微南移、东西人口大致平衡，以及 Hawaii/Alaska 如何使地理极值产生偏斜。
**Score 0.75**：在大多数章节有良好洞察。
**Score 0.5**：有一些观察，但遗漏了主要规律。
**Score 0.25**：大多是原始数字。
**Score 0.0**：没有解读。

### Criterion 3: Completeness (Weight: 20%)

**Score 1.0**：全部五项要求的分析齐备，处理详尽。
**Score 0.75**：所有章节齐备，仅有小缺口。
**Score 0.5**：缺少某些章节。
**Score 0.25**：缺少大部分章节。
**Score 0.0**：报告缺失或为空。

### Criterion 4: Report Structure (Weight: 15%)

**Score 1.0**：组织良好，章节清晰，纬度带数据用表格，逻辑流畅。
**Score 0.75**：组织良好，仅有小问题。
**Score 0.5**：包含分析但组织混乱。
**Score 0.25**：难以理解。
**Score 0.0**：无报告或无法使用。

---

## Additional Notes

本任务测试 Agent 的以下能力：

- 处理地理坐标（纬度/经度）
- 计算加权和非加权平均值
- 将连续数据分箱为离散区间
- 沿分界线分割数据并对比两半
- 计算每组的跨度/范围指标
- 从数值分析中解读地理规律

数据集包含全部 1000 座城市的 lat/lon 坐标。Hawaii（Honolulu）作为同时为最南和最西的城市是个离群点。Alaska（Anchorage）是最北的。美国本土城市的纬度大致跨越 25°N 到 48°N，经度跨越 70°W 到 122°W。

已知正确值：

- 人口加权质心：约 (36.99°N, 96.51°W)
- 非加权质心：约 (37.34°N, 96.48°W)
- 极值：Anchorage（北），Honolulu（南+西），Portland ME（东）
- 40-45°N 带：316 座城市（最多）；30-35°N 带：38,580,127 人口（最多）
- 95°W 以东：546 座城市 / 67.0M 人口；以西：454 座城市 / 64.1M 人口
