---
id: task_log_ssh_successful
name: SSH 认证日志 - 成功认证摘要
category: 日志分析
scene: 数据库检索、表格整理与数据分析
sub_scene: ssh认证日志分析
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 指令遵循与约束理解
- 输出格式适配
- 自然语言生成
grading_type: hybrid
timeout_seconds: 180
workspace_files:
  - dest: "auth.log"
    source: "logs/openssh_auth.log"
---

# SSH 认证日志 - 成功认证摘要

## Prompt

分析位于 `auth.log` 的 OpenSSH 认证日志，生成一份聚焦于成功认证的报告。在失败尝试的噪声之中，识别出所有合法访问。

你的报告应当包括：

1. **成功登录**：列出每一次成功认证，包括时间戳、用户名、源 IP、端口和认证方式
2. **成功与失败比率**：在所有认证尝试中，成功的占多少百分比？
3. **合法用户画像**：对每个成功认证的用户，描述其访问模式
4. **会话活动**：是否有证据表明登录后发生了什么（会话打开/关闭事件）？
5. **源 IP 校验**：成功登录的 IP 是否也与某些失败尝试相关联？
6. **异常检查**：成功登录看起来合法，还是可疑（例如，来自一个同时也在进行暴力破解的 IP）？

将报告写入 `successful_auth_report.md`，作为一份结构良好的 markdown 文档。

---

## Expected Behavior

Agent 应当识别出：

**成功登录：**
- 整个日志中只有 1 次成功登录：
  - 时间：Dec 10 09:32:20
  - 用户：fztu
  - 来源：119.137.62.142
  - 端口：49116
  - 方式：password（ssh2）
  - 条目："Accepted password for fztu from 119.137.62.142 port 49116 ssh2"

**成功与失败比率：**
- 数百次尝试中仅 1 次成功 — 成功率极低
- 这进一步印证该日志记录了一台正遭受暴力破解攻击的服务器

**异常检查：**
- 应将 119.137.62.142（成功登录的 IP）与失败尝试列表进行核对
- 如果它只出现在成功条目中，则很可能是合法用户
- 如果它也有失败尝试，则可能是被盗用的凭据

**会话活动：**
- 查找用户 fztu 对应的 "session opened" / "session closed" 事件

可接受的变化：
- 分析深度可能有所不同
- 部分 Agent 可能会找到额外的会话相关条目
- 异常评估的措辞会有所不同

---

## Grading Criteria

- [ ] 在工作区中创建了 `successful_auth_report.md`
- [ ] 识别出唯一一次成功登录（用户 fztu，IP 119.137.62.142）
- [ ] 计算了成功/失败比率（1 次成功对数百次失败）
- [ ] 将成功登录的 IP 与失败尝试来源进行了核对
- [ ] 提供了对该登录是否合法的评估

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """Grade the SSH successful authentication summary task."""
    from pathlib import Path

    scores = {}
    workspace = Path(workspace_path)
    report_file = workspace / "successful_auth_report.md"

    if not report_file.exists():
        return {
            "output_created": 0.0,
            "login_identified": 0.0,
            "ratio_calculated": 0.0,
            "ip_checked": 0.0,
            "legitimacy_assessed": 0.0,
        }

    scores["output_created"] = 1.0
    content = report_file.read_text(encoding="utf-8").lower()

    # Check 1: Successful login identified
    has_user = "fztu" in content
    has_ip = "119.137.62.142" in content
    has_accepted = "accepted" in content or "successful" in content
    scores["login_identified"] = (
        1.0 if has_user and has_ip else
        0.5 if has_user or has_ip else 0.0
    )

    # Check 2: Ratio calculated
    ratio_keywords = ["ratio", "percent", "1 success", "1 out of", "only 1",
                      "single success", "one success", "0."]
    scores["ratio_calculated"] = (
        1.0 if sum(1 for kw in ratio_keywords if kw in content) >= 1 else 0.0
    )

    # Check 3: IP checked against failed attempts
    check_keywords = ["119.137.62.142", "not associated", "not found",
                      "does not appear", "no failed", "legitimate",
                      "only successful", "no other"]
    scores["ip_checked"] = (
        1.0 if has_ip and sum(1 for kw in check_keywords if kw in content) >= 2 else
        0.5 if has_ip else 0.0
    )

    # Check 4: Legitimacy assessment
    legit_keywords = ["legitimate", "authorized", "valid", "genuine",
                      "suspicious", "anomal", "normal", "expected"]
    scores["legitimacy_assessed"] = (
        1.0 if sum(1 for kw in legit_keywords if kw in content) >= 1 else 0.0
    )

    return scores
```

---

## Additional Notes

**日志中的关键事实：**

- 1500 条记录中只有 1 次成功登录
- 用户 "fztu" 于 09:32:20 通过密码从 119.137.62.142:49116 完成认证
- 119.137.62.142 未作为任何失败尝试的来源出现 — 这是一个合法用户
- 失败与成功尝试之间的巨大失衡是暴力破解目标的典型特征
- PAM 会话事件（打开/关闭）可能提供额外的上下文

**评分权重（均等）：** 五项标准中每一项对最终得分贡献 0.2。
