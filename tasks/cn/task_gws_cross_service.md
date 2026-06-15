---
id: task_gws_cross_service
name: GWS 跨服务工作流
category: 集成
scene: 本地环境、命令执行与脚本任务
sub_scene: 跨服务工作流自动化
difficulty: L2
capabilities:
- 外部服务集成
- 工具调用
- 多步推理
- 数据提取与处理
- 指令遵循与约束理解
grading_type: hybrid
timeout_seconds: 300
grading_weights:
  automated: 0.6
  llm_judge: 0.4
workspace_files: []
prerequisites:
  - npm:@juppytt/fws
  - cli:gws
---

## Prompt

你可以通过 `gws` CLI 工具访问一个 Google Workspace 帐户（使用 `gws --help` 查看用法）。

你收到了一封来自 alice@company.com 的关于"Q3 Planning Meeting"的邮件。请执行以下操作：

1. 找到并阅读该邮件以获取会议详情
2. 根据邮件中找到的信息创建一个日历事件
3. 在 Drive 中找到"Q3 Planning Agenda"文档，并与 bob@company.com 共享（读者访问权限）
4. 将你所做的操作摘要保存到 `actions.md`

## Expected Behavior

Agent 应当：

1. 搜索或列出 Gmail 消息以找到来自 Alice 的 Q3 Planning 邮件
2. 阅读邮件内容以获取会议详情
3. 使用 gws Calendar 创建一个事件，包含正确的摘要、时间和参会者
4. 使用 gws Drive 找到议程文档，并为 bob@company.com 添加权限
5. 将已完成操作的摘要写入 `actions.md`

这测试 Agent 在单个工作流中协调 Gmail、Calendar 和 Drive 的能力。

## Grading Criteria

- [ ] Agent 找到并阅读了 Q3 Planning 邮件
- [ ] 创建了包含相关摘要的日历事件
- [ ] 日历事件有开始时间
- [ ] 在 Drive 中找到了 Q3 Planning Agenda 文档
- [ ] 为该文档创建了 bob@company.com 的权限
- [ ] 创建了文件 `actions.md`，包含已采取操作的摘要

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the GWS cross-service workflow task.
    """
    from pathlib import Path

    scores = {}
    workspace = Path(workspace_path)

    read_email = False
    created_event = False
    found_file = False
    shared_file = False

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
        if "gws" not in cmd:
            continue
        if "messages get" in cmd or "messages list" in cmd or "+triage" in cmd:
            read_email = True
        if "events insert" in cmd or "events create" in cmd:
            created_event = True
        if "files list" in cmd or "files get" in cmd:
            found_file = True
        if "permissions create" in cmd:
            shared_file = True

    scores["read_email"] = 1.0 if read_email else 0.0
    scores["created_event"] = 1.0 if created_event else 0.0
    scores["found_drive_file"] = 1.0 if found_file else 0.0
    scores["shared_file"] = 1.0 if shared_file else 0.0

    actions_file = workspace / "actions.md"
    if actions_file.exists():
        scores["actions_summary"] = 1.0
    else:
        scores["actions_summary"] = 0.0

    return scores
```

## LLM Judge Rubric

### Criterion 1: Cross-Service Coordination (Weight: 50%)

**Score 1.0**：Agent 无缝浏览 Gmail、Calendar 和 Drive，从一个服务提取信息并在另一个服务中使用。工作流逻辑清晰且高效。
**Score 0.75**：Agent 使用了全部三个服务，但有轻微的低效或服务之间的连接有所遗漏。
**Score 0.5**：Agent 正确使用了三个服务中的两个，但未能在它们之间连接数据。
**Score 0.25**：Agent 尝试使用这些服务，但大部分操作遇到困难。
**Score 0.0**：Agent 未能跨多个服务使用 gws。

### Criterion 2: Task Completeness (Weight: 50%)

**Score 1.0**：全部四个步骤都正确完成：阅读了邮件、使用正确的详情创建了事件、与 bob 共享了文档、撰写了摘要。
**Score 0.75**：四个步骤中的三个正确完成。
**Score 0.5**：四个步骤中的两个正确完成。
**Score 0.25**：一个步骤正确完成。
**Score 0.0**：未完成任何步骤。

## Additional Notes

此任务需要运行 [fws](https://github.com/juppytt/fws) 作为模拟 GWS 服务器。测试运行器应在任务开始前执行 `fws server start` 并设置环境变量（GOOGLE_WORKSPACE_CLI_CONFIG_DIR、GOOGLE_WORKSPACE_CLI_TOKEN、HTTPS_PROXY、SSL_CERT_FILE）。

fws 种子数据包括：一封来自 alice@company.com 的关于"Q3 Planning Meeting"的邮件、一个名为"Q3 Planning Agenda"的 Drive 文件（id: file001）以及一个包含现有事件的主日历。
