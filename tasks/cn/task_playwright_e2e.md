---
id: task_playwright_e2e
name: Playwright 端到端表单测试
category: 编程
scene: 本地环境、命令执行与脚本任务
sub_scene: 浏览器端到端测试生成
difficulty: L2
capabilities:
- 代码生成与理解
- 指令遵循与约束理解
- 多步推理
- 工具调用
- 输出格式适配
grading_type: hybrid
timeout_seconds: 300
workspace_files:
  - source: form.html
    dest: form.html
---

## Prompt

工作区中有一个文件 `form.html`——这是一个自包含的 3 步注册表单，仅使用纯 HTML、CSS 和 JavaScript 构建（不依赖任何框架）。你的任务是：

1. 仔细阅读 `form.html`，理解表单结构和导航逻辑
2. 编写一个 Playwright 端到端测试脚本，保存为 `test_form.py`
3. 脚本应使用 `playwright.sync_api`（Python 同步 API）
4. 依次完成全部 3 个步骤的导航：
   - 第 1 步：填写个人信息（全名、邮箱、电话）
   - 第 2 步：填写地址详情（街道、城市、州下拉框、邮编）
   - 第 3 步：核对回顾摘要中的数据是否正确，然后提交
5. 提交后，验证成功面板可见且包含一个提交 ID
6. 在每一步都校验 UI 状态（正确的步骤可见、进度条已更新）
7. 为选择器交互加入重试逻辑——若某个选择器失败，应在短暂延迟后最多重试 3 次
8. 将最终成功状态的截图保存为 `success.png`

该表单会对输入做校验（必填字段、邮箱格式、5 位邮编）——请提供能通过校验的数据。

在可用的地方使用 `data-testid` 选择器——它们是最稳健的选择器策略。

## Expected Behavior

Agent 应当：

1. 阅读 `form.html` 并分析 DOM 结构，注意 `data-testid` 属性、表单校验规则和步骤导航逻辑
2. 使用 `playwright.sync_api` 配合 `sync_playwright` 上下文管理器创建 `test_form.py`
3. 启动 Chromium 浏览器（无头模式）
4. 使用 `file://` URL 打开本地的 `form.html` 文件
5. 用有效的测试数据填写第 1 步字段（fullname、email、phone）
6. 点击 "Next"，验证第 2 步处于激活状态且第 1 步已隐藏
7. 用有效数据填写第 2 步字段（street、city、州下拉框、zip）
8. 点击 "Next"，验证第 3 步显示回顾摘要
9. 断言回顾值与所填写的内容一致
10. 点击 "Submit Registration"
11. 验证成功面板可见且包含一个提交 ID
12. 截取截图并保存为 `success.png`
13. 加入重试/等待逻辑，使不稳定的选择器不会立即导致测试失败
14. 使用恰当的 Playwright 模式：`page.locator()`、`data-testid` 选择器、`expect()` 断言

## Grading Criteria

### Automated Criteria (50%)

- [ ] 工作区中创建了文件 `test_form.py`
- [ ] 文件包含有效的 Python 语法
- [ ] 脚本从 `playwright.sync_api` 导入
- [ ] 脚本引用 `form.html` 来打开表单
- [ ] 脚本跨多个步骤填写字段（至少 5 处不同的字段交互）
- [ ] 脚本包含重试或显式等待逻辑
- [ ] 脚本包含用于状态校验的 assertion/expect 调用
- [ ] 脚本将截图保存到 `success.png`

### LLM Judge Criteria (50%)

- [ ] 多步导航的正确性
- [ ] 回顾数据断言的质量
- [ ] 错误处理与重试的健壮性
- [ ] 代码质量与 Playwright 最佳实践

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the Playwright E2E test task based on file creation and code quality.

    Args:
        transcript: Parsed JSONL transcript as list of dicts
        workspace_path: Path to the task's isolated workspace directory

    Returns:
        Dict mapping criterion names to scores (0.0 to 1.0)
    """
    from pathlib import Path
    import re
    import ast

    scores = {}
    workspace = Path(workspace_path)

    # Check if test_form.py exists
    script_file = workspace / "test_form.py"

    if not script_file.exists():
        scores["file_created"] = 0.0
        scores["valid_python"] = 0.0
        scores["imports_playwright"] = 0.0
        scores["references_form_html"] = 0.0
        scores["fills_multiple_fields"] = 0.0
        scores["has_retry_or_wait"] = 0.0
        scores["has_assertions"] = 0.0
        scores["saves_screenshot"] = 0.0
        return scores

    scores["file_created"] = 1.0

    # Read file content
    content = script_file.read_text()

    # Check for valid Python syntax
    try:
        ast.parse(content)
        scores["valid_python"] = 1.0
    except SyntaxError:
        scores["valid_python"] = 0.0
        scores["imports_playwright"] = 0.0
        scores["references_form_html"] = 0.0
        scores["fills_multiple_fields"] = 0.0
        scores["has_retry_or_wait"] = 0.0
        scores["has_assertions"] = 0.0
        scores["saves_screenshot"] = 0.0
        return scores

    # Check for Playwright import
    pw_patterns = [
        r'from\s+playwright\.sync_api\s+import',
        r'from\s+playwright\.async_api\s+import',
        r'from\s+playwright\s+import',
        r'import\s+playwright',
    ]
    if any(re.search(p, content) for p in pw_patterns):
        scores["imports_playwright"] = 1.0
    else:
        scores["imports_playwright"] = 0.0

    # Check for form.html reference
    form_patterns = [
        r'form\.html',
        r'form_html',
    ]
    if any(re.search(p, content, re.IGNORECASE) for p in form_patterns):
        scores["references_form_html"] = 1.0
    else:
        scores["references_form_html"] = 0.0

    # Check for multiple field fills using AST to count actual method calls
    # This avoids penalizing DRY code with helper functions
    try:
        tree = ast.parse(content)
        fill_methods = {'fill', 'type', 'select_option', 'check', 'click', 'press'}
        fill_calls = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Handle method calls (obj.fill(), obj.type(), etc.)
                if isinstance(node.func, ast.Attribute) and node.func.attr in fill_methods:
                    fill_calls.append(node.func.attr)
        
        fill_count = len(fill_calls)
        if fill_count >= 10:
            scores["fills_multiple_fields"] = 1.0
        elif fill_count >= 5:
            scores["fills_multiple_fields"] = 0.75
        elif fill_count >= 3:
            scores["fills_multiple_fields"] = 0.5
        else:
            scores["fills_multiple_fields"] = 0.0
    except Exception:
        # Fall back to regex if AST parsing fails
        fill_patterns = [
            r'\.fill\s*\(',
            r'\.type\s*\(',
            r'\.select_option\s*\(',
            r'\.check\s*\(',
            r'\.click\s*\(',
            r'\.press\s*\(',
        ]
        fill_count = sum(len(re.findall(p, content)) for p in fill_patterns)
        if fill_count >= 10:
            scores["fills_multiple_fields"] = 1.0
        elif fill_count >= 5:
            scores["fills_multiple_fields"] = 0.75
        elif fill_count >= 3:
            scores["fills_multiple_fields"] = 0.5
        else:
            scores["fills_multiple_fields"] = 0.0

    # Check for retry or wait logic
    retry_patterns = [
        r'retry',
        r'attempt',
        r'max_retries',
        r'max_attempts',
        r'tries',
        r'wait_for',
        r'wait_for_selector',
        r'wait_for_timeout',
        r'time\.sleep',
        r'expect\s*\(',
        r'to_be_visible',
        r'to_be_hidden',
    ]
    retry_count = sum(1 for p in retry_patterns if re.search(p, content, re.IGNORECASE))
    if retry_count >= 3:
        scores["has_retry_or_wait"] = 1.0
    elif retry_count >= 1:
        scores["has_retry_or_wait"] = 0.5
    else:
        scores["has_retry_or_wait"] = 0.0

    # Check for assertions
    assert_patterns = [
        r'assert\s+',
        r'expect\s*\(',
        r'to_be_visible',
        r'to_have_text',
        r'to_contain_text',
        r'to_have_value',
        r'is_visible\s*\(',
        r'inner_text\s*\(',
        r'text_content\s*\(',
    ]
    assert_count = sum(1 for p in assert_patterns if re.search(p, content))
    if assert_count >= 4:
        scores["has_assertions"] = 1.0
    elif assert_count >= 2:
        scores["has_assertions"] = 0.75
    elif assert_count >= 1:
        scores["has_assertions"] = 0.5
    else:
        scores["has_assertions"] = 0.0

    # Check for screenshot
    screenshot_patterns = [
        r'screenshot\s*\(',
        r'success\.png',
    ]
    if any(re.search(p, content) for p in screenshot_patterns):
        scores["saves_screenshot"] = 1.0
    else:
        scores["saves_screenshot"] = 0.0

    return scores
```

## LLM Judge Rubric

### Criterion 1: Multi-Step Navigation (Weight: 30%)

**Score 1.0**：脚本正确地按顺序导航全部 3 个表单步骤。每次步骤切换都很明确——填写字段、点击 Next，并在继续前验证新步骤已激活。使用 `select_option` 处理州下拉框。回退导航经过测试，或至少没有被破坏。

**Score 0.75**：全部 3 个步骤导航正确，但存在小问题（例如步骤切换之间没有显式等待，或用 click 而非 select_option 处理州下拉框）。

**Score 0.5**：3 个步骤中有 2 个处理正确，或 3 个都尝试了但字段名错误，或缺少能通过校验的数据。

**Score 0.25**：仅处理了 1 个步骤，或导航逻辑存在根本性缺陷。

**Score 0.0**：没有进行任何有意义的步骤导航。

### Criterion 2: Review Data Assertions (Weight: 25%)

**Score 1.0**：脚本验证第 3 步回顾摘要显示的内容与第 1、2 步所填写的数据完全一致。用文本内容断言检查至少 3 个回顾字段（姓名、邮箱、地址）。

**Score 0.75**：用正确的断言验证了 2 个以上回顾字段。

**Score 0.5**：检查了回顾步骤可见，但没有验证具体的数据值。

**Score 0.25**：回顾断言很少或不正确。

**Score 0.0**：没有进行任何回顾验证。

### Criterion 3: Error Handling & Retry (Weight: 25%)

**Score 1.0**：实现了带可配置最大尝试次数（3+）的重试封装，捕获特定的 Playwright 异常（TimeoutError 或类似异常），重试之间包含延迟，并具备恰当的清理（在 finally 块中调用 browser.close）。

**Score 0.75**：具有 2 次以上尝试的重试逻辑和基本的错误捕获。清理方面有小缺口。

**Score 0.5**：使用 Playwright 内置的等待（wait_for_selector、expect），但没有自定义重试循环。

**Score 0.25**：错误处理很少——仅有基本的 try/except，没有重试。

**Score 0.0**：完全没有错误处理。

### Criterion 4: Code Quality & Best Practices (Weight: 20%)

**Score 1.0**：代码整洁、组织良好。一致地使用 `data-testid` 选择器。为 playwright 使用恰当的上下文管理器。用函数/类封装可复用逻辑。变量名有意义。注释解释了不明显的选择。

**Score 0.75**：代码质量良好，仅有小的风格问题。大多使用 data-testid 选择器。

**Score 0.5**：可运行但组织混乱。好的选择器与脆弱的选择器混用。没有辅助函数。

**Score 0.25**：代码混乱、硬编码值、通篇使用脆弱的 CSS/XPath 选择器。

**Score 0.0**：代码无法运行或无法理解。
