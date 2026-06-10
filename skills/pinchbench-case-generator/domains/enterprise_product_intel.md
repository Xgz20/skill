# 企业产品情报与业务信息助手 - 评测维度定义

## 领域概述

企业产品情报与业务信息助手场景涵盖产品查询、竞品情报、定价研究、市场定位与业务问答等任务，强调信息准确性、覆盖度与时效性。

## 常见子场景 (sub_scene)

- `product_lookup` - 产品查询
- `competitor_intel` - 竞品情报
- `pricing_research` - 定价研究
- `market_positioning` - 市场定位
- `business_qa` - 业务问答

## 核心能力点 (capabilities)

> 以下为本领域常见涉及的 Agent 能力，均来自 `references/agent-capability-dimensions.md` 标准清单。
> 生成用例时从中选取该任务真正考察的 3-5 个（也可按需选用清单内其他标签）。

- `information_retrieval` - 信息检索与综合（产品/竞品/定价信息收集与甄别）
- `data_extraction` - 数据提取与处理（从网页/文档提取规格、价格等结构化信息）
- `multi_step_reasoning` - 多步推理（竞争分析、市场定位判断）
- `hallucination_resistance` - 幻觉抑制（实体准确、价格可溯源、防张冠李戴）
- `output_format` - 输出格式适配（对比表格、结构化输出）

## 评测重点

### 信息准确性（Automated 优先）
- 产品名称、型号、规格正确
- 价格/套餐信息精确
- 公司/品牌实体无张冠李戴

### 覆盖度（Automated）
- 是否涵盖任务指定的关键竞品/产品
- 对比维度是否齐全（价格、功能、定位）
- 是否遗漏明确要求的条目

### 时效性（Hybrid）
- 是否使用web search获取最新产品/定价信息
- 数据是否为近期、避免过时信息
- 是否标注信息时间与来源

### 分析质量（LLM Judge）
- 竞争分析是否有洞察
- 市场定位判断是否合理
- 结论是否有据可依

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
  - key: output_created
    check_type: automated
    weight: 10
  - key: info_accuracy
    check_type: automated
    weight: 25
  - key: coverage_completeness
    check_type: automated
    weight: 20
  - key: data_timeliness
    check_type: hybrid
    weight: 20
  - key: analysis_quality
    check_type: llm_judge
    weight: 25
```

## 注意事项

- 产品/定价信息时效性强，优先检测是否调用web search
- 覆盖度可用关键竞品/产品关键词命中做automated检查
- 警惕实体混淆与价格幻觉，数值需可溯源
