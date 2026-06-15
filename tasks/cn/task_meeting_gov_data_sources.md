---
id: task_meeting_gov_data_sources
name: NASA UAP听证会数据源提取
category: 会议分析
scene: 数据库检索、表格整理与数据分析
sub_scene: 记录源提取
difficulty: L2
capabilities:
- 数据提取与处理
- 输出格式适配
- 指令遵循与约束理解
- 幻觉抑制
- 自然语言生成
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

我有一个记录文件 `transcript.md`，来自NASA关于不明异常现象（UAPs/UFOs）的首次公开会议。在整个会议期间，发言人引用了与UAP研究相关的各种数据源、传感器、数据库和测量系统。

请阅读记录并将所有引用的数据源和测量系统提取到名为 `data_sources.md` 的文件中。对于每个源，包括：

- **名称/类型**，数据源或传感器系统
- **所有者/运营商**（机构或组织）
- **描述**（它测量或提供什么）
- **与UAP的相关性**（在UAP研究背景下如何讨论）
- **局限性**（提到的任何局限性或注意事项）
- **谁引用的**（发言人姓名）

将源组织成类别：政府/军事传感器、民用航空系统、天基资产、地基科学仪器、众包/公共数据和数据库/档案。在顶部包含一个汇总表，列出所有源及其类别和所有者。

---

## Expected Behavior

Agent应该：

1. 阅读并解析完整记录
2. 识别提到的所有数据源、传感器、数据库和测量系统
3. 捕获每个讨论的能力和局限性
4. 全面组织

关键引用的数据源：

**政府/军事：**
- AARO数据库（800多个案例，DOD/IC机密持有）
- 国防部传感器（F-35摄像头，MQ-9 EO传感器——"不是科学传感器"）
- 情报界传感器（"非常接近科学传感器，经过校准，高精度"）
- AARO专用UAP检测传感器

**民用航空：**
- FAA短程雷达（40-60英里范围，高达24,000英尺）
- FAA远程雷达 / ARSR-4和CRSR系统（200-250海里范围，高达100,000英尺）
- ADS-B（自动相关监视-广播）协作系统
- FAA TRACON终端系统
- ERAM（航路自动化现代化）/ STARS系统
- FAA国内事件网络（报告系统）

**天基：**
- NASA地球科学/遥感卫星
- NOAA卫星
- 詹姆斯·韦伯太空望远镜（作为校准示例提及）
- 哈勃太空望远镜（作为校准示例提及）
- 国际空间站成像（雪碧观测示例）

**地基科学：**
- 大型射电望远镜（FRB检测类比）
- 天文观测站（时域巡天望远镜）
- NOAA地面传感器
- 国家气象局气球跟踪系统

**众包/公共：**
- 智能手机传感器数据（GPS、位置、速度、加速度计）
- 目击者报告（注意单独不足）
- iPhone图像（注意"通常没有帮助"，除非近距离）
- 提议的NASA众包平台

**数据库/档案：**
- NASA开放数据门户（data.nasa.gov）
- Data.gov开放数据资源
- FAA处理的雷达数据档案（保留数月）
- 国家气象局气球发射记录（92个站点，每天两次）

---

## Grading Criteria

- [ ] 创建了输出文件 `data_sources.md`
- [ ] 引用了AARO数据库及案例数量详情
- [ ] 描述了FAA雷达系统（区分短程和远程）
- [ ] 提到了ADS-B系统
- [ ] 引用了NASA卫星/地球遥感资产
- [ ] 包含了智能手机/公民科学数据源
- [ ] 提到了NASA开放数据门户（data.nasa.gov）
- [ ] 至少为3个数据源注明了局限性
- [ ] 源被组织成类别
- [ ] 包含了汇总表或概述

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the data sources extraction task.

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

    report_path = workspace / "data_sources.md"
    if not report_path.exists():
        alternatives = ["sources.md", "data.md", "sensors.md", "data_sources_report.md"]
        for alt in alternatives:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "aaro_database": 0.0,
            "faa_radar": 0.0,
            "adsb": 0.0,
            "nasa_satellites": 0.0,
            "citizen_data": 0.0,
            "nasa_portal": 0.0,
            "limitations": 0.0,
            "categorization": 0.0,
            "summary_table": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # AARO database
    has_aaro = bool(re.search(r'aaro', content_lower))
    has_cases = bool(re.search(r'800|case|holding', content_lower))
    scores["aaro_database"] = 1.0 if has_aaro and has_cases else (0.5 if has_aaro else 0.0)

    # FAA radar systems
    has_short = bool(re.search(r'short.range\s+radar|asr|terminal\s+radar', content_lower))
    has_long = bool(re.search(r'long.range\s+radar|arsr|crsr|en.?route', content_lower))
    scores["faa_radar"] = 1.0 if has_short and has_long else (0.5 if has_short or has_long else 0.0)

    # ADS-B
    scores["adsb"] = 1.0 if re.search(r'ads.?b|automatic\s+dependent\s+surveillance', content_lower) else 0.0

    # NASA satellites
    nasa_sat_patterns = [r'earth\s+(?:science|sensing)\s+satellite', r'nasa\s+satellite', r'space.based', r'james\s+webb|jwst', r'hubble']
    scores["nasa_satellites"] = 1.0 if sum(bool(re.search(p, content_lower)) for p in nasa_sat_patterns) >= 2 else (0.5 if any(re.search(p, content_lower) for p in nasa_sat_patterns) else 0.0)

    # Citizen / smartphone data
    citizen_patterns = [r'smartphone|cell\s*phone|iphone|mobile\s+(?:phone|device)', r'crowdsourc', r'citizen\s+science', r'eyewitness']
    scores["citizen_data"] = 1.0 if sum(bool(re.search(p, content_lower)) for p in citizen_patterns) >= 2 else (0.5 if any(re.search(p, content_lower) for p in citizen_patterns) else 0.0)

    # NASA data portal
    scores["nasa_portal"] = 1.0 if re.search(r'data\.nasa\.gov|nasa.*open\s+data\s+portal|data\.gov', content_lower) else 0.0

    # Limitations noted
    limitation_patterns = [
        r'not\s+(?:calibrated|scientific|optimized)',
        r'uncalibrated',
        r'limit(?:ation|ed)',
        r'cannot\s+(?:detect|see|measure)',
        r'insufficient|inadequate',
        r'filter(?:ing|ed)\s+out',
        r'not\s+helpful',
        r'clutter',
        r'not\s+designed\s+for',
    ]
    lim_count = sum(1 for p in limitation_patterns if re.search(p, content_lower))
    scores["limitations"] = 1.0 if lim_count >= 3 else (0.5 if lim_count >= 1 else 0.0)

    # Categorization
    category_patterns = [
        r'government|military|dod|defense',
        r'civilian|aviation|faa',
        r'space.based|satellite|orbital',
        r'ground.based|terrestrial|observatory',
        r'crowdsourc|public|citizen',
        r'database|archive|repository',
    ]
    cat_count = sum(1 for p in category_patterns if re.search(p, content_lower))
    scores["categorization"] = 1.0 if cat_count >= 4 else (0.5 if cat_count >= 2 else 0.0)

    # Summary table
    has_table = bool(re.search(r'\|.*\|.*\|', content))
    has_overview = bool(re.search(r'summary|overview|at.a.glance', content_lower))
    scores["summary_table"] = 1.0 if has_table else (0.5 if has_overview else 0.0)

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Source Identification Completeness (Weight: 30%)

**Score 1.0**: 识别了至少15个不同的数据源/系统，跨所有类别。涵盖了军事传感器、FAA系统、天基资产、科学仪器和公共/公民数据。没有遗漏主要源。
**Score 0.75**: 跨大多数类别识别了10-14个源。
**Score 0.5**: 识别了6-9个源，某些类别代表性不足。
**Score 0.25**: 少于6个源。
**Score 0.0**: 未识别源。

### Criterion 2: Technical Accuracy (Weight: 25%)

**Score 1.0**: 描述在技术上准确，包括具体细节（例如，FAA短程雷达40-60英里范围，ADS-B覆盖至离地1,500英尺，MQ-9 EO传感器）。局限性描述正确。
**Score 0.75**: 大部分准确，有轻微技术错误。
**Score 0.5**: 有一定准确性但缺少重要技术细节。
**Score 0.25**: 描述模糊或不准确。
**Score 0.0**: 无技术细节。

### Criterion 3: Limitation Analysis (Weight: 25%)

**Score 1.0**: 为关键系统清楚注明了局限性。包括：国防部传感器不是为科学设计的，FAA过滤去除小目标，雷达视线限制，iPhone照片通常无用，仅目击者报告不足。
**Score 0.75**: 为大多数系统注明了局限性。
**Score 0.5**: 注明了一些局限性但不完整。
**Score 0.25**: 提到的局限性很少。
**Score 0.0**: 未讨论局限性。

### Criterion 4: Organization and Presentation (Weight: 20%)

**Score 1.0**: 清晰的分类，顶部有汇总表，每个条目格式一致，易于参考和比较源。
**Score 0.75**: 良好的组织，有轻微问题。
**Score 0.5**: 有组织但格式不一致。
**Score 0.25**: 组织混乱。
**Score 0.0**: 无组织。

---

## Additional Notes

此任务测试Agent的能力：

- 识别在上下文中提到的技术系统和数据源（不仅仅是列出的）
- 从对话式讨论中提取技术规格
- 区分不同类型的传感器及其能力
- 注意能力和局限性
- 以结构化、可参考的格式呈现技术信息

发言人经常顺带提到或作为示例提及数据源，而不是以结构化方式。Agent必须在完整记录中识别这些引用。
