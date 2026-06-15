---
id: task_log_mapreduce_slow_tasks
name: MapReduce 日志 - 慢任务识别
category: 日志分析
scene: 数据库检索、表格整理与数据分析
sub_scene: 日志时序分析
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 输出格式适配
- 自然语言生成
grading_type: hybrid
timeout_seconds: 180
workspace_files:
  - dest: "mapreduce.log"
    source: "logs/hadoop_mapreduce.log"
---

# MapReduce 日志 - 慢任务识别

## Prompt

分析位于 `mapreduce.log` 的 Hadoop MapReduce 应用日志，识别哪些 map 和 reduce 任务最慢。比较任务完成时间以找出落后者。

你的报告应包括：

1. **任务完成时间**：对于每个完成的任务，计算从容器分配到任务完成的时间
2. **最快与最慢**：识别最快和最慢的 map 任务，以及 reduce 任务的时序
3. **落后者分析**：是否有任何任务的耗时明显长于平均值？量化偏差
4. **重试影响**：对于重试的任务（attempt > 0），重试时间与原始时间相比如何？
5. **Reduce 阶段时序**：reduce 任务相对于 map 完成时何时开始？耗时多长？
6. **瓶颈识别**：关键路径是什么？哪个（些）任务决定了整体作业持续时间？

将报告写入 `slow_tasks_report.md`，格式为结构良好的 markdown 文档。

---

## Expected Behavior

Agent 应提取任务完成时间戳并计算：

**Map 任务完成（按顺序）：**
1. m_000009: 15:39:24 完成（第一个）
2. m_000005: 15:40:28 完成
3. m_000003: 15:40:32 完成
4. m_000000: 15:40:34 完成
5. m_000001: 15:40:50 完成
6. m_000002: 15:40:50 完成
7. m_000004: 15:40:50 完成
8. m_000008: 15:40:52 完成
9. m_000007: 15:41:12 完成（重试 — _1 尝试）
10. m_000006: 15:41:25 完成（重试 — _1 尝试，最慢/最后）

**Reduce 任务：**
- r_000000: 15:42:46 完成

**关键发现：**
- m_000009 在 15:39:24 最先完成 — 作业开始后约 1.5 分钟
- m_000006 在 15:41:25 最后完成 — 作业开始后约 3.5 分钟（这是一次重试）
- 重试的任务（m_000006, m_000007）最慢，因为它们必须重新启动
- 第一个和最后一个 map 之间的跨度：约 2 分钟
- Reduce 在足够多的 map 完成后开始，约 1.3 分钟后完成

可接受的变化：
- 确切持续时间取决于使用哪个时间戳作为开始参考
- "任务开始"的不同定义是可接受的
- 落后者阈值可能有所不同

---

## Grading Criteria

- [ ] 工作区中创建了 `slow_tasks_report.md`
- [ ] 列出了各个任务的完成时间
- [ ] 识别了最快和最慢的 map 任务
- [ ] 重试的任务（m_000006, m_000007）被标记为较慢
- [ ] reduce 任务时序被单独分析

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """Grade the MapReduce slow task identification task."""
    from pathlib import Path

    scores = {}
    workspace = Path(workspace_path)
    report_file = workspace / "slow_tasks_report.md"

    if not report_file.exists():
        return {
            "output_created": 0.0,
            "completion_times": 0.0,
            "fastest_slowest": 0.0,
            "retries_flagged": 0.0,
            "reduce_timing": 0.0,
        }

    scores["output_created"] = 1.0
    content = report_file.read_text(encoding="utf-8").lower()

    # Check 1: Task completion times listed
    task_ids = ["m_000009", "m_000005", "m_000003", "m_000000", "m_000006"]
    tasks_found = sum(1 for t in task_ids if t in content)
    scores["completion_times"] = (
        1.0 if tasks_found >= 4 else
        0.5 if tasks_found >= 2 else 0.0
    )

    # Check 2: Fastest and slowest identified
    has_fastest = any(kw in content for kw in ["fastest", "first to complete",
                                                 "earliest", "quickest"])
    has_slowest = any(kw in content for kw in ["slowest", "last to complete",
                                                 "longest", "straggler"])
    scores["fastest_slowest"] = (
        1.0 if has_fastest and has_slowest else
        0.5 if has_fastest or has_slowest else 0.0
    )

    # Check 3: Retried tasks flagged
    has_retry = any(kw in content for kw in ["retry", "retried", "reattempt",
                                               "second attempt", "_1"])
    has_slow_retry = any(kw in content for kw in ["m_000006", "m_000007"])
    scores["retries_flagged"] = (
        1.0 if has_retry and has_slow_retry else
        0.5 if has_retry else 0.0
    )

    # Check 4: Reduce timing analyzed
    has_reduce = "r_000000" in content or "reduce" in content
    has_reduce_time = any(t in content for t in ["15:42", "42:46"])
    scores["reduce_timing"] = (
        1.0 if has_reduce and has_reduce_time else
        0.5 if has_reduce else 0.0
    )

    return scores
```

---

## Additional Notes

**日志中的关键事实：**

- 作业在 15:37:56 开始，在约 15:42:47 结束
- Map 任务从约 15:38:00 开始分配容器
- 在足够多的 map 完成之前，未达到 reduce 慢启动阈值
- 两个任务（m_000006, m_000007）在第一次尝试时失败，重试后成功
- 重试为总 map 阶段时间增加了约 30-55 秒
- 关键路径通过最后一个 map 完成（15:41:25 的 m_000006）加上 reduce 阶段

**评分权重（相等）：** 五个标准各贡献 0.2 到最终分数。
