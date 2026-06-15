---
id: task_log_syslog_services
name: Linux 系统日志 - 服务启停汇总
category: 日志分析
scene: 数据库检索、表格整理与数据分析
sub_scene: 日志服务事件分析
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 自然语言生成
- 输出格式适配
grading_type: hybrid
timeout_seconds: 180
workspace_files:
  - dest: "syslog.log"
    source: "logs/linux_syslog.log"
---

# Linux 系统日志 - 服务启停汇总

## Prompt

分析位于 `syslog.log` 的 Linux 系统日志，并生成一份关于所有服务启动与停止事件的汇总。该日志来自一台名为 "combo"、运行 Linux 2.6 的服务器。

你的报告应包含：

1. **服务清单（Service Inventory）**：列出日志中提及的、带有启动或关闭事件的每一个服务
2. **系统启动事件（System Boot Events）**：通过查找服务启动的聚集，识别所有系统启动 / 重启
3. **按服务列出状态（Per-Service Status）**：对每个服务，列出所有带时间戳的启动 / 停止事件
4. **CUPS 特例（CUPS Special Case）**：CUPS 打印服务频繁重启 —— 单独记录其模式
5. **服务依赖（Service Dependencies）**：根据启动顺序，推断哪些服务先启动（核心 OS）、哪些后启动（应用）
6. **运行时长估算（Uptime Estimate）**：根据启动事件，估算服务器在两次重启之间的运行时长

将报告写入 `service_status_report.md`，作为一份结构良好的 markdown 文档。

---

## Expected Behavior

Agent 应当识别出：

**系统启动（检测到 3 次）：**
1. Jun 9 约 06:06 —— 完整启动（syslogd、klogd、kernel、irqbalance、portmap 等）
2. Jun 10 约 11:32 —— 完整启动（相同的服务序列）
3. Jul 27 约 14:42 —— 另一次启动事件

**服务清单（20+ 个带启动事件的服务）：**
- 核心：syslogd、klogd、irqbalance、portmap
- 网络：rpc.statd、rpc.idmapd、sendmail、sm-client、named
- 安全：spamd、privoxy
- 硬件：bluetooth (hcid, sdpd)、smartd、apmd、gpm
- 打印：cupsd（17 次启动！）
- 调度：crond、anacron、xinetd
- Web：htt

**CUPS 模式：**
- cupsd 有 17 次启动事件和 15 次关闭事件
- 规律的每周模式：清晨（04:0x）关闭后随即启动
- 这与 logrotate 触发 CUPS 重启相吻合

**服务依赖（启动顺序）：**
1. syslogd、klogd（日志优先）
2. 内核消息
3. irqbalance、portmap（系统服务）
4. 网络服务（rpc、named）
5. 应用服务（cups、cron、sendmail）

可接受的差异：
- 启动检测方法可能不同
- 服务分类带有主观性
- 运行时长计算为近似值

---

## Grading Criteria

- [ ] `service_status_report.md` 已在工作区中创建
- [ ] 识别出系统启动事件（至少找到 2 次启动）
- [ ] 列出了服务及其启动 / 停止事件
- [ ] 记录了 CUPS 的频繁重启（17 次启动）
- [ ] 分析了服务启动顺序

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """Grade the Linux syslog service status summary task."""
    from pathlib import Path

    scores = {}
    workspace = Path(workspace_path)
    report_file = workspace / "service_status_report.md"

    if not report_file.exists():
        return {
            "output_created": 0.0,
            "boots_identified": 0.0,
            "services_listed": 0.0,
            "cups_pattern": 0.0,
            "startup_ordering": 0.0,
        }

    scores["output_created"] = 1.0
    content = report_file.read_text(encoding="utf-8").lower()

    # Check 1: Boot events identified
    boot_dates = ["jun 9", "jun 10", "jul 27", "june 9", "june 10", "july 27"]
    boots_found = sum(1 for d in boot_dates if d in content)
    has_boot = any(kw in content for kw in ["boot", "restart", "reboot", "startup"])
    scores["boots_identified"] = (
        1.0 if boots_found >= 2 and has_boot else
        0.5 if boots_found >= 1 else 0.0
    )

    # Check 2: Services listed
    services = ["syslogd", "klogd", "crond", "cupsd", "cups", "sendmail",
                "portmap", "sshd", "named", "xinetd", "smartd", "gpm"]
    services_found = sum(1 for s in services if s in content)
    scores["services_listed"] = (
        1.0 if services_found >= 6 else
        0.5 if services_found >= 3 else 0.0
    )

    # Check 3: CUPS pattern noted
    has_cups = "cups" in content
    has_frequent = any(kw in content for kw in ["17", "frequent", "multiple",
                                                  "regular", "weekly", "logrotate"])
    scores["cups_pattern"] = (
        1.0 if has_cups and has_frequent else
        0.5 if has_cups else 0.0
    )

    # Check 4: Startup ordering analyzed
    order_keywords = ["order", "first", "before", "after", "sequence",
                      "dependency", "boot order", "startup order"]
    scores["startup_ordering"] = (
        1.0 if sum(1 for kw in order_keywords if kw in content) >= 2 else
        0.5 if sum(1 for kw in order_keywords if kw in content) >= 1 else 0.0
    )

    return scores
```

---

## Additional Notes

**日志中的关键事实：**

- 服务器："combo"，Fedora/Red Hat，Linux 2.6.5-1.358
- 日志中检测到 3 次完整的系统启动
- CUPS 每周重启 —— 很可能由 logrotate 触发
- 20+ 个带启动事件的唯一服务
- 启动序列在全部 3 次启动中保持一致
- 启动序列显示出清晰的顺序：日志 → 系统 → 网络 → 应用服务

**评分权重（均等）：** 五项标准各占最终得分的 0.2。
