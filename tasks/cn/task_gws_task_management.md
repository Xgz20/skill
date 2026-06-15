---
id: task_gws_task_management
name: GWS 任务管理
category: 集成
scene: Skill发现、创建、安装与调用
sub_scene: 任务收件箱工作流
difficulty: L2
capabilities:
- 工具调用
- 数据提取与处理
- 多步推理
- 外部服务集成
- 输出格式适配
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

你可以通过 `gws` CLI 工具访问一个 Google Workspace 账户（使用 `gws --help` 查看用法）。

根据收件箱中的内容来管理你的任务：

1. 检查当前的任务列表，并将任何已经完成的事项标记为已完成
2. 阅读你最近的邮件以找出待办事项
3. 为你在邮件中发现的每一个待办事项创建一个新任务
4. 将一份摘要保存到 `task_summary.md`，列出你发现、创建和完成了哪些任务

## Expected Behavior

Agent 应当：

1. 使用 gws Tasks 列出当前任务并更新已完成的任务
2. 使用 gws Gmail 阅读最近的邮件并提取待办事项
3. 根据邮件中发现的待办事项创建新任务
4. 将一份摘要写入 `task_summary.md`

本任务测试 Agent 结合 Tasks 和 Gmail、从非结构化邮件内容中提取结构化信息以及管理任务列表的能力。

## Grading Criteria

- [ ] Agent 使用 gws 列出了现有任务
- [ ] Agent 将已完成的任务标记为已完成
- [ ] Agent 使用 gws 阅读了邮件
- [ ] 至少根据邮件待办事项创建了一个新任务
- [ ] 新任务拥有源自邮件内容的有意义的标题
- [ ] 创建了包含摘要的 `task_summary.md` 文件

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the GWS task management task.
    """
    from pathlib import Path

    scores = {}
    workspace = Path(workspace_path)

    listed_tasks = False
    updated_task = False
    read_emails = False
    created_task = False

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
        if "tasks" in cmd and "list" in cmd:
            listed_tasks = True
        if "tasks" in cmd and ("patch" in cmd or "update" in cmd):
            updated_task = True
        if "gmail" in cmd and ("messages" in cmd or "triage" in cmd):
            read_emails = True
        if "tasks" in cmd and "insert" in cmd:
            created_task = True

    scores["listed_tasks"] = 1.0 if listed_tasks else 0.0
    scores["updated_completed"] = 1.0 if updated_task else 0.0
    scores["read_emails"] = 1.0 if read_emails else 0.0
    scores["created_new_task"] = 1.0 if created_task else 0.0

    summary_file = workspace / "task_summary.md"
    if summary_file.exists():
        scores["summary_created"] = 1.0
    else:
        scores["summary_created"] = 0.0

    return scores
```

## LLM Judge Rubric

### Criterion 1: Information Extraction (Weight: 40%)

**Score 1.0**: Agent 正确地从邮件中识别出可执行的待办事项，并为每一项创建了标题恰当、具体的任务。
**Score 0.75**: Agent 发现了大多数待办事项，任务标题合理。
**Score 0.5**: Agent 发现了一些待办事项，但遗漏了重要事项，或任务标题含糊。
**Score 0.25**: Agent 创建了任务，但它们与邮件内容的关联不清晰。
**Score 0.0**: 没有根据邮件创建任何任务。

### Criterion 2: Task List Management (Weight: 30%)

**Score 1.0**: Agent 正确地审阅了现有任务，识别出已完成的那一项并将其标记为完成，且合理地组织了新任务。
**Score 0.75**: Agent 管理了任务列表，但有少量疏漏。
**Score 0.5**: Agent 部分管理了任务列表，但漏掉了更新已完成任务或存在其他缺口。
**Score 0.25**: Agent 与任务的交互极少。
**Score 0.0**: Agent 没有管理任务列表。

### Criterion 3: Summary Quality (Weight: 30%)

**Score 1.0**: 摘要清晰地列出了发现了什么、创建了什么以及完成了什么，组织良好。
**Score 0.75**: 摘要涵盖了关键要点，但组织可以更好。
**Score 0.5**: 摘要存在，但不完整或结构较差。
**Score 0.25**: 摘要内容极少或不清晰。
**Score 0.0**: 没有创建摘要。

## Additional Notes

本任务需要 [fws](https://github.com/juppytt/fws) 作为模拟 GWS 服务器运行。测试运行器应在任务开始前执行 `fws server start`，并设置环境变量（GOOGLE_WORKSPACE_CLI_CONFIG_DIR、GOOGLE_WORKSPACE_CLI_TOKEN、HTTPS_PROXY、SSL_CERT_FILE）。

fws 的种子数据包含：一个 "My Tasks" 列表，内有 2 个任务（1 个待处理："Review Q3 proposal"，1 个已完成："Update documentation"），以及 5 封带有各种待办事项的邮件（Q3 规划会议、代码评审请求、CI 失败通知）。
