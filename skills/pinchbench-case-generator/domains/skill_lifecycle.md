# Skill 发现、创建、安装与调用 - 评测维度定义

## 领域概述

Skill 发现、创建、安装与调用场景涵盖Skill发现、安装、调用、创建与搜索等任务，强调工具调用正确性、多步工作流编排与错误处理。

## 常见子场景 (sub_scene)

- `skill_discovery` - Skill发现
- `skill_installation` - Skill安装
- `skill_invocation` - Skill调用
- `skill_creation` - Skill创建
- `skill_search` - Skill搜索

## 核心能力点 (capabilities)

- `tool_use` - 工具调用
- `instruction_following` - 指令遵循
- `multi_step_workflow` - 多步工作流
- `error_handling` - 错误处理
- `skill_comprehension` - Skill理解

## 评测重点

### 工具调用正确性（Automated 优先）
- transcript中是否出现预期的工具调用
- 工具参数是否正确（Skill名称、路径、参数）
- 调用顺序是否符合工作流要求

### 流程完整性（Automated）
- 是否完成发现→安装→调用全链路
- 是否遗漏关键步骤
- 中间产物（配置、文件）是否生成

### 错误处理（Hybrid）
- 遇到失败是否有重试/回退
- 是否正确解读错误信息
- 是否避免在错误状态下继续

### 任务完成度（LLM Judge）
- 最终目标是否达成
- Skill是否被正确理解并应用
- 结果是否满足用户意图

## 典型评分维度示例

> **说明**：下面的 `grading_dimensions` 是「概念评分维度」，用于指导用例设计。
> 每个维度的 `check_type` 取值为：
> - `automated`：可程序化验证（如文件存在、数值精度、格式规范）
> - `llm_judge`：需 LLM 主观评判（如内容质量、分析深度、创意性）
> - `hybrid`：需自动化检测与 LLM 判断结合（如时效性：自动检测是否调用 web search + LLM 判断数据新鲜度）
>
> 在最终生成的任务文件中，这些维度会被归并为 harness 级别的 `grading_type`
> （`automated` / `llm_judge` / `hybrid`）以及对应的 Automated Checks 代码和 LLM Judge Rubric。

```yaml
grading_dimensions:
  - key: tool_call_present
    check_type: automated
    weight: 25
  - key: tool_params_correct
    check_type: automated
    weight: 20
  - key: workflow_completeness
    check_type: automated
    weight: 20
  - key: error_handling
    check_type: hybrid
    weight: 15
  - key: task_completion
    check_type: llm_judge
    weight: 20
```

## 注意事项

- 核心检测点在transcript中的工具调用记录，需automated解析调用与参数
- 多步工作流需校验步骤顺序与中间产物，而非仅看最终输出
- 任务完成度判断交由LLM Judge，结合工具调用证据综合评分
