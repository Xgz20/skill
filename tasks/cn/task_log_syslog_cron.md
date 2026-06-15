---
id: task_log_syslog_cron
name: Linux 系统日志 - Cron 作业执行分析
category: 日志分析
scene: 数据库检索、表格整理与数据分析
sub_scene: 日志模式提取
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
  - dest: "syslog.log"
    source: "logs/linux_syslog.log"
---

# Linux 系统日志 - Cron 作业执行分析

## Prompt

分析位于 `syslog.log` 的 Linux 系统日志，并生成一份关于 cron 作业与定时任务活动的报告。查找 crond、anacron、logrotate 以及任何其他定时执行的证据。

你的报告应包含：

1. **Cron 服务状态（Cron Service Status）**：crond 何时启动？有多少次启动事件？
2. **Anacron 活动（Anacron Activity）**：记录所有 anacron 启动事件及其时间
3. **Logrotate 活动（Logrotate Activity）**：识别 logrotate 的执行及其影响的服务
4. **su 会话模式（su Session Patterns）**：`su(pam_unix)` 条目通常表示 cron 以不同用户身份执行任务 —— 分析这些模式
5. **定时任务时间线（Scheduled Task Timeline）**：创建一条涵盖所有定时 / 周期性活动的时间线
6. **重复模式（Recurring Patterns）**：识别定时执行中的任何规律性模式（每日、每周）

将报告写入 `cron_analysis.md`，作为一份结构良好的 markdown 文档。

---

## Expected Behavior

Agent 应当识别出：

**Cron/Anacron 启动：**
- crond 启动：Jun 9 06:06:49、Jun 10 11:32:10、Jul 27 14:42:23（3 次事件，与系统启动对齐）
- anacron 启动：Jun 9 06:06:51、Jun 10 11:32:12、Jul 27 14:42:25（紧随 crond 之后）

**Logrotate 活动：**
- 日志中有 97 条 logrotate 条目
- Logrotate 触发服务重启（尤其是 CUPS）
- 周期性运行 —— 很可能通过 anacron/cron 每日运行

**su(pam_unix) 模式：**
- 394 条 su 会话条目
- 为以下用户打开的会话：htt、cyrus、news
- 模式："session opened for user X by (uid=0)" → "session closed for user X"
- 这些是以特定服务用户身份运行的 cron 作业

**关键的定时用户：**
- htt（web 服务器）—— 规律的 su 会话
- cyrus（邮件）—— 规律的 su 会话
- news —— 周期性会话

**重复模式：**
- 每日：logrotate 运行、为服务用户打开的 su 会话
- 启动时：crond → anacron 启动序列
- 每周：CUPS 重启模式（关闭 + 启动）

可接受的差异：
- 模式检测方法可能不同
- 时间线粒度可能不同
- 部分定时模式需要从 su 会话数据中推断

---

## Grading Criteria

- [ ] `cron_analysis.md` 已在工作区中创建
- [ ] 记录了 crond 与 anacron 的启动事件
- [ ] 识别出 logrotate 活动（97 条）
- [ ] 将 su(pam_unix) 会话与定时任务关联起来
- [ ] 识别出重复模式（每日、启动时等）

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """Grade the Linux syslog cron job analysis task."""
    from pathlib import Path

    scores = {}
    workspace = Path(workspace_path)
    report_file = workspace / "cron_analysis.md"

    if not report_file.exists():
        return {
            "output_created": 0.0,
            "cron_anacron": 0.0,
            "logrotate": 0.0,
            "su_sessions": 0.0,
            "recurring_patterns": 0.0,
        }

    scores["output_created"] = 1.0
    content = report_file.read_text(encoding="utf-8").lower()

    # Check 1: Crond and anacron documented
    has_crond = "crond" in content or "cron daemon" in content
    has_anacron = "anacron" in content
    scores["cron_anacron"] = (
        1.0 if has_crond and has_anacron else
        0.5 if has_crond else 0.0
    )

    # Check 2: Logrotate identified
    has_logrotate = "logrotate" in content
    has_count = "97" in content or any(kw in content for kw in
        ["frequent", "numerous", "many logrotate"])
    scores["logrotate"] = (
        1.0 if has_logrotate and has_count else
        0.5 if has_logrotate else 0.0
    )

    # Check 3: su sessions analyzed
    has_su = "su(" in content or "su(pam" in content or "su session" in content
    has_users = sum(1 for u in ["htt", "cyrus", "news"] if u in content)
    scores["su_sessions"] = (
        1.0 if has_su and has_users >= 2 else
        0.5 if has_su else 0.0
    )

    # Check 4: Recurring patterns identified
    pattern_keywords = ["daily", "weekly", "periodic", "regular", "recurring",
                        "schedule", "pattern", "at boot", "every"]
    scores["recurring_patterns"] = (
        1.0 if sum(1 for kw in pattern_keywords if kw in content) >= 2 else
        0.5 if sum(1 for kw in pattern_keywords if kw in content) >= 1 else 0.0
    )

    return scores
```

---

## Additional Notes

**日志中的关键事实：**

- crond 与 anacron 总是在启动时一同启动，相隔 2 秒
- logrotate 是最活跃的周期性进程（97 条）
- su 会话（394 条）是定时任务执行的主要指标
- 常见的 cron 用户模式：uid=0 为服务用户打开会话，随后关闭
- 该服务器运行邮件（cyrus）、web（htt）和 news 服务 —— 全部带有 cron 维护

**评分权重（均等）：** 五项标准各占最终得分的 0.2。
