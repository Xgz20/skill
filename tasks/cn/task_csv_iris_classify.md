---
id: task_csv_iris_classify
name: 鸢尾花物种分类规则
category: CSV 数据分析
scene: 数据库检索、表格整理与数据分析
sub_scene: CSV 数据分析
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 代码生成与理解
- 输出格式适配
- 指令遵循与约束理解
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

我的工作区中有一个 CSV 文件 `iris_flowers.csv`，包含经典的鸢尾花数据集，共 150 个样本。列包括：`SepalLength`、`SepalWidth`、`PetalLength`、`PetalWidth` 和 `Name`（物种：Iris-setosa、Iris-versicolor、Iris-virginica）。

请分析数据并开发一套能够根据测量值预测物种的简单分类规则。将结果写入 `iris_classification.md`。你的报告应包含：

- **特征分析**：哪些特征对区分物种最有用，并提供支持性的统计数据或取值范围
- **分类规则**：一套清晰的决策树式或基于阈值的规则集（例如 "if PetalLength < X then species is Y"）
- **准确率评估**：将你的规则应用于完整数据集，报告每条规则正确分类了多少样本，以及整体准确率
- **误分类分析**：列出哪些样本（如有）被你的规则误分类，以及为什么它们是困难案例
- 一个**混淆矩阵**或显示预测物种与实际物种对比的等效汇总

---

## Expected Behavior

The agent should:

1. 读取并解析 CSV 文件
2. 发现 PetalLength 和 PetalWidth 是最具区分度的特征
3. 发现 setosa 可被完美分离（PetalLength < 2.5 可捕获全部 50 个 setosa 且不包含其他物种）
4. 开发区分 versicolor 与 virginica 的规则（例如 PetalLength < 4.9 或 PetalWidth < 1.7）
5. 达到高准确率（>= 90%，理想为 95%+）
6. 识别出 versicolor/virginica 边界是大多数错误发生的地方
7. 报告混淆矩阵或各物种准确率
8. 撰写一份结构良好的 markdown 报告

预期关键值：

- PetalLength < 2.5 → Iris-setosa（100% 准确，全部 50 个正确）
- versicolor/virginica 边界约在 PetalLength ~4.8–5.0 或 PetalWidth ~1.6–1.8
- 可达成的整体准确率：使用简单阈值规则为 94–97%
- 大多数误分类发生在 versicolor 和 virginica 之间

---

## Grading Criteria

- [ ] 创建了报告文件 `iris_classification.md`
- [ ] 将 PetalLength（或 PetalWidth）识别为最具区分度的特征
- [ ] 正确识别出 setosa 可用简单阈值完美分离
- [ ] 明确陈述了带有数值阈值的分类规则
- [ ] 准确率评估：将规则应用于完整数据集并报告整体准确率
- [ ] 准确率 >= 90%
- [ ] 讨论或列出了被误分类的样本
- [ ] 包含混淆矩阵或各物种准确率细分

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the Iris classification rules task.

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
    report_path = workspace / "iris_classification.md"
    if not report_path.exists():
        alternatives = ["classification.md", "report.md", "iris_rules.md", "iris_report.md", "classification_rules.md"]
        for alt in alternatives:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "discriminating_feature": 0.0,
            "setosa_separable": 0.0,
            "explicit_rules": 0.0,
            "accuracy_reported": 0.0,
            "high_accuracy": 0.0,
            "misclassification_analysis": 0.0,
            "confusion_matrix": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Check discriminating feature identification
    petal_patterns = [
        r'petal\s*length.*(?:most|best|key|primary|strongest|discriminat|import)',
        r'(?:most|best|key|primary|strongest|discriminat|import).*petal\s*length',
        r'petal\s*width.*(?:most|best|key|primary|strongest|discriminat|import)',
        r'(?:most|best|key|primary|strongest|discriminat|import).*petal\s*width',
        r'petal.*(?:useful|effective|powerful|informative).*(?:feature|variable|predictor)',
    ]
    scores["discriminating_feature"] = 1.0 if any(re.search(p, content_lower) for p in petal_patterns) else 0.0

    # Check setosa separability
    setosa_patterns = [
        r'setosa.*(?:perfect|100|complete|linear).*(?:separ|classif|distinguish)',
        r'(?:perfect|100|complete|linear).*(?:separ|classif|distinguish).*setosa',
        r'petal\s*length\s*[<≤]\s*2\.[0-5].*setosa',
        r'setosa.*petal\s*length\s*[<≤]\s*2\.[0-5]',
        r'petal\s*width\s*[<≤]\s*0\.[5-8].*setosa',
    ]
    scores["setosa_separable"] = 1.0 if any(re.search(p, content_lower) for p in setosa_patterns) else 0.0

    # Check explicit rules with thresholds
    threshold_patterns = [
        r'(?:if|when|where)\s+.*(?:petal|sepal)\s*(?:length|width)\s*[<>≤≥]=?\s*\d+\.?\d*',
        r'(?:petal|sepal)\s*(?:length|width)\s*[<>≤≥]=?\s*\d+\.?\d*\s*(?:→|->|then|:)',
        r'threshold.*\d+\.?\d*',
    ]
    rule_count = sum(1 for p in threshold_patterns if re.search(p, content_lower))
    scores["explicit_rules"] = 1.0 if rule_count >= 2 else (0.5 if rule_count >= 1 else 0.0)

    # Check accuracy reported
    accuracy_patterns = [
        r'(?:accuracy|correct)\s*(?::|=|of|is)?\s*\d{2,3}[.%]',
        r'\d{2,3}\.?\d*\s*%\s*(?:accuracy|correct)',
        r'(?:9[0-9]|100)\s*(?:out of|/)\s*150',
        r'(?:accuracy|correct).*(?:9[0-9]|100)%',
    ]
    scores["accuracy_reported"] = 1.0 if any(re.search(p, content_lower) for p in accuracy_patterns) else 0.0

    # Check high accuracy (>= 90%)
    acc_values = re.findall(r'(\d{2,3}\.?\d*)\s*%', content)
    high_acc = False
    for val in acc_values:
        try:
            if 90 <= float(val) <= 100:
                high_acc = True
                break
        except ValueError:
            pass
    # Also check fraction form
    frac_match = re.search(r'(\d{2,3})\s*/\s*150', content)
    if frac_match:
        try:
            if int(frac_match.group(1)) >= 135:
                high_acc = True
        except ValueError:
            pass
    scores["high_accuracy"] = 1.0 if high_acc else 0.0

    # Check misclassification analysis
    misclass_patterns = [
        r'mis(?:classif|label)',
        r'(?:incorrect|wrong|error).*(?:classif|predict)',
        r'(?:classif|predict).*(?:incorrect|wrong|error)',
        r'versicolor.*virginica.*(?:overlap|confus|difficult|hard)',
        r'(?:overlap|confus|difficult|hard).*versicolor.*virginica',
    ]
    scores["misclassification_analysis"] = 1.0 if any(re.search(p, content_lower) for p in misclass_patterns) else 0.0

    # Check confusion matrix
    confusion_patterns = [
        r'confusion\s*matrix',
        r'\|\s*(?:setosa|versicolor|virginica)\s*\|.*\d+.*\|',
        r'(?:predicted|actual).*(?:setosa|versicolor|virginica)',
        r'(?:true|false)\s*(?:positive|negative)',
        r'(?:tp|fp|fn|tn)\b',
        r'per[- ]?species.*(?:accuracy|precision|recall)',
    ]
    scores["confusion_matrix"] = 1.0 if any(re.search(p, content_lower) for p in confusion_patterns) else 0.0

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Classification Rule Quality (Weight: 35%)

**Score 1.0**：规则清晰陈述并带有具体数值阈值，正确地完美分离 setosa，并在 versicolor/virginica 上达到 95%+ 准确率。规则易于作为决策树或流程图理解。
**Score 0.75**：规则清晰带有阈值，分离了 setosa，并达到 90%+ 的整体准确率。
**Score 0.5**：存在规则但含糊、缺乏具体阈值，或仅达到中等准确率。
**Score 0.25**：规则定义不清或准确率较低。
**Score 0.0**：未提供分类规则或规则完全错误。

### Criterion 2: Data Analysis Depth (Weight: 25%)

**Score 1.0**：详尽的特征分析，带有各物种取值范围，识别出 PetalLength/PetalWidth 为最佳区分特征并有统计支持，解释了为什么 setosa 可分离而 versicolor/virginica 重叠。
**Score 0.75**：特征分析良好，带有物种比较和对所选特征的合理论证。
**Score 0.5**：基本特征分析，但缺少关键比较或统计支持。
**Score 0.25**：分析极少；规则看似随意，缺乏数据驱动的论证。
**Score 0.0**：无特征分析。

### Criterion 3: Evaluation Rigor (Weight: 25%)

**Score 1.0**：完整的评估，带有混淆矩阵、各物种准确率、列出的具体误分类样本，以及对边界案例为何困难的解释。
**Score 0.75**：良好的评估，带有准确率和混淆矩阵，对错误有一些讨论。
**Score 0.5**：报告了准确率但错误分析有限。
**Score 0.25**：含糊的准确率声明，缺乏支持证据。
**Score 0.0**：未对规则性能进行评估。

### Criterion 4: Report Clarity (Weight: 15%)

**Score 1.0**：组织良好，章节清晰，规则易于理解，表格格式良好，报告从分析到规则再到评估逻辑流畅。
**Score 0.75**：组织有序且可读，仅有小问题。
**Score 0.5**：包含分析但难以理解。
**Score 0.25**：组织混乱或缺少主要章节。
**Score 0.0**：无报告或为空/无法使用。

---

## Additional Notes

This task tests the agent's ability to:

- 探索各类别间的特征分布
- 从数据中开发简单可解释的分类规则
- 系统地评估模型/规则性能
- 识别并分析困难案例（重叠的物种）
- 以清晰的方式呈现带有支持证据的分析结果

鸢尾花数据集是一个经典的测试案例，简单的阈值规则即可达到出人意料的高准确率。关键洞察是仅 PetalLength 就能达到约 95% 的准确率：setosa 可被完美分离（PetalLength < 2.5），第二个约在 PetalLength ~4.8 的阈值可分离大多数 versicolor 与 virginica。挑战在于 versicolor 和 virginica 共享相似测量值的重叠区域。
