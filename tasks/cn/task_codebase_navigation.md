---
id: task_codebase_navigation
name: 代码库导航
category: 编程
scene: 深度搜索与专题研究报告
sub_scene: 代码库导航分析
difficulty: L3
capabilities:
- 信息检索与综合
- 多步推理
- 工具调用
- 自然语言生成
grading_type: hybrid
timeout_seconds: 180
workspace_files: []
---

## Prompt

给你一个不熟悉的开源项目：GitHub 上的 **expressjs/express** 仓库（https://github.com/expressjs/express）。

回答以下关于该代码库中身份认证与请求处理工作方式的问题。将你的答案保存到 `codebase_report.md`。

1. **路由在哪里处理？** 找出负责路由匹配与分发的文件。给出相对于仓库根目录的文件路径。
2. **请求与响应对象在哪里被扩展？** 找到那些添加 Express 特有方法（如 `res.send`、`res.json`、`req.params`）的文件。给出文件路径。
3. **中间件执行如何工作？** 追踪从请求到达到中间件栈被执行的代码路径。描述涉及的关键函数与文件。
4. **身份认证中间件会在哪里接入？** 基于该架构，说明像 `passport` 这样的中间件会在哪里以及如何集成。引用你发现的具体代码模式。

对于每个答案，包含你查阅过的具体文件路径与行号范围。在有帮助时使用代码片段。

## Expected Behavior

Agent 应当：

1. 克隆或浏览 Express.js 仓库以查看其源代码
2. 导航代码库以识别路由逻辑（`lib/router/index.js`、`lib/router/route.js`、`lib/router/layer.js`）
3. 找到请求/响应扩展（`lib/request.js`、`lib/response.js`）
4. 通过路由器的 `handle` 方法追踪中间件执行
5. 解释中间件模式以及认证会在哪里接入
6. 将一份结构良好的报告保存到 `codebase_report.md`

Agent 可以使用 `git clone`、`gh` CLI、网页抓取或任意组合来探索代码。关键在于展现导航和理解陌生代码库的能力。

## Grading Criteria

- [ ] 已创建文件 `codebase_report.md`
- [ ] 报告识别出路由文件（lib/router/）
- [ ] 报告识别出请求/响应扩展文件
- [ ] 报告解释了中间件执行流程
- [ ] 报告讨论了身份认证的集成点
- [ ] 文件路径具体且准确
- [ ] 包含代码片段或行号引用

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    from pathlib import Path
    import re

    scores = {}
    workspace = Path(workspace_path)
    report = workspace / "codebase_report.md"

    if not report.exists():
        return {
            "file_created": 0.0,
            "routing_identified": 0.0,
            "req_res_identified": 0.0,
            "middleware_explained": 0.0,
            "auth_discussed": 0.0,
        }

    scores["file_created"] = 1.0
    content = report.read_text().lower()

    # Check for routing file identification
    routing_keywords = ["lib/router", "router/index", "route.js", "layer.js", "dispatch"]
    routing_matches = sum(1 for k in routing_keywords if k in content)
    scores["routing_identified"] = min(1.0, routing_matches / 2)

    # Check for request/response identification
    reqres_keywords = ["lib/request", "lib/response", "res.send", "res.json", "req.params"]
    reqres_matches = sum(1 for k in reqres_keywords if k in content)
    scores["req_res_identified"] = min(1.0, reqres_matches / 2)

    # Check for middleware explanation
    mw_keywords = ["middleware", "next(", "next function", "stack", "handle", "use("]
    mw_matches = sum(1 for k in mw_keywords if k in content)
    scores["middleware_explained"] = min(1.0, mw_matches / 2)

    # Check for auth discussion
    auth_keywords = ["auth", "passport", "middleware", "hook", "session", "token"]
    auth_matches = sum(1 for k in auth_keywords if k in content)
    scores["auth_discussed"] = min(1.0, auth_matches / 2)

    return scores
```

## LLM Judge Rubric

### Criterion 1: Codebase Understanding (Weight: 35%)

**Score 1.0**: 报告展现出对 Express 内部机制的深刻理解。正确识别 router、layer 与 route 抽象。从 `app.handle` 到路由器分发完整追踪请求生命周期。引用了具体函数及其作用。
**Score 0.75**: 报告正确识别关键文件并解释了整体架构，但在中间件链或路由内部机制上遗漏了一些细微之处。
**Score 0.5**: 报告识别出一些正确的文件，但解释停留在表面或存在轻微不准确之处。
**Score 0.25**: 报告提及了 Express 文件，但对它们之间关系的理解有限。
**Score 0.0**: 报告缺失，或没有任何代码库探索的证据。

### Criterion 2: Navigation Strategy (Weight: 25%)

**Score 1.0**: Agent 使用了有效的代码库导航策略——搜索关键术语、跟踪 import、先阅读入口点再深入细节。有系统化探索的证据。
**Score 0.75**: Agent 展现了合理的导航能力，但本可以更高效或更系统。
**Score 0.5**: Agent 找到了一些相关代码，但导航杂乱或低效。
**Score 0.25**: Agent 在寻找相关代码上明显吃力。
**Score 0.0**: 没有代码库导航的证据。

### Criterion 3: Specificity and Evidence (Weight: 25%)

**Score 1.0**: 报告包含具体的文件路径、行号或行号范围，以及直接支撑每个答案的代码片段。论断有具体引用支撑。
**Score 0.75**: 报告包含文件路径和一些代码引用，但并非所有论断都有充分证据。
**Score 0.5**: 报告有一些文件路径，但缺少代码片段或具体的行号引用。
**Score 0.25**: 报告大多是笼统陈述，缺少具体的代码引用。
**Score 0.0**: 没有对源代码的具体引用。

### Criterion 4: Auth Integration Analysis (Weight: 15%)

**Score 1.0**: 清晰解释了身份认证中间件如何与 Express 的中间件模式集成。引用了 `app.use()`、中间件顺序以及 `next()` 模式。可能引用真实的认证库。
**Score 0.75**: 对认证集成有良好解释，存在轻微缺口。
**Score 0.5**: 基本解释正确，但缺乏深度。
**Score 0.25**: 解释含糊或部分不正确。
**Score 0.0**: 没有讨论身份认证集成。

## Additional Notes

- 选择 Express.js 是因为它是一个知名、稳定、可公开访问且具有清晰架构模式的代码库。
- Agent 可以使用 `git clone`、`gh api`、网页抓取或浏览器工具来探索代码。
- 此任务考察 Agent 系统化导航陌生代码并将发现综合成一份连贯报告的能力。
