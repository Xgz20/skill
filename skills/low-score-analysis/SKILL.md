---
name: low-score-analysis
description: Use when the user wants to analyze why a model scored low on PinchBench evaluation tasks — root-cause analysis of failed/low-score tasks. Triggers on requests like "分析低分任务""失分根因分析""为什么这个模型在某些任务上得分低""low score analysis""root cause of failures". Reads grading details + transcript evidence and produces per-task result analysis and root cause analysis JSON.
---

# 低分任务根因分析 Skill（PinchBench 版）

为 PinchBench 评测产出**低分任务的根因分析**。对某个模型筛出得分低于阈值的任务，逐个任务用 LLM 结合评测判词（从 summary.json 的 grading 字段）和执行全过程（transcript.jsonl）找出失分的**事实依据与根本原因**，结果写入 JSON，可供评测报告脚本回填到 Excel。

## 核心原则：用证据说话，不臆测

评分细节是"判决书"（完整、不可摘要）：`grading.runs[0].breakdown` 标出哪个检查点扣分，`notes` 是裁判判词。分析的正确做法不是"看摘要下结论"，而是：

> 带着 grading 列出的**每一个失分点**这个具体问题，去 transcript 这个"案发现场"**全量直读**找证据。

绝不预先有损摘要 transcript，否则摘要内容若与失分点无关，分析就会误判。

## 输入

- **评测结果根目录**（`--result-root`）：例如 `astronclaw-result/all-suite/round-3`，其下含各模型子目录，每个子目录有 `summary.json` 和每个任务的 `<task_id>/transcript.jsonl`
- **模型信息**（`--model`）：模型目录名，如 `xsparkx2flash-530`
- **低分阈值**（`--threshold`，百分制，默认 60）：`score` 低于此值（满分为 1.0）的任务列入分析

## 输出

均位于 **`<result-root>/report-workspace/`**：

1. **中间过程清单**：`_failed_tasks_<model>.json` —— 低分任务列表及其 grading/transcript/任务文件路径
2. **根因分析结果**：`analysis_<model>.json` —— `{task_id: {result_analysis, root_cause_analysis}}`

## 执行流程

### 第 1 步：生成任务清单

运行本 Skill 自带脚本解析评测结果，筛出低分任务：

```bash
python3 <skill_dir>/scripts/generate_failed_tasks_manifest.py \
  --result-root <评测结果根目录> \
  --model <模型名> \
  --threshold 60
```

脚本输出 `<result-root>/report-workspace/_failed_tasks_<model>.json`，包含所有低分任务的完整信息。

### 第 2 步：数据精简与安全检查（必须）

**为什么必须精简**：原始任务数据包含大量冗余字段（min_score_pct、max_score_pct 等统计值），会导致 Workflow 参数传输失败。精简后可减少 40-50% 体积，同时保留 100% 的分析关键信息（task_id、score_pct、breakdown、notes、transcript 路径）。

使用 `utils.py` 精简并检查数据大小：

```python
import json
from scripts.utils import simplify_task, analyze_data_size, split_into_batches

# 1. 读取任务清单
with open('_failed_tasks_<model>.json') as f:
    all_tasks = json.load(f)

# 2. 精简数据
simplified_tasks = [simplify_task(t) for t in all_tasks]

# 3. 检查大小（确保安全）
size_info = analyze_data_size(all_tasks)
print(f"原始: {size_info['original_size_mb']:.2f} MB → 精简后: {size_info['simplified_size_mb']:.2f} MB")
print(f"减少 {size_info['reduction_pct']:.1f}%")

# 4. 分批（每批不超过10个任务）
batches = split_into_batches(simplified_tasks, batch_size=10)
print(f"共 {len(simplified_tasks)} 个任务，分为 {len(batches)} 批")
```

### 第 3 步：分批调用 Workflow

**关键原则**：调用方（Claude主对话）必须自己分批，每次只传一个小批次（≤10个任务）给 Workflow。不能一次性传所有任务，即使已精简也会触发参数传输限制。

**执行步骤**：

1. **加载已完成任务**（断点续传）：
   ```python
   from scripts.utils import load_completed_tasks
   
   completed = load_completed_tasks(workspace_dir, model)
   completed_ids = list(completed.keys())
   print(f"已完成 {len(completed_ids)} 个任务，跳过")
   ```

2. **逐批次调用 Workflow 工具**：
   
   对每个批次，调用一次 Workflow 工具，参数设置：
   - `scriptPath`: `<skill_dir>/references/workflow_template.js`
   - `args.model`: 模型名
   - `args.project`: PinchBench 根目录
   - `args.result_root`: 评测结果根目录
   - `args.tasks`: **当前批次的任务列表**（10个任务）
   - `args.completed_task_ids`: 已完成的 task_id 列表（用于跳过）
   
   每批次返回结果后，立即保存到 `<workspace>/analysis_<model>_batch_<i>.json`，避免数据丢失。

3. **进度追踪**：
   - 每批次约耗时 2-3 分钟
   - 87 个任务分 9 批，总耗时约 20-25 分钟
   - 失败后重新运行会自动跳过已完成任务

**工作流模板特性**：
- ✅ **内部并行**: 单批次内的任务并发分析（pipeline模式）
- ✅ **容错**: 单个任务失败不影响其他任务
- ✅ **进度可观测**: 实时输出当前处理的任务

所有批次完成后，合并成最终结果文件：

```python
from scripts.utils import merge_all_batches

# 自动扫描 workspace 目录下所有 analysis_<model>_batch_*.json
final_file = merge_all_batches(
    workspace_dir=workspace_dir,
    model=model
)

print(f"✅ 最终结果: {final_file}")
# 输出: <workspace>/analysis_<model>.json
```

输出文件格式：
```json
{
  "task_id_1": {
    "result_analysis": "详细分析...",
    "root_cause_analysis": "根因总结..."
  },
  "task_id_2": {...}
}
```

### 第 5 步（可选）：回填 Excel 报告

`scripts/generate_eval_report.py` 支持 `--analysis` 参数，把结果回填到对应模型用例详情 Sheet 的「结果分析」「根因分析」两列：

```bash
python3 skill/scripts/generate_eval_report.py \
  -d <result-root>/<model1> <result-root>/<model2> ... \
  --analysis <report-workspace>/analysis_input.json \
  --output <输出xlsx>
```

其中 `analysis_input.json` 需包含所有模型的分析结果，格式为：
```json
{
  "<model1>::<task_id>": {
    "ra": "<result_analysis>",
    "rc": "<root_cause_analysis>"
  },
  ...
}
```

## transcript.jsonl 结构速查

JSONL 格式，每行一个事件。主要事件类型：
- `message`：包含 `message.content` 数组
  - `type=text`：模型输出文本
  - `type=thinking`：模型思考（不计入产出）
  - `type=tool_use`：工具调用，含 `name` 和 `input`，是模型**实际做的操作**
- `message` (role=user)：工具返回结果，`content[0].type=tool_result`

常见失分信号：只读不写（全是读文件的 tool_use，无写文件）、伪造工具调用（文本里写了调用但没有真正的 tool_use）、`error` 事件（如超时）导致半途中断、过早结束。

## 安装（软链接到 .claude/skills）

Skill 源码在 `skill/skills/low-score-analysis/`，使用前软链到项目的 `.claude/skills/`：

```bash
mkdir -p .claude/skills
ln -snf ../../skill/skills/low-score-analysis .claude/skills/low-score-analysis
```
