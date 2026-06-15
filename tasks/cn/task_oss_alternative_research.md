---
id: task_oss_alternative_research
name: 开源替代方案调研
category: 调研
scene: 深度搜索与专题研究报告
sub_scene: 开源替代方案对比
difficulty: L3
capabilities:
- 信息检索与综合
- 工具调用
- 自然语言生成
- 输出格式适配
- 多步推理
grading_type: llm_judge
timeout_seconds: 300
workspace_files: []
---

## Prompt

一个创业团队正在为其内部知识库和项目文档寻找 **Notion 的开源替代方案**。出于数据主权的考虑，他们希望自托管（self-host）。

请调研并整理一份报告，覆盖至少 5 个开源替代方案。对每个方案，记录以下内容：

1. **项目名称和 URL**（GitHub/GitLab 仓库链接）
2. **许可证**（MIT、AGPL、Apache 等）
3. **技术栈**（用什么构建的）
4. **部署方式**（Docker、Kubernetes、手动安装）
5. **核心功能**——具体说明它们与 Notion 的对比（块编辑器、数据库、实时协作、API、集成）
6. **社区健康度**——GitHub stars、近期提交活跃度、贡献者数量、发版节奏
7. **局限性**——与 Notion 相比缺少什么、已知的痛点
8. **自托管复杂度**——部署和维护有多难？

将报告保存到 `oss_alternatives.md`。报告应包含：
- 顶部一张汇总对比表
- 每个替代方案的详细介绍
- 一个推荐部分，针对该创业团队的使用场景对各方案排名

## Expected Behavior

Agent 应当：

1. 使用网络搜索找到当前的 Notion 开源替代方案
2. 访问 GitHub/GitLab 仓库以检查社区健康度指标
3. 查阅文档，了解部署和功能细节
4. 整理出一份结构化的对比报告
5. 给出有主见的排名并附理由
6. 保存到 `oss_alternatives.md`

可能的替代方案包括：AppFlowy、AFFiNE、Outline、BookStack、Wiki.js、Docmost、Trilium Notes、Focalboard 等。

## Grading Criteria

- [ ] 创建了文件 `oss_alternatives.md`
- [ ] 记录了至少 5 个替代方案
- [ ] 每个替代方案都有许可证信息
- [ ] 提供了 GitHub/GitLab URL
- [ ] 描述了部署方式
- [ ] 与 Notion 做了功能对比
- [ ] 包含社区健康度指标
- [ ] 为每个方案注明了局限性
- [ ] 存在对比表
- [ ] 有带排名的推荐

## LLM Judge Rubric

### Criterion 1: Research Quality (Weight: 30%)

**Score 1.0**：报告包含具体、可核实的细节——精确的 GitHub star 数、近期发版日期、具体版本号、来自实际文档的具体功能列表。信息明显来自查阅实际仓库和文档，而非仅凭一般性知识。
**Score 0.75**：大部分替代方案有良好的具体细节。少数条目可能依赖一般性知识。
**Score 0.5**：具体信息与泛泛信息混杂。部分方案调研充分，其他则浮于表面。
**Score 0.25**：大多是泛泛的描述，没有明显的调研证据。
**Score 0.0**：报告缺失，或包含明显不准确的信息。

### Criterion 2: Practical Usefulness (Weight: 25%)

**Score 1.0**：报告能真正帮助一个创业团队做决策。包含自托管复杂度评估、迁移考量，以及对每个工具是否真能替代 Notion 关键功能的诚实评价。推荐针对所述使用场景（创业团队、知识库、数据主权）量身定制。
**Score 0.75**：大体有用，有良好的实用细节，但某些方面缺乏针对性。
**Score 0.5**：提供了信息，但没有强有力地回应该创业团队的具体需求。
**Score 0.25**：泛泛的概述，无助于实际决策。
**Score 0.0**：对决策没有用处。

### Criterion 3: Coverage Breadth (Weight: 20%)

**Score 1.0**：覆盖 5 个以上替代方案，每个都记录了全部 8 个要求的维度。包含成熟方案与新兴方案的组合。没有遗漏主要的知名替代方案。
**Score 0.75**：5 个以上替代方案，覆盖了大部分维度。有一两处缺口。
**Score 0.5**：4-5 个替代方案，各维度覆盖不一致。
**Score 0.25**：少于 4 个替代方案，或覆盖非常单薄。
**Score 0.0**：记录的替代方案少于 2 个。

### Criterion 4: Comparison Table and Structure (Weight: 15%)

**Score 1.0**：清晰的对比表，含关键维度（许可证、stars、核心功能、自托管难度、与 Notion 的对等程度）。报告组织良好，每个替代方案有一致的章节结构。便于扫读。
**Score 0.75**：表格和结构良好，仅有少量缺口。
**Score 0.5**：存在表格或结构，但不完整。
**Score 0.25**：组织混乱。
**Score 0.0**：没有表格，没有结构。

### Criterion 5: Honest Assessment of Limitations (Weight: 10%)

**Score 1.0**：每个替代方案都有诚实、具体的局限性部分。不过度吹捧任何方案。注明来自社区反馈的真实痛点或文档缺口。承认没有任何开源方案能完全替代 Notion。
**Score 0.75**：大部分替代方案注明了局限性，并有一定的针对性。
**Score 0.5**：提到了局限性，但流于泛泛（"功能比 Notion 少"）。
**Score 0.25**：几乎没有触及局限性。
**Score 0.0**：没有讨论局限性——读起来像营销文案。

## Additional Notes

- 选择 Notion 替代方案，是因为这是一个常见的真实调研任务，且其格局变化频繁。
- 自托管要求增加了一个实用的筛选条件，用以测试 Agent 是否真的去查阅了部署文档。
- 社区健康度指标（stars、提交、贡献者）需要访问实际的 GitHub/GitLab 仓库。
- 这个任务测试 Agent 为特定决策者画像产出可付诸行动的调研的能力。
