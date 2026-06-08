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

```yaml
judge:
  model_id: anthropic/claude-sonnet-4-6
  api_key: "your-judge-api-key"
  base_url: "https://..."

models_under_test:
  - model_id: xopglm5
    api_key: "your-model-api-key"
    base_url: "https://..."
```

配置文件已在 `.gitignore` 中，不会提交到 git。

## 用法

```bash
# 执行用例（自动检测轮次）
python skills/pinchbench-batch-runner/scripts/batch_runner.py output/generated_cases/task_xxx

# 指定轮次
python skills/pinchbench-batch-runner/scripts/batch_runner.py task_xxx --round 2
```

## 输入

- 用例输入：支持 task_id（在 tasks/ 和 output/generated_cases/ 查找）或文件路径
- 轮次号：可选，默认自动递增

## 输出

```
results-auto/<task_id>/round_<N>/
├── <model_id>/
│   ├── 0001_<model_id>.json       # 评测结果
│   └── <run_id>_transcripts/      # 交互过程
└── batch-run-summary.md           # 执行摘要
```

## 工作流程

1. 读取 models-config.yaml
2. 解析用例路径
3. 自动检测轮次号
4. 临时复制用例到 tasks/（框架限制）
5. 临时注册 task_id 到 tasks/manifest.yaml（框架通过 manifest 加载任务）
6. 串行执行每个模型的评测
7. 生成执行摘要
8. 还原 manifest.yaml + 清理临时文件

## 设计说明

- **串行执行**：PinchBench 框架任务循环是串行的
- **临时复制 + manifest 注册**：框架硬编码从 tasks/ 加载用例，且只加载 manifest.yaml 中列出的 task_id；执行后自动清理副本并还原 manifest
- **结果隔离**：每个模型独立目录，便于对比
- **目录结构**：脚本在 `scripts/`，配置模板在 `assets/`，测试在 `tests/`
