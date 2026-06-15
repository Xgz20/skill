---
id: task_log_mapreduce_timeline
name: MapReduce 日志 - 作业时间线可视化
category: 日志分析
scene: 数据库检索、表格整理与数据分析
sub_scene: 日志时间线可视化
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 输出格式适配
- 指令遵循与约束理解
grading_type: hybrid
timeout_seconds: 180
workspace_files:
  - dest: "mapreduce.log"
    source: "logs/hadoop_mapreduce.log"
---

# MapReduce 日志 - 作业时间线可视化

## Prompt

分析位于 `mapreduce.log` 的 Hadoop MapReduce 应用日志，并创建整个作业执行的详细时间线可视化。按时间顺序显示所有主要事件。

你的输出应包括：

1. **事件时间线**：包含时间戳的每个重要事件的时间顺序列表，包括：
   - 作业初始化事件
   - 容器分配
   - 任务启动和完成
   - 错误和警告
   - Reduce 阶段开始
   - 作业完成
2. **阶段图**：将作业划分为阶段（初始化、map 阶段、shuffle、reduce 阶段、清理），包含开始/结束时间和持续时间
3. **甘特式任务视图**：在基于文本的时间线中显示每个任务（m_000000 到 m_000009、r_000000）的大致开始和结束时间
4. **关键事件**：突出显示最有影响力的事件（错误、重试、作业状态转换）
5. **并发分析**：在每个时间点，有多少任务并行运行？

将报告写入 `mapreduce_timeline.md`，格式为结构良好的 markdown 文档，包含 ASCII/基于文本的可视化。

---

## Expected Behavior

Agent 应生成如下时间线：

**阶段分解：**
| 阶段 | 开始 | 结束 | 持续时间 |
|---|---|---|---|
| 初始化 | 15:37:56 | 15:38:00 | ~4s |
| Map 阶段 | 15:38:00 | 15:41:25 | ~3m 25s |
| Reduce 阶段 | 15:39:24 | 15:42:46 | ~3m 22s |
| 清理 | 15:42:46 | 15:42:47 | ~1s |
| **总计** | **15:37:56** | **15:42:47** | **~4m 51s** |

**关键事件：**
- 15:37:56 — 创建 MRAppMaster
- 15:37:57 — 设置 OutputCommitter（FileOutputCommitter）
- 15:38:00 — 容器分配开始（10 个 map 待处理，1 个 reduce 待处理）
- 15:39:24 — 第一个 map 完成（m_000009），完成数：1
- 15:40:28–15:40:52 — 快速 map 完成（任务 2-8）
- 15:40:45 — 警告：块 I/O 错误（ResponseProcessor、DataStreamer）
- 15:41:12 — m_000007 完成（重试尝试）
- 15:41:25 — m_000006 完成（重试尝试，最后一个 map）
- 15:42:46 — r_000000 完成，完成数：11
- 15:42:46 — 作业转换为 SUCCEEDED
- 15:42:47 — 记录最终统计

**并发性：**
- 峰值：最多 10 个 map 任务同时运行
- 15:39:24 之后，随着 map 完成，并发性降低

可接受的变化：
- ASCII 可视化风格会有所不同
- 不是每个日志条目都需要在时间线中 — 主要事件就足够了
- 阶段定义可能略有不同

---

## Grading Criteria

- [ ] 工作区中创建了 `mapreduce_timeline.md`
- [ ] 事件按时间顺序列出并带有时间戳
- [ ] 识别了阶段（初始化、map、reduce、完成）
- [ ] 尝试了可视化或结构化时间线/甘特图
- [ ] 突出显示了关键事件（第一个 map 完成、错误、作业成功）

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """Grade the MapReduce timeline visualization task."""
    from pathlib import Path

    scores = {}
    workspace = Path(workspace_path)
    report_file = workspace / "mapreduce_timeline.md"

    if not report_file.exists():
        return {
            "output_created": 0.0,
            "chronological_events": 0.0,
            "phases_identified": 0.0,
            "visual_timeline": 0.0,
            "key_events_highlighted": 0.0,
        }

    scores["output_created"] = 1.0
    content = report_file.read_text(encoding="utf-8").lower()

    # Check 1: Chronological events with timestamps
    timestamps = ["15:37", "15:38", "15:39", "15:40", "15:41", "15:42"]
    ts_found = sum(1 for ts in timestamps if ts in content)
    scores["chronological_events"] = (
        1.0 if ts_found >= 5 else
        0.5 if ts_found >= 3 else 0.0
    )

    # Check 2: Phases identified
    phase_keywords = ["initialization", "init", "map phase", "reduce phase",
                      "shuffle", "cleanup", "completion", "startup"]
    phases_found = sum(1 for kw in phase_keywords if kw in content)
    scores["phases_identified"] = (
        1.0 if phases_found >= 3 else
        0.5 if phases_found >= 2 else 0.0
    )

    # Check 3: Visual/structured timeline attempted
    visual_keywords = ["timeline", "gantt", "---", "===", "|||", "phase",
                       "diagram", "chart", "|", "─", "-"]
    # Check for table-like structures or ASCII art
    lines = content.split("\n")
    table_lines = [l for l in lines if l.count("|") >= 2]
    ascii_lines = [l for l in lines if any(c in l for c in ["─", "━", "═", "▓", "█", "░"])]
    scores["visual_timeline"] = (
        1.0 if len(table_lines) >= 5 or len(ascii_lines) >= 3 else
        0.5 if len(table_lines) >= 2 else 0.0
    )

    # Check 4: Key events highlighted
    key_events = ["mrappmaster", "first map", "succeeded", "warn", "error",
                  "m_000009", "r_000000", "retry", "completed"]
    events_found = sum(1 for kw in key_events if kw in content)
    scores["key_events_highlighted"] = (
        1.0 if events_found >= 4 else
        0.5 if events_found >= 2 else 0.0
    )

    return scores
```

---

## Additional Notes

**日志中的关键事实：**

- 作业总持续时间：约 4 分 51 秒
- Map 阶段和 reduce 阶段重叠 — reduce 在 map 仍在运行时开始
- reduce "慢启动"阈值意味着 reduce 任务没有立即调度
- 两次 map 任务重试（m_000006、m_000007）将 map 阶段延长了约 35 秒
- 总共 1282 条日志条目，但只有约 50 条代表主要状态转换

**评分权重（相等）：** 五个标准各贡献 0.2 到最终分数。
