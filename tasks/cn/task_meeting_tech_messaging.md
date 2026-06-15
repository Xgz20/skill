---
id: task_meeting_tech_messaging
name: 会议传播信息框架提取
category: 会议分析
scene: 内容创作、PPT、网页与多媒体生成
sub_scene: 会议传播信息提取
difficulty: L2
capabilities:
- 指令遵循与约束理解
- 数据提取与处理
- 自然语言生成
- 输出格式适配
grading_type: hybrid
timeout_seconds: 180
grading_weights:
  automated: 0.6
  llm_judge: 0.4
workspace_files:
  - source: meetings/2021-06-28-gitlab-product-marketing-meeting.md
    dest: meeting_transcript.md
---

## Prompt

我有一个文件 `meeting_transcript.md`，里面是 2021 年 6 月 28 日一次 GitLab 产品营销周会的逐字记录。在会议接近尾声时，团队做了一个协作式的传播信息练习，为 GitLab 拟定 slogan 和传播支柱（messaging pillar）。

请提取并整理会议中讨论过的所有传播信息框架方案，写入名为 `messaging_framework.md` 的文件。你的输出应包括：

1. **所有候选 slogan/短语**，按它们所属的传播支柱分组
2. 团队使用的**评估标准**（例如各短语之间语气的对称性、朗朗上口程度、名词短语 vs 动词短语）
3. 每个方案讨论过的**优缺点**
4. **最终选定项**（团队决定采用的方案）
5. **被否决的备选项**及被否决的原因

---

## Expected Behavior

Agent 应当：

1. 解析逐字记录，找到传播信息框架的讨论部分
2. 识别三个传播支柱及所有候选短语

关键传播信息内容：

**Pillar 1 — Transparency/Single Platform:**
- "From roadmap to company vision, we are transparent" (original)
- "A single source of truth, countless possibilities" (proposed, well-liked)
- "All-in-one for everyone" (proposed, William liked it but acknowledged not everyone's cup of tea)

**Pillar 2 — End-to-end control:**
- "Automate nearly anything, collaborate on everything" (original)
- "End to end control over your software factory" (proposed, described as less catchy but descriptive)

**Pillar 3 — Speed/Security:**
- "Scale up, speed up, test up" (original — William hated it, especially "test up")
- "Move fast with confidence" (proposed — liked the sentiment but poor parity with other noun phrases)
- "More speed less risk" (proposed — team consensus favorite)
- "Increase speed and stay on track" (proposed — not liked)
- "Velocity with confidence" (mentioned as a concept)
- "No trade-offs" (briefly entertained, rejected because engineer mindset says there's always trade-offs)
- "More speed less risk with confidence" (suggested combination)

**Evaluation criteria discussed:**
- Parity of tone (noun phrases should match noun phrases)
- Catchiness/pithiness
- Technical accuracy (no absolute claims like "no trade-offs" or "100% secure")
- Ability to use in parallel construction ("With GitLab you get X")

**Final selections:**
- "A single source of truth, countless possibilities"
- "End to end control over your software factory"
- "More speed less risk"

**Security sub-tagline:**
- "Secure the factory and its deliverables" (credited to Cindy's blog post)

---

## Grading Criteria

- [ ] 创建了文件 `messaging_framework.md`
- [ ] 识别出全部三个传播支柱
- [ ] 每个支柱下列出了多个候选短语
- [ ] 将 "More speed less risk" 识别为 speed/security 支柱选定的 slogan
- [ ] 将 "A single source of truth, countless possibilities" 识别为 transparency 支柱的选定项
- [ ] 列出了被否决的备选项及原因（例如 "test up" 被否决、"no trade-offs" 被否决）
- [ ] 捕捉到了评估标准（对称性/语气、朗朗上口、准确性）
- [ ] 捕捉到了安全子 slogan "Secure the factory and its deliverables"
- [ ] 最终选定项与备选项清晰区分

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the meeting messaging framework extraction task.

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

    report_path = workspace / "messaging_framework.md"
    if not report_path.exists():
        for alt in ["messaging.md", "framework.md", "taglines.md", "messaging_options.md"]:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "three_pillars": 0.0,
            "multiple_candidates": 0.0,
            "chosen_speed_tagline": 0.0,
            "chosen_transparency_tagline": 0.0,
            "rejected_alternatives": 0.0,
            "evaluation_criteria": 0.0,
            "security_subtagline": 0.0,
            "finals_distinguished": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Three pillars identified
    pillar_terms = [
        [r'(?:transparen|single\s*(?:source|platform)|all.in.one)'],
        [r'(?:end.to.end|control|automat)'],
        [r'(?:speed|security|risk|velocity|confidence)'],
    ]
    pillar_count = sum(1 for terms in pillar_terms if any(re.search(p, content_lower) for p in terms))
    scores["three_pillars"] = 1.0 if pillar_count >= 3 else (0.5 if pillar_count >= 2 else 0.0)

    # Multiple candidate phrases
    candidate_phrases = [
        r'single\s*source\s*of\s*truth',
        r'all.in.one\s*for\s*everyone',
        r'end\s*to\s*end\s*control',
        r'more\s*speed\s*less\s*risk',
        r'move\s*fast\s*with\s*confidence',
        r'scale\s*up.*speed\s*up.*test\s*up',
        r'no\s*trade.?offs?',
        r'automate\s*nearly\s*anything',
        r'countless\s*possibilities',
        r'velocity\s*with\s*confidence',
    ]
    phrase_count = sum(1 for p in candidate_phrases if re.search(p, content_lower))
    scores["multiple_candidates"] = 1.0 if phrase_count >= 6 else (0.75 if phrase_count >= 4 else (0.5 if phrase_count >= 3 else 0.0))

    # "More speed less risk" as chosen
    chosen_patterns = [
        r'more\s*speed\s*less\s*risk.*(?:chosen|selected|final|decided|winner|preferred|went\s*with)',
        r'(?:chosen|selected|final|decided|winner|preferred|went\s*with).*more\s*speed\s*less\s*risk',
        r'more\s*speed\s*less\s*risk',
    ]
    scores["chosen_speed_tagline"] = 1.0 if any(re.search(p, content_lower) for p in chosen_patterns[:2]) else (0.5 if re.search(chosen_patterns[2], content_lower) else 0.0)

    # "A single source of truth, countless possibilities" as chosen
    transparency_patterns = [
        r'single\s*source\s*of\s*truth.*countless\s*possibilities',
    ]
    scores["chosen_transparency_tagline"] = 1.0 if any(re.search(p, content_lower) for p in transparency_patterns) else 0.0

    # Rejected alternatives with reasons
    rejected_patterns = [
        r'(?:test\s*up|scale\s*up.*test\s*up).*(?:reject|hate|goofy|bad|dislike|didn.t\s*like)',
        r'(?:reject|hate|goofy|bad|dislike|didn.t\s*like).*(?:test\s*up|scale\s*up.*test\s*up)',
        r'no\s*trade.?offs?.*(?:reject|never|always|engineer)',
        r'(?:reject|never|always|engineer).*no\s*trade.?offs?',
    ]
    rejected_hits = sum(1 for p in rejected_patterns if re.search(p, content_lower))
    scores["rejected_alternatives"] = 1.0 if rejected_hits >= 2 else (0.5 if rejected_hits >= 1 else 0.0)

    # Evaluation criteria
    criteria_patterns = [
        r'(?:pari(?:ty|del)|tone|parallel)',
        r'(?:catch|pith|punch)',
        r'(?:noun\s*phrase|verb\s*phrase|construction)',
    ]
    criteria_hits = sum(1 for p in criteria_patterns if re.search(p, content_lower))
    scores["evaluation_criteria"] = 1.0 if criteria_hits >= 2 else (0.5 if criteria_hits >= 1 else 0.0)

    # Security sub-tagline
    security_patterns = [
        r'secure\s*the\s*factory.*deliverables',
    ]
    scores["security_subtagline"] = 1.0 if any(re.search(p, content_lower) for p in security_patterns) else 0.0

    # Finals clearly distinguished
    final_patterns = [
        r'(?:final|selected|chosen|decided|winner)',
        r'(?:reject|alternative|considered|discard)',
    ]
    final_hits = sum(1 for p in final_patterns if re.search(p, content_lower))
    scores["finals_distinguished"] = 1.0 if final_hits >= 2 else (0.5 if final_hits >= 1 else 0.0)

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Completeness of Options Captured (Weight: 30%)

**Score 1.0**：列出了全部三个支柱下提出的所有 slogan/短语，包括原版和备选版。至少捕捉到 8-10 个不同的短语，且支柱分组正确。
**Score 0.75**：捕捉到大部分短语且分组正确，遗漏一两个。
**Score 0.5**：捕捉到若干短语，但漏掉了整组备选项或某个支柱。
**Score 0.25**：只捕捉到最终选定项，没有备选项。
**Score 0.0**：未捕捉到任何有意义的方案。

### Criterion 2: Evaluation Criteria and Reasoning (Weight: 25%)

**Score 1.0**：准确捕捉到评估框架：语气的对称性、朗朗上口、技术准确性、可用于排比结构。包含对否决项的具体理由（例如 "test up" 听起来很傻、"no trade-offs" 与工程师思维相悖、"move fast with confidence" 缺乏名词短语的对称性）。
**Score 0.75**：捕捉到大部分评估标准并有较好的理由。
**Score 0.5**：提到一些标准，但理由不完整。
**Score 0.25**：提供的理由极少。
**Score 0.0**：没有评估标准或理由。

### Criterion 3: Final vs. Rejected Distinction (Weight: 25%)

**Score 1.0**：清晰地将最终选定项与被否决的备选项区分开。容易识别哪些被采用、哪些被舍弃。
**Score 0.75**：区分良好，仅有少量模糊。
**Score 0.5**：有一些区分，但读者需要自己推断哪些是最终项。
**Score 0.25**：所有方案混在一起，没有明确的结论。
**Score 0.0**：未做任何区分。

### Criterion 4: Nuance and Attribution (Weight: 20%)

**Score 1.0**：捕捉到谁提出了什么，包含对 "secure the factory and its deliverables" 来自 Cindy 博客文章的署名，注明了 Ash Withers 的启发，并反映出这个练习的协作动态。
**Score 0.75**：署名良好，仅有少量缺漏。
**Score 0.5**：有一些署名，但漏掉了关键贡献。
**Score 0.25**：未将想法归属到个人。
**Score 0.0**：没有细节或署名。
