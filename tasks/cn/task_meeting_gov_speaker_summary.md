---
id: task_meeting_gov_speaker_summary
name: NASA UAP 听证会发言者摘要
category: 会议分析
scene: 内容创作、PPT、网页与多媒体生成
sub_scene: 会议记录发言者摘要
difficulty: L2
capabilities:
- 数据提取与处理
- 自然语言生成
- 指令遵循与约束理解
- 输出格式适配
grading_type: hybrid
timeout_seconds: 180
grading_weights:
  automated: 0.5
  llm_judge: 0.5
workspace_files:
  - source: meetings/2025-07-30-nasa-holds-first-public-meeting-on-ufos-transcript.md
    dest: transcript.md
---

## Prompt

我有一个文件 `transcript.md`，这是 NASA 首次关于不明异常现象（UAP/UFO）公开会议的记录。这是 NASA 的 UAP 独立研究团队根据《联邦咨询委员会法案》（FACA）召开的审议会议。

请阅读记录并生成一个名为 `speaker_summary.md` 的文件，总结每位发言者的关键观点。对于每位做了实质性演讲或发言的发言者，包括：

- **发言者姓名和角色/隶属关系**（如果提及）
- **关键观点**（项目符号列表）
- **值得注意的引用**（1-2 条捕捉其主要信息的直接引用）

按发言者出现的顺序组织。将次要插话或简短的程序性评论归入"Panel Q&A Contributions"部分，而不是给它们完整的条目。专注于做了演讲或实质性发言的发言者。

---

## Expected Behavior

Agent 应该：

1. 阅读并解析完整记录
2. 识别主要发言者：Dan Evans（NASA，指定联邦官员）、Nicola Fox（NASA 副署长）、David Spergel（小组主席，宇宙学家）、Sean Kirkpatrick（AARO 主任）、Mike Freie（FAA）、Nadia Drake（科学记者）、Paula Bontempi（地球科学家）、Federica Bianco（天体物理学家/数据科学家）、David Grinspoon（行星科学家/天体生物学家）等
3. 准确总结每位发言者的关键观点
4. 包含值得注意的直接引用
5. 编写结构良好的 markdown 文件

关键发言者及其主要观点：

- **Dan Evans**：开场会议，谈及小组成员遭受的骚扰，解释 FACA 合规性，描述 UAP 研究目的
- **Nicola Fox**：强调数据质量限制，解释分类与非分类数据的区别（战斗机/自由女神像类比），推广开放数据
- **David Spergel**：需要高质量校准数据，快速射电暴类比，异常作为发现的引擎，公民科学机会
- **Sean Kirkpatrick**：AARO 的 800+ 案例，2-5% 真正异常，展示解密录像，描述传感器校准需求，推荐众包和地基仪器
- **Mike Freie**：FAA 监视能力和限制，雷达覆盖图，管制员每月 3-5 份 UAP 报告，过滤技术
- **Nadia Drake**：界定 UAP 问题，"大海捞针中的细针"，没有地外起源的确凿证据
- **Paula Bontempi**：NASA 的独特角色 — 60 年经验、开放数据、公众信任、跨学科团队
- **Federica Bianco**：数据标准（FAIR）、异常检测方法、众包平台建议、机器学习就绪性
- **David Grinspoon**：技术信号、天体生物学联系、与 UAP 相关的地球以外观测

---

## Grading Criteria

- [ ] 创建了输出文件 `speaker_summary.md`
- [ ] 识别并总结了 Dan Evans 的关键观点（开场发言、骚扰问题、FACA 合规性）
- [ ] 识别并总结了 Nicola Fox 的关键观点（数据质量、分类与非分类的区别）
- [ ] 识别并总结了 David Spergel 的关键观点（需要校准数据、小组主席角色）
- [ ] 识别并总结了 Sean Kirkpatrick 的关键观点（AARO 数据、800+ 案例、2-5% 异常）
- [ ] 识别并总结了 Mike Freie / FAA 的关键观点（监视能力、雷达覆盖）
- [ ] 至少总结了 3 位额外的小组成员（Drake、Bontempi、Bianco、Grinspoon 等）
- [ ] 至少为 3 位发言者包含直接引用
- [ ] 发言者按大致出现顺序组织

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the speaker summary task.

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

    report_path = workspace / "speaker_summary.md"
    if not report_path.exists():
        alternatives = ["speakers.md", "summary.md", "speaker_summaries.md"]
        for alt in alternatives:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "dan_evans": 0.0,
            "nicola_fox": 0.0,
            "david_spergel": 0.0,
            "sean_kirkpatrick": 0.0,
            "faa_speaker": 0.0,
            "additional_panelists": 0.0,
            "quotes_included": 0.0,
            "speaker_order": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Check Dan Evans
    dan_patterns = [r'dan\s+evans', r'designated\s+federal\s+official']
    has_dan = any(re.search(p, content_lower) for p in dan_patterns)
    dan_points = sum([
        bool(re.search(r'harass', content_lower)),
        bool(re.search(r'faca|federal\s+advisory', content_lower)),
        bool(re.search(r'stigma', content_lower)),
    ])
    scores["dan_evans"] = 1.0 if has_dan and dan_points >= 2 else (0.5 if has_dan else 0.0)

    # Check Nicola Fox
    fox_patterns = [r'nicola?\s+fox', r'nicky?\s+fox', r'dr\.?\s+fox']
    has_fox = any(re.search(p, content_lower) for p in fox_patterns)
    fox_points = sum([
        bool(re.search(r'classif', content_lower)),
        bool(re.search(r'calibrat', content_lower)),
        bool(re.search(r'open\s+data|data\.nasa', content_lower)),
    ])
    scores["nicola_fox"] = 1.0 if has_fox and fox_points >= 2 else (0.5 if has_fox else 0.0)

    # Check David Spergel
    spergel_patterns = [r'sperg[eo]l', r'panel\s+chair']
    has_spergel = any(re.search(p, content_lower) for p in spergel_patterns)
    spergel_points = sum([
        bool(re.search(r'fast\s+radio\s+burst|frb', content_lower)),
        bool(re.search(r'calibrat', content_lower)),
        bool(re.search(r'high.quality\s+data', content_lower)),
        bool(re.search(r'citizen\s+science', content_lower)),
    ])
    scores["david_spergel"] = 1.0 if has_spergel and spergel_points >= 2 else (0.5 if has_spergel else 0.0)

    # Check Sean Kirkpatrick
    kirk_patterns = [r'kirkpatrick', r'aaro']
    has_kirk = any(re.search(p, content_lower) for p in kirk_patterns)
    kirk_points = sum([
        bool(re.search(r'800', content_lower)),
        bool(re.search(r'2.{0,5}5\s*%|single.digit\s*percent', content_lower)),
        bool(re.search(r'declassif|footage|video', content_lower)),
        bool(re.search(r'five\s+eyes', content_lower)),
    ])
    scores["sean_kirkpatrick"] = 1.0 if has_kirk and kirk_points >= 2 else (0.5 if has_kirk else 0.0)

    # Check FAA speaker
    faa_patterns = [r'freie|faa']
    has_faa = any(re.search(p, content_lower) for p in faa_patterns)
    faa_points = sum([
        bool(re.search(r'radar', content_lower)),
        bool(re.search(r'14.?000\s*controller|controller', content_lower)),
        bool(re.search(r'3.{0,5}5\s*report|per\s+month', content_lower)),
        bool(re.search(r'surveillance', content_lower)),
    ])
    scores["faa_speaker"] = 1.0 if has_faa and faa_points >= 2 else (0.5 if has_faa else 0.0)

    # Check additional panelists (need at least 3 of: Drake, Bontempi, Bianco, Grinspoon, Gold, Wright, Kelly)
    additional = 0
    if re.search(r'drake', content_lower): additional += 1
    if re.search(r'bontempi', content_lower): additional += 1
    if re.search(r'bianco|federica', content_lower): additional += 1
    if re.search(r'grinspoon', content_lower): additional += 1
    if re.search(r'mike\s+gold|gold', content_lower): additional += 1
    if re.search(r'shelley\s+wright|wright', content_lower): additional += 1
    scores["additional_panelists"] = 1.0 if additional >= 4 else (0.5 if additional >= 2 else 0.0)

    # Check for quotes (look for quotation marks with substantial text)
    quote_patterns = re.findall(r'["“].{20,}?["”]', content)
    scores["quotes_included"] = 1.0 if len(quote_patterns) >= 3 else (0.5 if len(quote_patterns) >= 1 else 0.0)

    # Check speaker order (Evans/Fox before Kirkpatrick before FAA)
    evans_pos = content_lower.find('evans')
    kirk_pos = content_lower.find('kirkpatrick')
    faa_pos = content_lower.find('freie') if 'freie' in content_lower else content_lower.find('faa')
    if evans_pos >= 0 and kirk_pos >= 0 and faa_pos >= 0:
        scores["speaker_order"] = 1.0 if evans_pos < kirk_pos < faa_pos else 0.5
    elif evans_pos >= 0 and kirk_pos >= 0:
        scores["speaker_order"] = 1.0 if evans_pos < kirk_pos else 0.5
    else:
        scores["speaker_order"] = 0.0

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Speaker Identification Completeness (Weight: 30%)

**Score 1.0**: 所有主要发言者都被识别，姓名、角色和隶属关系正确。涵盖至少 8 位发言者。
**Score 0.75**: 大部分主要发言者被正确识别。涵盖 6-7 位发言者。
**Score 0.5**: 核心发言者被识别但有些缺失或角色不正确。涵盖 4-5 位发言者。
**Score 0.25**: 只识别了少数发言者，许多缺失。
**Score 0.0**: 未识别发言者或完全错误。

### Criterion 2: Key Point Accuracy (Weight: 35%)

**Score 1.0**: 每位发言者的关键观点准确、具体，捕捉到了他们的主要论点。包括具体细节，如统计数据（800+ 案例、2-5% 异常、每天 45,000 次飞行）。
**Score 0.75**: 大部分关键观点准确，有轻微遗漏或泛化。
**Score 0.5**: 关键观点部分准确，但遗漏重要细节或包含不准确之处。
**Score 0.25**: 关键观点模糊或严重不准确。
**Score 0.0**: 未提取有意义的关键观点。

### Criterion 3: Quote Quality (Weight: 15%)

**Score 1.0**: 包含相关的、有启发性的引用，捕捉到每位发言者的视角。引用准确或为接近的释义。
**Score 0.75**: 为大部分发言者包含良好的引用。
**Score 0.5**: 包含一些引用但可能泛泛或选择不当。
**Score 0.25**: 引用很少或质量差。
**Score 0.0**: 未包含引用。

### Criterion 4: Organization and Readability (Weight: 20%)

**Score 1.0**: 按出现顺序按发言者良好组织，格式清晰，易于浏览和参考。
**Score 0.75**: 良好的组织，有轻微问题。
**Score 0.5**: 可读但组织不佳。
**Score 0.25**: 组织混乱，难以理解。
**Score 0.0**: 没有可用的结构。

---

## Additional Notes

此任务测试 Agent 的能力：

- 处理长会议记录（约 1800 行）
- 识别陈述并归属于特定发言者
- 区分主要演讲和简短插话
- 提取并总结每位发言者的关键论点
- 选择代表性引用
- 以结构化、易浏览的格式组织信息

记录包含多位贡献程度不同的发言者，从完整演讲到简短问题。Agent 必须区分实质性演讲和简短交流。
