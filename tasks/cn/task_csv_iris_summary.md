---
id: task_csv_iris_summary
name: 鸢尾花统计汇总
category: CSV 数据分析
scene: 数据库检索、表格整理与数据分析
sub_scene: CSV 统计汇总
difficulty: L2
capabilities:
- 数据提取与处理
- 代码生成与理解
- 多步推理
- 输出格式适配
- 自然语言生成
grading_type: hybrid
timeout_seconds: 180
grading_weights:
  automated: 0.6
  llm_judge: 0.4
workspace_files:
  - source: csvs/iris_flowers.csv
    dest: iris_flowers.csv
---

## Prompt

我的工作区中有一个 CSV 文件 `iris_flowers.csv`，包含经典的鸢尾花数据集。它有 150 行和 5 列：`SepalLength`、`SepalWidth`、`PetalLength`、`PetalWidth` 和 `Name`（物种）。

请计算统计汇总并将其写入 `iris_summary.md`。你的报告应包含：

- **数据集概览**：总行数、列数，以及三个物种名称及其数量
- **整体统计**（针对每个数值列）：均值、中位数、标准差、最小值和最大值
- **各物种统计**：按物种分组的每个数值列的均值和标准差
- **相关性洞察**：哪一对数值特征具有最强的线性相关性，以及这意味着什么
- 一个简短的**关键发现**章节，突出数据中最值得注意的模式

---

## Expected Behavior

The agent should:

1. 读取并解析 CSV 文件
2. 确认 150 行，涵盖三个物种（Iris-setosa、Iris-versicolor、Iris-virginica），每个 50 个
3. 计算整体统计：
   - SepalLength：mean≈5.84，median=5.80，stdev≈0.83，min=4.3，max=7.9
   - SepalWidth：mean≈3.05，median=3.00，stdev≈0.43，min=2.0，max=4.4
   - PetalLength：mean≈3.76，median=4.35，stdev≈1.76，min=1.0，max=6.9
   - PetalWidth：mean≈1.20，median=1.30，stdev≈0.76，min=0.1，max=2.5
4. 计算各物种均值（例如 setosa PetalLength mean≈1.46，virginica PetalLength mean≈5.55）
5. 识别出 PetalLength 和 PetalWidth 具有最强相关性
6. 指出基于花瓣测量值 setosa 可清晰地与其他两个物种分离
7. 撰写一份结构良好的 markdown 报告

预期关键值：

- 150 行，3 个物种，每个 50 个
- 整体 SepalLength 均值：~5.84
- 整体 PetalLength 均值：~3.76
- Setosa PetalLength 均值：~1.46
- Virginica PetalLength 均值：~5.55
- 最强相关性：PetalLength–PetalWidth

---

## Grading Criteria

- [ ] 创建了报告文件 `iris_summary.md`
- [ ] 数据集概览：正确说明 150 行、3 个物种、每个 50 个
- [ ] 为每个数值列报告了整体均值、中位数、标准差、最小值、最大值
- [ ] 为每个数值列报告了各物种统计（至少均值）
- [ ] 识别出最强相关性（PetalLength–PetalWidth）
- [ ] 关键发现：基于花瓣测量值 setosa 可与 versicolor/virginica 分离
- [ ] 报告结构良好，带有 markdown 格式

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the Iris statistical summary task.

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
    report_path = workspace / "iris_summary.md"
    if not report_path.exists():
        alternatives = ["summary.md", "report.md", "iris_report.md", "iris_statistics.md", "iris_analysis.md"]
        for alt in alternatives:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "dataset_overview": 0.0,
            "overall_stats": 0.0,
            "per_species_stats": 0.0,
            "correlation": 0.0,
            "separability_insight": 0.0,
            "formatting": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Check dataset overview (150 rows, 3 species, 50 each)
    has_150 = bool(re.search(r'150', content))
    has_3_species = bool(re.search(r'(?:three|3)\s*(?:species|class)', content_lower))
    has_50_each = bool(re.search(r'50\s*(?:each|samples|rows|per|observations)', content_lower))
    species_names = sum(1 for s in ['setosa', 'versicolor', 'virginica'] if s in content_lower)
    overview_score = 0.0
    if has_150:
        overview_score += 0.25
    if has_3_species or species_names >= 3:
        overview_score += 0.25
    if has_50_each:
        overview_score += 0.25
    if species_names >= 3:
        overview_score += 0.25
    scores["dataset_overview"] = overview_score

    # Check overall statistics (means for key columns)
    stats_score = 0.0
    if re.search(r'5\.8[0-9]', content):  # SepalLength mean ~5.84
        stats_score += 0.25
    if re.search(r'3\.0[0-9]', content):  # SepalWidth mean ~3.05
        stats_score += 0.25
    if re.search(r'3\.7[56]', content):  # PetalLength mean ~3.76
        stats_score += 0.25
    if re.search(r'1\.1[89]|1\.20', content):  # PetalWidth mean ~1.20
        stats_score += 0.25
    scores["overall_stats"] = stats_score

    # Check per-species statistics
    species_score = 0.0
    # Setosa PetalLength mean ~1.46
    if re.search(r'1\.46', content):
        species_score += 0.34
    # Versicolor PetalLength mean ~4.26
    if re.search(r'4\.26', content):
        species_score += 0.33
    # Virginica PetalLength mean ~5.55
    if re.search(r'5\.5[45]', content):
        species_score += 0.33
    scores["per_species_stats"] = min(species_score, 1.0)

    # Check correlation identification
    corr_patterns = [
        r'petal\s*length.*petal\s*width.*corr',
        r'corr.*petal\s*length.*petal\s*width',
        r'petal\s*width.*petal\s*length.*corr',
        r'strongest.*corr.*petal',
        r'high(?:est|ly)?\s*corr.*petal',
        r'petal.*strong.*corr',
    ]
    scores["correlation"] = 1.0 if any(re.search(p, content_lower) for p in corr_patterns) else 0.0

    # Check separability insight
    sep_patterns = [
        r'setosa.*(?:separab|distinct|clearly\s*different|easily\s*distinguish|linearly\s*separab)',
        r'(?:separab|distinct|clearly\s*different|easily\s*distinguish).*setosa',
        r'setosa.*(?:smaller|shorter)\s*petal',
        r'petal.*(?:separate|distinguish|differentiate).*setosa',
    ]
    scores["separability_insight"] = 1.0 if any(re.search(p, content_lower) for p in sep_patterns) else 0.0

    # Check formatting (headers, tables or structured data)
    has_headers = len(re.findall(r'^#{1,3}\s+', content, re.MULTILINE)) >= 3
    has_table = bool(re.search(r'\|.*\|.*\|', content))
    has_lists = len(re.findall(r'^[\s]*[-*]\s+', content, re.MULTILINE)) >= 3
    fmt_score = 0.0
    if has_headers:
        fmt_score += 0.5
    if has_table or has_lists:
        fmt_score += 0.5
    scores["formatting"] = fmt_score

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Statistical Accuracy (Weight: 35%)

**Score 1.0**：所有统计数据（均值、中位数、标准差、最小/最大值）在整体和各物种细分上均数值正确。
**Score 0.75**：大多数统计数据正确，仅有一两处小的取整差异。
**Score 0.5**：部分统计数据正确，但若干关键值错误或缺失。
**Score 0.25**：少数统计数据正确；存在重大计算错误。
**Score 0.0**：无正确统计数据或未尝试分析。

### Criterion 2: Analytical Insight (Weight: 30%)

**Score 1.0**：正确识别出 PetalLength–PetalWidth 相关性最强，指出 setosa 可分离，并对数据模式提供有意义的解读。
**Score 0.75**：识别出关键相关性和物种差异，并有合理的细节。
**Score 0.5**：提及相关性或物种差异，但分析肤浅或部分不正确。
**Score 0.25**：分析洞察含糊或不正确。
**Score 0.0**：未提供洞察或分析完全不正确。

### Criterion 3: Report Structure and Presentation (Weight: 20%)

**Score 1.0**：组织良好的 markdown，章节清晰，统计数据使用表格，从概览到详细分析再到关键发现逻辑流畅。
**Score 0.75**：组织有序且可读，仅有小的格式问题。
**Score 0.5**：包含分析但组织较差或难以理解。
**Score 0.25**：组织混乱或缺少主要章节。
**Score 0.0**：未创建报告或为空/无法使用。

### Criterion 4: Completeness (Weight: 15%)

**Score 1.0**：所有所需元素齐全：概览、整体统计、各物种统计、相关性和关键发现。
**Score 0.75**：大多数元素齐全，仅有一两处小遗漏。
**Score 0.5**：缺少若干所需元素。
**Score 0.25**：仅有少数元素。
**Score 0.0**：报告缺失或几乎为空。

---

## Additional Notes

This task tests the agent's ability to:

- 解析包含数值列和分类列混合的 CSV
- 计算描述性统计（均值、中位数、标准差、最小值、最大值）
- 按分类变量分组并计算分组层级的统计
- 识别特征之间的相关性
- 将发现综合为关于数据的有意义洞察

鸢尾花数据集是统计学和机器学习中最知名的数据集之一。关键模式：setosa 的花瓣比其他两个物种小得多，PetalLength 和 PetalWidth 高度相关（~0.96），versicolor 和 virginica 在特征空间中重叠而 setosa 是线性可分的。
