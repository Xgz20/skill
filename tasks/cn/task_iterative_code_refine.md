---
id: task_iterative_code_refine
name: 迭代式代码精炼
category: 编程
scene: 本地环境、命令执行与脚本任务
sub_scene: 迭代式代码精炼
difficulty: L2
capabilities:
- 代码生成与理解
- 上下文记忆与状态管理
- 指令遵循与约束理解
- 自我纠错与反思
- 输出格式适配
grading_type: automated
timeout_seconds: 300
multi_session: true
sessions:
  - id: initial_implementation
    prompt: |
      创建一个名为 `calculator.py` 的 Python 脚本，实现一个简单的计算器，包含以下函数：
      1. `add(a, b)` — 返回 a + b
      2. `subtract(a, b)` — 返回 a - b
      3. `multiply(a, b)` — 返回 a * b
      4. `divide(a, b)` — 返回 a / b（暂不做错误处理）

      将其保存为工作区中的 `calculator.py`。
  - id: add_error_handling
    prompt: |
      我注意到 `divide` 函数没有处理除以零的情况。请更新 `calculator.py`：
      1. 让 `divide(a, b)` 在 b 为 0 时抛出一个带有消息 "Cannot divide by zero" 的 `ValueError`
      2. 添加一个 `power(a, b)` 函数，返回 a ** b
      3. 添加一个 `modulo(a, b)` 函数，返回 a % b（同样在此处理除以零的情况）

      保留所有现有函数，只需添加上述改进。
  - id: final_review
    new_session: true
    prompt: |
      请阅读工作区中的文件 `calculator.py`，并核实它具备以下特性：
      1. 函数：add、subtract、multiply、divide、power、modulo
      2. divide 和 modulo 在除以零时都会抛出 ValueError
      3. 所有函数都能正确运行

      然后将你的核实结果写入 `review.txt`。包括存在哪些函数以及是否具备错误处理。
workspace_files: []
---

## Prompt

这是一个多会话任务。请参阅 frontmatter 中的 `sessions` 字段以获取提示词序列。

## Expected Behavior

Agent 应当：

1. **会话 1（初始实现）**：
   - 创建 `calculator.py`，包含 add、subtract、multiply 和 divide 函数
   - 初始的 divide 函数应仅返回 a / b，不做错误处理

2. **会话 2（添加错误处理）**：
   - 修改现有的 `calculator.py`，为 divide 添加错误处理
   - 添加 power 和 modulo 函数
   - 保留现有函数

3. **会话 3（最终审查——新会话）**：
   - 在没有对话历史的全新会话中开始
   - 从工作区读取 `calculator.py`
   - 核实所有函数都存在且错误处理正确
   - 将核实结果写入 `review.txt`

本任务测试 Agent 跨对话轮次迭代精炼代码的能力，以及在仅使用基于文件的上下文的全新会话中核实自身工作的能力。

## Grading Criteria

- [ ] `calculator.py` 存在且包含 add、subtract、multiply 函数
- [ ] `calculator.py` 的 divide 函数对零会抛出 ValueError
- [ ] `calculator.py` 有 power 函数
- [ ] `calculator.py` 的 modulo 函数对零会抛出 ValueError
- [ ] `review.txt` 存在且提及全部 6 个函数
- [ ] `review.txt` 提及错误处理 / ValueError

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the iterative code refinement task.

    Checks calculator.py for required functions and error handling,
    and review.txt for verification content.
    """
    from pathlib import Path
    import re

    scores = {}
    workspace = Path(workspace_path)

    # --- Check calculator.py ---
    calc_file = workspace / "calculator.py"
    calc_content = ""
    if calc_file.exists():
        calc_content = calc_file.read_text()

    # Basic functions
    has_add = bool(re.search(r'def\s+add\s*\(', calc_content))
    has_subtract = bool(re.search(r'def\s+subtract\s*\(', calc_content))
    has_multiply = bool(re.search(r'def\s+multiply\s*\(', calc_content))
    has_basic = sum([has_add, has_subtract, has_multiply])
    scores["basic_functions"] = has_basic / 3.0

    # Divide with error handling
    has_divide = bool(re.search(r'def\s+divide\s*\(', calc_content))
    has_divide_error = has_divide and bool(re.search(r'ValueError.*divide.*zero|Cannot divide by zero', calc_content, re.IGNORECASE))
    scores["divide_error_handling"] = 1.0 if has_divide_error else (0.5 if has_divide else 0.0)

    # Power function
    has_power = bool(re.search(r'def\s+power\s*\(', calc_content))
    scores["power_function"] = 1.0 if has_power else 0.0

    # Modulo with error handling
    has_modulo = bool(re.search(r'def\s+modulo\s*\(', calc_content))
    has_modulo_error = has_modulo and bool(re.search(r'ValueError.*zero|Cannot divide by zero', calc_content, re.IGNORECASE))
    scores["modulo_error_handling"] = 1.0 if has_modulo_error else (0.5 if has_modulo else 0.0)

    # --- Check review.txt ---
    review_file = workspace / "review.txt"
    review_content = ""
    if review_file.exists():
        review_content = review_file.read_text().lower()

    # Review mentions all functions
    review_mentions = sum([
        "add" in review_content,
        "subtract" in review_content,
        "multiply" in review_content,
        "divide" in review_content,
        "power" in review_content,
        "modulo" in review_content,
    ])
    scores["review_functions"] = review_mentions / 6.0

    # Review mentions error handling
    review_mentions_errors = bool(re.search(r'error|valueerror|zero|handling', review_content, re.IGNORECASE))
    scores["review_error_handling"] = 1.0 if review_mentions_errors else 0.0

    return scores
```

## Additional Notes

- 本任务专门测试多轮迭代精炼——Agent 必须修改自己先前的工作
- 最终会话上的 `new_session: true` 测试 Agent 能否使用基于文件的上下文（读取 calculator.py），而非依赖对话历史
- 一个好的 Agent 应当在会话 2 中保留现有代码的同时添加新特性
- 会话 3 中的审查应当表明 Agent 能够独立核实自己的工作
