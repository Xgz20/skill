---
id: task_meeting_advisory_acronyms
name: NTIA 咨询委员会缩略语词汇表
category: 会议分析
scene: 数据库检索、表格整理与数据分析
sub_scene: 会议记录缩略语提取
difficulty: L2
capabilities:
- 数据提取与处理
- 领域推理
- 输出格式适配
- 指令遵循与约束理解
grading_type: hybrid
timeout_seconds: 180
grading_weights:
  automated: 0.6
  llm_judge: 0.4
workspace_files:
  - source: meetings/2012-05-30-meeting-transcript-ntia-csmac.md
    dest: meeting-transcript.md
---

## Prompt

我在 `meeting-transcript.md` 中有一份政府咨询委员会会议的记录。这是商务部频谱管理咨询委员会（Commerce Spectrum Management Advisory Committee，CSMAC）于 2012 年 5 月 30 日召开的会议，讨论联邦频谱管理与共享。

请分析这份记录，并在一个名为 `acronym_glossary.md` 的文件中构建一份全面的缩略语词汇表。对于发现的每一个缩略语或缩写：

- **缩略语**（记录中使用的缩写形式）
- **全称**（它所代表的完整名称）
- **上下文**（简要描述它在本次会议中的使用方式，1-2 句话）
- **类别**（政府机构、频谱 / 技术、监管、行业、军事或其他）

按缩略语字母顺序对词汇表排序。在末尾包含发现的缩略语总数。

注意：部分缩略语可能在记录本身中被展开；其他则可能需要频谱管理与电信政策方面的领域知识来解读。提取所有出现的缩略语，包括仅出现一次的。

---

## Expected Behavior

Agent 应当：

1. 读取并解析会议记录
2. 识别所有缩略语与缩写
3. 确定它们的全称（从上下文或领域知识）
4. 对它们进行分类与排序

预期的关键缩略语（最小集合）：

| Acronym | Full Form | Category |
|---------|-----------|----------|
| CSMAC | Commerce Spectrum Management Advisory Committee | Government Agency |
| NTIA | National Telecommunications and Information Administration | Government Agency |
| FCC | Federal Communications Commission | Government Agency |
| NOAA | National Oceanic and Atmospheric Administration | Government Agency |
| DoD | Department of Defense | Government Agency |
| DHS | Department of Homeland Security | Government Agency |
| OMB | Office of Management and Budget | Government Agency |
| OSTP | Office of Science and Technology Policy | Government Agency |
| ITS | Institute for Telecommunication Sciences | Government Agency |
| ISART | International Symposium on Advanced Radio Technologies | Spectrum/Technical |
| MHz | Megahertz | Spectrum/Technical |
| GHz | Gigahertz | Spectrum/Technical |
| UAV | Unmanned Aerial Vehicle | Military |
| LTE | Long-Term Evolution | Industry |
| PCS | Personal Communications Service | Spectrum/Technical |
| AWS | Advanced Wireless Services | Spectrum/Technical |
| CMRS | Commercial Mobile Radio Service | Industry |
| STA | Special Temporary Authority | Regulatory |
| CSEA | Commercial Spectrum Enhancement Act | Regulatory |
| PCAST | President's Council of Advisors on Science and Technology | Government Agency |
| CTIA | Cellular Telecommunications Industry Association | Industry |
| TIA | Telecommunications Industry Association | Industry |
| TSB | Telecommunications Systems Bulletin | Spectrum/Technical |
| ITU-R | International Telecommunication Union - Radiocommunication | Spectrum/Technical |
| WRC | World Radiocommunication Conference | Spectrum/Technical |
| IP | Intellectual Property | Other |
| TMI | Too Much Information | Other |
| NFL | National Football League (used metaphorically for major cities) | Other |

总计：约 25-30 个缩略语

---

## Grading Criteria

- [ ] 已创建文件 `acronym_glossary.md`
- [ ] CSMAC 被正确展开
- [ ] NTIA 被正确展开
- [ ] 识别出至少 15 个唯一缩略语
- [ ] 识别出至少 20 个唯一缩略语（加分阈值）
- [ ] 包含技术类缩略语（MHz、GHz、LTE、UAV、STA）
- [ ] 包含政府机构（FCC、DoD、DHS、OMB、OSTP）
- [ ] 对条目应用了类别或分组
- [ ] 使用了字母顺序排序

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the acronym glossary task.

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

    report_path = workspace / "acronym_glossary.md"
    if not report_path.exists():
        alternatives = ["glossary.md", "acronyms.md", "acronym_list.md"]
        for alt in alternatives:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "csmac_expanded": 0.0,
            "ntia_expanded": 0.0,
            "min_15_acronyms": 0.0,
            "min_20_acronyms": 0.0,
            "technical_acronyms": 0.0,
            "gov_agencies": 0.0,
            "categories_applied": 0.0,
            "alphabetical_sort": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # CSMAC correctly expanded
    csmac_patterns = [
        r'commerce spectrum management advisory committee',
    ]
    scores["csmac_expanded"] = 1.0 if any(re.search(p, content_lower) for p in csmac_patterns) else 0.0

    # NTIA correctly expanded
    ntia_patterns = [
        r'national telecommunications and information administration',
        r'national telecommunications & information administration',
    ]
    scores["ntia_expanded"] = 1.0 if any(re.search(p, content_lower) for p in ntia_patterns) else 0.0

    # Count unique acronyms found (look for patterns like "ACRONYM" followed by expansion or in a list)
    # Count uppercase sequences of 2+ chars that appear as standalone entries
    acronym_candidates = set()
    known_acronyms = [
        "csmac", "ntia", "fcc", "noaa", "dod", "dhs", "omb", "ostp",
        "its", "isart", "mhz", "ghz", "uav", "lte", "pcs", "aws",
        "cmrs", "sta", "csea", "pcast", "ctia", "tia", "tsb",
        "itu", "wrc", "nfl", "ip", "tmi", "int"
    ]
    for acr in known_acronyms:
        if acr in content_lower:
            acronym_candidates.add(acr)

    # Also look for capitalized abbreviations in the content
    for match in re.finditer(r'\b[A-Z]{2,6}\b', content):
        acronym_candidates.add(match.group().lower())

    count = len(acronym_candidates)
    scores["min_15_acronyms"] = 1.0 if count >= 15 else (0.5 if count >= 10 else 0.0)
    scores["min_20_acronyms"] = 1.0 if count >= 20 else (0.5 if count >= 15 else 0.0)

    # Technical acronyms
    tech_acrs = ["mhz", "ghz", "lte", "uav", "sta", "pcs"]
    tech_found = sum(1 for t in tech_acrs if t in content_lower)
    scores["technical_acronyms"] = 1.0 if tech_found >= 4 else (0.5 if tech_found >= 2 else 0.0)

    # Government agencies
    gov_acrs = ["fcc", "dod", "dhs", "omb", "ostp", "noaa"]
    gov_found = sum(1 for g in gov_acrs if g in content_lower)
    scores["gov_agencies"] = 1.0 if gov_found >= 4 else (0.5 if gov_found >= 2 else 0.0)

    # Categories applied
    category_patterns = [
        r'(?:government|agency|agencies)',
        r'(?:technical|spectrum)',
        r'(?:regulatory|regulation)',
        r'(?:industry|commercial)',
        r'(?:military|defense)',
        r'(?:categor|type|group|classification)',
    ]
    cat_found = sum(1 for cp in category_patterns if re.search(cp, content_lower))
    scores["categories_applied"] = 1.0 if cat_found >= 3 else (0.5 if cat_found >= 2 else 0.0)

    # Alphabetical sorting check
    # Extract lines that start with acronyms and check if they're sorted
    acr_lines = []
    for line in content.split('\n'):
        stripped = line.strip()
        if stripped and re.match(r'[\*\-\|#]*\s*\**[A-Z]{2,}', stripped):
            # Extract the acronym
            match = re.search(r'[A-Z]{2,}', stripped)
            if match:
                acr_lines.append(match.group())

    if len(acr_lines) >= 5:
        sorted_lines = sorted(acr_lines)
        # Check if the order roughly matches alphabetical
        matches = sum(1 for a, b in zip(acr_lines, sorted_lines) if a == b)
        ratio = matches / len(acr_lines)
        scores["alphabetical_sort"] = 1.0 if ratio >= 0.7 else (0.5 if ratio >= 0.4 else 0.0)
    elif len(acr_lines) >= 2:
        scores["alphabetical_sort"] = 0.5
    else:
        scores["alphabetical_sort"] = 0.0

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Acronym Coverage (Weight: 35%)

**Score 1.0**：识别出 25+ 个缩略语，包括 CSEA、ISART、TSB、CMRS 等冷僻者，以及 NFL（隐喻）和 TMI 等上下文用法。既覆盖了显而易见的政府缩略语，也覆盖了技术性频谱术语。
**Score 0.75**：识别出 20-24 个缩略语，覆盖大多数主要类别。
**Score 0.5**：识别出 15-19 个缩略语，覆盖了显而易见者，但遗漏了若干领域特定术语。
**Score 0.25**：识别出 10-14 个缩略语，大多只是知名的政府机构。
**Score 0.0**：识别出的缩略语少于 10 个。

### Criterion 2: Expansion Accuracy (Weight: 30%)

**Score 1.0**：所有缩略语展开均正确。领域特定术语（CSEA、CSMAC、CMRS、ISART、TSB 10F）均被准确展开。
**Score 0.75**：大多数展开正确，仅有一两处小错误。
**Score 0.5**：常见缩略语正确，但若干领域特定者展开错误或缺失。
**Score 0.25**：存在多处错误的展开。
**Score 0.0**：展开大体上不正确或属于杜撰。

### Criterion 3: Context Quality (Weight: 20%)

**Score 1.0**：每个条目都包含有意义的、针对本次会议的上下文描述，解释该缩略语与本次 CSMAC 讨论的相关性。
**Score 0.75**：大多数条目有实用的上下文。
**Score 0.5**：存在上下文但流于通用（只是复述展开，而非会议上下文）。
**Score 0.25**：上下文极少或为套话。
**Score 0.0**：未提供上下文。

### Criterion 4: Organization and Categorization (Weight: 15%)

**Score 1.0**：按字母顺序排序，分类清晰（政府、技术、监管、行业、军事、其他），全篇格式一致。
**Score 0.75**：组织良好，仅有小的格式不一致。
**Score 0.5**：有一定组织，但类别或排序不完整。
**Score 0.25**：组织混乱。
**Score 0.0**：没有组织。

---

## Additional Notes

本任务测试 Agent 的以下能力：

- 在连续文本中识别缩略语（在记录中并不总是以全大写形式出现）
- 区分常识性缩略语与领域特定缩略语
- 运用领域知识展开文本中未明确定义的缩略语
- 识别缩写的上下文 / 幽默用法（TMI、作为隐喻的 NFL）
- 按领域对术语分类
- 生成一份干净、按字母顺序排序的参考文档

部分缩略语在记录开头被展开（CSMAC），而其他则需要电信政策领域知识（CSEA、CMRS、ISART）。Agent 应妥善处理这两种情况。
