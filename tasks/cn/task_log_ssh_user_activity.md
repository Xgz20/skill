---
id: task_log_ssh_user_activity
name: SSH 认证日志 - 用户登录活动报告
category: 日志分析
scene: 数据库检索、表格整理与数据分析
sub_scene: SSH 日志用户活动分析
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 自然语言生成
- 输出格式适配
- 领域推理
grading_type: hybrid
timeout_seconds: 180
workspace_files:
  - dest: "auth.log"
    source: "logs/openssh_auth.log"
---

# SSH 认证日志 - 用户登录活动报告

## Prompt

分析位于 `auth.log` 的 OpenSSH 认证日志，并生成一份以用户为中心的活动报告。针对日志中出现的每一个用户名（无论有效或无效），汇总其认证活动。

你的报告应包含：

1. **所有尝试过的用户名（All Usernames Attempted）**：列出日志中出现的每一个用户名（既包括有效的系统用户，也包括无效的 / 不存在的用户）
2. **有效与无效用户（Valid vs Invalid Users）**：将每个用户名分类为有效（被系统接受）或无效（被拒绝为不存在）
3. **按用户汇总（Per-User Summary）**：对每个用户名，列出：尝试次数、来源 IP、成功 / 失败、首次与末次尝试的时间戳
4. **被攻击最频繁的用户（Most Targeted Users）**：按失败尝试次数对用户名排序
5. **用户名模式（Username Patterns）**：攻击者是否在使用字典？常见模式（admin、root、test、服务账户）？
6. **用户风险评估（User Risk Assessment）**：哪些用户名一旦存在，将构成最大的安全风险？

将报告写入 `user_activity_report.md`，作为一份结构良好的 markdown 文档。

---

## Expected Behavior

Agent 应当识别出：

**无效用户（按频率排名靠前）：**
- admin（18 次尝试）、oracle（6）、support（5）、test（4）、inspur（3）、0（3）、matlab（3）、webmaster（2）、guest（2）、1234（2）以及其他

**有效用户：**
- fztu —— 唯一一个成功登录的用户
- root —— 很可能是一个被攻击的有效用户（检查是 "Failed password for root" 还是 "Failed password for invalid user root"）

**用户名模式：**
- 常见服务账户：admin、oracle、support、webmaster
- 默认凭据：test、guest、1234、0
- 应用相关：matlab、inspur
- 这显然是一次使用常见用户名列表的字典攻击

**风险评估：**
- "admin" 与 "root" 风险最高 —— 一旦被攻陷，将获得完整的系统访问权限
- "oracle" 表明攻击者知道这很可能是一台运行数据库的 Linux 服务器
- 像 "0" 和 "1234" 这样的数字用户名表明这是自动化 / 脚本化攻击

可接受的差异：
- 有效与无效用户的区分取决于对 "invalid user" 消息的解析
- 部分用户名可能存在歧义
- 风险评估的措辞会有所不同

---

## Grading Criteria

- [ ] `user_activity_report.md` 已在工作区中创建
- [ ] 同时列出了有效与无效用户名
- [ ] 识别出被攻击最频繁的用户名（admin）
- [ ] 分析了用户名模式（字典攻击、常见默认值）
- [ ] 为最危险的用户名提供了风险评估

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """Grade the SSH user activity report task."""
    from pathlib import Path

    scores = {}
    workspace = Path(workspace_path)
    report_file = workspace / "user_activity_report.md"

    if not report_file.exists():
        return {
            "output_created": 0.0,
            "usernames_listed": 0.0,
            "admin_targeted": 0.0,
            "patterns_analyzed": 0.0,
            "risk_assessment": 0.0,
        }

    scores["output_created"] = 1.0
    content = report_file.read_text(encoding="utf-8").lower()

    # Check 1: Both valid and invalid usernames listed
    invalid_users = ["admin", "oracle", "support", "test", "webmaster", "guest"]
    valid_users = ["fztu"]
    invalid_found = sum(1 for u in invalid_users if u in content)
    valid_found = sum(1 for u in valid_users if u in content)
    scores["usernames_listed"] = (
        1.0 if invalid_found >= 3 and valid_found >= 1 else
        0.5 if invalid_found >= 2 else 0.0
    )

    # Check 2: Admin identified as most targeted
    scores["admin_targeted"] = (
        1.0 if "admin" in content and any(kw in content for kw in
            ["most", "top", "highest", "18", "target"]) else
        0.5 if "admin" in content else 0.0
    )

    # Check 3: Username patterns analyzed
    pattern_keywords = ["dictionary", "common", "default", "service account",
                        "automated", "wordlist", "brute", "pattern"]
    scores["patterns_analyzed"] = (
        1.0 if sum(1 for kw in pattern_keywords if kw in content) >= 2 else
        0.5 if sum(1 for kw in pattern_keywords if kw in content) >= 1 else 0.0
    )

    # Check 4: Risk assessment
    risk_keywords = ["risk", "danger", "critical", "compromise", "privilege",
                     "escalat", "root access", "full access"]
    scores["risk_assessment"] = (
        1.0 if sum(1 for kw in risk_keywords if kw in content) >= 2 else
        0.5 if sum(1 for kw in risk_keywords if kw in content) >= 1 else 0.0
    )

    return scores
```

---

## Additional Notes

**日志中的关键事实：**

- 约 100 条 "Invalid user" 条目，涉及各种用户名
- "admin" 被尝试了 18 次 —— 最热门的攻击目标
- 用户 "fztu" 是唯一确认有效的用户（成功登录）
- "root" 出现在失败的密码尝试中，但不以 "invalid user" 形式出现 —— 这表明 root 是一个真实账户
- 用户名列表读起来就像一份标准的 SSH 暴力破解字典

**评分权重（均等）：** 五项标准各占最终得分的 0.2。
