---
id: task_meeting_council_public_comment
name: 坦帕市议会 – 总结公众意见
category: 会议分析
scene: 内容创作、PPT、网页与多媒体生成
sub_scene: 会议记录摘要生成
difficulty: L2
capabilities:
- 数据提取与处理
- 自然语言生成
- 输出格式适配
- 指令遵循与约束理解
grading_type: hybrid
timeout_seconds: 180
grading_weights:
  automated: 0.5
  llm_judge: 0.5
workspace_files:
  - source: meetings/2026-04-02-tampa-city-council-transcript.md
    dest: transcript.md
---

## Prompt

我有一份 2026 年 4 月 2 日举行的坦帕市议会会议的记录，保存在 `transcript.md` 中。这是一份实时字幕记录。

请分析公众意见部分，并生成一个名为 `public_comments_report.md` 的文件，总结每位公众发言人的意见。对于每位发言人，请包括：

- **发言人姓名**
- **提及的议题或议程项目**（如适用）
- **提出的关键点或关注事项**
- **向议会提出的任何具体请求或要求**

还需在最后包括一个**主题摘要**，按议题领域对意见进行分组（例如，基础设施、住房、历史保护、警务、交通等），并注明哪些议题引起了最多的公众关注。

---

## Expected Behavior

Agent 应识别公众意见部分并提取每位发言人的发言。主要发言人：

- **Jeraldine Williams** — Zion Cemetery（第 16 项），感谢议会
- **Reva Iman** — Zion Cemetery，要求 800 万美元用于纪念馆/族谱中心
- **Daryl Hych** — 退伍军人咨询委员会（第 22 项），DEI 评论
- **Pam Cannella** — 雨水/飓风防范，城市忽视
- **David Moss Cornell** — Highland Pines 的无家可归问题（第 5 区）
- **Joseph Citro** — 交通，三县 MPO，Rays 体育场交通
- **Ashley Morrow** — 坦帕黑人历史（1877 年 Hernando 县）
- **Carroll Ann Bennett** — 人行道规范漏洞，Culbreath Bayou
- **Tiffany Poole** — TPD 事件，15 岁儿子，8 名警察对两名未成年人
- **Steve Michelini** — South Howard 街道关闭，管道/雨水
- **James Adair** — 自 2020 年以来未使用的城市发电机
- **Robin Lockett** — Zion Cemetery 和 Yellow Jackets
- **Valerie Bullock** — 第 19-21 项分区，Aquino Property Management
- **Stephanie Poynor** — Rome Yard 延迟（1436 天），退伍军人委员会
- **Michael Randolph**（在线）— West Tampa CDC，Rome Yard CBA
- **Adrian Rodriguez**（在线）— Colon Cemetery，佛罗里达州法规 872

---

## Grading Criteria

- [ ] 报告文件 `public_comments_report.md` 已创建
- [ ] 识别了 Jeraldine Williams 与 Zion Cemetery
- [ ] 识别了 Reva Iman 与 800 万美元请求
- [ ] 识别了 Pam Cannella 与雨水/飓风
- [ ] 识别了 Tiffany Poole 与 TPD 事件
- [ ] 识别了 Stephanie Poynor 与 Rome Yard（1436 天）
- [ ] 至少识别了 16 位发言人中的 12 位
- [ ] 按议题分组的主题摘要
- [ ] 注明 Zion Cemetery 为多位发言人议题

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    from pathlib import Path
    import re
    scores = {}
    workspace = Path(workspace_path)
    report_path = workspace / "public_comments_report.md"
    if not report_path.exists():
        for alt in ["public_comments.md", "comments_report.md", "comments.md"]:
            if (workspace / alt).exists():
                report_path = workspace / alt
                break
    if not report_path.exists():
        return {k: 0.0 for k in ["report_created", "williams_zion", "iman_8million", "cannella_stormwater", "poole_tpd", "poynor_romeyard", "speaker_count", "thematic_summary", "zion_multiple"]}
    scores["report_created"] = 1.0
    content = report_path.read_text()
    cl = content.lower()
    scores["williams_zion"] = 1.0 if (re.search(r'jeraldine|j\.?\s*williams', cl) and re.search(r'zion', cl)) else 0.0
    scores["iman_8million"] = 1.0 if (re.search(r'reva|iman', cl) and re.search(r'(?:\$?8\s*million|8m)', cl)) else 0.0
    scores["cannella_stormwater"] = 1.0 if (re.search(r'cannella|pam\s*c', cl) and re.search(r'(?:stormwater|hurricane|flood)', cl)) else 0.0
    scores["poole_tpd"] = 1.0 if (re.search(r'(?:tiffany|poole)', cl) and re.search(r'(?:son|child|minor|tpd|police|officer|e-?bike|body\s*cam)', cl)) else 0.0
    scores["poynor_romeyard"] = 1.0 if (re.search(r'(?:stephanie|poynor)', cl) and re.search(r'(?:rome\s*yard|1436)', cl)) else 0.0
    speaker_names = [r'jeraldine', r'reva|iman', r'daryl|hych', r'cannella', r'cornell', r'citro', r'ashley\s*morrow', r'bennett', r'tiffany|poole', r'michelini', r'adair', r'lockett', r'bullock', r'poynor', r'randolph', r'rodriguez']
    found = sum(1 for pat in speaker_names if re.search(pat, cl))
    scores["speaker_count"] = 1.0 if found >= 14 else (0.75 if found >= 12 else (0.5 if found >= 8 else 0.0))
    themes = [r'(?:theme|thematic|topic|categor|group)', r'(?:infrastructure|housing|histor|polic|transport)']
    scores["thematic_summary"] = 1.0 if all(re.search(t, cl) for t in themes) else 0.0
    zion_speakers = sum(1 for pat in [r'(?:jeraldine|williams).*zion|zion.*(?:jeraldine|williams)', r'(?:reva|iman).*zion|zion.*(?:reva|iman)', r'(?:robin|lockett).*zion|zion.*(?:robin|lockett)'] if re.search(pat, cl))
    scores["zion_multiple"] = 1.0 if zion_speakers >= 2 else (0.5 if zion_speakers >= 1 else 0.0)
    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Speaker Identification (Weight: 35%)
**Score 1.0**: 所有 16 位发言人均被正确识别并标注议题。**Score 0.75**: 12-15 位。**Score 0.5**: 8-11 位。**Score 0.0**: 无。

### Criterion 2: Summary Quality (Weight: 30%)
**Score 1.0**: 准确捕获关键点和请求。**Score 0.5**: 存在但缺少细节。**Score 0.0**: 无。

### Criterion 3: Thematic Grouping (Weight: 20%)
**Score 1.0**: 明确识别主题。**Score 0.5**: 部分分组。**Score 0.0**: 无。

### Criterion 4: Organization (Weight: 15%)
**Score 1.0**: 格式良好，按时间顺序。**Score 0.5**: 组织混乱。**Score 0.0**: 不可读。
