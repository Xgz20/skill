---
id: task_csv_iris_outliers
name: 鸢尾花异常值检测
category: CSV 数据分析
scene: 数据库检索、表格整理与数据分析
sub_scene: CSV 异常值检测
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 领域推理
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

我的工作区中有一个 CSV 文件 `iris_flowers.csv`，包含经典的鸢尾花数据集，共 150 个样本。列：`SepalLength`、`SepalWidth`、`PetalLength`、`PetalWidth` 和 `Name`（物种：Iris-setosa、Iris-versicolor、Iris-virginica）。

请分析数据集中的异常值和异常观测，然后将你的发现写入 `iris_outliers.md`。你的报告应包含：

- **异常值检测方法**：解释所用的统计方法（例如 IQR、z-score，或两者）
- **整体异常值**：在完整数据集上对每个数值列检测到的异常值，附具体数值和行标识
- **物种内异常值**：在每个物种分组内检测到的异常值（某个值在整体上可能正常，但对其物种而言却很极端）
- **异常观测**：在同时考虑多个特征时对其物种而言非典型的样本（例如花瓣异常小的 virginica）
- **总结**：发现了多少异常值，哪些特征和物种受影响最大，以及是否有样本可能被错误标注

---

## Expected Behavior

The agent should:

1. 读取并解析 CSV 文件
2. 在每个数值列上应用基于 IQR 或基于 z-score 的异常值检测
3. 找出整体数据集中的 SepalWidth 异常值：
   - 第 16 行：Iris-setosa，SepalWidth=4.4（高于上界）
   - 第 33 行：Iris-setosa，SepalWidth=4.1（高于上界）
   - 第 34 行：Iris-setosa，SepalWidth=4.2（高于上界）
   - 第 61 行：Iris-versicolor，SepalWidth=2.0（低于下界）
4. 执行物种内分析以找出对其分组而言极端的观测
5. 标注异常的多特征观测，例如：
   - 第 42 行：Iris-setosa，SepalWidth=2.3（setosa 中最低，远离 setosa 均值 3.42）
   - 第 107 行：Iris-virginica，SepalLength=4.9，最小的 virginica（均值 6.59）
6. 讨论是否有异常值可能表明标注错误
7. 撰写一份结构良好的 markdown 报告

预期关键值：

- SepalWidth IQR 异常值：第 16、33、34 行（高），第 61 行（低）
- SepalWidth Q1=2.8、Q3=3.3、IQR=0.5、上下界：[2.05, 4.05]
- 在完整数据集上使用 IQR，SepalLength、PetalLength 或 PetalWidth 中无异常值
- 物种内分析揭示了整体数据中不可见的额外异常值

---

## Grading Criteria

- [ ] 创建了报告文件 `iris_outliers.md`
- [ ] 清晰解释了异常值检测方法（IQR、z-score 或类似方法）
- [ ] 将 SepalWidth 识别为整体异常值最多的列
- [ ] 报告了具体的异常值和行号（4 个 SepalWidth 异常值中至少 2 个）
- [ ] 执行了物种内异常值分析
- [ ] 讨论了异常的多特征观测（例如对其物种而言非典型的样本）
- [ ] 带有异常值计数和受影响特征/物种的总结

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the Iris outlier detection task.

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
    report_path = workspace / "iris_outliers.md"
    if not report_path.exists():
        alternatives = ["outliers.md", "report.md", "iris_report.md", "outlier_analysis.md", "iris_outlier_report.md"]
        for alt in alternatives:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "method_explained": 0.0,
            "sepalwidth_outliers": 0.0,
            "specific_values": 0.0,
            "within_species": 0.0,
            "unusual_observations": 0.0,
            "summary": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Check method explanation
    method_patterns = [
        r'iqr|inter\s*-?\s*quartile\s*range',
        r'z\s*-?\s*score',
        r'(?:1\.5|1\.5\s*[*×x]\s*iqr)',
        r'(?:standard\s*deviation|sigma).*(?:outlier|threshold)',
        r'(?:upper|lower)\s*(?:fence|bound|whisker)',
    ]
    method_count = sum(1 for p in method_patterns if re.search(p, content_lower))
    scores["method_explained"] = 1.0 if method_count >= 2 else (0.5 if method_count >= 1 else 0.0)

    # Check SepalWidth identified as having outliers
    sw_patterns = [
        r'sepal\s*width.*outlier',
        r'outlier.*sepal\s*width',
        r'sepalwidth.*outlier',
        r'outlier.*sepalwidth',
    ]
    scores["sepalwidth_outliers"] = 1.0 if any(re.search(p, content_lower) for p in sw_patterns) else 0.0

    # Check specific outlier values reported
    specific_score = 0.0
    # SepalWidth = 4.4 (row 16, setosa)
    if re.search(r'4\.4', content) and re.search(r'sepal\s*width|sepalwidth', content_lower):
        specific_score += 0.25
    # SepalWidth = 4.1 or 4.2 (rows 33, 34)
    if re.search(r'4\.[12]', content):
        specific_score += 0.25
    # SepalWidth = 2.0 (row 61, versicolor)
    if re.search(r'(?:sepal\s*width|sepalwidth).*2\.0|2\.0.*(?:sepal\s*width|sepalwidth)', content_lower):
        specific_score += 0.25
    # Any row numbers mentioned
    if re.search(r'(?:row|sample|observation|index)\s*(?:#?\s*)?(?:16|33|34|42|61|107)', content_lower):
        specific_score += 0.25
    scores["specific_values"] = min(specific_score, 1.0)

    # Check within-species analysis
    within_patterns = [
        r'within[- ]species.*outlier',
        r'(?:per|each|by)[- ]species.*outlier',
        r'outlier.*(?:within|per|each|by)[- ](?:species|group|class)',
        r'(?:setosa|versicolor|virginica).*(?:outlier|extreme|unusual).*(?:within|for\s+(?:its|the)\s+species)',
        r'(?:group|species|class)[- ](?:level|specific|wise).*outlier',
    ]
    scores["within_species"] = 1.0 if any(re.search(p, content_lower) for p in within_patterns) else 0.0

    # Check unusual multi-feature observations
    unusual_patterns = [
        r'(?:unusual|atypical|anomal).*(?:observ|sample|row|specimen)',
        r'(?:row|sample)\s*(?:#?\s*)?(?:42|107).*(?:unusual|atypical|extreme|outlier)',
        r'(?:virginica|setosa).*(?:small|low|unusual|atypical)',
        r'sepal\s*width\s*(?:=|of|:)?\s*2\.3.*setosa',
        r'(?:mislabel|misclassif|wrong\s*(?:label|species))',
    ]
    unusual_count = sum(1 for p in unusual_patterns if re.search(p, content_lower))
    scores["unusual_observations"] = 1.0 if unusual_count >= 2 else (0.5 if unusual_count >= 1 else 0.0)

    # Check summary
    summary_patterns = [
        r'(?:total|found)\s*\d+\s*outlier',
        r'\d+\s*outlier.*(?:found|detected|identified)',
        r'(?:summary|conclusion|overall)',
        r'(?:most|primarily).*(?:sepal\s*width|affected)',
    ]
    summary_count = sum(1 for p in summary_patterns if re.search(p, content_lower))
    scores["summary"] = 1.0 if summary_count >= 2 else (0.5 if summary_count >= 1 else 0.0)

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Outlier Detection Quality (Weight: 35%)

**Score 1.0**：使用定义明确的统计方法（IQR 或 z-score），正确识别出所有 SepalWidth 异常值并附具体数值，并指出在整体 IQR 方法下其他列没有异常值。
**Score 0.75**：使用有效方法，正确识别出大多数异常值并附具体数值。
**Score 0.5**：识别出部分异常值但遗漏了关键的，或方法应用不当。
**Score 0.25**：尝试了异常值检测但结果大多不正确或不完整。
**Score 0.0**：未执行异常值检测或完全错误。

### Criterion 2: Within-Species and Multi-Feature Analysis (Weight: 30%)

**Score 1.0**：执行了物种内异常值检测，识别出对其物种而言极端但整体上不极端的样本（例如 SepalWidth=2.3 的 setosa、SepalLength=4.9 的 virginica），并讨论了多特征异常模式。
**Score 0.75**：物种内分析良好，有一些多特征讨论。
**Score 0.5**：基本的物种内分析，但多特征洞察有限。
**Score 0.25**：物种内分析极少。
**Score 0.0**：未执行物种内分析。

### Criterion 3: Interpretation and Context (Weight: 20%)

**Score 1.0**：讨论了异常值的生物学合理性、它们是否可能表明测量误差或标注错误，解释了为什么某些物种受影响更大，并提供了可操作的结论。
**Score 0.75**：良好的解读，对异常值的含义有一些背景说明。
**Score 0.5**：基本解读，缺乏深度。
**Score 0.25**：解读极少；只是列出数字而无背景说明。
**Score 0.0**：未对发现进行解读。

### Criterion 4: Report Completeness and Clarity (Weight: 15%)

**Score 1.0**：所有所需章节齐全（方法、整体异常值、物种内、异常观测、总结），格式良好，带有表格或结构化列表，清晰易懂。
**Score 0.75**：大多数章节齐全且格式良好。
**Score 0.5**：缺少部分章节或组织较差。
**Score 0.25**：缺少主要章节或难以理解。
**Score 0.0**：无报告或为空/无法使用。

---

## Additional Notes

This task tests the agent's ability to:

- 应用统计异常值检测方法（IQR、z-score）
- 在多个层级执行分析（整体与组内）
- 考虑多变量异常值（特征的异常组合）
- 在背景中解读统计发现
- 以易于理解的格式呈现技术发现

鸢尾花数据集在整体分析时极端异常值相对较少，但物种内分析揭示了更细致的发现。关键挑战是超越简单的逐列 IQR，去考虑物种层级的分析和多特征模式。SepalWidth 是整体数据集中唯一有 IQR 异常值的列（4 个异常值：三个高的 setosa 值和一个低的 versicolor 值）。
