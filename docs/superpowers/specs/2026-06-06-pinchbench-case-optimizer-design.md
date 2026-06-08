# PinchBench 评测用例优化 Skill 设计文档

**日期**：2026-06-06
**状态**：设计待审核
**关联**：[pinchbench-case-generator](2026-06-03-pinchbench-case-generator-skill-design.md)

---

## 1. 背景与目标

PinchBench 已支持用例生成（`pinchbench-case-generator`），生成的用例默认输出到 `output/generated_cases/`。但新生成的用例质量未经验证，需要一套机制：

1. 在多个被评测模型上实际执行用例
2. 根据多模型的评测结果和中间过程（交互 transcript）反向逆推用例的合理性
3. 分析优化点，产出优化后的用例和详细报告
4. 支持多轮迭代优化

**核心场景**：新用例验证——刚生成评测用例后，在多个模型上试跑并优化。

**用例生命周期**：
```
生成 (output/generated_cases/) → 验证优化 (本 Skill，多轮) → 晋升 (tasks/)
```
`tasks/` 目录理论上只存放验证通过、真实可用的用例。

---

## 2. 整体架构

采用**双 Skill 协作式架构**，将评测执行和用例优化分离，形成可复用工具链：

```
pinchbench-case-generator → pinchbench-batch-runner → pinchbench-case-optimizer
     (生成用例)                (批量执行)                  (分析优化)
                                     ↓
                              [多轮迭代循环]
```

### 数据流

```
  输入用例                  batch-runner              结果
  task_xxx_r(N-1)  ──────►  串行执行多模型  ──────►  results-auto/
  (N=1时为原始)             读取models-config         task_xxx/round_N/
                                                          │
                                                          ▼
  优化产物                  case-optimizer            分析
  task_xxx_rN.md   ◄──────  五维度分析      ◄──────  读取round_N结果
  报告 _rN_report          链式演进                  + transcripts
                                │
                                ▼
                        收敛检测 + 询问用户
                                │
                          ┌─────┴─────┐
                          ▼           ▼
                      继续Round    停止
                       N+1
```

---

## 3. 配置管理

### 设计原则
- **单一配置文件**：`models-config.yaml`（不使用 `.env`）
- **安全**：配置文件加入 `.gitignore`，Skill 本身不含任何敏感信息
- **低门槛**：Skill 提供模板，首次运行自动复制并提示用户填写

### 配置文件结构

```yaml
# models-config.yaml（位于项目根目录 skill/）

# 裁判模型配置（唯一）
judge:
  model_id: anthropic/claude-sonnet-4-6
  api_key: "your-judge-api-key"
  base_url: "https://one.iflytek.com/api/llm/console/chat"

# 被评测模型列表（可多个，串行执行）
models_under_test:
  - model_id: xopglm5
    api_key: "your-model-api-key"
    base_url: "https://maas-api.cn-huabei-1.xf-yun.com/v2"
  - model_id: spark-x
    api_key: "your-model-api-key"
    base_url: "https://..."
```

### 模板文件
- 位置：`skills/pinchbench-batch-runner/models-config.yaml.example`
- 首次运行逻辑：
  ```python
  config_path = project_root / "models-config.yaml"
  if not config_path.exists():
      shutil.copy(template_path, config_path)
      print("✅ 已创建配置文件: models-config.yaml")
      print("⚠️  请编辑该文件，填写模型的 api_key 和 base_url")
      exit(0)  # 提示用户配置后再运行
  ```

### .gitignore 补充
```gitignore
results-auto         # 已有
models-config.yaml   # 需补充（保护敏感信息）
```

---

## 4. Skill 1：pinchbench-batch-runner

### 职责
读取配置 → 串行执行多个模型的评测 → 结果分目录存储。

### 输入
- 评测用例（支持 task_id 或文件路径，见 §6 路径解析）
- 轮次号（可选，默认自动递增）
- 配置文件 `models-config.yaml`

### 核心工作流

```python
def batch_run(task_input, round_num=None):
    # 1. 配置检查
    config_path = project_root / "models-config.yaml"
    if not config_path.exists():
        copy_template_and_exit()

    config = load_yaml(config_path)
    judge = config["judge"]
    models = config["models_under_test"]

    # 2. 解析用例路径（支持任意目录）
    source = resolve_task_path(task_input)
    task_id = source.stem

    # 3. 轮次自动检测（同一task_id的多次评测）
    if round_num is None:
        round_num = detect_next_round(task_id)  # 扫描 results-auto/<task_id>/round_*

    output_base = f"results-auto/{task_id}/round_{round_num}"
    # 注意：task_id 是真实文件名（如 task_xxx_r1），结果目录与之对应

    # 4. 临时复制到 tasks/（框架限制，见 §6）
    temp_in_tasks = Path(f"tasks/{task_id}.md")
    already_in_tasks = temp_in_tasks.exists() and temp_in_tasks.samefile(source)
    if not already_in_tasks:
        shutil.copy(source, temp_in_tasks)

    try:
        # 5. 串行执行每个模型
        for model in models:
            cmd = build_command(model, judge, task_id,
                                output_dir=f"{output_base}/{model['model_id']}")
            run(cmd)  # 调用 scripts/run.sh
    finally:
        # 6. 清理临时文件
        if not already_in_tasks:
            temp_in_tasks.unlink()

    return output_base
```

### 命令组装示例

```bash
export ANTHROPIC_API_KEY="<judge.api_key>"
export ANTHROPIC_BASE_URL="<judge.base_url>"
./scripts/run.sh \
  --model <model.model_id> \
  --base-url <model.base_url> \
  --api-key <model.api_key> \
  --judge <judge.model_id> \
  --suite <task_id> \
  --output-dir results-auto/<task_id>/round_<N>/<model.model_id> \
  --no-upload \
  --verbose
```

### 输出结构

```
results-auto/<task_id>/round_<N>/
├── xopglm5/
│   ├── 0001_xopglm5.json              # 评测结果
│   └── <run_id>_transcripts/          # 交互过程
│       └── <task_id>.jsonl
├── spark-x/
│   ├── 0001_spark-x.json
│   └── <run_id>_transcripts/
└── batch-run-summary.md               # 本轮执行摘要
```

示例：
- `results-auto/task_csv_iris_summary/round_1/` — 原始用例第1次评测
- `results-auto/task_csv_iris_summary_r1/round_1/` — 优化用例r1第1次评测
- `results-auto/task_csv_iris_summary_r1/round_2/` — 优化用例r1第2次评测（验证稳定性）

### 关键设计点
- **串行执行**：符合 PinchBench 限制（任务循环硬编码串行），每个模型跑完再跑下一个
- **结果隔离**：每个模型独立目录，便于对比
- **进度可见**：实时输出每个模型的执行状态和得分
- **失败容错**：单个模型失败不影响其他模型，记录在摘要中
- **临时文件清理**：`finally` 块保证异常时也能清理

---

## 5. Skill 2：pinchbench-case-optimizer

### 职责
读取批量评测结果 → 五维度分析 → 生成优化用例 + 详细报告。

### 输入
- 原始评测用例（task_id 或路径）
- 批量评测结果目录（可选）：
  - **不指定** → 默认读取 `results-auto/<task_id>/round_<最大N>`
  - **指定** → 读取指定目录

**注意**：optimizer 在链式演进中需要识别"用例家族"，以便跨版本对比优化效果。例如分析 `task_xxx_r1` 时，需要能找到 `task_xxx` 的结果做基线对比。

### 核心工作流

```python
def optimize_case(task_input, results_dir=None):
    # 1. 加载源用例
    source = resolve_task_path(task_input)
    task_id = source.stem
    original_task = load_task(source)

    # 2. 默认读取最新结果
    if results_dir is None:
        results_dir = find_latest_round(f"results-auto/{task_id}")

    round_num = extract_round_number(results_dir)

    # 3. 收集所有模型结果 + transcripts
    model_results = collect_model_results(results_dir)

    # 4. 提取 base_task_id 用于家族识别
    base_task_id = extract_base_task_id(task_id)  # task_xxx_r1 → task_xxx
    
    # 5. 加载上一轮结果（用于收敛对比）
    prev_results = find_previous_round_results(task_id)  # 找家族中的上一版本

    # 6. 五维度分析
    analysis = {
        "prompt_clarity":  analyze_prompt_clarity(original_task, model_results),
        "grading_validity": analyze_grading(original_task, model_results),
        "difficulty":       analyze_difficulty(model_results),
        "timeout":          analyze_timeout(model_results),
        "tool_usage":       analyze_tool_usage(model_results),
    }

    # 7. 计算优化轮次（家族内的第N个优化版本）
    optimization_round = extract_optimization_round(task_id)  # task_xxx → 0, task_xxx_r1 → 1

    # 8. 生成优化用例（产物与源同目录，链式演进）
    output_path = source.parent / f"{base_task_id}_r{optimization_round + 1}.md"
    write_optimized_task(output_path, original_task, analysis)

    # 9. 生成详细报告
    report_path = f"optimization-reports/{base_task_id}/{base_task_id}_r{optimization_round + 1}_report.md"
    write_report(report_path, analysis, model_results, prev_results)

    # 10. 收敛检测 + 询问用户
    convergence = check_convergence(optimization_round + 1, analysis, prev_results)
    prompt_next_round(convergence)
```

**关键函数**：
```python
def extract_base_task_id(task_id):
    """task_csv_iris_summary_r2 → task_csv_iris_summary"""
    return re.sub(r'_r\d+$', '', task_id)

def extract_optimization_round(task_id):
    """task_csv_iris_summary → 0, task_csv_iris_summary_r2 → 2"""
    match = re.match(r'^.+_r(\d+)$', task_id)
    return int(match.group(1)) if match else 0

def find_previous_round_results(task_id):
    """找到用例家族中上一版本的结果，用于对比"""
    base = extract_base_task_id(task_id)
    current_round = extract_optimization_round(task_id)
    if current_round == 0:
        return None  # 原始用例，无基线
    prev_round = current_round - 1
    prev_id = base if prev_round == 0 else f"{base}_r{prev_round}"
    # 返回该版本的最新一次评测结果
    return find_latest_round(f"results-auto/{prev_id}")
```

### 五维度分析

| 维度 | 分析方法 | 优化触发条件 |
|------|----------|--------------|
| **A. Prompt 清晰度** | 对比各模型 transcript 中的理解偏差 | 多个模型对同一指令有不同解读 |
| **B. 评分标准合理性** | 检查得分与实际完成质量的匹配度 | 评分与实际表现不符（过严/过松）|
| **C. 难度区分度** | 计算分数分布（方差、极差）| 全部满分/全部 0 分，或方差过小 |
| **D. 超时设置** | 统计 timeout 发生率 | 任一模型因超时失败 |
| **E. 工具使用合理性** | 分析 tool_call 成功率和 gap | 工具调用失败率高，或缺少必要工具 |

### 输出 1：优化后的用例
- **新文件**，不修改原文件
- **轮次标记** `_r1`, `_r2`...
- **与源用例同目录**（生命周期一致）：
  - 源在 `output/generated_cases/` → 产物在 `output/generated_cases/task_xxx_r1.md`
  - 源在 `tasks/` → 产物在 `tasks/task_xxx_r1.md`

### 输出 2：详细优化报告

位置：`optimization-reports/<base_task_id>/<base_task_id>_r<N>_report.md`

（`base_task_id` 指去除 `_r<N>` 后缀的原始用例 ID，确保同一用例的所有轮次报告聚合在同一目录下。优化产物用例文件名同理用 `<base_task_id>_r<N>.md`。）

报告结构（详细分析版）：

```markdown
# 评测用例优化报告 - <task_id> (Round N)

## 执行概览
- 评测轮次、参与模型、配置裁判

## 模型表现总览
| 模型 | 得分 | 用时 | 是否超时 | Token消耗 |

## 维度A：Prompt清晰度分析
### 发现的问题（含 transcript 片段引用）
### 优化建议（具体改动）

## 维度B：评分标准合理性
## 维度C：难度区分度
## 维度D：超时设置
## 维度E：工具使用

## 优化改动清单
| 改动项 | 原值 | 新值 | 维度 | 理由 |

## 收敛性判断
- 本轮发现问题数
- 与上轮对比（改进幅度）
- 建议：继续/停止
```

### 收敛检测（混合方式）

```python
def check_convergence(round_num, current_analysis, prev_analysis=None):
    signals = []
    # 信号1：无新问题
    if count_issues(current_analysis) == 0:
        signals.append("无新问题发现")
    # 信号2：与上轮对比改进幅度
    if prev_analysis and compare_scores(current, prev) < 0.05:
        signals.append("分数提升<0.05，趋于收敛")
    # 信号3：最大轮次
    if round_num >= 5:
        signals.append("达到最大轮次限制")
    return {
        "converged": len(signals) > 0,
        "signals": signals,
        "recommendation": "建议停止" if signals else "建议继续优化"
    }
```

终止逻辑：**收敛检测给出建议，最终由用户决定**（每轮结束后询问是否进入下一轮）。

---

## 6. 路径解析与框架适配

### 框架约束
PinchBench 的 `tasks_dir` **硬编码**为 `skill_root/tasks`（`benchmark.py:729`），无 `--tasks-dir` 参数，`--suite` 只接受 task_id（去 `tasks/<task_id>.md` 查找）。框架原生不支持从其他目录加载用例。

### 解决方案：临时复制 + 执行后清理（不改框架）
batch-runner 执行前把指定用例临时复制到 `tasks/`，执行完在 `finally` 块删除。优点是对框架完全透明，避免与上游产生分歧。

### 统一路径解析（两个 Skill 共用）

```python
def resolve_task_path(task_input):
    """支持三种输入形式"""
    # 1. 纯 task_id：默认 tasks/，回退 output/generated_cases/
    if "/" not in task_input and not task_input.endswith(".md"):
        for base in ["tasks", "output/generated_cases"]:
            candidate = Path(f"{base}/{task_input}.md")
            if candidate.exists():
                return candidate
    # 2. 显式路径
    return Path(task_input)
```

### 边界处理
- 若 `tasks/` 已存在同名真实用例且与源是同一文件 → 不复制、不删除（避免误删真实用例）
- 清理在 `finally` 块，确保异常时也能执行

---

## 7. 多轮迭代模型（链式演进）

采用**链式演进**：每轮基于上一轮优化后的用例继续优化。这是收敛检测有意义的前提——必须执行优化后的用例，才能验证优化效果。

```
原始: task_csv_iris_summary
  ↓ Round 1 执行原始 + 优化
task_csv_iris_summary_r1
  ↓ Round 2 执行 _r1 + 优化
task_csv_iris_summary_r2
  ↓ Round 3 ...
```

### 命名规则（不累积后缀）

```python
def get_input_task(base_task_id, round_num):
    """Round N 执行 Round N-1 的产物"""
    return base_task_id if round_num == 1 else f"{base_task_id}_r{round_num-1}"

def get_output_task(base_task_id, round_num):
    """Round N 产出 _r<N>"""
    return f"{base_task_id}_r{round_num}"
```

### 结果目录（按真实 task_id 分目录）

```
results-auto/task_csv_iris_summary/round_1/     # 原始用例第1次评测
results-auto/task_csv_iris_summary/round_2/     # 原始用例第2次评测（验证稳定性）
results-auto/task_csv_iris_summary_r1/round_1/  # 优化用例r1第1次评测
results-auto/task_csv_iris_summary_r1/round_2/  # 优化用例r1第2次评测
results-auto/task_csv_iris_summary_r2/round_1/  # 优化用例r2第1次评测
```

**语义**：
- 第一层目录 = 用例版本（task_id，从文件名提取）
- 第二层目录 = 该版本的评测轮次（round_N，支持同一版本多次评测）

**优点**：
- 结果目录与实际执行的 task_id 一致，语义清晰
- 支持单个优化版本的多轮评测（验证稳定性、调整模型配置后重跑）
- 避免歧义（task_id 是框架核心概念，应与文件系统保持一致）

**optimizer 的家族识别**：
optimizer 通过正则提取 `base_task_id`（去除 `_r\d+` 后缀），找到用例家族的上一版本结果进行基线对比。例如分析 `task_xxx_r1` 时，自动查找 `results-auto/task_xxx/round_<最新>/` 作为基线。

---

## 8. 文件组织总览

```
PinchBench/skill/
├── models-config.yaml              # 用户配置（gitignore）
├── models-config.yaml.example      # 模板（Skill提供）
├── .gitignore                      # 补充 models-config.yaml
│
├── skills/
│   ├── pinchbench-case-generator/  # 已有
│   ├── pinchbench-batch-runner/    # 新增 Skill 1
│   │   ├── SKILL.md
│   │   └── models-config.yaml.example
│   └── pinchbench-case-optimizer/  # 新增 Skill 2
│       └── SKILL.md
│
├── tasks/                          # 真实可用用例库（晋升目标）
│   └── task_xxx.md
│
├── output/generated_cases/         # 生成器输出 + 优化产物
│   ├── task_xxx.md
│   ├── task_xxx_r1.md              # 优化产物（同源目录）
│   └── task_xxx_r2.md
│
├── results-auto/                   # 自动化评测结果（gitignore）
│   ├── task_csv_iris_summary/
│   │   ├── round_1/                # 原始用例第1次评测
│   │   └── round_2/                # 原始用例第2次评测
│   ├── task_csv_iris_summary_r1/
│   │   ├── round_1/                # 优化用例r1第1次评测
│   │   └── round_2/                # 优化用例r1第2次评测
│   └── task_csv_iris_summary_r2/
│       └── round_1/                # 优化用例r2第1次评测
│
└── optimization-reports/           # 优化报告
    └── task_xxx/
        ├── task_xxx_r1_report.md
        └── task_xxx_r2_report.md
```

---

## 9. 使用示例

```bash
# Step 1：首次配置（无配置文件时自动生成模板）
/pinchbench-batch-runner output/generated_cases/task_csv_iris_summary
# → 创建 models-config.yaml，提示填写

# Step 2：填写 models-config.yaml 后，Round 1 批量执行（原始用例）
/pinchbench-batch-runner output/generated_cases/task_csv_iris_summary
# → results-auto/task_csv_iris_summary/round_1/

# Step 3：Round 1 分析优化（产出_r1）
/pinchbench-case-optimizer output/generated_cases/task_csv_iris_summary
# → output/generated_cases/task_csv_iris_summary_r1.md
# → optimization-reports/task_csv_iris_summary/task_csv_iris_summary_r1_report.md
# → 收敛分析 + 询问是否继续优化

# Step 4：Round 2 批量执行（优化用例_r1）
/pinchbench-batch-runner output/generated_cases/task_csv_iris_summary_r1
# → results-auto/task_csv_iris_summary_r1/round_1/

# Step 5：Round 2 分析优化（产出_r2）
/pinchbench-case-optimizer output/generated_cases/task_csv_iris_summary_r1
# → optimizer 自动识别家族，对比 task_csv_iris_summary vs task_csv_iris_summary_r1
# → output/generated_cases/task_csv_iris_summary_r2.md
# → optimization-reports/task_csv_iris_summary/task_csv_iris_summary_r2_report.md

# Step 6：（可选）对_r1进行多次评测验证稳定性
/pinchbench-batch-runner output/generated_cases/task_csv_iris_summary_r1
# → results-auto/task_csv_iris_summary_r1/round_2/
/pinchbench-batch-runner output/generated_cases/task_csv_iris_summary_r1
# → results-auto/task_csv_iris_summary_r1/round_3/
# optimizer 可以聚合分析 round_1-3 的结果

# Step 7：验证通过后，晋升到 tasks/
```

---

## 10. 需求满足检查表

| 需求 | 设计满足 |
|------|----------|
| 新用例验证场景 | ✅ batch-runner + optimizer 工具链 |
| 配置文件方式 | ✅ 单一 models-config.yaml + 模板 |
| 五维度分析 (A-E) | ✅ optimizer 核心逻辑 |
| 详细分析版报告 | ✅ 含 transcript 片段的分维度报告 |
| 自动轮次递增 | ✅ round_N 自动检测 |
| 混合终止条件 | ✅ 收敛检测 + 用户询问 |
| 安全（无敏感信息） | ✅ config 在 gitignore，Skill 不含密钥 |
| 多轮链式演进 | ✅ 模型A：Round N 执行 _r(N-1) |
| results-auto 区分 | ✅ 独立输出目录 |
| 支持非 tasks 目录用例 | ✅ 方案1临时复制，产物同源目录 |
| 用例生命周期管理 | ✅ 生成→验证优化→晋升 |

---

## 11. 待实现确认点（实现阶段处理）

1. `models-config.yaml` 加入 `.gitignore`
2. transcript JSONL 解析逻辑（提取模型理解偏差、tool_call 信息）
3. 结果 JSON 字段映射（grading.mean, usage, timed_out 等）
4. 收敛检测中 prev_analysis 的加载（读取上一轮报告或结果）
