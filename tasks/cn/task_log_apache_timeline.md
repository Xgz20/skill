---
id: task_log_apache_timeline
name: Apache 错误日志 - 创建错误时间线
category: 日志分析
scene: 数据库检索、表格整理与数据分析
sub_scene: 日志时间线分析
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 输出格式适配
- 指令遵循与约束理解
grading_type: hybrid
timeout_seconds: 180
workspace_files:
  - dest: "apache_error.log"
    source: "logs/apache_error.log"
---

# Apache 错误日志 - 创建错误时间线

## Prompt

分析位于 `apache_error.log` 的 Apache 错误日志，并创建一个重要事件的时间线。日志时间跨度从 2005 年 6 月 9 日星期四到 2005 年 6 月 16 日星期四。

对于每一天，识别：

1. error 级别条目的数量
2. 值得注意的事件（服务器重启、攻击爆发、异常活动激增）
3. 任何活动集中的时段（短时间窗口内出现大量错误）

此外，识别整个日志中**单次最密集的活动爆发**——包含最多错误条目的最短时间窗口——并描述这次爆发期间发生了什么。

将你的发现写入 `error_timeline.json`，结构如下：

```json
{
  "date_range": "2005-06-09 to 2005-06-16",
  "daily_summary": [
    {
      "date": "2005-06-09",
      "day_of_week": "Thursday",
      "error_count": 50,
      "notable_events": ["Description of what happened"]
    }
  ],
  "peak_burst": {
    "start_time": "2005-06-11 03:03:03",
    "end_time": "2005-06-11 03:04:02",
    "duration_seconds": 59,
    "error_count": 150,
    "description": "What caused this burst"
  }
}
```

---

## Expected Behavior

Agent 应解析时间戳并按天对条目进行分组。预期的每日明细（近似值）：

| Date | Day | Error Count | Notable Events |
|---|---|---|---|
| Jun 9 | Thu | ~50 | 服务器启动，JK connector 错误，目录扫描开始 |
| Jun 10 | Fri | ~80 | 11:32 服务器重启，IIS 蠕虫探测（Invalid method），210.22.201.x 子网扫描 |
| Jun 11 | Sat | ~350+ | **重大爆发**：来自 202.133.98.6 的 03:03（awstats 扫描导致 scoreboard 耗尽和 mod_jk2 关闭），IIS 蠕虫探测持续 |
| Jun 12 | Sun | ~100 | 04:04 优雅重启，210.91.137.35 探测 _vti_bin，URI too long 攻击 |
| Jun 13 | Mon | ~90 | 195.23.79.241 大规模扫描（~22 个错误），218.68.233.47 扫描，218.82.188.130 扫描 |
| Jun 14 | Tue | ~80 | 81.214.165.213 探测 _vti_bin（23 次请求），60.191.134.226 大规模扫描（19 次请求） |
| Jun 15 | Wed | ~50 | 219.133.247.159 扫描（18 次请求），URI too long 攻击，常规目录扫描 |
| Jun 16 | Thu | ~3 | 仅 2-3 个条目（日志可能在当天早些时候被截断） |

**峰值爆发**是 6 月 11 日星期六来自 202.133.98.6 的 awstats 扫描，开始于约 03:03:03，在不到 10 分钟内产生约 150+ 个错误条目。这次爆发非常密集，导致 Apache 派生了许多新的子进程（可从 jk2_init scoreboard slot 消息看出），并触发了一连串的 mod_jk2 关闭。

可接受的变化：
- 每日计数可能因边界处理方式不同而有 ±15 的偏差
- 峰值爆发的识别是关键洞察——时间和 IP 应匹配
- 星期标签可以省略

---

## Grading Criteria

- [ ] `error_timeline.json` 在工作区中被创建
- [ ] 每日明细覆盖 8 天中至少 5 天并附带错误计数
- [ ] 6 月 11 日（星期六）被识别为错误最多的一天
- [ ] 峰值爆发被归因于 202.133.98.6 或 6 月 11 日约 03:03 的 awstats 扫描
- [ ] 记录了服务器重启事件（至少包含以下之一：6 月 9 日、6 月 10 日、6 月 12 日的启动）

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """Grade the Apache error log timeline task."""
    from pathlib import Path
    import json

    scores = {}
    workspace = Path(workspace_path)
    report_file = workspace / "error_timeline.json"

    if not report_file.exists():
        return {
            "output_created": 0.0,
            "daily_breakdown": 0.0,
            "peak_day_identified": 0.0,
            "peak_burst_identified": 0.0,
            "server_restarts_noted": 0.0,
        }

    scores["output_created"] = 1.0

    try:
        data = json.loads(report_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, Exception):
        return {
            "output_created": 1.0,
            "daily_breakdown": 0.0,
            "peak_day_identified": 0.0,
            "peak_burst_identified": 0.0,
            "server_restarts_noted": 0.0,
        }

    full_text = json.dumps(data).lower()

    # Check 1: Daily breakdown with at least 5 days
    daily = data.get("daily_summary", [])
    if not isinstance(daily, list):
        daily = []
    days_with_counts = sum(
        1 for d in daily
        if isinstance(d, dict) and isinstance(d.get("error_count"), (int, float)) and d.get("error_count", 0) > 0
    )
    scores["daily_breakdown"] = (
        1.0 if days_with_counts >= 5 else
        0.5 if days_with_counts >= 3 else 0.0
    )

    # Check 2: June 11 identified as peak day
    jun11_found = False
    max_count = 0
    max_date = ""
    for d in daily:
        if not isinstance(d, dict):
            continue
        date_str = str(d.get("date", ""))
        count = d.get("error_count", 0)
        if isinstance(count, (int, float)) and count > max_count:
            max_count = count
            max_date = date_str
        if "06-11" in date_str or "jun 11" in date_str.lower():
            jun11_found = True

    scores["peak_day_identified"] = (
        1.0 if ("06-11" in max_date or "jun 11" in max_date.lower()) else
        0.5 if jun11_found else 0.0
    )

    # Check 3: Peak burst identified (202.133.98.6 or awstats on Jun 11 ~03:03)
    burst = data.get("peak_burst", {})
    burst_text = json.dumps(burst).lower() if isinstance(burst, dict) else full_text
    has_burst_ip = "202.133.98.6" in burst_text
    has_burst_awstats = "awstats" in burst_text
    has_burst_time = any(t in burst_text for t in ["03:03", "jun 11", "06-11", "saturday"])
    scores["peak_burst_identified"] = (
        1.0 if (has_burst_ip or has_burst_awstats) and has_burst_time else
        0.5 if has_burst_ip or has_burst_awstats else 0.0
    )

    # Check 4: Server restarts noted
    restart_keywords = ["restart", "startup", "configured -- resuming", "startup",
                        "graceful", "resuming normal operations"]
    scores["server_restarts_noted"] = (
        1.0 if any(kw in full_text for kw in restart_keywords) else 0.0
    )

    return scores
```

---

## Additional Notes

**日志中的服务器生命周期事件：**

| Timestamp | Event |
|---|---|
| Thu Jun 9 06:07 | 初始服务器启动（Apache/2.0.49 configured） |
| Fri Jun 10 11:32 | 服务器重启（重复完整的启动序列） |
| Sun Jun 12 04:04 | 请求优雅重启 |

**6 月 11 日 202.133.98.6 的爆发：**
- 始于 03:03:03，结束于约 03:04:02
- 在约 70 秒内产生 ~150+ 个错误条目
- 导致 Apache 派生许多新子进程（scoreboard slots 8→70）
- 在旧 worker 被替换时触发级联的 mod_jk2 shutdown 消息
- 这单次爆发约占 6 月 11 日所有错误的一半

**Grading weights (equal)：** 五项标准中每一项对最终得分贡献 0.2。
</content>
</invoke>
