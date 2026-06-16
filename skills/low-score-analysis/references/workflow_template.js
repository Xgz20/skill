// 低分任务根因分析 —— Workflow 脚本模板（PinchBench 版）
//
// 用途：读取 generate_failed_tasks_manifest.py 产出的清单（args.tasks），
// 为每个低分任务并发 spawn 一个 agent，让 agent 先从 grading_runs 定位失分点，
// 再全量直读 transcript.jsonl 找证据，输出结果分析与根因分析。
//
// 调用方（Claude Code）需通过 Workflow 工具的 args 传入：
//   {
//     model,
//     project,
//     result_root,
//     tasks: [{
//       task_id,
//       score_pct,
//       min_score_pct,
//       grading_runs: [{run, score, breakdown, notes}, ...],
//       task_file,
//       transcript
//     }, ...]
//   }
//
// 其中 tasks 来自清单 JSON。
//
// 产物：workflow 返回 [{task_id, result_analysis, root_cause_analysis}, ...]，
// 由调用方转换格式后写入 <report-workspace>/<model>_analysis_input.json。

export const meta = {
  name: 'pinchbench-low-score-root-cause-analysis',
  description: '并发分析某模型所有低分任务，输出结果分析与根因分析（证据来自 grading runs + transcript）',
  phases: [{ title: 'Analyze', detail: '每个低分任务一个 agent：从 grading runs 定位失分点，全量直读 transcript 找证据' }],
}

const SCHEMA = {
  type: 'object',
  properties: {
    task_id: { type: 'string', description: '任务ID' },
    result_analysis: {
      type: 'string',
      description: `结果分析（中文，800-1200字）：

        结合任务目标与评分标准，**逐个失分检查点**给出事实依据和关键中间过程数据佐证。

        【必须包含】：
        1. **任务概述**（2-3句话）：
           - 这个任务要求模型做什么？
           - 预期产出什么？
           - 关键评分点是什么？

        2. **多轮表现对比**（如果多轮表现不一致）：
           - 第X轮得分Y%：哪些检查点扣分
           - 第X轮得分Y%：哪些检查点扣分
           - 总结：多轮表现的稳定性如何

        3. **失分点逐条分析**（每个扣分检查点都要分析）：
           对每个 breakdown 中得分 < 1.0 的检查点：
           - **检查点名称**：如 automated.report_created, llm_judge.data_accuracy
           - **要求是什么**：这个检查点要求模型做什么
           - **实际做了什么**：从 transcript 引用证据说明模型的实际行为
           - **为什么扣分**：对比要求与实际，说明失分原因

           **引用 transcript 证据的范例**：
           ✓ "transcript 显示模型共调用了 11 次工具，全部是 Read 文件操作（Read CSV 8次、Read task 3次），从未出现 Write 工具调用，因此报告文件 report.md 根本没有被创建。"
           ✓ "模型在第 23 行调用了 bash 执行 'python analyze.py'，工具返回结果显示 'NameError: name pd is not defined'，说明代码中将 pandas 拼写成了 pd 但没有导入。"
           ✓ "模型计算区域总营收时，transcript 第 15 行显示调用 pandas groupby('region').sum()，但随后直接用 head(1) 取第一行而非按金额排序后取最大值，导致输出的最佳区域是 West($27,225) 而非实际的 East($33,075)。"

           ❌ 不要写"模型调用了工具但结果不对"（太空泛，没说哪个工具、哪里不对）
           ❌ 不要写"存在数据处理错误"（没有具体指出哪个数据、什么错误）

        4. **裁判判词引用**（如果 notes 有内容）：
           - 引用裁判的关键判词
           - 说明裁判指出的具体问题

        【风格要求】：
        - 通俗易懂，让没看过这个任务的人能立即理解问题
        - 用具体的 transcript 行号/工具名/参数/返回值佐证
        - 如果模型编造了不存在的数据或产物，明确指出
        - 多轮不一致要分轮说明，不要混在一起
      `
    },
    root_cause_analysis: {
      type: 'string',
      description: `根因分析（中文，1-2句话，80-150字）：

        把多个失分点归纳到根本原因类别，简明扼要点出核心问题。

        【常见根因类别】：
        1. **稳定性问题**：同一任务多轮表现差异大（如一轮满分一轮全零）
        2. **产物未落盘/文件写入失败**：分析逻辑对但文件没成功写入，automated检查全失分
        3. **任务串扰**：产出了相邻任务的文件，说明混淆了不同任务
        4. **代码错误**：Python语法错误、包名拼错(pd vs pandas)、正则表达式bug、函数调用错误
        5. **数据计算错误**：聚合口径错(如未排序直接取head)、算法实现有误、解析逻辑错
        6. **不回退知识库**：联网失败后不降级使用训练知识（对比其他模型会回退）
        7. **幻觉/编造数据**：编造了不存在的数据、虚构了文件内容、伪造工具调用
        8. **能力短板**：如多模态识别失败、多文件编辑能力不足、跨语言处理困难
        9. **环境限制（非模型能力问题）**：工具/联网不可用、API不可达、权限不足
        10. **内容质量小瑕疵**：本质高分(>0.85)，仅细节不够完善(如字数略少、格式小问题)

        【写作要求】：
        - **第一句**：直接点出核心问题类别和具体表现
        - **第二句（可选）**：补充关键细节或影响范围
        - 如果是环境/工具问题，**必须**说明"非模型能力问题"
        - 如果是高分小扣(>0.85)，**必须**说明"本质高分，仅XXX小瑕疵，非能力短板"

        【正例】：
        ✓ "数据计算准确性不足：区域聚合时直接用 head(1) 取第一行而非按金额排序取最大值，导致最佳区域识别错误。"
          （清晰指出问题类别"数据计算"，具体说明错误原因）

        ✓ "稳定性问题：同一任务三轮表现为1.0/1.0/0.0，成功轮能正确创建文件，失败轮无任何工具调用记录，多轮表现极不一致。"
          （说明稳定性问题，给出具体的分数对比和差异表现）

        ✓ "环境/工具不可用（非模型能力）：任务执行层即报错无 transcript，疑似 gh CLI 工具在评测环境中不可用或鉴权失败。"
          （明确标注"非模型能力"，说明是环境问题）

        ✓ "本质高分(0.93)，仅实时定价未经联网核实、Linux兼容性文档可更严谨，采购建议和车队规划都准确，非能力短板。"
          （高分任务必须说明"本质高分"和"非能力短板"）

        【反例】：
        ❌ "模型存在多个问题需要改进"
          （没说什么问题，太空泛）

        ❌ "数据处理能力不足，代码质量有待提高，稳定性需要加强"
          （堆砌多个问题，没抓住根因）

        ❌ "联网失败导致无法完成任务"
          （没说明是否是环境问题还是模型问题）
      `
    },
  },
  required: ['task_id', 'result_analysis', 'root_cause_analysis'],
  additionalProperties: false,
}

const { model, project, result_root, tasks } = args

function buildPrompt(t) {
  const tid = t.task_id
  const task_file = t.task_file || '(任务文件未定位，可从 task_id 推断任务目标)'
  const transcript = t.transcript

  // 格式化多轮评分信息
  const runsInfo = t.grading_runs.map(r => {
    const failedPoints = Object.entries(r.breakdown)
      .filter(([k, v]) => v < 1.0)
      .map(([k, v]) => `${k}=${v}`)
      .join(', ')
    return `  第${r.run}轮: 得分${(r.score * 100).toFixed(1)}%${failedPoints ? `, 失分点: ${failedPoints}` : ''}`
  }).join('\n')

  // 提取所有失分点（去重）
  const allFailedPoints = new Set()
  t.grading_runs.forEach(r => {
    Object.entries(r.breakdown).forEach(([k, v]) => {
      if (v < 1.0) allFailedPoints.add(k)
    })
  })

  return `你是评测失分分析专家。请分析被测模型 ${model} 在任务 ${tid} 上为什么失分。

## 任务基本信息
- 任务ID: ${tid}
- 平均得分: ${t.score_pct}%
- 最低得分: ${t.min_score_pct}%
- 类别: ${t.category || '未分类'}

## 多轮评分情况
${runsInfo}

## 分析步骤（严格按顺序执行，用证据说话，禁止臆测）

### 第1步：理解任务目标
${task_file !== '(任务文件未定位，可从 task_id 推断任务目标)' ?
  `读取任务文件：${task_file}

重点关注：
- 任务标题和描述
- 输入数据/文件
- 预期输出/产出
- 评分标准（Grading Criteria）

理解后用2-3句话概括：这个任务要模型做什么、产出什么、关键评分点是什么。` :
  `任务文件未定位。从 task_id="${tid}" 推断：
- 前缀 task_log_ 表示日志分析类任务
- 前缀 task_csv_ 表示 CSV 数据分析类任务
- 前缀 task_meeting_ 表示会议记录分析类任务
根据前缀和任务名推断其目标。`
}

### 第2步：分析失分点（重点）
上述多轮评分中，以下检查点出现了扣分：
${Array.from(allFailedPoints).map(p => `- ${p}`).join('\n')}

对**每一个**失分检查点，必须：
1. 说明这个检查点要求什么
2. 从 transcript 找证据，说明模型实际做了什么
3. 对比要求与实际，说明为什么扣分

### 第3步：全量读取 transcript 找证据
transcript 路径：${transcript}

这是 JSONL 格式文件，每行一个事件。如果文件很大（>100KB），用 Read 工具的 offset/limit 参数分页读取，或用 Grep 定位关键片段。

**transcript 事件结构**：
- message (role=assistant)：模型的输出
  - content[].type=text：模型输出的文本
  - content[].type=thinking：模型的思考过程
  - content[].type=tool_use：**模型调用工具（这是实际操作）**
    - name: 工具名（Read, Write, Edit, Bash等）
    - input: 工具参数
- message (role=user)：系统响应
  - content[].type=tool_result：工具返回结果（紧随对应的tool_use）
    - content: 工具执行结果或错误信息
- error 事件：执行异常（如超时、权限错误）

**分析方法**（带着失分点这个具体问题去找证据）：

对于 automated 类检查点（如 file_created, data_accurate）：
- 去 transcript 找模型是否调用了相应工具
- 例如 file_created 失分 → 找是否有 Write/Edit 工具调用
- 如果没有对应工具调用 → 说明"该做却没做"
- 如果有工具调用但失败 → 找 tool_result 看错误信息

对于 llm_judge 类检查点（如 analysis_quality, completeness）：
- 多轮中哪些轮次这个点扣分了？
- 去对应轮次的 transcript 找模型的实际输出（type=text）
- 对比任务要求，看输出缺少了什么、哪里不对

**常见失分信号**：
- 只读不写：全是 Read 工具调用，无 Write/Edit
- 伪造工具调用：文本里说"我调用了XX工具"，但 transcript 里没有对应的 tool_use
- 过早结束：任务没完成就停止了
- 代码错误：Bash 执行 Python 脚本，tool_result 显示语法错误/NameError
- 数据计算错：读取数据后，在处理逻辑中出错（如排序方向错、聚合口径错）
- 任务串扰：Write 了其他任务的文件名
- 产物未落盘：分析过程看起来对，但最后的 Write 调用失败或根本没调用

### 第4步：引用裁判判词
每轮评分都有一个 notes 字段（裁判的文字判词）。如果 notes 有内容，引用其中的关键判词作为辅助证据。

### 第5步：输出分析结果（中文，结构化）

**result_analysis（800-1200字）**：
1. 任务概述（2-3句话）
2. 多轮表现对比（如果不一致）
3. 失分点逐条分析（每个失分检查点单独分析）
4. 引用裁判判词（如果有）

每个失分点必须包含：
- 检查点名称
- 要求是什么
- 实际做了什么（引用 transcript 证据）
- 为什么扣分

**root_cause_analysis（1-2句话，80-150字）**：
把多个失分点归纳到根本原因类别：
- 稳定性问题 / 产物未落盘 / 任务串扰
- 代码错误 / 数据计算错误 / 不回退知识库
- 幻觉编造 / 能力短板 / 环境限制
- 内容质量小瑕疵

格式：
- 第一句：直接点出核心问题类别和具体表现
- 第二句（可选）：补充关键细节
- 如果是环境问题，标注"非模型能力问题"
- 如果是高分(>0.85)，标注"本质高分，非能力短板"

## 注意事项
- 务必保证引用的 transcript 证据真实存在，不要编造
- 不要遗漏任何一个失分检查点
- 多轮不一致要分轮说明，不要混在一起
- 用具体的工具名、参数、返回值佐证，不要空泛描述`
}

phase('Analyze')

log(`开始分析 ${tasks.length} 个低分任务...`)

const results = await pipeline(
  tasks,
  (t) => agent(buildPrompt(t), {
    label: `${t.task_id.slice(0, 25)} (${t.min_score_pct}%)`,
    phase: 'Analyze',
    schema: SCHEMA
  })
)

const ok = results.filter(Boolean)
log(`✓ 完成分析 ${ok.length}/${tasks.length} 个任务`)

if (ok.length < tasks.length) {
  log(`⚠ ${tasks.length - ok.length} 个任务分析失败（agent 返回 null）`)
}

return ok
