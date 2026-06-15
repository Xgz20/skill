---
id: task_video_transcript_extraction
name: 视频字幕提取与摘要
category: 编程
scene: 内容创作、PPT、网页与多媒体生成
sub_scene: 视频字幕摘要
difficulty: L2
capabilities:
- 外部服务集成
- 数据提取与处理
- 自然语言生成
- 工具调用
- 输出格式适配
grading_type: llm_judge
timeout_seconds: 300
workspace_files: []
---

## Prompt

获取这个 YouTube 视频的字幕，并创建一份结构化摘要：

**Video:** https://www.youtube.com/watch?v=dQw4w9WgXcQ

从该视频中提取或下载字幕/subtitles。然后创建：

1. **Metadata**：标题、频道、时长、上传日期
2. **Full transcript**：将完整字幕保存到 `transcript.txt`
3. **Summary**：一段 200-300 词的视频内容摘要，保存到 `video_summary.md`
4. **Key points**：主要主题或要点的项目符号列表（放在摘要文件中）
5. **Timestamps**：值得关注的时刻及其时间戳（放在摘要文件中）

将完整字幕保存到 `transcript.txt`，将结构化摘要保存到 `video_summary.md`。

## Expected Behavior

Agent 应当：

1. 访问该 YouTube 视频以提取其字幕（通过 yt-dlp、YouTube API、网页抓取或字幕服务）
2. 将字幕解析为干净、可读的文本
3. 创建一份结构良好的摘要文档
4. 识别关键要点和值得关注的时间戳
5. 同时保存原始字幕和摘要

Agent 可以采用多种方法：
- `yt-dlp --write-auto-sub` 下载字幕
- YouTube 字幕 API 或服务
- 通过 web fetch 访问字幕数据
- 任何其他能够生成字幕文本的方法

## Grading Criteria

- [ ] 创建了包含字幕内容的 `transcript.txt`
- [ ] 创建了包含摘要的 `video_summary.md`
- [ ] 包含视频元数据（标题、频道）
- [ ] 摘要为 200-300 词
- [ ] 列出了关键要点 / takeaways
- [ ] 引用了时间戳
- [ ] 字幕文本可读（不是带时间码的原始 SRT）

## LLM Judge Rubric

### Criterion 1: Transcript Extraction (Weight: 30%)

**Score 1.0**: 完整提取了字幕并保存为干净、可读的文本。时间码已去除或格式整洁。文本自然流畅，准确捕捉了视频的口述内容。
**Score 0.75**: 提取了字幕，仅有小的格式问题。捕捉了大部分内容。
**Score 0.5**: 仅获得部分字幕，或存在明显格式问题（原始 SRT 数据、重复行）。
**Score 0.25**: 仅提取了极少的字幕内容。
**Score 0.0**: 未获得任何字幕。

### Criterion 2: Summary Quality (Weight: 25%)

**Score 1.0**: 摘要以 200-300 词准确捕捉了视频的主要内容。撰写良好、信息丰富，无需观看即可让读者了解视频内容。
**Score 0.75**: 良好的摘要，涵盖了要点。词数可能略微超出范围。
**Score 0.5**: 摘要尚可，但遗漏了关键要点，或过于简短/冗长。
**Score 0.25**: 摘要非常单薄或大体不准确。
**Score 0.0**: 未创建摘要。

### Criterion 3: Structure and Metadata (Weight: 20%)

**Score 1.0**: 摘要文件结构良好，元数据、摘要、关键要点和时间戳各有清晰的章节。视频标题、频道和时长被正确识别。
**Score 0.75**: 结构良好，包含大部分元数据。有小的组织问题。
**Score 0.5**: 有基本结构，但缺少某些元数据或章节。
**Score 0.25**: 组织较差，元数据极少。
**Score 0.0**: 没有结构。

### Criterion 4: Key Points and Timestamps (Weight: 15%)

**Score 1.0**: 关键要点有洞察力，准确反映了视频内容。时间戳对应视频中的实际时刻，便于导航。
**Score 0.75**: 良好的关键要点，时间戳大体准确。
**Score 0.5**: 列出了关键要点但较为笼统，或时间戳不准确。
**Score 0.25**: 关键要点极少，无时间戳。
**Score 0.0**: 既无关键要点也无时间戳。

### Criterion 5: Technical Execution (Weight: 10%)

**Score 1.0**: Agent 使用合适的工具高效提取了字幕。执行干净利落，没有不必要的重试或失败。
**Score 0.75**: 提取字幕时遇到小困难，但最终成功。
**Score 0.5**: 需要多次尝试或变通方法，但最终成功。
**Score 0.25**: 遇到重大困难，部分成功。
**Score 0.0**: 未能提取字幕。

## Additional Notes

- 选择此视频 URL（Rick Astley - Never Gonna Give You Up）是因为它是最知名的 YouTube 视频之一，可确保长期可用并具备字幕/transcripts。
- 本任务考察 Agent 与外部服务（YouTube）交互以及处理媒体内容的能力。
- Agent 可使用多种工具：yt-dlp、web fetch、YouTube API 或浏览器自动化。所有方法均有效。
- 摘要质量比提取方法更重要——只能获取部分字幕但写出优秀摘要的 Agent 在整体上仍应获得较好分数。
