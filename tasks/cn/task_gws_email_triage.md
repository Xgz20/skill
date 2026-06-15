---
id: task_gws_email_triage
name: GWS 邮件分类处理
category: 集成
scene: 数据库检索、表格整理与数据分析
sub_scene: 邮件分类处理
difficulty: L3
capabilities:
- 工具调用
- 外部服务集成
- 数据提取与处理
- 自然语言生成
- 多步推理
grading_type: hybrid
timeout_seconds: 300
grading_weights:
  automated: 0.5
  llm_judge: 0.5
workspace_files: []
prerequisites:
  - npm:@juppytt/fws
  - cli:gws
---

## Prompt

你可以通过 `gws` CLI 工具访问一个 Google Workspace 账户（使用 `gws --help` 查看用法）。

你的收件箱里有若干封未读邮件。请对它们进行分类处理：

1. 查看你的未读邮件
2. 阅读每一封邮件以理解其内容和紧急程度
3. 针对最紧急的那封邮件，起草一封回复（保存为草稿，不要发送）
4. 创建一份分类报告并保存到 `triage_report.md`，为每封邮件标注优先级（P0-P3）、类别和建议采取的行动，并按优先级排序（最紧急的排在最前）

## Expected Behavior

Agent 应当：

1. 发现并使用 gws Gmail 命令来列出和阅读邮件
2. 分析邮件内容、发件人和紧急程度
3. 识别出最紧急的邮件并创建一封草稿回复
4. 将一份结构化的分类报告写入 `triage_report.md`

本任务测试 Agent 发现并使用 gws CLI 来完成一个多步邮件工作流的能力：列出、阅读、起草和综合。

## Grading Criteria

- [ ] Agent 使用 gws 列出了未读邮件
- [ ] Agent 使用 gws 阅读了单封邮件
- [ ] Agent 为最紧急的邮件创建了一封草稿回复
- [ ] 工作区中创建了 `triage_report.md` 文件
- [ ] 所有未读邮件都出现在报告中
- [ ] 每封邮件都被分配了优先级（P0-P3）
- [ ] 每封邮件都有建议采取的行动
- [ ] 报告按优先级排序

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the GWS email triage task.
    """
    from pathlib import Path
    import re

    scores = {}
    workspace = Path(workspace_path)

    used_list = False
    used_get = False
    used_draft = False

    def extract_commands(transcript):
        """Extract shell commands from transcript, handling multiple tool call formats."""
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
        if "gws" in cmd and ("triage" in cmd or "messages list" in cmd):
            used_list = True
        if "gws" in cmd and "messages get" in cmd:
            used_get = True
        if "gws" in cmd and "drafts create" in cmd:
            used_draft = True

    scores["listed_emails"] = 1.0 if used_list else 0.0
    scores["read_messages"] = 1.0 if used_get else 0.0
    scores["created_draft"] = 1.0 if used_draft else 0.0

    report_file = workspace / "triage_report.md"
    if report_file.exists():
        scores["report_created"] = 1.0
        content = report_file.read_text().lower()

        has_priorities = bool(re.search(r'p[0-3]', content))
        scores["priorities_assigned"] = 1.0 if has_priorities else 0.0

        p0_pos = content.find("p0")
        p3_pos = content.find("p3")
        if p0_pos >= 0 and p3_pos >= 0:
            scores["sorted_by_priority"] = 1.0 if p0_pos < p3_pos else 0.0
        else:
            scores["sorted_by_priority"] = 0.5
    else:
        scores["report_created"] = 0.0
        scores["priorities_assigned"] = 0.0
        scores["sorted_by_priority"] = 0.0

    return scores
```

## LLM Judge Rubric

### Criterion 1: GWS CLI Discovery and Usage (Weight: 30%)

**Score 1.0**: Agent 发现并流畅地使用了 gws Gmail 命令（list、get、drafts），参数正确。
**Score 0.75**: Agent 正确使用了 gws CLI，但存在少量参数问题或多余的无效调用。
**Score 0.5**: Agent 使用了部分 gws 命令，但在语法上遇到困难或遗漏了关键命令。
**Score 0.25**: Agent 几乎没有使用 gws CLI，或使用了错误的命令。
**Score 0.0**: Agent 完全没有使用 gws CLI。

### Criterion 2: Triage Quality (Weight: 40%)

**Score 1.0**: 所有邮件都被正确分配了优先级，类别准确，建议具体且可执行。
**Score 0.75**: 大多数邮件优先级分配正确，有少量分类错误。建议合理。
**Score 0.5**: 部分邮件优先级正确，但判断上有明显错误。建议较为笼统。
**Score 0.25**: 优先级分配大多不正确或缺失。
**Score 0.0**: 没有进行有意义的分类处理。

### Criterion 3: Draft Reply Quality (Weight: 30%)

**Score 1.0**: 草稿回复针对正确的紧急邮件，回复专业且承认了具体情况。
**Score 0.75**: 草稿针对正确的邮件并给出合理回复，但语气或内容仍有改进空间。
**Score 0.5**: 创建了草稿，但针对了不太合适的邮件，或内容笼统。
**Score 0.25**: 创建了草稿，但格式不正确或内容无关。
**Score 0.0**: 没有创建草稿。

## Additional Notes

本任务需要 [fws](https://github.com/juppytt/fws) 作为模拟 GWS 服务器运行。测试运行器应在任务开始前执行 `fws server start`，并设置环境变量（GOOGLE_WORKSPACE_CLI_CONFIG_DIR、GOOGLE_WORKSPACE_CLI_TOKEN、HTTPS_PROXY、SSL_CERT_FILE）。

fws 的种子数据包含 5 封邮件：3 封未读收件箱邮件（来自 alice@company.com 关于 Q3 Planning、bob@company.com 关于代码评审、notifications@github.com 关于一次 CI 失败）、1 封已发送邮件，以及 1 封已读邮件。
