---
id: task_csv_gdp_regions
name: 世界 GDP 区域分析
category: CSV 数据分析
scene: 数据库检索、表格整理与数据分析
sub_scene: CSV 数据分析
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 指令遵循与约束理解
- 自然语言生成
- 输出格式适配
grading_type: hybrid
timeout_seconds: 180
grading_weights:
  automated: 0.6
  llm_judge: 0.4
workspace_files:
  - source: csvs/world_gdp_2014.csv
    dest: world_gdp_2014.csv
---

## Prompt

我的工作区中有一个 CSV 文件 `world_gdp_2014.csv`，包含全球各国和地区的 GDP 数据。文件有三列：`COUNTRY`、`GDP (BILLIONS)`（以美元计）和 `CODE`（ISO 国家代码）。共有 222 条记录。

该数据集不包含区域列。请运用你的世界地理知识，将每个国家归入以下区域之一：**North America**（北美）、**Europe**（欧洲）、**East Asia & Pacific**（东亚与太平洋）、**South Asia**（南亚）、**Latin America & Caribbean**（拉丁美洲与加勒比）、**Middle East & North Africa**（中东与北非）、**Sub-Saharan Africa**（撒哈拉以南非洲）和 **Central Asia & Caucasus**（中亚与高加索）。然后将区域分析写入 `gdp_regions_report.md`。你的报告应包含：

- **各区域 GDP 总量**，包含每个区域的合计 GDP、国家数量及占世界 GDP 的百分比份额，按总量降序排列
- **每个区域的前 3 大经济体**（国家名称和 GDP）
- **区域比较**：哪 3 个区域主导全球经济，它们的合计份额是多少
- **各区域人均每国 GDP**：哪个区域的平均每国 GDP 最高和最低，这说明了什么
- **差距分析**：针对每个区域，计算最大和最小经济体之间的比率——哪个区域内部差距最大
- 一段简短的**总结段落**，论述全球经济产出的地理分布

注意：某些国家可能存在归属模糊的情况（例如 Russia、Turkey）。将它们归入你认为最合适的区域，并标注任何边界情况。

---

## Expected Behavior

The agent should:

1. 读取并解析 CSV 文件（222 条记录）
2. 运用地理知识将每个国家归入某个区域
3. 按区域聚合 GDP
4. 计算百分比份额和平均值
5. 识别每个区域的顶级经济体
6. 分析区域内部差距
7. 撰写一份结构良好的 markdown 报告

预期关键值（近似值，取决于区域归属）：

- East Asia & Pacific：~$21,000–27,000B（最大区域，由 China 和 Japan 拉动）
- North America：~$20,500B（3 个国家：US、Canada、Mexico）
- Europe：~$18,000–22,000B（取决于 Russia/Turkey 的归属，30–40 个国家）
- South Asia：~$2,500B（7 个国家，由 India 主导）
- Latin America & Caribbean：~$4,500B（20+ 个国家，由 Brazil 领衔）
- Middle East & North Africa：~$3,000–4,000B（由 Saudi Arabia 领衔）
- Sub-Saharan Africa：~$1,700B（40+ 个国家，由 Nigeria 领衔）
- Central Asia & Caucasus：~$400–500B（8 个国家，由 Kazakhstan 领衔）

前 3 个区域合计应占世界 GDP 的 ~75-80%。
North America 拥有最高的平均每国 GDP（仅 3 个国家，~$6,800B/国）。
Sub-Saharan Africa 平均值最低（~$35B/国，尽管记录数最多）。

---

## Grading Criteria

- [ ] 创建了报告文件 `gdp_regions_report.md`
- [ ] 计算了各区域 GDP 总量及百分比份额
- [ ] 列出了每个区域的前 3 大经济体
- [ ] 识别了三个主导区域及其合计份额
- [ ] 分析了各区域的平均每国 GDP
- [ ] 计算了各区域的内部差距比率
- [ ] 标注了边界情况（Russia、Turkey 等）
- [ ] 关于地理分布的总结段落

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the GDP regional analysis task.

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

    report_path = workspace / "gdp_regions_report.md"
    if not report_path.exists():
        for alt in ["regions_report.md", "report.md", "gdp_regions.md", "regional_report.md", "regional_analysis.md", "analysis.md"]:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "regional_totals": 0.0,
            "top_per_region": 0.0,
            "dominant_regions": 0.0,
            "avg_per_country": 0.0,
            "disparity": 0.0,
            "borderline_cases": 0.0,
            "summary_paragraph": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Check regional totals present
    regions_found = 0
    region_names = [
        r'north\s*america', r'europe', r'east\s*asia', r'south\s*asia',
        r'latin\s*america', r'middle\s*east', r'sub[- ]saharan', r'central\s*asia'
    ]
    for rn in region_names:
        if re.search(rn, content_lower):
            regions_found += 1
    has_pct = bool(re.search(r'\d+\.?\d*\s*%', content))
    scores["regional_totals"] = 1.0 if (regions_found >= 7 and has_pct) else (0.5 if regions_found >= 4 else 0.0)

    # Check top economies per region
    top_econ_patterns = [
        r'united\s*states',  # North America
        r'germany',          # Europe
        r'china',            # East Asia
        r'india',            # South Asia
        r'brazil',           # Latin America
        r'saudi\s*arabia',   # MENA
        r'nigeria',          # SSA
        r'kazakhstan',       # Central Asia
    ]
    top_found = sum(1 for p in top_econ_patterns if re.search(p, content_lower))
    scores["top_per_region"] = 1.0 if top_found >= 7 else (0.5 if top_found >= 4 else 0.0)

    # Check dominant regions identified
    dominant_patterns = [
        r'(?:dominat|largest|top\s*(?:3|three)).*(?:region|area)',
        r'(?:north\s*america|europe|east\s*asia).*(?:combin|together|account)',
        r'(?:7[5-9]|80)\s*[\.\d]*%.*(?:combin|together|three|3)',
    ]
    dom_found = sum(1 for p in dominant_patterns if re.search(p, content_lower))
    scores["dominant_regions"] = 1.0 if dom_found >= 1 else 0.0

    # Check average GDP per country analysis
    avg_patterns = [
        r'(?:average|mean)\s*(?:gdp)?\s*(?:per\s*country|per\s*economy)',
        r'north\s*america.*(?:highest|largest).*(?:average|mean)',
        r'(?:africa|sub[- ]saharan).*(?:lowest|smallest).*(?:average|mean)',
    ]
    avg_found = sum(1 for p in avg_patterns if re.search(p, content_lower))
    scores["avg_per_country"] = 1.0 if avg_found >= 2 else (0.5 if avg_found >= 1 else 0.0)

    # Check disparity analysis
    disp_patterns = [
        r'(?:dispar|ratio|inequal|gap|range)',
        r'(?:largest|biggest).*(?:smallest|lowest)',
        r'(?:ratio|factor|times)',
    ]
    disp_found = sum(1 for p in disp_patterns if re.search(p, content_lower))
    scores["disparity"] = 1.0 if disp_found >= 2 else (0.5 if disp_found >= 1 else 0.0)

    # Check borderline cases mentioned
    border_patterns = [
        r'(?:russia|turkey).*(?:border|ambiguous|classify|assign|debat|could)',
        r'(?:border|ambiguous|transcontinental).*(?:russia|turkey)',
        r'(?:classif|assign|categori).*(?:challeng|difficult|judgment|borderline)',
    ]
    scores["borderline_cases"] = 1.0 if any(re.search(p, content_lower) for p in border_patterns) else 0.0

    # Check summary paragraph
    summary_patterns = [
        r'(?:concentrat|cluster|dominat).*(?:global|world)',
        r'(?:global|world).*(?:output|gdp).*(?:concentrat|dominat|cluster)',
        r'(?:africa|developing|south).*(?:small|fraction|marginal)',
    ]
    summary_found = sum(1 for p in summary_patterns if re.search(p, content_lower))
    scores["summary_paragraph"] = 1.0 if summary_found >= 1 else 0.0

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Regional Classification Accuracy (Weight: 25%)

**Score 1.0**：各国被归入合理的区域。8 个区域覆盖了全部或几乎全部 222 条记录。边界情况（Russia、Turkey、Cyprus）被承认并加以论证。小型地区得到合理处理。
**Score 0.75**：大多数归属正确，仅有少数错置并对边界情况有所承认。
**Score 0.5**：总体正确，但遗漏了重要国家或将若干国家归入错误区域。
**Score 0.25**：许多错误归属或覆盖存在大缺口。
**Score 0.0**：未尝试分类或根本性错误。

### Criterion 2: Quantitative Analysis (Weight: 30%)

**Score 1.0**：区域总量、百分比、平均值和差距比率均计算正确。数字内部一致（百分比合计 ~100%，总量与世界 GDP 吻合）。
**Score 0.75**：大多数计算正确，仅有小的偏差。
**Score 0.5**：部分计算正确，但有明显错误或缺失指标。
**Score 0.25**：重大计算错误。
**Score 0.0**：未尝试计算。

### Criterion 3: Analytical Depth (Weight: 25%)

**Score 1.0**：对全球 GDP 分布提供了有意义的洞察——为什么 North America 在平均值上领先（仅 3 个大型经济体），为什么 Sub-Saharan Africa 平均值低（许多小型经济体），East Asia 的总量如何由 China/Japan 拉动，以及差距比率揭示了区域经济结构的什么特征。
**Score 0.75**：洞察良好，仅有小的缺漏。
**Score 0.5**：基本观察，缺乏更深入的解读。
**Score 0.25**：分析肤浅。
**Score 0.0**：未提供任何分析。

### Criterion 4: Completeness and Presentation (Weight: 20%)

**Score 1.0**：所有所需章节齐全，表格或列表格式良好，标题清晰，逻辑流畅。每个区域前 3、平均值、差距、主导区域和总结全部包含。
**Score 0.75**：大多数章节齐全且格式良好。
**Score 0.5**：缺少若干章节或格式较差。
**Score 0.25**：内容极少。
**Score 0.0**：报告缺失或为空。

---

## Additional Notes

This task tests the agent's ability to:

- 解析没有显式分类标签的 CSV 文件
- 应用外部地理知识对数据分类
- 处理模糊的分类（例如 Russia 横跨欧洲和亚洲，Turkey 是跨大陆国家）
- 在自定义的分类变量上执行分组聚合
- 计算并解读每个分组的多个派生指标
- 以清晰的格式呈现复杂的多分组分析

该数据集包含 222 条记录，包括主权国家、地区和属地。某些记录（例如 Puerto Rico、Hong Kong、Macau）可能被归入其主权国家所在区域或单独处理。Sint Maarten 的 GDP $304.1B 显得异常。

Agent 应识别出 North America 拥有最高的平均每国 GDP（因为仅有 3 个大型经济体），而 Sub-Saharan Africa 记录数最多但合计和平均 GDP 最低。East Asia & Pacific 通常因 China 和 Japan 而成为按总量计算的最大区域。
