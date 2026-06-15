---
id: task_executive_lookup
name: 高管信息查询
category: 调研
scene: 数据库检索、表格整理与数据分析
sub_scene: 高管信息查询
difficulty: L2
capabilities:
- 信息检索与综合
- 工具调用
- 输出格式适配
- 幻觉抑制
grading_type: automated
timeout_seconds: 180
workspace_files: []
---

## Prompt

截至 2026 年 4 月 7 日，GitLab 的 CFO 是谁？

请调研出答案并保存到 `gitlab_cfo.txt`。需包含该高管的全名，以及一段简短的来源说明或日期参考，证明该答案截至 2026 年 4 月 7 日仍然有效。

## Expected Behavior

Agent 应当：

1. 确认截至 2026 年 4 月 7 日 GitLab 的首席财务官（CFO）是谁。
2. 使用可靠来源，例如 GitLab 投资者关系页面、新闻稿或权威财经报道。
3. 在工作区中创建 `gitlab_cfo.txt`。
4. 包含该 CFO 的全名以及简短的日期/来源说明。

答案应当简洁且基于事实。如果 Agent 使用网络工具，应依赖 2026 年的最新信息，而非陈旧的历史数据。

## Grading Criteria

- [ ] 已创建文件 `gitlab_cfo.txt`
- [ ] 文件中指明 Jessica Ross 为 GitLab CFO
- [ ] 文件中提及 GitLab 及 CFO 职位
- [ ] 文件中包含 2026 年的日期或来源说明
- [ ] 答案简洁且易读

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    from pathlib import Path
    import re

    workspace = Path(workspace_path)
    answer_file = workspace / "gitlab_cfo.txt"

    if not answer_file.exists():
        return {
            "file_created": 0.0,
            "correct_name": 0.0,
            "mentions_role": 0.0,
            "has_date_or_source": 0.0,
            "readable": 0.0,
        }

    content = answer_file.read_text(encoding="utf-8", errors="ignore")
    lowered = content.lower()

    scores = {
        "file_created": 1.0,
        "correct_name": 1.0 if "jessica ross" in lowered else 0.0,
        "mentions_role": 1.0 if ("gitlab" in lowered and "cfo" in lowered) else 0.0,
        "has_date_or_source": 1.0 if re.search(r"2026|march 3, 2026|april 7, 2026|source|press release|investor", lowered) else 0.0,
        "readable": 1.0 if len(content.strip()) >= 20 and len(content.splitlines()) >= 1 else 0.0,
    }
    return scores
```

## Additional Notes

- GitLab 于 2026 年初宣布 Jessica Ross 出任 CFO，因此评分以该答案为准。
- 这是一个精确的事实查询任务，旨在奖励使用最新来源的能力。
