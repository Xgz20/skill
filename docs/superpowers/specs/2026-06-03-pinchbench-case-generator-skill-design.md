# PinchBench 评测用例生成 Skill 设计文档

> 版本：v1.0
> 日期：2026-06-03
> 状态：设计待评审

## 1. 背景与目标

### 1.1 背景

PinchBench 通过一组评测任务（`tasks/task_*.md`）衡量 LLM 作为 OpenClaw Agent 大脑的表现。评测用例的质量和覆盖度直接决定评测的有效性。当前评测用例需人工编写，效率低、覆盖面有限。

### 1.2 目标

沉淀一个 **评测用例生成 Skill**，将「用户真实 Query → PinchBench 评测用例」的转换过程自动化：

- 输入：用户实际使用 OpenClaw 时的真实 Query
- 输出：符合 PinchBench 格式的评测用例 `.md` 文件
- 核心诉求：**在保证生成质量的前提下，尽可能减少人工投入成本**

## 2. 核心设计决策

| 决策点 | 选择 | 说明 |
|--------|------|------|
| 使用方式 | 简单 Query 直接生成 / 复杂 Query 先澄清 | 关键信息无法推断时才触发人工澄清 |
| 评分策略 | 默认 `hybrid` | automated 验证结构 + llm_judge 评质量 |
| Skill 架构 | 单一通用 Skill + 可挂载领域维度文件 | 主流程通用，领域知识按需加载 |
| 质量保证 | 多 Agent 对抗式质检 | 替代人工确认评分维度，自动拦截低质量用例 |
| 生成引擎 | 多 Agent workflow 编排 | 6 阶段 pipeline |
| 存放位置 | `output/generated_cases/` | 不污染 git，审核后迁入 `tasks/` |
| 命名规则 | `task_<4位序号>_<semantic_name>.md` | 序号由 Skill 自动分配 |
| 来源标识 | `source: astronclaw` | 区分自建与开源用例 |

## 3. 评测用例文件格式

### 3.1 元数据规范（frontmatter）

所有元数据字段使用**英文**，多值字段使用 **YAML 数组格式**：

```yaml
---
id: task_0001_stock_price_lookup
name: Stock Price Lookup
category: research                          # 技术维度（沿用现有 PinchBench 分类）
scene: finance_investment_research          # 业务场景（英文枚举）
sub_scene: realtime_quote_lookup            # 子场景（英文）
source: astronclaw                          # 来源标识
grading_type: hybrid                         # automated | llm_judge | hybrid
timeout_seconds: 180
capabilities:                                # 核心能力（YAML 数组）
  - instruction_following
  - realtime_data_retrieval
  - tool_use
workspace_files: []
---
```

### 3.2 业务场景枚举（scene）

8 大业务场景（英文枚举值，可扩展）：

| 中文场景 | scene 英文枚举 |
|----------|----------------|
| 金融投研与企业价值评估 | `finance_investment_research` |
| 深度搜索与专题研究报告 | `deep_research_report` |
| 科学技术、医学与计算问答 | `science_tech_medical_qa` |
| 数据库检索、表格整理与数据分析 | `data_retrieval_analysis` |
| 内容创作、PPT、网页与多媒体生成 | `content_creation_multimedia` |
| 企业产品情报与业务信息助手 | `enterprise_product_intel` |
| Skill 发现、创建、安装与调用 | `skill_lifecycle` |
| 本地环境、命令执行与脚本任务 | `local_env_scripting` |

### 3.3 正文章节（必须保持英文标题）

以下章节标题**必须保持英文**（改中文会破坏框架解析，见 `lib_tasks.py` 的 `_parse_sections`）：

```markdown
## Prompt
## Expected Behavior
## Grading Criteria
## Automated Checks
## LLM Judge Rubric
```

**标题下的正文内容**根据 Query 语言决定：

- Query 是英文 → 正文内容英文
- Query 是中文 → 正文内容**必须中文**（注释、说明、rubric 描述都用中文）

## 4. 语言适配规则

| 输入 Query 语言 | 用例 md 正文内容 | 框架章节标题 | 元数据字段 |
|-----------------|------------------|--------------|------------|
| 英文 | 英文 | 英文（固定） | 英文（固定） |
| 中文 | **中文** | 英文（固定） | 英文（固定） |

Skill 自身的内容（SKILL.md、说明文档）**必须为中文**。

## 5. Skill 架构

```
skills/pinchbench-case-generator/
├── SKILL.md                          # Skill 入口（中文）
├── workflows/
│   └── case-generation-pipeline.js   # 多 Agent 编排脚本
├── domains/                          # 领域维度定义文件（按需加载）
│   ├── finance_investment_research.md
│   ├── deep_research_report.md
│   ├── science_tech_medical_qa.md
│   ├── data_retrieval_analysis.md
│   ├── content_creation_multimedia.md
│   ├── enterprise_product_intel.md
│   ├── skill_lifecycle.md
│   └── local_env_scripting.md
└── lib/
    └── assemble.py                   # 序号分配 + md 文件组装写入
```

### 5.1 职责划分

- **SKILL.md**：定义触发条件、使用流程、调用 workflow 的方式
- **workflow 脚本**：6 阶段多 Agent 生成引擎（核心）
- **domains/**：每个领域一个维度定义文件，描述该领域的评测重点、常见能力点、评分参考
- **lib/assemble.py**：在 workflow 返回结构化结果后，分配序号、组装 md、写入文件

## 6. Workflow 生成引擎（6 阶段）

### 阶段 1：需求分析（Analyze）

单 Agent 解析 Query，识别 `scene` / `sub_scene` / `category` / `grading_type` / `capabilities` / `suggested_timeout`。Skill 外层先识别 `scene` 并将对应领域维度文件内容作为 `args.domainContext` 透传给 workflow，阶段 1 据此细化分析。

> 澄清逻辑放在 Skill 外层（见第 7 节），不在 workflow 内。workflow 假设输入完整。
>
> 注：scene 的初判在外层完成（决定加载哪个领域文件），阶段 1 在领域上下文加持下做最终确认与细化（sub_scene、capabilities 等）。

### 阶段 2：多方案生成（Generate，judge-panel）

3 个 Agent 从不同视角并行生成完整草稿（`parallel` barrier 必要）：

- **严格评分视角**：可验证性优先，评分标准明确无歧义
- **覆盖度视角**：边界情况与失败模式优先
- **真实场景视角**：贴近真实用户使用场景

### 阶段 3：评分择优（Judge）

并行评委对每份草稿打分（0-10），按 Prompt 清晰度、评分标准合理性、真实性、完整性四维度评分。选最高分草稿，收集各草稿亮点。

### 阶段 4：评分逻辑生成（Refine，pipeline）

按 `grading_type` 生成评分逻辑（两阶段 pipeline：生成 → 验证修复）：

- `automated` 维度 → 生成 Python `grade()` 函数，做语法/库依赖验证
- `llm_judge` 维度 → 生成 5 档评分 rubric，做权重总和=100% 校验（纯 JS 逻辑）

### 阶段 5：对抗式质检（Verify，pipeline）

多个 critic 独立挑错（无 barrier，pipeline）：

- **Prompt 歧义检查**：默认假设有问题，找出歧义与缺失信息
- **Python 可执行性**：检查库依赖、异常处理、维度覆盖
- **评分标准覆盖度**：核心能力是否都有对应维度
- **边界情况覆盖**：列举失败模式，检查标准能否识别

按 severity（critical/moderate/minor）分级。存在 critical 问题则标记 `needs_review`。

### 阶段 6：最终组装（Assemble）

workflow 返回结构化结果（frontmatter 字段 + 各章节内容 + 质量报告）。**id 字段留空**，由 Skill 外层分配序号后填充。

## 7. Skill 外层逻辑

1. **语言识别**：检测 Query 语言（zh/en）
2. **澄清判断**：若 Query 关键信息缺失，先用 AskUserQuestion 澄清（唯一人工触点）
3. **调用 workflow**：传入 `{ query, language, domainFile }`
4. **序号分配**：扫描 `output/generated_cases/` 和 `tasks/` 中 `task_(\d{4})_` 最大值 +1
5. **文件写入**：组装 md，写入 `output/generated_cases/task_<seq>_<name>.md`
6. **质检结果处理**：
   - 质检通过 → 正常输出
   - 存在 critical 问题 → 仍输出，但标记需人工审查，附质检报告

## 8. 关键技术约束

| 约束 | 说明 |
|------|------|
| 子目录不可用 | `lib_tasks.py` 用 `tasks_dir / f"{id}.md"` 与 `glob("task_*.md")`，不支持 `tasks/astron/` 子目录，故用数字前缀命名 |
| 序号外置分配 | workflow 脚本内 `Date.now()` 不可用，序号在 workflow 返回后由 Skill 分配 |
| 结构化输出 | 所有 agent 调用使用 JSON Schema 强制输出，避免解析错误 |
| pipeline 优先 | 默认用 `pipeline()`，仅在需要全部结果时用 `parallel()` barrier |
| 标准库限制 | Automated Checks 的 Python 代码只能用 stdlib（pathlib/re/json/datetime） |

## 9. 验收标准

- [ ] 输入英文 Query，生成英文用例；输入中文 Query，生成中文正文用例
- [ ] 生成的 md 通过 `lib_tasks.py` 的 `load_task` 正常解析
- [ ] 元数据字段全英文 + YAML 数组格式
- [ ] 框架章节标题保持英文
- [ ] 自动分配的序号无冲突
- [ ] `source: astronclaw` 标识正确
- [ ] hybrid 用例同时包含可运行的 Automated Checks 和权重和=100% 的 Rubric
- [ ] 对抗式质检能识别明显缺陷并标记 `needs_review`
- [ ] 简单 Query 全自动生成，无需人工干预
- [ ] 复杂/模糊 Query 触发澄清问题

## 10. 后续扩展

- `--source astronclaw` 脚本选项：仅执行自建评测集
- 批量生成：一次输入多条 Query
- 新增 scene：只需新增一个 `domains/<scene>.md` 文件
- workspace_files 自动生成：为需要输入文件的用例自动准备 fixture
