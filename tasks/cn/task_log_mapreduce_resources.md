---
id: task_log_mapreduce_resources
name: MapReduce 日志 - 资源利用率分析
category: 日志分析
scene: 数据库检索、表格整理与数据分析
sub_scene: 日志模式提取
difficulty: L2
capabilities:
- 工具调用
- 数据提取与处理
- 输出格式适配
- 多步推理
- 指令遵循与约束理解
grading_type: hybrid
timeout_seconds: 180
workspace_files:
  - dest: "mapreduce.log"
    source: "logs/hadoop_mapreduce.log"
---

# MapReduce 日志 - 资源利用率分析

## Prompt

分析位于 `mapreduce.log` 的 Hadoop MapReduce 应用日志，并产出一份资源利用率报告。重点关注容器分配、调度以及资源使用模式。

你的报告应包括：

1. **容器清单**：列出为此作业分配的所有容器及其 ID
2. **容器分配时间线**：每个容器是何时被请求和分配的？
3. **调度分析**：根据 RMContainerAllocator 条目，跟踪待处理的 map 和 reduce 数量随时间的变化
4. **Reduce 调度**：reduce 慢启动阈值何时被满足？此时的完成百分比是多少？
5. **容器复用**：是否有容器完成后被复用？
6. **资源效率**：基于容器分配与任务完成模式，评估资源效率

将报告写入 `mapreduce_resources.md`，格式为结构良好的 markdown 文档。

---

## Expected Behavior

Agent 应解析 RMContainerAllocator 条目并产出：

**容器清单：**
- 使用了 13 个唯一容器（container_1445062781478_0011_01_000001 至 000013）
- 应用尝试：01

**调度进展：**
- 初始状态：10 个待处理 map，1 个待处理 reduce
- 从 15:38:00 到 15:39:24，reduce 慢启动阈值反复"未满足"（not met）
- 第一个 map 在 15:39:24 完成（完成 10%）—— 仍不足以启动 reduce
- 当 completedMapPercent 达到足够阈值时开始 reduce 调度
- 15:39:24 记录了 "completedMapPercent 0.1 totalResources 2"

**容器生命周期：**
- 容器在 15:38:00–15:38:15 左右被分配
- 任务完成后容器被释放
- "Received completed container" 条目跟踪容器何时完成

**关键观察：**
- reduce 任务必须等待足够多的 map 完成（慢启动）
- map 任务的完成时间各不相同（1.5 到 3.5 分钟）
- 容器周转：部分容器被释放，其资源被迅速释放

可接受的变化：
- 容器 ID 的枚举方式可能有所不同
- 时间线粒度可能不同
- 资源效率评估带有主观性

---

## Grading Criteria

- [ ] 工作区中创建了 `mapreduce_resources.md`
- [ ] 列出了容器（识别出 13 个容器）
- [ ] 跟踪了调度进展（待处理 map/reduce 随时间的变化）
- [ ] 包含 reduce 慢启动阈值的讨论
- [ ] 分析了容器完成事件

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """Grade the MapReduce resource utilization analysis task."""
    from pathlib import Path

    scores = {}
    workspace = Path(workspace_path)
    report_file = workspace / "mapreduce_resources.md"

    if not report_file.exists():
        return {
            "output_created": 0.0,
            "containers_listed": 0.0,
            "scheduling_tracked": 0.0,
            "slow_start": 0.0,
            "container_completion": 0.0,
        }

    scores["output_created"] = 1.0
    content = report_file.read_text(encoding="utf-8").lower()

    # Check 1: Containers listed
    has_container = "container_" in content or "container" in content
    has_count = any(n in content for n in ["13 container", "13 unique", "thirteen"])
    scores["containers_listed"] = (
        1.0 if has_container and has_count else
        0.5 if has_container else 0.0
    )

    # Check 2: Scheduling tracked
    sched_keywords = ["pending", "scheduled", "pendingreds", "pendingmaps",
                      "scheduledmaps", "scheduling"]
    scores["scheduling_tracked"] = (
        1.0 if sum(1 for kw in sched_keywords if kw in content) >= 2 else
        0.5 if sum(1 for kw in sched_keywords if kw in content) >= 1 else 0.0
    )

    # Check 3: Reduce slow start discussed
    slow_start_keywords = ["slow start", "slowstart", "threshold", "reduce.*wait",
                           "completedmappercent", "not met"]
    scores["slow_start"] = (
        1.0 if sum(1 for kw in slow_start_keywords if kw in content) >= 2 else
        0.5 if sum(1 for kw in slow_start_keywords if kw in content) >= 1 else 0.0
    )

    # Check 4: Container completion analyzed
    completion_keywords = ["completed container", "container released", "received completed",
                           "container finish", "freed"]
    scores["container_completion"] = (
        1.0 if sum(1 for kw in completion_keywords if kw in content) >= 1 else
        0.5 if "complet" in content else 0.0
    )

    return scores
```

---

## Additional Notes

**日志中的关键事实：**

- 基于 YARN 的 MapReduce（v2），运行在带有 RM 的集群上
- 13 个容器用于 10 个 map 任务 + 1 个 reduce + 1 个 AM 容器 + 重试
- reduce 慢启动阈值是标准的 Hadoop 优化机制
- "Before Scheduling" / "After Scheduling" 条目提供了调度状态快照
- 最终统计："PendingReds:0 ScheduledMaps:0" —— 所有资源已释放

**评分权重（相等）：** 五个标准各贡献 0.2 到最终分数。
