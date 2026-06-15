---
id: task_meeting_gov_recommendations
name: NASA UAP 听证会小组建议
category: 会议分析
scene: 数据库检索、表格整理与数据分析
sub_scene: 会议记录建议提取
difficulty: L2
capabilities:
- 数据提取与处理
- 信息检索与综合
- 自然语言生成
- 指令遵循与约束理解
- 输出格式适配
grading_type: hybrid
timeout_seconds: 180
grading_weights:
  automated: 0.5
  llm_judge: 0.5
workspace_files:
  - source: meetings/2025-07-30-nasa-holds-first-public-meeting-on-ufos-transcript.md
    dest: transcript.md
---

## Prompt

我有一个文件 `transcript.md`，这是 NASA 首次关于不明异常现象（UAP/UFO）公开会议的记录。在整个会议中，小组成员和演讲者就 NASA 应该如何开展 UAP 研究提出了各种建议。

请阅读记录并将所有建议提取到一个名为 `recommendations.md` 的文件中。对于每个建议，包括：

- **建议**（明确的、可操作的陈述）
- **提出者**（发言者姓名）
- **背景**（为什么他们提出这个建议的简要解释）
- **分类**（归类为：数据收集、数据标准、传感器技术、合作伙伴关系、公众参与、科学方法或其他）

按类别对建议分组。在每个类别中，按它们在记录中出现的顺序列出。最后，包括对最强调或重复最多的建议的简要总结。

---

## Expected Behavior

Agent 应该：

1. 阅读并解析完整记录
2. 识别发言者的明确和隐含建议
3. 清晰地分类和组织它们
4. 将每个建议归属于正确的发言者

关键建议包括：

**数据收集：**
- 从公众众包未分类的开源数据（Kirkpatrick）
- 开发用于 UAP 数据收集的公民科学众包平台/应用（Bianco、Spergel）
- 同时收集多传感器、多平台、多站点数据（Bianco）
- 在热点地区建立 24/7 收集监测活动，持续 3 个月（Kirkpatrick - 生活模式分析）

**数据标准：**
- 确保 UAP 数据满足 FAIR 标准（可查找性、可访问性、互操作性、可重用性）（Bianco）
- 创建有组织的存储库以进行系统化数据检索（Bianco）
- 收集观测数据的同时收集全面的元数据（Bianco）
- NASA 应提供高数据质量标准（Spergel）

**传感器技术：**
- 评估大规模地基科学仪器用于 UAP 检测（Kirkpatrick）
- 评估地球科学卫星的 UAP 检测能力（Kirkpatrick）
- 在选定区域部署专用传感器（Kirkpatrick）
- 利用现有的为时域异常检测设计的天文观测站（Bianco）
- 使用经过良好校准的专用仪器（Spergel）
- 收集 FAA 原始雷达数据而不仅仅是处理后的数据（Reggie 建议）

**合作伙伴关系：**
- 建立国外/国际科学合作伙伴关系（Kirkpatrick）
- 利用五眼情报合作伙伴关系（Kirkpatrick）
- 跨联邦机构合作 — FAA、NOAA、DOD、DOE（多位发言者）
- 利用 NASA 的阿尔忒弥斯协议国际关系（Gold）
- 与商务部合作进行太空交通管理（Gold）

**公众参与：**
- NASA 应引领科学讨论以减少污名（Kirkpatrick、Spergel）
- 利用公众对 NASA 的信任来消除 UAP 报告的污名（Bontempi）
- 将 UAP 话题作为扩大公众对科学方法理解的机会（Bianco）

**科学方法：**
- 对先进能力进行同行评审并在科学期刊上发表（Kirkpatrick）
- 将 AI/ML 技术应用于存档的科学数据（Kirkpatrick）
- 在识别异常之前彻底表征"正常"背景（Spergel）
- 使用监督和非监督机器学习进行异常检测（Bianco）
- 组建跨学科研究团队（Bontempi）
- 将搜索扩展到技术信号和地球大气层之外的观测（Grinspoon）

---

## Grading Criteria

- [ ] 创建了输出文件 `recommendations.md`
- [ ] 提取至少 12 个不同的建议
- [ ] 建议被归类到有意义的组中
- [ ] 包含众包/公民科学建议
- [ ] 包含数据标准（FAIR 或类似）建议
- [ ] 包含传感器评估建议
- [ ] 包含国际合作伙伴关系建议
- [ ] 包含减少污名建议
- [ ] 建议归属于具体发言者
- [ ] 包含最强调主题的总结

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the recommendations extraction task.

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

    report_path = workspace / "recommendations.md"
    if not report_path.exists():
        alternatives = ["recs.md", "panel_recommendations.md", "nasa_recommendations.md"]
        for alt in alternatives:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "recommendation_count": 0.0,
            "categorization": 0.0,
            "crowdsourcing": 0.0,
            "data_standards": 0.0,
            "sensor_eval": 0.0,
            "international": 0.0,
            "stigma": 0.0,
            "attribution": 0.0,
            "summary": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Count recommendations (bullet points, numbered items, or heading-based)
    bullet_items = len(re.findall(r'(?:^|\n)\s*[-*]\s+\S', content))
    numbered_items = len(re.findall(r'(?:^|\n)\s*\d+[\.\)]\s+\S', content))
    rec_count = max(bullet_items, numbered_items)
    scores["recommendation_count"] = 1.0 if rec_count >= 12 else (0.5 if rec_count >= 6 else 0.0)

    # Check categorization
    category_patterns = [
        r'data\s+collect', r'data\s+standard', r'sensor', r'partner',
        r'public\s+engage|stigma|outreach', r'scientific\s+method|methodology'
    ]
    cat_count = sum(1 for p in category_patterns if re.search(p, content_lower))
    scores["categorization"] = 1.0 if cat_count >= 4 else (0.5 if cat_count >= 2 else 0.0)

    # Check crowdsourcing
    crowd_patterns = [r'crowdsourc', r'citizen\s+science', r'public\s+(?:data|report|app)', r'smartphone|cell\s*phone|mobile']
    scores["crowdsourcing"] = 1.0 if sum(bool(re.search(p, content_lower)) for p in crowd_patterns) >= 2 else (0.5 if any(re.search(p, content_lower) for p in crowd_patterns) else 0.0)

    # Check data standards
    fair_patterns = [r'fair\b', r'findab', r'accessib', r'interoper', r'reusab', r'data\s+standard', r'data\s+quality', r'data\s+curation']
    scores["data_standards"] = 1.0 if sum(bool(re.search(p, content_lower)) for p in fair_patterns) >= 2 else (0.5 if any(re.search(p, content_lower) for p in fair_patterns) else 0.0)

    # Check sensor evaluation
    sensor_patterns = [r'ground.based\s+(?:sensor|instrument|scientific)', r'earth\s+(?:science|sensing)\s+satellite', r'purpose.built', r'dedicated\s+sensor', r'telescope|observator']
    scores["sensor_eval"] = 1.0 if sum(bool(re.search(p, content_lower)) for p in sensor_patterns) >= 2 else (0.5 if any(re.search(p, content_lower) for p in sensor_patterns) else 0.0)

    # Check international partnerships
    intl_patterns = [r'international', r'foreign\s+partner', r'five\s+eyes', r'artemis\s+accord', r'global\s+(?:partner|cooperat|collaborat)']
    scores["international"] = 1.0 if sum(bool(re.search(p, content_lower)) for p in intl_patterns) >= 2 else (0.5 if any(re.search(p, content_lower) for p in intl_patterns) else 0.0)

    # Check stigma reduction
    stigma_patterns = [r'stigma', r'destigma', r'harass', r'reporting.*barrier|barrier.*reporting', r'reluctan']
    scores["stigma"] = 1.0 if sum(bool(re.search(p, content_lower)) for p in stigma_patterns) >= 2 else (0.5 if any(re.search(p, content_lower) for p in stigma_patterns) else 0.0)

    # Check attribution
    named_speakers = set()
    for name in ['kirkpatrick', 'spergel', 'bianco', 'bontempi', 'drake', 'grinspoon', 'gold', 'fox', 'freie']:
        if name in content_lower:
            named_speakers.add(name)
    scores["attribution"] = 1.0 if len(named_speakers) >= 5 else (0.5 if len(named_speakers) >= 3 else 0.0)

    # Check summary
    summary_patterns = [r'summary|conclusion|key\s+theme|most\s+(?:emphasized|repeated|common)|overall|takeaway']
    scores["summary"] = 1.0 if any(re.search(p, content_lower) for p in summary_patterns) else 0.0

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Recommendation Extraction Completeness (Weight: 30%)

**Score 1.0**: 提取至少 15 个不同的、可操作的建议，涵盖数据收集、标准、传感器、合作伙伴关系、参与和方法论。没有遗漏主要建议。
**Score 0.75**: 10-14 个建议，涵盖大部分类别。
**Score 0.5**: 6-9 个建议，某些类别代表性不足。
**Score 0.25**: 少于 6 个建议或有重大遗漏。
**Score 0.0**: 未提取建议。

### Criterion 2: Categorization Quality (Weight: 20%)

**Score 1.0**: 建议清晰地归类到有意义的、不重叠的组中。类别直观且标签良好。
**Score 0.75**: 良好的分类，有轻微重叠或一个错误分类的项目。
**Score 0.5**: 类别存在但模糊或有明显重叠。
**Score 0.25**: 最小或混乱的分类。
**Score 0.0**: 没有分类。

### Criterion 3: Accuracy and Attribution (Weight: 30%)

**Score 1.0**: 建议准确反映了所说的话，正确归属于正确的发言者，并有适当的背景解释为什么提出每个建议。
**Score 0.75**: 大部分准确，有轻微的归属错误或背景缺失。
**Score 0.5**: 有一些不准确或缺少归属。
**Score 0.25**: 显著的不准确。
**Score 0.0**: 建议捏造或完全归属错误。

### Criterion 4: Synthesis and Summary (Weight: 20%)

**Score 1.0**: 总结识别出 2-3 个最强调的主题（例如，需要高质量数据、公民科学、减少污名），并指出哪些建议被多位发言者重复。
**Score 0.75**: 良好的总结，有轻微遗漏。
**Score 0.5**: 总结存在但肤浅。
**Score 0.25**: 最小的总结。
**Score 0.0**: 没有总结。

---

## Additional Notes

此任务测试 Agent 的能力：

- 提取通常嵌入在较长讨论中而不是明确陈述的建议
- 区分观察/描述和可操作的建议
- 识别多位发言者何时强化同一建议
- 跨不同发言者的贡献进行主题分类
- 从集体建议中综合最重要的主题

许多建议是隐含的而不是明确地框定为"我建议 X"。Agent 必须从上下文推断建议性意图（例如，"我认为 NASA 应该..."、"这将有助于..."、"我们需要..."）。
