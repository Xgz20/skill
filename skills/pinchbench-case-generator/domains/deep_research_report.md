# 深度搜索与专题研究报告 - 评测维度定义

## 领域概述

深度搜索与专题研究报告场景涵盖行业周报、竞品分析、专题研究、资讯聚合与趋势预测等任务，强调多源信息检索、综合归纳与结构化输出。

## 常见子场景 (sub_scene)

- `industry_weekly_report` - 行业周报
- `competitor_analysis` - 竞品分析
- `topic_research` - 专题研究
- `news_aggregation` - 资讯聚合
- `trend_forecast` - 趋势预测

## 核心能力点 (capabilities)

- `multi_source_research` - 多源研究
- `information_synthesis` - 信息综合
- `source_verification` - 来源验证
- `structured_report` - 结构化报告
- `citation_management` - 引用管理

## 评测重点

### 信息覆盖度（Automated 优先）
- 是否覆盖任务要求的所有主题/子话题
- 关键实体（公司、产品、事件）是否齐全
- 是否遗漏明确指定的检索维度

### 来源可信度（Hybrid）
- 是否引用权威来源（官方、主流媒体、研报）
- 引用链接是否真实有效
- 来源数量是否充分、是否多源交叉验证

### 报告结构（Automated）
- 文件创建成功
- 章节组织清晰（摘要、正文、结论、参考来源）
- 引用格式规范、可追溯

### 内容深度（LLM Judge）
- 分析是否超越简单罗列、有洞察
- 是否提炼趋势与因果逻辑
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
  - key: report_created
    check_type: automated
    weight: 10
  - key: topic_coverage
    check_type: automated
    weight: 20
  - key: source_validity
    check_type: hybrid
    weight: 20
  - key: citation_format
    check_type: automated
    weight: 10
  - key: content_depth
    check_type: llm_judge
    weight: 25
  - key: structure_clarity
    check_type: llm_judge
    weight: 15
```

## 注意事项

- 优先检测是否真正调用web search获取多源信息，而非凭记忆作答
- 引用链接需校验真实性，警惕幻觉式来源
- 覆盖度可用关键词命中做automated检查，深度判断交由LLM Judge
