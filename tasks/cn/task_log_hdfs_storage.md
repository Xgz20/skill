---
id: task_log_hdfs_storage
name: HDFS DataNode 日志 - 存储与容量分析
category: 日志分析
scene: 数据库检索、表格整理与数据分析
sub_scene: HDFS 日志存储分析
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 领域推理
- 输出格式适配
- 自然语言生成
grading_type: hybrid
timeout_seconds: 180
workspace_files:
  - dest: "hdfs_datanode.log"
    source: "logs/hdfs_datanode.log"
---

# HDFS DataNode 日志 - 存储与容量分析

## Prompt

分析位于 `hdfs_datanode.log` 的 HDFS DataNode 日志，产出一份聚焦存储的分析报告。检查块大小、跨节点的数据分布以及存储模式。

你的报告应包含：

1. **数据量（Data Volume）**：所有已确认块接收（已知大小）的总存储字节数
2. **块大小分布（Block Size Distribution）**：列出所有已知块大小，计算最小值/最大值/平均值/中位数
3. **按节点的数据分布（Data Distribution by Node）**：对每个确认接收块的节点（PacketResponder "Received" 条目），统计其存储的总字节数
4. **存储路径分析（Storage Path Analysis）**：正在使用哪些存储路径？（从 allocateBlock 的文件路径中提取）
5. **复制因子（Replication Factor）**：根据有多少节点接收同一个块，有效复制因子是多少？
6. **容量规划（Capacity Planning）**：根据观察到的数据写入速率，估算 1 小时类似活动所需的存储空间

将报告以结构良好的 markdown 文档写入 `hdfs_storage_report.md`。

---

## Expected Behavior

Agent 应解析日志并计算：

**已确认的块大小：**
- blk_-1608999687919862906：91,178 字节（被 3 个以上节点接收）
- blk_7503483334202473044：233,217 字节（被 3 个节点接收）
- blk_-3544583377289625738：11,971 字节（被 3 个节点接收）
- blk_-9073992586687739851：11,977 字节（被 3 个节点接收）

**块大小统计：**
- 最小值：11,971 字节（约 12 KB）
- 最大值：233,217 字节（约 228 KB）
- 平均值：约 87,086 字节（约 85 KB）
- 已确认总数据量：每个副本约 348,343 字节

**复制因子：**
- 每个已确认的块都被 3 个节点接收 → 复制因子为 3
- 这是标准的 HDFS 默认复制配置

**存储路径：**
- `/mnt/hadoop/mapred/system/job_200811092030_0001/` —— MapReduce 作业暂存目录
- 文件：job.jar、job.split

**容量规划：**
- 约 28 秒的活动产生了约 390 次块分配
- 若每个块平均约 85 KB、复制因子为 3，则约为 100 MB/分钟的原始存储
- 1 小时估算：约 6 GB（粗略）

可接受的变化：
- 鉴于已确认大小有限，容量估算会非常粗略
- 外推方法会有所不同
- 统计应仅基于已确认的大小

---

## Grading Criteria

- [ ] 工作区中创建了 `hdfs_storage_report.md`
- [ ] 列出了已知块大小（91178、233217、11971、11977）
- [ ] 计算了块大小统计（最小值、最大值、平均值）
- [ ] 识别出复制因子（3）
- [ ] 从日志中提取了存储路径

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """Grade the HDFS storage and capacity analysis task."""
    from pathlib import Path

    scores = {}
    workspace = Path(workspace_path)
    report_file = workspace / "hdfs_storage_report.md"

    if not report_file.exists():
        return {
            "output_created": 0.0,
            "block_sizes_listed": 0.0,
            "statistics_calculated": 0.0,
            "replication_factor": 0.0,
            "storage_paths": 0.0,
        }

    scores["output_created"] = 1.0
    content = report_file.read_text(encoding="utf-8").lower()

    # Check 1: Block sizes listed
    sizes = ["91178", "233217", "11971", "11977"]
    sizes_found = sum(1 for s in sizes if s in content)
    scores["block_sizes_listed"] = (
        1.0 if sizes_found >= 3 else
        0.5 if sizes_found >= 1 else 0.0
    )

    # Check 2: Statistics calculated
    stat_keywords = ["min", "max", "mean", "median", "average", "total",
                     "distribution", "range"]
    scores["statistics_calculated"] = (
        1.0 if sum(1 for kw in stat_keywords if kw in content) >= 3 else
        0.5 if sum(1 for kw in stat_keywords if kw in content) >= 1 else 0.0
    )

    # Check 3: Replication factor identified
    has_replication = any(kw in content for kw in ["replication factor",
                                                     "replication of 3",
                                                     "factor of 3",
                                                     "3 replicas",
                                                     "three replicas",
                                                     "3 copies",
                                                     "three copies",
                                                     "replicated 3",
                                                     "3 nodes"])
    scores["replication_factor"] = 1.0 if has_replication else 0.0

    # Check 4: Storage paths extracted
    has_path = any(p in content for p in ["/mnt/hadoop", "job_200811092030",
                                           "mapred/system", "job.jar", "job.split"])
    scores["storage_paths"] = 1.0 if has_path else 0.0

    return scores
```

---

## Additional Notes

**日志中的关键事实：**

- 日志中仅确认了 4 个唯一块大小（来自 PacketResponder "Received" 条目）
- 共分配了 390 个块，但在日志窗口内仅出现约 19 个接收确认
- 标准 HDFS 复制因子为 3，与每个块的 3 个接收确认相吻合
- addStoredBlock 条目（19 个）更新了 NameSystem 的块映射
- 存储位于 `/mnt/hadoop/mapred/system/` 下——标准 MapReduce 暂存目录

**评分权重（均等）：** 五项标准中每项对最终得分贡献 0.2。
