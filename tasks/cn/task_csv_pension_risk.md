---
id: task_csv_pension_risk
name: 美国养老金风险评估
category: CSV 数据分析
scene: 数据库检索、表格整理与数据分析
sub_scene: CSV 养老金风险评估
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
  - source: csvs/us_pension_by_state.csv
    dest: us_pension_by_state.csv
---

## Prompt

我的工作区里有一个 CSV 文件 `us_pension_by_state.csv`，包含按州和国会选区细分的美国联邦养老金支付数据。各列如下：

- `STATE_ABBREV_NAME` — 州缩写和名称（例如，州级汇总行用 "OH-OHIO Total"）
- `DISTRICT` — 国会选区编号、"At Large" 或年份
- `PAYEE_AMOUNT` — 支付给当前退休人员的总金额（带 $ 符号和逗号格式）
- `PAYEE_COUNT` — 当前领取福利的领取者人数
- `DEFERRED_COUNT` — 递延领取者人数（已归属但尚未领取福利的员工）

以 "Total" 结尾的行是州级汇总。第一行是总计（Grand Total）。

请对养老金的债务义务进行风险评估，并把你的发现写入 `pension_risk_report.md`。你的分析应包含：

- 各州的**递延-领取者比率**：计算 DEFERRED_COUNT / PAYEE_COUNT。该比率表明每个当前领取者对应有多少未来领取者在等待——比率越高意味着相对于当前的未来义务越多。按此比率对前 10 个州排名（排除领取者少于 100 人的条目）。
- **集中度风险**：前 5 个州占总支付金额的百分比是多少？前 10 个州呢？
- **选区级热点**：识别支付金额最高的 5 个单独国会选区（不是州级汇总）。这些代表了养老金义务的地理集中点。
- **风险分级分类**：根据递延-领取者比率将所有州分为三个等级：
  - **高风险**（比率 > 0.75）：相对于当前领取者有显著的未来义务
  - **中风险**（比率 0.50–0.75）：中等的未来义务
  - **低风险**（比率 < 0.50）：可控的未来义务
  列出每个等级的州数量，并指明高风险等级中的州名。
- 对整体风险概况和建议的**总结**

---

## Expected Behavior

Agent 应当：

1. 解析该 CSV，清理格式，并计算每个州的递延-领取者比率
2. 按比率排名：DC (~5.69)、NJ (~1.07)、AK (~0.99)、ND (~0.99)、UT (~0.88) 居前
3. 计算集中度：前 5 个州（OH、PA、FL、MI、CA）占总额的 ~38%；前 10 个 ~55%
4. 找出选区热点：IN-1 ($99.2M)、MI-5 ($97.8M)、OH-13 ($111.2M)、PA-7 ($72.0M)、WV-1 ($67.4M)
5. 根据比率阈值将各州分入风险等级
6. DC 是一个重大异常值，比率 ~5.69（544 名领取者，3,093 名递延者）
7. 高风险等级包括：DC、NJ、AK、ND、UT、CA、NY、CO、CT、HI（比率 > 0.75）

关键预期数值：

- DC 递延-领取者比率：~5.69（遥遥领先的最高值）
- NJ 比率：~1.07（除 DC 外唯一 > 1.0 的州）
- 按金额排名最高的选区：OH-13 (~$111.2M)
- 前 5 集中度：占总额 $5.71B 的 ~38%
- 全国平均比率：~0.55
- 高风险州（比率 > 0.75）：约 10 个州

---

## Grading Criteria

- [ ] 创建了报告文件 `pension_risk_report.md`
- [ ] 计算了递延-领取者比率并对前 10 个州排名
- [ ] 识别 DC 为最高比率（~5.69）
- [ ] 识别 NJ 为第二高比率（~1.07）
- [ ] 计算了集中度风险（前 5 和前 10 的百分比）
- [ ] 识别出选区级热点
- [ ] 识别 OH-13 为顶部选区（~$111M）
- [ ] 风险分级分类带各等级州数量
- [ ] 列出高风险等级的州
- [ ] 带风险评估和建议的总结

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the pension risk assessment task.

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
    report_path = workspace / "pension_risk_report.md"
    if not report_path.exists():
        alternatives = ["risk_report.md", "report.md", "pension_report.md", "pension_risk.md", "risk_assessment.md"]
        for alt in alternatives:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "ratio_ranking": 0.0,
            "dc_highest_ratio": 0.0,
            "nj_second_ratio": 0.0,
            "concentration_risk": 0.0,
            "district_hotspots": 0.0,
            "oh13_top_district": 0.0,
            "risk_tiers": 0.0,
            "high_risk_states": 0.0,
            "summary_recommendations": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Deferred-to-payee ratio ranking
    ratio_context = bool(re.search(r'(?:deferred|ratio|defer.*payee)', content_lower))
    ratio_states = ["washington dc", "dc", "new jersey", "alaska", "north dakota", "utah"]
    ratio_mentioned = sum(1 for s in ratio_states if s in content_lower)
    scores["ratio_ranking"] = 1.0 if ratio_mentioned >= 4 and ratio_context else (0.5 if ratio_mentioned >= 2 else 0.0)

    # DC highest ratio
    dc_patterns = [
        r'(?:dc|washington\s*dc|district\s*of\s*columbia).*(?:5\.69|5\.7|highest|outlier|extreme)',
        r'(?:highest|outlier|extreme).*(?:ratio).*(?:dc|washington\s*dc)',
        r'(?:dc|washington\s*dc).*ratio.*(?:5\.[67])',
    ]
    scores["dc_highest_ratio"] = 1.0 if any(re.search(p, content_lower) for p in dc_patterns) else 0.0

    # NJ second ratio
    nj_patterns = [
        r'new\s*jersey.*(?:1\.0[67]|second|#2|only.*(?:above|over|exceed).*1)',
        r'(?:second|#2).*(?:ratio).*new\s*jersey',
        r'new\s*jersey.*1\.0\d',
    ]
    scores["nj_second_ratio"] = 1.0 if any(re.search(p, content_lower) for p in nj_patterns) else 0.0

    # Concentration risk
    conc_patterns = [
        r'(?:3[5-9]|4[0-2])\s*%.*(?:top\s*5|five)',
        r'(?:top\s*5|five).*(?:3[5-9]|4[0-2])\s*%',
        r'(?:5[2-8]|concentration).*(?:top\s*10|ten)',
        r'(?:top\s*10|ten).*(?:5[2-8])\s*%',
        r'concentration.*risk',
    ]
    scores["concentration_risk"] = 1.0 if any(re.search(p, content_lower) for p in conc_patterns) else 0.0

    # District hotspots
    district_terms = ["district", "congressional", "hotspot"]
    has_district_context = any(t in content_lower for t in district_terms)
    hotspot_patterns = [r'in-?1', r'mi-?5', r'oh-?13', r'pa-?7', r'wv-?1', r'oh-?6']
    hotspot_count = sum(1 for p in hotspot_patterns if re.search(p, content_lower))
    scores["district_hotspots"] = 1.0 if hotspot_count >= 3 and has_district_context else (0.5 if hotspot_count >= 2 else 0.0)

    # OH-13 as top district
    oh13_patterns = [
        r'oh(?:io)?[- ]?13.*(?:111|highest|top|largest|first)',
        r'(?:highest|top|largest|first).*(?:district).*oh(?:io)?[- ]?13',
        r'oh(?:io)?[- ]?13.*\$?111',
    ]
    scores["oh13_top_district"] = 1.0 if any(re.search(p, content_lower) for p in oh13_patterns) else 0.0

    # Risk tiers
    tier_patterns = [
        r'(?:high|medium|low)\s*risk',
        r'(?:tier|category|classification)',
        r'(?:0\.75|0\.50|0\.5)',
    ]
    tier_count = sum(1 for p in tier_patterns if re.search(p, content_lower))
    scores["risk_tiers"] = 1.0 if tier_count >= 2 else (0.5 if tier_count >= 1 else 0.0)

    # High-risk states listed
    high_risk_names = ["dc", "washington dc", "new jersey", "alaska", "north dakota",
                       "utah", "california", "new york", "colorado", "connecticut", "hawaii"]
    hr_mentioned = sum(1 for s in high_risk_names if s in content_lower)
    has_high_risk_context = bool(re.search(r'high.*risk', content_lower))
    scores["high_risk_states"] = 1.0 if hr_mentioned >= 6 and has_high_risk_context else (0.5 if hr_mentioned >= 3 else 0.0)

    # Summary and recommendations
    rec_patterns = [
        r'recommend',
        r'(?:monitor|watch|attention|concern)',
        r'(?:mitigat|manag|address|plan)',
        r'(?:risk|exposure).*(?:profile|assessment|overall)',
    ]
    rec_count = sum(1 for p in rec_patterns if re.search(p, content_lower))
    scores["summary_recommendations"] = 1.0 if rec_count >= 2 else (0.5 if rec_count >= 1 else 0.0)

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Risk Metric Accuracy (Weight: 30%)

**Score 1.0**：递延-领取者比率计算正确，DC 被识别为极端异常值（~5.69），NJ 为第二（~1.07），并指出全国平均（~0.55）。集中度百分比准确。
**Score 0.75**：大多数比率正确，仅有轻微错误；关键异常值已识别。
**Score 0.5**：理解比率概念但若干数值有误或遗漏关键异常值。
**Score 0.25**：重大计算错误或对比率概念的误解。
**Score 0.0**：未计算比率或完全错误。

### Criterion 2: Multi-Level Analysis (Weight: 25%)

**Score 1.0**：分析在三个层次上运作——州级比率、整体组合的集中度风险，以及选区级粒度。每个层次都提供独特的洞见。选区热点识别正确。
**Score 0.75**：三个层次都齐全，但其中一个较浅或不完整。
**Score 0.5**：仅提供三个分析层次中的两个。
**Score 0.25**：仅有一个层次的分析。
**Score 0.0**：没有结构化分析。

### Criterion 3: Risk Framework Quality (Weight: 25%)

**Score 1.0**：清晰的等级分类，阈值明确，各州分类正确，框架产生可操作的分组。指出 DC 是特殊情况。承认比率作为单一风险指标的局限性。
**Score 0.75**：良好的等级体系，大多数州分类正确。
**Score 0.5**：等级概念存在但阈值不清晰或分类有误。
**Score 0.25**：没有明确标准的含糊风险分类。
**Score 0.0**：未尝试风险分类。

### Criterion 4: Recommendations and Insight (Weight: 20%)

**Score 1.0**：与具体发现挂钩的可操作建议。指出仅有高比率并不意味着高美元风险（ND 比率高但金额很小）。区分比率风险与绝对美元风险。提及监测策略。
**Score 0.75**：良好的建议，有一定细微考量。
**Score 0.5**：未与具体数据发现挂钩的泛泛建议。
**Score 0.25**：建议很少或肤浅。
**Score 0.0**：没有建议。

---

## Additional Notes

本任务测试 Agent 的以下能力：

- 计算并解读用于风险评估的比率指标
- 在多个粒度层次（全国、州、选区）上分析数据
- 从量化阈值构建分类框架
- 识别异常值并解释其意义
- 将量化发现综合为定性风险评估
- 处理边界情况（DC 作为非州、计数极小的领地、零值条目）

递延-领取者比率是未来义务增长的一个代理指标。DC 的极端比率（5.69）反映了它作为联邦就业枢纽的独特角色，许多员工已归属但在退休前已迁离。优秀的回答会指出这一背景上的细微之处。
