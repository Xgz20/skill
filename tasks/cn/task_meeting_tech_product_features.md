---
id: task_meeting_tech_product_features
name: 会议产品功能优先级排序
category: 会议分析
scene: 企业产品情报与业务信息助手
sub_scene: 会议功能优先级排序
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

我有一个文件 `meeting_transcript.md`，里面是 2021 年 6 月 28 日一次 GitLab 产品营销周会的逐字记录。会议中很大一部分讨论了在即将到来的 GitLab Commit 大会上该重点呈现哪些产品功能和改进。

请分析这份逐字记录，创建一个名为 `feature_priorities.md` 的文件，包含讨论过的功能的优先级列表。对每个功能，请包含：

1. **功能名称**
2. **阶段/领域**（例如 Create、Secure、Monitor、Plan、CI/CD、GitOps 等）
3. **兴奋度等级**（会议中讨论的 1-3 级，其中 3 为最令人兴奋）
4. **描述**（该功能做什么，或它为什么重要）
5. **备注**（任何讨论要点，例如它是否为社区贡献、是否已经有过媒体报道等）

此外还应包括：
- 团队为 Commit 主题演讲选出的**整体前 5 名**
- 他们一致同意用于评估功能的**方法论**（捆绑 MVC、兴奋度等级、堆栈排序）
- 任何被**明确降低优先级**的功能及其原因

---

## Expected Behavior

Agent 应当：

1. 解析会议逐字记录，找到所有功能讨论
2. 提取并整理功能及其元数据

讨论过的关键功能：

**Top 5 / High Priority:**
1. **UX improvements** (cross-stage) — Excitement: 3. Brian noted this maps beyond just Create stage. Common "big launch" category per industry practice.
2. **Vulnerability management** (Secure) — Excitement: high. Cindy proposed bundling small MVCs over the year into one narrative. Already part of 14.0 announcements.
3. **GitOps capabilities** (Configure/GitOps) — Kubernetes agent + HashiCorp/Terraform integrations bundled together.
4. **Pipeline editor** (CI/CD) — Mentioned as a definite option for CI/CD stage.
5. **Something from Plan** — Cormac assigned to add; epic boards mentioned (long-requested feature), milestone burnup charts mentioned.

**Other notable features:**
- **Fuzzing acquisitions** (Secure) — Deprioritized because already had press coverage twice (acquisition announcement + integration follow-up); "worn out"
- **Semgrep scanner replacement** (Secure) — Replaced an existing scanner; could be a line item
- **DAST Browser scanner** (Secure) — Proprietary DAST for single-page applications, in beta; called "Berserker"
- **VS Code integrations** (Create) — Two integrations that were community contributions; the unofficial extension becoming official
- **Terraform module** (Configure) — Community module now officially supported
- **Value Stream Analytics** (Plan) — Potential story but customizable version was from 12.9 (too old)
- **Incident management** (Monitor) — Bundle of improvements, though core was from earlier

**Methodology:**
- Bundle small MVCs into larger themes rather than listing individual features
- Use excitement levels 1-3 as stack rank (one each, not raw scores)
- Look back over past year for features that started as beta and are now GA-ready
- Reuse GitLab 14.0 announcements plus additions
- Target: top 5 overall for PR team to use as keynote fodder

---

## Grading Criteria

- [ ] 创建了文件 `feature_priorities.md`
- [ ] 列出了至少 8 个不同的功能或功能捆绑组
- [ ] 将 UX improvements 识别为顶级首选项
- [ ] 将 vulnerability management 识别为顶级首选项
- [ ] 将 GitOps/Kubernetes agent 识别为顶级首选项
- [ ] 为 CI/CD 提到了 pipeline editor
- [ ] 因之前已有媒体报道而将 fuzzing 降低优先级
- [ ] 注明了社区贡献（VS Code、Terraform module）
- [ ] 捕捉到了捆绑方法论（将 MVC 归入主题）
- [ ] 包含整体前 5 名（top 5）部分

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the meeting product feature prioritization task.

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

    report_path = workspace / "feature_priorities.md"
    if not report_path.exists():
        for alt in ["features.md", "product_features.md", "feature_list.md", "priorities.md"]:
            alt_path = workspace / alt
            if alt_path.exists():
                report_path = alt_path
                break

    if not report_path.exists():
        return {
            "report_created": 0.0,
            "min_features": 0.0,
            "ux_top_pick": 0.0,
            "vuln_mgmt_top_pick": 0.0,
            "gitops_top_pick": 0.0,
            "pipeline_editor": 0.0,
            "fuzzing_deprioritized": 0.0,
            "community_contributions": 0.0,
            "bundling_methodology": 0.0,
            "top_five_section": 0.0,
        }

    scores["report_created"] = 1.0
    content = report_path.read_text()
    content_lower = content.lower()

    # Minimum features listed
    feature_markers = re.findall(r'(?:^|\n)\s*(?:[-*•]|\d+[.)]) .{10,}', content)
    headers = re.findall(r'(?:^|\n)#+\s+.+', content)
    total_items = len(feature_markers) + len(headers)
    scores["min_features"] = 1.0 if total_items >= 8 else (0.5 if total_items >= 5 else 0.0)

    # UX as top pick
    ux_patterns = [
        r'(?:ux|user\s*experience).*(?:top|high|exciting|priorit|important)',
        r'(?:top|high|exciting|priorit|important).*(?:ux|user\s*experience)',
    ]
    scores["ux_top_pick"] = 1.0 if any(re.search(p, content_lower) for p in ux_patterns) else (0.5 if re.search(r'(?:ux|user\s*experience)', content_lower) else 0.0)

    # Vulnerability management as top pick
    vuln_patterns = [
        r'vulnerability\s*management',
    ]
    scores["vuln_mgmt_top_pick"] = 1.0 if any(re.search(p, content_lower) for p in vuln_patterns) else 0.0

    # GitOps/K8s agent as top pick
    gitops_patterns = [
        r'(?:kubernetes|k8s)\s*agent',
        r'gitops',
        r'(?:hashicorp|terraform)\s*integrat',
    ]
    gitops_hits = sum(1 for p in gitops_patterns if re.search(p, content_lower))
    scores["gitops_top_pick"] = 1.0 if gitops_hits >= 2 else (0.5 if gitops_hits >= 1 else 0.0)

    # Pipeline editor
    scores["pipeline_editor"] = 1.0 if re.search(r'pipeline\s*editor', content_lower) else 0.0

    # Fuzzing deprioritized
    fuzzing_patterns = [
        r'fuzz.*(?:already|prior|previous|worn|press|cover|depriorit)',
        r'(?:already|prior|previous|worn|press|cover|depriorit).*fuzz',
    ]
    scores["fuzzing_deprioritized"] = 1.0 if any(re.search(p, content_lower) for p in fuzzing_patterns) else (0.5 if re.search(r'fuzz', content_lower) else 0.0)

    # Community contributions
    community_patterns = [
        r'communit.*contribut',
        r'(?:vs\s*code|vscode).*communit',
        r'communit.*(?:vs\s*code|vscode|terraform)',
    ]
    community_hits = sum(1 for p in community_patterns if re.search(p, content_lower))
    scores["community_contributions"] = 1.0 if community_hits >= 1 else 0.0

    # Bundling methodology
    bundle_patterns = [
        r'(?:bundle|group|bucket|aggregat|roll\s*up)',
        r'(?:mvc|small\s*feature|iteration)',
        r'(?:theme|narrative|story)',
    ]
    bundle_hits = sum(1 for p in bundle_patterns if re.search(p, content_lower))
    scores["bundling_methodology"] = 1.0 if bundle_hits >= 2 else (0.5 if bundle_hits >= 1 else 0.0)

    # Top 5 section
    top5_patterns = [
        r'top\s*(?:five|5)',
    ]
    scores["top_five_section"] = 1.0 if any(re.search(p, content_lower) for p in top5_patterns) else 0.0

    return scores
```

---

## LLM Judge Rubric

### Criterion 1: Feature Extraction Completeness (Weight: 30%)

**Score 1.0**：列出了讨论过的所有功能，包括 UX improvements、vulnerability management、GitOps/K8s agent、pipeline editor、fuzzing、Semgrep、DAST Browser（Berserker）、VS Code integrations、Terraform module、value stream analytics、incident management 以及 epic boards。每个都有准确的阶段归属。
**Score 0.75**：捕捉到大部分功能且阶段归属正确，遗漏一两个。
**Score 0.5**：捕捉到主要功能，但漏掉了若干次要功能。
**Score 0.25**：只捕捉到最显而易见的功能。
**Score 0.0**：未提取到任何有意义的功能。

### Criterion 2: Prioritization Accuracy (Weight: 30%)

**Score 1.0**：正确识别出逐渐成形的前 5 名（UX、vulnerability management、GitOps bundle、CI/CD、待定的 Plan）。准确反映兴奋度等级和团队的排序理由。注明了哪些功能被降低优先级（fuzzing 因之前已有媒体报道）以及哪些需要后续跟进。
**Score 0.75**：顶级首选项基本正确，仅有少量排序问题。
**Score 0.5**：有一些优先级排序，但漏掉了关键排名或理由。
**Score 0.25**：列出了功能但没有有意义的优先级排序。
**Score 0.0**：没有尝试优先级排序。

### Criterion 3: Methodology Documentation (Weight: 20%)

**Score 1.0**：清晰解释了一致同意的方法论：将 MVC 捆绑成主题、用 1-3 兴奋度作为堆栈排序、回顾过去一年中从 beta 到 GA 的功能、复用 14.0 内容、为 PR 团队选出前 5 名。注明了从"每个阶段 3 个"到"整体前 5 名"的转变。
**Score 0.75**：捕捉到大部分方法论要素。
**Score 0.5**：提到一些方法论，但不完整。
**Score 0.25**：对方法论只有含糊的提及。
**Score 0.0**：没有记录任何方法论。

### Criterion 4: Context and Detail Quality (Weight: 20%)

**Score 1.0**：为每个功能包含了相关背景：社区贡献状态、之前的媒体报道、成熟度等级、客户需求信号（点赞数、MAU 讨论）。注明了与 GitLab Commit 主题演讲的关联。
**Score 0.75**：背景良好，仅有少量缺漏。
**Score 0.5**：有一些背景，但许多功能缺乏细节。
**Score 0.25**：提供的背景极少。
**Score 0.0**：没有背景或细节。
