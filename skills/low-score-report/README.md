# 低分任务根因共性分析报告生成 Skill

为 PinchBench 评测产出**格式规范、层次分明、深度根因分析**的共性分析报告。

## 快速开始

### 1. 安装 Skill

```bash
cd /path/to/PinchBench
mkdir -p .claude/skills
ln -snf ../../skill/skills/low-score-report .claude/skills/low-score-report
```

### 2. 前置准备

确保已运行 `low-score-analysis` Skill 生成了必要的输入文件：
- `_failed_tasks_<model>.json`
- `analysis_<model>.json`

### 3. 使用

**独立分析**（默认）：
```
生成 xsparkx2flash-530 的低分任务根因分析报告
基于 astronclaw-result/all-suite/round-4
```

**带特殊配置说明**：
```
生成 xsparkx2flash-530 的低分任务根因分析报告
评测轮次：round-4
说明：超时时间相对 round-3 放大 4 倍
```

**对比分析**：
```
生成 xsparkx2flash-530 的低分任务根因分析报告
对比 round-3 与 round-4 的差异
```

## 输出

**报告文件**：`<result-root>/低分任务根因共性分析报告_<model>.md`（无版本后缀）

**报告标题格式**：`# AstronClaw PinchBench {模型显示名} 模型低分任务根因分析报告`

示例：
- `# AstronClaw PinchBench Spark 模型低分任务根因分析报告`
- `# AstronClaw PinchBench Claude 模型低分任务根因分析报告`

## 核心特性

✅ **四层归因框架**：L1a底层推理 / L1b长程执行 / L3环境 / L4评测
✅ **深度根因分析**：追溯到具体代码逻辑问题
✅ **层次化排版**：序号、缩进、分点，避免大段堆砌
✅ **通俗易懂**：避免AI腔，用事实说话
✅ **术语统一**：自动将 "provider" 替换为 "推理服务"
✅ **动态元信息**：从 summary.json 自动提取任务数、模型显示名
✅ **独立/对比模式**：默认独立分析，明确要求才包含对比

## 关键改进（v2）

1. **产物文件命名**：去掉 `_v4` 后缀，直接用 `低分任务根因共性分析报告_<model>.md`
2. **报告标题**：统一为 `# AstronClaw PinchBench {具体模型} 模型低分任务根因分析报告`
3. **评测轮次**：从 summary.json 自动提取实际任务数
4. **术语统一**：所有 "provider" 自动替换为 "推理服务"
5. **特殊配置提取**：支持用户输入评测特殊配置（如"超时4倍"）
6. **独立分析**：除非明确要求对比，否则不提及其他轮次

## 工具函数

`scripts/report_utils.py` 提供：
- `extract_eval_metadata()` - 从 summary.json 提取元信息
- `format_round_description()` - 生成轮次描述
- `normalize_terminology()` - 统一术语（provider→推理服务）
- `classify_root_causes()` - 根因分类统计
- `extract_layer_attribution()` - 层归属提取
- `extract_code_executions()` - 从 transcript 提取代码
- `analyze_key_error()` - KeyError 深度分析
- `format_task_table()` - 生成 Markdown 表格
- `generate_report_header()` - 生成报告头部

## 报告结构

1. **标题**：AstronClaw PinchBench {模型} 模型低分任务根因分析报告
2. **开头信息**：模型、轮次（含特殊配置）、样本数
3. **分析维度定义**
4. **执行摘要**
5. **根因分类统计**
6. **按根因详述**（含典型案例深析）
7. **跨任务关键发现**
8. **改进建议**（按层归类）

## 深度根因分析要求

对于代码类失败，不止步于"KeyError"，而是：
1. 提取失败代码片段
2. 分析具体错误原因（日期格式？排序键？）
3. 说明为什么模型反复调试仍失败
4. 给出修复方向

## 测试工具函数

```bash
cd /path/to/PinchBench/skill/skills/low-score-report/scripts
python3 report_utils.py
```

会输出元信息提取、轮次描述生成、根因分类等测试结果。

## 依赖

- Python 3.8+
- `low-score-analysis` Skill 的输出
- summary.json（用于提取元信息）
