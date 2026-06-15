---
id: task_csv_gdp_per_capita
name: 世界人均 GDP 估算
category: CSV 数据分析
scene: 数据库检索、表格整理与数据分析
sub_scene: CSV 数据分析
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 领域推理
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

该数据集包含 GDP 总量，但不包含人口数据。请运用你对 **GDP 排名前 30 的经济体**约 2014 年人口的了解，估算每个经济体的人均 GDP，并将你的发现写入 `gdp_per_capita_report.md`。你的报告应包含：

- **按 GDP 总量排序的前 30 大经济体**，列包括：排名、国家、GDP（十亿美元）、估算人口和估算人均 GDP
- **按人均 GDP 重新排名**：将这同样的 30 个国家按人均 GDP 从高到低重新排序
- **关键观察**：哪些大型经济体在人均水平上排名最高和最低，以及这揭示了生活水平与经济规模之间的什么关系
- **异常值与意外发现**：找出那些人均排名与 GDP 总量排名差异巨大的国家（例如，某个前 10 大经济体在人均上排名却低得多，或某个较小经济体在人均上排名却很高）
- 一段简短的**方法论说明**，解释由于 CSV 缺少人口数据，人口数字是根据常识估算的

---

## Expected Behavior

The agent should:

1. 读取并解析 CSV 文件
2. 按 GDP 排序以确定前 30 大经济体
3. 应用合理的 2014 年人口估算值（基于常识）
4. 计算每个经济体的人均 GDP（GDP 十亿美元 × 1,000,000,000 / 人口）
5. 按人均 GDP 重新排名
6. 找出关于经济规模与人均财富的关键洞察
7. 撰写一份结构良好且带有方法论说明的 markdown 报告

预期关键值（近似值，基于 2014 年人口）：

按 GDP 总量排名的前 30 大经济体从这些开始：US ($17,420B)、China ($10,360B)、Japan ($4,770B)、Germany ($3,820B)、France ($2,902B)

前 30 大经济体按人均排名大致应显示为：
- 前 30 中人均最高：Australia (~$62k)、Sweden (~$58k)、United States (~$55k)、Netherlands (~$52k)、Switzerland-excluded（不在 GDP 总量前 30 中）
- 前 30 中人均最低：India (~$1.6k)、Nigeria (~$3.4k)、Indonesia (~$3.5k)、Pakistan (~$1.3k，若在前 30 中)
- China 人均：~$7.5k，尽管 GDP 总量排名第 2
- India 人均：~$1.6k，尽管 GDP 总量排名第 10

---

## Grading Criteria

- [ ] 创建了报告文件 `gdp_per_capita_report.md`
- [ ] 按 GDP 总量列出前 30 大经济体及其 GDP 值
- [ ] 为每个国家提供了人口估算值
- [ ] 为每个国家计算了人均 GDP
- [ ] 包含按人均 GDP 的重新排名
- [ ] 关于规模与人均财富的关键观察
- [ ] 找出了异常值（例如 India/China 尽管 GDP 总量高但人均低）
- [ ] 关于估算人口的方法论说明

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the GDP per capita estimation task.

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

    report_path = workspace / "gdp_per_capita_report.md"
    if not report_path.exists():
        for alt in ["per_capita_report.md", "report.md", "gdp_per_capita.md", "per_capita.md", "analysis.md"]:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "top30_by_gdp": 0.0,
            "population_estimates": 0.0,
            "per_capita_calculated": 0.0,
            "per_capita_ranking": 0.0,
            "key_observations": 0.0,
            "outliers": 0.0,
            "methodology_note": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Check top 30 by GDP listed
    top_countries = ["united states", "china", "japan", "germany", "france",
                     "united kingdom", "brazil", "italy", "russia", "india"]
    found_top = sum(1 for c in top_countries if c in content_lower)
    scores["top30_by_gdp"] = 1.0 if found_top >= 8 else (0.5 if found_top >= 5 else 0.0)

    # Check population estimates present
    pop_patterns = [
        r'(?:population|pop\.?).*(?:million|billion|[0-9]{6,})',
        r'(?:318|319|320)\s*(?:million|m\b)',   # US ~318-320M
        r'(?:1[,.]?3[56]\d|1[,.]?36[0-9])\s*(?:million|billion|m\b|b\b)',  # China ~1.36B
        r'(?:1[,.]?2[567]\d)\s*(?:million|m\b|b\b)',  # India ~1.25B
    ]
    pop_found = sum(1 for p in pop_patterns if re.search(p, content_lower))
    scores["population_estimates"] = 1.0 if pop_found >= 2 else (0.5 if pop_found >= 1 else 0.0)

    # Check per capita values calculated
    per_capita_patterns = [
        r'per\s*capita',
        r'(?:54|55|56)[,.]?\d*\s*(?:k|thousand|,\d{3})',  # US per capita ~$55k
        r'(?:7[,.]?[345]\d{2}|7[,.]?5\d{2})',  # China per capita ~$7,500
        r'(?:1[,.]?[56]\d{2}|1[,.]?6\d{2})',  # India per capita ~$1,600
    ]
    pc_found = sum(1 for p in per_capita_patterns if re.search(p, content_lower + content))
    scores["per_capita_calculated"] = 1.0 if pc_found >= 3 else (0.5 if pc_found >= 1 else 0.0)

    # Check re-ranking by per capita
    rerank_patterns = [
        r'(?:rank|sort|order|re-?rank).*per\s*capita',
        r'per\s*capita.*(?:rank|sort|order)',
        r'(?:highest|top).*per\s*capita',
    ]
    scores["per_capita_ranking"] = 1.0 if any(re.search(p, content_lower) for p in rerank_patterns) else 0.0

    # Check key observations
    obs_patterns = [
        r'(?:living\s*standard|wealth|prosperity)',
        r'(?:economic\s*size|total\s*gdp).*(?:per\s*capita|per\s*person)',
        r'(?:large|big|populous).*(?:low|lower).*per\s*capita',
    ]
    obs_found = sum(1 for p in obs_patterns if re.search(p, content_lower))
    scores["key_observations"] = 1.0 if obs_found >= 2 else (0.5 if obs_found >= 1 else 0.0)

    # Check outliers identified (India, China as large GDP but low per capita)
    outlier_found = 0
    if re.search(r'(?:india|china).*(?:low|lower|bottom|despite|contrast)', content_lower):
        outlier_found += 1
    if re.search(r'(?:despite|although|while|but).*(?:per\s*capita|per\s*person)', content_lower):
        outlier_found += 1
    if re.search(r'(?:australia|sweden|netherlands).*(?:high|higher|top).*per\s*capita', content_lower):
        outlier_found += 1
    scores["outliers"] = 1.0 if outlier_found >= 2 else (0.5 if outlier_found >= 1 else 0.0)

    # Check methodology note
    method_patterns = [
        r'(?:methodolog|approach|note|caveat|limitation)',
        r'(?:estimat|approximat).*(?:population|pop)',
        r'(?:population).*(?:not\s*(?:in|available|included|provided)|missing|absent|lack)',
    ]
    method_found = sum(1 for p in method_patterns if re.search(p, content_lower))
    scores["methodology_note"] = 1.0 if method_found >= 2 else (0.5 if method_found >= 1 else 0.0)

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Population Estimates Quality (Weight: 30%)

**Score 1.0**：人口估算值对 2014 年而言是合理的（例如 US ~318M、China ~1.36B、India ~1.25B、Japan ~127M、Germany ~81M）。可接受小幅误差，但应在正确的数量级范围内。
**Score 0.75**：大多数估算值合理，仅有少数明显偏差。
**Score 0.5**：提供了估算值，但有若干明显错误（偏差 >20%）。
**Score 0.25**：许多估算值严重不准确。
**Score 0.0**：未提供人口估算值或完全捏造。

### Criterion 2: Per Capita Analysis Quality (Weight: 30%)

**Score 1.0**：给定人口估算值的情况下人均计算正确，重新排名做得正确，且分析正确地指出人口众多的发展中国家（India、China、Indonesia）人均排名要低得多，而较小的富裕国家排名更高。
**Score 0.75**：计算和重新排名大体正确，分析良好。
**Score 0.5**：计算了部分人均值，但重新排名不完整或分析肤浅。
**Score 0.25**：存在人均值但有重大计算错误。
**Score 0.0**：未尝试人均分析。

### Criterion 3: Insight Quality (Weight: 25%)

**Score 1.0**：清楚解释了 GDP 总量反映经济规模而人均反映个人富裕程度。识别出具体的意外发现（例如 India 按 GDP 排第 10 但人均接近垫底，Australia 是中等规模经济体但人均排名靠前）。讨论了人口在这种分化中的作用。
**Score 0.75**：洞察良好，仅有小的缺漏。
**Score 0.5**：基本观察，缺乏更深入的解读。
**Score 0.25**：观察肤浅或有误。
**Score 0.0**：未提供任何洞察。

### Criterion 4: Methodology and Presentation (Weight: 15%)

**Score 1.0**：方法论说明清晰，表格格式良好，对估算局限性诚实。承认人口数字是近似值。
**Score 0.75**：呈现良好，仅有小的格式问题或方法论说明简短。
**Score 0.5**：可读，但缺少方法论说明或表格格式较差。
**Score 0.25**：难以理解或方法论不清晰。
**Score 0.0**：无报告或无法阅读。

---

## Additional Notes

This task tests the agent's ability to:

- 解析 CSV 并识别出某个必需列（人口）缺失
- 应用外部知识（2014 年人口估算）来丰富数据集
- 从组合的数据来源计算派生指标（人均 GDP）
- 执行双重排名分析（按总量与按人均）
- 识别并解释两套排名系统之间的分化
- 清晰地传达方法论与局限性

这有意被设计为一个仅靠 CSV 不足以完成的任务——Agent 必须识别出缺失的数据，运用常识填补空缺，并对估算方法保持透明。评分对精确的人口数字较为宽容，但要求合理的数量级估算和正确的方法论。

预期关键人均值（近似值）：
- United States: ~$55,000
- China: ~$7,500
- Japan: ~$37,500
- Germany: ~$47,000
- India: ~$1,600
- Brazil: ~$11,000
- Australia: ~$62,000
