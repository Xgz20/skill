---
id: task_gh_issue_triage
name: GitHub Issue 分类
category: 技能
scene: Skill发现、创建、安装与调用
sub_scene: GitHub Issue 分类
difficulty: L2
capabilities:
- 工具调用
- 外部服务集成
- 多步推理
- 自然语言生成
- 输出格式适配
grading_type: hybrid
timeout_seconds: 300
grading_weights:
  automated: 0.5
  llm_judge: 0.5
workspace_files: []
prerequisites:
  - npm:@juppytt/fws
  - cli:gh
---

## Prompt

你可以通过 `gh` CLI 工具访问一个 GitHub 仓库（使用 `gh --help` 查看用法）。仓库是 `testuser/my-project`。

请审查开放的 issue 和 pull request：

1. 列出所有开放的 issue 和 PR
2. 阅读每一个以了解其内容
3. 对于最关键的 issue，添加一条评论，包含你的分析和建议的后续步骤
4. 创建一份分类报告并保存到 `triage_report.md`，为每个条目列出优先级、类别和推荐行动，并按优先级排序

## Expected Behavior

Agent 应当：

1. 使用 gh CLI 列出并阅读 issue 和 PR
2. 分析每个条目的紧急程度和影响
3. 对最关键的 issue 添加评论
4. 撰写结构化的分类报告到 `triage_report.md`

这测试 Agent 使用 gh CLI 完成多步 GitHub 工作流的能力：列出、阅读、评论和综合。

## Grading Criteria

- [ ] Agent 使用 gh 列出了 issue
- [ ] Agent 使用 gh 列出或查看了 PR
- [ ] Agent 阅读了单个 issue/PR 以了解内容
- [ ] Agent 对最关键的 issue 添加了评论
- [ ] 在工作区创建了文件 `triage_report.md`
- [ ] 报告中包含所有开放条目
- [ ] 每个条目都分配了优先级
- [ ] 报告按优先级排序

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the GitHub issue triage task.
    """
    from pathlib import Path
    import re

    scores = {}
    workspace = Path(workspace_path)

    listed_issues = False
    viewed_pr = False
    read_detail = False
    commented = False

    def extract_commands(transcript):
        cmds = []
        for event in transcript:
            if event.get("type") != "message":
                continue
            msg = event.get("message", {})
            for item in msg.get("content", []):
                t = item.get("type", "")
                if t in ("tool_use", "toolCall"):
                    cmd = (
                        item.get("input", {}).get("command", "")
                        or item.get("arguments", {}).get("command", "")
                        or item.get("params", {}).get("command", "")
                    )
                    if cmd:
                        cmds.append(cmd)
        return cmds

    for cmd in extract_commands(transcript):
        if "gh" in cmd and ("issue list" in cmd or "api" in cmd and "issues" in cmd):
            listed_issues = True
        if "gh" in cmd and ("pr list" in cmd or "pr view" in cmd or "pulls" in cmd):
            viewed_pr = True
        if "gh" in cmd and ("issue view" in cmd or "issues/" in cmd):
            read_detail = True
        if "gh" in cmd and ("comment" in cmd or "comments" in cmd) and ("-f" in cmd or "--body" in cmd or "-X POST" in cmd):
            commented = True

    scores["listed_issues"] = 1.0 if listed_issues else 0.0
    scores["viewed_prs"] = 1.0 if viewed_pr else 0.0
    scores["read_detail"] = 1.0 if read_detail else 0.0
    scores["commented"] = 1.0 if commented else 0.0

    report_file = workspace / "triage_report.md"
    if report_file.exists():
        scores["report_created"] = 1.0
        content = report_file.read_text().lower()
        has_priorities = bool(re.search(r'(p[0-3]|critical|high|medium|low|urgent)', content))
        scores["priorities_assigned"] = 1.0 if has_priorities else 0.0
    else:
        scores["report_created"] = 0.0
        scores["priorities_assigned"] = 0.0

    return scores
```

## LLM Judge Rubric

### Criterion 1: gh CLI Usage (Weight: 30%)

**Score 1.0**：Agent 熟练使用 gh CLI 以正确参数列出、查看和评论 issue/PR。
**Score 0.75**：Agent 正确使用了 gh CLI，但参数上有小问题。
**Score 0.5**：Agent 使用了部分 gh 命令，但语法上有困难。
**Score 0.25**：Agent 几乎没有使用 gh CLI。
**Score 0.0**：Agent 完全没有使用 gh CLI。

### Criterion 2: Triage Quality (Weight: 40%)

**Score 1.0**：所有条目正确排定优先级，分析准确且建议具体。
**Score 0.75**：大部分条目正确排定优先级，分析合理。
**Score 0.5**：部分条目排定了优先级，但判断上有明显错误。
**Score 0.25**：优先级分配大多不正确或缺失。
**Score 0.0**：未执行有意义的分类。

### Criterion 3: Comment Quality (Weight: 30%)

**Score 1.0**：在正确的 issue 上评论，分析深刻且后续步骤可执行。
**Score 0.75**：在正确的 issue 上评论，建议合理。
**Score 0.5**：创建了评论，但针对的是不太合适的 issue，或内容泛泛。
**Score 0.25**：创建了评论，但内容无关。
**Score 0.0**：未创建评论。

## Additional Notes

此任务需要运行 [fws](https://github.com/juppytt/fws) 作为模拟服务器。测试运行器应在任务开始前执行 `fws server start` 并通过 `eval $(fws server env)` 设置环境变量。

种子数据包括：1 个仓库（testuser/my-project）、2 个开放的 issue（#1 "Fix login bug" 带一条评论，#2 "Add dark mode support"）以及 1 个开放的 PR（#3 "Fix SSO login flow"）。
