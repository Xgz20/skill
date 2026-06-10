# 金融投研与企业价值评估 - 评测维度定义

## 领域概述

金融投研与企业价值评估场景涵盖实时行情查询、财务数据分析、投资研究报告生成等任务。

## 常见子场景 (sub_scene)

- `realtime_quote_lookup` - 实时行情查询
- `financial_report_generation` - 财务报告生成
- `stock_trend_analysis` - 股票趋势分析
- `market_summary_report` - 市场汇总报告
- `valuation_calculation` - 估值计算

## 核心能力点 (capabilities)

> 以下为本领域常见涉及的 Agent 能力，均来自 `references/agent-capability-dimensions.md` 标准清单。
> 生成用例时从中选取该任务真正考察的 3-5 个（也可按需选用清单内其他标签）。

- `information_retrieval` - 信息检索与综合（实时行情/财报数据获取，含时效性判断）
- `data_extraction` - 数据提取与处理（财务数据解析、指标提取）
- `multi_step_reasoning` - 多步推理（估值计算、趋势分析的数值逻辑链）
- `domain_reasoning` - 领域推理（金融术语、估值方法、风险逻辑的专业运用）
- `hallucination_resistance` - 幻觉抑制（数据准确、可溯源、拒绝编造行情）
- `output_format` - 输出格式适配（表格、结构化报告）

## 评测重点

### 数据准确性（Automated 优先）
- 股票代码/ticker正确
- 价格数值精度
- 日期时间准确性
- 单位一致性（元/美元、股/手）

### 时效性（Hybrid）
- 是否使用web search获取最新数据
- 数据时间戳是否当天/近期
- 避免使用过时的知识库数据

### 结构化输出（Automated）
- 文件创建成功
- 包含必要字段（价格、日期、来源）
- 格式规范（JSON/CSV/Markdown表格）

### 分析质量（LLM Judge）
- 市场分析是否有洞察
- 趋势判断是否合理
- 风险提示是否充分

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
  - key: file_created
    check_type: automated
    weight: 10
  - key: ticker_correct
    check_type: automated
    weight: 15
  - key: price_present
    check_type: automated
    weight: 15
  - key: data_timeliness
    check_type: hybrid
    weight: 20
  - key: analysis_quality
    check_type: llm_judge
    weight: 25
  - key: structure_clarity
    check_type: llm_judge
    weight: 15
```

## 注意事项

- 金融数据时效性极强，优先检测是否使用web search
- 数字精度要求高，automated checks需验证格式
- 避免幻觉：价格、市值等数值必须来自真实数据源
