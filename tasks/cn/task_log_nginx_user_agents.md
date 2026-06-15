---
id: task_log_nginx_user_agents
name: Nginx 访问日志 - User Agent 分析
category: 日志分析
scene: 数据库检索、表格整理与数据分析
sub_scene: 日志User Agent分析
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 输出格式适配
- 自然语言生成
- 工具调用
grading_type: hybrid
timeout_seconds: 180
workspace_files:
  - dest: "nginx_access.log"
    source: "logs/nginx_access_json.log"
---

# Nginx 访问日志 - User Agent 分析

## Prompt

分析位于 `nginx_access.log` 的 Nginx JSON 访问日志，并生成一份全面的 User Agent 分析。每一行都是一个 JSON 对象，包含以下字段：`time`、`remote_ip`、`remote_user`、`request`、`response`、`bytes`、`referrer`、`agent`。

你的报告应当包括：

1. **唯一 User Agent**：不同 User Agent 字符串的总数
2. **User Agent 排名**：按请求数量排序列出所有 User Agent，并附上计数和百分比
3. **客户端类型分类**：将 Agent 归类为不同类型（包管理器、Web 浏览器、机器人/爬虫、命令行工具、未知/空）
4. **Agent 到 IP 的映射**：对每个 User Agent，有多少个唯一 IP 使用它？
5. **各 Agent 的成功率与错误率**：对每个 Agent，有多少百分比的请求以错误（4xx/5xx）告终？
6. **结论**：根据 User Agent 画像判断这是什么类型的服务器？

将报告写入 `user_agent_report.md`，作为一份结构良好的 markdown 文档。

---

## Expected Behavior

Agent 应当解析全部 1000 条 JSON 日志条目，并生成：

**唯一 User Agent：** 14 个不同的 Agent 字符串（包括表示空的 "-"）

**排名靠前的 User Agent：**
- `Debian APT-HTTP/1.3 (0.9.7.9)` — 370 个请求（37.0%）
- `Debian APT-HTTP/1.3 (0.8.16~exp12ubuntu10.16)` — 177（17.7%）
- `Debian APT-HTTP/1.3 (0.8.16~exp12ubuntu10.22)` — 118（11.8%）
- `Debian APT-HTTP/1.3 (1.0.1ubuntu2)` — 116（11.6%）
- `Debian APT-HTTP/1.3 (0.8.16~exp12ubuntu10.21)` — 64（6.4%）
- 其余的 APT 变体以及少数其他 Agent（Go 1.1 package http、urlgrabber 等）

**分类：**
- 包管理器（Debian APT）：绝大多数（约 95% 以上）
- 其他自动化工具：Go HTTP 客户端、urlgrabber
- 空/缺失的 Agent（"-"）：少量

**结论：**
- 这显然是一个 Debian/Ubuntu 包仓库或软件下载镜像
- 多个 APT 版本表明客户端运行着不同的 Ubuntu/Debian 发行版
- 几乎没有人类浏览器流量

可接受的变化：
- 具体计数可从日志确定性地得出
- 分类类别可使用不同的名称
- 评估措辞会有所不同

---

## Grading Criteria

- [ ] 在工作区中创建了 `user_agent_report.md`
- [ ] 列出了所有 User Agent 及其计数
- [ ] Agent 按类型进行了分类（包管理器、机器人等）
- [ ] 占主导地位的 Agent（Debian APT）被识别为主要客户端
- [ ] 正确推断出服务器用途（包仓库/下载镜像）

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """Grade the Nginx user agent analysis task."""
    from pathlib import Path

    scores = {}
    workspace = Path(workspace_path)
    report_file = workspace / "user_agent_report.md"

    if not report_file.exists():
        return {
            "output_created": 0.0,
            "agents_listed": 0.0,
            "agents_classified": 0.0,
            "apt_dominant": 0.0,
            "server_purpose": 0.0,
        }

    scores["output_created"] = 1.0
    content = report_file.read_text(encoding="utf-8").lower()

    # Check 1: User agents listed with counts
    has_apt = "apt-http" in content or "apt http" in content or "debian apt" in content
    has_counts = any(str(c) in content for c in ["370", "177", "118", "116"])
    scores["agents_listed"] = (
        1.0 if has_apt and has_counts else
        0.5 if has_apt else 0.0
    )

    # Check 2: Agents classified by type
    type_keywords = ["package manager", "bot", "crawler", "automated", "tool",
                     "browser", "command line", "cli", "client type", "categor"]
    scores["agents_classified"] = (
        1.0 if sum(1 for kw in type_keywords if kw in content) >= 2 else
        0.5 if sum(1 for kw in type_keywords if kw in content) >= 1 else 0.0
    )

    # Check 3: APT identified as dominant
    dominant_keywords = ["dominant", "majority", "most common", "primary",
                         "most frequent", "largest", "overwhelming"]
    has_dominant = any(kw in content for kw in dominant_keywords)
    scores["apt_dominant"] = (
        1.0 if has_apt and has_dominant else
        0.5 if has_apt else 0.0
    )

    # Check 4: Server purpose inferred
    purpose_keywords = ["repository", "mirror", "download", "package",
                        "software", "debian", "ubuntu", "apt"]
    scores["server_purpose"] = (
        1.0 if sum(1 for kw in purpose_keywords if kw in content) >= 3 else
        0.5 if sum(1 for kw in purpose_keywords if kw in content) >= 1 else 0.0
    )

    return scores
```

---

## Additional Notes

**日志中的关键事实：**

- 14 个唯一的 User Agent 字符串
- 超过 95% 的流量来自 Debian APT 包管理器
- 多个 APT 版本对应不同的 Ubuntu/Debian 发行版
- `Go 1.1 package http` 和 `urlgrabber` 等 Agent 的存在表明有一些非 APT 的自动化流量
- 部分条目的 Agent 为 "-"（空/缺失的 User Agent）

**评分权重（均等）：** 五项标准中每一项对最终得分贡献 0.2。
