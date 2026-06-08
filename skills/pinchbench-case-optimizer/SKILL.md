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

```bash
# 分析最新轮次结果
python skills/pinchbench-case-optimizer/scripts/optimizer.py task_xxx

# 指定结果目录
python skills/pinchbench-case-optimizer/scripts/optimizer.py task_xxx --results-dir results-auto/task_xxx/round_1

# 输出分析数据为 JSON（供 LLM 处理 A/B 维度）
python skills/pinchbench-case-optimizer/scripts/optimizer.py task_xxx --dump-analysis
```

> 注意：CLI 只覆盖 analyze 阶段（自动维度分析 + LLM 数据准备）。
> 完整两阶段流程通过 Python API 调用：上层 Skill agent 拿到 `run_optimization` 的输出后，
> 调用 LLM 完成维度 A/B 分析并生成优化用例内容，再调用 `finalize_optimization` 写入产物。

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

```
原始 task_xxx
  → batch-runner → optimizer → task_xxx_r1
  → batch-runner task_xxx_r1 → optimizer → task_xxx_r2
  → ...
```

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

## 目录结构

- `scripts/`：可执行脚本（optimizer.py, analyzers.py, convergence.py 等）
- `tests/`：单元和集成测试
- 共享工具（path_resolver）位于 `skills/shared/`
