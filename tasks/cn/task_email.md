---
id: task_email
name: 专业邮件撰写
category: 写作
scene: 内容创作、PPT、网页与多媒体生成
sub_scene: 专业邮件撰写
difficulty: L1
capabilities:
- 指令遵循与约束理解
- 自然语言生成
- 输出格式适配
grading_type: llm_judge
timeout_seconds: 180
workspace_files: []
---

## Prompt

撰写一封因日程冲突而婉拒会议邀请的专业邮件。将其保存到 email_draft.txt。

## Expected Behavior

Agent 应当：

1. 创建一封结构得体的专业邮件
2. 包含关键要素：问候语、说明、婉拒、替代方案/致歉、结束语
3. 保持礼貌且专业的语气
4. 简洁但完整
5. 保存到名为 `email_draft.txt` 的文件中

这封邮件应当在明确表达婉拒的同时，维护积极的职业关系。

## Grading Criteria

- [ ] 已创建文件 `email_draft.txt`
- [ ] 邮件结构完整（问候语、正文、结束语）
- [ ] 明确婉拒会议邀请
- [ ] 提供理由（日程冲突）
- [ ] 保持专业且礼貌的语气
- [ ] 提供替代方案或表达改期意愿
- [ ] 包含得体的结束语
- [ ] 篇幅适中（既不过于简短，也不过于冗长）

## LLM Judge Rubric

### Criterion 1: Professional Tone and Courtesy (Weight: 30%)

**Score 1.0**: 语气始终专业、礼貌、得体。对婉拒表达了适当的歉意。聚焦于维护积极关系。没有过于随意或生硬的措辞。

**Score 0.75**: 总体专业且礼貌，存在轻微的语气问题。略显随意或正式，但仍然得体。

**Score 0.5**: 专业度尚可，但存在明显的语气问题。可能过于唐突、过度致歉，或前后不一致。

**Score 0.25**: 语气欠佳。过于随意、无礼，或不恰当地正式。缺乏礼貌。

**Score 0.0**: 完全不专业或内容缺失。

### Criterion 2: Completeness and Clarity (Weight: 25%)

**Score 1.0**: 邮件明确婉拒了会议，提供了理由（日程冲突），并提供了替代方案（改期、更换时间或其他解决方案）。信息明确无歧义。

**Score 0.75**: 邮件明确婉拒并给出理由。可能缺乏强有力的替代方案，但意图清晰。

**Score 0.5**: 邮件婉拒了会议，但理由或替代方案不够清晰。信息可能略有歧义。

**Score 0.25**: 邮件对婉拒表述不清，或缺少关键要素（理由或任何替代方案）。

**Score 0.0**: 邮件未能婉拒会议，或完全表述不清。

### Criterion 3: Structure and Format (Weight: 20%)

**Score 1.0**: 邮件结构完美，包含问候语（Dear/Hi [Name]）、清晰的正文段落，以及专业的结束语（Best regards、Sincerely 等）和署名行。组织良好。

**Score 0.75**: 结构良好，包含所有关键要素。存在轻微的格式问题。

**Score 0.5**: 基本结构尚可，但缺少要素（如缺少问候语或结束语）或组织欠佳。

**Score 0.25**: 结构欠佳。缺失多个要素或非常杂乱。

**Score 0.0**: 没有可辨识的邮件结构或内容缺失。

### Criterion 4: Conciseness and Appropriateness (Weight: 15%)

**Score 1.0**: 邮件长度适中（3-6 句话或 50-150 词）。在不冗余也不过度简略的情况下传达了所有必要信息。

**Score 0.75**: 长度良好（2-3 句或 6-8 句）。略显冗长或略显简短，但仍然有效。

**Score 0.5**: 过于简短（1-2 句）或过于冗长（超过 200 词）。仍可用但非最佳。

**Score 0.25**: 极度简短（单句）或极度冗长（超过 300 词）。平衡欠佳。

**Score 0.0**: 长度完全不当或内容缺失。

### Criterion 5: Task Completion (Weight: 10%)

**Score 1.0**: 创建了正确命名的文件（email_draft.txt），包含完整的邮件，满足所有要求。

**Score 0.75**: 文件已创建，存在轻微问题但基本完整。

**Score 0.5**: 文件已创建，但缺少重要要求。

**Score 0.25**: 文件已创建，但内容严重不足。

**Score 0.0**: 未创建文件或文件为空。
