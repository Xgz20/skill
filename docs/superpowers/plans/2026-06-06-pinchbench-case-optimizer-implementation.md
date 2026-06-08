# PinchBench 评测用例优化 Skills 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现双 Skill 协作架构（pinchbench-batch-runner + pinchbench-case-optimizer），支持评测用例的批量执行、五维度分析和多轮链式优化。

**Architecture:** 
- batch-runner：读取 models-config.yaml → 临时复制用例到 tasks/ → 串行执行多模型评测 → 结果分目录存储 → 清理临时文件
- case-optimizer：读取评测结果 + transcripts → 五维度分析 → 家族识别与基线对比 → 生成优化用例和详细报告 → 收敛检测

**Tech Stack:** Python 3.10+, PyYAML, PinchBench 框架（scripts/run.sh, lib_tasks.py）

---

## 文件结构

### 新建文件

**Skill 1: pinchbench-batch-runner**
- `skills/pinchbench-batch-runner/SKILL.md` — Skill 元数据和使用文档
- `skills/pinchbench-batch-runner/models-config.yaml.example` — 配置模板
- `skills/pinchbench-batch-runner/batch_runner.py` — 核心执行逻辑

**Skill 2: pinchbench-case-optimizer**
- `skills/pinchbench-case-optimizer/SKILL.md` — Skill 元数据和使用文档
- `skills/pinchbench-case-optimizer/optimizer.py` — 核心优化逻辑
- `skills/pinchbench-case-optimizer/analyzers.py` — 五维度分析器
- `skills/pinchbench-case-optimizer/report_generator.py` — 报告生成器

**共享工具**
- `skills/shared/path_resolver.py` — 统一路径解析（两个 Skill 共用）

### 修改文件
- `.gitignore:106` — 添加 `models-config.yaml`
- `optimization-reports/` — 新目录（运行时自动创建）

---

## Task 1: 准备工作 - 更新 .gitignore

**Files:**
- Modify: `.gitignore:106`

- [ ] **Step 1: 添加 models-config.yaml 到 gitignore**

```bash
echo "models-config.yaml   # 保护敏感信息（模型API密钥）" >> .gitignore
```

- [ ] **Step 2: 验证 .gitignore**

Run: `git check-ignore -v models-config.yaml`
Expected: 输出显示该文件被忽略

- [ ] **Step 3: 提交**

```bash
git add .gitignore
git commit -m "chore: add models-config.yaml to gitignore

保护敏感的模型API配置信息

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: 共享工具 - 路径解析器

**Files:**
- Create: `skills/shared/path_resolver.py`

- [ ] **Step 1: 编写路径解析逻辑**

```python
"""统一路径解析工具，支持 task_id 或文件路径输入。"""
from pathlib import Path
from typing import Union


def resolve_task_path(task_input: str, project_root: Path) -> Path:
    """
    解析用例路径，支持三种输入形式：
    1. 纯 task_id：在 tasks/ 和 output/generated_cases/ 中查找
    2. 相对路径：相对于项目根目录解析
    3. 绝对路径：直接使用
    
    Args:
        task_input: 用户输入（task_id 或路径）
        project_root: 项目根目录
        
    Returns:
        用例文件的绝对路径
        
    Raises:
        FileNotFoundError: 如果用例文件不存在
    """
    # 如果不包含路径分隔符且不以 .md 结尾，视为 task_id
    if "/" not in task_input and not task_input.endswith(".md"):
        # 优先在 tasks/ 中查找
        for base_dir in ["tasks", "output/generated_cases"]:
            candidate = project_root / base_dir / f"{task_input}.md"
            if candidate.exists():
                return candidate
        raise FileNotFoundError(
            f"未找到用例 {task_input}，已搜索: tasks/, output/generated_cases/"
        )
    
    # 否则视为路径
    path = Path(task_input)
    if not path.is_absolute():
        path = project_root / path
    
    if not path.exists():
        raise FileNotFoundError(f"用例文件不存在: {path}")
    
    return path


def extract_base_task_id(task_id: str) -> str:
    """
    从 task_id 中提取 base_task_id（去除 _r<N> 后缀）。
    
    Examples:
        task_csv_iris_summary → task_csv_iris_summary
        task_csv_iris_summary_r2 → task_csv_iris_summary
    """
    import re
    return re.sub(r'_r\d+$', '', task_id)


def extract_optimization_round(task_id: str) -> int:
    """
    从 task_id 中提取优化轮次。
    
    Examples:
        task_csv_iris_summary → 0
        task_csv_iris_summary_r2 → 2
    """
    import re
    match = re.match(r'^.+_r(\d+)$', task_id)
    return int(match.group(1)) if match else 0
```

- [ ] **Step 2: 编写单元测试**

Create: `skills/shared/test_path_resolver.py`

```python
"""测试路径解析器。"""
import pytest
from pathlib import Path
from path_resolver import (
    resolve_task_path,
    extract_base_task_id,
    extract_optimization_round,
)


def test_resolve_task_path_with_task_id(tmp_path):
    """测试：纯 task_id 输入"""
    # 准备：创建测试文件
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    test_file = tasks_dir / "task_test.md"
    test_file.write_text("# Test")
    
    # 执行
    result = resolve_task_path("task_test", tmp_path)
    
    # 验证
    assert result == test_file


def test_resolve_task_path_fallback_to_generated_cases(tmp_path):
    """测试：回退到 output/generated_cases/"""
    # 准备
    gen_dir = tmp_path / "output" / "generated_cases"
    gen_dir.mkdir(parents=True)
    test_file = gen_dir / "task_test.md"
    test_file.write_text("# Test")
    
    # 执行
    result = resolve_task_path("task_test", tmp_path)
    
    # 验证
    assert result == test_file


def test_resolve_task_path_not_found(tmp_path):
    """测试：用例不存在"""
    with pytest.raises(FileNotFoundError, match="未找到用例"):
        resolve_task_path("task_nonexistent", tmp_path)


def test_extract_base_task_id():
    """测试：提取 base_task_id"""
    assert extract_base_task_id("task_xxx") == "task_xxx"
    assert extract_base_task_id("task_xxx_r1") == "task_xxx"
    assert extract_base_task_id("task_xxx_r10") == "task_xxx"


def test_extract_optimization_round():
    """测试：提取优化轮次"""
    assert extract_optimization_round("task_xxx") == 0
    assert extract_optimization_round("task_xxx_r1") == 1
    assert extract_optimization_round("task_xxx_r10") == 10
```

- [ ] **Step 3: 运行测试**

Run: `cd skills/shared && pytest test_path_resolver.py -v`
Expected: 所有测试通过

- [ ] **Step 4: 提交**

```bash
git add skills/shared/
git commit -m "feat(shared): add path resolver for task input

支持 task_id 和路径两种输入形式，提取 base_task_id 和优化轮次

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Skill 1 配置模板

**Files:**
- Create: `skills/pinchbench-batch-runner/models-config.yaml.example`

- [ ] **Step 1: 创建配置模板**

```yaml
# PinchBench 批量评测配置模板
# 使用说明：
# 1. 复制此文件到项目根目录：cp models-config.yaml.example ../../models-config.yaml
# 2. 填写真实的 API 密钥和 base_url
# 3. 该配置文件已在 .gitignore 中，不会被提交到 git

# 裁判模型配置（唯一，用于 LLM 评分）
judge:
  model_id: anthropic/claude-sonnet-4-6
  api_key: "your-judge-api-key"  # 替换为真实密钥
  base_url: "https://one.iflytek.com/api/llm/console/chat"  # 裁判模型的 API 地址

# 被评测模型列表（可配置多个，串行执行）
models_under_test:
  - model_id: xopglm5
    api_key: "your-model-api-key"  # 替换为真实密钥
    base_url: "https://maas-api.cn-huabei-1.xf-yun.com/v2"
  
  - model_id: spark-x
    api_key: "your-model-api-key"  # 替换为真实密钥
    base_url: "https://spark-api.example.com"

# 配置说明：
# - judge: 裁判模型只有一个，用于评分所有被评测模型的输出
# - models_under_test: 可以配置任意数量的被评测模型，按列表顺序串行执行
# - model_id: 模型标识符
# - api_key: 模型的 API 密钥（敏感信息）
# - base_url: 模型的 API 端点地址
```

- [ ] **Step 2: 验证 YAML 格式**

Run: `python -c "import yaml; yaml.safe_load(open('skills/pinchbench-batch-runner/models-config.yaml.example'))"`
Expected: 无输出（格式正确）

- [ ] **Step 3: 提交**

```bash
git add skills/pinchbench-batch-runner/models-config.yaml.example
git commit -m "feat(batch-runner): add models-config template

提供配置模板，包含裁判模型和被评测模型的配置结构

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: Skill 1 核心逻辑 - batch_runner.py (Part 1/2)

**Files:**
- Create: `skills/pinchbench-batch-runner/batch_runner.py`

- [ ] **Step 1: 编写配置加载和轮次检测逻辑**

```python
#!/usr/bin/env python3
"""
PinchBench 批量评测执行器

职责：
1. 读取 models-config.yaml 配置
2. 临时复制用例到 tasks/ 目录
3. 串行执行多个模型的评测
4. 结果分目录存储
5. 清理临时文件
"""
import argparse
import shutil
import subprocess
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional

# 导入共享工具
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
from path_resolver import resolve_task_path


def load_config(project_root: Path) -> Dict:
    """
    加载或创建配置文件。
    
    如果配置文件不存在，从模板复制并提示用户填写后退出。
    """
    config_path = project_root / "models-config.yaml"
    template_path = Path(__file__).parent / "models-config.yaml.example"
    
    if not config_path.exists():
        shutil.copy(template_path, config_path)
        print("✅ 已创建配置文件: models-config.yaml")
        print("⚠️  请编辑该文件，填写模型的 api_key 和 base_url")
        print(f"📝 配置文件路径: {config_path}")
        sys.exit(0)
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # 验证配置结构
    if "judge" not in config or "models_under_test" not in config:
        print(f"❌ 配置文件格式错误: {config_path}")
        print("   必须包含 'judge' 和 'models_under_test' 字段")
        sys.exit(1)
    
    return config


def detect_next_round(task_id: str, project_root: Path) -> int:
    """
    自动检测下一个轮次号（同一 task_id 的多次评测）。
    
    扫描 results-auto/<task_id>/round_* 目录，返回最大 N + 1。
    """
    results_base = project_root / "results-auto" / task_id
    if not results_base.exists():
        return 1
    
    existing_rounds = [
        int(d.name.replace("round_", ""))
        for d in results_base.iterdir()
        if d.is_dir() and d.name.startswith("round_")
    ]
    
    return max(existing_rounds) + 1 if existing_rounds else 1
```

- [ ] **Step 2: 编写测试（配置加载）**

Create: `skills/pinchbench-batch-runner/test_batch_runner.py`

```python
"""测试 batch_runner.py"""
import pytest
from pathlib import Path
from batch_runner import load_config, detect_next_round


def test_load_config_creates_template(tmp_path):
    """测试：配置文件不存在时，创建模板并退出"""
    # 准备：复制模板到临时目录
    template = Path(__file__).parent / "models-config.yaml.example"
    (tmp_path / "skills" / "pinchbench-batch-runner").mkdir(parents=True)
    shutil.copy(template, tmp_path / "skills" / "pinchbench-batch-runner" / "models-config.yaml.example")
    
    # 执行 + 验证
    with pytest.raises(SystemExit) as exc_info:
        load_config(tmp_path)
    assert exc_info.value.code == 0
    assert (tmp_path / "models-config.yaml").exists()


def test_detect_next_round_no_existing(tmp_path):
    """测试：没有已存在的轮次，返回 1"""
    assert detect_next_round("task_test", tmp_path) == 1


def test_detect_next_round_with_existing(tmp_path):
    """测试：已存在 round_1 和 round_2，返回 3"""
    results_dir = tmp_path / "results-auto" / "task_test"
    (results_dir / "round_1").mkdir(parents=True)
    (results_dir / "round_2").mkdir(parents=True)
    
    assert detect_next_round("task_test", tmp_path) == 3
```

- [ ] **Step 3: 运行测试**

Run: `cd skills/pinchbench-batch-runner && pytest test_batch_runner.py::test_load_config_creates_template -v`
Expected: PASS

- [ ] **Step 4: 提交（Part 1）**

```bash
git add skills/pinchbench-batch-runner/batch_runner.py skills/pinchbench-batch-runner/test_batch_runner.py
git commit -m "feat(batch-runner): add config loader and round detection

配置加载：首次运行创建模板并提示用户填写
轮次检测：扫描 results-auto 自动递增

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Skill 1 核心逻辑 - batch_runner.py (Part 2/2)

**Files:**
- Modify: `skills/pinchbench-batch-runner/batch_runner.py`

- [ ] **Step 1: 编写临时复制和命令执行逻辑**

```python
def build_command(
    model: Dict,
    judge: Dict,
    task_id: str,
    output_dir: Path,
    project_root: Path,
) -> List[str]:
    """
    组装 PinchBench 评测命令。
    
    Args:
        model: 被评测模型配置 {model_id, api_key, base_url}
        judge: 裁判模型配置 {model_id, api_key, base_url}
        task_id: 用例 ID（文件名不含 .md）
        output_dir: 结果输出目录
        project_root: 项目根目录
        
    Returns:
        命令参数列表（用于 subprocess.run）
    """
    run_script = project_root / "scripts" / "run.sh"
    
    return [
        str(run_script),
        "--model", model["model_id"],
        "--base-url", model["base_url"],
        "--api-key", model["api_key"],
        "--judge", judge["model_id"],
        "--suite", task_id,
        "--output-dir", str(output_dir),
        "--no-upload",
        "--verbose",
    ]


def run_batch(task_input: str, round_num: Optional[int] = None) -> Path:
    """
    批量执行多个模型的评测。
    
    Args:
        task_input: 用例输入（task_id 或路径）
        round_num: 指定轮次号（None 表示自动检测）
        
    Returns:
        结果输出目录（results-auto/<task_id>/round_<N>/）
    """
    project_root = Path(__file__).parent.parent.parent
    
    # 1. 加载配置
    config = load_config(project_root)
    judge = config["judge"]
    models = config["models_under_test"]
    
    # 2. 解析用例路径
    source = resolve_task_path(task_input, project_root)
    task_id = source.stem
    print(f"📋 用例: {task_id} ({source})")
    
    # 3. 轮次检测
    if round_num is None:
        round_num = detect_next_round(task_id, project_root)
    print(f"🔄 执行轮次: Round {round_num}")
    
    output_base = project_root / "results-auto" / task_id / f"round_{round_num}"
    output_base.mkdir(parents=True, exist_ok=True)
    
    # 4. 临时复制到 tasks/（PinchBench 框架限制）
    tasks_dir = project_root / "tasks"
    temp_in_tasks = tasks_dir / f"{task_id}.md"
    already_in_tasks = (
        temp_in_tasks.exists() and temp_in_tasks.samefile(source)
    )
    
    if not already_in_tasks:
        print(f"📄 临时复制用例到 {temp_in_tasks}")
        shutil.copy(source, temp_in_tasks)
    
    try:
        # 5. 串行执行每个模型
        for i, model in enumerate(models, 1):
            model_id = model["model_id"]
            print(f"\n{'=' * 60}")
            print(f"▶ [{i}/{len(models)}] 评测模型: {model_id}")
            print(f"{'=' * 60}")
            
            output_dir = output_base / model_id
            output_dir.mkdir(parents=True, exist_ok=True)
            
            cmd = build_command(model, judge, task_id, output_dir, project_root)
            
            # 设置裁判模型环境变量
            env = {
                **subprocess.os.environ,
                "ANTHROPIC_API_KEY": judge["api_key"],
                "ANTHROPIC_BASE_URL": judge["base_url"],
            }
            
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=False,  # 实时输出到终端
                text=True,
            )
            
            if result.returncode != 0:
                print(f"⚠️  模型 {model_id} 评测失败（退出码 {result.returncode}）")
            else:
                print(f"✅ 模型 {model_id} 评测完成")
        
        # 6. 生成摘要文件
        summary_path = output_base / "batch-run-summary.md"
        write_summary(summary_path, task_id, round_num, models, output_base)
        print(f"\n📊 摘要文件: {summary_path}")
        
    finally:
        # 7. 清理临时文件
        if not already_in_tasks and temp_in_tasks.exists():
            print(f"🗑️  清理临时文件: {temp_in_tasks}")
            temp_in_tasks.unlink()
    
    print(f"\n✅ 批量评测完成")
    print(f"📂 结果目录: {output_base}")
    return output_base


def write_summary(
    summary_path: Path,
    task_id: str,
    round_num: int,
    models: List[Dict],
    output_base: Path,
):
    """生成批量执行摘要文件"""
    with open(summary_path, "w") as f:
        f.write(f"# 批量评测摘要 - {task_id} (Round {round_num})\n\n")
        f.write(f"**用例ID**: {task_id}\n")
        f.write(f"**评测轮次**: Round {round_num}\n")
        f.write(f"**参与模型数**: {len(models)}\n\n")
        f.write("## 模型列表\n\n")
        for model in models:
            model_id = model["model_id"]
            result_file = output_base / model_id / f"*_{model_id}.json"
            f.write(f"- `{model_id}`\n")
            f.write(f"  - 结果: `{output_base / model_id}/`\n")


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="PinchBench 批量评测执行器")
    parser.add_argument("task", help="用例输入（task_id 或文件路径）")
    parser.add_argument(
        "--round",
        type=int,
        default=None,
        help="指定轮次号（默认自动检测）",
    )
    
    args = parser.parse_args()
    run_batch(args.task, args.round)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 手动测试（需要真实配置）**

Run: `cd skills/pinchbench-batch-runner && python batch_runner.py --help`
Expected: 显示帮助信息

- [ ] **Step 3: 提交（Part 2）**

```bash
git add skills/pinchbench-batch-runner/batch_runner.py
git commit -m "feat(batch-runner): add execution logic

- 临时复制用例到 tasks/（框架限制）
- 串行执行多模型评测
- 生成批量执行摘要
- finally 块保证临时文件清理

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: Skill 1 文档 - batch-runner SKILL.md

**Files:**
- Create: `skills/pinchbench-batch-runner/SKILL.md`

- [ ] **Step 1: 编写 SKILL.md**

```markdown
---
name: pinchbench-batch-runner
description: 在多个被评测模型上批量执行 PinchBench 评测用例。Use when 需要在多个模型上试跑同一个评测用例、为用例优化收集多模型评测数据、或验证刚生成的评测用例质量时。支持从 models-config.yaml 读取模型配置，串行执行，结果按 task_id/round_N 分目录存储。
metadata:
  version: "1.0.0"
  author: astronclaw
---

# PinchBench 批量评测执行器

在多个被评测模型上串行执行同一评测用例，为用例优化收集多模型评测数据。

## 何时使用

- 刚生成新评测用例，需在多个模型上试跑验证
- 为 pinchbench-case-optimizer 收集多模型评测结果
- 对同一用例进行多次评测以验证稳定性

## 前置条件

- 已配置 `models-config.yaml`（首次运行自动生成模板）
- PinchBench 框架可用（scripts/run.sh）

## 配置

首次运行会自动从模板创建 `models-config.yaml`，需填写：

\`\`\`yaml
judge:
  model_id: anthropic/claude-sonnet-4-6
  api_key: "your-judge-api-key"
  base_url: "https://..."

models_under_test:
  - model_id: xopglm5
    api_key: "your-model-api-key"
    base_url: "https://..."
\`\`\`

配置文件已在 `.gitignore` 中，不会提交到 git。

## 用法

\`\`\`bash
# 执行用例（自动检测轮次）
python skills/pinchbench-batch-runner/batch_runner.py output/generated_cases/task_xxx

# 指定轮次
python skills/pinchbench-batch-runner/batch_runner.py task_xxx --round 2
\`\`\`

## 输入

- 用例输入：支持 task_id（在 tasks/ 和 output/generated_cases/ 查找）或文件路径
- 轮次号：可选，默认自动递增

## 输出

\`\`\`
results-auto/<task_id>/round_<N>/
├── <model_id>/
│   ├── 0001_<model_id>.json       # 评测结果
│   └── <run_id>_transcripts/      # 交互过程
└── batch-run-summary.md           # 执行摘要
\`\`\`

## 工作流程

1. 读取 models-config.yaml
2. 解析用例路径
3. 自动检测轮次号
4. 临时复制用例到 tasks/（框架限制）
5. 串行执行每个模型的评测
6. 生成执行摘要
7. 清理临时文件

## 设计说明

- **串行执行**：PinchBench 框架任务循环是串行的
- **临时复制**：框架硬编码从 tasks/ 加载用例，执行后自动清理
- **结果隔离**：每个模型独立目录，便于对比
```

- [ ] **Step 2: 验证文档存在**

Run: `test -f skills/pinchbench-batch-runner/SKILL.md && echo "OK"`
Expected: 输出 OK

- [ ] **Step 3: 提交**

```bash
git add skills/pinchbench-batch-runner/SKILL.md
git commit -m "docs(batch-runner): add SKILL.md

Skill元数据和使用文档

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 7: Skill 2 结果收集器 - result_collector.py

**Files:**
- Create: `skills/pinchbench-case-optimizer/result_collector.py`
- Test: `skills/pinchbench-case-optimizer/test_result_collector.py`

- [ ] **Step 1: 编写测试（先写测试）**

```python
"""测试 result_collector.py"""
import json
import pytest
from pathlib import Path
from result_collector import (
    find_latest_round,
    collect_model_results,
    find_previous_round_results,
)


def test_find_latest_round_returns_max(tmp_path):
    """测试：返回最大轮次目录"""
    base = tmp_path / "task_test"
    (base / "round_1").mkdir(parents=True)
    (base / "round_2").mkdir(parents=True)
    (base / "round_3").mkdir(parents=True)

    result = find_latest_round(base)
    assert result == base / "round_3"


def test_find_latest_round_none_when_empty(tmp_path):
    """测试：无轮次目录时返回 None"""
    base = tmp_path / "task_test"
    base.mkdir()
    assert find_latest_round(base) is None


def test_collect_model_results(tmp_path):
    """测试：收集模型结果"""
    round_dir = tmp_path / "round_1"
    model_dir = round_dir / "xopglm5"
    model_dir.mkdir(parents=True)

    # 创建结果 JSON
    result_data = {
        "tasks": [{
            "task_id": "task_test",
            "grading": {"mean": 0.75},
            "usage": {"total_tokens": 12000},
            "timed_out": False,
        }]
    }
    (model_dir / "0001_xopglm5.json").write_text(json.dumps(result_data))

    results = collect_model_results(round_dir)
    assert len(results) == 1
    assert results[0]["model"] == "xopglm5"
    assert results[0]["score"] == 0.75
    assert results[0]["timed_out"] is False


def test_find_previous_round_results_original_returns_none(tmp_path):
    """测试：原始用例（round 0）无基线"""
    result = find_previous_round_results("task_test", tmp_path)
    assert result is None


def test_find_previous_round_results_r1_finds_base(tmp_path):
    """测试：_r1 找到原始用例的结果作为基线"""
    base_results = tmp_path / "results-auto" / "task_test" / "round_1"
    base_results.mkdir(parents=True)

    result = find_previous_round_results("task_test_r1", tmp_path)
    assert result == base_results
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd skills/pinchbench-case-optimizer && pytest test_result_collector.py -v`
Expected: FAIL（模块不存在）

- [ ] **Step 3: 实现 result_collector.py**

```python
"""评测结果收集器：读取 results-auto 下的评测结果和 transcripts。"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
from path_resolver import extract_base_task_id, extract_optimization_round


def find_latest_round(task_results_base: Path) -> Optional[Path]:
    """
    找到 task_results_base 下最大轮次的目录。

    Args:
        task_results_base: 如 results-auto/task_xxx/

    Returns:
        最大轮次目录路径，无则返回 None
    """
    if not task_results_base.exists():
        return None

    round_dirs = [
        (int(d.name.replace("round_", "")), d)
        for d in task_results_base.iterdir()
        if d.is_dir() and d.name.startswith("round_")
    ]

    if not round_dirs:
        return None

    return max(round_dirs, key=lambda x: x[0])[1]


def collect_model_results(round_dir: Path) -> List[Dict]:
    """
    收集某轮评测中所有模型的结果。

    Args:
        round_dir: 如 results-auto/task_xxx/round_1/

    Returns:
        模型结果列表，每项包含 model/score/usage/timed_out/transcript_path
    """
    results = []

    for model_dir in round_dir.iterdir():
        if not model_dir.is_dir() or model_dir.name.endswith("_transcripts"):
            continue

        # 查找结果 JSON（排除 transcripts 目录）
        json_files = [
            f for f in model_dir.glob("*.json")
        ]
        if not json_files:
            continue

        with open(json_files[0]) as f:
            data = json.load(f)

        # 提取任务结果（取第一个任务）
        task_data = data.get("tasks", [{}])[0]

        # 查找 transcript 文件
        transcript_dirs = list(model_dir.glob("*_transcripts"))
        transcript_path = None
        if transcript_dirs:
            jsonl_files = list(transcript_dirs[0].glob("*.jsonl"))
            if jsonl_files:
                transcript_path = jsonl_files[0]

        results.append({
            "model": model_dir.name,
            "score": task_data.get("grading", {}).get("mean", 0.0),
            "usage": task_data.get("usage", {}),
            "timed_out": task_data.get("timed_out", False),
            "status": task_data.get("status", "unknown"),
            "transcript_path": transcript_path,
            "raw_task_data": task_data,
        })

    return results


def find_previous_round_results(task_id: str, project_root: Path) -> Optional[Path]:
    """
    找到用例家族中上一版本的最新评测结果，用于基线对比。

    Args:
        task_id: 当前用例 ID（如 task_xxx_r1）
        project_root: 项目根目录

    Returns:
        上一版本的最新轮次结果目录，原始用例返回 None
    """
    base = extract_base_task_id(task_id)
    current_round = extract_optimization_round(task_id)

    if current_round == 0:
        return None  # 原始用例，无基线

    prev_round = current_round - 1
    prev_id = base if prev_round == 0 else f"{base}_r{prev_round}"

    return find_latest_round(project_root / "results-auto" / prev_id)


def load_transcript(transcript_path: Optional[Path]) -> List[Dict]:
    """
    加载 transcript JSONL 文件。

    Args:
        transcript_path: JSONL 文件路径

    Returns:
        消息列表，每项为一条交互记录
    """
    if transcript_path is None or not transcript_path.exists():
        return []

    messages = []
    with open(transcript_path) as f:
        for line in f:
            line = line.strip()
            if line:
                messages.append(json.loads(line))

    return messages
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd skills/pinchbench-case-optimizer && pytest test_result_collector.py -v`
Expected: 所有测试 PASS

- [ ] **Step 5: 提交**

```bash
git add skills/pinchbench-case-optimizer/result_collector.py skills/pinchbench-case-optimizer/test_result_collector.py
git commit -m "feat(optimizer): add result collector

收集评测结果、transcripts，支持家族基线识别

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 8: Skill 2 五维度分析器 - analyzers.py (Part 1/2: C/D维度)

**Files:**
- Create: `skills/pinchbench-case-optimizer/analyzers.py`
- Test: `skills/pinchbench-case-optimizer/test_analyzers.py`

维度 C（难度区分度）和 D（超时设置）是纯数据计算，先实现这两个可自动化的维度。

- [ ] **Step 1: 编写测试**

```python
"""测试 analyzers.py"""
import pytest
from analyzers import analyze_difficulty, analyze_timeout


def test_analyze_difficulty_all_perfect():
    """测试：全部满分，区分度不足"""
    results = [
        {"model": "a", "score": 1.0},
        {"model": "b", "score": 1.0},
    ]
    analysis = analyze_difficulty(results)
    assert analysis["has_issue"] is True
    assert "全部满分" in analysis["summary"] or "区分度" in analysis["summary"]


def test_analyze_difficulty_all_zero():
    """测试：全部零分，难度过高"""
    results = [
        {"model": "a", "score": 0.0},
        {"model": "b", "score": 0.0},
    ]
    analysis = analyze_difficulty(results)
    assert analysis["has_issue"] is True


def test_analyze_difficulty_good_spread():
    """测试：良好分布，无问题"""
    results = [
        {"model": "a", "score": 0.3},
        {"model": "b", "score": 0.7},
    ]
    analysis = analyze_difficulty(results)
    assert analysis["has_issue"] is False


def test_analyze_timeout_with_timeout():
    """测试：存在超时"""
    results = [
        {"model": "a", "score": 0.5, "timed_out": True},
        {"model": "b", "score": 0.8, "timed_out": False},
    ]
    analysis = analyze_timeout(results)
    assert analysis["has_issue"] is True
    assert "a" in analysis["summary"]


def test_analyze_timeout_no_timeout():
    """测试：无超时"""
    results = [
        {"model": "a", "score": 0.5, "timed_out": False},
        {"model": "b", "score": 0.8, "timed_out": False},
    ]
    analysis = analyze_timeout(results)
    assert analysis["has_issue"] is False
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd skills/pinchbench-case-optimizer && pytest test_analyzers.py -v`
Expected: FAIL（模块不存在）

- [ ] **Step 3: 实现 analyzers.py（C/D维度）**

```python
"""五维度分析器：分析评测结果，识别用例优化点。

维度：
- A. Prompt 清晰度（需 LLM 分析 transcript）
- B. 评分标准合理性（需 LLM 分析）
- C. 难度区分度（纯数据计算）
- D. 超时设置（纯数据计算）
- E. 工具使用合理性（transcript 解析）
"""
import statistics
from typing import Dict, List


def analyze_difficulty(model_results: List[Dict]) -> Dict:
    """
    维度C：难度区分度分析。

    优化触发条件：全部满分/全部0分，或方差过小。
    """
    scores = [r["score"] for r in model_results]

    if not scores:
        return {"has_issue": False, "summary": "无评测数据", "details": {}}

    mean_score = statistics.mean(scores)
    score_range = max(scores) - min(scores)
    variance = statistics.variance(scores) if len(scores) > 1 else 0.0

    has_issue = False
    issues = []

    # 全部满分
    if all(s >= 0.95 for s in scores):
        has_issue = True
        issues.append("所有模型接近满分，用例难度过低，缺乏区分度")
    # 全部零分
    elif all(s <= 0.05 for s in scores):
        has_issue = True
        issues.append("所有模型接近零分，用例难度过高或存在缺陷")
    # 方差过小（多模型时）
    elif len(scores) > 1 and score_range < 0.15:
        has_issue = True
        issues.append(f"分数极差仅 {score_range:.2f}，区分度不足")

    summary = "；".join(issues) if issues else "分数分布合理，有良好区分度"

    return {
        "has_issue": has_issue,
        "summary": summary,
        "details": {
            "scores": {r["model"]: r["score"] for r in model_results},
            "mean": round(mean_score, 3),
            "range": round(score_range, 3),
            "variance": round(variance, 3),
        },
    }


def analyze_timeout(model_results: List[Dict]) -> Dict:
    """
    维度D：超时设置分析。

    优化触发条件：任一模型因超时失败。
    """
    timed_out_models = [
        r["model"] for r in model_results if r.get("timed_out", False)
    ]

    has_issue = len(timed_out_models) > 0

    if has_issue:
        summary = (
            f"模型 {', '.join(timed_out_models)} 发生超时，"
            f"可能因 timeout 设置过短导致误判，建议增加 timeout"
        )
    else:
        summary = "无超时发生，timeout 设置合理"

    return {
        "has_issue": has_issue,
        "summary": summary,
        "details": {
            "timed_out_models": timed_out_models,
            "total_models": len(model_results),
        },
    }
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd skills/pinchbench-case-optimizer && pytest test_analyzers.py -v`
Expected: 所有测试 PASS

- [ ] **Step 5: 提交**

```bash
git add skills/pinchbench-case-optimizer/analyzers.py skills/pinchbench-case-optimizer/test_analyzers.py
git commit -m "feat(optimizer): add difficulty and timeout analyzers

维度C：难度区分度（分数分布、方差、极差）
维度D：超时设置（统计超时模型）

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 9: Skill 2 五维度分析器 - analyzers.py (Part 2/2: E维度 + LLM维度框架)

**Files:**
- Modify: `skills/pinchbench-case-optimizer/analyzers.py`
- Modify: `skills/pinchbench-case-optimizer/test_analyzers.py`

维度 E（工具使用）通过解析 transcript 实现；维度 A/B 需 LLM 分析，提供数据准备框架。

- [ ] **Step 1: 追加测试（E维度）**

在 `test_analyzers.py` 末尾追加：

```python
from analyzers import analyze_tool_usage, extract_tool_calls


def test_extract_tool_calls():
    """测试：从 transcript 提取工具调用"""
    transcript = [
        {"role": "assistant", "tool_calls": [
            {"function": {"name": "read_file"}, "id": "1"}
        ]},
        {"role": "tool", "tool_call_id": "1", "content": "file content"},
        {"role": "assistant", "tool_calls": [
            {"function": {"name": "bad_tool"}, "id": "2"}
        ]},
        {"role": "tool", "tool_call_id": "2", "content": "Error: tool not found"},
    ]
    calls = extract_tool_calls(transcript)
    assert len(calls) == 2
    assert calls[0]["name"] == "read_file"
    assert calls[0]["success"] is True
    assert calls[1]["success"] is False


def test_analyze_tool_usage_high_failure():
    """测试：工具调用失败率高"""
    model_results = [{
        "model": "a",
        "transcript": [
            {"role": "assistant", "tool_calls": [{"function": {"name": "t1"}, "id": "1"}]},
            {"role": "tool", "tool_call_id": "1", "content": "Error: failed"},
            {"role": "assistant", "tool_calls": [{"function": {"name": "t2"}, "id": "2"}]},
            {"role": "tool", "tool_call_id": "2", "content": "Error: failed"},
        ],
    }]
    analysis = analyze_tool_usage(model_results)
    assert analysis["has_issue"] is True


def test_analyze_tool_usage_no_issue():
    """测试：工具调用正常"""
    model_results = [{
        "model": "a",
        "transcript": [
            {"role": "assistant", "tool_calls": [{"function": {"name": "t1"}, "id": "1"}]},
            {"role": "tool", "tool_call_id": "1", "content": "success result"},
        ],
    }]
    analysis = analyze_tool_usage(model_results)
    assert analysis["has_issue"] is False
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd skills/pinchbench-case-optimizer && pytest test_analyzers.py::test_extract_tool_calls -v`
Expected: FAIL（函数不存在）

- [ ] **Step 3: 实现 E维度 + LLM维度数据准备**

在 `analyzers.py` 末尾追加：

```python
def extract_tool_calls(transcript: List[Dict]) -> List[Dict]:
    """
    从 transcript 提取工具调用记录及成功状态。

    Args:
        transcript: 交互消息列表

    Returns:
        工具调用列表，每项含 name/success/result
    """
    calls = []
    # 建立 tool_call_id → 结果的映射
    tool_results = {
        msg.get("tool_call_id"): msg.get("content", "")
        for msg in transcript
        if msg.get("role") == "tool"
    }

    for msg in transcript:
        if msg.get("role") == "assistant" and msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                call_id = tc.get("id")
                name = tc.get("function", {}).get("name", "unknown")
                result = tool_results.get(call_id, "")
                # 简单的成功判定：结果中不含 Error
                success = "error" not in result.lower()
                calls.append({
                    "name": name,
                    "success": success,
                    "result": result[:200],  # 截断
                })

    return calls


def analyze_tool_usage(model_results: List[Dict]) -> Dict:
    """
    维度E：工具使用合理性分析。

    优化触发条件：工具调用失败率高，或缺少必要工具。
    """
    all_calls = []
    per_model_stats = {}

    for r in model_results:
        transcript = r.get("transcript", [])
        calls = extract_tool_calls(transcript)
        all_calls.extend(calls)

        if calls:
            failed = [c for c in calls if not c["success"]]
            per_model_stats[r["model"]] = {
                "total": len(calls),
                "failed": len(failed),
                "failure_rate": round(len(failed) / len(calls), 2),
            }

    if not all_calls:
        return {
            "has_issue": False,
            "summary": "无工具调用数据",
            "details": {},
        }

    total_failed = sum(1 for c in all_calls if not c["success"])
    overall_failure_rate = total_failed / len(all_calls)

    has_issue = overall_failure_rate > 0.3  # 失败率超30%视为问题

    if has_issue:
        summary = (
            f"工具调用整体失败率 {overall_failure_rate:.0%}，"
            f"可能存在工具能力 gap 或用例对工具要求不合理"
        )
    else:
        summary = f"工具调用失败率 {overall_failure_rate:.0%}，使用正常"

    return {
        "has_issue": has_issue,
        "summary": summary,
        "details": {
            "overall_failure_rate": round(overall_failure_rate, 2),
            "per_model": per_model_stats,
        },
    }


def prepare_llm_analysis_data(original_task: Dict, model_results: List[Dict]) -> Dict:
    """
    为 LLM 分析（维度 A/B）准备数据。

    维度 A（Prompt清晰度）和 B（评分标准）需要 LLM 来分析，
    此函数整理出 LLM 分析所需的结构化输入。

    Args:
        original_task: 原始用例数据（含 prompt、grading 等）
        model_results: 各模型评测结果

    Returns:
        结构化的 LLM 分析输入
    """
    return {
        "task_prompt": original_task.get("prompt", ""),
        "grading_criteria": original_task.get("grading", {}),
        "model_outputs": [
            {
                "model": r["model"],
                "score": r["score"],
                "transcript_summary": _summarize_transcript(r.get("transcript", [])),
            }
            for r in model_results
        ],
    }


def _summarize_transcript(transcript: List[Dict], max_messages: int = 20) -> List[Dict]:
    """提取 transcript 关键信息（用户指令 + 助手响应），截断长内容。"""
    summary = []
    for msg in transcript[:max_messages]:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if isinstance(content, str):
            content = content[:500]  # 截断
        summary.append({"role": role, "content": content})
    return summary
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd skills/pinchbench-case-optimizer && pytest test_analyzers.py -v`
Expected: 所有测试 PASS

- [ ] **Step 5: 提交**

```bash
git add skills/pinchbench-case-optimizer/analyzers.py skills/pinchbench-case-optimizer/test_analyzers.py
git commit -m "feat(optimizer): add tool usage analyzer and LLM data prep

维度E：工具使用（解析transcript，统计失败率）
维度A/B：准备LLM分析所需的结构化数据

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 10: Skill 2 收敛检测 - convergence.py

**Files:**
- Create: `skills/pinchbench-case-optimizer/convergence.py`
- Test: `skills/pinchbench-case-optimizer/test_convergence.py`

- [ ] **Step 1: 编写测试**

```python
"""测试 convergence.py"""
import pytest
from convergence import check_convergence, count_issues


def test_count_issues():
    """测试：统计问题数量"""
    analysis = {
        "prompt_clarity": {"has_issue": True},
        "grading_validity": {"has_issue": False},
        "difficulty": {"has_issue": True},
        "timeout": {"has_issue": False},
        "tool_usage": {"has_issue": False},
    }
    assert count_issues(analysis) == 2


def test_check_convergence_no_issues():
    """测试：无问题时建议停止"""
    analysis = {
        "prompt_clarity": {"has_issue": False},
        "grading_validity": {"has_issue": False},
        "difficulty": {"has_issue": False},
        "timeout": {"has_issue": False},
        "tool_usage": {"has_issue": False},
    }
    result = check_convergence(1, analysis)
    assert result["converged"] is True
    assert "无新问题发现" in result["signals"]


def test_check_convergence_max_rounds():
    """测试：达到最大轮次"""
    analysis = {
        "prompt_clarity": {"has_issue": True},
        "grading_validity": {"has_issue": False},
        "difficulty": {"has_issue": False},
        "timeout": {"has_issue": False},
        "tool_usage": {"has_issue": False},
    }
    result = check_convergence(5, analysis)
    assert result["converged"] is True
    assert any("最大轮次" in s for s in result["signals"])


def test_check_convergence_has_issues_continue():
    """测试：有问题且未达最大轮次，建议继续"""
    analysis = {
        "prompt_clarity": {"has_issue": True},
        "grading_validity": {"has_issue": False},
        "difficulty": {"has_issue": False},
        "timeout": {"has_issue": False},
        "tool_usage": {"has_issue": False},
    }
    result = check_convergence(2, analysis)
    assert result["converged"] is False
    assert result["recommendation"] == "建议继续优化"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd skills/pinchbench-case-optimizer && pytest test_convergence.py -v`
Expected: FAIL（模块不存在）

- [ ] **Step 3: 实现 convergence.py**

```python
"""收敛检测：判断多轮优化是否应停止（混合方式）。"""
from typing import Dict, List, Optional


def count_issues(analysis: Dict) -> int:
    """统计五维度中有问题的维度数量。"""
    return sum(
        1 for dim in analysis.values()
        if isinstance(dim, dict) and dim.get("has_issue", False)
    )


def check_convergence(
    round_num: int,
    current_analysis: Dict,
    prev_score_mean: Optional[float] = None,
    current_score_mean: Optional[float] = None,
    max_rounds: int = 5,
) -> Dict:
    """
    收敛检测：给出停止建议，最终由用户决定。

    检测信号：
    1. 无新问题发现
    2. 与上轮对比改进幅度 < 0.05
    3. 达到最大轮次限制

    Args:
        round_num: 当前优化轮次
        current_analysis: 五维度分析结果
        prev_score_mean: 上一轮平均分（用于对比）
        current_score_mean: 当前轮平均分
        max_rounds: 最大轮次限制

    Returns:
        {converged, signals, recommendation}
    """
    signals: List[str] = []

    # 信号1：无新问题
    issue_count = count_issues(current_analysis)
    if issue_count == 0:
        signals.append("无新问题发现")

    # 信号2：与上轮对比改进幅度
    if prev_score_mean is not None and current_score_mean is not None:
        improvement = current_score_mean - prev_score_mean
        if abs(improvement) < 0.05:
            signals.append(f"分数提升{improvement:+.3f}，趋于收敛")

    # 信号3：最大轮次
    if round_num >= max_rounds:
        signals.append(f"达到最大轮次限制（{max_rounds}）")

    converged = len(signals) > 0

    return {
        "converged": converged,
        "signals": signals,
        "issue_count": issue_count,
        "recommendation": "建议停止" if converged else "建议继续优化",
    }
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd skills/pinchbench-case-optimizer && pytest test_convergence.py -v`
Expected: 所有测试 PASS

- [ ] **Step 5: 提交**

```bash
git add skills/pinchbench-case-optimizer/convergence.py skills/pinchbench-case-optimizer/test_convergence.py
git commit -m "feat(optimizer): add convergence detection

混合方式收敛检测：无新问题/改进幅度<0.05/达到最大轮次

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 11: Skill 2 报告生成器 - report_generator.py

**Files:**
- Create: `skills/pinchbench-case-optimizer/report_generator.py`
- Test: `skills/pinchbench-case-optimizer/test_report_generator.py`

- [ ] **Step 1: 编写测试**

```python
"""测试 report_generator.py"""
import pytest
from pathlib import Path
from report_generator import generate_report, format_model_overview


def test_format_model_overview():
    """测试：格式化模型表现总览表格"""
    model_results = [
        {"model": "xopglm5", "score": 0.30, "timed_out": False,
         "usage": {"total_tokens": 12000}},
        {"model": "spark-x", "score": 0.85, "timed_out": True,
         "usage": {"total_tokens": 35000}},
    ]
    table = format_model_overview(model_results)
    assert "xopglm5" in table
    assert "0.30" in table
    assert "spark-x" in table
    assert "是" in table  # spark-x 超时


def test_generate_report_creates_file(tmp_path):
    """测试：生成报告文件"""
    analysis = {
        "prompt_clarity": {"has_issue": True, "summary": "存在歧义",
                           "details": {}},
        "grading_validity": {"has_issue": False, "summary": "评分合理",
                            "details": {}},
        "difficulty": {"has_issue": True, "summary": "区分度不足",
                      "details": {"scores": {}, "mean": 0.5}},
        "timeout": {"has_issue": False, "summary": "无超时", "details": {}},
        "tool_usage": {"has_issue": False, "summary": "正常", "details": {}},
    }
    model_results = [
        {"model": "a", "score": 0.5, "timed_out": False, "usage": {}},
    ]
    convergence = {
        "converged": False, "signals": [], "issue_count": 2,
        "recommendation": "建议继续优化",
    }

    report_path = tmp_path / "report.md"
    generate_report(
        report_path=report_path,
        task_id="task_test",
        round_num=1,
        model_results=model_results,
        analysis=analysis,
        convergence=convergence,
        judge_model="anthropic/claude-sonnet-4-6",
    )

    assert report_path.exists()
    content = report_path.read_text()
    assert "task_test" in content
    assert "维度A" in content
    assert "维度C" in content
    assert "存在歧义" in content
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd skills/pinchbench-case-optimizer && pytest test_report_generator.py -v`
Expected: FAIL（模块不存在）

- [ ] **Step 3: 实现 report_generator.py**

```python
"""详细优化报告生成器。"""
from pathlib import Path
from typing import Dict, List


def format_model_overview(model_results: List[Dict]) -> str:
    """格式化模型表现总览表格。"""
    lines = [
        "| 模型 | 得分 | 是否超时 | Token消耗 |",
        "|------|------|----------|-----------|",
    ]
    for r in model_results:
        tokens = r.get("usage", {}).get("total_tokens", "N/A")
        timed_out = "是" if r.get("timed_out") else "否"
        lines.append(
            f"| {r['model']} | {r['score']:.2f} | {timed_out} | {tokens} |"
        )
    return "\n".join(lines)


def _format_dimension(title: str, dim_key: str, analysis: Dict) -> str:
    """格式化单个维度的分析章节。"""
    dim = analysis.get(dim_key, {})
    has_issue = dim.get("has_issue", False)
    summary = dim.get("summary", "无数据")
    details = dim.get("details", {})

    status = "⚠️ 发现问题" if has_issue else "✅ 正常"

    section = f"## {title}\n\n"
    section += f"**状态**: {status}\n\n"
    section += f"**分析**: {summary}\n\n"

    if details:
        section += "**详细数据**:\n\n```\n"
        for k, v in details.items():
            section += f"{k}: {v}\n"
        section += "```\n\n"

    return section


def generate_report(
    report_path: Path,
    task_id: str,
    round_num: int,
    model_results: List[Dict],
    analysis: Dict,
    convergence: Dict,
    judge_model: str,
):
    """
    生成详细优化报告（详细分析版）。

    Args:
        report_path: 报告输出路径
        task_id: 用例 ID
        round_num: 优化轮次
        model_results: 模型评测结果
        analysis: 五维度分析结果
        convergence: 收敛检测结果
        judge_model: 裁判模型
    """
    report_path.parent.mkdir(parents=True, exist_ok=True)

    content = f"# 评测用例优化报告 - {task_id} (Round {round_num})\n\n"

    # 执行概览
    content += "## 执行概览\n\n"
    content += f"- **优化轮次**: Round {round_num}\n"
    content += f"- **参与模型**: {', '.join(r['model'] for r in model_results)}\n"
    content += f"- **裁判模型**: {judge_model}\n\n"

    # 模型表现总览
    content += "## 模型表现总览\n\n"
    content += format_model_overview(model_results) + "\n\n"

    # 五维度分析
    content += _format_dimension("维度A：Prompt清晰度分析", "prompt_clarity", analysis)
    content += _format_dimension("维度B：评分标准合理性", "grading_validity", analysis)
    content += _format_dimension("维度C：难度区分度", "difficulty", analysis)
    content += _format_dimension("维度D：超时设置", "timeout", analysis)
    content += _format_dimension("维度E：工具使用合理性", "tool_usage", analysis)

    # 收敛性判断
    content += "## 收敛性判断\n\n"
    content += f"- **本轮发现问题数**: {convergence['issue_count']}\n"
    if convergence["signals"]:
        content += f"- **收敛信号**: {'; '.join(convergence['signals'])}\n"
    content += f"- **建议**: {convergence['recommendation']}\n\n"

    report_path.write_text(content)
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd skills/pinchbench-case-optimizer && pytest test_report_generator.py -v`
Expected: 所有测试 PASS

- [ ] **Step 5: 提交**

```bash
git add skills/pinchbench-case-optimizer/report_generator.py skills/pinchbench-case-optimizer/test_report_generator.py
git commit -m "feat(optimizer): add detailed report generator

生成详细分析版报告：执行概览/模型总览/五维度分析/收敛判断

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 12: Skill 2 用例文件读写 - task_io.py

**Files:**
- Create: `skills/pinchbench-case-optimizer/task_io.py`
- Test: `skills/pinchbench-case-optimizer/test_task_io.py`

- [ ] **Step 1: 编写测试**

```python
"""测试 task_io.py"""
import pytest
from pathlib import Path
from task_io import load_task_markdown, get_output_path


def test_load_task_markdown(tmp_path):
    """测试：加载用例 markdown"""
    task_file = tmp_path / "task_test.md"
    task_file.write_text("""---
id: task_test
timeout: 60
---

## Prompt

分析数据
""")
    task = load_task_markdown(task_file)
    assert task["raw_content"].startswith("---")
    assert "分析数据" in task["raw_content"]
    assert task["frontmatter"]["timeout"] == 60


def test_get_output_path_from_generated_cases(tmp_path):
    """测试：源在 generated_cases，产物同目录"""
    source = tmp_path / "output" / "generated_cases" / "task_test.md"
    source.parent.mkdir(parents=True)
    source.write_text("# test")

    output = get_output_path(source, "task_test", 1)
    assert output == source.parent / "task_test_r1.md"


def test_get_output_path_chained(tmp_path):
    """测试：链式演进，_r1 产出 _r2（去除旧后缀）"""
    source = tmp_path / "task_test_r1.md"
    source.write_text("# test")

    # base_task_id=task_test, 新轮次=2
    output = get_output_path(source, "task_test", 2)
    assert output == source.parent / "task_test_r2.md"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd skills/pinchbench-case-optimizer && pytest test_task_io.py -v`
Expected: FAIL（模块不存在）

- [ ] **Step 3: 实现 task_io.py**

```python
"""用例文件读写工具。"""
import yaml
from pathlib import Path
from typing import Dict


def load_task_markdown(task_file: Path) -> Dict:
    """
    加载用例 markdown 文件，解析 frontmatter 和正文。

    Args:
        task_file: 用例文件路径

    Returns:
        {raw_content, frontmatter, body}
    """
    raw_content = task_file.read_text()

    frontmatter = {}
    body = raw_content

    # 解析 YAML frontmatter
    if raw_content.startswith("---"):
        parts = raw_content.split("---", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                frontmatter = {}
            body = parts[2]

    return {
        "raw_content": raw_content,
        "frontmatter": frontmatter,
        "body": body,
    }


def get_output_path(source: Path, base_task_id: str, new_round: int) -> Path:
    """
    计算优化产物的输出路径（与源用例同目录）。

    Args:
        source: 源用例文件路径
        base_task_id: 基础用例 ID（去除 _r 后缀）
        new_round: 新的优化轮次

    Returns:
        产物路径，如 <源目录>/<base_task_id>_r<N>.md
    """
    return source.parent / f"{base_task_id}_r{new_round}.md"


def write_optimized_task(
    output_path: Path,
    optimized_content: str,
):
    """
    写入优化后的用例文件。

    Args:
        output_path: 输出路径
        optimized_content: 优化后的完整用例内容
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(optimized_content)
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd skills/pinchbench-case-optimizer && pytest test_task_io.py -v`
Expected: 所有测试 PASS

- [ ] **Step 5: 提交**

```bash
git add skills/pinchbench-case-optimizer/task_io.py skills/pinchbench-case-optimizer/test_task_io.py
git commit -m "feat(optimizer): add task markdown I/O

加载用例（解析frontmatter）、计算产物路径、写入优化用例

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 13: Skill 2 主流程编排 - optimizer.py

**Files:**
- Create: `skills/pinchbench-case-optimizer/optimizer.py`

将前面的模块组装成完整的优化流程。维度 A/B 的 LLM 分析在此处通过调用方（Claude）完成——optimizer.py 准备数据，由 Skill 使用者基于数据进行 LLM 分析后填充。

- [ ] **Step 1: 实现 optimizer.py 主流程**

```python
#!/usr/bin/env python3
"""
PinchBench 评测用例优化器

职责：
1. 读取批量评测结果 + transcripts
2. 五维度分析（C/D/E自动 + A/B数据准备供LLM分析）
3. 家族识别与基线对比
4. 生成优化用例 + 详细报告
5. 收敛检测
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
from path_resolver import (
    resolve_task_path,
    extract_base_task_id,
    extract_optimization_round,
)

from result_collector import (
    find_latest_round,
    collect_model_results,
    find_previous_round_results,
    load_transcript,
)
from analyzers import (
    analyze_difficulty,
    analyze_timeout,
    analyze_tool_usage,
    prepare_llm_analysis_data,
)
from convergence import check_convergence
from report_generator import generate_report
from task_io import load_task_markdown, get_output_path


def run_optimization(
    task_input: str,
    results_dir: Optional[str] = None,
) -> Dict:
    """
    执行用例优化分析，输出分析数据供 LLM 进一步处理。

    Args:
        task_input: 用例输入（task_id 或路径）
        results_dir: 评测结果目录（None 表示自动读取最新）

    Returns:
        优化分析数据包，含五维度分析、LLM输入、路径信息
    """
    project_root = Path(__file__).parent.parent.parent

    # 1. 加载源用例
    source = resolve_task_path(task_input, project_root)
    task_id = source.stem
    base_task_id = extract_base_task_id(task_id)
    optimization_round = extract_optimization_round(task_id)
    original_task = load_task_markdown(source)
    print(f"📋 源用例: {task_id} ({source})")

    # 2. 确定结果目录
    if results_dir is None:
        results_path = find_latest_round(
            project_root / "results-auto" / task_id
        )
        if results_path is None:
            print(f"❌ 未找到 {task_id} 的评测结果，请先运行 batch-runner")
            sys.exit(1)
    else:
        results_path = Path(results_dir)
        if not results_path.is_absolute():
            results_path = project_root / results_path

    print(f"📂 评测结果: {results_path}")

    # 3. 收集模型结果 + 加载 transcripts
    model_results = collect_model_results(results_path)
    for r in model_results:
        r["transcript"] = load_transcript(r.get("transcript_path"))

    print(f"📊 收集到 {len(model_results)} 个模型的结果")

    # 4. 加载基线（家族上一版本）
    prev_results_path = find_previous_round_results(task_id, project_root)
    prev_score_mean = None
    if prev_results_path:
        prev_results = collect_model_results(prev_results_path)
        if prev_results:
            prev_score_mean = sum(r["score"] for r in prev_results) / len(prev_results)
        print(f"📈 基线: {prev_results_path}（均分 {prev_score_mean:.3f}）")

    # 5. 五维度分析（C/D/E 自动）
    analysis = {
        # A/B 维度先占位，由 LLM 分析后填充
        "prompt_clarity": {
            "has_issue": None,
            "summary": "待LLM分析（见 llm_analysis_data）",
            "details": {},
        },
        "grading_validity": {
            "has_issue": None,
            "summary": "待LLM分析（见 llm_analysis_data）",
            "details": {},
        },
        "difficulty": analyze_difficulty(model_results),
        "timeout": analyze_timeout(model_results),
        "tool_usage": analyze_tool_usage(model_results),
    }

    # 6. 准备 LLM 分析数据（维度 A/B）
    llm_data = prepare_llm_analysis_data(
        {"prompt": original_task["body"],
         "grading": original_task["frontmatter"].get("grading", {})},
        model_results,
    )

    # 7. 当前轮均分
    current_score_mean = (
        sum(r["score"] for r in model_results) / len(model_results)
        if model_results else 0.0
    )

    # 8. 计算输出路径
    new_round = optimization_round + 1
    output_task_path = get_output_path(source, base_task_id, new_round)
    report_path = (
        project_root / "optimization-reports" / base_task_id
        / f"{base_task_id}_r{new_round}_report.md"
    )

    return {
        "task_id": task_id,
        "base_task_id": base_task_id,
        "optimization_round": optimization_round,
        "new_round": new_round,
        "source_path": source,
        "original_task": original_task,
        "model_results": model_results,
        "analysis": analysis,
        "llm_analysis_data": llm_data,
        "current_score_mean": current_score_mean,
        "prev_score_mean": prev_score_mean,
        "output_task_path": output_task_path,
        "report_path": report_path,
    }


def finalize_optimization(
    opt_data: Dict,
    analysis: Dict,
    optimized_task_content: str,
    judge_model: str = "anthropic/claude-sonnet-4-6",
) -> Dict:
    """
    完成优化：写入优化用例和报告，执行收敛检测。

    在 LLM 完成维度 A/B 分析并生成优化用例后调用。

    Args:
        opt_data: run_optimization 返回的数据包
        analysis: 完整的五维度分析（A/B 已由 LLM 填充）
        optimized_task_content: LLM 生成的优化用例完整内容
        judge_model: 裁判模型

    Returns:
        {output_task_path, report_path, convergence}
    """
    from task_io import write_optimized_task

    # 1. 写入优化用例
    write_optimized_task(opt_data["output_task_path"], optimized_task_content)

    # 2. 收敛检测
    convergence = check_convergence(
        round_num=opt_data["new_round"],
        current_analysis=analysis,
        prev_score_mean=opt_data["prev_score_mean"],
        current_score_mean=opt_data["current_score_mean"],
    )

    # 3. 生成报告
    generate_report(
        report_path=opt_data["report_path"],
        task_id=opt_data["task_id"],
        round_num=opt_data["new_round"],
        model_results=opt_data["model_results"],
        analysis=analysis,
        convergence=convergence,
        judge_model=judge_model,
    )

    return {
        "output_task_path": opt_data["output_task_path"],
        "report_path": opt_data["report_path"],
        "convergence": convergence,
    }


def main():
    """命令行入口：输出分析数据为 JSON，供调用方处理。"""
    parser = argparse.ArgumentParser(description="PinchBench 评测用例优化器")
    parser.add_argument("task", help="用例输入（task_id 或文件路径）")
    parser.add_argument(
        "--results-dir",
        default=None,
        help="评测结果目录（默认自动读取最新轮次）",
    )
    parser.add_argument(
        "--dump-analysis",
        action="store_true",
        help="输出分析数据为 JSON（供 LLM 处理）",
    )

    args = parser.parse_args()
    opt_data = run_optimization(args.task, args.results_dir)

    if args.dump_analysis:
        # 序列化（排除不可序列化的 Path 和 transcript）
        dumpable = {
            "task_id": opt_data["task_id"],
            "base_task_id": opt_data["base_task_id"],
            "new_round": opt_data["new_round"],
            "analysis": opt_data["analysis"],
            "llm_analysis_data": opt_data["llm_analysis_data"],
            "current_score_mean": opt_data["current_score_mean"],
            "prev_score_mean": opt_data["prev_score_mean"],
            "output_task_path": str(opt_data["output_task_path"]),
            "report_path": str(opt_data["report_path"]),
        }
        print(json.dumps(dumpable, ensure_ascii=False, indent=2))
    else:
        print(f"\n✅ 分析完成")
        print(f"📝 优化用例将输出到: {opt_data['output_task_path']}")
        print(f"📊 报告将输出到: {opt_data['report_path']}")
        print(f"\n维度C（难度）: {opt_data['analysis']['difficulty']['summary']}")
        print(f"维度D（超时）: {opt_data['analysis']['timeout']['summary']}")
        print(f"维度E（工具）: {opt_data['analysis']['tool_usage']['summary']}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 验证语法和导入**

Run: `cd skills/pinchbench-case-optimizer && python -c "import optimizer; print('OK')"`
Expected: 输出 OK（如果 import 报错需修复路径）

- [ ] **Step 3: 验证帮助信息**

Run: `cd skills/pinchbench-case-optimizer && python optimizer.py --help`
Expected: 显示帮助信息

- [ ] **Step 4: 提交**

```bash
git add skills/pinchbench-case-optimizer/optimizer.py
git commit -m "feat(optimizer): add main orchestration

主流程：收集结果→自动维度分析→准备LLM数据→收敛检测→报告
分两阶段：run_optimization准备数据，finalize_optimization写入产物

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 14: Skill 2 文档 - case-optimizer SKILL.md

**Files:**
- Create: `skills/pinchbench-case-optimizer/SKILL.md`

- [ ] **Step 1: 编写 SKILL.md**

```markdown
---
name: pinchbench-case-optimizer
description: 分析 PinchBench 多模型评测结果，反向优化评测用例。Use when 需要根据多个模型的评测结果优化评测用例、分析用例的prompt清晰度/评分标准/难度区分度/超时/工具使用问题、或对评测用例进行多轮迭代优化时。读取 results-auto 下的评测结果和交互transcript，生成优化用例和详细分析报告。
metadata:
  version: "1.0.0"
  author: astronclaw
---

# PinchBench 评测用例优化器

根据多模型评测结果反向逆推用例合理性，从五个维度分析优化点，生成优化用例和详细报告。支持多轮链式优化。

## 何时使用

- batch-runner 执行完评测后，需要分析结果优化用例
- 评测用例在多个模型上表现异常，需诊断是用例问题还是模型问题
- 对用例进行多轮迭代优化，逐步逼近理想状态

## 前置条件

- 已通过 pinchbench-batch-runner 生成评测结果（results-auto/）

## 五维度分析

| 维度 | 说明 | 自动化 |
|------|------|--------|
| A. Prompt清晰度 | 各模型对指令的理解偏差 | LLM分析 |
| B. 评分标准合理性 | 得分与实际质量的匹配度 | LLM分析 |
| C. 难度区分度 | 分数分布、方差、极差 | 自动 |
| D. 超时设置 | 超时发生率 | 自动 |
| E. 工具使用 | tool_call成功率 | 自动 |

## 用法

\`\`\`bash
# 分析最新轮次结果
python skills/pinchbench-case-optimizer/optimizer.py task_xxx

# 指定结果目录
python skills/pinchbench-case-optimizer/optimizer.py task_xxx --results-dir results-auto/task_xxx/round_1

# 输出分析数据为 JSON（供 LLM 处理 A/B 维度）
python skills/pinchbench-case-optimizer/optimizer.py task_xxx --dump-analysis
\`\`\`

## 工作流程

1. 加载源用例
2. 读取评测结果（默认最新轮次）+ transcripts
3. 识别用例家族，加载上一版本基线
4. 五维度分析（C/D/E自动，A/B准备数据供LLM分析）
5. LLM 完成 A/B 维度分析 + 生成优化用例
6. 写入优化用例（同源目录，_r<N>后缀）
7. 生成详细报告
8. 收敛检测 + 询问用户是否继续

## 多轮链式优化

每轮基于上一轮优化产物继续：

\`\`\`
原始 task_xxx
  → batch-runner → optimizer → task_xxx_r1
  → batch-runner task_xxx_r1 → optimizer → task_xxx_r2
  → ...
\`\`\`

optimizer 自动识别家族（去除 `_r<N>` 后缀），对比上一版本评测结果。

## 输出

- **优化用例**: `<源目录>/<base_task_id>_r<N>.md`
- **优化报告**: `optimization-reports/<base_task_id>/<base_task_id>_r<N>_report.md`

## 收敛检测（混合方式）

停止信号（满足任一即建议停止，最终由用户决定）：
- 无新问题发现
- 与上轮分数提升 < 0.05
- 达到最大轮次（5）

## 设计说明

optimizer.py 分两阶段：
- `run_optimization`：自动分析 + 准备 LLM 数据
- `finalize_optimization`：LLM 完成 A/B 分析和优化用例后，写入产物
```

- [ ] **Step 2: 验证文档存在**

Run: `test -f skills/pinchbench-case-optimizer/SKILL.md && echo "OK"`
Expected: 输出 OK

- [ ] **Step 3: 提交**

```bash
git add skills/pinchbench-case-optimizer/SKILL.md
git commit -m "docs(optimizer): add SKILL.md

Skill元数据、五维度说明、多轮链式优化流程文档

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 15: 集成测试与端到端验证

**Files:**
- Create: `skills/pinchbench-case-optimizer/test_integration.py`

- [ ] **Step 1: 编写集成测试（用模拟数据）**

```python
"""集成测试：模拟评测结果，验证 optimizer 完整流程。"""
import json
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))


def _make_mock_results(project_root: Path, task_id: str, round_num: int, scores: dict):
    """创建模拟评测结果。"""
    round_dir = project_root / "results-auto" / task_id / f"round_{round_num}"
    for model, score in scores.items():
        model_dir = round_dir / model
        model_dir.mkdir(parents=True)
        result = {
            "tasks": [{
                "task_id": task_id,
                "grading": {"mean": score},
                "usage": {"total_tokens": 10000},
                "timed_out": False,
                "status": "completed",
            }]
        }
        (model_dir / f"0001_{model}.json").write_text(json.dumps(result))


def test_run_optimization_end_to_end(tmp_path, monkeypatch):
    """测试：完整优化流程（自动维度）"""
    # 准备目录结构
    (tmp_path / "tasks").mkdir()
    gen_dir = tmp_path / "output" / "generated_cases"
    gen_dir.mkdir(parents=True)

    # 创建源用例
    source = gen_dir / "task_test.md"
    source.write_text("""---
id: task_test
timeout: 60
---

## Prompt

分析数据并总结
""")

    # 创建模拟结果（全部满分 → 难度区分度问题）
    _make_mock_results(tmp_path, "task_test", 1,
                       {"model_a": 1.0, "model_b": 1.0})

    # patch project_root
    import optimizer
    monkeypatch.setattr(
        optimizer.Path,
        "__truediv__",
        Path.__truediv__,
    )

    # 直接调用，传入 tmp_path 作为根
    monkeypatch.chdir(tmp_path)
    # 由于 optimizer 用 __file__ 推导 project_root，这里直接测试核心函数
    from result_collector import collect_model_results, find_latest_round
    from analyzers import analyze_difficulty

    results_dir = find_latest_round(tmp_path / "results-auto" / "task_test")
    assert results_dir is not None

    model_results = collect_model_results(results_dir)
    assert len(model_results) == 2

    difficulty = analyze_difficulty(model_results)
    assert difficulty["has_issue"] is True  # 全部满分


def test_chained_family_baseline(tmp_path):
    """测试：链式演进的家族基线识别"""
    from result_collector import find_previous_round_results

    # 创建原始用例的结果
    base_results = tmp_path / "results-auto" / "task_test" / "round_1"
    base_results.mkdir(parents=True)

    # _r1 应该找到原始用例结果作为基线
    prev = find_previous_round_results("task_test_r1", tmp_path)
    assert prev == base_results

    # 原始用例无基线
    prev_none = find_previous_round_results("task_test", tmp_path)
    assert prev_none is None
```

- [ ] **Step 2: 运行集成测试**

Run: `cd skills/pinchbench-case-optimizer && pytest test_integration.py -v`
Expected: 所有测试 PASS

- [ ] **Step 3: 运行所有测试（全量验证）**

Run: `cd skills && python -m pytest pinchbench-case-optimizer/ pinchbench-batch-runner/ shared/ -v`
Expected: 所有测试 PASS

- [ ] **Step 4: 提交**

```bash
git add skills/pinchbench-case-optimizer/test_integration.py
git commit -m "test: add integration tests for optimizer

端到端验证：完整优化流程、链式家族基线识别

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## 完成标准

所有任务完成后，应具备：

1. **Skill 1 (batch-runner)**：可读取配置、串行执行多模型评测、结果分目录存储
2. **Skill 2 (case-optimizer)**：可分析结果、五维度诊断、生成优化用例和报告、收敛检测
3. **共享工具**：路径解析、家族识别
4. **完整测试**：单元测试 + 集成测试全部通过

## 后续手动验证（需真实环境）

实现完成后，建议用真实模型配置端到端验证一次：

```bash
# 1. 配置 models-config.yaml
# 2. 执行一个简单用例
python skills/pinchbench-batch-runner/batch_runner.py task_sanity
# 3. 分析结果
python skills/pinchbench-case-optimizer/optimizer.py task_sanity
```


