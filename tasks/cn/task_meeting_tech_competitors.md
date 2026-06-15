---
id: task_meeting_tech_competitors
name: 会议竞争对手分析提取
category: 会议分析
scene: 企业产品情报与业务信息助手
sub_scene: 会议竞争对手分析
difficulty: L2
capabilities:
- 数据提取与处理
- 指令遵循与约束理解
- 输出格式适配
- 自然语言生成
- 多步推理
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

我有一个文件 `meeting_transcript.md`，包含 2021 年 6 月 28 日 GitLab 产品营销每周会议的记录。会议的一部分涉及关于竞争定位、对比电子表格以及如何将 GitLab 与竞争对手对比展示的详细讨论。

请分析记录并创建一个名为 `competitor_analysis.md` 的文件，涵盖：

1. **提及的竞争对手**：列出提及的每个竞争对手或竞争产品，附其梯队分类（如有讨论）
2. **竞争定位方法**：团队计划如何将 GitLab 定位于这些竞争对手？
3. **特定阶段竞争对手映射**：哪些竞争对手适用于哪些产品阶段（如讨论所述）？
4. **方法论决策**：关于如何进行竞争分析做出了哪些决策（例如，关注哪些梯队，如何处理竞争对手不适用的阶段）？
5. **关键竞争洞察**：讨论中提及的关于特定竞争对手的任何战略洞察

---

## Expected Behavior

Agent 应该：

1. 仔细阅读会议记录
2. 提取所有竞争对手名称并分类

关键竞争对手和细节：

- **第一梯队竞争对手**（当前分析的重点）：Azure DevOps (ADO)、Atlassian、GitHub、Jenkins、JFrog、CloudBees
- **梯队分类**：团队此前将竞争对手分为第一、二、三梯队；目前仅关注第一梯队
- **阶段相关性**：并非所有第一梯队竞争对手都适用于所有阶段（例如，CloudBees 可能与 Monitor 不相关；GitHub 可能与 Monitor 不相关）
- **平台定位**：一些竞争对手（Azure DevOps、GitHub、Atlassian、JFrog）将自己定位为平台；Jenkins/CloudBees 则不然
- **方法论**：竞争电子表格在每个阶段标签页上都被复制粘贴了相同的 6 个竞争对手，这被识别为错误 — 每个阶段只应出现相关的竞争对手
- **GitLab 行项目**：团队决定向对比表添加 GitLab 行，使该表不只显示 GitLab 更擅长的方面
- **功能选择视角**：应从市场视角（买家购买的东西）选择功能，而不是仅从 GitLab 视角；应包括一些仅竞争对手才有的功能以保持诚实
- **信息图方法**：新设计使用仅绿色（无红色）以呈现为有帮助的行业对比，而不是竞争攻击材料

---

## Grading Criteria

- [ ] 创建了文件 `competitor_analysis.md`
- [ ] 列出所有第一梯队竞争对手（ADO/Azure DevOps、Atlassian、GitHub、Jenkins、JFrog、CloudBees）
- [ ] 提及梯队分类系统（第一、二、三梯队）
- [ ] 讨论特定阶段相关性（并非所有竞争对手适用于所有阶段）
- [ ] 捕捉平台与非平台区别（GitHub、ADO、Atlassian、JFrog 为平台；Jenkins/CloudBees 不是）
- [ ] 捕捉添加 GitLab 行项目的决策
- [ ] 注明功能选择的市场视角方法
- [ ] 捕捉信息图设计理念（仅绿色，对比而非攻击）
- [ ] 捕捉先关注第一梯队的方法论决策

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the meeting competitor analysis extraction task.

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

    report_path = workspace / "competitor_analysis.md"
    if not report_path.exists():
        for alt in ["competitors.md", "competitive_analysis.md", "competitor_report.md"]:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "tier1_competitors": 0.0,
            "tier_system": 0.0,
            "stage_relevance": 0.0,
            "platform_distinction": 0.0,
            "gitlab_line_item": 0.0,
            "market_lens": 0.0,
            "infographic_philosophy": 0.0,
            "tier1_focus": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Tier 1 competitors listed
    competitors = {
        "ado": [r'(?:azure\s*devops|ado)'],
        "atlassian": [r'atlassian'],
        "github": [r'github'],
        "jenkins": [r'jenkins'],
        "jfrog": [r'jfrog|j\s*frog'],
        "cloudbees": [r'cloudbees|cloud\s*bees'],
    }
    comp_count = 0
    for name, patterns in competitors.items():
        if any(re.search(p, content_lower) for p in patterns):
            comp_count += 1
    scores["tier1_competitors"] = 1.0 if comp_count >= 5 else (0.75 if comp_count >= 4 else (0.5 if comp_count >= 3 else 0.0))

    # Tier classification system
    tier_patterns = [r'tier\s*(?:one|1|two|2|three|3)', r'tier[- ]?\d']
    scores["tier_system"] = 1.0 if any(re.search(p, content_lower) for p in tier_patterns) else 0.0

    # Stage-specific relevance
    stage_patterns = [
        r'(?:not\s*(?:all|every)|relevant|applicable|apply).*(?:stage|monitor|configure)',
        r'(?:stage|monitor|configure).*(?:not\s*(?:all|every)|relevant|applicable)',
    ]
    scores["stage_relevance"] = 1.0 if any(re.search(p, content_lower) for p in stage_patterns) else 0.0

    # Platform distinction
    platform_patterns = [
        r'platform',
    ]
    non_platform_patterns = [
        r'(?:jenkins|cloudbees).*(?:not|don.t|doesn.t).*platform',
        r'(?:not|don.t|doesn.t).*platform.*(?:jenkins|cloudbees)',
    ]
    has_platform = any(re.search(p, content_lower) for p in platform_patterns)
    has_non_platform = any(re.search(p, content_lower) for p in non_platform_patterns)
    scores["platform_distinction"] = 1.0 if has_platform and has_non_platform else (0.5 if has_platform else 0.0)

    # GitLab line item decision
    gitlab_patterns = [
        r'(?:add|include).*gitlab.*(?:line|row|column|entry)',
        r'gitlab.*(?:line|row|column|entry).*(?:add|include)',
        r'(?:add|include).*(?:line|row|column|entry).*gitlab',
    ]
    scores["gitlab_line_item"] = 1.0 if any(re.search(p, content_lower) for p in gitlab_patterns) else 0.0

    # Market lens approach
    market_patterns = [
        r'market\s*lens',
        r'(?:buyer|customer|shopp)',
        r'(?:honest|trustworthy|accurate\s*assessment)',
    ]
    market_hits = sum(1 for p in market_patterns if re.search(p, content_lower))
    scores["market_lens"] = 1.0 if market_hits >= 2 else (0.5 if market_hits >= 1 else 0.0)

    # Infographic philosophy
    infographic_patterns = [
        r'(?:green|color).*(?:comparison|helpful|industry)',
        r'(?:no\s*red|without\s*red|avoid\s*red)',
        r'(?:comparison|helpful).*(?:not\s*(?:competitive|attack))',
    ]
    infographic_hits = sum(1 for p in infographic_patterns if re.search(p, content_lower))
    scores["infographic_philosophy"] = 1.0 if infographic_hits >= 2 else (0.5 if infographic_hits >= 1 else 0.0)

    # Tier 1 focus decision
    focus_patterns = [
        r'(?:focus|only|just).*tier\s*(?:one|1)',
        r'tier\s*(?:one|1).*(?:focus|first|now|current)',
    ]
    scores["tier1_focus"] = 1.0 if any(re.search(p, content_lower) for p in focus_patterns) else 0.0

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Competitor Identification Completeness (Weight: 30%)

**Score 1.0**: 识别所有六个第一梯队竞争对手（Azure DevOps、Atlassian、GitHub、Jenkins、JFrog、CloudBees），并准确进行梯队分类和梯队系统讨论。
**Score 0.75**: 识别大部分竞争对手并附梯队信息，遗漏一两个。
**Score 0.5**: 识别出几个竞争对手，但梯队系统解释不充分。
**Score 0.25**: 仅提及少数竞争对手，无分类。
**Score 0.0**: 未识别竞争对手。

### Criterion 2: Strategic Positioning Analysis (Weight: 30%)

**Score 1.0**: 捕捉 GitLab 定位方法的全部细微之处：功能的市场视角、平台与非平台区别、用于对比（非攻击）的仅绿色信息图、添加 GitLab 行以进行诚实对比，以及创建有帮助的行业资源的目标。
**Score 0.75**: 捕捉大部分定位要素，有轻微差距。
**Score 0.5**: 一些定位洞察，但遗漏关键战略决策。
**Score 0.25**: 表面提及竞争定位。
**Score 0.0**: 没有定位分析。

### Criterion 3: Stage-Specific Mapping (Weight: 20%)

**Score 1.0**: 清晰解释并非所有竞争对手适用于所有阶段，给出具体例子（例如，CloudBees/GitHub 与 Monitor 不相关），并注明识别出的电子表格复制粘贴问题。
**Score 0.75**: 对阶段相关性有良好理解，有轻微差距。
**Score 0.5**: 提及阶段相关性但缺乏具体内容。
**Score 0.25**: 对阶段的模糊引用。
**Score 0.0**: 没有特定阶段分析。

### Criterion 4: Methodology Clarity (Weight: 20%)

**Score 1.0**: 清晰记录约定的方法论：先关注第一梯队，然后扩展；每个阶段只列相关竞争对手；从市场视角选择功能；添加 GitLab 进行对比。将其呈现为可操作的指导。
**Score 0.75**: 捕捉大部分方法论决策。
**Score 0.5**: 提及一些方法论但不完整。
**Score 0.25**: 模糊的方法论描述。
**Score 0.0**: 没有记录方法论。
