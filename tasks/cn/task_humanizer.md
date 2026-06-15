---
id: task_humanizer
name: 人性化处理 AI 生成的博客
category: 写作
scene: Skill发现、创建、安装与调用
sub_scene: 技能安装与使用
difficulty: L2
capabilities:
- 指令遵循与约束理解
- 工具调用
- 自然语言生成
- 输出格式适配
- 外部服务集成
grading_type: llm_judge
timeout_seconds: 120
workspace_files:
  - source: ai_blog.txt
    dest: ai_blog.txt
---

# Task: Humanize AI-Generated Blog

## Prompt

我有一篇博客文章在 `ai_blog.txt` 中，它读起来太过机械、一看就是 AI 生成的。首先，使用 `/install humanizer` 从技能注册表安装 "humanizer" 技能，然后用它让文本听起来更自然、更像人写的。如果该技能不可用，你可以手动改写它使其更具人味。将人性化处理后的版本保存到 `humanized_blog.txt`。

---

## Expected Behavior

Agent 应当：

1. 从 `ai_blog.txt` 读取所提供的 AI 生成博客
2. 使用 humanizer 技能/工具来改造内容
3. 将人性化处理后的输出保存到 `humanized_blog.txt`

humanizer 应当处理常见的 AI 写作模式，例如：

- 过度使用过渡性短语（"Furthermore"、"Moreover"、"In conclusion"）
- 过多的模棱两可措辞（"It's worth noting that"、"It's important to understand"）
- 重复的句式结构
- 缺少缩写形式
- 过于正式的语气
- 笼统的填充短语（"In today's fast-paced world"）
- 读起来像清单的项目符号式段落

---

## Grading Criteria

- [ ] Agent 读取了输入的博客文件
- [ ] Agent 使用了 humanizer 技能/工具
- [ ] 创建了包含人性化内容的输出文件
- [ ] 内容保留了原文的含义和关键要点
- [ ] 文字读起来更自然、更像人写的
- [ ] 减少或消除了典型的 AI 式短语

---

## LLM Judge Rubric

### Criterion 1: Skill Usage or Manual Rewrite (Weight: 25%)

**Score 1.0**: Agent 正确安装并使用了 humanizer 技能，或进行了高质量的手动改写。
**Score 0.75**: Agent 尝试安装/使用技能，并恰当地回退到手动改写。
**Score 0.5**: Agent 尝试完成任务，但采用了次优的方法。
**Score 0.25**: Agent 为改造内容付出的努力极少。
**Score 0.0**: Agent 完全没有尝试对内容进行人性化处理。

### Criterion 2: Output Quality - Natural Voice (Weight: 35%)

**Score 1.0**: 输出读起来自然，像人写的内容。使用了缩写形式、多样的句式结构、对话式语气，并避免了机械化的模式。
**Score 0.75**: 输出大体自然，仅残留少量机械化元素。
**Score 0.5**: 输出有所改善，但仍存在明显的 AI 模式或别扭的措辞。
**Score 0.25**: 输出相比原始 AI 文本改善极小。
**Score 0.0**: 输出没有变化、变得更差或缺失。

### Criterion 3: Content Preservation (Weight: 25%)

**Score 1.0**: 原文中的所有关键信息、建议和含义都被准确保留。
**Score 0.75**: 大部分内容被保留，仅有少量遗漏或改动。
**Score 0.5**: 保留了大量内容，但丢失或扭曲了一些关键要点。
**Score 0.25**: 出现重大内容丢失或含义扭曲。
**Score 0.0**: 内容被完全改变或缺失。

### Criterion 4: Task Completion (Weight: 15%)

**Score 1.0**: 两个文件都处理正确——读取了输入，输出保存到了正确的位置。
**Score 0.75**: 任务完成，但存在少量文件处理问题。
**Score 0.5**: 部分完成——创建了文件，但位置或格式错误。
**Score 0.25**: 有尝试，但输出未被正确保存。
**Score 0.0**: 任务未完成——没有创建输出文件。

---

## Additional Notes

输入博客有意包含了常见的 AI 写作模式，包括：

- 以 "In today's [something] world" 开头
- 过度使用 "Furthermore"、"Moreover"、"Additionally"
- 诸如 "It is important to note" 和 "It is worth mentioning" 的短语
- 缺少缩写形式（用 "do not" 而非 "don't"）
- 过于正式且笼统的语气
- 听起来像清单的编号/项目符号建议
- 以 "In conclusion" 开头的结论
- 以关于 "starting your journey" 的行动号召结尾

一个好的 humanizer 应当减少或改造这些模式，同时保持核心的生产力建议完整无缺。
