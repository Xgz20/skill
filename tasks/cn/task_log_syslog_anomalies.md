---
id: task_log_syslog_anomalies
name: Linux 系统日志 - 异常检测
category: 日志分析
scene: 数据库检索、表格整理与数据分析
sub_scene: 日志异常检测
difficulty: L2
capabilities:
- 数据提取与处理
- 工具调用
- 多步推理
- 输出格式适配
- 领域推理
grading_type: hybrid
timeout_seconds: 180
workspace_files:
  - dest: "syslog.log"
    source: "logs/linux_syslog.log"
---

# Linux 系统日志 - 异常检测

## Prompt

分析位于 `syslog.log` 的 Linux 系统日志，识别其中异常或可疑的条目。该日志来自一台名为 "combo"、运行 Linux 2.6 内核的服务器，覆盖了数月的活动。

你的报告应包含：

1. **日志概览（Log Overview）**：条目总数、日期范围、按数量排名的主要服务
2. **安全异常（Security Anomalies）**：指示潜在攻击、漏洞利用或未授权访问尝试的条目
3. **格式化字符串攻击检测（Format String Attack Detection）**：查找服务输入中含有异常二进制内容或漏洞利用载荷的条目
4. **FTP 异常（FTP Anomalies）**：该日志有大量 FTP 流量 —— 识别任何可疑的 FTP 连接模式（突发、异常来源）
5. **rpc.statd 漏洞利用（rpc.statd Exploitation）**：检查 rpc.statd gethostbyname 错误中是否含有畸形主机名（缓冲区溢出尝试）
6. **异常汇总（Anomaly Summary）**：将最令人担忧的前 5 个异常按严重程度与证据排序

将报告写入 `syslog_anomalies.md`，作为一份结构良好的 markdown 文档。

---

## Expected Behavior

Agent 应当解析 5000 条条目并识别出：

**日志概览：**
- 5000 条条目，6 月 9 日至 9 月 14 日（根据内核版本判断为 2005 年）
- 主要服务：ftpd (1655)、sshd/pam_unix (1610)、kernel (545)、su/pam_unix (394)

**安全异常：**
1. **rpc.statd 格式化字符串攻击**（6 月 13 日约 9 条）：
   - `gethostbyname error for ^X...%8x%8x...%hn%51859x%hn` —— 这是针对 rpc.statd 的缓冲区溢出 / 格式化字符串漏洞利用尝试
   - 该载荷包含格式化字符串说明符（%x、%hn），是经典的漏洞利用模式
2. **SSH 暴力破解** —— 大量 sshd(pam_unix) 认证失败
3. **FTP 洪泛** —— 1655 条 FTP 连接条目，存在突发（例如 209.184.7.130 同时发起多个连接）
4. **认证失败** —— 跨 SSH 及其他服务的 2000+ 条 pam_unix 认证失败条目

**rpc.statd 漏洞利用：**
- 9 条条目，时间为 6 月 13 日 11:55:04–11:55:09
- 畸形主机名包含 NOP sled（\220\220\220\220）和格式化字符串载荷
- 这是一次远程代码执行漏洞利用尝试

可接受的差异：
- 异常排序可能不同
- 欢迎给出预期之外的额外异常
- 严重程度评估会有所不同

---

## Grading Criteria

- [ ] `syslog_anomalies.md` 已在工作区中创建
- [ ] 提供了包含日期范围与服务细分的日志概览
- [ ] rpc.statd 格式化字符串攻击被识别为安全异常
- [ ] 分析了 FTP 连接模式
- [ ] 标记了 SSH 认证失败

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """Grade the Linux syslog anomaly detection task."""
    from pathlib import Path

    scores = {}
    workspace = Path(workspace_path)
    report_file = workspace / "syslog_anomalies.md"

    if not report_file.exists():
        return {
            "output_created": 0.0,
            "log_overview": 0.0,
            "rpc_statd_attack": 0.0,
            "ftp_analysis": 0.0,
            "ssh_failures": 0.0,
        }

    scores["output_created"] = 1.0
    content = report_file.read_text(encoding="utf-8").lower()

    # Check 1: Log overview
    has_count = any(n in content for n in ["5000", "5,000"])
    has_date = any(d in content for d in ["jun", "june", "sep", "september"])
    scores["log_overview"] = (
        1.0 if has_count and has_date else
        0.5 if has_count or has_date else 0.0
    )

    # Check 2: rpc.statd attack identified
    rpc_keywords = ["rpc.statd", "rpc statd", "gethostbyname", "format string",
                    "buffer overflow", "exploit", "%hn", "nop sled", "\\220"]
    scores["rpc_statd_attack"] = (
        1.0 if sum(1 for kw in rpc_keywords if kw in content) >= 2 else
        0.5 if sum(1 for kw in rpc_keywords if kw in content) >= 1 else 0.0
    )

    # Check 3: FTP analysis
    ftp_keywords = ["ftpd", "ftp", "1655", "209.184", "connection flood",
                    "burst", "ftp connection"]
    scores["ftp_analysis"] = (
        1.0 if sum(1 for kw in ftp_keywords if kw in content) >= 2 else
        0.5 if sum(1 for kw in ftp_keywords if kw in content) >= 1 else 0.0
    )

    # Check 4: SSH failures flagged
    ssh_keywords = ["sshd", "ssh", "authentication failure", "brute force",
                    "failed", "pam_unix"]
    scores["ssh_failures"] = (
        1.0 if sum(1 for kw in ssh_keywords if kw in content) >= 2 else
        0.5 if sum(1 for kw in ssh_keywords if kw in content) >= 1 else 0.0
    )

    return scores
```

---

## Additional Notes

**日志中的关键事实：**

- 服务器："combo"，Linux 2.6.5-1.358，基于 Fedora/Red Hat
- 日期范围：Jun 9 至 Sep 14（根据内核构建日期判断为 2005 年）
- 6 月 13 日的 rpc.statd 攻击是最严重的异常 —— 一次真实的漏洞利用尝试
- 1655 条 FTP 连接，高度集中于特定 IP（209.184.7.130）
- su(pam_unix) 条目（394）显示有规律的权限提升 —— 很可能是合法的 cron 作业
- 部分条目含有非 UTF-8 字节（二进制漏洞利用载荷）

**评分权重（均等）：** 五项标准各占最终得分的 0.2。
