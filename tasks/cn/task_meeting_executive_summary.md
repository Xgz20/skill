---
id: task_meeting_executive_summary
name: 会议执行摘要
category: 会议分析
scene: 内容创作、PPT、网页与多媒体生成
sub_scene: 会议摘要生成
difficulty: L2
capabilities:
- 自然语言生成
- 数据提取与处理
- 指令遵循与约束理解
- 输出格式适配
- 幻觉抑制
grading_type: hybrid
timeout_seconds: 180
grading_weights:
  automated: 0.5
  llm_judge: 0.5
workspace_files:
  - source: meetings/2021-06-28-gitlab-product-marketing-meeting.md
    dest: meeting_transcript.md
---

## Prompt

我有一个文件 `meeting_transcript.md`，包含了2021年6月28日举行的GitLab产品营销团队会议的记录。请阅读会议记录并生成一份简明的执行摘要。

将您的摘要写入名为 `executive_summary.md` 的文件中。它应包括：

- **会议标题和日期**
- **与会者**（记录中提到的姓名）
- **讨论的关键主题**（3-5个要点总结主要讨论领域）
- **做出的决策**（团队达成的具体决定或结论）
- **行动事项**（分配给特定人员的任务，在可识别的情况下标注负责人）
- **后续步骤**（下次会议前需要完成的事项）

摘要应不超过约500字，并且应该为没有参加会议的忙碌高管撰写。

---

## Expected Behavior

Agent应该：

1. 阅读会议记录
2. 识别主要讨论主题：
   - 企业活动赞助分配（平台参加re:Invent，CI/CD参加Google Next，GitOps参加KubeCon）
   - Commit大会的产品发布公告（跨阶段的前5大功能）
   - 竞争对比信息图（来自设计团队的新设计，颜色决策）
   - 消息传递框架（如"more speed, less risk"和"single source of truth, countless possibilities"等标语）
   - 竞争对手电子表格方法（一级竞争对手，与阶段相关的比较）
3. 识别关键决策：
   - 活动分配：Platform→re:Invent，CI/CD→Google Next，GitOps→KubeCon
   - 消息传递："more speed, less risk"被选为最终标语
   - 竞争信息图：保持仅使用绿色（不用红色）
   - 漏洞管理作为首要安全公告
4. 提取行动事项（Cormac添加Plan的前5项，团队与活动经理确认等）
5. 撰写结构良好的执行摘要

---

## Grading Criteria

- [ ] 创建了文件 `executive_summary.md`
- [ ] 提到了会议日期（2021-06-28 或 June 28, 2021）
- [ ] 至少识别了3个关键主题
- [ ] 涵盖了企业活动/活动赞助主题
- [ ] 涵盖了产品公告/Commit大会主题
- [ ] 记录了至少2个具体决策
- [ ] 存在行动事项或后续步骤部分
- [ ] 摘要简明扼要（约800字以内）

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the meeting executive summary task.

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
    report_path = workspace / "executive_summary.md"
    if not report_path.exists():
        alternatives = ["exec_summary.md", "summary.md", "meeting_summary.md"]
        for alt in alternatives:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "file_created": 0.0,
            "meeting_date": 0.0,
            "topics_identified": 0.0,
            "events_covered": 0.0,
            "announcements_covered": 0.0,
            "decisions_documented": 0.0,
            "action_items_present": 0.0,
            "concise": 0.0,
        }

    scores["file_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Check meeting date
    date_patterns = [r'2021-06-28', r'june\s*28', r'6/28/2021', r'28\s*june\s*2021']
    scores["meeting_date"] = 1.0 if any(re.search(p, content_lower) for p in date_patterns) else 0.0

    # Count key topics identified
    topic_count = 0
    if re.search(r'(?:corporate\s*event|event\s*sponsor|re:?\s*invent|kubecon|google\s*next)', content_lower):
        topic_count += 1
    if re.search(r'(?:product\s*announce|commit\s*(?:conference|event)|top\s*(?:5|five)\s*feature)', content_lower):
        topic_count += 1
    if re.search(r'(?:competitive|infographic|comparison)', content_lower):
        topic_count += 1
    if re.search(r'(?:messaging\s*framework|tagline|more\s*speed|single\s*source\s*of\s*truth)', content_lower):
        topic_count += 1
    if re.search(r'(?:vulnerability\s*management|security\s*announce)', content_lower):
        topic_count += 1
    scores["topics_identified"] = 1.0 if topic_count >= 3 else (0.5 if topic_count >= 2 else 0.0)

    # Events coverage
    events_patterns = [
        r're:?\s*invent',
        r'google\s*next',
        r'kubecon',
        r'event\s*(?:sponsor|support|assign)',
    ]
    scores["events_covered"] = 1.0 if sum(1 for p in events_patterns if re.search(p, content_lower)) >= 2 else 0.0

    # Product announcements coverage
    announce_patterns = [
        r'commit',
        r'product\s*announce',
        r'top\s*(?:5|five)',
        r'vulnerability\s*management',
        r'kubernetes\s*agent',
    ]
    scores["announcements_covered"] = 1.0 if sum(1 for p in announce_patterns if re.search(p, content_lower)) >= 2 else 0.0

    # Decisions documented
    decision_count = 0
    if re.search(r'more\s*speed.*less\s*risk', content_lower):
        decision_count += 1
    if re.search(r'(?:green|no\s*red|color)', content_lower):
        decision_count += 1
    if re.search(r'vulnerability\s*management', content_lower):
        decision_count += 1
    if re.search(r'(?:platform.*re:?\s*invent|ci.*cd.*google|gitops.*kubecon)', content_lower):
        decision_count += 1
    scores["decisions_documented"] = 1.0 if decision_count >= 2 else (0.5 if decision_count >= 1 else 0.0)

    # Action items present
    action_patterns = [
        r'action\s*item',
        r'next\s*step',
        r'follow[\s-]*up',
        r'(?:need|should|will|to)\s*(?:do|complete|confirm|add|update|review)',
        r'assign(?:ed|ment)',
        r'(?:cormac|cindy|brian|samia|william).*(?:will|to|should)',
    ]
    scores["action_items_present"] = 1.0 if sum(1 for p in action_patterns if re.search(p, content_lower)) >= 2 else 0.0

    # Conciseness check (under ~800 words)
    word_count = len(content.split())
    scores["concise"] = 1.0 if word_count <= 800 else (0.5 if word_count <= 1200 else 0.0)

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Accuracy and Completeness (Weight: 40%)

**Score 1.0**: 摘要准确捕获了所有主要讨论主题（企业活动、产品公告、竞争信息图、消息传递框架），关键决策和行动事项，且没有引入虚假信息。
**Score 0.75**: 大多数主题和决策被准确捕获，有一两处次要遗漏。
**Score 0.5**: 核心主题存在但缺少几个重要细节或不准确。
**Score 0.25**: 仅涵盖少数主题或存在重大不准确之处。
**Score 0.0**: 摘要缺失、为空或根本不准确。

### Criterion 2: Executive Readability (Weight: 30%)

**Score 1.0**: 摘要简明扼要，结构清晰，使用专业语言，忙碌的高管能在2分钟内掌握要点。没有来自随意对话语气的不必要细节。
**Score 0.75**: 摘要可读且组织良好，略显冗长。
**Score 0.5**: 摘要存在但过于详细、组织混乱或难以快速浏览。
**Score 0.25**: 摘要杂乱无章或更像原始笔记而非高管简报。
**Score 0.0**: 没有摘要或格式完全不可用。

### Criterion 3: Actionability (Weight: 30%)

**Score 1.0**: 决策清晰陈述，行动事项在可识别的情况下标注了负责人，后续步骤具体到可以采取行动。阅读此文档的人能准确知道做出了什么决定以及接下来会发生什么。
**Score 0.75**: 大多数决策和行动事项清晰，在负责权或具体性方面有轻微缺口。
**Score 0.5**: 存在一些决策或行动事项但模糊或缺少上下文。
**Score 0.25**: 行动事项基本缺失或过于模糊而无用。
**Score 0.0**: 从会议中未提取任何可操作内容。

---

## Additional Notes

此任务测试Agent的能力：

- 处理带有对话语言的长篇非正式会议记录
- 从随意讨论中提炼关键业务决策
- 识别特定人员及其承诺
- 从非正式源材料生成专业的执行摘要
- 在保持简洁的同时维持准确性

该记录来自真实的GitLab产品营销会议，具有非正式语气、离题讨论（Talladega Nights、学校集会）和重叠对话。Agent必须将信号与噪音分离。
