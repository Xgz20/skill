---
id: task_meeting_tech_decisions
name: 会议决策提取
category: 会议分析
scene: 企业产品情报与业务信息助手
sub_scene: 会议决策提取
difficulty: L2
capabilities:
- 数据提取与处理
- 自然语言生成
- 指令遵循与约束理解
- 输出格式适配
- 上下文记忆与状态管理
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

我有一个文件 `meeting_transcript.md`，包含 2021 年 6 月 28 日 GitLab 产品营销每周会议的记录。会议涵盖企业活动赞助、GitLab Commit 的产品公告、竞争分析方法论、信息图设计反馈和消息传递框架练习。

请识别会议期间做出的所有决策（或达成的共识）并将它们写入一个名为 `decisions.md` 的文件。对于每个决策，包括：

- **决策**（决定了什么）
- **背景**（关于为什么讨论这个的简要背景）
- **涉及的参与者**（谁参与了）
- **状态**（最终、暂定或需要跟进）

同时在顶部包含一个汇总，附决策总数以及哪些决策可能需要进一步确认。

---

## Expected Behavior

Agent 应该：

1. 阅读并解析会议记录
2. 区分决策（达成的结论）和开放讨论
3. 捕捉每个决策背后的背景

应识别的关键决策：

1. **活动分配**：Platform 团队 → AWS re:Invent，CI/CD → Google Next，GitOps → KubeCon
2. **产品公告方法**：将小型 MVC 捆绑到更大的主题（例如，漏洞管理）而不是列出单个功能；重用 GitLab 14.0 内容加上新增内容
3. **前 5 个功能选择**：团队从所有阶段中选择总体前 5 个功能用于 Commit 主题演讲（而不是每个阶段 3 个）
4. **竞争表方法论**：仅使用第一梯队竞争对手；仅包括与每个特定阶段相关的竞争对手（不是每个阶段全部 5 个）；添加 GitLab 行项目进行对比
5. **信息图颜色**：保持仅绿色的配色方案（无红色/黄色）以维持对比基调而非竞争攻击
6. **消息传递标语选择**："More speed less risk"被选为最终标语（优于"move fast with confidence"、"no trade-offs"等替代方案）
7. **阶段命名**：承认"configure"和"monitor"等阶段描述性不够，但暂时保留；下一次迭代将添加点击查看的详情页面

---

## Grading Criteria

- [ ] 创建了文件 `decisions.md`
- [ ] 识别出至少 5 个不同的决策
- [ ] 捕捉活动分配决策（re:Invent、Google Next、KubeCon）
- [ ] 捕捉产品公告捆绑方法
- [ ] 捕捉竞争方法论决策（仅第一梯队、相关阶段、GitLab 行）
- [ ] 捕捉消息传递标语决策（"more speed less risk"）
- [ ] 捕捉信息图颜色决策（仅绿色，无红色）
- [ ] 为每个决策提供背景
- [ ] 注明决策状态（最终 vs 需要跟进）

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the meeting decisions extraction task.

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

    report_path = workspace / "decisions.md"
    if not report_path.exists():
        for alt in ["meeting_decisions.md", "decision_log.md", "decisions_summary.md"]:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "min_decisions": 0.0,
            "event_assignments": 0.0,
            "announcement_approach": 0.0,
            "competitive_methodology": 0.0,
            "messaging_tagline": 0.0,
            "infographic_colors": 0.0,
            "context_provided": 0.0,
            "status_indicated": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Check minimum number of decisions
    decision_markers = re.findall(r'(?:^|\n)\s*(?:[-*•]|\d+[.)]) .{10,}', content)
    headers = re.findall(r'(?:^|\n)#+\s+.+', content)
    scores["min_decisions"] = 1.0 if len(decision_markers) >= 5 or len(headers) >= 5 else (0.5 if len(decision_markers) >= 3 or len(headers) >= 3 else 0.0)

    # Event assignments
    event_terms = ["reinvent", "re:invent", "google next", "kubecon"]
    event_hits = sum(1 for t in event_terms if t in content_lower)
    scores["event_assignments"] = 1.0 if event_hits >= 2 else (0.5 if event_hits >= 1 else 0.0)

    # Announcement approach (bundling/grouping MVCs)
    announce_patterns = [
        r'(?:bundle|group|bucket|aggregat)',
        r'(?:vulnerability\s*management|mvc|14\.0)',
    ]
    announce_hits = sum(1 for p in announce_patterns if re.search(p, content_lower))
    scores["announcement_approach"] = 1.0 if announce_hits >= 2 else (0.5 if announce_hits >= 1 else 0.0)

    # Competitive methodology
    comp_patterns = [
        r'(?:tier\s*(?:one|1))',
        r'(?:gitlab\s*(?:line|row|column)|add\s*gitlab|gitlab\s*comparison)',
        r'(?:relevant|applicable).*(?:stage|competitor)',
    ]
    comp_hits = sum(1 for p in comp_patterns if re.search(p, content_lower))
    scores["competitive_methodology"] = 1.0 if comp_hits >= 2 else (0.5 if comp_hits >= 1 else 0.0)

    # Messaging tagline
    tagline_patterns = [
        r'more\s*speed\s*less\s*risk',
    ]
    scores["messaging_tagline"] = 1.0 if any(re.search(p, content_lower) for p in tagline_patterns) else 0.0

    # Infographic colors
    color_patterns = [
        r'(?:green|color).*(?:no\s*red|without\s*red|comparison)',
        r'(?:no\s*red|avoid\s*red|stick\s*with\s*green)',
    ]
    scores["infographic_colors"] = 1.0 if any(re.search(p, content_lower) for p in color_patterns) else 0.0

    # Context provided (look for explanatory text around decisions)
    context_patterns = [r'(?:because|reason|background|context|rationale|why|since|given\s*that)', r'(?:discuss|debate|consider|weigh)']
    context_hits = sum(1 for p in context_patterns if re.search(p, content_lower))
    scores["context_provided"] = 1.0 if context_hits >= 2 else (0.5 if context_hits >= 1 else 0.0)

    # Status indicated
    status_patterns = [r'(?:final|tentative|follow.?up|confirmed|pending|needs?\s*(?:confirmation|follow))', r'(?:status|resolved|agreed|consensus)']
    status_hits = sum(1 for p in status_patterns if re.search(p, content_lower))
    scores["status_indicated"] = 1.0 if status_hits >= 2 else (0.5 if status_hits >= 1 else 0.0)

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Decision Identification Accuracy (Weight: 35%)

**Score 1.0**: 识别所有主要决策，包括活动分配、公告方法、竞争方法论、信息图颜色和消息传递标语。正确区分决策与正在进行的讨论。
**Score 0.75**: 捕捉大部分决策，但遗漏一个或包含了讨论过但未决定的项目。
**Score 0.5**: 捕捉一些决策，但遗漏几个或将讨论与决策混淆。
**Score 0.25**: 仅识别一两个明显的决策。
**Score 0.0**: 未识别有意义的决策。

### Criterion 2: Context Quality (Weight: 25%)

**Score 1.0**: 每个决策包含准确的背景，解释什么引发了讨论、考虑了哪些替代方案，以及为什么选择了所选选项。
**Score 0.75**: 大部分决策有良好背景，有轻微差距。
**Score 0.5**: 提供了一些背景，但缺少关键推理或考虑的替代方案。
**Score 0.25**: 最小背景，决策无解释列出。
**Score 0.0**: 没有提供背景。

### Criterion 3: Participant Attribution (Weight: 20%)

**Score 1.0**: 正确识别谁主张每个立场以及谁参与达成共识。姓名准确地从记录中提取。
**Score 0.75**: 大部分参与者正确识别，有轻微错误。
**Score 0.5**: 识别出一些参与者，但有几个缺失或错误归属。
**Score 0.25**: 最小的参与者识别。
**Score 0.0**: 没有参与者归属。

### Criterion 4: Structure and Usefulness (Weight: 20%)

**Score 1.0**: 决策以一致的结构清晰格式化，包含有用的汇总，并指明哪些决策是最终的 vs 需要跟进的。可直接用作会议纪要。
**Score 0.75**: 结构良好，有轻微格式问题。
**Score 0.5**: 可读但结构不一致或缺少汇总。
**Score 0.25**: 组织不佳，难以用作参考。
**Score 0.0**: 没有可用的结构。
