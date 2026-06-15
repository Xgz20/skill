---
id: task_log_apache_critical
name: Apache 错误日志 - 识别关键安全问题
category: 日志分析
scene: 数据库检索、表格整理与数据分析
sub_scene: 日志安全分析
difficulty: L2
capabilities:
- 数据提取与处理
- 领域推理
- 多步推理
- 输出格式适配
grading_type: hybrid
timeout_seconds: 180
workspace_files:
  - dest: "apache_error.log"
    source: "logs/apache_error.log"
---

# Apache 错误日志 - 识别关键安全问题

## Prompt

你是一名安全分析师，正在审查位于 `apache_error.log` 的 Apache 错误日志。你的工作是识别所有**与安全相关**的条目——那些表明针对该服务器的主动攻击、漏洞扫描或漏洞利用尝试的内容。

将每个发现归类为以下严重级别之一：

| Severity | Definition |
|---|---|
| `critical` | 主动漏洞利用尝试（例如命令执行、带编码 payload 的目录遍历） |
| `high` | 针对特定已知漏洞的漏洞扫描 |
| `medium` | 侦察活动（目录探测、来自单一 IP 的反复 forbidden 请求） |
| `low` | 可能表明配置错误但并非攻击的偶发错误 |

将你的发现写入 `security_findings.json`，作为一个 JSON 数组。每个元素必须是一个对象，包含：

```json
{
  "severity": "critical",
  "category": "Brief category name",
  "source_ips": ["1.2.3.4", "5.6.7.8"],
  "evidence": "Description of what was found and why it's a security concern",
  "sample_entry": "One example log line"
}
```

按从 critical 到 low 的严重级别排序。

---

## Expected Behavior

Agent 应至少识别以下发现：

**Critical：**
- **IIS 目录遍历 / 命令执行尝试**：多个 IP 发送 "Invalid method" 请求，包含类似 `/scripts/..%c0%af../winnt/system32/cmd.exe?/c+dir` 的路径。这些使用 Unicode 编码漏洞利用（CVE-2000-0884、CVE-2001-0333）尝试远程命令执行。源 IP 包括：63.203.254.140、213.61.135.6、201.252.246.11、62.221.237.83、213.205.73.192、64.147.69.59、207.181.126.3、12.216.230.125、220.228.80.199、64.60.251.53、63.197.230.242、61.72.66.8、202.118.167.71。
- **IIS 蠕虫传播探测**：IP 扫描 root.exe、MSADC、_vti_bin、_mem_bin、msadc 以及遍历路径（`..%5c..`、`..\xc1\x1c..`、`..\xc0\xaf..`、`..\xc1\x9c..`、`..%2f..`）。这些符合 Nimda/Code Red 蠕虫行为。

**High：**
- **Awstats 漏洞扫描**：202.133.98.6 发送了 ~184 次请求，在多个路径（cgi-bin、/awstats/、/stats/、/cgi/）探测 awstats.pl。AWStats 有已知的远程代码执行漏洞。
- **OpenWebMail 扫描**：212.238.198.203 探测 /var/www/cgi-bin/openwebmail 20 次。
- **缓冲区溢出尝试**：IP 210.91.137.35、211.211.14.224 和 150.161.187.25 发送的请求触发了 "URI too long (longer than 8190)" 错误，并结合 _vti_bin 探测。

**Medium：**
- **大规模目录探测**：多个 IP 反复请求目录索引（195.23.79.241 ~22 次请求，219.133.246.207 ~15 次，218.82.188.130 ~13 次等）

可接受的变化：
- 严重级别分类可能略有不同（例如将 awstats 归为 "critical" 还是 "high"）
- 超出预期之外的额外发现是可以的
- 只要识别出关键攻击者，IP 列表可以是部分的

---

## Grading Criteria

- [ ] `security_findings.json` 在工作区中被创建
- [ ] 命令执行 / 目录遍历尝试被识别为 critical（cmd.exe、root.exe 模式）
- [ ] 识别出 Awstats 扫描（202.133.98.6 或 awstats 关键字）
- [ ] 至少识别出 3 个不同的攻击类别
- [ ] 发现使用了严重级别分类系统

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """Grade the Apache error log critical security issues task."""
    from pathlib import Path
    import json

    scores = {}
    workspace = Path(workspace_path)
    report_file = workspace / "security_findings.json"

    if not report_file.exists():
        return {
            "output_created": 0.0,
            "cmd_traversal_critical": 0.0,
            "awstats_scanning": 0.0,
            "multiple_categories": 0.0,
            "severity_classification": 0.0,
        }

    scores["output_created"] = 1.0

    try:
        data = json.loads(report_file.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            data = data.get("findings", data.get("security_findings", []))
        if not isinstance(data, list):
            data = []
    except (json.JSONDecodeError, Exception):
        return {
            "output_created": 1.0,
            "cmd_traversal_critical": 0.0,
            "awstats_scanning": 0.0,
            "multiple_categories": 0.0,
            "severity_classification": 0.0,
        }

    full_text = json.dumps(data).lower()

    # Check 1: Command execution / directory traversal identified
    traversal_keywords = ["cmd.exe", "root.exe", "traversal", "command execution",
                          "invalid method", "nimda", "code red", "worm", "unicode"]
    has_traversal = sum(1 for kw in traversal_keywords if kw in full_text) >= 2
    has_critical = "critical" in full_text
    scores["cmd_traversal_critical"] = (
        1.0 if has_traversal and has_critical else
        0.5 if has_traversal else 0.0
    )

    # Check 2: Awstats scanning identified
    has_awstats = "awstats" in full_text
    has_scanner_ip = "202.133.98.6" in full_text
    scores["awstats_scanning"] = (
        1.0 if has_awstats or has_scanner_ip else 0.0
    )

    # Check 3: At least 3 distinct attack categories
    categories_found = 0
    category_patterns = [
        ["cmd.exe", "root.exe", "traversal", "command", "invalid method"],
        ["awstats", "202.133.98.6"],
        ["_vti_bin", "frontpage", "iis"],
        ["openwebmail", "212.238.198.203"],
        ["directory", "forbidden", "scanning", "probing", "reconnaissance"],
        ["uri too long", "buffer", "overflow", "8190"],
    ]
    for patterns in category_patterns:
        if any(p in full_text for p in patterns):
            categories_found += 1
    scores["multiple_categories"] = (
        1.0 if categories_found >= 3 else
        0.5 if categories_found >= 2 else 0.0
    )

    # Check 4: Severity classification used
    severity_levels = ["critical", "high", "medium", "low"]
    levels_used = sum(1 for s in severity_levels if s in full_text)
    scores["severity_classification"] = (
        1.0 if levels_used >= 3 else
        0.5 if levels_used >= 2 else 0.0
    )

    return scores
```

---

## Additional Notes

**日志中的关键攻击模式：**

| Attack Pattern | Example Path | CVE / Worm |
|---|---|---|
| Unicode traversal | `/scripts/..%c0%af../winnt/system32/cmd.exe?/c+dir` | CVE-2000-0884 (Nimda) |
| Double-encode traversal | `/scripts/.%252e/.%252e/winnt/system32/cmd.exe?/c+dir` | CVE-2001-0333 |
| IIS root.exe | `/scripts/root.exe?/c+dir` | Nimda/Code Red |
| Superfluous decode | `/scripts/..%e0%80%af../winnt/system32/cmd.exe?/c+dir` | CVE-2001-0333 |
| Awstats scanning | `/cgi-bin/awstats.pl`, `/awstats/awstats.pl`, `/stats/awstats.pl` | CVE-2005-0116 |
| FrontPage probing | `/_vti_bin`, URI too long with _vti_bin | FrontPage RPC vulnerabilities |

**Grading weights (equal)：** 五项标准中每一项对最终得分贡献 0.2。
</content>
