---
id: task_csv_pension_ranking
name: 美国养老金州级排名
category: CSV 数据分析
scene: 数据库检索、表格整理与数据分析
sub_scene: CSV 排名分析
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 自然语言生成
- 输出格式适配
- 指令遵循与约束理解
grading_type: hybrid
timeout_seconds: 180
grading_weights:
  automated: 0.6
  llm_judge: 0.4
workspace_files:
  - source: csvs/us_pension_by_state.csv
    dest: us_pension_by_state.csv
---

## Prompt

我的工作区里有一个 CSV 文件 `us_pension_by_state.csv`，包含按州和国会选区细分的美国联邦养老金支付数据。各列如下：

- `STATE_ABBREV_NAME` — 州缩写和名称（例如，州级汇总行用 "OH-OHIO Total"，选区行用 "OH-OHIO"）
- `DISTRICT` — 国会选区编号、"At Large" 或年份（总计行使用 "2018"）
- `PAYEE_AMOUNT` — 支付给退休人员的总金额（带 $ 符号和逗号格式）
- `PAYEE_COUNT` — 当前领取者人数（带逗号格式）
- `DEFERRED_COUNT` — 递延（未来）领取者人数（带逗号格式）

以 "Total" 结尾的行包含州级汇总。第一行数据是所有州的总计（Grand Total）。

请分析这些数据，并把你的发现写入 `pension_ranking_report.md`。你的报告应包含：

- 按总支付金额降序排列的**前 10 个州**，以及它们的金额和领取人数
- 按总支付金额排列的**后 5 个州**（排除领地以及金额为 $0 的条目）
- 按当前领取人数排列的**前 10 个州**
- 所有州的**总计**（总金额、总领取人数、总递延人数）
- 对地理分布规律的简要**分析**——哪些区域主导了联邦养老金支付，以及为什么可能如此

---

## Expected Behavior

Agent 应当：

1. 读取并解析该 CSV 文件，处理美元格式的金额（去除 `$` 和逗号）
2. 筛选出州级 "Total" 行并提取金额、领取人数和递延人数
3. 按总支付金额排序以生成前 10 排名
4. 识别金额非零的后 5 个州/领地
5. 按领取人数排序以生成领取人数排名
6. 提取总计（Grand Total）行
7. 撰写一份带分析的结构化 markdown 报告

关键预期数值：

- 总计：约 $5,711,533,247，覆盖 877,305 名领取者，483,720 名递延者
- 按金额排名前 3：Ohio (~$536.2M)、Pennsylvania (~$456.4M)、Florida (~$429.0M)
- 按金额排名第 4-5：Michigan (~$389.7M)、California (~$357.7M)
- 按领取人数排名前 3：Pennsylvania (78,119)、Ohio (77,679)、Florida (59,857)
- 后几名的州/领地包括：Northern Mariana Islands (~$5,894)、American Samoa (~$39,962)、Armed Forces Pacific (~$103,423)

---

## Grading Criteria

- [ ] 创建了报告文件 `pension_ranking_report.md`
- [ ] 正确列出按总支付金额排名的前 10 个州
- [ ] 识别 Ohio 为按金额排名 #1（~$536M）
- [ ] 识别 Pennsylvania 为按金额排名 #2（~$456M）
- [ ] 识别 Florida 为按金额排名 #3（~$429M）
- [ ] 识别出后 5 个州/领地
- [ ] 报告总计数字（~$5.7B、~877K 领取者、~484K 递延者）
- [ ] 包含按领取人数排名的州
- [ ] 提供地理分布规律分析

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the pension fund ranking task.

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
    report_path = workspace / "pension_ranking_report.md"
    if not report_path.exists():
        alternatives = ["ranking_report.md", "report.md", "pension_report.md", "pension_ranking.md"]
        for alt in alternatives:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "top_10_listed": 0.0,
            "ohio_first": 0.0,
            "pennsylvania_second": 0.0,
            "florida_third": 0.0,
            "bottom_states": 0.0,
            "grand_total": 0.0,
            "payee_count_ranking": 0.0,
            "geographic_analysis": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Check top 10 listing — at least 8 of the actual top 10 states mentioned
    top_10_states = ["ohio", "pennsylvania", "florida", "michigan", "california",
                     "new york", "illinois", "indiana", "north carolina", "georgia"]
    mentioned = sum(1 for s in top_10_states if s in content_lower)
    scores["top_10_listed"] = 1.0 if mentioned >= 8 else (0.5 if mentioned >= 5 else 0.0)

    # Ohio as #1 by amount
    ohio_patterns = [
        r'ohio.*(?:536|first|#1|highest|top|rank.*1|largest)',
        r'(?:first|#1|highest|top|rank.*1|largest).*ohio',
        r'1[\.\)]\s*(?:oh[- ])?ohio',
        r'ohio.*\$?536',
    ]
    scores["ohio_first"] = 1.0 if any(re.search(p, content_lower) for p in ohio_patterns) else 0.0

    # Pennsylvania as #2
    pa_patterns = [
        r'pennsylvania.*(?:456|second|#2|rank.*2)',
        r'(?:second|#2|rank.*2).*pennsylvania',
        r'2[\.\)]\s*(?:pa[- ])?pennsylvania',
        r'pennsylvania.*\$?456',
    ]
    scores["pennsylvania_second"] = 1.0 if any(re.search(p, content_lower) for p in pa_patterns) else 0.0

    # Florida as #3
    fl_patterns = [
        r'florida.*(?:429|third|#3|rank.*3)',
        r'(?:third|#3|rank.*3).*florida',
        r'3[\.\)]\s*(?:fl[- ])?florida',
        r'florida.*\$?429',
    ]
    scores["florida_third"] = 1.0 if any(re.search(p, content_lower) for p in fl_patterns) else 0.0

    # Bottom states mentioned
    bottom_terms = ["northern mariana", "american samoa", "armed forces", "guam", "palau"]
    bottom_count = sum(1 for t in bottom_terms if t in content_lower)
    scores["bottom_states"] = 1.0 if bottom_count >= 3 else (0.5 if bottom_count >= 2 else 0.0)

    # Grand total
    grand_patterns = [
        r'5[,.]7\d*\s*billion',
        r'\$?5[,.]711',
        r'877[,.]?\d*\s*(?:thousand|payee|recipient)',
        r'483[,.]?\d*\s*(?:thousand|deferred)',
    ]
    grand_count = sum(1 for p in grand_patterns if re.search(p, content_lower))
    scores["grand_total"] = 1.0 if grand_count >= 2 else (0.5 if grand_count >= 1 else 0.0)

    # Payee count ranking (PA and OH should be top by count)
    payee_patterns = [
        r'pennsylvania.*78[,.]?119',
        r'ohio.*77[,.]?679',
        r'payee.*count.*pennsylvania',
        r'(?:most|highest).*(?:payee|recipient).*pennsylvania',
    ]
    scores["payee_count_ranking"] = 1.0 if any(re.search(p, content_lower) for p in payee_patterns) else 0.5 if "payee" in content_lower and "count" in content_lower else 0.0

    # Geographic analysis
    geo_patterns = [
        r'(?:rust\s*belt|midwest|industrial)',
        r'(?:geographic|regional|pattern)',
        r'(?:federal|government|military).*(?:employ|presence|base)',
        r'(?:northeast|southeast|sunbelt)',
    ]
    geo_count = sum(1 for p in geo_patterns if re.search(p, content_lower))
    scores["geographic_analysis"] = 1.0 if geo_count >= 2 else (0.5 if geo_count >= 1 else 0.0)

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Data Parsing and Accuracy (Weight: 35%)

**Score 1.0**：所有美元金额、领取人数和排名都被正确解析并报告。州级汇总与预期数值精确一致。
**Score 0.75**：大多数数值正确，仅有轻微舍入差异或排名中有一个州位置错误。
**Score 0.5**：排名大致正确，但若干数值存在解析错误，或 Agent 混淆了选区行与州级汇总。
**Score 0.25**：重大解析错误——金额错误、行类型混淆或排名严重不正确。
**Score 0.0**：未能解析 CSV 或产生完全错误的结果。

### Criterion 2: Completeness of Rankings (Weight: 30%)

**Score 1.0**：所有要求的排名都齐全：按金额前 10、后 5、按领取人数前几名以及总计——每项都有支撑数字。
**Score 0.75**：大部分排名齐全，仅有小遗漏（例如缺少某一类排名或缺少支撑数字）。
**Score 0.5**：仅提供按金额前 10，其他排名缺失或不完整。
**Score 0.25**：仅有部分排名且数据缺失。
**Score 0.0**：未提供任何排名。

### Criterion 3: Analysis Quality (Weight: 20%)

**Score 1.0**：有洞见的地理分析，将养老金集中度与联邦就业模式、军事基地或历史因素联系起来。指出诸如 Rust Belt 主导等有趣规律。
**Score 0.75**：合理的分析，有一些地理观察。
**Score 0.5**：表面观察，缺乏更深入的分析。
**Score 0.25**：分析很少或含糊。
**Score 0.0**：未提供任何分析。

### Criterion 4: Report Structure (Weight: 15%)

**Score 1.0**：结构良好的 markdown，章节清晰，排名以格式化的表格或列表呈现，可读性好。
**Score 0.75**：结构良好，仅有轻微格式问题。
**Score 0.5**：内容齐全但组织混乱。
**Score 0.25**：杂乱或难以阅读。
**Score 0.0**：没有报告或文件为空。

---

## Additional Notes

本任务测试 Agent 的以下能力：

- 解析带格式化货币值（美元符号、逗号、带引号字段）的 CSV
- 基于命名模式（"Total" 后缀）筛选并聚合行
- 沿多个维度排序并排名数据
- 处理边界情况（领地、武装部队条目、零值行）
- 提供超越原始数字的地理/背景分析

该 CSV 包含 61 个州/领地级别的汇总。美元金额的格式为 `"$1,234,567 "`，带有尾随空格和内嵌逗号。Agent 必须去除格式才能进行数值比较。
