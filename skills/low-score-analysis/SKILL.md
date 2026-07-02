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

- **评测结果根目录**（`--result-root`）：
  - **单模型模式**：直接指定模型目录，如 `/path/to/results/xsparkx2flash-530`
  - **多模型模式**：指定包含多个模型子目录的根目录，如 `/path/to/results`
- **模型信息**（`--model`）：多模型模式时必须指定，单模型模式可省略
- **低分阈值**（`--threshold`，百分制，默认 60）：三轮**平均分**低于此值的任务列入「低分主口径」
- **高波动阈值**（`--variance-threshold`，百分制，默认 50）：平均分≥阈值、但三轮极差(max-min)≥此值的任务列入「高波动/稳定性专项」（如 [100,0,100] 这类单轮偶发塌陷）

> **双通道选取**：脚本按「主口径（均分<60）+ 高波动专项（均分≥60 但极差≥50）」两个通道并集选取任务，每条记录用 `low_score_type` 字段标注归属（`low` / `high_variance`），并附 `score_range_pct` 极差字段。分析（per-task，与筛选口径无关）对两桶通用；报告据此分章：主口径进正文，高波动进稳定性专项。

脚本会**自动检测目录模式**：
- 如果 `--result-root` 本身包含评测结果 JSON → 单模型模式，workspace 在模型目录内
- 如果 `--result-root` 下有子目录包含 JSON → 多模型模式，workspace 在根目录

## 输出

**单模型模式**（workspace 在模型目录内）：
```
model-dir/
  └── report-workspace/
      ├── _failed_tasks_<model>.json    ← 低分任务清单
      └── analysis_<model>.json         ← 根因分析结果
```

**多模型模式**（workspace 与模型目录平级）：
```
results-root/
  ├── model-1/
  ├── model-2/
  └── report-workspace/
      ├── _failed_tasks_model1.json
      ├── _failed_tasks_model2.json
      ├── analysis_model1.json
      └── analysis_model2.json
```

## 执行流程

### 第 1 步：生成任务清单

运行本 Skill 自带脚本解析评测结果，筛出低分任务。

**单模型目录模式**（推荐）：
```bash
python3 <skill_dir>/scripts/generate_failed_tasks_manifest.py \
  --result-root <模型目录路径> \
  --threshold 60

# 示例
python3 .claude/skills/low-score-analysis/scripts/generate_failed_tasks_manifest.py \
  --result-root results-astronclaw-local/xsparkx2flash-530 \
  --threshold 60
```

**多模型根目录模式**：
```bash
python3 <skill_dir>/scripts/generate_failed_tasks_manifest.py \
  --result-root <评测结果根目录> \
  --model <模型目录名> \
  --threshold 60

# 示例
python3 .claude/skills/low-score-analysis/scripts/generate_failed_tasks_manifest.py \
  --result-root astronclaw-result/all-suite/round-3 \
  --model xsparkx2flash-530 \
  --threshold 60
```

脚本输出：
- **单模型模式**：`<模型目录>/report-workspace/_failed_tasks_<model>.json`
- **多模型模式**：`<结果根>/report-workspace/_failed_tasks_<model>.json`

**⚠️ 重要提示**：脚本会显示**实际模型名**（从评测结果 JSON 中读取）和**工作区目录位置**。后续生成的分析文件必须使用模型名命名，并保存到显示的工作区目录。

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

`scripts/generate_eval_report.py` 支持 `--analysis` 参数，把结果回填到对应模型用例详情 Sheet 的「结果分析」「根因分析」两列。

**⚠️ 关键要求：分析文件名必须包含模型名**

报告脚本通过**文件名匹配模型名**来识别分析结果。如果文件名不匹配，回填会失败并显示警告：

```
警告：分析文件为 task_id 字典格式，但无法从文件名 xxx 匹配到已加载模型
已加载分析回填合计 0 条  ← 回填失败
```

**命名规范**：

✅ **正确**：`analysis_<实际模型名>.json`
```bash
# 示例：模型名是 xsparkx2flash
analysis_xsparkx2flash.json          ← 能匹配
analysis_xsparkx2flash_v2.json       ← 能匹配（模型名作为子串）
```

❌ **错误**：使用目录名而非模型名
```bash
# 示例：目录名是 debug-001，但模型名是 xsparkx2flash
analysis_debug-001.json              ← 无法匹配，回填失败
```

**如何查看实际模型名**：

在第 1 步运行 `generate_failed_tasks_manifest.py` 时，脚本会输出：
```
模型目录: debug-001
实际模型名: xsparkx2flash ⚠️  (与目录名不同)
...
💡 提示：如需回填 Excel 报告，请确保分析文件名包含模型名 'xsparkx2flash'
   建议命名: analysis_xsparkx2flash.json
```

**修复方法**（如果已生成错误命名的文件）：

方法 1 - **重命名文件**（推荐）：
```bash
cd <workspace>
mv analysis_<目录名>.json analysis_<模型名>.json
mv analysis_<目录名>_batch_*.json analysis_<模型名>_batch_*.json
```

方法 2 - **使用显式模型绑定**：
```bash
python3 scripts/generate_eval_report.py \
  -d <result-dir> \
  --analysis MODEL=<模型名>:<workspace>/analysis_<目录名>.json
```

**回填示例**：

```bash
# 单模型回填
python3 scripts/generate_eval_report.py \
  -d results-astronclaw-local/debug-001 \
  --analysis results-astronclaw-local/report-workspace/analysis_xsparkx2flash.json

# 多模型回填
python3 scripts/generate_eval_report.py \
  -d <result-root>/<model1> <result-root>/<model2> \
  --analysis <workspace>/analysis_<model1>.json \
  --analysis <workspace>/analysis_<model2>.json \
  --output report_multi_models.xlsx
```

**验证回填成功**：

脚本输出应显示：
```
已加载分析回填合计 N 条（来自 1 个文件）  ← N > 0 表示成功
```

生成的 Excel 文件中，对应模型的"评分详情"Sheet 的「第1轮结果分析」「第1轮根因分析」列应包含分析内容。

**高级格式**（多模型合并文件）：

如需一个文件包含多个模型的分析，使用键值格式 `<model>::<task_id>`：
```json
{
  "xsparkx2flash::task_calendar": {
    "result_analysis": "...",
    "root_cause_analysis": "..."
  },
  "glm51::task_calendar": {
    "result_analysis": "...",
    "root_cause_analysis": "..."
  }
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
