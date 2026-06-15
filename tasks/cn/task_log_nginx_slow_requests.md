---
id: task_log_nginx_slow_requests
name: Nginx 访问日志 - 查找最大响应
category: 日志分析
scene: 数据库检索、表格整理与数据分析
sub_scene: 访问日志分析
difficulty: L2
capabilities:
- 数据提取与处理
- 多步推理
- 输出格式适配
- 代码生成与理解
- 指令遵循与约束理解
grading_type: hybrid
timeout_seconds: 180
workspace_files:
  - dest: "nginx_access.log"
    source: "logs/nginx_access_json.log"
---

# Nginx 访问日志 - 查找最大响应

## Prompt

分析位于 `nginx_access.log` 的 Nginx JSON 访问日志，并识别产生最大响应（按传输字节数）的请求。每一行都是一个 JSON 对象，包含以下字段：`time`、`remote_ip`、`remote_user`、`request`、`response`、`bytes`、`referrer`、`agent`。

你的报告应当包括：

1. **最大的前 10 个响应**：列出字节数最高的请求，包括时间戳、客户端 IP、请求路径、状态码和字节数
2. **字节分布摘要**：总体统计 — 传输字节数的最小值、最大值、平均值、中位数（不含零字节响应）
3. **零字节响应**：零字节响应的数量以及哪些状态码会产生这类响应
4. **大响应分析**：哪些路径和客户端 IP 与最大的传输相关联？
5. **效率评估**：有多少百分比的请求产生了实际数据传输，而非缓存命中（304）？

将报告写入 `large_responses_report.md`，作为一份结构良好的 markdown 文档。

---

## Expected Behavior

Agent 应当解析全部 1000 条 JSON 日志条目，并生成：

**最大的响应：**
- 观察到的最大字节数：约 3318 字节
- 最大的响应是针对 `/downloads/product_1` 和 `/downloads/product_2` 的 200 OK 响应
- 排名靠前的字节值包括：3318、3316、3301、2582、2578 等

**零字节分析：**
- 304 Not Modified 响应全部为 0 字节（274 条）
- 404 响应的字节数较小（通常在 300-340 区间）

**效率：**
- 1000 个请求中约有 274 个是 304（缓存命中）— 27.4%
- 携带数据的 200 OK：约 35 个请求 — 3.5%
- 404 错误：688 个请求 — 这些传输的是较小的错误页面

可接受的变化：
- 具体字节值可从日志确定性地得出
- 评估措辞会有所不同
- 列出前 10 或前 20 都可以

---

## Grading Criteria

- [ ] 在工作区中创建了 `large_responses_report.md`
- [ ] 列出了最大的响应及其字节数
- [ ] 对零字节 / 304 响应进行了单独分析
- [ ] 提供了分布统计（最小值、最大值、平均值或中位数）
- [ ] 识别出与最大响应相关联的路径

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """Grade the Nginx largest responses task."""
    from pathlib import Path

    scores = {}
    workspace = Path(workspace_path)
    report_file = workspace / "large_responses_report.md"

    if not report_file.exists():
        return {
            "output_created": 0.0,
            "top_responses_listed": 0.0,
            "zero_byte_analysis": 0.0,
            "distribution_stats": 0.0,
            "paths_identified": 0.0,
        }

    scores["output_created"] = 1.0
    content = report_file.read_text(encoding="utf-8").lower()

    # Check 1: Top responses listed with byte counts
    has_max_bytes = any(b in content for b in ["3318", "3316", "3301"])
    has_ranking = any(kw in content for kw in ["top", "largest", "biggest", "highest"])
    scores["top_responses_listed"] = (
        1.0 if has_max_bytes and has_ranking else
        0.5 if has_max_bytes else 0.0
    )

    # Check 2: Zero-byte / 304 analysis
    has_zero = "0 byte" in content or "zero byte" in content or "zero-byte" in content or "no data" in content
    has_304 = "304" in content
    scores["zero_byte_analysis"] = (
        1.0 if has_304 and has_zero else
        0.5 if has_304 else 0.0
    )

    # Check 3: Distribution statistics
    stat_keywords = ["min", "max", "mean", "median", "average", "total bytes",
                     "distribution", "range"]
    scores["distribution_stats"] = (
        1.0 if sum(1 for kw in stat_keywords if kw in content) >= 3 else
        0.5 if sum(1 for kw in stat_keywords if kw in content) >= 1 else 0.0
    )

    # Check 4: Paths identified
    has_product_1 = "product_1" in content
    has_product_2 = "product_2" in content
    has_downloads = "downloads" in content or "/download" in content
    scores["paths_identified"] = (
        1.0 if has_product_1 and has_product_2 else
        0.5 if has_downloads else 0.0
    )

    return scores
```

---

## Additional Notes

**日志中的关键事实：**

- 最大响应大小仅约 3318 字节 — 这是一个轻量级下载服务器
- 绝大多数响应要么是 304（0 字节），要么是 404（小型错误页面）
- 只有约 35 个请求返回带有实际内容的 200
- 所有请求都只指向两个路径：`/downloads/product_1` 和 `/downloads/product_2`

**评分权重（均等）：** 五项标准中每一项对最终得分贡献 0.2。
