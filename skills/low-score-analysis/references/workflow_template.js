// 低分任务根因分析 —— Workflow 脚本模板
//
// 特性:
// 1. ✅ 支持分批处理 - 自动将大批量任务切分成小批次串行执行
// 2. ✅ 支持断点续传 - 通过 args.completed_task_ids 跳过已完成任务
// 3. ✅ 数据已精简 - 调用方应传入精简后的任务数据
// 4. ✅ 容错机制增强 - 单个 agent 失败不中断整体流程
// 5. ✅ 进度可观测 - 每批次完成后输出进度日志
//
// 调用方式:
//   Workflow({
//     scriptPath: "workflow_template.js",
//     args: {
//       model: "xsparkx2flash-530",
//       project: "/path/to/PinchBench/skill",
//       result_root: "/path/to/astronclaw-result/round-3",
//       tasks: [...],  // 已精简的任务数组
//       batch_size: 10,  // 可选，默认10
//       completed_task_ids: ["task1", "task2"]  // 可选，已完成的任务ID
//     }
//   })

export const meta = {
  name: 'pinchbench-low-score-root-cause-analysis',
  description: '分批并发分析低分任务（支持断点续传、自动分批、容错）',
  phases: [
    { title: 'Analyze', detail: '分批分析，每批10个任务避免超时' }
  ],
}

// JSON Schema for structured output
const SCHEMA = {
  type: 'object',
  properties: {
    task_id: {
      type: 'string',
      description: '任务ID'
    },
    result_analysis: {
      type: 'string',
      description: '详细的结果分析(800-1200字)，包含任务概述、多轮对比、失分点逐条分析、裁判判词引用'
    },
    root_cause_analysis: {
      type: 'string',
      description: '根因总结(1-2句话, 80-150字)，归类到常见根因类别并标注特殊情况'
    },
  },
  required: ['task_id', 'result_analysis', 'root_cause_analysis'],
  additionalProperties: false,
}

// ========== 参数解析与验证 ==========

// 兼容性修复：动态 scriptPath 模式下 Workflow 会把 args 序列化成 JSON 字符串传入脚本
// （实测 typeof args === 'string'），而非对象。这里统一归一化回对象，否则 A.tasks/A.task_files
// 会是 undefined，导致"未提供任务"报错。同时兼容对象/未定义两种情况。
let A = args
if (typeof A === 'string') {
  try { A = JSON.parse(A) } catch (e) { A = {} }
}
A = A || {}

const model = A.model || 'unknown-model'
const project = A.project || ''
const result_root = A.result_root || ''
const tasks = A.tasks || []
const taskFiles = A.task_files || []  // 路径模式：每个元素是单任务JSON文件的绝对路径
const batchSize = A.batch_size || 10
const completedIds = new Set(A.completed_task_ids || [])

// 参数验证
if ((!tasks || tasks.length === 0) && (!taskFiles || taskFiles.length === 0)) {
  throw new Error('未提供任务：请通过 args.tasks 传入清单，或 args.task_files 传入单任务文件路径数组')
}

log(`模型: ${model}`)
log(`任务总数: ${tasks.length}`)
log(`批次大小: ${batchSize}`)

// ========== 过滤已完成任务 ==========

// 路径模式：把 task_files 转成轻量任务对象（task_id 从文件名推断，仅用于标签/去重）
const pathModeTasks = taskFiles.map(fp => {
  const base = String(fp).split('/').pop().replace(/\.json$/, '')
  // 文件名形如 b5_t02_task_subway_navigation，去掉 b<batch>_t<idx>_ 前缀得到 task_id
  const tid = base.replace(/^b\d+_t\d+_/, '')
  return { task_id: tid, grading_file: fp, _pathMode: true }
})

const allInputTasks = [...tasks, ...pathModeTasks]
const pendingTasks = allInputTasks.filter(t => !completedIds.has(t.task_id))

if (pendingTasks.length === 0) {
  log('✅ 所有任务已完成，无需重复分析')
  return []
}

if (completedIds.size > 0) {
  log(`⏭️  跳过已完成: ${completedIds.size} 个`)
}
log(`📋 待分析: ${pendingTasks.length} 个`)

// ========== Prompt 构建函数 ==========

// 路径模式 prompt：agent 自己从单任务 JSON 文件读取全部数据，杜绝调用方传入数据时的误差
function buildPromptFromFile(t) {
  const tid = t.task_id
  const gradingFile = t.grading_file
  return `你是评测失分分析专家。请分析被测模型 ${model} 在任务 ${tid} 上为什么失分。

## 第0步（必做）：读取完整评分数据
本任务的完整数据保存在单个 JSON 文件：${gradingFile}
**先用 Read 工具读取该文件**。文件包含字段：task_id、score_pct（平均得分%）、category（类别）、grading_detail.grading_runs（每轮 score + breakdown 失分点 + notes 裁判判词）、task_file（任务定义路径）、transcript（执行记录路径，可能为空）。
后续分析必须严格基于该文件内容，引用判词时照搬文件中的 notes 原文，禁止编造或臆测任何评分、判词、数值。

## 分析步骤（严格按顺序执行，用证据说话）

### 第1步：理解任务目标
读取文件中的 task_file 路径所指任务定义。重点：任务标题、输入数据、预期输出、评分标准。用2-3句话概括这个任务要模型做什么。

### 第2步：分析失分点（重点）
遍历 grading_detail.grading_runs 中每一轮的 breakdown，找出所有 <1.0 的检查点。对**每一个**失分检查点：
1. 说明该检查点要求什么
2. 从 transcript 找证据，说明模型实际做了什么
3. 对比要求与实际，说明为什么扣分

### 第3步：读取 transcript 找证据
读取文件中的 transcript 路径（JSONL，每行一个事件；>100KB 用 Read 的 offset/limit 分页）。
- 若 transcript 为空字符串：说明任务执行层报错，模型未获运行机会，通常是环境问题（非模型能力）。
- 多轮时 transcript 仅含最后一轮，注意结合各轮 breakdown 差异分析稳定性。
引用证据须具体（"第23行模型调用 Bash 执行X，返回错误Y"），禁止空泛表述。

### 第4步：输出分析结果（中文，结构化）

**result_analysis（800-1200字）**：1.任务概述 2.多轮表现对比 3.失分点逐条分析 4.引用裁判判词原文

**root_cause_analysis（1-2句话，80-150字）**：
- 第一句：核心问题类别 + 具体表现
- 环境问题标注"非模型能力问题"；高分(>0.85)标注"本质高分，非能力短板"

## 常见根因类别
1. 稳定性问题 2. 产物未落盘/文件写入失败 3. 任务串扰 4. 代码错误 5. 数据计算错误 6. 不回退知识库 7. 幻觉/编造数据 8. 能力短板 9. 环境限制（非模型能力问题）10. 内容质量小瑕疵（本质高分>0.85）`
}

function buildPrompt(t) {
  if (t._pathMode) return buildPromptFromFile(t)
  const tid = t.task_id
  const task_file = t.task_file || '(任务文件未定位)'
  const transcript = t.transcript || ''
  const gradingFile = t.grading_file || ''

  // 格式化多轮评分信息
  const runs = t.grading_detail?.grading_runs || []
  const runsInfo = runs.map(r => {
    const failedPoints = Object.entries(r.breakdown || {})
      .filter(([_, v]) => v < 1.0)
      .map(([k, v]) => `${k}=${v}`)
      .join(', ')
    return `  第${r.run}轮: 得分${(r.score * 100).toFixed(1)}%${failedPoints ? `, 失分点: ${failedPoints}` : ''}`
  }).join('\n')

  // 提取所有失分点（去重）
  const allFailedPoints = new Set()
  runs.forEach(r => {
    Object.entries(r.breakdown || {}).forEach(([k, v]) => {
      if (v < 1.0) allFailedPoints.add(k)
    })
  })

  // 提取所有 notes
  const notesInfo = runs
    .filter(r => r.notes)
    .map(r => `  第${r.run}轮: ${r.notes}`)
    .join('\n') || '(无 notes)'

  return `你是评测失分分析专家。请分析被测模型 ${model} 在任务 ${tid} 上为什么失分。
${gradingFile ? `
## 第0步（必做）：读取完整评分数据
本任务的完整评分明细（含每轮 breakdown 与裁判判词 notes）保存在文件：${gradingFile}
**先用 Read 工具读取该 JSON 文件**，以其中的 grading_detail.grading_runs 为准进行分析。
下方"多轮评分情况""裁判判词"仅为摘要，若与文件不一致，以文件为准。文件中的 notes 是裁判原始判词，引用时务必基于文件内容，禁止编造。
` : ''}
## 任务基本信息
- 任务ID: ${tid}
- 平均得分: ${t.score_pct}%
- 类别: ${t.category || '未分类'}

## 多轮评分情况
${runsInfo}

## 裁判判词（notes）
${notesInfo}

## 分析步骤（严格按顺序执行，用证据说话，禁止臆测）

### 第1步：理解任务目标
${task_file !== '(任务文件未定位)' ?
  `读取任务文件：${task_file}

重点关注：任务标题、输入数据、预期输出、评分标准。

理解后用2-3句话概括：这个任务要模型做什么、产出什么、关键评分点是什么。` :
  `任务文件未定位。从 task_id="${tid}" 推断任务目标。`
}

### 第2步：分析失分点（重点）
上述多轮评分中，以下检查点出现了扣分：
${Array.from(allFailedPoints).map(p => `- ${p}`).join('\n')}

对**每一个**失分检查点，必须：
1. 说明这个检查点要求什么
2. 从 transcript 找证据，说明模型实际做了什么
3. 对比要求与实际，说明为什么扣分

### 第3步：全量读取 transcript 找证据
transcript 路径：${transcript || '(无 transcript，任务执行失败)'}

${transcript ? (runs.length > 1 ?
`⚠️ **重要说明**：该任务跑了 ${runs.length} 轮，但 transcript 文件**仅包含最后一轮（第${runs.length}轮）**的执行记录。
如果前几轮与最后一轮得分差异很大，说明模型表现不稳定。分析时：
- 对比各轮 breakdown 差异，找出哪些检查点在哪轮失分
- 重点分析最后一轮的 transcript（这是唯一可见的执行过程）
- 如果最后一轮失分而前几轮成功，在分析中明确说明"前X轮成功但无transcript可查"
` :
`该任务仅跑了 1 轮，transcript 包含完整执行记录。`) :
`该任务没有 transcript 文件（任务执行层报错），说明模型在评测环境中根本没有机会运行，这通常是环境问题（工具不可用、权限不足、依赖缺失）而非模型能力问题。`}

${transcript ? `这是 JSONL 格式文件，每行一个事件。如果文件很大（>100KB），用 Read 工具的 offset/limit 参数分页读取。

**引用 transcript 证据时必须具体**:
✓ "第23行模型调用 Bash 执行 'python analyze.py'，工具返回 'NameError: name pd is not defined'"
✓ "第6-15行模型连续10次 Read 文件，但从未调用 Write 工具，导致报告文件未创建"

❌ "模型调用了工具但结果不对"（太空泛）
❌ "存在数据处理错误"（没有具体指出哪个数据、什么错误）` : ''}

### 第4步：输出分析结果（中文，结构化）

**result_analysis（800-1200字）**：
1. 任务概述（2-3句话）
2. 多轮表现对比（如果不一致）
3. 失分点逐条分析（每个失分检查点单独分析）
4. 引用裁判判词

**root_cause_analysis（1-2句话，80-150字）**：
- 第一句：直接点出核心问题类别和具体表现
- 第二句（可选）：补充关键细节
- 如果是环境问题，标注"非模型能力问题"
- 如果是高分(>0.85)，标注"本质高分，非能力短板"

## 常见根因类别
1. 稳定性问题 - 同一任务多轮表现差异大
2. 产物未落盘/文件写入失败
3. 任务串扰 - 产出了相邻任务的文件
4. 代码错误 - Python语法错误、包名拼错、函数调用错误
5. 数据计算错误 - 聚合口径错、算法实现有误、解析逻辑错
6. 不回退知识库 - 联网失败后不降级
7. 幻觉/编造数据
8. 能力短板
9. 环境限制（非模型能力问题）
10. 内容质量小瑕疵 - 本质高分(>0.85)，仅细节不足`
}

// ========== 分批执行逻辑 ==========

phase('Analyze')

// 将任务分成小批次
const batches = []
for (let i = 0; i < pendingTasks.length; i += batchSize) {
  batches.push(pendingTasks.slice(i, i + batchSize))
}

log(`📦 分为 ${batches.length} 批次`)

// 逐批串行执行（避免并发过多导致超时）
const allResults = []
let totalSucceeded = 0
let totalFailed = 0

for (let i = 0; i < batches.length; i++) {
  const batch = batches[i]
  const batchNum = i + 1

  log(`\n${'='.repeat(60)}`)
  log(`🔄 批次 ${batchNum}/${batches.length} 开始`)
  log(`   任务: ${batch.map(t => t.task_id).slice(0, 3).join(', ')}${batch.length > 3 ? ` ... (共${batch.length}个)` : ''}`)
  log(`${'='.repeat(60)}`)

  // 批次内并发执行
  const results = await pipeline(
    batch,
    (t) => agent(buildPrompt(t), {
      label: `${t.task_id.slice(0, 30)}${t.score_pct != null ? ` (${t.score_pct}%)` : ''}`,
      phase: 'Analyze',
      schema: SCHEMA
    })
  )

  // 统计成功/失败
  const succeeded = results.filter(Boolean)
  const failed = results.length - succeeded.length

  totalSucceeded += succeeded.length
  totalFailed += failed

  allResults.push(...succeeded)

  log(`\n✓ 批次 ${batchNum}/${batches.length} 完成`)
  log(`   成功: ${succeeded.length}/${batch.length}`)
  if (failed > 0) {
    log(`   失败: ${failed}`)
  }
}

// ========== 最终统计 ==========

log(`\n${'='.repeat(60)}`)
log(`🎉 全部完成`)
log(`${'='.repeat(60)}`)
log(`✅ 成功: ${totalSucceeded}/${pendingTasks.length}`)
if (totalFailed > 0) {
  log(`❌ 失败: ${totalFailed}`)
}
log(`📊 成功率: ${(totalSucceeded/pendingTasks.length*100).toFixed(1)}%`)
log(`${'='.repeat(60)}`)

return allResults
