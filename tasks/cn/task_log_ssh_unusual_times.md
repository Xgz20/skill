---
id: task_log_ssh_unusual_times
name: SSH 认证日志 - 异常时段登录检测
category: 日志分析
scene: 数据库检索、表格整理与数据分析
sub_scene: 日志时间维度分析
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 输出格式适配
- 指令遵循与约束理解
grading_type: hybrid
timeout_seconds: 180
workspace_files:
  - dest: "auth.log"
    source: "logs/openssh_auth.log"
---

# SSH 认证日志 - 异常时段登录检测

## Prompt

分析位于 `auth.log` 的 OpenSSH 认证日志，识别发生在异常时段的登录活动。假定正常工作时间为服务器本地时间 08:00–18:00。

你的报告应当包括：

1. **逐小时分布**：每小时的认证事件计数
2. **非工作时段活动**：所有发生在 08:00 之前或 18:00 之后的认证事件
3. **清晨分析**：对 06:00–08:00 之间事件的详细分解（日志中最早的时段）
4. **成功登录时间**：成功登录发生在何时？是否在工作时间内？
5. **攻击时间模式**：攻击者是否偏好特定时段？是否存在某种规律？
6. **时间维度风险评估**：根据时间模式，哪些时段应被最密切地监控？

将报告写入 `unusual_hours_report.md`，作为一份结构良好的 markdown 文档。

---

## Expected Behavior

Agent 应当解析日志并生成：

**逐小时分布：**
- 06:xx — 7 条记录（日志从 06:55 开始）
- 07:xx — 169 条记录
- 08:xx — 118 条记录
- 09:xx — 676 条记录（峰值小时）
- 10:xx — 530 条记录（日志在 10:59 结束）

**非工作时段活动：**
- 07:00 之前有 7 条记录（在 06:55–06:56）
- 所有 08:00 之前的记录都是攻击流量（失败登录、BREAK-IN 警告）

**成功登录时间：**
- 用户 fztu 在 09:32:20 登录 — 在工作时间内

**攻击时间模式：**
- 攻击从 07:xx 到 09:xx 急剧升级
- 攻击量峰值出现在 09:xx，达 676 条记录
- 这可能表明攻击者处于不同时区，那里的工作时间对应 LabSZ 时间的 09:00
- 清晨的记录（06:55）代表某次攻击行动的尾段或起始

可接受的变化：
- "异常时段" 的定义可能有所不同
- 时区假设可能有所差异
- 评估措辞会有所不同

---

## Grading Criteria

- [ ] 在工作区中创建了 `unusual_hours_report.md`
- [ ] 提供了事件的逐小时分布
- [ ] 单独识别出非工作时段（08:00 之前）的事件
- [ ] 注明了成功登录的时间（09:32:20，在工作时间内）
- [ ] 分析了攻击时间模式

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """Grade the SSH unusual hours detection task."""
    from pathlib import Path

    scores = {}
    workspace = Path(workspace_path)
    report_file = workspace / "unusual_hours_report.md"

    if not report_file.exists():
        return {
            "output_created": 0.0,
            "hourly_distribution": 0.0,
            "off_hours_identified": 0.0,
            "successful_timing": 0.0,
            "timing_patterns": 0.0,
        }

    scores["output_created"] = 1.0
    content = report_file.read_text(encoding="utf-8").lower()

    # Check 1: Hourly distribution provided
    hour_markers = ["06:", "07:", "08:", "09:", "10:"]
    alt_markers = ["6 am", "7 am", "8 am", "9 am", "10 am", "6:00", "7:00",
                   "8:00", "9:00", "10:00"]
    all_markers = hour_markers + alt_markers
    hours_found = sum(1 for m in all_markers if m in content)
    scores["hourly_distribution"] = (
        1.0 if hours_found >= 4 else
        0.5 if hours_found >= 2 else 0.0
    )

    # Check 2: Off-hours events identified
    off_hours_keywords = ["before 08", "before 8:00", "early morning",
                          "06:55", "pre-business", "off-hour", "off hour",
                          "unusual hour", "outside business"]
    scores["off_hours_identified"] = (
        1.0 if sum(1 for kw in off_hours_keywords if kw in content) >= 1 else 0.0
    )

    # Check 3: Successful login timing noted
    has_fztu = "fztu" in content
    has_time = "09:32" in content or "9:32" in content
    has_business = any(kw in content for kw in ["business hour", "normal hour",
                                                  "working hour", "during"])
    scores["successful_timing"] = (
        1.0 if has_fztu and (has_time or has_business) else
        0.5 if has_fztu else 0.0
    )

    # Check 4: Timing patterns analyzed
    pattern_keywords = ["peak", "escalat", "increas", "pattern", "trend",
                        "676", "530", "busiest", "most active", "concentrated"]
    scores["timing_patterns"] = (
        1.0 if sum(1 for kw in pattern_keywords if kw in content) >= 2 else
        0.5 if sum(1 for kw in pattern_keywords if kw in content) >= 1 else 0.0
    )

    return scores
```

---

## Additional Notes

**日志中的关键事实：**

- 日志跨越约 4 小时：12 月 10 日的 06:55 至 10:59
- 攻击强度随时间急剧增加：每小时 7 → 169 → 118 → 676 → 530
- 09:xx 时段最繁忙，达 676 条记录
- 08:00 之前的记录全部为攻击流量
- 唯一一次成功登录（09:32 的 fztu）发生在攻击活动峰值期间

**评分权重（均等）：** 五项标准中每一项对最终得分贡献 0.2。
