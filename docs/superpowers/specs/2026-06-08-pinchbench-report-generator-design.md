# PinchBench 评测报告生成 Skill 设计文档

> **设计日期**: 2026-06-08  
> **版本**: 1.0  
> **目标**: 自动分析 AstronClaw 在 PinchBench 评测框架上的执行结果，生成类似 `comparison_four_models_report.md` 的评测报告

## 一、设计目标

构建一个 **pinchbench-report-generator** Skill，支持：

1. **标准化报告生成**：固定结构、多模型对比，适合发布分享
2. **快速问题分析**：灵活定制，针对特定模型、任务类别深入分析
3. **目标模型深度分析**：详尽分析指定目标模型的优劣势，低分任务需列出评分标准（中文）及详细失分点
4. **单/多模型自适应**：输入单模型时降级为单模型报告，多模型时生成完整对比

## 二、整体架构

### 2.1 三阶段流水线

```
输入：评测结果目录（总目录 或 多个模型目录）+ --target-model
  │
  ├─ 阶段1  collect (Python)
  │    扫描目录 → 识别模型目录（含 *.json + *_transcripts/）
  │    读所有结果 JSON → 算得分率/排名/分类别得分/Token统计
  │    筛选"需深度分析任务"：① 相对短板 ② 全员低分（单模型时回退绝对阈值）
  │    输出 collected_data.json（结构化中间数据）
  │
  ├─ 阶段2  analyze (LLM)
  │    读 collected_data.json + 低分任务 transcripts + 任务md(评分标准)
  │    + agent-capability-dimensions.md
  │    产出 analysis.json：Agent能力归类 / 失分点深度分析 / 改进建议
  │
  └─ 阶段3  render (Python)
       Python算的表格 + LLM写的分析章节 → 按示例结构拼装最终 md
       默认输出到输入目录，--output 可覆盖
```

### 2.2 职责边界

- **Python**：所有数字计算（表格、排名、统计）、目录扫描、JSON 解析、模板拼装 → 保证绝对准确
- **LLM**：Agent 能力归类、失分点语义分析、根本原因推断、改进建议撰写 → 深度理解 transcripts

### 2.3 Skill 文件结构

```
skill/skills/pinchbench-report-generator/
├── SKILL.md                        # Skill 说明 + LLM 在阶段2的工作指引
├── agent-capability-dimensions.md  # Agent 能力维度定义（从 docs/ 复制作为静态资源）
├── result_collector.py             # 阶段1：目录扫描、模型识别、数据收集
├── score_calculator.py             # 得分率、分类别、排名、Token 效率计算
├── task_filter.py                  # 低分任务筛选（相对短板 + 全员低分 + 绝对阈值回退）
├── report_renderer.py              # 阶段3：模板拼装
├── report_cli.py                   # CLI 入口（collect / render 两个子命令）
├── test_result_collector.py        # 单元测试
├── test_score_calculator.py
├── test_task_filter.py
└── test_report_renderer.py
```

## 三、阶段1：数据收集（collect）

### 3.1 模型目录识别

**方案**：按内容识别（不依赖目录命名规则）

- 递归扫描输入路径
- 识别条件：同时包含 `*.json` 结果文件和 `*_transcripts/` 目录
- 模型展示名：优先从 JSON 的 `"model"` 字段读取，目录名作为内部 key
- 输入总目录 → 自动发现所有模型目录
- 输入多个具体目录 → 只收集这些
- 单一模型 → 触发降级模式

### 3.2 数据提取

从每个结果 JSON 提取：

**模型级**：
- `model`（模型名）
- `benchmark_version`、`suite`
- 总 Token（所有任务累加）
- 总请求数
- 任务列表

**任务级**：
- `task_id`、`category`、`status`、`timed_out`、`execution_time`
- `usage`: `input_tokens`, `output_tokens`, `total_tokens`, `request_count`
- `grading.mean`（任务得分）
- `grading.runs[].breakdown`（细分项得分）
- `grading.runs[].notes`（评语）
- `frontmatter`（含 `grading_weights` 等元信息）

### 3.3 计算指标（score_calculator.py）

- **单模型总得分率** = Σ(各任务 `grading.mean`) / 任务数 × 100%
- **分类别得分** = 按 `category` 分组求均值
- **≥95% 任务数**：得分率 ≥ 0.95 的任务数（优秀覆盖面）
- **<60% 任务数**：得分率 < 0.60 的任务数（明显短板数）
- **Token 效率** = 得分率 / 总 Token（每千 Token 得分）

### 3.4 输出 collected_data.json

包含：
- `models[]`：模型列表及其全部指标（得分率、Token统计、分类别得分）
- `task_matrix[]`：对齐后的任务矩阵（每任务 × 每模型的得分/breakdown/notes）
- `category_summary[]`：分类别汇总表
- `token_summary[]`：Token 统计对比表
- `tasks_to_analyze[]`：待深度分析任务清单（包含 transcript 路径、任务 md 路径、入选原因）

## 四、低分任务筛选（task_filter.py）

筛选"需要 LLM 深度分析"的任务，减少 context 消耗。

### 4.1 多模型场景（两个维度并集）

**① 相对短板**：目标模型明显落后于对比模型
- 判定条件：对比模型得分中位数 ≥ 0.8 **且** 目标模型比对比模型中位数低 ≥ 0.2
- 捕捉：其他模型都行，唯独目标模型差（如 task_stock：三模型满分、Spark 0分）

**② 全员低分**：所有模型（含目标）得分均 < **0.4**
- 捕捉：大家都搞不定的任务，分析任务本身难度或环境问题

### 4.2 单模型降级回退

无对比模型时，①②都失效，回退到**绝对阈值**：
- 目标模型得分 < 0.8 的任务

### 4.3 参数配置

阈值设为常量并可通过 CLI 参数覆盖：
- `RELATIVE_WEAKNESS_MIN_OTHERS` = 0.8（对比模型中位数下限）
- `RELATIVE_WEAKNESS_GAP` = 0.2（目标模型落后幅度）
- `ALL_LOW_THRESHOLD` = 0.4（全员低分阈值）
- `ABSOLUTE_LOW_THRESHOLD` = 0.8（单模型阈值）

每个入选任务标注入选原因（`relative_weakness` / `all_low` / `absolute_low`），供阶段2 LLM 区分分析角度，也供阶段3 渲染时归类。

## 五、阶段2：LLM 分析（analyze）

LLM 读取 `collected_data.json` + 原始数据，产出 `analysis.json`。SKILL.md 给出明确工作指引。

### 5.1 输入给 LLM

1. **collected_data.json**（统计数据 + 待分析任务清单）
2. **每个待分析任务的**：
   - 目标模型 transcript（必读）
   - 得分高的对比模型 transcript（选读对比，理解为什么对比模型得分高）
3. **对应任务 md 文件的评分标准章节**：
   - Grading Criteria
   - Automated Checks
   - LLM Judge Rubric
   （原文为英文，需翻译成中文）
4. **agent-capability-dimensions.md**（20 个 Agent 能力维度参考，Skill 内置副本）

### 5.2 LLM 产出（analysis.json）

```json
{
  "capability_mapping": {
    "task_id": ["能力维度1", "能力维度2", ...]
  },
  "task_analysis": [
    {
      "task_id": "task_xxx",
      "filter_reason": "relative_weakness | all_low | absolute_low",
      "grading_criteria_cn": "评分标准中文翻译",
      "target_model_breakdown": {
        "breakdown": {"automated.xxx": 0.0, "llm_judge.yyy": 0.5, ...},
        "notes": "评语摘要",
        "transcript_summary": "关键行为摘要（工具调用54次、输出截断等）"
      },
      "comparison_models": [
        {"model": "DeepSeek V4 Pro", "score": 1.0, "why_succeeded": "为什么成功"}
      ],
      "root_cause": "根本原因分析"
    }
  ],
  "target_model_weaknesses": [
    {
      "theme": "短板主题（如：联网搜索失败后缺乏回退策略）",
      "related_tasks": ["task_stock", "task_market_research"],
      "evidence": "证据描述（结合 transcript 和 token 数据）",
      "comparison": "对比模型表现",
      "token_data": {"target": 7500000, "others_avg": 3200000}
    }
  ],
  "improvement_suggestions": [
    {
      "priority": "P0 | P1 | P2",
      "direction": "改进方向",
      "expected_gain": "+X.X%",
      "explanation": "说明"
    }
  ]
}
```

### 5.3 Context 控制策略

- 阶段1 已筛掉高分任务，只读低分任务 transcript
- transcript 大时（如 Spark task_stock 54 次工具调用）：
  - 按需读 `type: toolCall`、`type: toolResult`、`type: thinking` 关键片段
  - 不全量灌入，提取关键指标（工具调用次数、失败模式、token 消耗）

## 六、阶段3：报告渲染（render）

`report_renderer.py` 读取 `collected_data.json` + `analysis.json`，按示例报告结构拼装 Markdown。

### 6.1 报告结构模板

参考示例报告 `comparison_four_models_report.md`，自适应单/多模型：

```markdown
# {标题}
多模型："PinchBench {Suite} {N}模型评测对比报告"
单模型："{模型} PinchBench 评测报告"

> 评测时间 | 评测配置 | 评测框架 | Judge模型

[多模型] 一、整体排名
  表格：排名 | 模型 | 得分率 | ≥95%任务数 | <60%任务数 | 综合结论

[多模型] 二、Agent核心能力对比
  表格：考察点（LLM归类） | 对应任务 | 各模型得分 | 排名 | 结论
  （Python 按 LLM 的 capability_mapping 生成此表）

三、分类别得分对比
  表格：类别(category中文名) | 各模型得分 | 最优模型

四、各任务详细得分
  表格：任务 | 类别 | 各模型得分 | 失分点分析
  （Python 从 notes 取 + LLM 分析合并）

五、{目标模型}短板深度分析
  （单模型时改为"失分任务深度分析"）
  按 LLM 归纳的每个短板主题（如 5.1/5.2/5.3）：
    - 标题 + 对应任务
    - **评分标准（中文）**
    - **目标模型失分明细**（breakdown + transcript摘要）
    - **对比模型表现**（Token数据表）
    - **根本原因**

[多模型] 六、Token消耗与效率对比
  表格：总Token | 总请求数 | 得分率 | 每千Token得分

[多模型] 七、分项排名
  汇总各维度第一名

八、最终总结 + 改进建议表
  按 P0/P1/P2 优先级
```

### 6.2 自适应逻辑

- **多模型（≥2）**：生成完整结构，包含所有排名对比章节（一、二、六、七）
- **单模型**：跳过排名章节，重点突出"三（仅该模型）、四、五（失分任务深度）、八"

### 6.3 文件命名与输出路径

**默认输出位置**：输入目录第一层级（总目录或模型目录的父目录）

**文件名规则**：
- 多模型：`comparison_{N}_models_report.md`
- 单模型：`{target_model}_evaluation_report.md`

**覆盖选项**：`--output` 参数可覆盖完整路径

## 七、CLI 接口设计

### 7.1 主命令

```bash
python skills/pinchbench-report-generator/report_cli.py \
  <result_dir> \
  --target-model xsparkx2flash \
  [--output <path>] \
  [--thresholds relative_weakness_min=0.8,gap=0.2,all_low=0.4,absolute=0.8]
```

**参数说明**：
- `<result_dir>`：评测结果目录（总目录或多个模型目录，空格分隔）
- `--target-model`：目标模型名（用于深度分析），默认 `xsparkx2flash`
- `--output`：输出路径（可选，默认输入目录）
- `--thresholds`：覆盖筛选阈值（可选）

### 7.2 子命令（调试用）

```bash
# 仅阶段1：数据收集
python report_cli.py collect <result_dir> --output collected_data.json

# 仅阶段3：渲染（需要已有 collected_data.json + analysis.json）
python report_cli.py render \
  --collected-data collected_data.json \
  --analysis analysis.json \
  --output report.md
```

阶段2（LLM 分析）通过上层 Skill agent 调用，不单独暴露 CLI。

## 八、测试策略

### 8.1 单元测试

- **test_result_collector.py**：模拟目录结构，验证模型识别、JSON解析
- **test_score_calculator.py**：验证得分率、分类别、排名计算公式
- **test_task_filter.py**：验证相对短板/全员低分/单模型降级筛选逻辑（构造数据）
- **test_report_renderer.py**：验证 Markdown 模板拼装、章节自适应显示

### 8.2 集成测试

用真实数据 `astronclaw-result/all-suite/round-2/` 运行完整流程：

```bash
# collect + analyze (mock LLM输出) + render
python report_cli.py astronclaw-result/all-suite/round-2/ \
  --target-model xsparkx2flash-530
```

对比生成报告与示例报告 `comparison_four_models_report.md` 的结构一致性：
- 表格行列数
- 章节标题层级
- 数值计算准确性

### 8.3 端到端验证

使用真实 LLM 阶段2（非 mock），验证：
- Agent 能力归类是否合理
- 失分点分析是否准确读取 transcript
- 改进建议是否可操作

## 九、设计权衡与边界

### 9.1 为什么三阶段？

- **Python 算表格**：避免 LLM 拼大表格时算错/串列，数字准确性至关重要
- **LLM 做语义**：transcript 分析、失分原因推断是 LLM 强项，Python 无法胜任
- **分离关注点**：collect 可独立复用（如给其他分析脚本用），render 可快速迭代模板

### 9.2 为什么复制 agent-capability-dimensions.md？

- Skill 应自包含，避免依赖外部路径变动导致运行时失败
- `docs/` 下的文档可能被重构、移动或删除
- Skill 内副本作为稳定快照，即使外部更新也不影响已有 Skill

### 9.3 单模型降级的必要性

- 用户可能只跑一个模型，需要看该模型的失分分析
- 降级模式虽然缺少对比，但绝对低分任务依然有分析价值
- 报告结构自适应，避免生成无意义的空表

### 9.4 低分任务筛选的必要性

- PinchBench all-suite 有 53 个任务，读所有 transcripts 会爆 context
- 高分任务（如满分的编码任务）无需深度分析，统计表格已足够
- 筛选后 LLM 只聚焦"有问题"的任务，token 消耗可控

## 十、与现有 Skill 的关系

### 10.1 复用 shared/ 工具

- `path_resolver.py`：任务 ID 解析、路径处理
- 其他通用工具按需复用

### 10.2 与 pinchbench-case-optimizer 的对比

| 维度 | case-optimizer | report-generator |
|------|----------------|------------------|
| 目标 | 优化评测用例 | 生成评测报告 |
| 输入 | results-auto/ 单任务结果 | 评测结果目录（多模型） |
| 分析维度 | 5维度（Prompt清晰度/评分/难度/超时/工具） | Agent能力对比 + 失分深度分析 |
| 输出 | 优化后的任务md + 优化报告 | 多模型对比报告md |
| 迭代性 | 多轮链式优化 | 单次生成报告 |

两者互补：case-optimizer 面向用例改进，report-generator 面向模型评估。

## 十一、实施里程碑

### 里程碑 1：Python 框架（2天）
- [ ] 目录扫描、模型识别（result_collector.py）
- [ ] 得分计算、统计指标（score_calculator.py）
- [ ] 低分任务筛选（task_filter.py）
- [ ] 单元测试覆盖

### 里程碑 2：报告渲染（1天）
- [ ] Markdown 模板拼装（report_renderer.py）
- [ ] 单/多模型自适应
- [ ] CLI 接口（report_cli.py）
- [ ] 集成测试（mock LLM 输出）

### 里程碑 3：LLM 分析（2天）
- [ ] SKILL.md 撰写（LLM 工作指引）
- [ ] 复制 agent-capability-dimensions.md 到 Skill
- [ ] LLM 分析脚本（或通过上层 Skill agent 调用）
- [ ] 端到端测试（真实 LLM）

### 里程碑 4：文档与优化（1天）
- [ ] README、使用示例
- [ ] 性能优化（transcript 分批读取）
- [ ] 错误处理完善

## 十二、未来扩展

### 12.1 短期（v1.1）
- 支持 HTML 格式报告输出
- 支持报告模板自定义（用户提供模板文件）
- 增加报告对比功能（多轮评测结果趋势分析）

### 12.2 长期（v2.0）
- 集成到 Web 界面（上传结果目录 → 在线生成报告）
- 支持更多图表可视化（散点图、雷达图）
- 支持多语言报告（英文/日文）

---

**设计确认**：本设计已与用户确认，包含：
- 三阶段流水线架构（Python/LLM/Python）
- 单/多模型自适应
- 目标模型深度分析（评分标准中文 + 失分点 + transcript摘要）
- 低分任务筛选（相对短板 0.8/0.2 + 全员低分 0.4 + 单模型降级 0.8）
- Agent 能力维度参考（Skill 内置副本）
- 输出位置自适应（输入目录 + --output 覆盖）

准备进入实施阶段。
