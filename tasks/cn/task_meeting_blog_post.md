---
id: task_meeting_blog_post
name: 会议转化为博客文章
category: 会议分析
scene: 内容创作、PPT、网页与多媒体生成
sub_scene: 会议转化为博客文章
difficulty: L2
capabilities:
- 自然语言生成
- 指令遵循与约束理解
- 数据提取与处理
- 输出格式适配
grading_type: hybrid
timeout_seconds: 180
grading_weights:
  automated: 0.4
  llm_judge: 0.6
workspace_files:
  - source: meetings/2021-06-28-gitlab-product-marketing-meeting.md
    dest: meeting_transcript.md
---

## Prompt

我有一个文件 `meeting_transcript.md`，其中包含 GitLab 产品营销团队于 2021-06-28 召开的一次会议记录。团队讨论了他们如何处理产品发布公告、竞争定位和信息传递。

请以这次会议作为素材，撰写一篇博客文章，探讨当一家公司以增量方式发布（持续交付/开源模式）而非进行"大爆炸式"发布时，产品营销团队如何才能有效地传达产品发布。

请将博客文章写入名为 `blog_post.md` 的文件。要求：

- **标题**：拟定一个引人入胜的标题
- **篇幅**：600-1000 字（英文单词）
- **受众**：产品营销专业人士和 DevOps 从业者
- **切入角度**：从会议中关于"当路线图公开、功能以 MVC/迭代方式发布时如何做公告"这一挑战的讨论中汲取洞见
- **包含**：至少 2-3 条其他团队可借鉴的具体策略或经验
- **语气**：信息丰富且实用，而非会议复盘

这篇文章应当作为一篇独立的博客文章来阅读，而非会议总结。请将会议内容作为灵感和素材来源，但撰写原创内容。

---

## Expected Behavior

Agent 应当：

1. 阅读会议记录
2. 识别关键洞见：GitLab 持续发布并公开路线图，这使得传统的"发布"公告变得困难
3. 提取讨论中的策略：
   - 将小型 MVC 打包成更大的叙事主题（例如"漏洞管理"涵盖众多小型发布）
   - 回顾过去一年，识别哪些功能现在已"达到 GA 就绪"，即便其各个部分此前已发布
   - 使用兴奋度/排序来确定优先突出哪些内容
   - 创建叙事桶（UX 改进、GitOps 能力、安全性），将多个功能打包
   - 围绕活动（Commit 大会）安排公告时机以获得媒体关注
   - 以积极方式表述改进（"新能力"而非"我们修复了原本损坏的东西"）
4. 撰写一篇将这些内容概括为可操作建议的博客文章
5. 保持适合营销/DevOps 受众的专业、信息丰富的语气

---

## Grading Criteria

- [ ] 创建了文件 `blog_post.md`
- [ ] 拥有引人入胜的标题（而非"会议总结"之类）
- [ ] 阐述了持续交付模式下做公告的核心挑战
- [ ] 包含至少 2 条具体策略或建议
- [ ] 作为一篇独立博客文章来阅读（而非会议复盘）
- [ ] 篇幅适当（400-1200 字）
- [ ] 面向目标受众撰写（产品营销/DevOps）
- [ ] 专业且信息丰富的语气

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the meeting-to-blog-post task.

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

    # Check if file exists
    report_path = workspace / "blog_post.md"
    if not report_path.exists():
        alternatives = ["blog.md", "post.md", "article.md", "blogpost.md"]
        for alt in alternatives:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "file_created": 0.0,
            "has_title": 0.0,
            "core_challenge": 0.0,
            "strategies_present": 0.0,
            "standalone_post": 0.0,
            "appropriate_length": 0.0,
            "target_audience": 0.0,
            "professional_tone": 0.0,
        }

    scores["file_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()
    word_count = len(content.split())

    # Has a title (first heading)
    title_match = re.search(r'^#\s+(.+)', content, re.MULTILINE)
    if title_match:
        title = title_match.group(1).lower()
        # Title shouldn't be generic "meeting summary" type
        is_meeting_recap = bool(re.search(r'(?:meeting\s*(?:summary|recap|notes|minutes))', title))
        scores["has_title"] = 0.0 if is_meeting_recap else 1.0
    else:
        scores["has_title"] = 0.0

    # Core challenge addressed (continuous delivery + announcements)
    challenge_patterns = [
        r'(?:continuous|incremental|iterati).*(?:deliver|ship|release|deploy)',
        r'(?:ship|release|deploy).*(?:continuous|incremental|small|iterati)',
        r'(?:public\s*roadmap|open\s*source).*(?:announce|launch|market)',
        r'(?:mvc|minimum\s*viable)',
        r'(?:big[\s-]*bang|traditional).*(?:launch|release|announce)',
        r'(?:announce|launch|market).*(?:difficult|challenge|tough|hard).*(?:continuous|incremental|open)',
    ]
    scores["core_challenge"] = 1.0 if sum(1 for p in challenge_patterns if re.search(p, content_lower)) >= 2 else (
        0.5 if any(re.search(p, content_lower) for p in challenge_patterns) else 0.0)

    # Strategies present (at least 2 concrete recommendations)
    strategy_count = 0
    if re.search(r'(?:bundl|group|aggregat|roll[\s-]*up|bucket)', content_lower):
        strategy_count += 1
    if re.search(r'(?:look\s*back|retrospect|year\s*in\s*review|maturity|ga[\s-]*ready)', content_lower):
        strategy_count += 1
    if re.search(r'(?:prioriti|rank|stack[\s-]*rank|excitement|top\s*(?:5|five))', content_lower):
        strategy_count += 1
    if re.search(r'(?:narrative|theme|story|bucket|categor)', content_lower):
        strategy_count += 1
    if re.search(r'(?:event|conference|keynote|commit).*(?:timing|press|announce)', content_lower):
        strategy_count += 1
    if re.search(r'(?:frame|position|spin|messag).*(?:positive|improvement|capabilit)', content_lower):
        strategy_count += 1
    scores["strategies_present"] = 1.0 if strategy_count >= 3 else (0.5 if strategy_count >= 2 else 0.0)

    # Standalone post (should NOT read like a meeting recap)
    recap_signals = [
        r'in\s*the\s*meeting',
        r'(?:attendees|participants)\s*(?:discussed|talked)',
        r'the\s*team\s*(?:then|next)\s*(?:discussed|moved)',
        r'meeting\s*(?:minutes|notes|recap|summary)',
    ]
    recap_count = sum(1 for p in recap_signals if re.search(p, content_lower))
    scores["standalone_post"] = 1.0 if recap_count == 0 else (0.5 if recap_count <= 1 else 0.0)

    # Appropriate length (600-1000 target, 400-1200 acceptable)
    if 600 <= word_count <= 1000:
        scores["appropriate_length"] = 1.0
    elif 400 <= word_count <= 1200:
        scores["appropriate_length"] = 0.5
    else:
        scores["appropriate_length"] = 0.0

    # Target audience (product marketing / DevOps terms)
    audience_terms = [
        r'product\s*market', r'devops', r'(?:launch|release)\s*(?:strategy|plan)',
        r'go[\s-]*to[\s-]*market', r'press', r'pr\s*team',
        r'(?:ci|cd|ci/cd)', r'devsecops', r'(?:feature|product)\s*launch',
    ]
    audience_score = sum(1 for p in audience_terms if re.search(p, content_lower))
    scores["target_audience"] = 1.0 if audience_score >= 3 else (0.5 if audience_score >= 1 else 0.0)

    # Professional tone (no casual meeting language)
    casual_signals = [r'um\b', r'uh\b', r'like\s+you\s+know', r'et\s+cetera', r'yada']
    casual_count = sum(1 for p in casual_signals if re.search(p, content_lower))
    has_structure = len(re.findall(r'^#{1,3}\s+', content, re.MULTILINE)) >= 2
    scores["professional_tone"] = 1.0 if (casual_count == 0 and has_structure) else (
        0.5 if casual_count <= 1 else 0.0)

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Content Quality and Insight (Weight: 40%)

**Score 1.0**：博客文章从会议中提取出真正有用的洞见，并将其呈现为可操作的建议。策略具体（将 MVC 打包成主题、利用成熟度里程碑、由活动驱动的时机安排），并辅以推理。产品营销专业人士能从中学到有用的东西。
**Score 0.75**：洞见良好，建议扎实，在深度或具体性上仅有少量缺口。
**Score 0.5**：有一些有用内容，但大多停留在表面，或是未扎根于素材的通用营销建议。
**Score 0.25**：洞见单薄，大多为泛泛之谈。
**Score 0.0**：无有意义内容，或只是会议复盘。

### Criterion 2: Writing Quality (Weight: 35%)

**Score 1.0**：读起来像一篇出自营销刊物的精炼博客文章。拥有引人入胜的开篇、逻辑流畅、结构清晰、结尾有力。使用具体示例，而不像会议记录。适合目标受众，又不堆砌行话。
**Score 0.75**：写作良好，结构出色，仅有少量瑕疵。
**Score 0.5**：可读，但感觉像草稿——结构或行文有待打磨。
**Score 0.25**：写作较差，难以理解，或语气不当。
**Score 0.0**：无法辨认为博客文章。

### Criterion 3: Originality and Transformation (Weight: 25%)

**Score 1.0**：成功将内部会议讨论转化为普遍适用的内容。会议是素材来源，而非主题本身。读者不会知道这源自某次具体的会议记录。补充了使建议具有广泛相关性的背景和框架。
**Score 0.75**：大体原创，概括良好，偶有可进一步打磨的会议特定引用。
**Score 0.5**：部分转化，但仍有些像会议复盘，或过于针对 GitLab。
**Score 0.25**：几乎未转化——大多描述会议中发生了什么。
**Score 0.0**：只是贴了"博客文章"标签的会议总结。

---

## Additional Notes

本任务测试 Agent 的以下能力：

- 将原始的内部讨论转化为精炼的对外内容
- 从具体情境中识别可概括的洞见
- 面向与会议参与者不同的目标受众进行写作
- 创作以素材为依托的原创内容
- 为博客文章保持适当的范围和语气

关键挑战在于转化：会议中充满了 GitLab 特定的行话、内部流程细节和随意的对话。Agent 必须提取出普遍适用的经验，并以对任何采用持续交付的产品营销团队都有用的方式呈现出来。
