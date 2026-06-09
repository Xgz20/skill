---
name: pinchbench-case-generator
description: 根据用户Query自动生成高质量PinchBench评测用例，通过多Agent协作保证生成质量
metadata:
  version: "1.0.0"
  author: astronclaw
---

# PinchBench 评测用例生成器

自动将用户真实Query转换为符合PinchBench格式的评测用例，通过6阶段workflow生成引擎和对抗式质检保证质量。

## 何时使用

- 用户输入真实场景的Query，需要转换为评测用例
- 需要批量生成评测用例覆盖特定领域
- 想要基于真实使用场景扩充评测集

## 生成流程

1. **语言识别**：自动检测Query语言（中文/英文）
2. **场景识别**：识别业务场景（finance/research/coding等）
3. **Workflow生成**：6阶段多Agent协作生成用例
   - 需求分析
   - 多方案生成（judge-panel模式）
   - 评分择优
   - 评分逻辑生成
   - 对抗式质检
   - 最终组装
4. **序号分配**：自动分配task_NNNN前缀
5. **文件输出**：写入output/generated_cases/

## 输出格式

生成的评测用例符合PinchBench标准格式：
- 元数据字段：英文 + YAML数组
- 章节标题：英文（框架要求）
- 正文内容：根据Query语言（中文Query→中文内容）
- 来源标识：source: astronclaw
- **难度等级**：difficulty 字段（L1-L4），由 LLM 判定 + 规则推算双重校验，
  不一致时以规则为准。规则按预估步数和工具数取较高者对应等级。
- **混合评分权重**：grading_type 为 hybrid 时，自动输出 grading_weights
  （automated / llm_judge 比例），由各评分维度的 weight 总和归一化推算。
  若不输出此字段，框架会回退到 50/50 默认，可能与维度实际占比不符。

### 难度等级 (difficulty)

L1-L4 四级体系，由步数和工具数双维度量化：

| 等级 | 定义 | 量化参考 | 典型场景 |
|------|------|----------|----------|
| L1 | 单步执行，单工具调用 | 1-3 步，1 个工具 | 文件读取、简单查询 |
| L2 | 多步推理，工具组合 | 4-10 步，2-3 个工具 | 数据分析、日志提取 |
| L3 | 复杂规划，跨领域 | 10-30 步，多工具链 | 代码重构、深度研究 |
| L4 | 长程任务，跨系统/多Agent | 30+ 步，跨会话 | 端到端项目、多Agent协作 |

- 识别方式：LLM 结合场景判定难度并给出 estimated_steps/estimated_tools，
  workflow 用规则独立推算，两者不一致时 log 警告并以规则为准（避免低估）。
- timeout 校验：difficulty 与 timeout_seconds 的合理区间一致性校验
  （L1:60-180s / L2:120-300s / L3:180-600s / L4:300-600s），越界时 log 提示人工复核。
- 框架说明：difficulty 为纯标注元数据，框架不用于评分，但会完整保留在
  task.frontmatter 中，可供筛选、分析与报表使用。

## 质量保证

- **多方案生成**：3个视角独立生成草稿（严格评分、覆盖度、真实场景）
- **评分择优**：独立评委打分选最优
- **对抗式质检**：4个critic挑错（Prompt歧义、Python可执行性、覆盖度、边界情况）
- **质量报告**：输出时附带质量评分和问题列表

## 支持的场景

1. 金融投研与企业价值评估 (finance_investment_research)
2. 深度搜索与专题研究报告 (deep_research_report)
3. 科学技术、医学与计算问答 (science_tech_medical_qa)
4. 数据库检索、表格整理与数据分析 (data_retrieval_analysis)
5. 内容创作、PPT、网页与多媒体生成 (content_creation_multimedia)
6. 企业产品情报与业务信息助手 (enterprise_product_intel)
7. Skill发现、创建、安装与调用 (skill_lifecycle)
8. 本地环境、命令执行与脚本任务 (local_env_scripting)

## 架构组成

- **生成引擎**：workflows/case-generation-pipeline.js（6阶段workflow）
- **领域知识**：domains/目录下8个场景定义文件
- **序号分配**：scripts/assemble.py扫描现有文件自动分配
- **格式组装**：scripts/assemble.py渲染YAML frontmatter并组装md
- **Python验证**：scripts/validate_python.py 确定性语法验证器
  （用 py_compile 在系统临时目录验证，with 退出时自动清理，绝不污染项目根）
  workflow 子 Agent 通过 stdin 管道调用此脚本，不再自行创建临时文件
- **组装入口**：`python scripts/assemble.py <workflow_result.json>`
  自动定位项目根（向上查找 scripts/lib_grading.py + tasks/ 标志），
  统一输出到项目根 output/generated_cases/，并在质检发现严重问题时
  生成同名 *_REPORT.md 质量报告便于后续分析优化。

## 后续步骤

生成后的用例保存在 output/generated_cases/，审核通过后可迁移到 tasks/ 并更新 manifest.yaml：

1. 审核用例内容
2. 迁移到 tasks/ 目录
3. 更新 manifest.yaml，将用例 ID 加到对应 category

## 注意事项

- 生成的用例md文件需要人工审核后再正式使用
- 质检标记needs_review的用例建议仔细检查
- Python代码虽经语法验证，建议实际运行测试
- 中文Query生成的中文内容可能需要润色
- 元数据字段和章节标题保持英文（框架要求），正文内容跟随Query语言
