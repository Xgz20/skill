---
id: task_log_syslog_auth_failures
name: Linux 系统日志 - 认证失败汇总
category: 日志分析
scene: 数据库检索、表格整理与数据分析
sub_scene: 日志认证失败分析
difficulty: L2
capabilities:
- 数据提取与处理
- 工具调用
- 多步推理
- 自然语言生成
- 输出格式适配
grading_type: hybrid
timeout_seconds: 180
workspace_files:
  - dest: "syslog.log"
    source: "logs/linux_syslog.log"
---

# Linux 系统日志 - 认证失败汇总

## Prompt

分析位于 `syslog.log` 的 Linux 系统日志，并生成一份关于所有认证失败的全面汇总。该日志包含来自多个服务的 PAM 认证事件。

你的报告应包含：

1. **认证失败总数（Total Auth Failures）**：统计所有服务中的全部认证失败条目
2. **按服务分类的失败（Failures by Service）**：按服务（sshd、ftpd、login、su 等）细分失败情况
3. **按来源分类的失败（Failures by Source）**：产生失败最多的前 10 个来源主机 / IP
4. **被攻击的用户（Targeted Users）**：哪些用户账户在失败的认证尝试中被攻击？
5. **时间分布（Temporal Distribution）**：大多数认证失败发生在何时？是否存在峰值？
6. **FTP 与 SSH 对比分析（FTP vs SSH Analysis）**：对比 FTP 与 SSH 的认证攻击模式 —— 是否是相同的来源同时攻击两者？
7. **建议（Recommendations）**：基于失败模式，提出具体的安全改进建议

将报告写入 `auth_failures_report.md`，作为一份结构良好的 markdown 文档。

---

## Expected Behavior

Agent 应当解析约 2000+ 条与 PAM 相关的条目并生成：

**认证失败总数：**
- 超过 2000 条与认证相关的 PAM 条目
- 主要来源：sshd(pam_unix)（约 1610 条）、ftpd 连接（约 1655 条）

**按服务分类的失败：**
- sshd(pam_unix) —— 认证失败消息的主要来源
- ftpd —— 连接量大（ftpd 记录连接，并不总是显式失败）
- su(pam_unix) —— 394 条（大多合法 —— cron 的会话打开 / 关闭）
- login(pam_unix) —— 14 条
- klogind —— 46 条（Kerberos 登录守护进程）

**按来源分类的失败：**
- SSH 攻击来自各种远程主机（pam 条目中的 rhost=）
- FTP 连接集中于特定 IP（例如 209.184.7.130）
- 部分主机同时出现在 SSH 与 FTP 失败日志中

**被攻击的用户：**
- root —— SSH 暴力破解的主要目标
- 通过 SSH 尝试的各种无效用户名

**时间分布：**
- 日志跨度为 Jun 9 至 Sep 14
- 在特定日期可见攻击峰值
- SSH 暴力破解倾向于在时间上聚集

可接受的差异：
- 确切的计数取决于如何定义"authentication failure"
- FTP 条目可能被归类为认证失败，也可能不被归类
- 时间分析的粒度可能不同

---

## Grading Criteria

- [ ] `auth_failures_report.md` 已在工作区中创建
- [ ] 统计了认证失败（2000+ 条与 pam 相关的条目）
- [ ] 按服务（sshd、ftpd、su 等）细分了失败
- [ ] 列出了主要来源主机
- [ ] 提供了安全改进建议

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """Grade the Linux syslog authentication failure summary task."""
    from pathlib import Path

    scores = {}
    workspace = Path(workspace_path)
    report_file = workspace / "auth_failures_report.md"

    if not report_file.exists():
        return {
            "output_created": 0.0,
            "failures_counted": 0.0,
            "by_service": 0.0,
            "source_hosts": 0.0,
            "recommendations": 0.0,
        }

    scores["output_created"] = 1.0
    content = report_file.read_text(encoding="utf-8").lower()

    # Check 1: Failures counted
    has_count = any(kw in content for kw in ["2000", "2,000", "1610", "1,610",
                                               "1655", "1,655", "thousand"])
    has_failure = "authentication failure" in content or "auth fail" in content or "failed" in content
    scores["failures_counted"] = (
        1.0 if has_count and has_failure else
        0.5 if has_failure else 0.0
    )

    # Check 2: Broken down by service
    services = ["sshd", "ftpd", "ftp", "su(pam", "su ", "login", "klogin", "pam_unix"]
    services_found = sum(1 for s in services if s in content)
    scores["by_service"] = (
        1.0 if services_found >= 3 else
        0.5 if services_found >= 2 else 0.0
    )

    # Check 3: Source hosts listed
    host_indicators = ["rhost", "source", "remote", "ip", "host", "209.184",
                       "sagonet", "iasi", "astral"]
    scores["source_hosts"] = (
        1.0 if sum(1 for kw in host_indicators if kw in content) >= 3 else
        0.5 if sum(1 for kw in host_indicators if kw in content) >= 1 else 0.0
    )

    # Check 4: Recommendations provided
    rec_keywords = ["recommend", "should", "implement", "consider", "disable",
                    "block", "firewall", "fail2ban", "key-based", "rate limit"]
    rec_lines = [l for l in content.split("\n") if any(kw in l for kw in rec_keywords)]
    scores["recommendations"] = (
        1.0 if len(rec_lines) >= 2 else
        0.5 if len(rec_lines) >= 1 else 0.0
    )

    return scores
```

---

## Additional Notes

**日志中的关键事实：**

- 服务器 "combo" 拥有多个认证入口：SSH、FTP、telnet（klogind）、本地 login、su
- sshd(pam_unix) 是最频繁的认证服务（1610 条）
- ftpd 有 1655 条连接条目 —— 按数量算是最重的服务
- su(pam_unix) 会话（394）大多合法（cron 作业、uid=0 以服务用户身份运行）
- login(pam_unix) 有 14 条 —— 控制台 / 终端登录
- klogind 有 46 条 —— Kerberos 远程登录
- 该系统是一台 2005 年代的 Fedora 服务器，暴露了许多服务 —— 是安全加固的候选对象

**评分权重（均等）：** 五项标准各占最终得分的 0.2。
