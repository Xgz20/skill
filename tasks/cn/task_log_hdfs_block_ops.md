---
id: task_log_hdfs_block_ops
name: HDFS DataNode 日志 - 块操作汇总
category: 日志分析
scene: 数据库检索、表格整理与数据分析
sub_scene: HDFS 日志块操作分析
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 输出格式适配
- 指令遵循与约束理解
- 工具调用
grading_type: hybrid
timeout_seconds: 180
workspace_files:
  - dest: "hdfs_datanode.log"
    source: "logs/hdfs_datanode.log"
---

# HDFS DataNode 日志 - 块操作汇总

## Prompt

分析位于 `hdfs_datanode.log` 的 HDFS DataNode 日志，并生成一份所有块操作的全面汇总。该日志来自一个 HDFS 集群，记录了块的生命周期事件。

你的报告应包含：

1. **块清单（Block Inventory）**：日志中唯一块 ID 的总数，并附完整列表
2. **操作类型（Operation Types）**：对每种操作类型（allocateBlock、Receiving、Received、addStoredBlock、replicate、PacketResponder），统计总出现次数
3. **块生命周期追踪（Block Lifecycle Tracking）**：对每个具有完整生命周期（allocate → receive → stored）的块，记录完整链路
4. **复制链（Replication Chain）**：对有复制事件的块，追踪跨节点的复制路径
5. **关联作业（Associated Jobs）**：识别触发这些块操作的 MapReduce 作业（可在文件路径中看到）
6. **逐块明细表（Per-Block Detail Table）**：创建一个表格，列为：Block ID、Size（如已知）、Allocated Path、Nodes Involved、Replication Count

将报告写入 `hdfs_block_ops_report.md`，作为一份结构良好的 markdown 文档。

---

## Expected Behavior

Agent 应解析 2000 条日志条目并产出：

**块清单：**
- ~390 个唯一块 ID

**操作计数：**
- Receiving block: ~1149
- allocateBlock: ~385
- Received block: ~19
- addStoredBlock: ~19
- PacketResponder: ~12
- Replicate: 4

**完整块生命周期（具有完整数据的块）：**
- blk_-1608999687919862906: 91178 bytes，为 job_200811092030_0001/job.jar 分配
- blk_7503483334202473044: 233217 bytes，为 job_200811092030_0001/job.split 分配
- blk_-3544583377289625738: 11971 bytes
- blk_-9073992586687739851: 11977 bytes

**复制链：**
- blk_-1608999687919862906 在集群中被复制了 4 次：
  10.250.14.224 → 10.251.215.16 → 10.251.74.79 → 10.251.31.5 → 10.251.90.64

**关联作业：**
- job_200811092030_0001 — MapReduce 作业，文件：job.jar、job.split

可接受的变化：
- 块 ID 列表可以被截断
- 不需要所有 390 个块都有完整明细——只需具有完整生命周期数据的那些
- 表格格式可以不同

---

## Grading Criteria

- [ ] `hdfs_block_ops_report.md` 在工作区中被创建
- [ ] 提供了唯一块计数（~390）
- [ ] 统计了操作类型（receiving、allocate、replicate 等）
- [ ] 至少完整追踪了一个块的生命周期（allocate → receive → stored）
- [ ] 识别了关联的 MapReduce 作业（job_200811092030_0001）

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """Grade the HDFS block operations summary task."""
    from pathlib import Path

    scores = {}
    workspace = Path(workspace_path)
    report_file = workspace / "hdfs_block_ops_report.md"

    if not report_file.exists():
        return {
            "output_created": 0.0,
            "block_count": 0.0,
            "operations_counted": 0.0,
            "lifecycle_traced": 0.0,
            "job_identified": 0.0,
        }

    scores["output_created"] = 1.0
    content = report_file.read_text(encoding="utf-8").lower()

    # Check 1: Block count
    has_count = any(n in content for n in ["390", "~390", "385", "~385", "380", "~400"])
    scores["block_count"] = (
        1.0 if has_count else
        0.5 if any(kw in content for kw in ["hundred", "unique block"]) else 0.0
    )

    # Check 2: Operations counted
    op_keywords = ["receiving", "allocate", "replicate", "addstored",
                   "packetresponder", "received"]
    ops_found = sum(1 for kw in op_keywords if kw in content)
    scores["operations_counted"] = (
        1.0 if ops_found >= 4 else
        0.5 if ops_found >= 2 else 0.0
    )

    # Check 3: Block lifecycle traced
    lifecycle_keywords = ["91178", "233217", "blk_-1608999687919862906",
                          "blk_7503483334202473044", "lifecycle", "job.jar", "job.split"]
    scores["lifecycle_traced"] = (
        1.0 if sum(1 for kw in lifecycle_keywords if kw in content) >= 2 else
        0.5 if sum(1 for kw in lifecycle_keywords if kw in content) >= 1 else 0.0
    )

    # Check 4: MapReduce job identified
    has_job = "job_200811092030_0001" in content or "200811092030" in content
    has_mapreduce = "mapreduce" in content or "mapred" in content or "map reduce" in content
    scores["job_identified"] = (
        1.0 if has_job else
        0.5 if has_mapreduce else 0.0
    )

    return scores
```

---

## Additional Notes

**日志中的关键事实：**

- 大多数块只有 "Receiving" 和 "allocateBlock" 条目——集群处于操作中途
- 只有 ~19 个块具有完整的生命周期数据并带有确认的大小
- 390 个块 ID 代表一个 MapReduce 作业的数据正在集群中分发
- 仅 blk_-1608999687919862906 记录了复制，它被复制了 4 次
- 文件路径显示这与一个 MapReduce 作业相关：`/mnt/hadoop/mapred/system/job_200811092030_0001/`

**Grading weights (equal)：** 五项标准中每一项对最终得分贡献 0.2。
</content>
