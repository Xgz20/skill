---
id: task_csv_cities_ranking
name: 美国城市人口排名
category: CSV 数据分析
scene: 数据库检索、表格整理与数据分析
sub_scene: CSV 数据分析
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 代码生成与理解
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

请分析人口排名并将你的发现写入名为 `cities_ranking_report.md` 的文件。你的报告应包含：

- **人口前 10 的城市**，及其所属州和确切人口
- **数据集中人口最少的 10 座城市**（前 1000 中最小的）
- 全部 1000 座城市的**总人口**
- 人口的**平均值和中位数**
- 按其城市在数据集中的总人口排序的**人口前 10 的州**，包括每个州的城市数量
- **人口分布**：有多少座城市落入以下区间：<50k、50k-100k、100k-250k、250k-500k、500k-1M、>1M

---

## Expected Behavior

Agent 应当：

1. 读取并解析 CSV 文件（1000 行数据，5 列）
2. 按人口对城市排序以得出排名
3. 计算汇总统计量
4. 按州分组以得出州级排名
5. 创建人口分布区间
6. 撰写一份结构良好的 markdown 报告

预期关键值：

- 第 1 名城市：New York, New York —— 8,405,837
- 第 2 名：Los Angeles, California —— 3,884,307
- 第 3 名：Chicago, Illinois —— 2,718,782
- 第 4 名：Houston, Texas —— 2,195,914
- 第 5 名：Philadelphia, Pennsylvania —— 1,553,165
- 数据集中最小的城市：Panama City, Florida —— 36,877
- 总人口：131,132,443
- 平均人口：约 131,132
- 中位数人口：约 68,224
- 按总人口排名居首的州：California（212 座城市，27,910,620）
- 人口 > 1M 的城市：10 座
- 人口 >= 500k 的城市：34 座

---

## Grading Criteria

- [ ] 创建了报告文件 `cities_ranking_report.md`
- [ ] 正确识别了人口前 10 的城市，且 New York 为第 1 名
- [ ] 列出了人口最少的 10 座城市，且 Panama City, FL 为最小
- [ ] 正确报告了总人口（约 131,132,443）
- [ ] 正确计算了平均人口（约 131,132）
- [ ] 正确计算了中位数人口（约 68,224）
- [ ] 列出了按总人口排名的州，且 California 为第 1 名
- [ ] 包含人口分布区间
- [ ] 报告结构良好，章节清晰

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the US cities population ranking task.

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

    report_path = workspace / "cities_ranking_report.md"
    if not report_path.exists():
        for alt in ["ranking_report.md", "report.md", "cities_report.md", "population_ranking.md"]:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "top_10_cities": 0.0,
            "bottom_10_cities": 0.0,
            "total_population": 0.0,
            "mean_population": 0.0,
            "median_population": 0.0,
            "state_rankings": 0.0,
            "distribution_brackets": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Top 10 cities — check for the top 5 at minimum
    top_cities = ["new york", "los angeles", "chicago", "houston", "philadelphia"]
    found_top = sum(1 for c in top_cities if c in content_lower)
    scores["top_10_cities"] = 1.0 if found_top >= 5 else (0.5 if found_top >= 3 else 0.0)

    # Bottom 10 — check for Panama City as smallest
    scores["bottom_10_cities"] = 1.0 if "panama city" in content_lower else 0.0

    # Total population (~131,132,443)
    total_patterns = [r'131[,.]?132[,.]?443', r'131[,.]?132[,.]?4', r'131\.1\s*million']
    scores["total_population"] = 1.0 if any(re.search(p, content) for p in total_patterns) else 0.0

    # Mean population (~131,132)
    mean_patterns = [r'131[,.]?132(?!\d{3})', r'131[,.]?1\d{2}(?!\d{3})']
    scores["mean_population"] = 1.0 if any(re.search(p, content) for p in mean_patterns) else 0.0

    # Median population (~68,224)
    median_patterns = [r'68[,.]?2[12]\d', r'68[,.]?224', r'68[,.]?225', r'68[,.]?223']
    scores["median_population"] = 1.0 if any(re.search(p, content) for p in median_patterns) else 0.0

    # State rankings — California should be #1
    california_patterns = [
        r'california.*(?:1st|#1|first|top|highest|most)',
        r'(?:1st|#1|first|top|highest).*california',
        r'california.*212.*cit',
        r'california.*27[,.]?910',
    ]
    scores["state_rankings"] = 1.0 if any(re.search(p, content_lower) for p in california_patterns) else 0.0

    # Distribution brackets
    bracket_keywords = ["50k", "100k", "250k", "500k", "1m", "million",
                        "50,000", "100,000", "250,000", "500,000", "1,000,000",
                        "bracket", "distribution", "range", "bin"]
    bracket_count = sum(1 for k in bracket_keywords if k in content_lower)
    scores["distribution_brackets"] = 1.0 if bracket_count >= 3 else (0.5 if bracket_count >= 1 else 0.0)

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Data Accuracy (Weight: 35%)

**Score 1.0**：所有排名、合计、平均值、中位数和州级聚合在数值上都正确。
**Score 0.75**：大部分值正确，仅有一两处小的数值错误。
**Score 0.5**：部分值正确，但若干关键数字有误。
**Score 0.25**：多个指标存在重大计算错误。
**Score 0.0**：没有正确的计算，或未尝试分析。

### Criterion 2: Completeness (Weight: 30%)

**Score 1.0**：所有要求的要素都齐备：前 10、后 10、总计/平均/中位数、州级排名和分布区间。
**Score 0.75**：大部分要素齐备，仅有一处小遗漏。
**Score 0.5**：缺少若干要求的要素。
**Score 0.25**：仅有少数要素。
**Score 0.0**：报告缺失或几乎为空。

### Criterion 3: Report Quality (Weight: 20%)

**Score 1.0**：组织良好的 markdown，章节清晰，排名用表格，逻辑流畅。
**Score 0.75**：组织清晰、可读，仅有小的格式问题。
**Score 0.5**：包含分析但组织混乱。
**Score 0.25**：杂乱或难以理解。
**Score 0.0**：无报告或无法使用。

### Criterion 4: Insight Quality (Weight: 15%)

**Score 1.0**：超越原始数字，指出规律——例如 California 的主导地位、第 1 名与第 2 名之间的巨大差距、小城市的长尾。
**Score 0.75**：对数据中的规律有一些观察。
**Score 0.5**：大多是原始数字，几乎没有解读。
**Score 0.25**：纯数字，没有评述。
**Score 0.0**：未尝试分析。

---

## Additional Notes

本任务测试 Agent 的以下能力：

- 解析一个 1000 行的 CSV 文件
- 按数值列排序和排名
- 计算基本的描述性统计量（求和、平均、中位数）
- 按分类列（State）分组并聚合
- 创建有意义的人口分布区间
- 以清晰的报告格式呈现排名数据

数据集包含美国按人口排名的前 1000 座城市。最小的城市（Panama City, FL，36,877）仍代表相当规模的人口，因此所有区间分析都应考虑这一下限。

已知正确值：

- 1000 座城市，分布于 47 个州 + DC
- 最大城市：New York（8,405,837），第 2：Los Angeles（3,884,307）
- 最小：Panama City, FL（36,877）
- 总计：131,132,443 | 平均：约 131,132 | 中位数：约 68,224
- California 居首，212 座城市，总人口 27,910,620
- Texas 第 2，83 座城市，总人口 14,836,230
