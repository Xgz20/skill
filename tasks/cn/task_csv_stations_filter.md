---
id: task_csv_stations_filter
name: 爱达荷州气象站多条件筛选
category: CSV 数据分析
scene: 数据库检索、表格整理与数据分析
sub_scene: CSV 数据分析
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 输出格式适配
- 工具调用
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

请执行以下筛选和分析任务，并把结果写入 `filter_report.md`：

1. **高海拔 NWS 气象站**：找出所有由 NWS 管理且海拔在 5,000 英尺及以上的气象站。按海拔（从高到低）排序，列出站名、海拔和县。一共有多少个？

2. **Custer County 的 NRCS 气象站**：找出所有位于 Custer County 的 NRCS 管理气象站。列出站名和海拔，按海拔（从高到低）排序。

3. **低海拔南部气象站**：找出所有海拔在 3,000 到 4,000 英尺（含端点）之间且位于北纬 43°N 以南的气象站。纬度列采用 DMS 格式（例如 "42 57 00"）。列出站名、县、海拔和纬度。

4. **汇总表**：创建一个交叉表，显示按管理机构（NWS、NRCS）和海拔类别（Below 3000、3000-4999、5000-6999、7000+）划分的气象站数量。

对每个筛选条件，说明匹配气象站的总数。

---

## Expected Behavior

Agent 应当：

1. 解析该 CSV 文件，处理 BOM 和 DMS 格式坐标
2. 筛选 >= 5,000 英尺的 NWS 气象站：找出恰好 39 个，最高的是海拔 7,300 英尺的 GALENA
3. 筛选 Custer County 的 NRCS 气象站：找出 4 个（DOLLARHIDE SUMMIT SNOTEL 8420、HILTS CREEK SNOTEL 8000、BEAR CANYON SNOTEL 7900、STICKNEY MILL SNOTEL 7430）
4. 解析 DMS 纬度，筛选北纬 43°N 以南海拔 3000-4000 英尺的站：找出 8 个，包括 BLISS 4 NW、BUHL 2、CASTLEFORD 2 N、GOODING 2S、JEROME、SHOSHONE 1 WNW、TWIN FALLS KVMT、TWIN FALLS WSO
5. 构建机构 × 海拔类别的交叉表
6. 将整理好的结果写入报告文件

关键预期数值：

- NWS >= 5000 英尺：39 个；最高为 GALENA，7,300 英尺
- Custer 的 NRCS：4 个；DOLLARHIDE SUMMIT SNOTEL (8,420 英尺) 最高
- 北纬 43°N 以南 3000-4000 英尺：8 个
- 交叉表合计：NWS 143，NRCS 70

---

## Grading Criteria

- [ ] 创建了报告文件 `filter_report.md`
- [ ] NWS >= 5000 英尺的数量为 39
- [ ] 识别 GALENA 为最高的 NWS 气象站，海拔 7,300 英尺
- [ ] Custer County 的 NRCS 数量为 4
- [ ] 识别 DOLLARHIDE SUMMIT SNOTEL，海拔 8,420 英尺
- [ ] 正确解析 DMS 纬度用于南部筛选
- [ ] 识别出 8 个低海拔南部气象站
- [ ] 包含按机构和海拔类别划分的交叉表

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the multi-criteria filtering task.

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

    report_path = workspace / "filter_report.md"
    if not report_path.exists():
        for alt in ["report.md", "filter_results.md", "filtering_report.md", "analysis.md", "stations_filter.md"]:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "nws_high_count": 0.0,
            "nws_highest": 0.0,
            "nrcs_custer_count": 0.0,
            "nrcs_custer_top": 0.0,
            "southern_filter": 0.0,
            "cross_tabulation": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Check NWS >= 5000 ft count (39)
    nws_count_patterns = [r'\b39\b.*(?:station|nws)', r'(?:station|nws).*\b39\b', r'\b39\b']
    scores["nws_high_count"] = 1.0 if any(re.search(p, content_lower) for p in nws_count_patterns) else 0.0

    # Check GALENA as highest NWS station at 7300
    has_galena = bool(re.search(r'galena', content_lower))
    has_7300 = bool(re.search(r'7[,.]?300', content))
    scores["nws_highest"] = 1.0 if (has_galena and has_7300) else (0.5 if has_galena else 0.0)

    # Check NRCS Custer count (4)
    custer_section = re.search(r'custer.*?(?=\n#|\Z)', content_lower, re.DOTALL)
    custer_text = custer_section.group() if custer_section else content_lower
    has_4_custer = bool(re.search(r'\b4\b.*(?:station|nrcs|custer)', custer_text) or
                       re.search(r'(?:station|nrcs|custer).*\b4\b', custer_text))
    scores["nrcs_custer_count"] = 1.0 if has_4_custer else 0.0

    # Check DOLLARHIDE as top NRCS/Custer station
    has_dollarhide = bool(re.search(r'dollarhide', content_lower))
    has_8420 = bool(re.search(r'8[,.]?420', content))
    scores["nrcs_custer_top"] = 1.0 if (has_dollarhide and has_8420) else (0.5 if has_dollarhide else 0.0)

    # Check southern filter (8 stations, latitude parsing)
    southern_stations = ['bliss', 'buhl', 'castleford', 'gooding', 'jerome', 'shoshone', 'twin falls']
    found_southern = sum(1 for s in southern_stations if s in content_lower)
    has_8_count = bool(re.search(r'\b8\b.*(?:station|south|low)', content_lower) or
                      re.search(r'(?:station|south|low).*\b8\b', content_lower))
    scores["southern_filter"] = 1.0 if found_southern >= 5 else (0.5 if found_southern >= 3 else 0.0)

    # Check cross-tabulation
    cross_tab_indicators = 0
    if re.search(r'cross.*tab|tabul|matrix|breakdown.*agency.*elev|agency.*elevation', content_lower):
        cross_tab_indicators += 1
    if re.search(r'\b143\b', content) and re.search(r'\b70\b', content):
        cross_tab_indicators += 1
    if re.search(r'(?:below|under|<)\s*3[,.]?000', content_lower) or re.search(r'7[,.]?000\s*\+|above\s*7', content_lower):
        cross_tab_indicators += 1
    scores["cross_tabulation"] = 1.0 if cross_tab_indicators >= 2 else (0.5 if cross_tab_indicators >= 1 else 0.0)

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Filter Accuracy (Weight: 40%)

**Score 1.0**：全部四个筛选都产生正确结果，计数精确（39、4、8）且站点列表正确。DMS 纬度解析处理正确。
**Score 0.75**：四个筛选中有三个正确；一个有轻微错误。
**Score 0.5**：两个筛选正确；其他有显著错误。
**Score 0.25**：一个筛选正确；其余有重大错误。
**Score 0.0**：没有筛选产生正确结果。

### Criterion 2: DMS Coordinate Handling (Weight: 20%)

**Score 1.0**：正确解析 DMS 格式纬度（例如 "42 57 00" → 42.95°），准确应用 43°N 阈值，并列出全部 8 个匹配站点。
**Score 0.75**：正确解析 DMS 但遗漏一个站点或有轻微边界误差。
**Score 0.5**：尝试 DMS 解析但出现影响结果的错误。
**Score 0.25**：将 DMS 当作十进制度数处理，或仅使用度数部分。
**Score 0.0**：未尝试纬度筛选或完全错误。

### Criterion 3: Cross-Tabulation Quality (Weight: 20%)

**Score 1.0**：清晰的表格/矩阵，机构为行、海拔区间为列，计数准确，行/列合计为 213。
**Score 0.75**：良好的表格，仅有轻微计数错误。
**Score 0.5**：尝试交叉表但格式较差或计数有误。
**Score 0.25**：交叉表努力很少。
**Score 0.0**：没有交叉表。

### Criterion 4: Report Organization (Weight: 20%)

**Score 1.0**：每个筛选结果都清晰分隔在各自的章节中，计数突出显示，站点列表格式良好（表格或排序列表），报告逻辑流畅。
**Score 0.75**：组织良好，仅有轻微格式问题。
**Score 0.5**：结果齐全但组织混乱或难以阅读。
**Score 0.25**：杂乱或章节缺失。
**Score 0.0**：没有报告或不可用。

---

## Additional Notes

本任务测试 Agent 的以下能力：

- 同时应用多个筛选条件（机构 + 海拔、机构 + 县、海拔 + 纬度）
- 将 DMS（度-分-秒）坐标格式解析为十进制度数
- 从类别型 + 数值型数据创建交叉表
- 处理边界情况（CSV 中的 BOM、空白县字段）
- 清晰地呈现带计数和排序列表的筛选结果

DMS 纬度解析是最具挑战性的部分。纬度列采用空格分隔的 DMS 格式（例如 "42 57 00" 表示 42°57'00"N = 42.95°N）。筛选要求正确地将其转换以与 43°N 比较。

已知正确的交叉表：

| Agency | Below 3000 | 3000-4999 | 5000-6999 | 7000+ |
|--------|-----------|-----------|-----------|-------|
| NWS    | 42        | 62        | 38        | 1     |
| NRCS   | 0         | 5         | 39        | 26    |

（行合计：NWS 143，NRCS 70。唯一一个 7000+ 的 NWS 站点是海拔 7,300 英尺的 GALENA。NRCS 在 3,000 英尺以下没有站点。）
