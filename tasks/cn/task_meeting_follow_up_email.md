---
id: task_meeting_follow_up_email
name: 会议跟进邮件
category: 会议分析
scene: 内容创作、PPT、网页与多媒体生成
sub_scene: 会议跟进邮件
difficulty: L2
capabilities:
- 数据提取与处理
- 自然语言生成
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

我有一个文件 `meeting_transcript.md`，包含了2021年6月28日举行的GitLab产品营销团队会议的记录。请起草一封专业的跟进邮件，可以在会议后发送给团队。

将邮件写入名为 `follow_up_email.md` 的文件中。邮件应包括：

- **主题行**
- **问候语**，称呼产品营销团队
- **简要回顾**讨论内容（最多2-3句话）
- **做出的决策**（清晰的编号列表）
- **行动事项**，在可识别的情况下标注负责人和截止日期
- **待解决事项**，仍需解决的问题
- **结束语**，包含任何相关的下次会议信息或截止日期

邮件应该专业但符合团队的协作语气。保持简洁——忙碌的团队成员应该能在一分钟内浏览完毕。

---

## Expected Behavior

Agent应该：

1. 阅读会议记录
2. 起草一封邮件，捕获：
   - **决策：**
     - 活动分配：Platform→re:Invent，CI/CD→Google Next，GitOps→KubeCon
     - 消息传递标语："more speed, less risk"被选中
     - 竞争信息图：保持仅使用绿色配色方案
     - 首选公告：漏洞管理作为主要安全故事
     - 集会标语："single source of truth, countless possibilities"
   - **行动事项：**
     - 所有人：与活动经理确认活动承诺，在issue上评论
     - Cormac：为Plan阶段添加前5大功能
     - 团队：完成产品公告电子表格条目（截止周二）
     - Samia：调整竞争对手表格，每个阶段仅使用相关的一级竞争对手
     - 在竞争对比中添加GitLab作为条目
   - **待解决事项：**
     - 所有阶段的最终前5大产品公告
     - 是否将UX改进作为重点类别
     - 具体包含哪些VS Code集成功能
3. 撰写清晰、易浏览的邮件

---

## Grading Criteria

- [ ] 创建了文件 `follow_up_email.md`
- [ ] 有主题行
- [ ] 包含决策或关键成果部分
- [ ] 列出了至少3个具体决策
- [ ] 包含行动事项，至少有一些负责人姓名
- [ ] 列出了至少3个行动事项
- [ ] 提到了周二截止日期
- [ ] 专业但亲和的语气
- [ ] 简洁（约600字以内）

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the meeting follow-up email task.

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

    # Check if file exists
    report_path = workspace / "follow_up_email.md"
    if not report_path.exists():
        alternatives = ["followup_email.md", "follow_up.md", "email.md", "meeting_followup.md"]
        for alt in alternatives:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "file_created": 0.0,
            "has_subject": 0.0,
            "decisions_section": 0.0,
            "decisions_count": 0.0,
            "action_items_with_owners": 0.0,
            "action_items_count": 0.0,
            "deadline_mentioned": 0.0,
            "tone_appropriate": 0.0,
            "concise": 0.0,
        }

    scores["file_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Subject line
    subject_patterns = [r'subject\s*:', r're\s*:', r'^#\s*.*(?:follow|recap|summary)', r'\*\*subject\*\*']
    scores["has_subject"] = 1.0 if any(re.search(p, content_lower, re.MULTILINE) for p in subject_patterns) else 0.0

    # Decisions section
    decision_section_patterns = [r'decision', r'key\s*outcome', r'(?:what\s*we\s*)?(?:agreed|decided)', r'outcome', r'conclusion']
    scores["decisions_section"] = 1.0 if any(re.search(p, content_lower) for p in decision_section_patterns) else 0.0

    # Count specific decisions
    decision_count = 0
    if re.search(r'(?:platform|re:?\s*invent)', content_lower):
        decision_count += 1
    if re.search(r'(?:ci.*cd|google\s*next)', content_lower):
        decision_count += 1
    if re.search(r'(?:gitops|kubecon)', content_lower):
        decision_count += 1
    if re.search(r'more\s*speed.*less\s*risk', content_lower):
        decision_count += 1
    if re.search(r'(?:green|no\s*red|color\s*scheme)', content_lower):
        decision_count += 1
    if re.search(r'vulnerability\s*management', content_lower):
        decision_count += 1
    scores["decisions_count"] = 1.0 if decision_count >= 3 else (0.5 if decision_count >= 2 else 0.0)

    # Action items with owners (names from the meeting)
    names = ['cormac', 'cindy', 'brian', 'samia', 'william', 'tai']
    names_found = sum(1 for n in names if n in content_lower)
    action_patterns = [r'action\s*item', r'to[\s-]*do', r'(?:will|should|needs?\s*to|please)\s+\w+']
    has_actions = any(re.search(p, content_lower) for p in action_patterns)
    scores["action_items_with_owners"] = 1.0 if (names_found >= 2 and has_actions) else (0.5 if names_found >= 1 or has_actions else 0.0)

    # Count action items (look for list items in action section)
    action_list_items = re.findall(r'(?:^|\n)\s*[-*•\d]+[.)]\s*.{10,}', content)
    scores["action_items_count"] = 1.0 if len(action_list_items) >= 5 else (0.5 if len(action_list_items) >= 3 else 0.0)

    # Tuesday deadline mentioned
    deadline_patterns = [r'tuesday', r'due\s*(?:date|by|end\s*of)', r'deadline', r'end\s*of\s*(?:the\s*)?day']
    scores["deadline_mentioned"] = 1.0 if any(re.search(p, content_lower) for p in deadline_patterns) else 0.0

    # Tone (professional but approachable - look for greeting and closing)
    has_greeting = bool(re.search(r'(?:hi|hey|hello|dear|team|everyone|all)', content_lower[:200]))
    has_closing = bool(re.search(r'(?:thanks|thank\s*you|best|regards|cheers|talk\s*soon)', content_lower[-300:]))
    scores["tone_appropriate"] = 1.0 if (has_greeting and has_closing) else (0.5 if (has_greeting or has_closing) else 0.0)

    # Conciseness
    word_count = len(content.split())
    scores["concise"] = 1.0 if word_count <= 600 else (0.5 if word_count <= 900 else 0.0)

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Accuracy of Content (Weight: 35%)

**Score 1.0**: 邮件准确捕获了会议中的决策、行动事项和待解决问题。没有虚构的承诺或错误的归属。活动分配、标语选择和竞争方法都正确呈现。
**Score 0.75**: 大多数内容准确，有一两处次要错误或遗漏。
**Score 0.5**: 核心决策存在但有几个项目不准确或缺少关键项目。
**Score 0.25**: 重大不准确或主要遗漏削弱了可用性。
**Score 0.0**: 邮件缺失、为空或根本不准确。

### Criterion 2: Email Format and Professionalism (Weight: 30%)

**Score 1.0**: 读起来像PMM负责人会发送的真实跟进邮件。有适当的主题行、问候语、结构化正文（包含可浏览的决策、行动事项、待解决事项部分）和专业的结束语。符合团队协作但直接的语气。
**Score 0.75**: 良好的邮件格式，有轻微结构问题。
**Score 0.5**: 包含正确信息但读起来不像自然的邮件。
**Score 0.25**: 格式差或语气不恰当（过于正式/非正式）。
**Score 0.0**: 无法识别为邮件。

### Criterion 3: Actionability and Clarity (Weight: 35%)

**Score 1.0**: 收到此邮件的团队成员能准确知道做出了什么决策、他们个人需要做什么以及何时到期。行动事项具体且有归属。对后续步骤没有歧义。
**Score 0.75**: 大部分清晰可行，有轻微歧义。
**Score 0.5**: 存在一些行动事项但缺乏具体性或明确的负责权。
**Score 0.25**: 对接下来需要发生的事情模糊或不清楚。
**Score 0.0**: 没有可操作内容。

---

## Additional Notes

此任务测试Agent的能力：

- 将非正式会议记录转化为专业商业沟通
- 识别并将行动事项归属于特定人员
- 保持适当的语气（专业但符合团队文化）
- 为可浏览性优先排列信息
- 从随意对话中提取截止日期和承诺

会议具有轻松、随意的语气，带有玩笑和离题内容。Agent必须将此过滤成专业邮件，同时保留团队的协作精神。关键挑战：在重叠对话中识别谁承诺了什么。
