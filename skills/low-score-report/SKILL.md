---
name: low-score-report
description: Generate a comprehensive root-cause report for PinchBench low-score tasks, with layered attribution analysis (L1a/L1b/L3/L4) and deep dive into failure mechanisms. Triggers on "生成低分任务报告""根因共性分析报告""low score report". Reads low-score-analysis results and produces a well-structured markdown report with clear hierarchy and detailed code-level analysis.
---

# 低分任务根因共性分析报告生成 Skill

基于 `low-score-analysis` Skill 的输出，生成一份**格式规范、层次分明、根因深入**的根因共性分析报告（Markdown），用于评测总结与模型改进方向分析。

## 核心特性

1. **四层归因框架**：区分 L1a（底层推理）、L1b（长程执行）、L3（环境）、L4（评测系统）
2. **深度根因分析**：不止步于"抛出错误"，追溯到**具体代码逻辑问题**
3. **层次化排版**：使用序号、缩进、分点陈述，避免大段堆砌
4. **通俗易懂**：避免AI腔，用事实说话
5. **独立分析**：每轮评测独立分析，除非明确要求对比才包含对比信息
6. **主口径 + 高波动专项**：低分主体按**三轮平均分 < 阈值**选取（与模型得分口径一致，不夸大问题）；另设**高波动/稳定性专项**单列"均分达标但单轮偶发塌陷"（极差≥50pt，如 [100,0,100]）的任务——这些是最可复现、最值得修的稳定性缺陷，不能因均分口径而漏掉

## 低分口径（重要）

- **主口径（正文主体）**：三轮**平均分 < 60%**。这是"真正拉低模型得分"的低分任务，与报告里类别均分、总分口径自洽。
- **高波动专项（独立章节）**：平均分 ≥ 60% 但三轮**极差(max-min) ≥ 50pt**。这类任务模型有满分能力，只是某轮偶发塌陷（多为产物未落盘/单轮超时），是清晰可操作的稳定性缺陷。
- 清单里每条任务由 `low_score_type` 字段（`low` / `high_variance`）标注归属；用 `report_utils.split_tasks_by_bucket()` 分桶。
- **为什么不用"任意一轮<60"**：该口径会把大量"2/3 轮满分的可恢复抖动"计入低分，把根因分布夸大成"执行能力差"；而纯平均分口径又会漏掉稳定性缺陷。二者结合最完整。

## 输入

### 必需输入

1. **评测结果目录**：例如 `/path/to/astronclaw-result/all-suite/round-4/xsparkx2flash-530`
2. **低分任务清单**：`<result-root>/report-workspace/_failed_tasks_<model>.json`
3. **根因分析结果**：`<result-root>/report-workspace/analysis_<model>.json`

这三个输入由 `low-score-analysis` Skill 产出，本 Skill 基于它们生成报告。

### 可选输入（元信息）

用户可以在调用时提供额外的评测上下文信息：

- **轮次标识**：如 `round-4`（用于报告命名和描述）
- **评测特殊配置**：如 `"超时时间是 round-3 的 4 倍"`（会提取到报告中）
- **对比目标**：如 `"对比 round-3"`（明确指定才包含对比信息）

**示例调用**：
```
生成 xsparkx2flash-530 的低分任务根因分析报告
评测轮次：round-4
说明：round-4 相对 round-3，每个任务超时时间放大了 4 倍
```

或者不带对比：
```
为 astronclaw-result/all-suite/round-4/xsparkx2flash-530 生成独立的根因分析报告
```

## 输出

**报告文件**：`<result-root>/低分任务根因共性分析报告_<model>.md`（无版本后缀）

## 报告结构

### 标题
```markdown
# AstronClaw PinchBench {具体模型名} 模型低分任务根因分析报告
```

例如：`# AstronClaw PinchBench Spark 模型低分任务根因分析报告`

### 开头信息
- 被测模型
- 评测轮次：根据实际任务数动态生成（从 summary.json 的 tasks 数组长度获取）
  - 示例：`round-4（all-suite 147 个评测任务，每任务 3 轮）`
  - 如果有特殊配置（如超时放大），在此注明
- 分析样本
- 数据来源

### 分析维度定义
用列表+缩进说明每层含义、典型表现。
**注意**：所有 "provider" 统一改为 "推理服务"

### 一、执行摘要
- 全0分任务列表
- 各类别均分表
- 一句话归因（四层分布）
- 核心结论
  - **独立分析**：只描述本轮特征，不提及其他轮次
  - **对比分析**（仅当用户明确要求对比时）：说明与对比目标的差异

### 二、根因分类
- 2.1 根因×归属层主表
- 2.2 四层归属汇总表
- （如果适用）2.3 为什么某些根因是"跨层"的

### 三、按根因分类详述（仅主口径低分任务）
每个根因分类（工具调用格式错误、超时、环境限制等）包含：
1. 主导归属层标注
2. 共性机制（分层说明）
3. 该类任务详表（Markdown表格）
4. **典型案例深析**（2-3个）：
   - 必须包含深度根因分析（见下文）

### 四、高波动 / 稳定性专项（独立章节）
针对 `low_score_type == "high_variance"` 的任务（均分达标但单轮偶发塌陷）：
1. 用 `format_variance_table()` 生成详表，展示**极差**与**各轮得分形态**（如 100/0/100）
2. 说明共性机制：这类几乎全是"模型有满分能力，但某轮产物未落盘/单轮超时"——是最可复现、最值得修的稳定性缺陷
3. 与主口径的关系说明：这些任务因三轮平均仍≥阈值而**不计入**正文低分统计，单列于此避免遗漏
4. 挑 1-2 个深度案例（对照满分轮 vs 塌陷轮，指出塌陷轮缺失了哪一步）

### 五、跨任务关键发现
- 发现一：LLM能力维度分析
- 发现二：LLM裁判假阳性（如有）
- 发现三：评分脚本刚性（如有）

### 六、改进建议
按层归类（L1a、L1b+框架、L3、L4），每层3-5条具体建议。

## 深度根因分析要求（核心）

对于代码类失败（KeyError、逻辑错误、格式错误），必须：

1. **读取 transcript.jsonl**，找到 `type=tool_use, name=exec` 的代码执行记录
2. **提取失败的代码片段**（从 `input.command` 或 `input.code`）
3. **分析具体错误原因**：
   - KeyError：字典键不存在，是因为数据结构理解错误还是日期格式解析错？
   - 排序错误：是 `sorted()` 的 `key` 参数写错了方向还是字段名错？
   - 变量未定义：是因为作用域问题还是前置步骤被跳过？
4. **给出正确代码示例或修复方向**

示例对比：

❌ **浅层分析**："第3轮转而写Python脚本解析日志，5次exec全部抛出KeyError，反复失败后任务超时"

✅ **深度分析**："第3轮转而写Python脚本解析日志，5次exec全部抛出KeyError。根本原因是脚本用`datetime.strptime(line_parts[3], '%b %d')`解析日期，但日志实际格式是`'Fri Jun 10'`（星期+月+日），缺少星期字段导致解析失败。模型反复修改日期格式串（`'%b %d'` → `'%Y-%b-%d'`）但始终未意识到需要先过滤掉星期，5次调试均卡在相同错误点，最终180秒超时。"

## 术语统一

- ❌ provider → ✅ 推理服务
- ❌ provider idle timeout → ✅ 推理服务空闲超时
- ❌ provider 无响应 → ✅ 推理服务无响应

## 评测轮次信息提取

从 `summary.json` 提取实际任务数：

```python
import json

with open('summary.json') as f:
    data = json.load(f)
    task_count = len(data.get('tasks', []))
    
# 生成描述
round_desc = f"round-X（all-suite {task_count} 个评测任务，每任务 3 轮）"
```

如果用户提供了特殊配置说明（如"超时4倍"），追加到描述：
```
round-4（all-suite 147 个评测任务，每任务 3 轮，超时时间相对 round-3 放大 4 倍）
```

## 对比模式控制

**默认（独立分析）**：
- 不提及其他轮次
- 不使用"本轮与 round-X 的不同"之类的表述
- 只描述当前轮次的特征

**对比模式（明确要求时）**：
用户明确说"对比 round-3"才启用，此时可以：
- 在核心结论中说明与对比目标的差异
- 在根因分类中对比层分布变化
- 在改进建议中指出"相比 round-X 改善/恶化的点"

## 使用方式

**独立分析**：
```
生成 xsparkx2flash-530 的低分任务根因分析报告
基于 astronclaw-result/all-suite/round-4
```

**带上下文信息**：
```
生成 xsparkx2flash-530 的低分任务根因分析报告
评测轮次：round-4
说明：超时时间是 round-3 的 4 倍
```

**对比分析**：
```
生成 xsparkx2flash-530 的低分任务根因分析报告
对比 round-3 与 round-4 的差异
```

## 依赖

- `low-score-analysis` Skill 的输出
- Python 3.8+（用于读取 JSONL、统计分类）

## 报告示例参考

参考 `astronclaw-result/all-suite/round-4/低分任务根因共性分析报告_xsparkx2flash-530.md`（修正后的版本）

