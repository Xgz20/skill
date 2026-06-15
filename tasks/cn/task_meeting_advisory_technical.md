---
id: task_meeting_advisory_technical
name: NTIA 咨询委员会技术讨论
category: 会议分析
scene: 数据库检索、表格整理与数据分析
sub_scene: 会议记录技术内容提取
difficulty: L2
capabilities:
- 数据提取与处理
- 领域推理
- 自然语言生成
- 指令遵循与约束理解
- 输出格式适配
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

我在 `meeting-transcript.md` 中有一份政府咨询委员会会议记录。这是商务部频谱管理咨询委员会（CSMAC）于 2012 年 5 月 30 日召开的会议，重点讨论 1755-1850 MHz 频段的联邦频谱管理。

请分析这份会议记录，将所有技术讨论提取到一份名为 `technical_discussions.md` 的结构化报告中。对于每个技术议题，请包含：

- **议题标题**（清晰、描述性的名称）
- **涉及的频段**（讨论的具体 MHz 范围）
- **受影响的联邦系统/应用**（该频段中的政府用途）
- **所描述的技术挑战**（具体的工程或干扰问题）
- **提出的方法或解决方案**（为应对该问题所提的建议）
- **工作组分工**（5 个拟议工作组中哪一个负责处理此事）

同时提供：

- 对 **5 个拟议工作组** 的总结，包括其范围和政府方联合主席分工
- 关于商用部署参数的 **关键技术争论**（需要哪些参数，以及它们为何对共享分析至关重要）
- 提及的任何 **具体技术测量或测试**（例如 T-Mobile/CTIA STA）

---

## Expected Behavior

Agent 应当：

1. 阅读并解析会议记录
2. 提取所有讨论的技术议题
3. 将议题映射到 5 个拟议工作组
4. 捕捉技术参数争论

预期的关键技术议题：

- **气象卫星接收机（1695-1710 MHz）**：接收机周围的排除区，通过更好的商用环境建模有望缩小这些区域（第 1 工作组，联合主席：Yvonne Navarro/NOAA，NTIA 代表：Ed Drocella）
- **执法监视**：宽带接收机、全国性授权、三阶段过渡计划（先退出 1755-1780，再压缩，最后离开该频段）（第 2 工作组，联合主席来自 DHS/Justice，NTIA 代表：Rich Orsulak、Scott Jackson）
- **卫星控制上行链路**：短期内无法搬迁，干扰问题是针对产业（而非来自产业），需要监管架构进行保护（第 3 工作组）
- **电子战训练**：军方需要针对商用技术进行训练（对手将手机用作触发器），需要有保障的接入（第 3 工作组）
- **战术无线电中继与固定微波**：来自 1710-1755 搬迁的过往经验，永久站点周围的排除区可缩小，Gary Patrick 参与（第 4 工作组）
- **空中作业（无人机、精确制导弹药、空战训练、遥测）**：最大的挑战，高功率空中发射器对地面接收机，T-Mobile/CTIA STA 用于测量（第 5 工作组，DoD 的 John Hunter）
- **商用部署参数争论**：Rush/Warren/Kahn/Calabrese 讨论是否需要统一参数（LTE 标准、宏蜂窝与小型蜂窝、功率水平）作为所有工作组的共同输入

---

## Grading Criteria

- [ ] 创建了文件 `technical_discussions.md`
- [ ] 涵盖气象卫星排除区议题（1695-1710 MHz）
- [ ] 描述了执法监视过渡计划（三阶段过程）
- [ ] 识别了卫星上行链路保护问题（指出干扰方向）
- [ ] 提及电子战训练需求
- [ ] 将空中作业识别为最大挑战
- [ ] 列出 5 个工作组及其范围
- [ ] 提及 T-Mobile/CTIA STA 测量申请
- [ ] 捕捉了商用参数争论（LTE、小型蜂窝、宏蜂窝）

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the technical discussions extraction task.

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

    report_path = workspace / "technical_discussions.md"
    if not report_path.exists():
        alternatives = ["technical_report.md", "tech_discussions.md", "technical.md"]
        for alt in alternatives:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "weather_satellite": 0.0,
            "law_enforcement": 0.0,
            "satellite_uplink": 0.0,
            "electronic_warfare": 0.0,
            "airborne_operations": 0.0,
            "working_groups": 0.0,
            "sta_measurement": 0.0,
            "parameters_debate": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Weather satellite (1695-1710)
    weather_patterns = [
        r'(?:weather|satellite).*(?:1695|1710)',
        r'1695.*1710.*(?:weather|satellite|exclusion)',
        r'exclusion.*(?:area|zone).*(?:weather|satellite|receiver)',
    ]
    scores["weather_satellite"] = 1.0 if any(re.search(p, content_lower) for p in weather_patterns) else 0.0

    # Law enforcement surveillance transition
    le_patterns = [
        r'law enforcement.*(?:surveillance|transition|three.?step|wideband)',
        r'surveillance.*(?:transition|three.?step|1755.*1780|digital)',
        r'(?:three.?step|3.?step).*(?:process|plan|transition)',
        r'1755.*1780.*(?:first|initial|phase)',
    ]
    scores["law_enforcement"] = 1.0 if any(re.search(p, content_lower) for p in le_patterns) else 0.0

    # Satellite uplink protection
    sat_patterns = [
        r'satellite.*(?:uplink|control).*(?:protect|interference|relocat)',
        r'(?:uplink|satellite control).*(?:cannot|not.*moving|remain)',
        r'interference.*(?:into|toward|against).*industry',
    ]
    scores["satellite_uplink"] = 1.0 if any(re.search(p, content_lower) for p in sat_patterns) else 0.0

    # Electronic warfare
    ew_patterns = [
        r'electronic warfare.*(?:training|test|train)',
        r'(?:ew|electronic warfare).*(?:commercial technology|cell phone|trigger)',
        r'(?:train|training).*(?:electronic warfare|ew)',
    ]
    scores["electronic_warfare"] = 1.0 if any(re.search(p, content_lower) for p in ew_patterns) else 0.0

    # Airborne operations as biggest challenge
    air_patterns = [
        r'airborne.*(?:challenge|difficult|biggest|greatest|complex)',
        r'(?:biggest|greatest).*challenge.*airborne',
        r'(?:uav|unmanned|precision.guided|telemetry|air combat).*(?:challenge|airborne)',
    ]
    scores["airborne_operations"] = 1.0 if any(re.search(p, content_lower) for p in air_patterns) else 0.0

    # Five working groups listed
    wg_patterns = [
        r'working group.*[1-5]',
        r'(?:five|5).*working group',
        r'group 1.*group 2',
    ]
    wg_indicators = 0
    for i in range(1, 6):
        if re.search(rf'(?:working group|group|wg)\s*{i}', content_lower):
            wg_indicators += 1
    if re.search(r'(?:five|5)\s*working\s*group', content_lower):
        wg_indicators += 2
    scores["working_groups"] = 1.0 if wg_indicators >= 3 else (0.5 if wg_indicators >= 1 else 0.0)

    # T-Mobile/CTIA STA measurement
    sta_patterns = [
        r't-?mobile.*(?:sta|measurement|test)',
        r'ctia.*(?:sta|measurement|test)',
        r'sta.*(?:request|measurement|test).*(?:t-?mobile|ctia)',
        r'special temporary auth',
    ]
    scores["sta_measurement"] = 1.0 if any(re.search(p, content_lower) for p in sta_patterns) else 0.0

    # Commercial parameters debate
    param_patterns = [
        r'(?:lte|long term evolution).*(?:standard|parameter|deployment)',
        r'(?:small cell|microcell|macrocell|femtocell).*(?:deploy|parameter|power)',
        r'(?:commercial|industry).*(?:parameter|characteristic|deployment).*(?:common|uniform|consistent)',
        r'(?:common|uniform).*(?:parameter|characteristic)',
    ]
    scores["parameters_debate"] = 1.0 if any(re.search(p, content_lower) for p in param_patterns) else 0.0

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Technical Accuracy (Weight: 35%)

**Score 1.0**：所有技术议题均准确提取，频段、系统描述和干扰动态均正确。干扰方向（例如卫星上行链路——干扰是针对产业的，而非来自产业）标注正确。
**Score 0.75**：大部分技术细节正确，仅有轻微不准确。
**Score 0.5**：识别出大致议题，但技术细节含糊或部分有误。
**Score 0.25**：存在若干技术错误或错误描述。
**Score 0.0**：技术内容大体上不正确。

### Criterion 2: Completeness of Technical Topics (Weight: 25%)

**Score 1.0**：涵盖所有主要技术议题：气象卫星、执法监视、卫星上行链路、电子战、战术无线电中继、固定微波、空中作业，以及商用参数争论。
**Score 0.75**：涵盖大部分议题，仅有一到两处遗漏。
**Score 0.5**：涵盖主要议题，但遗漏若干次要议题。
**Score 0.25**：仅提取了两三个议题。
**Score 0.0**：提取的技术内容极少。

### Criterion 3: Working Group Mapping (Weight: 20%)

**Score 1.0**：清晰描述了所有 5 个工作组，包括其范围、分配的技术议题、具名人员（联合主席、NTIA 代表）和目标完成日期（WG1 为 9 月，其余为 1 月）。
**Score 0.75**：描述了各工作组，大部分细节正确。
**Score 0.5**：提及工作组，但细节不完整。
**Score 0.25**：仅有部分工作组信息。
**Score 0.0**：无工作组信息。

### Criterion 4: Structure and Usefulness (Weight: 20%)

**Score 1.0**：报告组织良好，每个议题划分清晰，易于用作参考。技术挑战与提出的解决方案清晰分离。
**Score 0.75**：结构良好，仅有轻微组织问题。
**Score 0.5**：内容齐全，但组织较差。
**Score 0.25**：组织混乱，难以查找特定议题。
**Score 0.0**：没有有意义的结构。

---

## Additional Notes

本任务测试 Agent 的以下能力：

- 从面向政策的讨论中提取并组织技术信息
- 正确识别频段及其相关的联邦用途
- 理解干扰问题的方向性（哪个系统干扰哪个系统）
- 将组织结构（工作组）映射到技术问题
- 捕捉关于部署参数的细致争论，以及它为何对共享分析至关重要
- 识别具名人员及其在技术进程中的角色

会议记录将政策讨论与技术细节交织在一起。Agent 必须将技术实质内容从政治/程序性内容中分离出来，同时保留关于技术工作如何组织的重要背景。
