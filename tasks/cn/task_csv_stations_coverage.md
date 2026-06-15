---
id: task_csv_stations_coverage
name: 爱达荷州气象站覆盖缺口分析
category: CSV 数据分析
scene: 数据库检索、表格整理与数据分析
sub_scene: CSV 数据分析
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 工具调用
- 输出格式适配
- 自然语言生成
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

爱达荷州有 44 个县。请分析气象站网络的地理和海拔覆盖情况，并把你的发现写入 `coverage_report.md`。你的报告应包含：

- **县级覆盖**：爱达荷州 44 个县中有多少个县拥有至少一个气象站？哪个（或哪些）县没有任何气象站？
- **各县气象站密度**：哪些县的气象站最多，哪些县（在有站点的县中）最少？
- **海拔区间分布**：将气象站按海拔区间分组（例如每 1,000 英尺一个区间）并统计落入各区间的气象站数量。识别哪些海拔区间过度集中、哪些覆盖不足。
- **机构覆盖对比**：NWS 与 NRCS 的站点布局在地理上有何不同？哪些县仅由 NWS、仅由 NRCS 或同时由两者服务？
- **数据质量问题**：识别任何县数据缺失或空白的气象站。
- 一个**建议章节**，提出在何处增设气象站能改善覆盖。

---

## Expected Behavior

Agent 应当：

1. 读取并解析该 CSV 文件（213 行）
2. 将站点所属县与爱达荷州的 44 个县交叉对照
3. 发现 44 个县中有 43 个有站点；Payette County 没有任何气象站
4. 注意到 5 个站点的县数据空白/缺失
5. 识别顶部县：Idaho (13)、Blaine (11)、Shoshone (10)、Custer (10)、Clearwater (10)
6. 识别仅有单个站点的县：Kootenai、Jefferson、Nez Perce、Madison、Lincoln
7. 创建海拔区间分布，显示集中在 4,000-6,000 英尺范围
8. 对比 NWS（143 个站点，较低海拔）与 NRCS（70 个站点，较高海拔）
9. 撰写带建议的结构化报告

关键预期数值：

- 总站点数：213
- 有站点的县：44 个中的 43 个（若按非空白县数据计算则为 38-39 个）
- 缺失的县：Payette County 没有站点
- 5 个站点的县字段为空白
- 站点最多：Idaho County (13)
- 机构：NWS (143)、NRCS (70)
- 最大的海拔区间：4,000-5,000 英尺（37 个站点）、5,000-6,000 英尺（42 个站点）
- 站点最少：2,000 英尺以下（10 个站点）、8,000 英尺以上（7 个站点）

---

## Grading Criteria

- [ ] 创建了报告文件 `coverage_report.md`
- [ ] 识别 Payette County 为没有气象站的县
- [ ] 包含各县气象站数量，顶部县正确
- [ ] 包含海拔区间分布
- [ ] 包含 NWS 与 NRCS 的地理对比
- [ ] 识别出县数据缺失（5 个站点）
- [ ] 包含建议章节

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the coverage gap analysis task.

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

    report_path = workspace / "coverage_report.md"
    if not report_path.exists():
        for alt in ["coverage.md", "report.md", "gap_analysis.md", "analysis.md", "coverage_analysis.md"]:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "payette_identified": 0.0,
            "county_counts": 0.0,
            "elevation_bands": 0.0,
            "agency_comparison": 0.0,
            "missing_data": 0.0,
            "recommendations": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Check Payette County identified as missing
    has_payette = bool(re.search(r'payette', content_lower))
    has_zero_or_no = bool(re.search(r'payette.*(?:no |zero|0 |missing|without|lack)', content_lower) or
                         re.search(r'(?:no |zero|0 |missing|without|lack).*payette', content_lower))
    scores["payette_identified"] = 1.0 if has_payette else 0.0

    # Check county station counts
    top_counties = ['idaho', 'blaine', 'shoshone', 'custer', 'clearwater']
    county_mentions = sum(1 for c in top_counties if re.search(rf'\b{c}\b.*\b1[0-3]\b|\b1[0-3]\b.*\b{c}\b', content_lower))
    scores["county_counts"] = 1.0 if county_mentions >= 3 else (0.5 if county_mentions >= 1 else 0.0)

    # Check elevation band distribution
    elev_indicators = 0
    if re.search(r'elevation.*band|band.*elevation|elevation.*range|elevation.*distribution', content_lower):
        elev_indicators += 1
    if re.search(r'(?:4[,.]?000|5[,.]?000|6[,.]?000)', content):
        elev_indicators += 1
    if re.search(r'(?:37|42)\s*station', content_lower) or re.search(r'(?:over|under).*represent', content_lower):
        elev_indicators += 1
    scores["elevation_bands"] = 1.0 if elev_indicators >= 2 else (0.5 if elev_indicators >= 1 else 0.0)

    # Check NWS vs NRCS comparison
    has_nws = bool(re.search(r'\bnws\b', content_lower))
    has_nrcs = bool(re.search(r'\bnrcs\b', content_lower))
    has_143 = bool(re.search(r'\b143\b', content))
    has_70 = bool(re.search(r'\b70\b', content))
    scores["agency_comparison"] = 1.0 if (has_nws and has_nrcs and (has_143 or has_70)) else (0.5 if (has_nws and has_nrcs) else 0.0)

    # Check missing data identification
    missing_patterns = [
        r'(?:5|five)\s*station.*(?:missing|blank|empty)',
        r'(?:missing|blank|empty).*(?:5|five)\s*station',
        r'(?:missing|blank|empty).*county',
        r'county.*(?:missing|blank|empty)',
    ]
    scores["missing_data"] = 1.0 if any(re.search(p, content_lower) for p in missing_patterns) else 0.0

    # Check recommendations
    rec_patterns = [
        r'recommend',
        r'suggest',
        r'additional\s*station',
        r'improv.*coverage',
        r'gap.*(?:fill|address|close)',
    ]
    scores["recommendations"] = 1.0 if any(re.search(p, content_lower) for p in rec_patterns) else 0.0

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Coverage Analysis Accuracy (Weight: 35%)

**Score 1.0**：正确识别 44 个县中有 43 个有站点，指出 Payette 为缺失的县，提供各县准确的站点数量，并正确识别县数据缺失的 5 个站点。
**Score 0.75**：大多数覆盖事实正确，仅有一两处小错误（例如某县计数略有偏差）。
**Score 0.5**：识别出一些缺口但遗漏 Payette 或有若干计数错误。
**Score 0.25**：尝试覆盖分析但有重大事实错误。
**Score 0.0**：没有覆盖分析或完全错误。

### Criterion 2: Elevation Distribution Quality (Weight: 25%)

**Score 1.0**：清晰的海拔区间细分，计数准确，识别出 4,000-6,000 英尺的集中区，注意到 2,000 英尺以下和 8,000 英尺以上的稀疏覆盖。
**Score 0.75**：良好的海拔细分，仅有轻微计数错误。
**Score 0.5**：包含一些海拔分组但不完整或有错误。
**Score 0.25**：海拔分析很少。
**Score 0.0**：没有包含海拔分布。

### Criterion 3: Agency Analysis (Weight: 20%)

**Score 1.0**：清晰解释 NWS 与 NRCS 之间的地理/海拔分布，识别仅由一家机构服务的县，并对机构差异的原因提供洞见（NWS 在城镇，NRCS 在山区用于积雪监测）。
**Score 0.75**：良好的机构对比，仅有小缺口。
**Score 0.5**：提及两家机构但对比有限。
**Score 0.25**：机构讨论很少。
**Score 0.0**：没有机构分析。

### Criterion 4: Recommendations Quality (Weight: 20%)

**Score 1.0**：与已识别缺口挂钩的具体、可操作建议（例如在 Payette County 增设站点、改善北部县的低海拔覆盖、补全空白的县数据）。
**Score 0.75**：良好的建议，有一定具体性。
**Score 0.5**：未与具体发现挂钩的泛泛建议。
**Score 0.25**：含糊或无帮助的建议。
**Score 0.0**：没有建议章节。

---

## Additional Notes

本任务测试 Agent 的以下能力：

- 将数据集与外部知识（爱达荷州的 44 个县）交叉对照
- 识别数据集中的缺口和缺失数据
- 创建有意义的分组（海拔区间）和分布
- 对比数据子集（NWS 与 NRCS）
- 将发现综合为可操作的建议

该数据集存在已知的数据质量问题：5 个站点的县字段为空白（BEAR SADDLE SNOTEL、HOWELL CANYON SNOTEL、MILL CREEK SUMMIT SNOTEL、MOOSE CREEK SNOTEL、SQUAW FLAT PILLOW）。优秀的回答会标记这些。

爱达荷州的 44 个县：Ada、Adams、Bannock、Bear Lake、Benewah、Bingham、Blaine、Boise、Bonner、Bonneville、Boundary、Butte、Camas、Canyon、Caribou、Cassia、Clark、Clearwater、Custer、Elmore、Franklin、Fremont、Gem、Gooding、Idaho、Jefferson、Jerome、Kootenai、Latah、Lemhi、Lewis、Lincoln、Madison、Minidoka、Nez Perce、Oneida、Owyhee、Payette、Power、Shoshone、Teton、Twin Falls、Valley、Washington。

已知正确数值：

- 共 213 个站点，143 个 NWS + 70 个 NRCS
- 44 个县中有 43 个有站点（Payette 缺失）
- 5 个站点的县字段为空白
- 站点最多：Idaho (13)、Blaine (11)、Shoshone/Custer/Clearwater（各 10 个）
- 单站点县：Kootenai、Jefferson、Nez Perce、Madison、Lincoln
