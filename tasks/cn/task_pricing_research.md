---
id: task_pricing_research
name: 供应商定价对比
category: 调研
scene: 深度搜索与专题研究报告
sub_scene: 供应商定价对比
difficulty: L3
capabilities:
- 信息检索与综合
- 自然语言生成
- 领域推理
- 输出格式适配
- 多步推理
grading_type: llm_judge
timeout_seconds: 300
workspace_files: []
---

## Prompt

你的团队需要为一个生产应用选择一项**托管 PostgreSQL 数据库服务**。请对比以下供应商的定价：

1. **AWS RDS for PostgreSQL**
2. **Google Cloud SQL for PostgreSQL**
3. **Azure Database for PostgreSQL**
4. **DigitalOcean Managed Databases**
5. **Neon**（serverless Postgres）

为进行标准化对比，请为两种配置报价：

**Config A（小型）：** 2 vCPUs、8 GB RAM、100 GB 存储、单可用区
**Config B（生产级）：** 4 vCPUs、16 GB RAM、500 GB 存储、高可用（multi-AZ/副本）

对于每个供应商，请记录：
- Config A 和 Config B 的预估月成本
- 包含哪些内容（备份、监控、连接池）
- 定价模式（按小时、按月、serverless/按用量）
- 隐藏成本（数据传输、IOPS、备份存储等）
- 免费额度或试用可用性

将你的分析保存到 `pricing_comparison.md`。请包含：
- 顶部的定价对比表
- 每个供应商的详细拆解
- 标明隐藏成本的总拥有成本分析
- 带推理依据的推荐建议

## Expected Behavior

Agent 应当：

1. 从各供应商的定价页面调研当前定价
2. 将两种配置映射到最接近的可用实例类型
3. 计算包含相关附加项的月成本
4. 识别隐藏或容易被忽视的成本
5. 创建一份结构化的对比文档
6. 保存到 `pricing_comparison.md`

## Grading Criteria

- [ ] 创建了文件 `pricing_comparison.md`
- [ ] 覆盖全部 5 个供应商
- [ ] 为每个供应商预估了 Config A 定价
- [ ] 为每个供应商预估了 Config B 定价
- [ ] 识别出隐藏成本
- [ ] 包含定价表
- [ ] 提及实例类型/SKU
- [ ] 包含免费额度信息
- [ ] 带推理依据的推荐建议
- [ ] 价格看起来合理且当前

## LLM Judge Rubric

### Criterion 1: Pricing Accuracy (Weight: 30%)

**Score 1.0**：月成本预估具体（美元金额）且与当前市场行情大致相符。命名了实例类型或 SKU。预估考虑了计算、存储和 I/O。明显来源于定价页面。
**Score 0.75**：预估合理且命名了实例类型。有小的不准确或缺少某些成本组成部分。
**Score 0.5**：预估在正确的数量级，但缺乏具体性。没有实例类型的通用定价。
**Score 0.25**：预估模糊或定价明显过时。
**Score 0.0**：没有定价信息，或预估严重不准确。

### Criterion 2: Hidden Cost Analysis (Weight: 25%)

**Score 1.0**：识别出供应商特有的隐藏成本——数据传出流量、IOPS 费用、超出免费额度的备份保留、连接数限制、监控附加项、跨区域复制成本。至少对其中一些进行了量化。
**Score 0.75**：识别出若干隐藏成本并进行了部分量化。
**Score 0.5**：提到存在隐藏成本，但没有量化或表述模糊。
**Score 0.25**：几乎没有触及额外成本。
**Score 0.0**：没有讨论隐藏成本。

### Criterion 3: Comparison Completeness (Weight: 20%)

**Score 1.0**：为全部 5 个供应商都对两种配置报了价。包含哪些是捆绑的（备份、监控、HA）以及哪些需额外付费。免费额度细节准确。定价模式解释清晰。
**Score 0.75**：为大多数供应商对两种配置报了价。捆绑功能或免费额度信息有小缺口。
**Score 0.5**：一种配置覆盖良好，另一种较单薄。或全部供应商都覆盖但很表面。
**Score 0.25**：覆盖范围有明显缺口。
**Score 0.0**：覆盖少于 3 个供应商，或没有针对配置的具体定价。

### Criterion 4: Presentation and Usability (Weight: 15%)

**Score 1.0**：整洁的对比表让人一目了然。详细拆解组织一致。在真实的采购决策中会很有用。
**Score 0.75**：表格和组织良好。有小的格式问题。
**Score 0.5**：信息存在但难以跨供应商对比。
**Score 0.25**：组织混乱。
**Score 0.0**：没有对比结构。

### Criterion 5: Recommendation Quality (Weight: 10%)

**Score 1.0**：推荐建议考虑了总拥有成本，而不仅是标价。按使用场景区分（初创公司 vs 企业）。承认权衡（价格 vs 功能 vs 运维简便性）。
**Score 0.75**：推荐建议合理且有依据。在细致程度上有小缺口。
**Score 0.5**：通用推荐，缺乏有力依据。
**Score 0.25**：推荐模糊或缺乏支撑。
**Score 0.0**：没有推荐建议。

## Additional Notes

- 选择托管 PostgreSQL 是因为全部 5 个供应商都公开提供定价，且市场竞争充分，足以产生有意思的对比。
- Neon（serverless）的定价模式与其他供应商根本不同，这测试了 Agent 对不同类型事物进行对比的能力。
- 定价频繁变动——关键在于预估处于正确的范围，且 Agent 明显尝试使用了当前数据。
- 本任务对测试网络搜索能力尤其有用，因为训练数据中的定价可能已过时。
