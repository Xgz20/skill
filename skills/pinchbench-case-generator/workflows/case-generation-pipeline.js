export const meta = {
  name: 'pinchbench-case-generator',
  description: '多Agent协作生成高质量PinchBench评测用例',
  phases: [
    { title: '需求分析', detail: '识别场景、技术维度和核心能力点' },
    { title: '多方案生成', detail: '从3个视角并行生成评测用例草稿' },
    { title: '评分择优', detail: '对草稿打分并选出最优方案' },
    { title: '评分逻辑生成', detail: '生成Automated Checks和LLM Judge Rubric' },
    { title: '对抗式质检', detail: '多维度验证用例质量' },
    { title: '最终组装', detail: '合并所有部分输出完整用例' }
  ]
}

// args: { query: string, language: 'zh'|'en', domainContext: string }

// ============ 阶段 1: 需求分析 ============
phase('需求分析')

const SCENE_OPTIONS = [
  'finance_investment_research', 'deep_research_report', 'science_tech_medical_qa',
  'data_retrieval_analysis', 'content_creation_multimedia', 'enterprise_product_intel',
  'skill_lifecycle', 'local_env_scripting'
]

const CATEGORY_OPTIONS = [
  'productivity', 'research', 'writing', 'coding', 'analysis',
  'csv_analysis', 'log_analysis', 'meeting_analysis', 'memory', 'skills', 'integrations'
]

const analysis = await agent(
  `分析用户Query并识别评测用例元信息。

Query: ${args.query}
语言: ${args.language}
领域上下文: ${args.domainContext}

任务：
1. 识别scene（从以下枚举中选一）：${SCENE_OPTIONS.join(', ')}
2. 识别sub_scene（具体子场景，用英文snake_case，如realtime_quote_lookup）
3. 识别category（技术维度）：${CATEGORY_OPTIONS.join(', ')}
4. 识别grading_type：
   - automated: 输出确定性强
   - llm_judge: 输出开放式
   - hybrid: 结合两者（推荐）
5. 提取capabilities（核心能力点，3-5个，用英文snake_case）
6. 建议timeout_seconds（考虑任务复杂度，默认180）

输出语言必须与Query语言一致（${args.language === 'zh' ? '中文' : '英文'}）。`,
  {
    phase: '需求分析',
    schema: {
      type: 'object',
      properties: {
        scene: { type: 'string', enum: SCENE_OPTIONS },
        sub_scene: { type: 'string', pattern: '^[a-z_]+$' },
        category: { type: 'string', enum: CATEGORY_OPTIONS },
        grading_type: { type: 'string', enum: ['automated', 'llm_judge', 'hybrid'] },
        capabilities: {
          type: 'array',
          items: { type: 'string', pattern: '^[a-z_]+$' },
          minItems: 3, maxItems: 5
        },
        suggested_timeout: { type: 'number', minimum: 60, maximum: 600 }
      },
      required: ['scene', 'sub_scene', 'category', 'grading_type', 'capabilities', 'suggested_timeout']
    }
  }
)

log(`场景识别: ${analysis.scene} / ${analysis.sub_scene}`)
log(`技术分类: ${analysis.category}, 评分类型: ${analysis.grading_type}`)

// ============ 阶段 2: 多方案生成 ============
phase('多方案生成')

const perspectives = [
  { key: 'strict', name: '严格评分视角', focus: '可验证性优先。评分标准明确无歧义。' },
  { key: 'coverage', name: '覆盖度视角', focus: '边界情况和失败模式优先。' },
  { key: 'realistic', name: '真实场景视角', focus: '贴近真实用户使用场景。' }
]

const drafts = await parallel(perspectives.map(p => () =>
  agent(
    `从"${p.name}"生成评测用例草稿。

Query: ${args.query}
元信息: scene=${analysis.scene}, sub_scene=${analysis.sub_scene}, category=${analysis.category}, grading_type=${analysis.grading_type}

${p.focus}

生成完整草稿（用${args.language === 'zh' ? '中文' : '英文'}）：
1. task_name: 语义化英文ID（snake_case）
2. name: 用例显示名称
3. prompt: 发给Agent的完整指令
4. expected_behavior: 预期行为描述（200-400字）
5. grading_criteria: 评分标准列表（6-10项）
6. grading_dimensions: [{key, description, weight, check_type: "automated"|"llm"}]`,
    {
      label: p.key,
      phase: '多方案生成',
      schema: {
        type: 'object',
        properties: {
          task_name: { type: 'string', pattern: '^[a-z_]+$' },
          name: { type: 'string' },
          prompt: { type: 'string', minLength: 50 },
          expected_behavior: { type: 'string', minLength: 100 },
          grading_criteria: { type: 'array', items: { type: 'string' }, minItems: 6, maxItems: 12 },
          grading_dimensions: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                key: { type: 'string', pattern: '^[a-z_]+$' },
                description: { type: 'string' },
                weight: { type: 'number', minimum: 5, maximum: 50 },
                check_type: { type: 'string', enum: ['automated', 'llm'] }
              },
              required: ['key', 'description', 'weight', 'check_type']
            },
            minItems: 4
          }
        },
        required: ['task_name', 'name', 'prompt', 'expected_behavior', 'grading_criteria', 'grading_dimensions']
      }
    }
  )
))

const validDrafts = drafts.filter(Boolean)
if (validDrafts.length === 0) throw new Error('所有草稿生成失败')
log(`生成了${validDrafts.length}份草稿`)

// ============ 阶段 3: 评分择优 ============
phase('评分择优')

const scores = await parallel(validDrafts.map((draft, i) => () =>
  agent(
    `评分此评测用例草稿（0-10分）。草稿${i+1}: ${JSON.stringify(draft, null, 2)}
评分维度：清晰度(3分)、评分标准合理性(3分)、真实性(2分)、完整性(2分)`,
    {
      label: `评分:草稿${i+1}`,
      phase: '评分择优',
      schema: {
        type: 'object',
        properties: {
          score: { type: 'number', minimum: 0, maximum: 10 },
          strengths: { type: 'array', items: { type: 'string' }, minItems: 2 },
          weaknesses: { type: 'array', items: { type: 'string' } }
        },
        required: ['score', 'strengths', 'weaknesses']
      }
    }
  )
))

const ranked = validDrafts.map((d, i) => ({ draft: d, score: scores[i]?.score || 0 })).sort((a, b) => b.score - a.score)
const bestDraft = ranked[0].draft
const bestScore = ranked[0].score
log(`最优草稿: "${bestDraft.name}" (${bestScore.toFixed(1)}/10分)`)

// ============ 阶段 4: 评分逻辑生成 ============
phase('评分逻辑生成')

const needsAutomated = ['automated', 'hybrid'].includes(analysis.grading_type)
const needsLLMJudge = ['llm_judge', 'hybrid'].includes(analysis.grading_type)
const automatedDims = bestDraft.grading_dimensions.filter(d => d.check_type === 'automated')
const llmDims = bestDraft.grading_dimensions.filter(d => d.check_type === 'llm')

const gradingTasks = []
if (needsAutomated && automatedDims.length > 0) gradingTasks.push({ type: 'automated', dims: automatedDims })
if (needsLLMJudge && llmDims.length > 0) gradingTasks.push({ type: 'llm_judge', dims: llmDims })

const gradingLogic = await pipeline(
  gradingTasks,
  task => agent(
    task.type === 'automated' ?
      `生成Automated Checks Python代码。用例: ${bestDraft.name}, 维度: ${task.dims.map(d => d.key).join(', ')}
要求：返回完整grade()函数，签名def grade(transcript: list, workspace_path: str) -> dict，只用stdlib` :
      `生成LLM Judge Rubric。用例: ${bestDraft.name}, 维度: ${task.dims.map(d => `${d.key}(${d.weight}%)`).join(', ')}
要求：Markdown格式，每个维度5档评分（1.0/0.75/0.5/0.25/0.0），权重总和=100%`,
    {
      label: task.type,
      phase: '评分逻辑生成',
      schema: task.type === 'automated' ? {
        type: 'object',
        properties: {
          code: { type: 'string', minLength: 200 },
          explanation: { type: 'string' }
        },
        required: ['code']
      } : {
        type: 'object',
        properties: {
          rubric: { type: 'string', minLength: 300 },
          dimensions_summary: { type: 'array', items: { type: 'object', properties: { name: {type: 'string'}, weight: {type: 'number'} } } }
        },
        required: ['rubric', 'dimensions_summary']
      }
    }
  ),
  (result, task) => {
    if (task.type === 'automated') {
      return agent(`检查此Python代码语法是否正确：\n\`\`\`python\n${result.code}\n\`\`\`\n如果有错返回修复后的代码`, {
        label: '验证:Python', phase: '评分逻辑生成',
        schema: { type: 'object', properties: { has_issues: {type: 'boolean'}, fixed_code: {type: 'string'} }, required: ['has_issues'] }
      }).then(check => check.has_issues ? { code: check.fixed_code } : result)
    } else {
      const totalWeight = result.dimensions_summary.reduce((sum, d) => sum + d.weight, 0)
      if (Math.abs(totalWeight - 100) > 0.01) {
        log(`权重总和${totalWeight.toFixed(1)}%，调整为100%`)
        const factor = 100 / totalWeight
        result.dimensions_summary.forEach(d => { d.weight = Math.round(d.weight * factor * 10) / 10 })
      }
      return result
    }
  }
)

const automatedChecks = gradingLogic.find(g => g?.code)
const llmJudgeRubric = gradingLogic.find(g => g?.rubric)
log(`评分逻辑生成完成: ${automatedChecks ? 'Automated✓' : ''} ${llmJudgeRubric ? 'LLMJudge✓' : ''}`)

// ============ 阶段 5: 对抗式质检 ============
phase('对抗式质检')

const critics = [
  { key: 'prompt_ambiguity', prompt: `对此Prompt进行对抗式检查："${bestDraft.prompt}" 是否有歧义或缺失信息？默认假设有问题。` },
  { key: 'python_executable', prompt: automatedChecks ? `检查此Python代码：\`\`\`python\n${automatedChecks.code}\n\`\`\`\n是否有语法错误、库依赖问题？` : null },
  { key: 'criteria_coverage', prompt: `核心能力: ${analysis.capabilities.join(', ')}, 评分维度: ${bestDraft.grading_dimensions.map(d => d.key).join(', ')}。每个核心能力是否都有对应维度？` },
  { key: 'edge_cases', prompt: `任务: ${bestDraft.prompt}。列举5个边界情况，检查当前评分标准能否识别。` }
]

const validCritics = critics.filter(c => c.prompt !== null)

const critiques = await pipeline(
  validCritics,
  c => agent(c.prompt, {
    label: c.key, phase: '对抗式质检',
    schema: {
      type: 'object',
      properties: {
        hasIssues: { type: 'boolean' },
        issues: { type: 'array', items: { type: 'string' }, minItems: 1 },
        severity: { type: 'string', enum: ['critical', 'moderate', 'minor'] },
        suggestions: { type: 'array', items: { type: 'string' } }
      },
      required: ['hasIssues', 'issues', 'severity']
    }
  })
)

const validCritiques = critiques.filter(Boolean)
const criticalIssues = validCritiques.filter(c => c.hasIssues && c.severity === 'critical')
log(`质检完成: ${criticalIssues.length}个严重问题`)
const needsReview = criticalIssues.length > 0

// ============ 阶段 6: 最终组装 ============
phase('最终组装')

return {
  frontmatter: {
    name: bestDraft.name,
    category: analysis.category,
    scene: analysis.scene,
    sub_scene: analysis.sub_scene,
    source: 'astronclaw',
    grading_type: analysis.grading_type,
    timeout_seconds: analysis.suggested_timeout,
    capabilities: analysis.capabilities,
    workspace_files: []
  },
  sections: {
    prompt: bestDraft.prompt,
    expected_behavior: bestDraft.expected_behavior,
    grading_criteria: bestDraft.grading_criteria,
    automated_checks: automatedChecks?.code || null,
    llm_judge_rubric: llmJudgeRubric?.rubric || null
  },
  metadata: {
    task_name_suggestion: bestDraft.task_name,
    language: args.language,
    quality_report: {
      best_draft_score: bestScore,
      critiques: critiques.filter(Boolean).map((c, i) => ({
        key: validCritics[i].key,
        severity: c.severity,
        issues: c.issues
      })),
      needs_review: needsReview,
      review_reason: needsReview ? `发现${criticalIssues.length}个严重问题` : null
    }
  }
}
