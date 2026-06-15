---
id: task_csv_stations_by_elevation
name: 爱达荷州气象站海拔排名
category: CSV 数据分析
scene: 数据库检索、表格整理与数据分析
sub_scene: CSV 数据分析
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 输出格式适配
- 自然语言生成
- 指令遵循与约束理解
grading_type: hybrid
timeout_seconds: 180
grading_weights:
  automated: 0.6
  llm_judge: 0.4
workspace_files:
  - source: csvs/idaho_weather_stations.csv
    dest: idaho_weather_stations.csv
---

## Prompt

我的工作区里有一个 CSV 文件 `idaho_weather_stations.csv`，包含爱达荷州 213 个气象站的数据。该文件包含以下列：`OBJECTID`、`Station Name`、`Station Code`、`Managing Agency`、`County`、`Longitude`、`Latitude`、`Elevation (feet)`、`x`、`y`。

请按海拔分析这些气象站，并把你的发现写入 `elevation_report.md`。你的报告应包含：

- **海拔最高的 10 个气象站**，从高到低排名，包括站名、海拔、县和管理机构
- **海拔最低的 10 个气象站**，从低到高排名，包括站名、海拔、县和管理机构
- **汇总统计**：所有气象站海拔的最小值、最大值、平均值和中位数
- **按管理机构的海拔分布**：对比 NWS 气象站与 NRCS 气象站的平均海拔，并解释差异
- **平均海拔最高的县**（仅限有 3 个及以上站点的县）和平均海拔最低的县（仅限有 3 个及以上站点的县）
- 一个解读海拔规律的简要**总结段落**

---

## Expected Behavior

Agent 应当：

1. 读取并解析该 CSV 文件（213 行，UTF-8 带 BOM）
2. 按 `Elevation (feet)` 列对站点排序
3. 识别最高站点：MEADOW LAKE SNOTEL，海拔 9,150 英尺（LEMHI 县，NRCS）
4. 识别最低站点：DWORSHAK FISH HATCHERY，海拔 995 英尺（CLEARWATER 县，NWS）
5. 计算汇总统计：最小值 995，最大值 9150，平均值 ~4859，中位数 ~4920
6. 对比各机构：NWS 平均 ~3,993 英尺（143 个站点）vs NRCS 平均 ~6,628 英尺（70 个站点）
7. 识别县级海拔规律（带 3 个及以上站点的筛选）
8. 撰写结构良好的 markdown 报告

关键预期数值：

- 最高：MEADOW LAKE SNOTEL，9,150 英尺
- 最低：DWORSHAK FISH HATCHERY，995 英尺
- 平均海拔：~4,859 英尺
- 中位海拔：~4,920 英尺
- NWS 平均：~3,993 英尺（143 个站点）
- NRCS 平均：~6,628 英尺（70 个站点）
- 前 10 名包括：MEADOW LAKE SNOTEL (9150)、VIENNA MINE PILLOW (8960)、MILL CREEK SUMMIT SNOTEL (8800)、GALENA SUMMIT SNOTEL (8780)、DOLLARHIDE SUMMIT SNOTEL (8420)

---

## Grading Criteria

- [ ] 创建了报告文件 `elevation_report.md`
- [ ] 列出海拔最高的 10 个站点，且 #1 正确（MEADOW LAKE SNOTEL，9150 英尺）
- [ ] 列出海拔最低的 10 个站点，且 #1 正确（DWORSHAK FISH HATCHERY，995 英尺）
- [ ] 汇总统计包含最小值、最大值、平均值和中位数
- [ ] 包含 NWS 与 NRCS 的海拔对比，平均值正确
- [ ] 县级分析，含平均海拔最高/最低
- [ ] 解读规律的总结段落

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the elevation ranking task.

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

    report_path = workspace / "elevation_report.md"
    if not report_path.exists():
        for alt in ["elevation.md", "report.md", "stations_elevation.md", "analysis.md"]:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "highest_station": 0.0,
            "lowest_station": 0.0,
            "summary_stats": 0.0,
            "agency_comparison": 0.0,
            "county_analysis": 0.0,
            "summary_paragraph": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Check highest station (MEADOW LAKE SNOTEL, 9150)
    has_meadow = bool(re.search(r'meadow\s*lake', content_lower))
    has_9150 = bool(re.search(r'9[,.]?150', content))
    scores["highest_station"] = 1.0 if (has_meadow and has_9150) else (0.5 if has_meadow or has_9150 else 0.0)

    # Check lowest station (DWORSHAK FISH HATCHERY, 995)
    has_dworshak = bool(re.search(r'dworshak', content_lower))
    has_995 = bool(re.search(r'\b995\b', content))
    scores["lowest_station"] = 1.0 if (has_dworshak and has_995) else (0.5 if has_dworshak or has_995 else 0.0)

    # Check summary statistics
    stats_found = 0
    if re.search(r'\b995\b', content):
        stats_found += 1
    if re.search(r'9[,.]?150', content):
        stats_found += 1
    if re.search(r'4[,.]?8[56]\d', content):
        stats_found += 1
    if re.search(r'4[,.]?9[12]\d', content):
        stats_found += 1
    scores["summary_stats"] = min(1.0, stats_found / 3)

    # Check agency comparison
    has_nws_avg = bool(re.search(r'(?:3[,.]?99\d|3[,.]?98\d|4[,.]?0[01]\d)', content))
    has_nrcs_avg = bool(re.search(r'(?:6[,.]?6[23]\d|6[,.]?64\d)', content))
    has_agency_text = bool(re.search(r'nws.*nrcs|nrcs.*nws', content_lower))
    scores["agency_comparison"] = 1.0 if (has_nws_avg and has_nrcs_avg) else (0.5 if has_agency_text else 0.0)

    # Check county analysis
    county_patterns = [r'county', r'counties', r'highest.*average.*elevation', r'lowest.*average.*elevation']
    county_found = sum(1 for p in county_patterns if re.search(p, content_lower))
    scores["county_analysis"] = 1.0 if county_found >= 2 else (0.5 if county_found >= 1 else 0.0)

    # Check for summary/interpretation paragraph
    summary_patterns = [
        r'(?:summary|interpretation|overview|conclusion|pattern)',
        r'(?:nrcs|snotel).*(?:higher|mountain|alpine|backcountry)',
        r'(?:nws).*(?:lower|valley|town|populated|urban)',
    ]
    summary_found = sum(1 for p in summary_patterns if re.search(p, content_lower))
    scores["summary_paragraph"] = 1.0 if summary_found >= 2 else (0.5 if summary_found >= 1 else 0.0)

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Data Accuracy (Weight: 35%)

**Score 1.0**：所有排名正确，统计准确（平均值 ~4859，中位数 ~4920，前/后 10 名正确），机构平均值与预期数值一致。
**Score 0.75**：排名和统计大体正确，仅有轻微差异（例如平均值偏差几英尺）。
**Score 0.5**：最高和最低站点正确，但中间排名或统计有错误。
**Score 0.25**：排名或统计有若干重大错误。
**Score 0.0**：未尝试分析或根本性错误。

### Criterion 2: Analytical Depth (Weight: 30%)

**Score 1.0**：对 NWS 与 NRCS 差异（NRCS/SNOTEL 站点是高海拔积雪监测点，而 NWS 站点在有人居住的山谷）、县级规律和海拔分布提供有意义的解读。
**Score 0.75**：良好的解读，仅在解释机构差异上有小缺口。
**Score 0.5**：陈述事实但解读或洞见有限。
**Score 0.25**：除列出数字外分析很少。
**Score 0.0**：未提供任何分析或解读。

### Criterion 3: Report Completeness (Weight: 20%)

**Score 1.0**：所有要求的章节都齐全：前 10、后 10、汇总统计、机构对比、县级分析、总结段落。
**Score 0.75**：大部分章节齐全，仅有一处小遗漏。
**Score 0.5**：缺少若干章节。
**Score 0.25**：仅有一两个章节。
**Score 0.0**：报告缺失或为空。

### Criterion 4: Presentation Quality (Weight: 15%)

**Score 1.0**：格式良好的 markdown，配有表格、清晰标题和有组织的布局。
**Score 0.75**：格式良好，仅有轻微问题。
**Score 0.5**：可读但组织较差。
**Score 0.25**：难以阅读。
**Score 0.0**：没有报告或不可读。

---

## Additional Notes

本任务测试 Agent 的以下能力：

- 解析包含混合数据类型和 BOM 标记的 CSV 文件
- 按数值列排序和排名数据
- 计算基本描述性统计（最小值、最大值、平均值、中位数）
- 执行分组分析（按机构、按县）
- 解读数据中的规律并解释现实世界背景

该数据集包含由两家机构管理的 213 个爱达荷州气象站：NWS（National Weather Service，143 个站点）和 NRCS（Natural Resources Conservation Service，70 个站点）。NRCS 站点（SNOTEL/Pillow 站点）主要是高海拔积雪监测站，而 NWS 站点往往位于海拔较低的有人居住区域。

已知正确数值：

- 共 213 个站点（143 个 NWS，70 个 NRCS）
- 海拔范围：995 英尺至 9,150 英尺
- 平均值：~4,859 英尺，中位数：~4,920 英尺
- NWS 平均：~3,993 英尺，NRCS 平均：~6,628 英尺
- 最高：MEADOW LAKE SNOTEL（9,150 英尺，LEMHI）
- 最低：DWORSHAK FISH HATCHERY（995 英尺，CLEARWATER）
- 5 个站点的县数据缺失
