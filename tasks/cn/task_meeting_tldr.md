---
id: task_meeting_tldr
name: 会议 TL;DR 速览
category: 会议分析
scene: 内容创作、PPT、网页与多媒体生成
sub_scene: 会议摘要总结
difficulty: L2
capabilities:
- 指令遵循与约束理解
- 自然语言生成
- 数据提取与处理
- 输出格式适配
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

我有一个文件 `meeting_transcript.md`，里面是一次 GitLab 产品营销团队会议的逐字记录。我错过了这次会议，需要快速跟上进度。

请把一份 TL;DR 写入名为 `meeting_tldr.md` 的文件。它应当**极度精简**——就是那种你会发在 Slack 上、给错过通话的队友看的摘要。要求如下：

- **最多 150 个单词**（硬性限制）
- 顶部一句话总结（用一句话说明这次会议是关于什么的）
- **3-5 个要点**，覆盖最重要的结论
- 提及的**任何截止日期**

不要废话，不要铺垫，不要"In this meeting, the team discussed..."——只要核心事实。

---

## Expected Behavior

Agent 应当：

1. 阅读逐字记录
2. 将整场会议提炼到约 150 个单词或更少
3. 产出类似如下内容：

   **Weekly PMM sync — event assignments, Commit announcements, messaging.**

   - Event ownership locked: Platform→re:Invent, CI/CD→Google Next, GitOps→KubeCon. Confirm with your campaign managers and comment on the issue.
   - Top 5 product announcements needed for Commit. Vulnerability management is the lead security pick. Team voting on final list.
   - Messaging tagline decided: "more speed, less risk." Company-level: "single source of truth, countless possibilities."
   - Competitive infographic going green-only (no red) — design team's recommendation.
   - Competitive sheets: only use tier 1 competitors relevant to your stage. Add GitLab as a line item.

   **⏰ Product announcements spreadsheet due Tuesday.**

---

## Grading Criteria

- [ ] 创建了文件 `meeting_tldr.md`
- [ ] 顶部有一句话总结
- [ ] 包含 3-5 个要点
- [ ] 提到了 event 分配（re:Invent、Google Next 或 KubeCon）
- [ ] 提到了 messaging 决策（"more speed, less risk"）
- [ ] 提到了一个截止日期（Tuesday）
- [ ] 总字数低于 200 个单词
- [ ] 没有不必要的填充内容或铺垫

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the meeting TL;DR task.

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
    report_path = workspace / "meeting_tldr.md"
    if not report_path.exists():
        alternatives = ["tldr.md", "tl_dr.md", "meeting_tl_dr.md", "summary.md"]
        for alt in alternatives:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "file_created": 0.0,
            "one_line_summary": 0.0,
            "bullet_points": 0.0,
            "events_mentioned": 0.0,
            "messaging_decision": 0.0,
            "deadline_mentioned": 0.0,
            "word_count_ok": 0.0,
            "no_filler": 0.0,
        }

    scores["file_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()
    word_count = len(content.split())

    # One-line summary at top (first non-empty, non-heading line or first heading)
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    if lines:
        first_content = lines[0] if not lines[0].startswith('#') else (lines[1] if len(lines) > 1 else lines[0])
        # Should be a short summary line (under 30 words)
        first_words = len(first_content.split())
        scores["one_line_summary"] = 1.0 if first_words <= 30 else 0.5
    else:
        scores["one_line_summary"] = 0.0

    # Bullet points (3-5)
    bullets = re.findall(r'(?:^|\n)\s*[-*•]\s+.+', content)
    if 3 <= len(bullets) <= 7:
        scores["bullet_points"] = 1.0
    elif 2 <= len(bullets) <= 9:
        scores["bullet_points"] = 0.5
    else:
        scores["bullet_points"] = 0.0

    # Event assignments mentioned
    event_patterns = [r're:?\s*invent', r'google\s*next', r'kubecon']
    events_found = sum(1 for p in event_patterns if re.search(p, content_lower))
    scores["events_mentioned"] = 1.0 if events_found >= 2 else (0.5 if events_found >= 1 else 0.0)

    # Messaging decision
    scores["messaging_decision"] = 1.0 if re.search(r'more\s*speed.*less\s*risk', content_lower) else 0.0

    # Deadline mentioned
    scores["deadline_mentioned"] = 1.0 if re.search(r'tuesday|deadline|due', content_lower) else 0.0

    # Word count (target: ≤150, acceptable: ≤200)
    if word_count <= 150:
        scores["word_count_ok"] = 1.0
    elif word_count <= 200:
        scores["word_count_ok"] = 0.5
    else:
        scores["word_count_ok"] = 0.0

    # No filler/preamble
    filler_patterns = [
        r'in\s*this\s*meeting',
        r'the\s*team\s*(?:discussed|met|gathered)',
        r'this\s*(?:document|summary)\s*(?:provides|contains|covers)',
        r'here\s*(?:is|are)\s*(?:the|a)\s*(?:summary|overview)',
        r'below\s*(?:is|are)',
    ]
    filler_count = sum(1 for p in filler_patterns if re.search(p, content_lower))
    scores["no_filler"] = 1.0 if filler_count == 0 else (0.5 if filler_count == 1 else 0.0)

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Information Density (Weight: 40%)

**Score 1.0**：每句话都承载关键信息。会议中最重要的 5 项结论都被捕捉到。没有一个多余的词。读这份摘要的队友能了解到他们需要知道的一切。
**Score 0.75**：捕捉到了大部分重要结论，仅有少量遗漏或略显冗长。
**Score 0.5**：关键结论已呈现，但缺失了一些重要条目，或被不必要的背景信息填充。
**Score 0.25**：遗漏了重大结论，或对于 TL;DR 而言过于啰嗦。
**Score 0.0**：作为快速摘要没有用处。

### Criterion 2: Conciseness (Weight: 35%)

**Score 1.0**：少于 150 个单词。读起来像一条 Slack 消息——干脆、直接、没有套话。在合适处使用简写（用 → 表示分配，常见术语用缩写）。
**Score 0.75**：少于 200 个单词，大体精炼，仍有少量可删减空间。
**Score 0.5**：200-300 个单词，内容合理但并非真正的 TL;DR。
**Score 0.25**：超过 300 个单词——这是一份摘要，不是 TL;DR。
**Score 0.0**：超过 500 个单词，或完全未达到精简要求。

### Criterion 3: Scannability (Weight: 25%)

**Score 1.0**：可在 30 秒内完全读懂。视觉结构清晰（要点、加粗强调、单独标出截止日期）。顶部的一句话总结能让读者立即抓住重点。
**Score 0.75**：结构良好，大体易于扫读，仍有少量可改进之处。
**Score 0.5**：包含了信息，但需要仔细阅读才能提取关键点。
**Score 0.25**：一大段文字堆砌，或结构混乱。
**Score 0.0**：无结构或缺失。

---

## Additional Notes

这个任务测试 Agent 的以下能力：

- 执行极致的摘要压缩（长篇逐字记录 → 约 150 个单词）
- 无情地排定优先级——从一场 30 分钟的会议中找出真正重要的内容
- 以精炼、半正式的专业风格写作（适合 Slack）
- 识别截止日期和对行动至关重要的信息
- 抵制过度解释或添加背景的冲动

逐字记录约有 4000+ 个单词的非正式对话。Agent 必须将其压缩到原长度的约 3-4%，同时保留最重要的结论。这与其说是一个写作挑战，不如说是一个压缩与优先级排序的挑战。
