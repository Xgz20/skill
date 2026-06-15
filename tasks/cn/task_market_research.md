---
id: task_market_research
name: 竞争性市场调研
category: 调研
scene: 企业产品情报与业务信息助手
sub_scene: 竞争格局分析
difficulty: L3
capabilities:
- 信息检索与综合
- 自然语言生成
- 输出格式适配
- 指令遵循与约束理解
- 多步推理
grading_type: hybrid
timeout_seconds: 300
workspace_files: []
---

## Prompt

为**企业可观测性与 APM（应用性能监控，Application Performance Monitoring）**市场细分领域创建一份竞争格局分析。基于你的知识，识别排名前 5 的厂商、它们的关键差异化优势、市场趋势以及典型的定价模式。

**重要：你必须将报告保存到当前工作目录下一个名为 `market_research.md` 的文件中（文件名须完全一致）。** 不要仅在回复中输出报告 —— 文件必须写入磁盘。文件名必须精确（不能是 `market-research.md`，也不能放在子目录中）。

将报告组织为每个竞争对手各设一节，并附一张汇总对比表。

如果你能访问网页搜索工具，请使用它们来收集最新信息。否则，请运用你对该市场的知识来生成一份详尽的分析。

## Expected Behavior

Agent 应当：

1. 识别主要竞争对手（例如 Datadog、New Relic、Dynatrace、Splunk、Grafana Labs、Elastic 等）
2. 对每个竞争对手，记录：
   - 公司概况与市场地位
   - 关键产品差异化优势
   - 典型定价模式（按主机、按 GB、按用户等）
   - 显著的优势与劣势
3. 识别整体市场趋势（AI/ML 集成、OpenTelemetry 采用、整合、云原生等）
4. 创建一份组织良好的 Markdown 报告，包含：
   - 执行摘要
   - 各竞争对手简介
   - 一张对比表
   - 市场趋势章节

该报告读起来应像业务分析师为战略会议准备的材料。Agent 在可用时应使用网页搜索，但在网页搜索不可用时也能基于其知识库生成高质量的分析。

## Grading Criteria

- [ ] 已创建文件 `market_research.md`
- [ ] 报告识别出至少 5 个竞争对手
- [ ] 每个竞争对手都有实质性的简介（而不仅仅是一个名字）
- [ ] 报告包含一张对比表或矩阵
- [ ] 报告涵盖了竞争对手的定价模式
- [ ] 报告讨论了当前市场趋势
- [ ] 信息看起来是最新的、来源于网络（而非纯粹通用）
- [ ] 报告结构清晰，带有标题与章节
- [ ] 包含执行摘要或引言
- [ ] 写作质量专业且具分析性

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the market research task based on file creation and structural content.

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

    report_file = workspace / "market_research.md"

    if not report_file.exists():
        return {
            "file_created": 0.0,
            "competitors_identified": 0.0,
            "has_comparison_table": 0.0,
            "has_pricing_info": 0.0,
            "has_trends_section": 0.0,
            "has_structure": 0.0,
            "has_executive_summary": 0.0,
            "used_web_search": 0.0,
        }

    scores["file_created"] = 1.0
    content = report_file.read_text()
    content_lower = content.lower()

    # Check for known APM/observability competitors
    known_competitors = [
        "datadog", "new relic", "dynatrace", "splunk", "grafana",
        "elastic", "appdynamics", "honeycomb", "lightstep", "sumo logic",
        "instana", "sentry", "chronosphere", "logz.io", "coralogix",
        "signoz", "observe inc", "mezmo",
    ]
    found_competitors = [c for c in known_competitors if c in content_lower]

    if len(found_competitors) >= 5:
        scores["competitors_identified"] = 1.0
    elif len(found_competitors) >= 3:
        scores["competitors_identified"] = 0.5
    elif len(found_competitors) >= 1:
        scores["competitors_identified"] = 0.25
    else:
        scores["competitors_identified"] = 0.0

    # Check for comparison table (markdown table syntax)
    table_patterns = [
        r'\|.*\|.*\|',  # Markdown table rows
        r'\|[\s-]+\|',  # Table separator row
    ]
    has_table = all(re.search(p, content) for p in table_patterns)
    scores["has_comparison_table"] = 1.0 if has_table else 0.0

    # Check for pricing information
    pricing_patterns = [
        r'pric(e|ing|ed)',
        r'per[\s-]?(host|gb|user|seat|node|core)',
        r'free\s+tier',
        r'subscription',
        r'\$\d+',
        r'cost',
    ]
    pricing_matches = sum(1 for p in pricing_patterns if re.search(p, content_lower))
    if pricing_matches >= 3:
        scores["has_pricing_info"] = 1.0
    elif pricing_matches >= 1:
        scores["has_pricing_info"] = 0.5
    else:
        scores["has_pricing_info"] = 0.0

    # Check for market trends section
    trends_patterns = [
        r'trend', r'market\s+(direction|shift|movement|growth)',
        r'opentelemetry', r'otel',
        r'ai[\s/]ml', r'artificial intelligence', r'machine learning',
        r'consolidat', r'cloud[\s-]native',
    ]
    trends_matches = sum(1 for p in trends_patterns if re.search(p, content_lower))
    if trends_matches >= 3:
        scores["has_trends_section"] = 1.0
    elif trends_matches >= 1:
        scores["has_trends_section"] = 0.5
    else:
        scores["has_trends_section"] = 0.0

    # Check for document structure (headings)
    headings = re.findall(r'^#{1,3}\s+.+', content, re.MULTILINE)
    if len(headings) >= 6:
        scores["has_structure"] = 1.0
    elif len(headings) >= 3:
        scores["has_structure"] = 0.5
    else:
        scores["has_structure"] = 0.0

    # Check for executive summary / introduction
    summary_patterns = [
        r'(executive\s+summary|overview|introduction)',
    ]
    if any(re.search(p, content_lower) for p in summary_patterns):
        scores["has_executive_summary"] = 1.0
    else:
        scores["has_executive_summary"] = 0.0

    # Check transcript for web search tool usage
    used_search = False
    for event in transcript:
        if event.get("type") != "message":
            continue
        msg = event.get("message", {})
        if msg.get("role") == "assistant":
            for item in msg.get("content", []):
                if item.get("type") == "toolCall":
                    tool_name = item.get("name", "").lower()
                    params = item.get("arguments", item.get("params", {}))
                    # Check for web search / fetch tools
                    if any(t in tool_name for t in [
                        "web_search", "websearch", "search",
                        "web_fetch", "webfetch", "fetch",
                        "browse", "http",
                    ]):
                        used_search = True
                    # Also check execute_command for curl/wget
                    if tool_name in ["execute_command", "executecommand"]:
                        cmd = params.get("command", "").lower()
                        if any(t in cmd for t in ["curl", "wget", "web"]):
                            used_search = True

    scores["used_web_search"] = 1.0 if used_search else 0.0

    return scores
```

## LLM Judge Rubric

### Criterion 1: Research Depth and Accuracy (Weight: 30%)

**Score 1.0**：报告包含关于每个竞争对手的具体、准确的信息。细节超越表层描述 —— 包括具体的产品名称、特定功能以及市场定位。如果使用了网页搜索，信息应是最新的；如果基于知识，信息应准确且全面。
**Score 0.75**：报告对大多数竞争对手有良好的细节与具体信息，但少数简介显得单薄或依赖通用描述。
**Score 0.5**：报告对竞争对手的覆盖停留在表层。信息大体准确但缺乏具体性或深度。
**Score 0.25**：报告对竞争对手的细节很少。信息显得通用或可能不准确。
**Score 0.0**：报告缺失、没有实质性的竞争对手分析，或包含明显不准确的信息。

### Criterion 2: Analytical Quality (Weight: 25%)

**Score 1.0**：报告读起来像一份专业的市场分析。包含有意义的对比，识别出战略定位差异，并就竞争格局得出有洞见的结论。执行摘要有效地提炼了关键要点。
**Score 0.75**：报告提供了良好的分析，附有合理的对比和一定的战略洞见，但结论可能更加细致。
**Score 0.5**：报告呈现了信息但缺乏强有力的分析框架。读起来更像事实清单而非战略分析。
**Score 0.25**：报告大体上是原始数据堆砌，几乎没有分析或综合。
**Score 0.0**：没有任何分析性内容。

### Criterion 3: Market Trends and Context (Weight: 20%)

**Score 1.0**：报告识别并讨论了多个相关的市场趋势（例如 OpenTelemetry 采用、AI 驱动的可观测性、平台整合、向基于用量的定价转变、云原生监控）。趋势与它们如何影响竞争动态相关联。
**Score 0.75**：报告讨论了若干市场趋势并有合理的背景，但与竞争影响的关联有限。
**Score 0.5**：报告提及趋势但仅停留在表层，或遗漏了重要的当前趋势。
**Score 0.25**：趋势覆盖很少或通用。
**Score 0.0**：未讨论市场趋势。

### Criterion 4: Report Structure and Presentation (Weight: 15%)

**Score 1.0**：报告组织出色，层次清晰、格式一致，附有实用的对比表和专业的 Markdown 格式。易于浏览并提取关键信息。
**Score 0.75**：报告组织良好、格式得当。对比表存在但可以更全面。
**Score 0.5**：报告有基本结构但格式不一致，或缺少对比表等关键组织要素。
**Score 0.25**：报告组织混乱或难以浏览。
**Score 0.0**：报告没有可辨识的结构。

### Criterion 5: Pricing and Business Model Coverage (Weight: 10%)

**Score 1.0**：报告为每个竞争对手提供了具体的定价模式细节（按主机、按 GB、按用户、是否有免费层级、企业定价）。细节足以用于采购对比。
**Score 0.75**：报告为大多数竞争对手覆盖了定价模式，并有合理的具体性。
**Score 0.5**：报告提及部分竞争对手的定价，但缺乏细节或一致性。
**Score 0.25**：几乎没有提及定价，或仅涉及一两个竞争对手。
**Score 0.0**：未包含任何定价信息。

## Additional Notes

- 本任务测试 Agent 生成全面市场分析的能力。网页搜索为可选项，但若可用则更佳。
- 超时设置为 300 秒（5 分钟），以便从容地撰写报告。
- 混合评分方法将自动化的结构性检查（文件是否存在、是否含有正确的章节）与 LLM judge 对分析深度的评估相结合。
- 选择企业可观测性 / APM 市场是因为它是一个成熟的细分领域，有明确的市场领导者，无论是否使用网页搜索都可测试。
- 评分应奖励那些生成了含有具体、准确信息及良好分析框架报告的 Agent。
