---
id: task_log_hdfs_slow_ops
name: HDFS DataNode 日志 - 慢操作检测
category: 日志分析
scene: 数据库检索、表格整理与数据分析
sub_scene: 日志时序分析
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 输出格式适配
- 自然语言生成
- 工具调用
grading_type: hybrid
timeout_seconds: 180
workspace_files:
  - dest: "hdfs_datanode.log"
    source: "logs/hdfs_datanode.log"
---

# HDFS DataNode 日志 - 慢操作检测

## Prompt

分析位于 `hdfs_datanode.log` 的 HDFS DataNode 日志，识别出耗时超出预期的操作。该日志记录了带时间戳的块接收、块分配和块复制操作。

你的报告应包含：

1. **块生命周期时序（Block Lifecycle Timing）**：对于同时存在 "Receiving block" 和 "Received block" 条目的块，计算其耗时
2. **分配到接收时序（Allocation-to-Receive Timing）**：对于同时存在 "allocateBlock" 和首个 "Receiving block" 条目的块，计算其延迟
3. **复制时序（Replication Timing）**：块分配后，复制请求多快被发出？
4. **最慢操作（Slowest Operations）**：按耗时对最慢的 5 个块操作进行排名
5. **块大小与耗时相关性（Block Size vs Time Correlation）**：更大的块是否耗时更长？在两者数据都可用时，将块大小与传输时间进行关联分析
6. **性能总结（Performance Summary）**：对该时段内集群性能的整体评估

将报告以结构良好的 markdown 文档写入 `hdfs_slow_ops_report.md`。

---

## Expected Behavior

Agent 应从日志格式 `YYMMDD HHMMSS` 中解析时间戳并计算：

**块生命周期：**
- 日志仅覆盖约 28 秒（203518 到 203546）
- 大多数块操作在 1-3 秒内完成
- 已确认的块接收及其大小：91178 字节、233217 字节、11971 字节、11977 字节

**关键观察：**
- blk_-1608999687919862906（91178 字节）：在 203518 分配，203518 首次接收，203519 确认（约 1 秒）
- blk_7503483334202473044（233217 字节）：在 203520 分配，203521 确认（约 1 秒）
- blk_-3544583377289625738（11971 字节）：在 203522-203523 确认
- 块操作非常快——与正常负载下健康集群的表现一致

**复制：**
- 针对 blk_-1608999687919862906 的 4 个复制请求，分别在 203521、203524、203527、203530 发出
- 各复制跳之间约间隔 3 秒

**性能：**
- 所有操作均在 1-3 秒内完成——未检测到慢操作
- 该快照期间集群运行良好

可接受的变化：
- 时间戳精度为 1 秒，因此部分时序分析将是近似的
- 匹配起止事件的不同方法均有效
- 块大小相关性分析可能因数据不足而无法得出有意义的结论

---

## Grading Criteria

- [ ] 工作区中创建了 `hdfs_slow_ops_report.md`
- [ ] 至少为一个块计算了块生命周期时序
- [ ] 在数据可用时将块大小与操作耗时进行了关联
- [ ] 正确识别了日志的时间范围（约 28 秒）
- [ ] 提供了性能评估

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """Grade the HDFS slow operation detection task."""
    from pathlib import Path

    scores = {}
    workspace = Path(workspace_path)
    report_file = workspace / "hdfs_slow_ops_report.md"

    if not report_file.exists():
        return {
            "output_created": 0.0,
            "lifecycle_timing": 0.0,
            "size_correlation": 0.0,
            "time_range": 0.0,
            "performance_assessment": 0.0,
        }

    scores["output_created"] = 1.0
    content = report_file.read_text(encoding="utf-8").lower()

    # Check 1: Block lifecycle timing calculated
    has_timing = any(kw in content for kw in ["1 second", "2 second", "3 second",
                                                "elapsed", "duration", "latency",
                                                "took", "completed in"])
    has_block = "blk_" in content or "blk-" in content or "block" in content
    scores["lifecycle_timing"] = (
        1.0 if has_timing and has_block else
        0.5 if has_timing or has_block else 0.0
    )

    # Check 2: Block sizes mentioned
    sizes = ["91178", "233217", "11971", "11977"]
    sizes_found = sum(1 for s in sizes if s in content)
    has_correlation = any(kw in content for kw in ["size", "bytes", "larger", "smaller"])
    scores["size_correlation"] = (
        1.0 if sizes_found >= 2 and has_correlation else
        0.5 if sizes_found >= 1 else 0.0
    )

    # Check 3: Time range identified
    has_28s = any(kw in content for kw in ["28 second", "~28", "30 second",
                                            "half a minute", "less than a minute"])
    has_timestamps = "203518" in content or "20:35:18" in content or "20:35" in content
    scores["time_range"] = (
        1.0 if has_28s or has_timestamps else
        0.5 if any(kw in content for kw in ["short", "brief", "seconds"]) else 0.0
    )

    # Check 4: Performance assessment
    perf_keywords = ["healthy", "normal", "fast", "no slow", "performing well",
                     "efficient", "optimal", "good performance"]
    scores["performance_assessment"] = (
        1.0 if sum(1 for kw in perf_keywords if kw in content) >= 1 else 0.0
    )

    return scores
```

---

## Additional Notes

**日志中的关键事实：**

- 时间戳格式：YYMMDD HHMMSS（例如 081109 203518 = 2008-11-09 20:35:18）
- 精度：1 秒——因此无法获得亚秒级时序
- 390 个唯一块，但只有约 19 个带有大小的已确认 "Received" 条目
- 集群处于活动突发期（作业启动），因此性能处于负载状态
- 没有错误或警告，表明所有操作均成功完成

**评分权重（均等）：** 五项标准中每项对最终得分贡献 0.2。
