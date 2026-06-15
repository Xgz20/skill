---
id: task_workflow
name: 多步骤 API 工作流
category: 技能
scene: 本地环境、命令执行与脚本任务
sub_scene: 配置驱动的脚本生成
difficulty: L2
capabilities:
- 多步推理
- 代码生成与理解
- 数据提取与处理
- 自然语言生成
- 指令遵循与约束理解
grading_type: hybrid
timeout_seconds: 300
workspace_files:
  - path: "config.json"
    content: |
      {
        "api": {
          "endpoint": "https://api.example.com/v2/data",
          "method": "GET",
          "headers": {
            "Content-Type": "application/json",
            "Accept": "application/json"
          },
          "timeout": 30
        },
        "project": {
          "name": "DataFetcher",
          "version": "1.0.0",
          "description": "Automated data fetching utility"
        }
      }
---

## Prompt

读取 config.json，提取其中的 API endpoint，创建一个 Python 脚本来调用它，并在 NOTES.md 中记录整个过程。

## Expected Behavior

Agent 应当：

1. 从工作区读取 `config.json` 文件
2. 解析 JSON 并提取 API endpoint URL
3. 创建一个 Python 脚本，该脚本：
   - 读取配置文件
   - 向 endpoint 发起 HTTP 请求
   - 妥善处理错误
   - 打印或返回响应
4. 创建一个 `NOTES.md` 文件，记录：
   - 做了什么
   - 脚本如何工作
   - 如何使用它
   - 关于配置的任何重要细节

本任务考察多步骤协调、文件读取、代码生成以及文档撰写能力。

## Grading Criteria

### Automated Criteria (50%)

- [ ] 成功读取 `config.json` 文件
- [ ] 创建了 Python 脚本文件（任意 .py 文件名）
- [ ] 脚本包含有效的 Python 语法
- [ ] 脚本读取/解析 JSON
- [ ] 脚本包含 HTTP 请求代码
- [ ] 创建了 `NOTES.md` 文件

### LLM Judge Criteria (50%)

- [ ] 脚本质量与完整性
- [ ] 文档清晰度与实用性
- [ ] 过程说明质量
- [ ] 整体任务完成度

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the automated portion of the workflow task (50% of total).

    Args:
        transcript: Parsed JSONL transcript as list of dicts
        workspace_path: Path to the task's isolated workspace directory

    Returns:
        Dict mapping criterion names to scores (0.0 to 1.0)
    """
    from pathlib import Path
    import re
    import ast
    import json

    scores = {}
    workspace = Path(workspace_path)

    # Check if agent read config.json (from transcript)
    read_config = False
    for event in transcript:
        if event.get("type") != "message":
            continue
        msg = event.get("message", {})
        if msg.get("role") == "assistant":
            for item in msg.get("content", []):
                if item.get("type") == "toolCall":
                    tool_name = item.get("name", "")
                    # Support both "params" (Cursor/Windsurf) and "arguments" (OpenClaw/Claude Code)
                    params = item.get("params", item.get("arguments", {}))
                    if tool_name.lower() in ["read_file", "readfile", "read"]:
                        # Support multiple param formats across different agents:
                        # - files: ["config.json"] (Cursor, Windsurf)
                        # - path/file_path/file: "config.json" (OpenClaw, Claude Code)
                        files = params.get("files", [])
                        path_candidates = [
                            params.get("path", ""),
                            params.get("file_path", ""),
                            params.get("file", ""),
                        ]
                        if any("config.json" in str(f) for f in files) or any(
                            "config.json" in str(path) for path in path_candidates if path
                        ):
                            read_config = True
                            break

    scores["read_config"] = 1.0 if read_config else 0.0

    # Find Python script file
    py_files = list(workspace.glob("*.py"))

    if not py_files:
        scores["script_created"] = 0.0
        scores["valid_syntax"] = 0.0
        scores["parses_json"] = 0.0
        scores["has_http_request"] = 0.0
    else:
        scores["script_created"] = 1.0

        # Read the first Python file found
        script_content = py_files[0].read_text()

        # Check for valid Python syntax
        try:
            ast.parse(script_content)
            scores["valid_syntax"] = 1.0
        except SyntaxError:
            scores["valid_syntax"] = 0.0
            scores["parses_json"] = 0.0
            scores["has_http_request"] = 0.0
            scores["notes_created"] = 0.0
            return scores

        # Check for JSON parsing
        json_patterns = [
            r'import\s+json',
            r'from\s+json\s+import',
            r'json\.load',
            r'json\.loads',
        ]
        if any(re.search(pattern, script_content) for pattern in json_patterns):
            scores["parses_json"] = 1.0
        else:
            scores["parses_json"] = 0.0

        # Check for HTTP request
        http_patterns = [
            r'import\s+requests',
            r'from\s+requests\s+import',
            r'import\s+urllib',
            r'from\s+urllib',
            r'requests\.get',
            r'requests\.post',
            r'urllib\.request',
            r'urlopen',
        ]
        if any(re.search(pattern, script_content, re.IGNORECASE) for pattern in http_patterns):
            scores["has_http_request"] = 1.0
        else:
            scores["has_http_request"] = 0.0

    # Check if NOTES.md exists
    notes_file = workspace / "NOTES.md"
    if notes_file.exists():
        scores["notes_created"] = 1.0
    else:
        scores["notes_created"] = 0.0

    return scores
```

## LLM Judge Rubric

### Criterion 1: Script Quality and Functionality (Weight: 30%)

**Score 1.0**: Python 脚本结构良好，正确读取 config.json，提取出 endpoint，发起带有妥善错误处理的 HTTP 请求，并包含有用的注释。代码遵循最佳实践。

**Score 0.75**: 脚本可用，仅有小问题。能读取配置并发起请求，但可能缺少全面的错误处理，或存在轻微的代码质量问题。

**Score 0.5**: 脚本具备基本功能，但存在明显问题。可能错误处理不完整、结构较差，或缺少重要功能。

**Score 0.25**: 脚本写得很差或几乎无法运行。在逻辑、结构或错误处理方面存在重大问题。

**Score 0.0**: 脚本无法运行、缺失，或完全未能满足要求。

### Criterion 2: Documentation Quality (Weight: 30%)

**Score 1.0**: NOTES.md 内容全面、组织良好，清晰地说明了做了什么、脚本如何工作以及如何使用它。包含关于配置结构以及所做任何假设的相关细节。

**Score 0.75**: 文档良好，涵盖了大部分重点。在说明或组织上有少量欠缺。

**Score 0.5**: 有基本的文档，但缺乏细节或清晰度。缺少关于用法或实现的重要信息。

**Score 0.25**: 文档较差。信息极少或说明不清。

**Score 0.0**: 文档缺失或完全不充分。

### Criterion 3: Process Understanding (Weight: 25%)

**Score 1.0**: 有清晰证据表明 Agent 理解了这一多步骤工作流。正确地从配置中提取了 endpoint，创建了合适的脚本，并合乎逻辑地记录了整个过程。展现出良好的决策能力。

**Score 0.75**: 理解良好，仅有小问题。过程大体正确，逻辑或执行上有小缺口。

**Score 0.5**: 部分理解。Agent 完成了一些步骤，但遗漏了环节衔接或做出了有疑问的决策。

**Score 0.25**: 理解较差。Agent 在工作流上遇到困难，或在过程中犯了重大错误。

**Score 0.0**: 没有任何理解任务要求的证据。

### Criterion 4: Overall Completeness (Weight: 15%)

**Score 1.0**: 满足所有要求。读取了配置、提取了 endpoint、创建了可用脚本、提供了全面文档。任务完全完成。

**Score 0.75**: 满足大部分要求，仅有小遗漏。任务基本完成。

**Score 0.5**: 满足部分要求，但存在明显缺口。任务部分完成。

**Score 0.25**: 仅满足少数要求。任务几乎未尝试。

**Score 0.0**: 任务未完成或完全失败。
