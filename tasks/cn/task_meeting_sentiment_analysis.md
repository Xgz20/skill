---
id: task_meeting_sentiment_analysis
name: 会议情感分析
category: 会议分析
scene: 内容创作、PPT、网页与多媒体生成
sub_scene: 会议情感分析
difficulty: L2
capabilities:
- 指令遵循与约束理解
- 数据提取与处理
- 多步推理
- 自然语言生成
- 输出格式适配
grading_type: hybrid
timeout_seconds: 180
grading_weights:
  automated: 0.5
  llm_judge: 0.5
workspace_files:
  - source: meetings/2021-06-28-gitlab-product-marketing-meeting.md
    dest: meeting_transcript.md
---

## Prompt

我有一个文件 `meeting_transcript.md`，包含 GitLab 产品营销团队会议的记录。请分析会议的整体情感和情绪动态。

将你的分析写入一个名为 `sentiment_analysis.md` 的文件。它应该包括：

- **会议整体情感**（积极、消极、混合），附简要理由
- **逐主题情感分解**：对于讨论的每个主要主题，评定情感（积极/中性/消极）并解释原因
- **团队动态观察**：注意一致、分歧、热情或挫折的时刻
- **值得注意的引用**：提取 3-5 条最能说明会议情绪基调的直接引用
- **参与程度**：评估参与者的投入程度（积极讨论 vs. 被动倾听）
- **潜在担忧**：识别参与者表达犹豫、不确定或反对的任何主题

---

## Expected Behavior

Agent 应该：

1. 阅读会议记录
2. 识别整体积极/协作的情感 — 团队总体上保持一致且高效
3. 分析每个主题的情感：
   - 企业活动：中性/略微不确定（等待 GTM 团队的反馈）
   - 产品公告：积极/热情（团队对汇总成果感到兴奋）
   - 竞争信息图：积极并带有轻微辩论（颜色选择、阶段名称的描述性）
   - 消息传递框架：高度投入、有趣（Talladega Nights 引用、关于标语的热烈辩论）
4. 注意具体动态：
   - 对"more speed, less risk"标语的热情
   - 有趣的玩笑（Ricky Bobby/NASCAR 引用、学校集会）
   - William 直率的"我爱它或恨它"风格
   - 对公司不够庆祝成果的轻微挫折感
   - Samia 对竞争对手电子表格方法论的建设性反对
5. 提取显示基调的相关引用
6. 评估整体高参与度

---

## Grading Criteria

- [ ] 创建了文件 `sentiment_analysis.md`
- [ ] 整体情感正确识别为积极/协作
- [ ] 至少分析了 3 个主题并给出各自的情感评定
- [ ] 包含团队动态或人际观察
- [ ] 包含记录中的至少 2 条直接引用
- [ ] 评估了参与程度
- [ ] 识别出至少一个担忧或不确定领域
- [ ] 分析区分了不同主题间的不同情绪基调

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the meeting sentiment analysis task.

    Args:
        transcript: Parsed JSONL transcript as list of dicts
        workspace_path: Path to the task's isolated workspace directory

    Returns:
        Dict mapping criterion names to scores (0.0 to 1.0)
    """
    from pathlib import Path
    import re

    scores = {}
    workspace = Path(workspace_path)

    # Check if report exists
    report_path = workspace / "sentiment_analysis.md"
    if not report_path.exists():
        alternatives = ["sentiment_report.md", "sentiment.md", "meeting_sentiment.md", "analysis.md"]
        for alt in alternatives:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "file_created": 0.0,
            "overall_sentiment": 0.0,
            "topic_breakdown": 0.0,
            "team_dynamics": 0.0,
            "quotes_included": 0.0,
            "engagement_assessed": 0.0,
            "concerns_identified": 0.0,
            "tonal_distinction": 0.0,
        }

    scores["file_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Overall sentiment (should be positive/collaborative)
    positive_patterns = [r'(?:overall|general).*(?:positive|collaborative|constructive|productive|upbeat|energetic)',
                         r'(?:positive|collaborative|constructive|productive).*(?:overall|tone|sentiment|atmosphere)']
    scores["overall_sentiment"] = 1.0 if any(re.search(p, content_lower) for p in positive_patterns) else 0.0

    # Topic-by-topic breakdown (at least 3 topics analyzed)
    topic_count = 0
    if re.search(r'(?:event|sponsor|re:?\s*invent|kubecon).*(?:sentiment|tone|feeling|positive|neutral|negative|uncertain)', content_lower):
        topic_count += 1
    if re.search(r'(?:product\s*announce|commit|feature|top\s*(?:5|five)).*(?:sentiment|tone|feeling|positive|neutral|negative|enthus)', content_lower):
        topic_count += 1
    if re.search(r'(?:infographic|competitive|comparison|design).*(?:sentiment|tone|feeling|positive|neutral|negative|debate)', content_lower):
        topic_count += 1
    if re.search(r'(?:messag|tagline|speed.*risk|source.*truth).*(?:sentiment|tone|feeling|positive|neutral|negative|engag|excit)', content_lower):
        topic_count += 1
    # Also accept if they just have 3+ subsections with sentiment words nearby
    if topic_count < 3:
        sections = re.findall(r'#{2,3}\s+[^\n]+', content)
        sentiment_words = len(re.findall(r'(?:positive|negative|neutral|mixed|enthusias|frustrat|uncertain|collaborat|engag)', content_lower))
        if len(sections) >= 4 and sentiment_words >= 5:
            topic_count = max(topic_count, 3)
    scores["topic_breakdown"] = 1.0 if topic_count >= 3 else (0.5 if topic_count >= 2 else 0.0)

    # Team dynamics observations
    dynamics_patterns = [
        r'(?:agreement|consensus|align)',
        r'(?:disagree|pushback|debate|tension)',
        r'(?:enthusiasm|excited|energy|passion)',
        r'(?:humor|joke|laugh|playful|banter)',
        r'(?:collaborat|team\s*work|support)',
    ]
    dynamics_count = sum(1 for p in dynamics_patterns if re.search(p, content_lower))
    scores["team_dynamics"] = 1.0 if dynamics_count >= 3 else (0.5 if dynamics_count >= 2 else 0.0)

    # Quotes included (look for quotation marks or attributed speech)
    quote_patterns = [
        r'[""“].{10,}[""”]',  # Quoted text
        r'(?:said|stated|mentioned|noted|commented)\s*[,:]?\s*[""“]',
        r'>\s*.{10,}',  # Blockquotes
    ]
    quote_matches = sum(len(re.findall(p, content)) for p in quote_patterns)
    scores["quotes_included"] = 1.0 if quote_matches >= 2 else (0.5 if quote_matches >= 1 else 0.0)

    # Engagement level assessed
    engagement_patterns = [
        r'engag(?:ed|ement|ing)',
        r'(?:active|lively)\s*(?:discussion|participat|debate)',
        r'(?:high|strong|good)\s*(?:engagement|participation|energy)',
        r'(?:participat\w+|contribut\w+).*(?:most|all|several|multiple)',
    ]
    scores["engagement_assessed"] = 1.0 if sum(1 for p in engagement_patterns if re.search(p, content_lower)) >= 2 else (
        0.5 if any(re.search(p, content_lower) for p in engagement_patterns) else 0.0)

    # Concerns identified
    concern_patterns = [
        r'(?:concern|hesitat|uncertain|frustrat|challenge|struggle)',
        r'(?:difficult|tough|hard)\s*(?:to|for)',
        r'(?:pushback|resist|reluctan)',
        r'(?:not\s*(?:sure|certain)|unclear)',
        r'(?:worry|worries|worried|anxious)',
    ]
    scores["concerns_identified"] = 1.0 if sum(1 for p in concern_patterns if re.search(p, content_lower)) >= 2 else (
        0.5 if any(re.search(p, content_lower) for p in concern_patterns) else 0.0)

    # Tonal distinction (different tones identified for different parts)
    tone_words = re.findall(r'(?:positive|negative|neutral|mixed|enthusias\w+|frustrat\w+|uncertain\w*|playful|serious|collaborative|tense|relaxed|energetic|subdued)', content_lower)
    unique_tones = set(tone_words)
    scores["tonal_distinction"] = 1.0 if len(unique_tones) >= 4 else (0.5 if len(unique_tones) >= 2 else 0.0)

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Analytical Depth (Weight: 35%)

**Score 1.0**: 分析超越表面的情感标签。识别整个会议中细微的情绪变化，解释为什么某些主题产生更多能量，并捕捉非正式但高效的动态。注意到 Talladega Nights 跑题等具体时刻作为团队融洽的证据。
**Score 0.75**: 良好的分析，有清晰的逐主题分解和一些细微差别。
**Score 0.5**: 分配了基本的情感标签，但解释或洞察有限。
**Score 0.25**: 肤浅的分析，主要是重述显而易见的观察。
**Score 0.0**: 未尝试有意义的分析。

### Criterion 2: Evidence-Based Observations (Weight: 30%)

**Score 1.0**: 主张由记录中的具体引用或时刻支持。在适当的情况下将情绪归属于特定的人（例如，William 对标语的强烈观点，Samia 对竞争对手的有条理的问题）。引用选择得当且有说明性。
**Score 0.75**: 大部分主张有证据支持，引用选择良好。
**Score 0.5**: 提供了一些证据，但许多主张是无支撑的断言。
**Score 0.25**: 很少或没有引用，主要是猜测。
**Score 0.0**: 未使用记录中的证据。

### Criterion 3: Practical Value (Weight: 35%)

**Score 1.0**: 分析提供团队负责人可以使用的可操作洞察 — 识别潜在的摩擦点、团队一致的领域、谁可能需要更多支持，以及哪些主题能激励团队。"担忧"部分标记出值得解决的真实问题。
**Score 0.75**: 大体可操作，对动态和担忧识别良好。
**Score 0.5**: 一些有用的观察，但主要是描述性而非可操作的。
**Score 0.25**: 实用价值有限；读起来更像读书报告而非有用的分析。
**Score 0.0**: 没有可操作的洞察。

---

## Additional Notes

此任务测试 Agent 的能力：

- 对非正式的对话文本进行细微的情感分析
- 区分单一文档中的不同情绪基调
- 从对话模式识别人际动态
- 提取有意义的引用作为证据
- 提供可操作的情绪智能洞察

记录以自然对话为特色，带有幽默、跑题和非正式语言，使其比正式的会议记录更具挑战性。Agent 必须在没有音频线索的情况下从文本解读基调。
