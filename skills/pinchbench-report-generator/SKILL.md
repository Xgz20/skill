---
name: pinchbench-report-generator
description: 分析 PinchBench 多模型评测结果，生成结构化对比报告。Use when 需要将一次或多次 PinchBench 评测的执行结果（含 transcripts）整理成评测报告、对比多个模型的得分与能力、或对某个目标模型做失分点深度分析时。读取评测结果目录，产出 Markdown 对比报告。
metadata:
  version: "1.0.0"
  author: astronclaw
---

# PinchBench 评测报告生成器

三阶段流水线：Python 收集统计 → LLM 深度分析 → Python 渲染报告。Python 保证数字准确，LLM 负责失分点语义分析。

## 何时使用

- PinchBench 在一个或多个模型上执行完毕，需生成评测对比报告
- 需要对某个目标模型（默认 xsparkx2flash）做详尽的优劣势分析
- 输入可以是总目录（自动发现所有模型）或多个具体模型目录

## 前置条件

- 已有 PinchBench 评测结果目录，每个模型目录含结果 JSON + `*_transcripts/`

## 三阶段工作流

### 阶段1：收集数据（Python）

```bash
python skills/pinchbench-report-generator/scripts/report_cli.py collect \
  <result_dir...> \
  --target-model xsparkx2flash \
  --tasks-root tasks \
  --output collected_data.json \
  [--thresholds all_low=0.4,gap=0.2,min_others=0.8,absolute=0.8]
```

产出 `collected_data.json`，含模型统计、任务矩阵、分类别汇总、`tasks_to_analyze`（待深度分析任务及其 transcript/任务md 路径与入选原因）。

### 阶段2：深度分析（LLM，由你执行）

读取 `collected_data.json` 后，对 `tasks_to_analyze` 中的每个任务：

1. 读 `target_transcript`（目标模型过程），必要时读 `best_other_transcript`（高分对比模型）做对照
2. 读 `task_md`（任务定义），提取 **Grading Criteria / Automated Checks / LLM Judge Rubric**，翻译成中文
3. 参考 `references/agent-capability-dimensions.md`（20 个能力维度），为任务做能力归类
4. 结合 breakdown + notes + transcript 行为，分析目标模型失分点与对比模型为何得分

按入选原因区分分析角度：
- `relative_weakness`：目标模型独有短板，重点对比目标 vs 对比模型的行为差异
- `all_low`：全员低分，重点分析任务本身难度或环境问题
- `absolute_low`：单模型场景的绝对低分

产出 `analysis.json`，结构：

```json
{
  "capability_mapping": {"<task_id>": ["能力维度名", ...]},
  "task_analysis": [{
    "task_id": "...", "filter_reason": "relative_weakness|all_low|absolute_low",
    "grading_criteria_cn": "评分标准中文翻译",
    "target_model_breakdown": {"notes": "...", "transcript_summary": "关键行为摘要"},
    "comparison_models": [{"model": "...", "score": 1.0, "why_succeeded": "..."}],
    "root_cause": "根本原因"
  }],
  "target_model_weaknesses": [{
    "theme": "短板主题", "related_tasks": ["..."],
    "evidence": "证据", "comparison": "对比模型表现",
    "token_data": {"target": 0, "others_avg": 0}
  }],
  "improvement_suggestions": [{
    "priority": "P0|P1|P2", "direction": "...",
    "expected_gain": "+X.X%", "explanation": "..."
  }]
}
```

**Context 控制**：阶段1 已筛掉高分任务。transcript 大时只读关键片段（toolCall/toolResult/thinking），提取工具调用次数、失败模式、token 消耗，不全量灌入。

### 阶段3：渲染报告（Python）

```bash
python skills/pinchbench-report-generator/scripts/report_cli.py render \
  --collected-data collected_data.json \
  --analysis analysis.json \
  --output <result_dir 或 具体md路径>
```

`--output` 传目录时，文件名自适应：多模型 `comparison_<N>_models_report.md`，单模型 `<target>_evaluation_report.md`。

## 报告结构

参考 `astronclaw-result/core-suite/round-2/comparison_four_models_report.md`：
整体排名 → Agent核心能力对比 → 分类别得分 → 各任务详细得分 → 目标模型短板深度分析 → Token效率 → 分项排名 → 改进建议。单模型时跳过排名/Token对比章节。

## 目录结构

```
pinchbench-report-generator/
├── SKILL.md                 # 本文档（metadata + 指令）
├── scripts/                 # 可执行 Python 模块
│   ├── models.py            # 数据类（TaskResult/ModelResult）
│   ├── result_collector.py  # 模型目录识别与 JSON 解析
│   ├── score_calculator.py  # 统计指标计算
│   ├── task_filter.py       # 低分任务筛选
│   ├── collect.py           # 阶段1 编排
│   ├── report_renderer.py   # 阶段3 报告渲染
│   └── report_cli.py        # CLI 入口（collect/render）
├── tests/                   # 单元测试 + 集成测试
└── references/
    └── agent-capability-dimensions.md  # 能力维度定义（阶段2 参考）
```

## 设计说明

- Python 算所有表格数字，LLM 只产出分析文字章节，避免 LLM 拼表格算错
- `references/agent-capability-dimensions.md` 为 Skill 内置副本，不依赖外部 docs/ 路径
