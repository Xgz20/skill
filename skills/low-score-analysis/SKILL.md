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

### 第 1 步：生成中间过程清单（脚本）

运行本 Skill 自带脚本解析中间过程，筛出低分任务：

```bash
python3 <skill_dir>/scripts/generate_failed_tasks_manifest.py \
  --result-root <评测结果根目录> \
  --model <模型名> \
  --threshold 60
```

脚本会：筛出 `score < 阈值/100` 的任务 → 为每个任务汇总 `task_id / score_pct / 任务文件路径 / grading详情 / transcript.jsonl路径` → 写入 `<result-root>/report-workspace/_failed_tasks_<model>.json`，并在末行打印 `MANIFEST_PATH=<路径>`。

读取该清单，得到 `tasks` 数组（每项含 `task_id`、`score_pct`、`grading_detail`）。

### 第 2 步：用 Workflow 并发分析

**必须用 Workflow 工具**做并发分析（每个低分任务一个 agent）。脚本模板见 `<skill_dir>/references/workflow_template.js`，直接把其内容作为 `script` 传给 Workflow 工具，并通过 `args` 传入：

```json
{
  "model": "<模型名>",
  "project": "<PinchBench 项目根的绝对路径>",
  "result_root": "<评测结果根目录绝对路径>",
  "tasks": [
    {
      "task_id": "...",
      "score_pct": 0.0,
      "grading_detail": {...},
      "task_file": "/path/to/example.md",
      "transcript": "/path/to/transcript.jsonl"
    },
    ...
  ]
}
```

每个 agent 按模板里的提示词：① 从 `grading_detail` 列出所有失分检查点 → ② 读任务文件理解目标 → ③ 带着每个失分点**全量直读 transcript.jsonl** 找证据 → ④ schema 强制输出 `{task_id, result_analysis, root_cause_analysis}`。

> 规模提示：100+ 个任务约 10-20M tokens、15+ 分钟，并发自动限流。任务越多耗时越长，可先用较低阈值缩小范围。

### 第 3 步：写入结果 JSON

Workflow 返回的结果在 `output['result']`（数组）。转成 `{task_id: {result_analysis, root_cause_analysis}}` 映射，写入：

```
<result-root>/report-workspace/analysis_<model>.json
```

### 第 4 步（可选）：回填 Excel 报告

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
