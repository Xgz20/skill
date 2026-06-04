# 数据库检索、表格整理与数据分析 - 评测维度定义

## 领域概述

数据库检索、表格整理与数据分析场景涵盖CSV分析、数据筛选、统计汇总、数据转换与报表生成等任务，强调计算准确性、数据完整性与规范化输出。

## 常见子场景 (sub_scene)

- `csv_analysis` - CSV分析
- `data_filtering` - 数据筛选
- `statistical_summary` - 统计汇总
- `data_transformation` - 数据转换
- `report_generation` - 报表生成

## 核心能力点 (capabilities)

- `data_parsing` - 数据解析
- `statistical_computation` - 统计计算
- `data_filtering` - 数据筛选
- `tabular_output` - 表格输出
- `aggregation` - 聚合

## 评测重点

### 计算准确性（Automated 优先）
- 统计指标（均值、求和、计数、最值）数值正确
- 聚合分组结果与预期一致
- 排序/筛选条件命中正确行
- 数值精度与四舍五入符合要求

### 数据完整性（Automated）
- 是否处理全部数据行、无遗漏
- 缺失值/异常值处理是否合理
- 列映射与字段对应正确

### 输出格式（Automated）
- 文件创建成功（CSV/Markdown表格/JSON）
- 表头、列对齐、分隔符规范
- 字段类型一致、无格式错乱

### 分析洞察（LLM Judge）
- 是否提炼出有价值的发现
- 趋势/异常解读是否合理
- 结论与数据是否一致

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
  - key: computation_correct
    check_type: automated
    weight: 30
  - key: data_completeness
    check_type: automated
    weight: 20
  - key: table_format
    check_type: automated
    weight: 15
  - key: analysis_insight
    check_type: llm_judge
    weight: 25
```

## 注意事项

- 统计数值必须可程序化复算验证，警惕LLM"心算"误差
- 注意大数据集是否被截断，需检测是否处理全量数据
- 表格格式用automated检查分隔符与列数，洞察交由LLM Judge
