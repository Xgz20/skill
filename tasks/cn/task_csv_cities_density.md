---
id: task_csv_cities_density
name: 美国各州人口集中度
category: CSV 数据分析
scene: 数据库检索、表格整理与数据分析
sub_scene: CSV 数据分析
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 代码生成与理解
- 自然语言生成
- 输出格式适配
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

请分析各州的人口集中度模式，并将你的发现写入 `cities_density_report.md`。你的报告应包含：

1. **各州人口集中度**：对每个州，计算每座城市的平均人口（该州在数据集中的总人口 ÷ 城市数量）。按此指标对各州排名，展示前 10 和后 10。

2. **单一城市主导度**：对于拥有 5 座及以上城市的州，计算该州数据集总人口中居住在最大城市的百分比。识别出最大城市主导度最高的前 5 个州。

3. **州代表性**：数据集中出现了多少个不同的州（含 DC）？哪些州的城市数量最多，哪些最少（仅 1 或 2 座）？

4. **州内人口不均**：对于拥有 10 座以上城市的州，计算最大城市人口与最小城市人口之比。哪些州的城市规模分布最均衡，哪些最不均衡？

5. **区域汇总**：将各州分组为区域（Northeast、Southeast、Midwest、West），对比各区域的总人口、城市数量和平均城市规模。

---

## Expected Behavior

Agent 应当：

1. 读取并解析 CSV 文件
2. 按州分组并计算各州指标
3. 计算集中度比率和主导度百分比
4. 识别各州内部人口在城市间分布的规律
5. 创建区域分组并对比

预期关键值：

- 不同的州/地区：48（47 个州 + DC）
- 每城市平均人口最高：DC（646,449 —— 仅 1 座城市），其次为 New York（584,314，含 17 座城市）
- 每城市平均人口最低：Vermont（42,284 —— 1 座城市），West Virginia（约 50,000，含 2 座城市）
- 城市最多：California（212），Texas（83），Florida（73）
- 仅有 1 座城市的州：DC、Hawaii、Alaska、Vermont、Maine（取决于具体计数）
- California 最大城市（LA，3,884,307）约占 CA 数据集总人口（27,910,620）的 13.9%
- New York 州：NYC（8,405,837）约占该州数据集总数（9,933,332）的 84.6% —— 极端主导

---

## Grading Criteria

- [ ] 创建了报告文件 `cities_density_report.md`
- [ ] 计算了每城市平均人口并按州排名
- [ ] 识别出 New York 州具有高集中度（NYC 主导）
- [ ] 为符合条件的州计算了单一城市主导度百分比
- [ ] 正确报告了不同州/地区的数量（约 48）
- [ ] 识别出城市数量最少的州
- [ ] 为符合条件的州计算了人口不均比率
- [ ] 创建并对比了区域分组
- [ ] 报告结构良好，章节清晰

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the US cities population concentration task.

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

    report_path = workspace / "cities_density_report.md"
    if not report_path.exists():
        for alt in ["density_report.md", "report.md", "concentration_report.md", "cities_report.md"]:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "avg_pop_ranking": 0.0,
            "nyc_dominance": 0.0,
            "state_count": 0.0,
            "single_city_states": 0.0,
            "inequality_ratios": 0.0,
            "regional_summary": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Average population per city ranking — New York state should be near top
    ny_patterns = [
        r'new\s*york.*584',
        r'new\s*york.*highest.*average',
        r'new\s*york.*(?:concentration|dominat)',
    ]
    scores["avg_pop_ranking"] = 1.0 if any(re.search(p, content_lower) for p in ny_patterns) else 0.0

    # NYC dominance — ~84-85% of NY state's dataset population
    nyc_dom_patterns = [r'8[45][\.\d]*\s*%', r'84\.6', r'84\.5', r'8[45]\s*percent']
    has_nyc_dom = any(re.search(p, content_lower) for p in nyc_dom_patterns)
    has_nyc_mention = "new york" in content_lower and ("dominan" in content_lower or "concentrat" in content_lower or "largest" in content_lower)
    scores["nyc_dominance"] = 1.0 if has_nyc_dom else (0.5 if has_nyc_mention else 0.0)

    # State count (~48)
    state_count_patterns = [r'4[78]\s*(?:state|distinct|unique|territor|entri)', r'(?:state|distinct|unique|territor|entri)\w*\s*.*4[78]', r'4[78]\s+state']
    scores["state_count"] = 1.0 if any(re.search(p, content_lower) for p in state_count_patterns) else 0.0

    # Single-city states
    single_states = ["vermont", "maine", "alaska", "hawaii"]
    found_single = sum(1 for s in single_states if s in content_lower)
    scores["single_city_states"] = 1.0 if found_single >= 3 else (0.5 if found_single >= 2 else 0.0)

    # Inequality ratios (largest/smallest within state)
    ratio_patterns = [r'ratio', r'inequalit', r'largest.*smallest', r'most.*least.*equal']
    scores["inequality_ratios"] = 1.0 if any(re.search(p, content_lower) for p in ratio_patterns) else 0.0

    # Regional summary
    regions = ["northeast", "southeast", "midwest", "west"]
    alt_regions = ["south", "east", "pacific", "mountain", "atlantic", "central"]
    region_count = sum(1 for r in regions if r in content_lower)
    alt_count = sum(1 for r in alt_regions if r in content_lower)
    scores["regional_summary"] = 1.0 if region_count >= 3 else (0.5 if (region_count >= 2 or alt_count >= 3) else 0.0)

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Analytical Accuracy (Weight: 35%)

**Score 1.0**：所有集中度指标、主导度百分比和比率都计算正确。州分组和计数准确。
**Score 0.75**：大部分指标正确，仅有一两处小错误。
**Score 0.5**：部分指标正确，但若干关键计算有误。
**Score 0.25**：大部分计算存在重大错误。
**Score 0.0**：没有正确的分析。

### Criterion 2: Insight Quality (Weight: 30%)

**Score 1.0**：识别出关键规律，如 NYC 在 New York 州的极端主导、California 的人口分散、处于边缘的单一城市州，以及有意义的区域差异。对规律的含义得出结论。
**Score 0.75**：良好的规律识别，覆盖大部分关键洞察。
**Score 0.5**：有一些观察，但遗漏了主要规律。
**Score 0.25**：大多是原始数字，几乎没有解读。
**Score 0.0**：没有识别出洞察或规律。

### Criterion 3: Completeness (Weight: 20%)

**Score 1.0**：全部五个要求的章节齐备，每个章节分析详尽。
**Score 0.75**：所有章节齐备，仅有小缺口。
**Score 0.5**：缺少某些章节。
**Score 0.25**：缺少大部分章节。
**Score 0.0**：报告缺失或为空。

### Criterion 4: Report Structure (Weight: 15%)

**Score 1.0**：组织良好，章节清晰，使用适当的表格，从集中度指标到洞察逻辑流畅。
**Score 0.75**：组织良好，仅有小的格式问题。
**Score 0.5**：包含分析但结构混乱。
**Score 0.25**：难以理解。
**Score 0.0**：无报告或无法使用。

---

## Additional Notes

本任务测试 Agent 的以下能力：

- 对分类数据（state）进行分组操作
- 计算派生指标（平均值、百分比、比率）
- 在分组数据内识别离群点和规律
- 从州级数据创建有意义的区域分组
- 分析子组内的不均/分布情况
- 将多个指标综合为连贯的洞察

数据集没有面积或密度列——这里的"density"概念指的是人口集中度模式，而非每平方英里的地理密度。Agent 应基于可用数据（人口数和各州城市数）进行分析。

已知正确值：

- 48 个不同的州/地区条目（47 个州 + DC）
- California：212 座城市，数据集中最多
- NYC 约占 New York 州数据集人口的 84.6%
- DC、Hawaii、Alaska、Vermont、Maine 各仅有 1 座城市
- 平均城市人口范围从约 42,284（Vermont）到约 646,449（DC）
