---
id: task_second_brain
name: 第二大脑知识持久化
category: 记忆
scene: 本地环境、命令执行与脚本任务
sub_scene: 基于文件的记忆持久化
difficulty: L2
capabilities:
- 上下文记忆与状态管理
- 工具调用
- 输出格式适配
- 幻觉抑制
grading_type: hybrid
timeout_seconds: 300
multi_session: true
sessions:
  - id: store_knowledge
    prompt: |
      我想让你帮我记住这些重要信息。请将其保存到名为 `memory/MEMORY.md` 的文件中，以便你（或未来的会话）稍后可以调用它：

      我最喜欢的编程语言是 Rust。我于 2024 年 1 月 15 日开始学习它。我的导师名叫 Dr. Elena Vasquez，来自斯坦福大学。我正在做的项目叫 "NeonDB"——它是一个分布式键值存储。我们团队的秘密口令是 "purple elephant sunrise"。

      将此信息保存到 `memory/MEMORY.md` 并确认你已存储。
  - id: conversation
    prompt: |
      我正在学习什么编程语言？我当前项目的名称是什么？如果需要可以查看 memory/MEMORY.md 文件。
  - id: new_session_recall
    new_session: true
    prompt: |
      我之前在一个名为 `memory/MEMORY.md` 的文件中保存了一些个人信息。请阅读该文件并回答以下问题：
      1. 我最喜欢的编程语言是什么？
      2. 我什么时候开始学习它的？
      3. 我的导师名字和所属机构是什么？
      4. 我的项目叫什么，它是做什么的？
      5. 我们团队的秘密口令是什么？

      请根据你在文件中找到的内容回答所有 5 个问题。
workspace_files: []
---

## Prompt

这是一个多会话任务。请参见 frontmatter 中的 `sessions` 字段以了解提示序列。

## Expected Behavior

Agent 应当：

1. **会话 1（存储知识）**：
   - 接收要记住的个人信息
   - 如需要则创建 `memory/` 目录
   - 以结构化格式将信息保存到 `memory/MEMORY.md`
   - 确认信息已存储到文件
   - 这测试 Agent 通过文件存储持久化信息的能力

2. **会话 2（对话）**：
   - 从同一会话中调用信息（或通过读取文件）
   - 正确回答用户正在学习 Rust
   - 正确陈述项目名为 NeonDB

3. **会话 3（新会话调用）**：
   - 启动全新会话（模拟用户稍后返回）
   - 读取会话 1 中创建的 `memory/MEMORY.md` 文件
   - 准确调用全部 5 条信息：
     - 最喜欢的语言：Rust
     - 开始日期：2024 年 1 月 15 日
     - 导师：Dr. Elena Vasquez，来自斯坦福大学
     - 项目：NeonDB，一个分布式键值存储
     - 秘密口令："purple elephant sunrise"

这测试 Agent 通过文件存储持久化知识并在新会话中检索的能力。

## Grading Criteria

- [ ] Agent 在记忆系统中存储信息（会话 1）
- [ ] Agent 确认信息存储（会话 1）
- [ ] Agent 在同一会话中正确调用语言和项目（会话 2）
- [ ] Agent 在新会话中尝试记忆调用（会话 3）
- [ ] 正确调取最喜欢的语言（Rust）
- [ ] 正确调取开始日期（2024 年 1 月 15 日）
- [ ] 正确调取导师名字和所属机构（Dr. Elena Vasquez，斯坦福）
- [ ] 正确调取项目名称（NeonDB）
- [ ] 正确调取项目描述（分布式键值存储）
- [ ] 正确调取秘密口令（purple elephant sunrise）

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the second brain knowledge persistence task.

    Checks if the agent created the memory file with correct content.

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

    # Check if memory file was created
    memory_file = workspace / "memory" / "MEMORY.md"
    if not memory_file.exists():
        # Try alternative paths
        alt_paths = [
            workspace / "MEMORY.md",
            workspace / "memory.md",
        ]
        for alt in alt_paths:
            if alt.exists():
                memory_file = alt
                break

    if memory_file.exists():
        scores["memory_tool_used"] = 1.0
        content = memory_file.read_text().lower()

        # Check for key facts in the file
        has_rust = "rust" in content
        has_date = "january" in content and "2024" in content
        has_mentor = "elena" in content and "vasquez" in content
        has_project = "neondb" in content
        has_phrase = "purple" in content and "elephant" in content and "sunrise" in content

        fact_count = sum([has_rust, has_date, has_mentor, has_project, has_phrase])
        scores["recall_tool_used"] = fact_count / 5.0
    else:
        scores["memory_tool_used"] = 0.0
        scores["recall_tool_used"] = 0.0

    return scores
```

## LLM Judge Rubric

### Criterion 1: Memory Storage (Weight: 15%)

**Score 1.0**：Agent 创建 `memory/MEMORY.md` 文件，用清晰、有组织的格式存储用户的全部信息。确认文件已创建。
**Score 0.75**：Agent 将信息保存到文件，但使用不同路径或格式。存储功能正常。
**Score 0.5**：Agent 确认了信息，但存储到文件不完整或混乱。
**Score 0.25**：Agent 只是重复信息而没有保存到文件。
**Score 0.0**：Agent 未尝试存储信息或忽略请求。

### Criterion 2: Same-Session Recall (Weight: 15%)

**Score 1.0**：Agent 在会话 2 中毫不犹豫地正确回答两个问题（Rust、NeonDB）。
**Score 0.75**：Agent 正确回答两个问题，但有轻微的不确定性。
**Score 0.5**：Agent 正确回答一个，遗漏或错答另一个。
**Score 0.25**：Agent 严重挣扎但显示出一些记忆。
**Score 0.0**：Agent 无法调用信息或给出错误答案。

### Criterion 3: Cross-Session Memory Retrieval (Weight: 20%)

**Score 1.0**：Agent 在新会话中读取 `memory/MEMORY.md` 文件并成功检索存储的信息。
**Score 0.75**：Agent 检索大部分信息，但采取额外步骤或先读取错误文件。
**Score 0.5**：Agent 尝试检索但仅部分成功找到文件。
**Score 0.25**：Agent 对读取记忆文件做出最少努力。
**Score 0.0**：Agent 未尝试读取文件或声称没有记忆存在。

### Criterion 4: Accuracy of Recalled Facts (Weight: 40%)

**Score 1.0**：全部 5 条事实调取正确：

- Rust 作为最喜欢的语言
- 2024 年 1 月 15 日作为开始日期
- Dr. Elena Vasquez，来自斯坦福大学，作为导师
- NeonDB 作为项目名称（分布式键值存储）
- "purple elephant sunrise" 作为秘密口令

**Score 0.8**：5 条中 4 条正确，没有编造内容。
**Score 0.6**：5 条中 3 条正确，没有编造内容。
**Score 0.4**：5 条中 2 条正确，或更多条有轻微不准确。
**Score 0.2**：1 条事实正确或有显著不准确。
**Score 0.0**：没有事实正确或 Agent 编造了未提供的信息。

### Criterion 5: Response Quality and Confidence (Weight: 10%)

**Score 1.0**：Agent 自信、清晰地呈现调取的信息，展示可靠的第二大脑功能。
**Score 0.75**：回应清晰但显示轻微不确定。
**Score 0.5**：回应组织混乱或显著犹豫。
**Score 0.25**：回应令人困惑或 Agent 表达重大不确定。
**Score 0.0**：Agent 拒绝回答或提供不连贯的回应。

## Additional Notes

- 本任务测试"第二大脑"范式，即 AI Agent 使用文件存储跨会话持久化用户知识
- 文件 `memory/MEMORY.md` 充当简单但有效的持久化机制
- 秘密口令 "purple elephant sunrise" 是故意设计为任意的，以测试逐字调用 vs 语义理解
- 带有 `new_session: true` 的多会话格式模拟用户关闭并重新打开 Agent 后返回
- 成功创建并读取记忆文件的 Agent 在跨会话调用上应得高分
- 本任务测试实用的基于文件的记忆/笔记功能
