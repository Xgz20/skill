---
id: task_log_mapreduce_jobs
name: MapReduce 日志 - 作业完成总结
category: 日志分析
scene: 本地环境、命令执行与脚本任务
sub_scene: 日志模式提取
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 输出格式适配
- 工具调用
grading_type: hybrid
timeout_seconds: 180
workspace_files:
  - dest: "mapreduce.log"
    source: "logs/hadoop_mapreduce.log"
---

# MapReduce 日志 - 作业完成总结

## Prompt

分析位于 `mapreduce.log` 的 Hadoop MapReduce 应用日志，产出一份全面的作业完成总结。该日志来自一个 MapReduce v2（YARN）应用。

你的报告应包含：

1. **作业标识（Job Identification）**：作业 ID、应用尝试 ID 以及作业名称/类型
2. **作业配置（Job Configuration）**：OutputCommitter 类型、文件系统以及其他配置细节
3. **任务汇总（Task Summary）**：map 任务总数、reduce 任务总数，以及各自成功完成的数量
4. **任务完成时间线（Task Completion Timeline）**：每个任务何时完成？创建一条带时间戳、展示任务完成顺序的时间线
5. **作业时长（Job Duration）**：从开始到结束的作业总运行时间
6. **最终状态（Final Status）**：作业成功还是失败？最终的状态转换是什么？

将报告以结构良好的 markdown 文档写入 `job_completion_report.md`。

---

## Expected Behavior

Agent 应解析 1282 条日志记录并产出：

**作业标识：**
- 作业 ID：job_1445062781478_0011
- 应用尝试：appattempt_1445062781478_0011_000001
- 作业类型：pagerank（在历史文件路径中可见）
- 用户：msrabi

**配置：**
- OutputCommitter：FileOutputCommitter
- 文件系统：hdfs://msra-sa-41:9000
- API：mapred newApiCommitter

**任务汇总：**
- 10 个 map 任务（m_000000 至 m_000009），外加 2 次重试（m_000006_1、m_000007_1）
- 1 个 reduce 任务（r_000000）
- 全部 11 个任务成功完成（10 个 map + 1 个 reduce）
- 共 12 次 map 任务尝试，1 次 reduce 任务尝试

**时间线：**
- 作业开始：15:37:56
- 首个 map 完成：15:39:24（m_000009）
- 最后一个 map 完成：15:41:25（m_000006）
- reduce 完成：15:42:46（r_000000）
- 作业结束：约 15:42:47

**时长：** 约 5 分钟（15:37:56 至 15:42:47）

**最终状态：** SUCCEEDED

可接受的变化：
- 时间线格式可能有所不同
- 时长计算方法可能不同
- 任务编号记法可能有所差异

---

## Grading Criteria

- [ ] 工作区中创建了 `job_completion_report.md`
- [ ] 识别出作业 ID（job_1445062781478_0011）
- [ ] map 和 reduce 任务数量正确（10 个 map 任务，1 个 reduce 任务）
- [ ] 计算了作业时长（约 5 分钟）
- [ ] 最终状态被识别为 SUCCEEDED

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """Grade the MapReduce job completion summary task."""
    from pathlib import Path

    scores = {}
    workspace = Path(workspace_path)
    report_file = workspace / "job_completion_report.md"

    if not report_file.exists():
        return {
            "output_created": 0.0,
            "job_id": 0.0,
            "task_counts": 0.0,
            "duration": 0.0,
            "final_status": 0.0,
        }

    scores["output_created"] = 1.0
    content = report_file.read_text(encoding="utf-8").lower()

    # Check 1: Job ID identified
    scores["job_id"] = (
        1.0 if "job_1445062781478_0011" in content or "1445062781478_0011" in content else 0.0
    )

    # Check 2: Task counts correct
    has_10_map = any(kw in content for kw in ["10 map", "ten map", "10 mapper"])
    has_1_reduce = any(kw in content for kw in ["1 reduce", "one reduce", "single reduce",
                                                  "1 reducer"])
    scores["task_counts"] = (
        1.0 if has_10_map and has_1_reduce else
        0.5 if has_10_map or has_1_reduce else 0.0
    )

    # Check 3: Duration calculated
    duration_keywords = ["5 minute", "~5 min", "4 minute", "4:51", "4:50",
                         "approximately 5", "about 5", "15:37", "15:42",
                         "nearly 5"]
    scores["duration"] = (
        1.0 if sum(1 for kw in duration_keywords if kw in content) >= 1 else 0.0
    )

    # Check 4: Final status
    scores["final_status"] = (
        1.0 if "succeeded" in content else
        0.5 if "success" in content or "completed" in content else 0.0
    )

    return scores
```

---

## Additional Notes

**日志中的关键事实：**

- 单个 MapReduce 作业：由用户 "msrabi" 执行的 pagerank 计算
- 基于 YARN（v2 MapReduce），集群的 namenode 为 msra-sa-41
- 10 个 map 任务对应 12 次 map 任务尝试（m_000006 和 m_000007 各有一次重试）
- 作业历史文件确认了 SUCCEEDED 状态，包含 10 个 map 和 1 个 reduce
- 2015 年 10 月 17 日
- 可见容器分配：共使用 13 个唯一容器

**评分权重（均等）：** 五项标准中每项对最终得分贡献 0.2。
