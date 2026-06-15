---
id: task_log_ssh_failed_logins
name: SSH 认证日志 - 失败登录分析
category: 日志分析
scene: 数据库检索、表格整理与数据分析
sub_scene: 日志模式提取
difficulty: L2
capabilities:
- 数据提取与处理
- 工具调用
- 输出格式适配
- 自然语言生成
grading_type: hybrid
timeout_seconds: 180
workspace_files:
  - dest: "auth.log"
    source: "logs/openssh_auth.log"
---

# SSH 认证日志 - 失败登录分析

## Prompt

分析位于 `auth.log` 的 OpenSSH 认证日志，生成一份关于失败登录尝试的详细报告。该日志来自一台名为 "LabSZ" 的服务器，记录了 SSH 认证事件。

你的报告应当包括：

1. **概览**：日志条目总数、日期范围、失败登录尝试总数
2. **失败密码尝试**：按源 IP 分解的 "Failed password" 条目计数
3. **无效用户尝试**：使用不存在用户名的尝试计数，以及尝试最多的前 10 个用户名列表
4. **头号攻击 IP**：按失败尝试次数排序的前 10 个源 IP，及其计数
5. **认证方式**：正在尝试哪些认证方式（password、publickey 等）？
6. **反向 DNS 失败**：有多少条目显示 "POSSIBLE BREAK-IN ATTEMPT" 警告？
7. **总结评估**：该服务器是否正遭受主动攻击？这种模式说明了什么？

将报告写入 `failed_login_report.md`，作为一份结构良好的 markdown 文档。

---

## Expected Behavior

Agent 应当解析这 1500 条日志条目，并生成：

**概览：**
- 1500 条日志条目
- 日期：12 月 10 日（时间范围约从 06:55 到 10:59）
- 约 366 条 "Failed password" 条目
- 约 100 条 "Invalid user" 条目

**头号攻击 IP：**
- 183.62.140.253 — 约 307 条记录（占主导的攻击者）
- 187.141.143.180 — 约 189 条记录
- 103.99.0.122 — 约 83 条记录
- 112.95.230.3 — 约 54 条记录
- 5.188.10.180 — 约 30 条记录

**最常见的无效用户名：**
- admin（18）、oracle（6）、support（5）、test（4）、inspur（3）、0（3）、matlab（3）、webmaster（2）、guest（2）、1234（2）

**关键观察：**
- 整个日志中只有 1 次成功登录（来自 119.137.62.142 的用户 "fztu"）
- 85 次 "POSSIBLE BREAK-IN ATTEMPT" 警告源于反向 DNS 失败
- 该服务器显然正遭受主动暴力破解攻击
- 攻击来自少数几个 IP，每个都产生了数百次尝试

可接受的变化：
- 具体计数可能因解析方式不同而有 ±5 的差异
- 评估措辞会有所不同

---

## Grading Criteria

- [ ] 在工作区中创建了 `failed_login_report.md`
- [ ] 统计了失败尝试总数（约 366 条失败密码）
- [ ] 识别出头号攻击 IP（183.62.140.253 为头号攻击者）
- [ ] 列出了无效用户名（admin、oracle、support 为主要目标）
- [ ] 评估该服务器正遭受暴力破解攻击

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """Grade the SSH failed login analysis task."""
    from pathlib import Path

    scores = {}
    workspace = Path(workspace_path)
    report_file = workspace / "failed_login_report.md"

    if not report_file.exists():
        return {
            "output_created": 0.0,
            "failed_count": 0.0,
            "top_ips": 0.0,
            "invalid_usernames": 0.0,
            "attack_assessment": 0.0,
        }

    scores["output_created"] = 1.0
    content = report_file.read_text(encoding="utf-8").lower()

    # Check 1: Failed attempt count
    has_failed_count = any(n in content for n in ["366", "365", "367", "failed password"])
    scores["failed_count"] = (
        1.0 if has_failed_count else
        0.5 if "failed" in content and any(c.isdigit() for c in content) else 0.0
    )

    # Check 2: Top attacking IPs identified
    top_ips = ["183.62.140.253", "187.141.143.180", "103.99.0.122", "112.95.230.3"]
    ips_found = sum(1 for ip in top_ips if ip in content)
    scores["top_ips"] = (
        1.0 if ips_found >= 3 else
        0.5 if ips_found >= 1 else 0.0
    )

    # Check 3: Invalid usernames listed
    usernames = ["admin", "oracle", "support", "test", "webmaster", "guest"]
    users_found = sum(1 for u in usernames if u in content)
    scores["invalid_usernames"] = (
        1.0 if users_found >= 3 else
        0.5 if users_found >= 1 else 0.0
    )

    # Check 4: Attack assessment
    attack_keywords = ["brute force", "brute-force", "attack", "compromise",
                       "malicious", "automated", "scanning", "dictionary"]
    scores["attack_assessment"] = (
        1.0 if sum(1 for kw in attack_keywords if kw in content) >= 2 else
        0.5 if sum(1 for kw in attack_keywords if kw in content) >= 1 else 0.0
    )

    return scores
```

---

## Additional Notes

**日志中的关键事实：**

- 服务器：LabSZ，运行带 PAM 认证的 OpenSSH
- 攻击窗口约为 4 小时（12 月 10 日的 06:55–10:59）
- 仅 183.62.140.253 一个 IP 就占了约 307 条日志记录 — 明显的暴力破解来源
- 反向 DNS 失败触发 "POSSIBLE BREAK-IN ATTEMPT" 警告（85 次出现）
- 整个日志中只有 1 次成功登录（用户 fztu）

**评分权重（均等）：** 五项标准中每一项对最终得分贡献 0.2。
