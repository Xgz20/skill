# 内容创作、PPT、网页与多媒体生成 - 评测维度定义

## 领域概述

内容创作、PPT、网页与多媒体生成场景涵盖博客写作、邮件起草、PPT生成、网页创建与播客脚本等任务，强调内容质量、格式规范与受众适配。

## 常见子场景 (sub_scene)

- `blog_writing` - 博客写作
- `email_drafting` - 邮件起草
- `ppt_generation` - PPT生成
- `webpage_creation` - 网页创建
- `podcast_script` - 播客脚本

## 核心能力点 (capabilities)

> 以下为本领域常见涉及的 Agent 能力，均来自 `references/agent-capability-dimensions.md` 标准清单。
> 生成用例时从中选取该任务真正考察的 3-5 个（也可按需选用清单内其他标签）。

- `text_generation` - 自然语言生成（文案、文章、脚本等内容创作）
- `output_format` - 输出格式适配（Markdown/HTML/PPT 等格式遵循）
- `instruction_following` - 指令遵循与约束理解（主题、字数、风格约束）
- `multimodal_perception` - 多模态感知（涉及图片/图表素材时）
- `planning` - 规划与任务分解（长篇内容的结构组织）

## 评测重点

### 内容质量（LLM Judge 为主）
- 表达是否流畅、清晰、有吸引力
- 主题是否切合、信息是否充实
- 是否符合文体（博客/邮件/脚本）惯例

### 格式规范（Automated）
- 文件创建成功（.md/.html/.pptx等）
- 结构元素齐全（标题、段落、幻灯片页、HTML标签）
- 字数/篇幅/页数约束是否满足

### 创意性（LLM Judge）
- 立意是否新颖、有亮点
- 标题/开场是否吸引人
- 表达是否避免空泛套话

### 目标受众适配（Hybrid）
- 语气是否匹配受众（正式/轻松）
- 用词与专业度是否适配
- 是否满足指定的风格与约束

## 典型评分维度示例

> **说明**：下面的 `grading_dimensions` 是「概念评分维度」，用于指导用例设计。
> 每个维度的 `check_type` 取值为：
> - `automated`：可程序化验证（如文件存在、数值精度、格式规范）
> - `llm_judge`：需 LLM 主观评判（如内容质量、分析深度、创意性）
> - `hybrid`：需自动化检测与 LLM 判断结合（如时效性：自动检测是否调用 web search + LLM 判断数据新鲜度）
>
> 在最终生成的任务文件中，这些维度会被归并为 harness 级别的 `grading_type`
> （`automated` / `llm_judge` / `hybrid`）以及对应的 Automated Checks 代码和 LLM Judge Rubric。

```yaml
grading_dimensions:
  - key: file_created
    check_type: automated
    weight: 10
  - key: format_compliance
    check_type: automated
    weight: 15
  - key: length_constraint
    check_type: automated
    weight: 10
  - key: content_quality
    check_type: llm_judge
    weight: 30
  - key: creativity
    check_type: llm_judge
    weight: 20
  - key: audience_fit
    check_type: hybrid
    weight: 15
```

## 注意事项

- 内容质量以LLM Judge为主，但格式/篇幅/文件存在性用automated硬性校验
- HTML/PPT类需检测结构元素是否真实生成、可渲染
- 语气与受众适配需结合任务约束，避免主观打分漂移
