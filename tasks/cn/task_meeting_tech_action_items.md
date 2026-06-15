---
id: task_meeting_tech_action_items
name: 会议行动项提取
category: 会议分析
scene: 内容创作、PPT、网页与多媒体生成
sub_scene: 会议行动项提取
difficulty: L2
capabilities:
- 数据提取与处理
- 自然语言生成
- 指令遵循与约束理解
- 输出格式适配
- 多步推理
grading_type: hybrid
timeout_seconds: 180
grading_weights:
  automated: 0.6
  llm_judge: 0.4
workspace_files:
  - source: meetings/2021-06-28-gitlab-product-marketing-meeting.md
    dest: meeting_transcript.md
---

## Prompt

我有一个文件 `meeting_transcript.md`，包含 2021 年 6 月 28 日 GitLab 产品营销每周会议的记录。会议涵盖几个主题，包括企业活动、GitLab Commit 的产品公告、竞争分析、新的信息图设计和消息传递框架。

请从这次会议中提取所有行动项并将它们写入一个名为 `action_items.md` 的文件。对于每个行动项，包括：

- **负责人**（负责的人，按姓名）
- **行动**（他们需要做什么）
- **截止日期**（如果提及）
- **背景**（与哪个讨论主题相关）

按主题领域对行动项分组。同时在顶部包含行动项总数的汇总计数。

---

## Expected Behavior

Agent 应该：

1. 阅读并解析会议记录
2. 识别讨论中所有明确和隐含的行动项
3. 将每个行动项与正确的人员/负责人关联
4. 按主题对它们分组

应提取的关键行动项：

- **企业活动**：PMM 需要从他们的活动经理那里获得对特定活动的承诺（platform→re:Invent，CI/CD→Google Next，GitOps→KubeCon）并在 issue 上评论
- **产品公告**：Cormac 需要为 Plan 阶段添加前五名；团队成员需要审查并挑选总体前 5 个功能；这在周二到期
- **竞争分析**：Samia 需要仅使用与她的阶段相关的第一梯队竞争对手进行比较；团队需要向竞争表添加 GitLab 行项目
- **消息传递框架**：William 确定以"more speed less risk"作为选定标语来完成消息传递；当天结束前到期
- **一般**：团队应观看 Talladega Nights（幽默的家庭作业）

---

## Grading Criteria

- [ ] 创建了文件 `action_items.md`
- [ ] 识别出至少 5 个不同的行动项
- [ ] 行动项与具体负责人关联（例如，Cormac、Samia、William、Cindy）
- [ ] 捕捉企业活动行动项（获得活动经理承诺）
- [ ] 捕捉产品公告行动项（前 5 个功能，周二到期）
- [ ] 捕捉竞争分析行动项（第一梯队竞争对手，添加 GitLab 行）
- [ ] 捕捉消息传递框架行动项（确定标语，当天结束前到期）
- [ ] 行动项按主题或类别分组
- [ ] 在提及处注明截止日期（产品公告为周二，消息传递为当天结束前）

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the meeting action items extraction task.

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

    report_path = workspace / "action_items.md"
    if not report_path.exists():
        for alt in ["actions.md", "action-items.md", "meeting_actions.md"]:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "min_action_items": 0.0,
            "owners_identified": 0.0,
            "events_actions": 0.0,
            "announcements_actions": 0.0,
            "competitive_actions": 0.0,
            "messaging_actions": 0.0,
            "grouped_by_topic": 0.0,
            "deadlines_noted": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Check minimum number of action items (look for bullet points or numbered items)
    action_markers = re.findall(r'(?:^|\n)\s*(?:[-*•]|\d+[.)]) .+', content)
    scores["min_action_items"] = 1.0 if len(action_markers) >= 5 else (0.5 if len(action_markers) >= 3 else 0.0)

    # Check that owners are identified
    owners = ["cormac", "samia", "william", "cindy", "brian", "tai"]
    owner_count = sum(1 for o in owners if o in content_lower)
    scores["owners_identified"] = 1.0 if owner_count >= 3 else (0.5 if owner_count >= 2 else 0.0)

    # Corporate events actions
    events_patterns = [
        r'(?:campaign\s*manager|event|reinvent|google\s*next|kubecon)',
        r'(?:commit|sign\s*up|sponsor)',
    ]
    events_hits = sum(1 for p in events_patterns if re.search(p, content_lower))
    scores["events_actions"] = 1.0 if events_hits >= 2 else (0.5 if events_hits >= 1 else 0.0)

    # Product announcements actions
    announce_patterns = [
        r'(?:top\s*(?:five|5)|product\s*announce|feature)',
        r'(?:plan|cormac)',
    ]
    announce_hits = sum(1 for p in announce_patterns if re.search(p, content_lower))
    scores["announcements_actions"] = 1.0 if announce_hits >= 2 else (0.5 if announce_hits >= 1 else 0.0)

    # Competitive analysis actions
    competitive_patterns = [
        r'(?:tier\s*(?:one|1)|competitor)',
        r'(?:gitlab\s*(?:line|row|column)|add\s*gitlab)',
    ]
    competitive_hits = sum(1 for p in competitive_patterns if re.search(p, content_lower))
    scores["competitive_actions"] = 1.0 if competitive_hits >= 2 else (0.5 if competitive_hits >= 1 else 0.0)

    # Messaging framework actions
    messaging_patterns = [
        r'(?:messag|tagline|framework)',
        r'(?:more\s*speed\s*less\s*risk|finalize)',
    ]
    messaging_hits = sum(1 for p in messaging_patterns if re.search(p, content_lower))
    scores["messaging_actions"] = 1.0 if messaging_hits >= 2 else (0.5 if messaging_hits >= 1 else 0.0)

    # Check grouping by topic (look for headers or clear sections)
    headers = re.findall(r'(?:^|\n)#+\s+.+|(?:^|\n)\*\*.+\*\*', content)
    scores["grouped_by_topic"] = 1.0 if len(headers) >= 3 else (0.5 if len(headers) >= 2 else 0.0)

    # Check deadlines
    deadline_patterns = [r'tuesday', r'end\s*of\s*(?:the\s*)?day', r'due', r'deadline']
    deadline_hits = sum(1 for p in deadline_patterns if re.search(p, content_lower))
    scores["deadlines_noted"] = 1.0 if deadline_hits >= 2 else (0.5 if deadline_hits >= 1 else 0.0)

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Completeness of Action Item Extraction (Weight: 35%)

**Score 1.0**: 识别所有讨论主题（活动、公告、竞争、消息传递）中的所有主要行动项。捕捉明确的分配和隐含的承诺。
**Score 0.75**: 捕捉大部分行动项，但遗漏一两个次要项。
**Score 0.5**: 捕捉某些主题的行动项，但遗漏整个主题领域。
**Score 0.25**: 仅捕捉少数明显的行动项。
**Score 0.0**: 未提取有意义的行动项。

### Criterion 2: Owner Attribution Accuracy (Weight: 30%)

**Score 1.0**: 正确识别每个行动项的责任人。姓名根据对话背景准确归属。
**Score 0.75**: 大部分负责人正确识别，有一两个次要归属错误。
**Score 0.5**: 识别出一些负责人，但有几个错误或缺失。
**Score 0.25**: 负责人大部分缺失或错误归属。
**Score 0.0**: 未尝试负责人归属。

### Criterion 3: Organization and Structure (Weight: 20%)

**Score 1.0**: 行动项按主题清晰分组，格式一致，并包含汇总计数。易于浏览和用作后续检查清单。
**Score 0.75**: 组织良好，有轻微格式不一致。
**Score 0.5**: 有一定组织但项目跨主题混杂或难以理解。
**Score 0.25**: 最小组织，项目无分组列出。
**Score 0.0**: 没有结构或组织。

### Criterion 4: Context and Deadline Accuracy (Weight: 15%)

**Score 1.0**: 在提及处注明截止日期（公告为周二，消息传递为当天结束前）。每个行动项的背景准确且有帮助。
**Score 0.75**: 大部分截止日期和背景被捕捉，有轻微遗漏。
**Score 0.5**: 提供了一些背景，但截止日期缺失或不准确。
**Score 0.25**: 最小背景，无截止日期。
**Score 0.0**: 没有背景或截止日期信息。
