---
id: task_test_generation
name: 测试生成
category: 编程
scene: 本地环境、命令执行与脚本任务
sub_scene: 单元测试生成
difficulty: L2
capabilities:
- 代码生成与理解
- 指令遵循与约束理解
- 多步推理
- 工具调用
grading_type: hybrid
timeout_seconds: 180
grading_weights:
  automated: 0.6
  llm_judge: 0.4
workspace_files:
  - source: order_processor.py
    dest: order_processor.py
---

# 测试生成

## Prompt

工作区中的 `order_processor.py` 文件包含了一个用于电商订单流程的 `OrderProcessor` 类。请为这个模块编写一份全面的测试套件，并保存为工作区中的 `test_order_processor.py`。

要求：

1. 使用 `pytest` 作为测试框架
2. 测试 `OrderProcessor` 的每一个公开方法
3. 包含边缘情况的测试：空订单、零数量商品、未知区域、优惠券叠加行为、缺货商品
4. 测试无效输入时是否会抛出 `InvalidOrderError`
5. 使用 fixtures 或工厂辅助函数避免重复的测试设置
6. 以高分支覆盖率为目标 —— 测试每个条件分支的两侧

不要修改 `order_processor.py`。

## Expected Behavior

Agent 应当：

1. 阅读 `order_processor.py` 并理解所有公开方法、类常量和异常类型
2. 创建包含 pytest 风格测试的 `test_order_processor.py`
3. 覆盖所有 7 个公开方法：`validate_order`、`calculate_subtotal`、`apply_discount`、`calculate_tax`、`check_stock`、`estimate_delivery`、`process_order`
4. 测试每个方法的正常路径和异常路径
5. 使用 `pytest.raises` 进行异常测试
6. 使用 fixtures 或辅助函数来减少测试数据重复
7. 编写实际针对源模块运行时能够通过的测试

## Grading Criteria

### Automated Criteria (60%)

- [ ] 工作区中已创建文件 `test_order_processor.py`
- [ ] 文件包含合法的 Python 语法
- [ ] 文件导入 pytest
- [ ] 文件从 order_processor 模块导入
- [ ] 测试覆盖 validate_order（包括异常情况）
- [ ] 测试覆盖 calculate_subtotal
- [ ] 测试覆盖 apply_discount（层级与优惠券）
- [ ] 测试覆盖 calculate_tax
- [ ] 测试覆盖 check_stock
- [ ] 测试覆盖 estimate_delivery
- [ ] 测试覆盖 process_order（集成）
- [ ] 测试实际执行时能通过

### LLM Judge Criteria (40%)

- [ ] 边缘情况覆盖质量
- [ ] 测试组织与可读性
- [ ] fixtures 和辅助函数的使用
- [ ] 断言质量与具体性

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    from pathlib import Path
    import re
    import ast
    import subprocess
    import sys

    scores = {
        "file_created": 0.0,
        "valid_python": 0.0,
        "imports_pytest": 0.0,
        "imports_module": 0.0,
        "tests_validate_order": 0.0,
        "tests_calculate_subtotal": 0.0,
        "tests_apply_discount": 0.0,
        "tests_calculate_tax": 0.0,
        "tests_check_stock": 0.0,
        "tests_estimate_delivery": 0.0,
        "tests_process_order": 0.0,
        "tests_pass": 0.0,
    }

    workspace = Path(workspace_path)
    test_file = workspace / "test_order_processor.py"
    source_file = workspace / "order_processor.py"

    if not test_file.exists():
        return scores
    scores["file_created"] = 1.0

    content = test_file.read_text(encoding="utf-8")

    try:
        ast.parse(content)
        scores["valid_python"] = 1.0
    except SyntaxError:
        return scores

    # Check imports
    if re.search(r"import\s+pytest|from\s+pytest\s+import", content):
        scores["imports_pytest"] = 1.0

    if re.search(r"from\s+order_processor\s+import|import\s+order_processor", content):
        scores["imports_module"] = 1.0

    # Check coverage of each method by looking for method name references in test functions
    method_checks = {
        "tests_validate_order": [r"validate_order", r"InvalidOrderError"],
        "tests_calculate_subtotal": [r"calculate_subtotal"],
        "tests_apply_discount": [r"apply_discount"],
        "tests_calculate_tax": [r"calculate_tax"],
        "tests_check_stock": [r"check_stock"],
        "tests_estimate_delivery": [r"estimate_delivery"],
        "tests_process_order": [r"process_order"],
    }

    for score_key, patterns in method_checks.items():
        if any(re.search(p, content) for p in patterns):
            scores[score_key] = 1.0

    # Try to actually run the tests
    if source_file.exists():
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short", "-q"],
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=30,
            )
            # Parse pytest output for pass/fail counts
            output = result.stdout + result.stderr
            passed_match = re.search(r"(\d+)\s+passed", output)
            failed_match = re.search(r"(\d+)\s+failed", output)

            passed = int(passed_match.group(1)) if passed_match else 0
            failed = int(failed_match.group(1)) if failed_match else 0
            total = passed + failed

            if total > 0:
                pass_rate = passed / total
                if pass_rate == 1.0:
                    scores["tests_pass"] = 1.0
                elif pass_rate >= 0.8:
                    scores["tests_pass"] = 0.75
                elif pass_rate >= 0.5:
                    scores["tests_pass"] = 0.5
                else:
                    scores["tests_pass"] = 0.25
        except (subprocess.TimeoutExpired, Exception):
            scores["tests_pass"] = 0.0

    return scores
```

## LLM Judge Rubric

### Criterion 1: Edge Case Coverage (Weight: 35%)

**Score 1.0**：测试覆盖所有重要边缘情况：空商品列表、零数量、负价格、未知区域（0% 税率）、所有折扣层级与边界、优惠券代码（SAVE20、WELCOME10、无效/None）、优惠券与层级不叠加、空仓库库存、部分库存、优先与标准配送、加拿大与美国区域。

**Score 0.75**：大多数边缘情况覆盖（上述 8+ 项）。边界测试存在小缺漏。

**Score 0.5**：覆盖了几个边缘情况，但缺少重要场景，如折扣层级边界或优惠券叠加行为。

**Score 0.25**：只有基本的正常路径测试和 1-2 个边缘情况。

**Score 0.0**：没有有意义的边缘情况测试。

### Criterion 2: Test Organization and Readability (Weight: 25%)

**Score 1.0**：测试逻辑分组（按方法或功能）。测试名称清晰、描述性强，遵循一致的命名约定（例如 `test_<method>_<scenario>`）。测试类或模块级的组织结构清晰。易于理解每个测试验证的内容。

**Score 0.75**：组织良好，命名或分组上有小的不一致。

**Score 0.5**：测试可运行，但组织较差 —— 所有测试平铺在一个列表中，名称不清晰。

**Score 0.25**：杂乱无章，难以理解，结构不一致。

**Score 0.0**：没有有意义的组织。

### Criterion 3: Use of Fixtures and Helpers (Weight: 20%)

**Score 1.0**：使用 `@pytest.fixture` 进行共享测试设置（例如样本订单、预加载库存的处理器实例）。辅助函数或参数化装饰器减少了重复。没有复制粘贴的测试数据块。

**Score 0.75**：有一些 fixture 使用，但偶尔存在重复。

**Score 0.5**：最少的 fixture 使用 —— 大多数测试内联构造数据，但没有过度重复。

**Score 0.25**：测试间存在大量重复，没有 fixtures 或辅助函数。

**Score 0.0**：每个测试都完全独立，设置代码重复。

### Criterion 4: Assertion Quality (Weight: 20%)

**Score 1.0**：断言具体且有意义 —— 检查精确值，使用 `pytest.approx` 处理浮点数，验证字典的键和值，使用带匹配模式的 `pytest.raises` 处理异常。在适当时每个测试有多个断言以验证完整行为。

**Score 0.75**：断言良好，存在小缺陷（例如缺少浮点数容差，raises 上没有匹配模式）。

**Score 0.5**：基本断言确认了行为，但缺乏精确度（例如只检查真值性，而非具体值）。

**Score 0.25**：断言较弱 —— 主要检查类型或存在性，而非值。

**Score 0.0**：没有有意义的断言，或仅有简单的 `assert True` 检查。

## Additional Notes

- 本任务评估 Agent 从阅读源代码生成有用的、可运行测试的能力。
- 源模块是独立的，没有外部依赖，因此测试只需安装 pytest 即可运行。
- 评分权重为 60% 自动化 / 40% LLM 评判，反映了功能正确性和测试质量的重要性。
- 来源：Issue #140（ClawBytes: Test Factory）
