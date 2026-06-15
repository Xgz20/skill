---
id: task_log_hdfs_connections
name: HDFS DataNode 日志 - 连接模式分析
category: 日志分析
scene: 数据库检索、表格整理与数据分析
sub_scene: 日志连接分析
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 输出格式适配
- 工具调用
grading_type: hybrid
timeout_seconds: 180
workspace_files:
  - dest: "hdfs_datanode.log"
    source: "logs/hdfs_datanode.log"
---

# HDFS DataNode 日志 - 连接模式分析

## Prompt

分析位于 `hdfs_datanode.log` 的 HDFS DataNode 日志，并生成一份关于节点间连接与通信模式的报告。该日志包含来自 DataNode、FSNamesystem 和 PacketResponder 组件的条目。

你的报告应包含：

1. **网络拓扑（Network Topology）**：列出日志中出现的所有唯一 IP 地址，按其角色分类（source、destination 或两者兼有）
2. **子网分析（Subnet Analysis）**：按子网对 IP 进行分组（例如 10.250.x.x 与 10.251.x.x）。每个子网中有多少个节点？
3. **最活跃节点（Most Active Nodes）**：按出现频率（作为 source 或 destination）排名前 10 的 IP
4. **通信模式（Communication Patterns）**：哪些节点对之间通信最频繁？
5. **DataNode 与 NameSystem（DataNode vs NameSystem）**：区分活动——哪些来自 DataNode 操作，哪些来自 FSNamesystem 操作？
6. **集群规模估计（Cluster Size Estimate）**：基于观察到的 IP，估计集群规模

将报告写入 `hdfs_connections_report.md`，作为一份结构良好的 markdown 文档。

---

## Expected Behavior

Agent 应解析 2000 条日志条目并产出：

**网络拓扑：**
- 观察到 202 个唯一 IP 地址
- IP 落在 10.250.x.x 和 10.251.x.x 范围内（私有网络）
- 所有节点都使用端口 50010（HDFS DataNode 数据传输端口）

**子网分析：**
- 10.250.x.x 子网——包含一些最活跃的节点
- 10.251.x.x 子网——包含额外的 DataNode 集群成员
- 这种划分表明这是一个多机架的 HDFS 部署

**最活跃节点：**
- 10.250.19.102 — 极其活跃（在许多块传输中作为 source 出现）
- 10.250.10.6、10.251.215.16、10.250.14.224 — 同样非常活跃

**组件活动：**
- DataNode$DataXceiver: 块接收操作（~1149 条目）
- FSNamesystem: 块分配和存储追踪（~400+ 条目）
- DataNode$PacketResponder: 带大小的块接收确认

可接受的变化：
- 精确的 IP 计数和排名可能因解析方法不同而变化
- 子网分组的粒度可以不同
- 集群规模估计将是近似的

---

## Grading Criteria

- [ ] `hdfs_connections_report.md` 在工作区中被创建
- [ ] 唯一 IP 被列出或计数（~202）
- [ ] IP 按子网分组（10.250.x.x 与 10.251.x.x）
- [ ] 识别出最活跃节点
- [ ] 区分了 DataNode 与 FSNamesystem 活动

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """Grade the HDFS connection pattern analysis task."""
    from pathlib import Path

    scores = {}
    workspace = Path(workspace_path)
    report_file = workspace / "hdfs_connections_report.md"

    if not report_file.exists():
        return {
            "output_created": 0.0,
            "ips_listed": 0.0,
            "subnets_grouped": 0.0,
            "active_nodes": 0.0,
            "components_separated": 0.0,
        }

    scores["output_created"] = 1.0
    content = report_file.read_text(encoding="utf-8").lower()

    # Check 1: IPs listed/counted
    has_count = any(n in content for n in ["202", "200", "~200", "over 200"])
    has_ips = "10.250" in content and "10.251" in content
    scores["ips_listed"] = (
        1.0 if has_count and has_ips else
        0.5 if has_ips else 0.0
    )

    # Check 2: Subnets grouped
    subnet_keywords = ["subnet", "10.250", "10.251", "rack", "network segment",
                       "address range", "ip range"]
    scores["subnets_grouped"] = (
        1.0 if "10.250" in content and "10.251" in content and
              sum(1 for kw in subnet_keywords if kw in content) >= 2 else
        0.5 if "10.250" in content and "10.251" in content else 0.0
    )

    # Check 3: Active nodes identified
    active_ips = ["10.250.19.102", "10.251.215.16", "10.250.14.224", "10.250.10.6"]
    ips_found = sum(1 for ip in active_ips if ip in content)
    scores["active_nodes"] = (
        1.0 if ips_found >= 2 else
        0.5 if ips_found >= 1 else 0.0
    )

    # Check 4: Components separated
    component_keywords = ["dataxceiver", "dataxeceiver", "fsnamesystem",
                          "packetresponder", "namenode", "datanode"]
    scores["components_separated"] = (
        1.0 if sum(1 for kw in component_keywords if kw in content) >= 2 else
        0.5 if sum(1 for kw in component_keywords if kw in content) >= 1 else 0.0
    )

    return scores
```

---

## Additional Notes

**日志中的关键事实：**

- 202 个唯一 IP——这是一个大型 HDFS 集群
- 两个主要子网：10.250.x.x 和 10.251.x.x
- 全程使用端口 50010——标准 HDFS DataNode 端口
- 10.250.19.102 在不成比例的大量条目中作为 source 出现
- 该日志捕获了与 job_200811092030_0001 相关的一次活动爆发

**Grading weights (equal)：** 五项标准中每一项对最终得分贡献 0.2。
</content>
