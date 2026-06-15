---
id: task_log_ssh_brute_force
name: SSH 认证日志 - 暴力破解检测
category: 日志分析
scene: 数据库检索、表格整理与数据分析
sub_scene: 日志模式提取
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 输出格式适配
- 领域推理
- 工具调用
grading_type: hybrid
timeout_seconds: 180
workspace_files:
  - dest: "auth.log"
    source: "logs/openssh_auth.log"
---

# SSH 认证日志 - 暴力破解检测

## Prompt

你是一名安全分析师，正在审查位于 `auth.log` 的 OpenSSH 认证日志。你的任务是检测暴力破解攻击模式并生成一份威胁评估。

将暴力破解攻击定义为：**在日志时段内，来自单个 IP 地址的失败认证尝试超过 10 次**。

你的报告应当包括：

1. **暴力破解来源**：列出所有达到暴力破解阈值的 IP，以及每个 IP 的失败尝试总数
2. **攻击强度**：对每个暴力破解来源，计算大致的尝试速率（每分钟尝试次数）
3. **用户名模式**：对每个攻击 IP，它们尝试了哪些用户名？是字典攻击（大量用户名）还是定向攻击（少量用户名）？
4. **攻击时间线**：每次攻击何时开始和结束？攻击者之间是否有重叠？
5. **反向 DNS 分析**：哪些攻击 IP 触发了 "POSSIBLE BREAK-IN ATTEMPT" 警告？
6. **风险评估**：评定整体威胁级别并推荐具体的应对措施

将报告写入 `brute_force_report.json`，作为一份具有以下结构的 JSON 文档：

```json
{
  "summary": "Brief summary",
  "brute_force_sources": [
    {
      "ip": "x.x.x.x",
      "total_attempts": 100,
      "first_seen": "Dec 10 HH:MM:SS",
      "last_seen": "Dec 10 HH:MM:SS",
      "usernames_tried": ["user1", "user2"],
      "attack_type": "dictionary|targeted",
      "reverse_dns_warning": true
    }
  ],
  "risk_level": "critical|high|medium|low",
  "recommendations": ["rec1", "rec2"]
}
```

---

## Expected Behavior

Agent 应当识别出以下暴力破解来源：

**主要攻击者：**
- **183.62.140.253** — 约 307 条记录，最严重的攻击者，可能是字典攻击
- **187.141.143.180** — 约 189 条记录，持续攻击
- **103.99.0.122** — 约 83 条记录
- **112.95.230.3** — 约 54 条记录
- **5.188.10.180** — 约 30 条记录
- **185.190.58.151** — 约 26 条记录

**关键发现：**
- 来自不同 IP 的多个并发暴力破解攻击
- 攻击跨越约 4 小时（06:55–10:59）
- 用户名模式包含常见默认值（admin、root、test、oracle、support）
- 85 次 "POSSIBLE BREAK-IN ATTEMPT" 警告表明反向 DNS 被伪造/配置错误
- 风险级别应评定为 high 或 critical

可接受的变化：
- 暴力破解检测的阈值可能有所不同
- 速率计算取决于如何确定首次/末次时间戳
- 推荐措施的具体内容会有所不同

---

## Grading Criteria

- [ ] 在工作区中创建了 `brute_force_report.json`
- [ ] 识别出至少 3 个暴力破解来源 IP
- [ ] 183.62.140.253 被识别为头号攻击者
- [ ] 对每个来源进行了攻击类型分类（字典攻击 vs 定向攻击）
- [ ] 提供了应对措施的推荐建议

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """Grade the SSH brute force detection task."""
    from pathlib import Path
    import json

    scores = {}
    workspace = Path(workspace_path)
    report_file = workspace / "brute_force_report.json"

    if not report_file.exists():
        return {
            "output_created": 0.0,
            "sources_identified": 0.0,
            "top_attacker": 0.0,
            "attack_classified": 0.0,
            "recommendations": 0.0,
        }

    scores["output_created"] = 1.0

    try:
        data = json.loads(report_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, Exception):
        return {
            "output_created": 1.0,
            "sources_identified": 0.0,
            "top_attacker": 0.0,
            "attack_classified": 0.0,
            "recommendations": 0.0,
        }

    full_text = json.dumps(data).lower()

    # Check 1: At least 3 brute-force sources identified
    sources = data.get("brute_force_sources", [])
    if not isinstance(sources, list):
        sources = []
    scores["sources_identified"] = (
        1.0 if len(sources) >= 3 else
        0.5 if len(sources) >= 1 else 0.0
    )

    # Check 2: Top attacker identified
    scores["top_attacker"] = 1.0 if "183.62.140.253" in full_text else 0.0

    # Check 3: Attack type classified
    has_classification = "dictionary" in full_text or "targeted" in full_text or "attack_type" in full_text
    scores["attack_classified"] = 1.0 if has_classification else 0.0

    # Check 4: Recommendations provided
    recs = data.get("recommendations", [])
    if not isinstance(recs, list):
        recs = []
    has_recs = len(recs) >= 2 or any(kw in full_text for kw in
        ["fail2ban", "rate limit", "firewall", "block", "key-based",
         "disable password", "allowlist", "whitelist", "deny"])
    scores["recommendations"] = 1.0 if has_recs else 0.5 if len(recs) >= 1 else 0.0

    return scores
```

---

## Additional Notes

**日志中的关键事实：**

- 服务器：LabSZ，运行带 PAM 的 OpenSSH
- 攻击窗口：12 月 10 日 06:55 至 10:59（约 4 小时）
- 多个同时进行的攻击者 — 表明该服务器 IP 已在某个已知扫描列表上
- 183.62.140.253 平均每小时产生约 75 次尝试
- 唯一一次成功登录（来自 119.137.62.142 的用户 fztu）并非来自攻击 IP

**评分权重（均等）：** 五项标准中每一项对最终得分贡献 0.2。
