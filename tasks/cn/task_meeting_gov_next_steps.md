---
id: task_meeting_gov_next_steps
name: NASA UAP听证会后续步骤提取
category: 会议分析
scene: 内容创作、PPT、网页与多媒体生成
sub_scene: 会议行动事项提取
difficulty: L2
capabilities:
- 数据提取与处理
- 指令遵循与约束理解
- 多步推理
- 自然语言生成
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

我有一个记录文件 `transcript.md`，来自NASA关于不明异常现象（UAPs/UFOs）的首次公开会议。这是一次审议性会议，在小组最终报告之前还有几个月的工作要做。

请阅读记录并将所有提到的后续步骤、跟进行动、时间线和可交付成果提取到名为 `next_steps.md` 的文件中。对于每个项目，包括：

- **行动事项**（需要发生什么）
- **负责方**（预期由谁完成——NASA、AARO、小组、FAA等）
- **时间线**（如果提到，预期何时）
- **状态**（提到的是计划中、进行中还是已完成）
- **来源**（谁在会议中提到的）

组织成以下部分：即时后续步骤（数周）、近期行动（数月）、长期目标（持续/数年）和待解决问题（提出但没有明确跟进分配的项目）。最后包含一个时间线可视化，显示关键里程碑。

---

## Expected Behavior

Agent应该：

1. 阅读并解析完整记录
2. 识别所有关于行动、可交付成果和时间线的前瞻性陈述
3. 区分承诺的行动和愿景性目标
4. 注意哪些项目有具体时间线，哪些时间模糊

关键后续步骤和跟进行动：

**即时（数周）：**
- 小组在本次会议后继续审议"几个月"（Evans）
- AARO年度报告截止8月1日提交国会，包含更新的案例数量（Kirkpatrick）
- AARO在首次论坛后建立五眼数据共享协议（Kirkpatrick）

**近期（数月）：**
- 小组最终报告将"今年夏天"/"7月底前"发布（Evans、Spergel）
- 报告发布在NASA网站上（Evans）
- 报告首先提交给地球科学咨询委员会，然后正式传达给政府（Evans）
- AARO发布关于"进入水中"传感器异常案例的调查结果（Kirkpatrick）
- AARO在特定区域部署专用传感器进行监视（Kirkpatrick）
- NASA欢迎AARO嵌入人员（Pritar）帮助制定科学计划（Kirkpatrick）
- 在science.nasa.gov上发布额外的问答答案（Spergel）

**长期（持续）：**
- AARO在热点地区进行24/7收集监控活动，一次持续3个月（Kirkpatrick）
- AARO针对已知物体校准国防部传感器（在各种条件下用F-35对抗气象气球飞行）（Kirkpatrick）
- AARO为案例持有开发AI/ML分析（Kirkpatrick）
- 建立超越五眼的国际科学伙伴关系（Kirkpatrick、Gold）
- 开发公民科学众包平台（Bianco、Spergel）
- NASA在收到小组建议后确定预算分配（Evans）

**待解决问题（提出但未解决）：**
- 小组范围是包括水下/太空领域还是专注于空中（小组辩论）
- 如何为科学目的精确定义"异常"（Drake、Kirkpatrick讨论）
- 如何收集FAA原始雷达数据而不仅仅是处理/过滤后的数据（Reggie建议；Freie指出"可行但并非没有技术挑战"）
- 如何将众包平台连接到实时跟进观测（Bianco讨论）
- NASA是否将建立专门资金的正式UAP项目（Evans："现在说还为时过早"）

---

## Grading Criteria

- [ ] 创建了输出文件 `next_steps.md`
- [ ] 提到了小组最终报告时间线（夏天/7月底）
- [ ] 提到了AARO年度报告8月1日截止
- [ ] 提到了AARO传感器部署计划
- [ ] 提到了五眼数据共享
- [ ] 注明了预算/项目状态（未建立正式项目）
- [ ] 至少识别了一个待解决问题
- [ ] 项目按时间框架组织
- [ ] 至少为5个项目识别了负责方
- [ ] 包含了时间线可视化或里程碑摘要

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the next steps extraction task.

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

    report_path = workspace / "next_steps.md"
    if not report_path.exists():
        alternatives = ["action_items.md", "follow_up.md", "followup.md", "actions.md"]
        for alt in alternatives:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "final_report_timeline": 0.0,
            "aaro_annual_report": 0.0,
            "sensor_deployment": 0.0,
            "five_eyes": 0.0,
            "budget_status": 0.0,
            "open_questions": 0.0,
            "timeframe_org": 0.0,
            "responsible_parties": 0.0,
            "timeline_viz": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Final report timeline
    report_patterns = [r'final\s+report', r'report.*summer|summer.*report', r'end\s+of\s+july|july', r'publish.*website']
    scores["final_report_timeline"] = 1.0 if sum(bool(re.search(p, content_lower)) for p in report_patterns) >= 2 else (0.5 if any(re.search(p, content_lower) for p in report_patterns) else 0.0)

    # AARO annual report
    aaro_report_patterns = [r'aaro.*annual\s+report|annual\s+report.*aaro', r'august\s+1|august\s+first', r'report.*congress|congress.*report']
    scores["aaro_annual_report"] = 1.0 if sum(bool(re.search(p, content_lower)) for p in aaro_report_patterns) >= 1 else 0.0

    # Sensor deployment
    sensor_patterns = [r'purpose.built\s+sensor', r'dedicated\s+sensor', r'deploy.*sensor|sensor.*deploy', r'surveillance.*area|hotspot']
    scores["sensor_deployment"] = 1.0 if sum(bool(re.search(p, content_lower)) for p in sensor_patterns) >= 1 else 0.0

    # Five Eyes
    five_patterns = [r'five\s+eyes', r'uk.*canada.*australia', r'intelligence.*partner|partner.*intelligence']
    scores["five_eyes"] = 1.0 if any(re.search(p, content_lower) for p in five_patterns) else 0.0

    # Budget status
    budget_patterns = [r'no\s+(?:associated\s+)?(?:programmatic\s+)?fund', r'not\s+established\s+a\s+program', r'no\s+formal\s+(?:program|budget)', r'too\s+early\s+to\s+say', r'budget.*complex|complex.*budget']
    scores["budget_status"] = 1.0 if sum(bool(re.search(p, content_lower)) for p in budget_patterns) >= 1 else (0.5 if re.search(r'budget|fund', content_lower) else 0.0)

    # Open questions
    open_patterns = [r'open\s+question', r'unresolved', r'unclear|undefined', r'debate|debated', r'tbd|to\s+be\s+determined']
    has_open = any(re.search(p, content_lower) for p in open_patterns)
    # Also check for content about scope debate or definition of anomalous
    has_scope = bool(re.search(r'scope.*aerial.*anomalous|aerial.*anomalous.*scope|domain.*debate', content_lower))
    has_definition = bool(re.search(r'defin.*anomalous|anomalous.*defin', content_lower))
    scores["open_questions"] = 1.0 if has_open and (has_scope or has_definition) else (0.5 if has_open else 0.0)

    # Timeframe organization
    time_patterns = [r'immediate', r'short.term', r'near.term', r'long.term', r'ongoing', r'weeks', r'months', r'years']
    time_count = sum(1 for p in time_patterns if re.search(p, content_lower))
    scores["timeframe_org"] = 1.0 if time_count >= 3 else (0.5 if time_count >= 2 else 0.0)

    # Responsible parties
    parties = set()
    for party in ['nasa', 'aaro', 'panel', 'faa', 'congress', 'kirkpatrick', 'spergel', 'evans', 'department']:
        if party in content_lower:
            parties.add(party)
    scores["responsible_parties"] = 1.0 if len(parties) >= 5 else (0.5 if len(parties) >= 3 else 0.0)

    # Timeline visualization
    viz_patterns = [r'timeline', r'milestone', r'gantt', r'roadmap', r'schedule']
    has_viz = any(re.search(p, content_lower) for p in viz_patterns)
    has_dates = len(re.findall(r'(?:july|august|summer|2023|q[1-4])', content_lower)) >= 2
    scores["timeline_viz"] = 1.0 if has_viz and has_dates else (0.5 if has_viz or has_dates else 0.0)

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Action Item Completeness (Weight: 30%)

**Score 1.0**: 提取了至少12个不同的后续步骤/行动事项，跨所有时间框架。包括承诺的可交付成果（小组报告、AARO年度报告）和愿景性目标（众包平台、国际伙伴关系）。没有遗漏主要项目。
**Score 0.75**: 跨多个时间框架提取了8-11个项目。
**Score 0.5**: 提取了5-7个项目但缺少一些时间框架。
**Score 0.25**: 少于5个项目。
**Score 0.0**: 未提取行动事项。

### Criterion 2: Timeline and Specificity (Weight: 25%)

**Score 1.0**: 注明了提到的具体时间线（8月1日，7月底，"今年夏天"）。清楚区分了有明确截止日期的项目与时间模糊的项目与持续努力。准确分配了负责方。
**Score 0.75**: 良好的时间线细节，有轻微缺口。
**Score 0.5**: 注明了一些时间线但缺少具体信息。
**Score 0.25**: 时间线始终模糊。
**Score 0.0**: 无时间线信息。

### Criterion 3: Open Questions and Gaps (Weight: 25%)

**Score 1.0**: 识别了未解决的问题，包括：范围定义（空中vs异常）、"异常"的定义、预算承诺、原始数据收集可行性和众包实施细节。注意到研究建议与行动承诺之间的差距。
**Score 0.75**: 识别了大多数待解决问题。
**Score 0.5**: 注明了一些待解决问题。
**Score 0.25**: 很少或没有待解决问题。
**Score 0.0**: 缺少待解决问题部分。

### Criterion 4: Organization and Visualization (Weight: 20%)

**Score 1.0**: 按时间框架组织良好，部分清晰。包含时间线可视化或里程碑摘要，使时间关系清晰。易于用作参考文档。
**Score 0.75**: 良好的组织，有基本时间线。
**Score 0.5**: 按时间框架组织但无可视化。
**Score 0.25**: 组织混乱。
**Score 0.0**: 无组织。

---

## Additional Notes

此任务测试Agent的能力：

- 从会议讨论中提取前瞻性承诺
- 区分明确承诺和愿景性陈述
- 识别治理流程（小组→地球科学咨询委员会→政府）
- 识别仍未解决的待解决问题
- 以对跟进追踪有用的方式呈现行动事项

记录讨论了许多潜在的未来行动。Agent必须区分已经进行的事项（AARO校准测试）、计划的事项（年度报告）、建议的事项（众包平台）和未解决提出的事项（范围辩论）。
