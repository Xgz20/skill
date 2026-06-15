---
id: task_csv_gdp_ranking
name: 世界各国 GDP 排名
category: CSV 数据分析
scene: 数据库检索、表格整理与数据分析
sub_scene: CSV 数据分析
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 输出格式适配
- 自然语言生成
- 指令遵循与约束理解
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

请分析 GDP 排名并将你的发现写入 `gdp_ranking_report.md`。你的报告应包含：

- **前 20 大经济体**，按 GDP 从高到低排名，包含国家名称、GDP 值及其占世界 GDP 的百分比份额
- **后 10 名经济体**，按 GDP 从低到高排名
- **汇总统计**：世界 GDP 总量、GDP 均值、GDP 中位数、最小值和最大值
- **集中度分析**：前 5、前 10 和前 20 大经济体各持有世界 GDP 总量的多少百分比
- **"万亿美元俱乐部"**：列出所有 GDP 超过 1 万亿美元的国家及其合计占世界 GDP 的份额
- 一段简短的**总结段落**，解读全球 GDP 分布

---

## Expected Behavior

The agent should:

1. 读取并解析 CSV 文件（222 行）
2. 按 GDP 降序对国家排序
3. 识别出最大经济体：United States，$17,420.0B
4. 计算世界 GDP 总量（~$78,285.45B）
5. 计算每个国家的百分比份额
6. 计算集中度指标（前 5、前 10、前 20 份额）
7. 识别出 15 个 GDP 超过 1 万亿美元的国家
8. 计算汇总统计（均值 ~$352.64B，中位数 ~$21.52B）
9. 撰写一份结构良好的 markdown 报告

预期关键值：

- 世界 GDP 总量：~$78,285.45B
- #1：United States ($17,420.0B, ~22.3%)
- #2：China ($10,360.0B, ~13.2%)
- #3：Japan ($4,770.0B, ~6.1%)
- #4：Germany ($3,820.0B, ~4.9%)
- #5：France ($2,902.0B, ~3.7%)
- 前 5 份额：~50.2%
- 前 10 份额：~64.6%
- 前 20 份额：~79.2%
- GDP 均值：~$352.64B
- GDP 中位数：~$21.52B
- 万亿美元俱乐部：15 个国家
- 最小经济体：Niue ($0.01B)

---

## Grading Criteria

- [ ] 创建了报告文件 `gdp_ranking_report.md`
- [ ] 正确列出前 20 大经济体且 #1 为 United States
- [ ] 正确列出后 10 名经济体且 Niue 为最小
- [ ] 汇总统计包含总量、均值、中位数、最小值、最大值
- [ ] 集中度分析显示前 5、前 10 和前 20 的份额
- [ ] 识别出万亿美元俱乐部（15 个国家）
- [ ] 为已排名的国家包含百分比份额
- [ ] 解读分布的总结段落

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the GDP ranking task.

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

    report_path = workspace / "gdp_ranking_report.md"
    if not report_path.exists():
        for alt in ["gdp_report.md", "report.md", "ranking_report.md", "gdp_ranking.md", "analysis.md"]:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "top_economy": 0.0,
            "bottom_economy": 0.0,
            "summary_stats": 0.0,
            "concentration": 0.0,
            "trillion_club": 0.0,
            "pct_shares": 0.0,
            "summary_paragraph": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Check top economy (United States, $17,420B)
    has_us = bool(re.search(r'united\s*states', content_lower))
    has_17420 = bool(re.search(r'17[,.]?420', content))
    scores["top_economy"] = 1.0 if (has_us and has_17420) else (0.5 if has_us or has_17420 else 0.0)

    # Check bottom economy (Niue, $0.01B)
    has_niue = bool(re.search(r'niue', content_lower))
    has_001 = bool(re.search(r'0\.01', content))
    scores["bottom_economy"] = 1.0 if (has_niue and has_001) else (0.5 if has_niue or has_001 else 0.0)

    # Check summary statistics
    stats_found = 0
    if re.search(r'78[,.]?285', content):  # total
        stats_found += 1
    if re.search(r'35[12]\.\d|352\.6', content):  # mean ~352.64
        stats_found += 1
    if re.search(r'21\.5[0-9]', content):  # median ~21.52
        stats_found += 1
    if re.search(r'(?:mean|average|median)', content_lower):
        stats_found += 1
    scores["summary_stats"] = 1.0 if stats_found >= 3 else (0.5 if stats_found >= 2 else 0.0)

    # Check concentration analysis
    conc_found = 0
    if re.search(r'(?:top\s*5|five).*(?:50|49|51)\s*[\.\d]*%', content_lower):
        conc_found += 1
    if re.search(r'(?:top\s*10|ten).*(?:64|65)\s*[\.\d]*%', content_lower):
        conc_found += 1
    if re.search(r'(?:top\s*20|twenty).*(?:79|80)\s*[\.\d]*%', content_lower):
        conc_found += 1
    # Also accept the numbers without the "top N" prefix nearby
    if re.search(r'50\.?[12]%', content):
        conc_found += 1
    if re.search(r'64\.?[56]%', content):
        conc_found += 1
    if re.search(r'79\.?[12]%', content):
        conc_found += 1
    scores["concentration"] = 1.0 if conc_found >= 3 else (0.5 if conc_found >= 1 else 0.0)

    # Check $1 trillion club
    has_trillion = bool(re.search(r'(?:trillion|1[,.]?000|\$1t|\$1,000)', content_lower))
    has_15 = bool(re.search(r'(?:15|fifteen)\s*(?:countries|economies|nations|members)', content_lower))
    scores["trillion_club"] = 1.0 if (has_trillion and has_15) else (0.5 if has_trillion else 0.0)

    # Check percentage shares present
    pct_patterns = [r'22\.?[23]%', r'13\.?[23]%', r'6\.?[01]%']  # US, China, Japan shares
    pct_found = sum(1 for p in pct_patterns if re.search(p, content))
    scores["pct_shares"] = 1.0 if pct_found >= 2 else (0.5 if pct_found >= 1 else 0.0)

    # Check for summary/interpretation paragraph
    summary_patterns = [
        r'(?:concentrat|dominat|inequal|dispar|skew)',
        r'(?:united states|u\.?s\.?).*(?:largest|dominant|leading)',
        r'(?:median|mean).*(?:gap|difference|disparity|skew)',
    ]
    summary_found = sum(1 for p in summary_patterns if re.search(p, content_lower))
    scores["summary_paragraph"] = 1.0 if summary_found >= 2 else (0.5 if summary_found >= 1 else 0.0)

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Data Accuracy (Weight: 35%)

**Score 1.0**：所有排名正确，统计数据与预期值吻合（总量 ~$78,285B、均值 ~$353B、中位数 ~$21.5B），百分比份额计算准确。
**Score 0.75**：排名和统计数据大体正确，仅有小的取整差异。
**Score 0.5**：顶级经济体正确，但统计数据或较低排名有错误。
**Score 0.25**：排名或统计数据有若干重大错误。
**Score 0.0**：未尝试分析或根本性错误。

### Criterion 2: Analytical Depth (Weight: 30%)

**Score 1.0**：对 GDP 集中度提供了有意义的解读（均值与中位数之间的巨大差距表明极度偏斜），讨论了 US/China 的主导地位，指出大多数经济体规模较小，并对万亿美元俱乐部进行了背景说明。
**Score 0.75**：解读良好，仅有小的缺漏。
**Score 0.5**：陈述了事实但提供的解读或洞察有限。
**Score 0.25**：除列出数字外分析极少。
**Score 0.0**：未提供任何分析或解读。

### Criterion 3: Report Completeness (Weight: 20%)

**Score 1.0**：所有所需章节齐全：前 20、后 10、汇总统计、集中度分析、万亿美元俱乐部、总结段落。
**Score 0.75**：大多数章节齐全，仅有一处小遗漏。
**Score 0.5**：缺少若干章节。
**Score 0.25**：仅有一两个章节。
**Score 0.0**：报告缺失或为空。

### Criterion 4: Presentation Quality (Weight: 15%)

**Score 1.0**：格式良好的 markdown，排名使用表格，标题清晰，布局有条理。百分比份额与 GDP 值清晰地并列显示。
**Score 0.75**：格式良好，仅有小问题。
**Score 0.5**：可读但组织较差。
**Score 0.25**：难以理解。
**Score 0.0**：无报告或无法阅读。

---

## Additional Notes

This task tests the agent's ability to:

- 解析一个简单的三列 CSV 文件
- 按数值列对数据排序和排名
- 计算基本的描述性统计（总量、均值、中位数、最小值、最大值）
- 计算派生指标（百分比份额、集中度比率）
- 识别基于阈值的分组（万亿美元俱乐部）
- 解读极端的分布偏斜（均值 >> 中位数）

该数据集包含 222 个国家和地区。注意 Sint Maarten 显示的 GDP 为 $304.1B，对于一个约 4 万人口的地区而言这显得异常——这是一个已知的数据瑕疵。数据来自 2014 年。

已知正确值：

- 共 222 条记录
- 世界 GDP 总量：~$78,285.45B
- 均值：~$352.64B，中位数：~$21.52B
- 前 5 (US, China, Japan, Germany, France)：约占世界 GDP 的 ~50.2%
- 前 10：~64.6%，前 20：~79.2%
- 15 个国家超过 1 万亿美元
- 最小：Niue ($0.01B)，最大：United States ($17,420.0B)
