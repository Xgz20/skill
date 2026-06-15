---
id: task_meeting_advisory_timeline
name: NTIA 咨询委员会时间线与截止日期
category: 会议分析
scene: 数据库检索、表格整理与数据分析
sub_scene: 会议记录时间线提取
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 自然语言生成
- 输出格式适配
- 指令遵循与约束理解
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

请分析这份会议记录，将所有关于时间线、截止日期、日程安排和里程碑的引用提取到一份名为 `timeline.md` 的结构化报告中。你的报告应包含：

- 所有提及的日期、截止日期和里程碑（包括过去和未来）的 **按时间顺序排列的时间线**
- **工作组截止日期**（各工作组预计交付成果的时间）
- **下次会议详情**（日期、地点、形式）
- **历史引用**（提供背景的、带有日期的过往事件）
- **过渡时间线**（政府机构表示其搬迁或过渡所需的时长）

对于每个时间线条目，请包含日期（或时间范围）、它所指代的内容、提及者，以及任何注明的条件或附加说明。

---

## Expected Behavior

Agent 应当：

1. 阅读并解析会议记录
2. 提取所有时间引用（具体日期、相对时间范围、持续时长）
3. 按时间顺序进行组织
4. 区分过去事件、当前状态和未来截止日期

预期的关键时间线条目：

**历史/过去：**
- 2010 年 6 月：总统关于 500 MHz 频谱目标的备忘录
- 会议前约 2.5 年（约 2009 年底/2010 年初）：奥巴马政府确定 500 MHz 重新分配目标
- 2010 年 6 月备忘录后 6 个月内：NTIA/各机构识别出 115 MHz 频谱
- 2011 年 10 月 1 日：1755-1850 报告的截止日期（"臭名昭著的 10 月 1 日"）
- 约 2001 年：此前搬迁（1710-1755）的初始成本估算约 9 亿美元
- 过往经验：1710-1755 MHz 频段在 5 年内清空（主要是微波系统）
- 过往：政府与产业之间的 5 GHz Wi-Fi 合作项目

**当前（截至 2012 年 5 月 30 日）：**
- 会议日期：2012 年 5 月 30 日
- 500 MHz 和共享小组委员会在工作组工作期间暂停
- T-Mobile/CTIA 已提交用于频段测量的 STA 申请
- 工作组邀请将在下周内发出

**未来截止日期：**
- 下周左右：NTIA 将发出工作组邀请，确定联合主席
- 约 10 天：委员会联合主席就收尾计划进行汇报（Tramont 的提议）
- 2012 年 9 月：第 1 工作组（气象卫星，1695-1710）目标完成时间
- 2012 年 7 月 24 日：下次 CSMAC 会议在科罗拉多州博尔德召开（下午场）
- 2012 年 7 月 25-26 日：ITS 举办的关于频谱共享的 ISART 会议（紧接 CSMAC 会议之后）
- 2013 年 1 月：第 2-5 工作组（1755-1850 频段）的目标完成时间
- 5 年时间框架：执法部门退出 1755-1780 MHz（第一阶段）
- 10 年时间框架：机构全面过渡出该频段（如报告中所述）
- 10 年目标：500 MHz 频谱重新分配（源自 2010 年备忘录）

---

## Grading Criteria

- [ ] 创建了文件 `timeline.md`
- [ ] 引用了 2010 年 6 月的总统备忘录
- [ ] 提及 2011 年 10 月的报告截止日期
- [ ] 指出了下次 CSMAC 会议（7 月 24 日，科罗拉多州博尔德）
- [ ] 气象卫星工作组 2012 年 9 月的目标
- [ ] 其余工作组 2013 年 1 月的目标
- [ ] 提及 10 年过渡时间框架
- [ ] 指出紧接 CSMAC 会议之后的 ISART 会议
- [ ] 时间线按时间顺序组织

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the timeline extraction task.

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

    report_path = workspace / "timeline.md"
    if not report_path.exists():
        alternatives = ["timeline_report.md", "deadlines.md", "milestones.md", "schedule.md"]
        for alt in alternatives:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "presidential_memo": 0.0,
            "october_report": 0.0,
            "next_meeting": 0.0,
            "september_target": 0.0,
            "january_target": 0.0,
            "ten_year_transition": 0.0,
            "isart_meeting": 0.0,
            "chronological_order": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # June 2010 Presidential memorandum
    memo_patterns = [
        r'(?:june|jun).*2010.*(?:president|memorandum|memo)',
        r'(?:president|memorandum|memo).*(?:june|jun).*2010',
        r'2010.*(?:president|memorandum|memo).*(?:500|spectrum)',
    ]
    scores["presidential_memo"] = 1.0 if any(re.search(p, content_lower) for p in memo_patterns) else 0.0

    # October 2011 report deadline
    oct_patterns = [
        r'october.*(?:2011|1st|first).*(?:report|deadline)',
        r'(?:report|deadline).*october.*(?:2011|1st)',
        r'october 1.*(?:2011)?.*(?:report|deadline|infamous)',
        r'infamous.*october',
    ]
    scores["october_report"] = 1.0 if any(re.search(p, content_lower) for p in oct_patterns) else 0.0

    # Next meeting (July 24, Boulder)
    meeting_patterns = [
        r'july.*24.*(?:boulder|colorado)',
        r'boulder.*(?:colorado|co).*july',
        r'next.*meeting.*(?:july|boulder)',
        r'july 24',
    ]
    scores["next_meeting"] = 1.0 if any(re.search(p, content_lower) for p in meeting_patterns) else 0.0

    # September 2012 weather satellite target
    sept_patterns = [
        r'september.*(?:2012)?.*(?:weather|satellite|1695|complete|target|deadline)',
        r'(?:weather|satellite|1695).*september',
        r'(?:working group 1|wg.?1).*september',
        r'(?:earlier|shorter).*(?:date|time).*(?:september|sept)',
    ]
    scores["september_target"] = 1.0 if any(re.search(p, content_lower) for p in sept_patterns) else 0.0

    # January 2013 target for remaining working groups
    jan_patterns = [
        r'january.*(?:2013|next year).*(?:working group|complete|target|wrap|result)',
        r'(?:working group|1755).*january',
        r'january.*next year',
        r'wrap.*(?:up|issue).*january',
    ]
    scores["january_target"] = 1.0 if any(re.search(p, content_lower) for p in jan_patterns) else 0.0

    # 10-year transition timeframe
    ten_year_patterns = [
        r'ten.?year.*(?:transition|relocat|move|plan|time)',
        r'10.?year.*(?:transition|relocat|move|plan|time)',
        r'(?:transition|relocat|move).*ten.?year',
        r'(?:transition|relocat|move).*10.?year',
    ]
    scores["ten_year_transition"] = 1.0 if any(re.search(p, content_lower) for p in ten_year_patterns) else 0.0

    # ISART meeting
    isart_patterns = [
        r'isart.*(?:meeting|conference|its|spectrum sharing)',
        r'(?:following|after|next).*(?:two|2).*days.*(?:isart|its)',
        r'isart',
    ]
    scores["isart_meeting"] = 1.0 if any(re.search(p, content_lower) for p in isart_patterns) else 0.0

    # Chronological organization (check for year-ordered entries)
    years_found = []
    for match in re.finditer(r'20[01]\d', content):
        years_found.append(int(match.group()))
    if len(years_found) >= 3:
        # Check if years appear in roughly increasing order
        ordered_count = sum(1 for i in range(len(years_found) - 1)
                          if years_found[i] <= years_found[i + 1])
        ratio = ordered_count / (len(years_found) - 1) if len(years_found) > 1 else 0
        scores["chronological_order"] = 1.0 if ratio >= 0.6 else (0.5 if ratio >= 0.4 else 0.0)
    else:
        # Check for date-like patterns suggesting some ordering
        has_dates = bool(re.search(r'\d{4}', content))
        scores["chronological_order"] = 0.5 if has_dates else 0.0

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Completeness of Timeline Entries (Weight: 35%)

**Score 1.0**：捕捉到所有主要时间线条目——历史引用（2010 年备忘录、2011 年 10 月报告、此前的 1710-1755 搬迁、5 GHz Wi-Fi 先例、2001 年成本估算）、当前状态项，以及未来截止日期（9 月、1 月、下次会议、10 年计划）。至少 10 个不同的时间线条目。
**Score 0.75**：捕捉到大部分条目，仅有一到两处遗漏。
**Score 0.5**：指出了主要截止日期，但缺少历史背景或次要条目。
**Score 0.25**：仅提取了最明显的截止日期。
**Score 0.0**：几乎没有时间线条目。

### Criterion 2: Accuracy of Dates and Timeframes (Weight: 25%)

**Score 1.0**：所有日期、持续时长和相对时间范围均准确地从会议记录中提取。无虚构日期。
**Score 0.75**：大部分日期正确，仅有一处轻微错误。
**Score 0.5**：部分日期正确，但存在若干不准确之处。
**Score 0.25**：多处日期错误或存在虚构日期。
**Score 0.0**：日期大体上不正确。

### Criterion 3: Context and Attribution (Weight: 20%)

**Score 1.0**：每个条目都包含提及者、所指内容，以及任何条件或依赖关系。发言人归属准确。
**Score 0.75**：大部分条目背景清晰，仅有少量缺口。
**Score 0.5**：提供了一些背景，但归属不一致。
**Score 0.25**：背景或归属信息极少。
**Score 0.0**：未提供任何背景。

### Criterion 4: Organization and Usability (Weight: 20%)

**Score 1.0**：时间线按时间顺序（或按过去/现在/未来逻辑）清晰组织，易于浏览，格式清晰地区分日期与描述。
**Score 0.75**：组织良好，仅有轻微问题。
**Score 0.5**：有一定组织，但难以理清顺序。
**Score 0.25**：组织混乱。
**Score 0.0**：没有有意义的组织。

---

## Additional Notes

本任务测试 Agent 的以下能力：

- 提取散布在长篇讨论各处的时间信息
- 区分确切日期（7 月 24 日、10 月 1 日）与近似时间范围（"下周内"、"十年"）
- 识别用于提供背景的历史引用（此前的搬迁、过往的成本估算）
- 处理相对时间引用（"两年半前"、"备忘录之后六个月"）
- 将零散的时间线信息组织成连贯的按时间顺序的叙述
- 识别条件性时间线（例如执法部门的三阶段过渡取决于能否找到替代频段）

会议记录中既有明确陈述的日期，也有通过相对引用隐含的日期。Agent 应在可能的情况下解析相对引用（例如从 2012 年 5 月起算的"两年半前"= 2009 年底/2010 年初）。
