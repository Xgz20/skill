---
id: task_it_procurement
name: IT 采购调研
category: 调研
scene: 企业产品情报与业务信息助手
sub_scene: IT 硬件采购
difficulty: L2
capabilities:
- 信息检索与综合
- 数据提取与处理
- 多步推理
- 输出格式适配
- 领域推理
grading_type: llm_judge
timeout_seconds: 300
workspace_files: []
---

## Prompt

一家成长中的初创公司（50 名工程师）需要为新员工采购**开发者笔记本电脑**。帮助他们调研选项并给出推荐。

**需求：**
- 内存最低 32 GB
- SSD 最低 512 GB
- 现代 CPU（最近 2 代以内）
- 良好的做工质量（每日专业使用）
- 预算：每台 $1,500–$2,500
- 需要兼顾 macOS 和 Linux 兼容性（部分开发者各有偏好）

调研至少 5 款具体的笔记本型号，并制定一份采购推荐。对每款型号，记录：

1. **确切的型号名称和配置**（CPU、内存、存储、显示屏）
2. **当前价格**（以及购买渠道——直营、CDW 等）
3. **可维修性与保修**——标准保修时长、延保选项、维修的便利程度
4. **与开发者相关的规格**——键盘质量、接口配置、显示屏质量、电池续航
5. **Linux 兼容性**（针对非 Mac 选项）——WiFi、蓝牙、休眠等方面的已知问题
6. **批量采购选项**——批量折扣、企业/教育定价、车队管理工具

将你的报告保存到 `laptop_procurement.md`。报告应包含：
- 一个对比表格
- 分别针对 macOS 和 Linux 用户的推荐
- 一份 "车队推荐"，为一个 50 人团队建议理想的配置组合
- 估算的总预算

## Expected Behavior

Agent 应当：

1. 调研符合规格的当前笔记本型号
2. 找到带价格的具体配置
3. 检查非 Mac 选项的 Linux 兼容性
4. 考虑企业级/批量采购因素
5. 产出一份实用的采购文档
6. 保存到 `laptop_procurement.md`

## Grading Criteria

- [ ] 创建了 `laptop_procurement.md` 文件
- [ ] 记录了至少 5 款具体的笔记本型号
- [ ] 每款型号都包含价格
- [ ] 规格满足所述需求
- [ ] 针对非 Mac 选项讨论了 Linux 兼容性
- [ ] 包含对比表格
- [ ] 分别给出了 macOS 和 Linux 推荐
- [ ] 带估算总预算的车队推荐
- [ ] 提及了批量采购/企业定价
- [ ] 型号是当前在售的（未停产）

## LLM Judge Rubric

### Criterion 1: Product Research Quality (Weight: 30%)

**Score 1.0**: 给出了带确切配置的具体型号编号（例如 "ThinkPad T14s Gen 5 — AMD Ryzen 7 PRO 8840U, 32GB, 512GB, 14\" 2.8K"）。来自可识别来源的当前定价。所有型号当前均可购买。
**Score 0.75**: 大多数型号具体度良好。少数可能有近似的配置或定价。
**Score 0.5**: 列出了型号，但配置或价格含糊或可能已过时。
**Score 0.25**: 给出了笼统的产品线而无具体配置。
**Score 0.0**: 没有调研具体产品。

### Criterion 2: Practical Procurement Value (Weight: 25%)

**Score 1.0**: 报告对 IT 经理而言可执行。涵盖了车队管理、保修、维修、批量定价和部署方面的考量。包含供应商推荐（直营、CDW、SHI 等）。总预算计算切合实际。
**Score 0.75**: 采购细节良好。在供应商或车队考量方面有少量缺口。
**Score 0.5**: 涉及一些采购关切，但读起来更像消费者评测。
**Score 0.25**: 采购专属内容极少。
**Score 0.0**: 没有采购方面的考量。

### Criterion 3: Linux Compatibility Assessment (Weight: 20%)

**Score 1.0**: 针对每个非 Mac 选项给出了具体的 Linux 兼容性说明。提及了特定发行版的支持（Ubuntu 认证、Fedora 测试）、已知硬件问题和驱动状态。引用了实际的 Linux 硬件数据库或社区报告。
**Score 0.75**: Linux 兼容性覆盖良好，带一些具体细节。
**Score 0.5**: 提及了 Linux 兼容性但缺乏具体内容。诸如 "在 Linux 上运行良好" 之类的笼统陈述。
**Score 0.25**: 几乎没有提及 Linux。
**Score 0.0**: 没有讨论 Linux 兼容性。

### Criterion 4: Fleet Recommendation (Weight: 15%)

**Score 1.0**: 提供了具体的车队组合（例如 "30× MacBook Pro 14\", 20× ThinkPad T14s"），并基于团队构成给出理由。计算了总预算。考虑了标准化的好处与开发者选择权之间的权衡。
**Score 0.75**: 车队推荐良好，带预算估算。推理上有少量缺口。
**Score 0.5**: 笼统的推荐，无具体的车队组合或预算。
**Score 0.25**: 含糊的车队指导。
**Score 0.0**: 没有车队推荐。

### Criterion 5: Comparison Quality (Weight: 10%)

**Score 1.0**: 清晰的对比表格，涵盖规格、价格、操作系统、关键差异点。便于快速决策。
**Score 0.75**: 表格良好，有少量缺口。
**Score 0.5**: 表格存在但不完整。
**Score 0.25**: 表格质量差。
**Score 0.0**: 没有对比表格。

## Additional Notes

- 本任务模拟了初创运营团队经常面对的真实 IT 采购场景。
- 预算区间（$1,500–$2,500）切合实际，应当能够从 Apple、Lenovo、Dell、Framework 等厂商中得出多个可行选项。
- Linux 兼容性是一个有意设置的差异点——一些 Agent 只会罗列规格而不去核实实际的 Linux 支持情况。
- 车队推荐这一组成部分测试 Agent 将单个产品调研综合为整体推荐的能力。
