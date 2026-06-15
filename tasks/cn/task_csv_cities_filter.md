---
id: task_csv_cities_filter
name: 美国城市多条件筛选
category: CSV 数据分析
scene: 数据库检索、表格整理与数据分析
sub_scene: CSV 数据筛选
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 输出格式适配
- 指令遵循与约束理解
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

请执行以下筛选分析，并将结果写入 `cities_filter_report.md`：

1. **加州大城市**：列出 California 中人口 ≥ 200,000 的所有城市，按人口降序排列。包含该筛选集合的城市数量和总人口。

2. **南部城市**：找出纬度低于 33°N（即 `lat < 33.0`）且人口 ≥ 100,000 的所有城市。列出它们及其所属州和人口。

3. **州对比 —— Texas vs. Florida**：对比这两个州，分别列出每个州在数据集中的城市总数、总人口、平均城市人口，以及按人口排名的前 5 座城市。

4. **中等规模城市**：找出人口在 75,000 到 125,000 之间（含端点）的所有城市。报告它们有多少座，并按字母顺序列出前 10 座。

5. **西海岸各州**：筛选 California、Oregon 和 Washington 的城市。报告这个合并区域的总数量、总人口，以及按人口排名的前 10 座城市。

---

## Expected Behavior

Agent 应当：

1. 读取并解析 CSV 文件
2. 使用列值正确应用每个筛选条件
3. 对筛选后的子集进行聚合
4. 为每个章节清晰呈现结果

预期关键值：

- California 人口 ≥ 200k 的城市：21 座（最高为 Los Angeles，3,884,307；最低为 Moreno Valley，201,175）
- CA ≥ 200k 子集的总人口：约 12,343,323
- 南部城市（lat < 33.0，pop ≥ 100k）：包括 San Diego、Phoenix、Tucson、El Paso 等城市，以及若干 Texas/Florida/Arizona 城市
- Texas：83 座城市，总人口 14,836,230，最大城市 Houston（2,195,914）
- Florida：73 座城市，总人口 7,410,114，最大城市 Jacksonville（842,583）
- Texas 平均城市人口（约 178,749）高于 Florida（约 101,508）
- 中等规模城市（75k-125k）：该区间内城市数量可观
- 西海岸（CA+OR+WA）：254 座城市，总人口 32,548,214

---

## Grading Criteria

- [ ] 创建了报告文件 `cities_filter_report.md`
- [ ] California ≥ 200k 筛选返回 21 座城市，且列表正确
- [ ] 正确应用了南部城市筛选（lat < 33.0，pop ≥ 100k）
- [ ] Texas vs Florida 对比包含城市数量、合计和平均值
- [ ] 正确显示 Texas 的平均人口高于 Florida
- [ ] 应用了中等规模城市筛选（75k-125k）并列出结果
- [ ] 西海岸各州筛选包含全部三个州
- [ ] 各筛选的数值准确
- [ ] 报告结构良好，每个筛选有清晰章节

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the US cities multi-criteria filtering task.

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

    report_path = workspace / "cities_filter_report.md"
    if not report_path.exists():
        for alt in ["filter_report.md", "report.md", "cities_report.md", "filtering_report.md"]:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "california_filter": 0.0,
            "southern_filter": 0.0,
            "texas_florida_comparison": 0.0,
            "midsize_filter": 0.0,
            "western_coastal_filter": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # California >= 200k: 21 cities
    ca_patterns = [r'21\s*cit', r'twenty.?one\s*cit']
    has_ca_count = any(re.search(p, content_lower) for p in ca_patterns)
    has_ca_cities = "moreno valley" in content_lower and "los angeles" in content_lower
    scores["california_filter"] = 1.0 if (has_ca_count and has_ca_cities) else (0.5 if has_ca_cities else 0.0)

    # Southern cities filter — should mention San Diego, Phoenix, Tucson, El Paso
    southern_cities = ["san diego", "phoenix", "tucson", "el paso"]
    found_southern = sum(1 for c in southern_cities if c in content_lower)
    scores["southern_filter"] = 1.0 if found_southern >= 3 else (0.5 if found_southern >= 2 else 0.0)

    # Texas vs Florida comparison
    has_tx = re.search(r'texas.*83\s*cit|83.*cit.*texas', content_lower)
    has_fl = re.search(r'florida.*73\s*cit|73.*cit.*florida', content_lower)
    has_houston = "houston" in content_lower
    has_jacksonville = "jacksonville" in content_lower
    tx_fl_score = sum([
        bool(has_tx),
        bool(has_fl),
        has_houston,
        has_jacksonville,
    ])
    scores["texas_florida_comparison"] = 1.0 if tx_fl_score >= 4 else (0.5 if tx_fl_score >= 2 else 0.0)

    # Mid-size filter (75k-125k)
    midsize_patterns = [r'75[,.]?000.*125[,.]?000', r'75k.*125k', r'mid.?size', r'medium.?size']
    scores["midsize_filter"] = 1.0 if any(re.search(p, content_lower) for p in midsize_patterns) else 0.0

    # Western coastal filter (CA + OR + WA)
    has_all_states = all(s in content_lower for s in ["california", "oregon", "washington"])
    has_254 = re.search(r'254\s*cit', content_lower) or "254" in content
    scores["western_coastal_filter"] = 1.0 if (has_all_states and has_254) else (0.5 if has_all_states else 0.0)

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Filter Accuracy (Weight: 40%)

**Score 1.0**：全部五个筛选都正确应用，数量和数值准确。边界条件处理得当（≥ 对比 >、含端点的区间）。
**Score 0.75**：大部分筛选正确，仅在数量或边界处理上有一处小错误。
**Score 0.5**：部分筛选正确，但若干产生了错误结果。
**Score 0.25**：多个章节存在重大筛选错误。
**Score 0.0**：未应用筛选或完全不正确。

### Criterion 2: Completeness (Weight: 25%)

**Score 1.0**：全部五个筛选章节齐备，并按要求给出完整结果，包括数量、列表和聚合。
**Score 0.75**：所有章节齐备，但缺少部分要求的细节（例如合计或平均值）。
**Score 0.5**：完全缺少某些章节。
**Score 0.25**：仅有一两个章节。
**Score 0.0**：报告缺失或为空。

### Criterion 3: Comparison Quality (Weight: 20%)

**Score 1.0**：Texas vs Florida 对比详尽，有清晰的并列数据，且 Agent 指出尽管 Florida 城市数量相当，Texas 的平均城市人口更高。
**Score 0.75**：对比良好，覆盖大部分指标但缺少一些洞察。
**Score 0.5**：基础对比，指标有限。
**Score 0.25**：肤浅的对比。
**Score 0.0**：未尝试对比。

### Criterion 4: Report Structure (Weight: 15%)

**Score 1.0**：每个筛选有清晰的章节标题，适当处使用表格，组织合理。
**Score 0.75**：组织良好，仅有小的格式问题。
**Score 0.5**：包含结果但组织混乱。
**Score 0.25**：难以理解或缺乏结构。
**Score 0.0**：无报告或无法使用。

---

## Additional Notes

本任务测试 Agent 的以下能力：

- 应用多种筛选条件（字符串匹配、数值阈值、地理坐标）
- 组合筛选（州 AND 人口、纬度 AND 人口）
- 对筛选后的子集进行聚合（计数、求和、平均）
- 并列对比两个分组
- 正确处理含端点的边界条件
- 处理地理数据（用纬度进行区域筛选）

数据集有 1000 座城市，列为：City、State、Population、lat、lon。不含密度或面积数据，因此所有筛选均基于可用列进行。
