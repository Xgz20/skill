---
id: task_meeting_gov_qa_extract
name: NASA UAP 听证会问答提取
category: 会议分析
scene: 数据库检索、表格整理与数据分析
sub_scene: 会议记录问答提取
difficulty: L2
capabilities:
- 数据提取与处理
- 自然语言生成
- 输出格式适配
- 指令遵循与约束理解
- 上下文记忆与状态管理
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

我有一个文件 `transcript.md`，这是 NASA 首次关于不明异常现象（UAP/UFO）公开会议的记录。会议包括多个演讲，随后是小组成员与演讲者之间的问答交流，以及一个精选的公众问答环节。

请阅读记录并将所有问答交流提取到一个名为 `qa_exchanges.md` 的文件中。对于每个交流，包括：

- **提问者**（姓名和角色，如果已知）
- **回答者**（姓名和角色，如果已知）
- **主题**（简短标签，例如"数据校准"、"传感器限制"）
- **问题**（总结或引用）
- **答案**（总结关键点）

按时间顺序组织交流。将小组对演讲者的问答与会议后期发生的精选公众问答环节分开。为每个交流顺序编号。

---

## Expected Behavior

Agent 应该：

1. 阅读并解析完整记录
2. 识别与准备好的演讲不同的问答交流
3. 提取小组内部问题和精选公众问答环节
4. 准确地将问题和答案归属于正确的发言者
5. 简洁地总结问题和答案

关键问答交流包括：

- Spergel 向 Fox 询问 NASA 数据校准流程
- Bontempi 向 Spergel 询问跨科学挑战的数据质量
- Gold 向 Spergel 询问宇宙学中的高风险/高回报研究
- Drake 向 Kirkpatrick 询问具体数字（数据库规模、年份、"少数"的定义）
- Fox 向 Kirkpatrick 询问解密的 P-3 视频细节
- Walter 向 Kirkpatrick 询问传感器伪影和数据处理
- Berea 向 Kirkpatrick 询问 AI/ML 技术
- Gold 向 Kirkpatrick 询问什么使某事物异常 + 污名影响
- Walter 向 Freie 询问雷达数据保留和操作模式
- Bianco 向 Freie 询问报告偏差和传感器部署决策
- Wright 向 Freie 询问非合作监视异常
- Gold 向 Freie 询问飞行员报告流程和存档
- 公众问答：非人类智能证据、NASA 的 UAP 预算、地外生命发现协议

---

## Grading Criteria

- [ ] 创建了输出文件 `qa_exchanges.md`
- [ ] 识别出至少 10 个不同的问答交流
- [ ] 小组对演讲者的问答与公众问答部分分开
- [ ] 包含 Drake 向 Kirkpatrick 询问数据库数字的问题
- [ ] 包含 Kirkpatrick 关于 800+ 案例和 2-5% 异常的回答
- [ ] 包含至少一个与 FAA 相关的问答交流
- [ ] 包含关于非人类智能/地外起源的公众问答
- [ ] 问题和答案正确归属于指定发言者
- [ ] 交流已编号或清晰划分

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the Q&A extraction task.

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

    report_path = workspace / "qa_exchanges.md"
    if not report_path.exists():
        alternatives = ["qa.md", "questions_answers.md", "q_and_a.md", "qa_extract.md"]
        for alt in alternatives:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "exchange_count": 0.0,
            "section_separation": 0.0,
            "drake_kirkpatrick": 0.0,
            "case_numbers": 0.0,
            "faa_qa": 0.0,
            "nhi_question": 0.0,
            "attribution": 0.0,
            "numbering": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Count exchanges (look for numbered items or Q/A patterns)
    exchange_patterns = re.findall(r'(?:^|\n)\s*(?:\d+[\.\):]|#{2,3}\s*(?:exchange|q&?a|question))', content_lower)
    questioner_patterns = re.findall(r'question(?:er)?|asked|q:', content_lower)
    scores["exchange_count"] = 1.0 if len(exchange_patterns) >= 10 or len(questioner_patterns) >= 10 else (0.5 if len(exchange_patterns) >= 5 or len(questioner_patterns) >= 5 else 0.0)

    # Check section separation (panel Q&A vs public Q&A)
    has_sections = bool(re.search(r'public\s+q\s*&?\s*a|curated|audience|submitted', content_lower))
    has_panel = bool(re.search(r'panel|presenter|presentation', content_lower))
    scores["section_separation"] = 1.0 if has_sections and has_panel else (0.5 if has_sections or has_panel else 0.0)

    # Check Drake-Kirkpatrick exchange
    has_drake = bool(re.search(r'drake', content_lower))
    has_kirk = bool(re.search(r'kirkpatrick', content_lower))
    has_numbers_q = bool(re.search(r'how\s+(?:big|many|large)|database|number', content_lower))
    scores["drake_kirkpatrick"] = 1.0 if has_drake and has_kirk and has_numbers_q else (0.5 if has_drake and has_kirk else 0.0)

    # Check case numbers in response
    has_800 = bool(re.search(r'800|eight\s+hundred', content_lower))
    has_pct = bool(re.search(r'2.{0,5}5\s*%|single.digit|percent', content_lower))
    scores["case_numbers"] = 1.0 if has_800 and has_pct else (0.5 if has_800 or has_pct else 0.0)

    # Check FAA Q&A
    has_faa_qa = bool(re.search(r'faa|freie', content_lower))
    faa_topics = sum([
        bool(re.search(r'radar\s+data|retain|retention', content_lower)),
        bool(re.search(r'filter', content_lower)),
        bool(re.search(r'report.*process|pilot.*report', content_lower)),
        bool(re.search(r'deploy|coverage|site', content_lower)),
    ])
    scores["faa_qa"] = 1.0 if has_faa_qa and faa_topics >= 2 else (0.5 if has_faa_qa else 0.0)

    # Check non-human intelligence question
    nhi_patterns = [
        r'non.?human\s+intelligence',
        r'extraterrestrial\s+(?:origin|life|intelligence)',
        r'alien',
        r'extraordinary\s+claims.*extraordinary\s+evidence',
    ]
    scores["nhi_question"] = 1.0 if sum(bool(re.search(p, content_lower)) for p in nhi_patterns) >= 2 else (0.5 if any(re.search(p, content_lower) for p in nhi_patterns) else 0.0)

    # Check attribution (multiple named speakers in Q&A context)
    named_speakers = set()
    for name in ['drake', 'kirkpatrick', 'spergel', 'fox', 'freie', 'gold', 'walter', 'bianco', 'bontempi', 'wright', 'grinspoon', 'berea']:
        if name in content_lower:
            named_speakers.add(name)
    scores["attribution"] = 1.0 if len(named_speakers) >= 6 else (0.5 if len(named_speakers) >= 3 else 0.0)

    # Check numbering/delineation
    numbered = len(re.findall(r'(?:^|\n)\s*\d+[\.\):]', content)) >= 5
    headed = len(re.findall(r'(?:^|\n)#{2,4}\s', content)) >= 5
    separated = len(re.findall(r'(?:^|\n)---', content)) >= 3
    scores["numbering"] = 1.0 if numbered or headed else (0.5 if separated else 0.0)

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Exchange Completeness (Weight: 30%)

**Score 1.0**: 提取至少 12 个不同的问答交流，涵盖所有主要演讲问答环节和公众问答。没有遗漏重要交流。
**Score 0.75**: 提取 8-11 个交流，涵盖大部分环节。
**Score 0.5**: 提取 5-7 个交流但遗漏了一些关键交流。
**Score 0.25**: 少于 5 个交流或有重大遗漏。
**Score 0.0**: 未提取交流。

### Criterion 2: Accuracy of Attribution (Weight: 25%)

**Score 1.0**: 所有问题和答案正确归属于正确的发言者，姓名和角色准确。
**Score 0.75**: 大部分归属正确，有一两个错误。
**Score 0.5**: 有几个归属错误或缺少姓名。
**Score 0.25**: 频繁的归属错误。
**Score 0.0**: 没有归属或完全错误。

### Criterion 3: Summary Quality (Weight: 25%)

**Score 1.0**: 问题和答案都被简洁准确地总结，捕捉到了本质信息，没有不必要的冗长。保留了关键细节，如具体数字、例子和结论。
**Score 0.75**: 良好的总结，有轻微遗漏。
**Score 0.5**: 总结存在但遗漏关键细节或过于模糊。
**Score 0.25**: 总结质量差。
**Score 0.0**: 没有总结或只是没有上下文的原始引用。

### Criterion 4: Organization (Weight: 20%)

**Score 1.0**: 按时间顺序清晰组织，小组问答和公众问答分开。每个交流都编号并包含主题标签。易于参考。
**Score 0.75**: 良好的组织，有轻微问题。
**Score 0.5**: 有一定组织但部分混杂或难以浏览。
**Score 0.25**: 组织混乱。
**Score 0.0**: 没有可辨识的组织。

---

## Additional Notes

此任务测试 Agent 的能力：

- 在记录中区分问答交流与准备好的发言
- 准确归属多方对话
- 简洁地总结问题和答案
- 识别从小组讨论到精选公众问题的转换
- 处理发言者中断或问题跨多个回合的情况

记录有两种不同的问答格式：演讲后的非正式小组问题，以及由 Karen Fox 在会议接近尾声时主持的结构化公众问答环节。
