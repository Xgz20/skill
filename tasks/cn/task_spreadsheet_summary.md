---
id: task_spreadsheet_summary
name: CSV 与 Excel 数据汇总
category: 综合分析
scene: 数据库检索、表格整理与数据分析
sub_scene: 电子表格数据汇总
difficulty: L3
capabilities:
- 数据提取与处理
- 工具调用
- 输出格式适配
- 自然语言生成
- 多步推理
grading_type: hybrid
timeout_seconds: 180
grading_weights:
  automated: 0.6
  llm_judge: 0.4
workspace_files:
  - source: quarterly_sales.csv
    dest: quarterly_sales.csv
  - source: company_expenses.xlsx
    dest: company_expenses.xlsx
---

## Prompt

我的工作区中有两个数据文件，已提供给你进行分析：

1. `quarterly_sales.csv` —— 一个包含销售交易记录的 CSV 文件，列为：Date、Region、Product、Units_Sold、Unit_Price、Revenue、Cost（24 行数据）
2. `company_expenses.xlsx` —— 一个包含两个工作表的 Excel 工作簿："Q1_Expenses"（员工费用报告，12 条记录）和 "Budgets"（各部门预算分配）

请阅读并分析这两个文件，然后将一份汇总报告写入 `data_summary.md`，内容包括：

- **CSV 分析**：总营收、总利润（营收减去成本）、销售总量、按营收计算的最佳表现区域，以及按营收计算的最畅销产品。
- **Excel 分析**：Q1 总支出、支出最高的部门、总支出最高的员工，以及按部门进行的 Q1 实际支出与 Q1 预算对比。
- 一个简要的整体洞察部分，综合两个文件的发现。

---

## Expected Behavior

Agent 应当：

1. 读取并解析 CSV 文件（标准 CSV 格式，易于解析）
2. 读取并解析 Excel 文件（需要处理含多个工作表的 `.xlsx` 格式）
3. 从两个文件中计算出正确的聚合统计数据
4. 将一份结构良好的 markdown 汇总报告写入 `data_summary.md`

CSV 包含 24 行销售数据，涵盖 4 个区域（North、South、East、West）和 3 个产品（Widget A、B、C）。Excel 文件有 12 条费用记录，涵盖 4 个部门，另有一个独立的预算工作表，包含各部门的季度分配。

预期的关键值：

- CSV 总营收：$119,900
- CSV 总利润：$47,960
- CSV 总销量：3,775
- CSV 最佳区域：East（$33,075）
- CSV 最畅销产品：Widget B（$47,400）
- Excel Q1 总支出：$15,430
- Excel 支出最高部门：Engineering（$7,680）
- Excel 支出最高员工：Alice Chen（$5,400）

---

## Grading Criteria

- [ ] Agent 成功读取了 CSV 文件
- [ ] Agent 成功读取了 Excel 文件（包括多个工作表）
- [ ] 汇总报告文件 `data_summary.md` 已创建
- [ ] 总营收报告正确（~$119,900）
- [ ] 总利润计算正确（~$47,960）
- [ ] 识别出按营收计算的最佳区域（East）
- [ ] 识别出按营收计算的最畅销产品（Widget B）
- [ ] Q1 总支出报告正确（~$15,430）
- [ ] 识别出支出最高的部门（Engineering）
- [ ] 识别出支出最高的员工（Alice Chen）
- [ ] 包含预算与实际的对比
- [ ] 报告结构良好且易读

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the spreadsheet summary task by checking the output report
    for correct numerical values and key findings.

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

    # Check if summary report exists
    report_path = workspace / "data_summary.md"
    if not report_path.exists():
        # Try common alternative names
        alternatives = ["summary.md", "report.md", "data_report.md", "analysis.md"]
        for alt in alternatives:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        scores["report_created"] = 0.0
        scores["total_revenue"] = 0.0
        scores["total_profit"] = 0.0
        scores["top_region"] = 0.0
        scores["top_product"] = 0.0
        scores["total_expenses"] = 0.0
        scores["top_department"] = 0.0
        scores["top_employee"] = 0.0
        scores["budget_comparison"] = 0.0
        return scores

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Check total revenue (~119,900)
    # Look for the number in various formats: 119900, 119,900, 119900.00, etc.
    revenue_patterns = [
        r'119[,.]?900',
        r'119[,.]?900\.00',
    ]
    has_revenue = any(re.search(p, content.replace(' ', '')) for p in revenue_patterns)
    scores["total_revenue"] = 1.0 if has_revenue else 0.0

    # Check total profit (~47,960)
    profit_patterns = [
        r'47[,.]?960',
    ]
    has_profit = any(re.search(p, content.replace(' ', '')) for p in profit_patterns)
    scores["total_profit"] = 1.0 if has_profit else 0.0

    # Check top region (East)
    # Look for East being called out as top/highest/best/leading region
    east_patterns = [
        r'east.*(?:top|highest|most|best|leading|largest)',
        r'(?:top|highest|most|best|leading|largest).*east',
        r'east.*\$?33[,.]?075',
        r'33[,.]?075.*east',
    ]
    has_top_region = any(re.search(p, content_lower) for p in east_patterns)
    scores["top_region"] = 1.0 if has_top_region else 0.0

    # Check top product (Widget B)
    product_patterns = [
        r'widget\s*b.*(?:top|highest|most|best|leading|largest)',
        r'(?:top|highest|most|best|leading|largest).*widget\s*b',
        r'widget\s*b.*\$?47[,.]?400',
        r'47[,.]?400.*widget\s*b',
    ]
    has_top_product = any(re.search(p, content_lower) for p in product_patterns)
    scores["top_product"] = 1.0 if has_top_product else 0.0

    # Check total Q1 expenses (~15,430)
    expense_patterns = [
        r'15[,.]?430',
    ]
    has_expenses = any(re.search(p, content.replace(' ', '')) for p in expense_patterns)
    scores["total_expenses"] = 1.0 if has_expenses else 0.0

    # Check top department (Engineering)
    dept_patterns = [
        r'engineering.*(?:top|highest|most|largest|leading)',
        r'(?:top|highest|most|largest|leading).*engineering',
        r'engineering.*\$?7[,.]?680',
        r'7[,.]?680.*engineering',
    ]
    has_top_dept = any(re.search(p, content_lower) for p in dept_patterns)
    scores["top_department"] = 1.0 if has_top_dept else 0.0

    # Check top employee (Alice Chen)
    employee_patterns = [
        r'alice\s*chen.*(?:top|highest|most|largest|leading)',
        r'(?:top|highest|most|largest|leading).*alice\s*chen',
        r'alice\s*chen.*\$?5[,.]?400',
        r'5[,.]?400.*alice\s*chen',
    ]
    has_top_employee = any(re.search(p, content_lower) for p in employee_patterns)
    scores["top_employee"] = 1.0 if has_top_employee else 0.0

    # Check for budget vs actual comparison
    budget_indicators = [
        r'budget.*actual',
        r'actual.*budget',
        r'budget.*expense',
        r'under\s*budget',
        r'over\s*budget',
        r'variance',
        r'25[,.]?000',  # Engineering Q1 budget
    ]
    has_budget = any(re.search(p, content_lower) for p in budget_indicators)
    scores["budget_comparison"] = 1.0 if has_budget else 0.0

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Data Reading and Parsing (Weight: 25%)

**Score 1.0**：Agent 正确读取了 CSV 文件和多工作表的 Excel 文件，无错误地提取了所有相关数据。
**Score 0.75**：Agent 读取了两个文件，但在其中一种格式上有小问题（例如只读取了一个 Excel 工作表）。
**Score 0.5**：Agent 正确读取了一个文件，但在另一种格式上遇到困难。
**Score 0.25**：Agent 尝试读取文件，但遇到了明显的解析错误。
**Score 0.0**：Agent 未能读取任一文件，或未尝试数据提取。

### Criterion 2: Analytical Accuracy (Weight: 35%)

**Score 1.0**：所有计算的统计数据（总计、最佳表现者、对比）数值正确且清晰呈现。
**Score 0.75**：大多数统计数据正确，存在一两个小的数值错误。
**Score 0.5**：部分统计数据正确，但多个关键数字错误或缺失。
**Score 0.25**：很少有统计数据正确；存在重大计算错误。
**Score 0.0**：没有正确的统计数据，或未尝试分析。

### Criterion 3: Report Quality and Structure (Weight: 25%)

**Score 1.0**：报告组织良好，章节清晰，markdown 格式恰当，发现内容呈现易读。包含标题、表格或格式化的数据列表。
**Score 0.75**：报告组织有序且易读，存在小的格式问题。
**Score 0.5**：报告包含信息，但组织混乱或难以理解。
**Score 0.25**：报告杂乱无章或缺少主要章节。
**Score 0.0**：未创建报告，或报告为空/不可用。

### Criterion 4: Insights and Synthesis (Weight: 15%)

**Score 1.0**：报告包含深思熟虑的跨文件洞察、关于趋势的有意义观察，以及结合两个数据源的可行结论。
**Score 0.75**：报告包含一些跨文件观察，但可以更有洞察力。
**Score 0.5**：报告呈现了两个文件的数据，但没有有意义的综合。
**Score 0.25**：报告几乎没有将两个数据源的发现联系起来。
**Score 0.0**：未提供任何综合或洞察。

---

## Additional Notes

本任务测试 Agent 的以下能力：

- 解析多种文件格式（CSV 和 XLSX）
- 处理多工作表的 Excel 工作簿
- 执行数值聚合和对比
- 产出一份结合多个数据源的结构化书面汇总

数据有意保持小而干净（无缺失值、无编码问题），因此重点在于正确读取两种格式并计算准确的汇总。CSV 有 24 行，Excel 跨 2 个工作表共有 12 行费用数据加 4 行预算数据。

用于自动检查的已知正确值：

- CSV：24 行，总营收 $119,900，总成本 $71,940，总利润 $47,960，3,775 个单位
- CSV 最佳区域：East（$33,075），最畅销产品：Widget B（$47,400）
- Excel Q1 支出：$15,430，支出最高部门：Engineering（$7,680），支出最高员工：Alice Chen（$5,400）
- Excel Q1 预算：Engineering $25,000，Marketing $15,000，Sales $12,000，HR $8,000
