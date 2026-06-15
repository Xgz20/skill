---
id: task_log_nginx_traffic
name: Nginx 访问日志 - 按时间维度的流量模式分析
category: 日志分析
scene: 数据库检索、表格整理与数据分析
sub_scene: nginx日志流量分析
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 工具调用
- 输出格式适配
- 自然语言生成
grading_type: hybrid
timeout_seconds: 180
workspace_files:
  - dest: "nginx_access.log"
    source: "logs/nginx_access_json.log"
---

# Nginx 访问日志 - 按时间维度的流量模式分析

## Prompt

分析位于 `nginx_access.log` 的 Nginx JSON 访问日志，并生成一份按时间维度的流量模式报告。每一行都是一个 JSON 对象，包含以下字段：`time`、`remote_ip`、`remote_user`、`request`、`response`、`bytes`、`referrer`、`agent`。

你的报告应当包括：

1. **时间范围**：日志覆盖的完整日期/时间范围
2. **逐小时流量分解**：每小时的请求数量
3. **流量峰值与低谷**：识别最繁忙和最空闲的小时
4. **带宽随时间变化**：每小时传输的总字节数
5. **请求速率趋势**：请求是平稳的、突发的，还是呈现某种趋势？
6. **各 IP 随时间的活动情况**：识别那些跨越多个小时出现的 IP，以及那些只在突发时段出现的 IP

将报告写入 `traffic_report.md`，作为一份结构良好的 markdown 文档。

---

## Expected Behavior

Agent 应当解析全部 1000 条 JSON 日志条目，并生成：

**时间范围：** 2015 年 5 月 17 日 08:05:01 至 16:05:10 UTC（约 8 小时）

**逐小时分解（近似）：**
- 08:xx — 日志从该小时的中段开始
- 流量分布在 8 小时的时间窗口内
- 日志包含时间戳在 08:05 至 16:05 之间的条目

**关键观察：**
- 整个时段内有 73 个唯一客户端 IP
- 80.91.33.133 是最持续的客户端（约 210 个请求，分散在整个时间范围内）
- 大部分流量是 Debian APT 包管理器流量（自动更新）
- 传输的字节数各不相同 — 304（Not Modified）响应为 0 字节；200 响应的字节数最高可达约 3318 字节
- 该服务器看起来是一个软件下载/仓库镜像

可接受的变化：
- 具体的逐小时计数可能因解析方法不同而有所差异
- 任何合理的分桶方法（按小时、30 分钟等）都可接受
- 趋势分析的措辞会有所不同

---

## Grading Criteria

- [ ] 在工作区中创建了 `traffic_report.md`
- [ ] 识别出时间范围（2015 年 5 月 17 日；约 08:05–16:05 UTC）
- [ ] 流量按时间段（按小时或类似方式）进行了分解
- [ ] 识别出峰值/最繁忙的时段
- [ ] 分析了带宽或传输的字节数

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """Grade the Nginx traffic patterns task."""
    from pathlib import Path

    scores = {}
    workspace = Path(workspace_path)
    report_file = workspace / "traffic_report.md"

    if not report_file.exists():
        return {
            "output_created": 0.0,
            "time_range": 0.0,
            "hourly_breakdown": 0.0,
            "peak_identified": 0.0,
            "bandwidth_analysis": 0.0,
        }

    scores["output_created"] = 1.0
    content = report_file.read_text(encoding="utf-8").lower()

    # Check 1: Time range identified
    has_date = any(d in content for d in ["may 17", "2015-05-17", "17/may/2015", "may 2015"])
    has_range = any(t in content for t in ["08:05", "16:05", "8 hour", "eight hour"])
    scores["time_range"] = (
        1.0 if has_date and has_range else
        0.5 if has_date else 0.0
    )

    # Check 2: Traffic broken down by time period
    time_keywords = ["hour", "period", "interval", "08:", "09:", "10:", "11:", "12:",
                     "13:", "14:", "15:", "16:"]
    time_sections = sum(1 for kw in time_keywords if kw in content)
    scores["hourly_breakdown"] = (
        1.0 if time_sections >= 4 else
        0.5 if time_sections >= 2 else 0.0
    )

    # Check 3: Peak/busiest periods identified
    peak_keywords = ["peak", "busiest", "highest", "most active", "maximum",
                     "lowest", "quietest", "least"]
    scores["peak_identified"] = (
        1.0 if sum(1 for kw in peak_keywords if kw in content) >= 2 else
        0.5 if sum(1 for kw in peak_keywords if kw in content) >= 1 else 0.0
    )

    # Check 4: Bandwidth/bytes analysis
    bandwidth_keywords = ["bytes", "bandwidth", "transfer", "data", "0 bytes",
                          "304", "not modified"]
    scores["bandwidth_analysis"] = (
        1.0 if sum(1 for kw in bandwidth_keywords if kw in content) >= 2 else
        0.5 if sum(1 for kw in bandwidth_keywords if kw in content) >= 1 else 0.0
    )

    return scores
```

---

## Additional Notes

**日志中的关键事实：**

- 2015 年 5 月 17 日约 8 小时内的 1000 条 JSON 条目
- 时间戳格式为 `17/May/2015:HH:MM:SS +0000`
- 该日志来自一个提供 APT 包仓库服务的下载服务器
- 大多数传输的字节数都很小（200 响应最大约 3318 字节）
- 304 Not Modified 响应携带 0 字节 — 这对带宽分析很重要

**评分权重（均等）：** 五项标准中每一项对最终得分贡献 0.2。
