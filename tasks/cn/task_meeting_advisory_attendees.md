---
id: task_meeting_advisory_attendees
name: NTIA 咨询委员会参会人员名单
category: 会议分析
scene: 数据库检索、表格整理与数据分析
sub_scene: 会议记录参会人员提取
difficulty: L2
capabilities:
- 数据提取与处理
- 指令遵循与约束理解
- 输出格式适配
- 多步推理
grading_type: hybrid
timeout_seconds: 180
grading_weights:
  automated: 0.6
  llm_judge: 0.4
workspace_files:
  - source: meetings/2012-05-30-meeting-transcript-ntia-csmac.md
    dest: meeting-transcript.md
---

## Prompt

我在 `meeting-transcript.md` 中有一份政府咨询委员会会议记录。这是商务部频谱管理咨询委员会（CSMAC）于 2012 年 5 月 30 日召开的会议。

请分析这份会议记录，并在名为 `attendees.md` 的文件中创建一份结构化的参会人员名单。对于每位参会者，请包含：

- **全名**（如有提及，附上头衔，例如 Dr.、Esq.）
- **会议中的角色**（主席、成员、列席人员、公众参与者）
- **组织与职务**（如会议记录中所述）
- **参会方式**（现场出席或电话/远程）
- **发言角色**（是否做了实质性发言、提出问题，或仅作自我介绍）

请将名单组织成以下几个部分：委员会领导层、委员会成员（现场出席）、委员会成员（远程）、非成员官员，以及公众参与者。请在结尾包含参会者总数的汇总统计。

---

## Expected Behavior

Agent 应当：

1. 阅读并解析会议记录
2. 从"Members Present"名单、"Also Present"部分及对话中识别所有具名个人
3. 根据星号标记（电话）和点名情况确定参会方式
4. 对每个人的角色和参与程度进行分类
5. 生成结构良好的 markdown 文档

预期的关键参会者：

- Dr. Brian Fontes（主席，NENA）— 现场出席
- Larry Strickling（商务部助理部长）— 现场出席，列席人员
- Karl Nebbia（频谱管理办公室副主任）— 现场出席，列席人员
- Tom Power（白宫 OSTP）— 现场出席，列席人员
- Bruce M. Washington（指定联邦官员）— 现场出席，列席人员
- Dale Hatfield（科罗拉多大学）— 远程（电话）
- Molly Feldman（Verizon Wireless）— 远程（电话）
- Doug McGinnis（Exelon）— 远程（电话）
- Dan Stancil（NC State）— 远程（电话）
- Rick Reaser（Raytheon）— 远程（电话）
- David Donovan — 远程（电话）
- Mr. Snider — 公众参与者（在公众评议环节发言）
- 委员会成员总数：约 19-20 人
- 包括官员和公众在内的参会者总数：约 23-24 人

---

## Grading Criteria

- [ ] 创建了文件 `attendees.md`
- [ ] 正确识别 Brian Fontes 为主席，隶属 NENA
- [ ] 按姓名识别出至少 15 位委员会成员
- [ ] 正确识别远程/电话参会者（Hatfield、Feldman、McGinnis、Stancil、Reaser、Donovan）
- [ ] 列出非成员官员（Strickling、Nebbia、Power、Washington）
- [ ] 为大多数参会者包含组织/隶属关系
- [ ] 正确标注参会方式（现场出席与电话）
- [ ] 将 Mr. Snider 识别为公众参与者
- [ ] 包含参会者总数汇总统计

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the meeting attendee list task.

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

    report_path = workspace / "attendees.md"
    if not report_path.exists():
        alternatives = ["attendee_list.md", "attendees_list.md", "meeting_attendees.md"]
        for alt in alternatives:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "chair_identified": 0.0,
            "member_count": 0.0,
            "remote_attendees": 0.0,
            "officials_listed": 0.0,
            "organizations_included": 0.0,
            "attendance_mode": 0.0,
            "public_participant": 0.0,
            "summary_count": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Check Chair identification
    chair_ok = (
        "fontes" in content_lower
        and ("chair" in content_lower)
        and re.search(r'nena|national emergency number', content_lower) is not None
    )
    scores["chair_identified"] = 1.0 if chair_ok else 0.0

    # Check member count (at least 15 of ~19 committee members named)
    members = [
        "fontes", "borth", "calabrese", "dombrowsky", "donovan",
        "feldman", "furchtgott", "gibson", "hatfield", "kahn",
        "mcginnis", "mchenry", "obuchowski", "povelites", "reaser",
        "rush", "stancil", "tramont", "warren"
    ]
    found = sum(1 for m in members if m in content_lower)
    scores["member_count"] = 1.0 if found >= 15 else (0.5 if found >= 10 else 0.0)

    # Check remote/phone attendees identified
    remote_members = ["hatfield", "feldman", "mcginnis", "stancil", "reaser", "donovan"]
    remote_found = 0
    for rm in remote_members:
        # Check if the member is mentioned near phone/remote/telephone keywords
        if rm in content_lower:
            # Look for phone/remote indicators near the name
            patterns = [
                rf'{rm}.*(?:phone|remote|virtual|telephone|dial)',
                rf'(?:phone|remote|virtual|telephone|dial).*{rm}',
            ]
            if any(re.search(p, content_lower) for p in patterns):
                remote_found += 1
            elif re.search(r'\*', content):
                # Asterisk convention mentioned
                remote_found += 0.5
    scores["remote_attendees"] = 1.0 if remote_found >= 4 else (0.5 if remote_found >= 2 else 0.0)

    # Check non-member officials
    officials = ["strickling", "nebbia", "power", "washington"]
    officials_found = sum(1 for o in officials if o in content_lower)
    scores["officials_listed"] = 1.0 if officials_found >= 3 else (0.5 if officials_found >= 2 else 0.0)

    # Check organizations included
    orgs = [
        "nena", "national emergency number",
        "verizon", "at&t", "att", "intel",
        "lockheed", "raytheon", "comsearch",
        "new america", "wiley rein", "wilkinson barker",
        "shared spectrum", "exelon", "ntia",
        "furchtgott-roth", "nc state", "north carolina",
        "colorado", "freedom technologies"
    ]
    org_found = sum(1 for o in orgs if o in content_lower)
    scores["organizations_included"] = 1.0 if org_found >= 10 else (0.5 if org_found >= 5 else 0.0)

    # Check attendance mode notation
    mode_patterns = [
        r'in[- ]person', r'on[- ]?site', r'physical',
        r'phone', r'remote', r'virtual', r'telephone', r'dial'
    ]
    mode_found = sum(1 for p in mode_patterns if re.search(p, content_lower))
    scores["attendance_mode"] = 1.0 if mode_found >= 2 else (0.5 if mode_found >= 1 else 0.0)

    # Check public participant (Snider)
    scores["public_participant"] = 1.0 if "snider" in content_lower else 0.0

    # Check summary count
    count_patterns = [
        r'total.*\d+', r'\d+.*total',
        r'(?:attendee|participant|member)s?.*\d+',
        r'\d+.*(?:attendee|participant|member)',
        r'count.*\d+', r'summary.*\d+'
    ]
    scores["summary_count"] = 1.0 if any(re.search(p, content_lower) for p in count_patterns) else 0.0

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Completeness of Attendee Identification (Weight: 35%)

**Score 1.0**：识别出所有委员会成员、官员和公众参与者，姓名和角色均正确。无遗漏。
**Score 0.75**：识别出大部分参会者（18 人以上），仅有轻微遗漏。
**Score 0.5**：识别出大多数人，但仍有若干参会者遗漏。
**Score 0.25**：仅识别出最突出的发言人。
**Score 0.0**：识别出的参会者不足半数。

### Criterion 2: Accuracy of Details (Weight: 30%)

**Score 1.0**：所有组织、职务和参会方式均正确。远程与现场出席状态与会议记录的星号标记和点名一致。
**Score 0.75**：大部分细节正确，仅有一到两处轻微错误。
**Score 0.5**：组织或参会方式存在若干错误。
**Score 0.25**：隶属关系或角色存在多处不准确。
**Score 0.0**：细节大体上不正确或属于虚构。

### Criterion 3: Organization and Structure (Weight: 20%)

**Score 1.0**：清晰区分领导层、现场成员、远程成员、官员和公众等各部分。易于浏览和查阅。
**Score 0.75**：组织良好，仅有轻微结构问题。
**Score 0.5**：有一定组织，但各部分不清晰或不一致。
**Score 0.25**：组织混乱，难以查阅。
**Score 0.0**：没有有意义的结构。

### Criterion 4: Speaking Role Assessment (Weight: 15%)

**Score 1.0**：准确区分活跃参与者（提出问题、做了发言）与仅在点名时作自我介绍的人。
**Score 0.75**：大部分发言角色标注正确。
**Score 0.5**：尝试标注参与程度，但不完整。
**Score 0.25**：区分参与程度的努力极少。
**Score 0.0**：未评估发言角色。

---

## Additional Notes

本任务测试 Agent 的以下能力：

- 从非结构化的会议记录中提取结构化信息
- 区分不同的参会类别和角色
- 交叉引用文档多个部分的信息（头部名单与对话）
- 处理远程参会者的星号标记惯例
- 识别一位公众参与者（Mr. Snider），他在接近结尾时发言，但不在正式成员名单中
