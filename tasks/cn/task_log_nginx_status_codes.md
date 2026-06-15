---
id: task_log_nginx_status_codes
name: Nginx 访问日志 - HTTP 状态码分布
category: 日志分析
scene: 数据库检索、表格整理与数据分析
sub_scene: 日志状态码分析
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 输出格式适配
- 指令遵循与约束理解
- 自然语言生成
grading_type: hybrid
timeout_seconds: 180
workspace_files:
  - dest: "nginx_access.log"
    source: "logs/nginx_access_json.log"
---

# Nginx 访问日志 - HTTP 状态码分布

## Prompt

分析位于 `nginx_access.log` 的 Nginx JSON 访问日志，并生成一份 HTTP 状态码分布报告。每一行都是一个 JSON 对象，包含以下字段：`time`、`remote_ip`、`remote_user`、`request`、`response`、`bytes`、`referrer`、`agent`。

你的报告应当包括：

1. **总请求数**：日志条目总数
2. **状态码分解**：观察到的每个 HTTP 状态码的计数和百分比
3. **状态码分类**：按类别分组（2xx 成功、3xx 重定向、4xx 客户端错误、5xx 服务器错误）并给出各类合计
4. **主要问题来源**：对 4xx 和 5xx 错误，列出产生错误最多的前 5 个客户端 IP
5. **请求路径**：对每个状态码，展示请求最多的前 3 个路径
6. **评估**：根据状态码分布对服务器健康状况做简要评估

将报告写入 `status_code_report.md`，作为一份结构良好的 markdown 文档。

---

## Expected Behavior

Agent 应当解析全部 1000 条 JSON 日志条目，并生成：

**总请求数：** 1000

**状态码分解：**
- 200: 35（3.5%）
- 206: 1（0.1%）
- 304: 274（27.4%）
- 403: 2（0.2%）
- 404: 688（68.8%）

**状态码分类：**
- 2xx: 36（3.6%）
- 3xx: 274（27.4%）
- 4xx: 690（69.0%）

**关键观察：**
- 日志覆盖 2015 年 5 月 17 日，约 08:05–16:05 UTC
- 404 错误占主导 — 接近全部请求的 69%
- 路径主要为 `/downloads/product_1` 和 `/downloads/product_2`
- 大部分流量来自 Debian APT 包管理器客户端
- 80.91.33.133 是最活跃的 IP，约有 210 个请求

可接受的变化：
- 具体百分比可能因四舍五入而有所差异
- 评估措辞会有所不同
- 欢迎附加的分析

---

## Grading Criteria

- [ ] 在工作区中创建了 `status_code_report.md`
- [ ] 报告了总请求数（1000）
- [ ] 列出了所有观察到的状态码及其计数（200、206、304、403、404）
- [ ] 状态码按类别分组（2xx、3xx、4xx）
- [ ] 识别出产生错误最多的 IP

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """Grade the Nginx status code distribution task."""
    from pathlib import Path

    scores = {}
    workspace = Path(workspace_path)
    report_file = workspace / "status_code_report.md"

    if not report_file.exists():
        return {
            "output_created": 0.0,
            "total_count": 0.0,
            "status_codes_listed": 0.0,
            "categories_grouped": 0.0,
            "top_error_ips": 0.0,
        }

    scores["output_created"] = 1.0
    content = report_file.read_text(encoding="utf-8").lower()

    # Check 1: Total request count
    scores["total_count"] = 1.0 if "1000" in content or "1,000" in content else 0.0

    # Check 2: All status codes listed
    has_200 = "200" in content
    has_304 = "304" in content
    has_404 = "404" in content
    has_403 = "403" in content
    codes_found = sum([has_200, has_304, has_404, has_403])
    scores["status_codes_listed"] = (
        1.0 if codes_found >= 4 else
        0.5 if codes_found >= 3 else 0.0
    )

    # Check 3: Categories grouped
    has_2xx = "2xx" in content or "success" in content
    has_3xx = "3xx" in content or "redirect" in content
    has_4xx = "4xx" in content or "client error" in content
    scores["categories_grouped"] = (
        1.0 if sum([has_2xx, has_3xx, has_4xx]) >= 3 else
        0.5 if sum([has_2xx, has_3xx, has_4xx]) >= 2 else 0.0
    )

    # Check 4: Top error IPs identified
    top_ips = ["80.91.33.133", "5.83.131.103", "202.143.95.26", "50.57.209.92"]
    ips_found = sum(1 for ip in top_ips if ip in content)
    scores["top_error_ips"] = (
        1.0 if ips_found >= 2 else
        0.5 if ips_found >= 1 else 0.0
    )

    return scores
```

---

## Additional Notes

**日志中的关键事实：**

- 1000 条 JSON 条目，单日：2015 年 5 月 17 日（08:05–16:05 UTC）
- 极高的 404 比率（68.8%）表明资源缺失或下载路径配置错误
- 流量以自动化为主（Debian APT 包管理器）
- 仅有 2 个主要路径：`/downloads/product_1` 和 `/downloads/product_2`
- 未观察到 5xx 服务器错误

**评分权重（均等）：** 五项标准中每一项对最终得分贡献 0.2。
