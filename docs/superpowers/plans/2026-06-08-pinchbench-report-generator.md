# PinchBench 评测报告生成 Skill 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建 pinchbench-report-generator Skill，自动分析 PinchBench 多模型评测结果并生成结构化对比报告，对目标模型做失分点深度分析。

**Architecture:** 三阶段流水线 —— Python `collect`（扫描目录、计算统计、筛选低分任务）→ LLM `analyze`（读 transcript 做能力归类与失分分析）→ Python `render`（拼装 Markdown 报告）。Python 负责所有数字计算保证准确，LLM 只产出分析文字章节。

**Tech Stack:** Python 3.10+、pytest、标准库（json/pathlib/statistics/argparse/dataclasses）。复用 `skill/skills/shared/`。

---

## 文件结构

新建目录 `skill/skills/pinchbench-report-generator/`：

| 文件 | 职责 |
|------|------|
| `models.py` | 数据类定义（ModelResult/TaskResult/CollectedData 等），统一类型契约 |
| `result_collector.py` | 阶段1：目录扫描、模型识别、JSON 解析 |
| `score_calculator.py` | 得分率、分类别、排名、Token 效率计算 |
| `task_filter.py` | 低分任务筛选（相对短板 + 全员低分 + 绝对阈值回退） |
| `report_renderer.py` | 阶段3：Markdown 模板拼装 |
| `report_cli.py` | CLI 入口（collect / render 子命令） |
| `agent-capability-dimensions.md` | 能力维度静态资源（从 docs/ 复制） |
| `SKILL.md` | Skill 说明 + 阶段2 LLM 工作指引 |
| `test_*.py` | 各模块单测 |

所有 Python 文件路径前缀：`/Users/gzx/Project/GitHub/xgz/ai/evaluate/PinchBench/skill/skills/pinchbench-report-generator/`

测试运行约定：`cd skill && python -m pytest skills/pinchbench-report-generator/test_xxx.py -v`

---

## Task 1: 项目骨架与数据类定义

**Files:**
- Create: `skills/pinchbench-report-generator/__init__.py`
- Create: `skills/pinchbench-report-generator/models.py`
- Test: `skills/pinchbench-report-generator/test_models.py`

- [ ] **Step 1: 创建 __init__.py**

创建空文件 `skills/pinchbench-report-generator/__init__.py`（内容为空）。

- [ ] **Step 2: 写失败测试 test_models.py**

```python
"""数据类契约测试。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from models import TaskResult, ModelResult


def test_task_result_fields():
    t = TaskResult(
        task_id="task_stock",
        category="research",
        status="success",
        timed_out=False,
        execution_time=12.5,
        score=0.0,
        breakdown={"automated.file_created": 0.0},
        notes="failed",
        input_tokens=100,
        output_tokens=50,
        total_tokens=150,
        request_count=3,
    )
    assert t.task_id == "task_stock"
    assert t.score == 0.0
    assert t.total_tokens == 150


def test_model_result_aggregates():
    tasks = [
        TaskResult("task_a", "coding", "success", False, 1.0, 1.0, {}, "", 10, 5, 15, 1),
        TaskResult("task_b", "research", "success", False, 1.0, 0.5, {}, "", 20, 10, 30, 2),
    ]
    m = ModelResult(model="xspark", display_name="Spark", suite="all",
                    benchmark_version="2.0.0", tasks=tasks)
    assert m.total_tokens == 45
    assert m.total_requests == 3
    assert m.task_count == 2
```

- [ ] **Step 3: 运行测试确认失败**

Run: `cd skill && python -m pytest skills/pinchbench-report-generator/test_models.py -v`
Expected: FAIL（ModuleNotFoundError: No module named 'models'）

- [ ] **Step 4: 实现 models.py**

```python
"""报告生成器数据类定义，统一各阶段类型契约。"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TaskResult:
    """单个任务在单个模型上的评测结果。"""
    task_id: str
    category: str
    status: str
    timed_out: bool
    execution_time: Optional[float]
    score: float                      # grading.mean
    breakdown: Dict[str, float]       # grading.runs[0].breakdown
    notes: str                        # grading.runs[0].notes
    input_tokens: int
    output_tokens: int
    total_tokens: int
    request_count: int


@dataclass
class ModelResult:
    """单个模型的完整评测结果。"""
    model: str                        # JSON 的 model 字段（内部 key）
    display_name: str                 # 展示名（默认同 model）
    suite: str
    benchmark_version: str
    tasks: List[TaskResult] = field(default_factory=list)

    @property
    def task_count(self) -> int:
        return len(self.tasks)

    @property
    def total_tokens(self) -> int:
        return sum(t.total_tokens for t in self.tasks)

    @property
    def total_requests(self) -> int:
        return sum(t.request_count for t in self.tasks)
```

- [ ] **Step 5: 运行测试确认通过**

Run: `cd skill && python -m pytest skills/pinchbench-report-generator/test_models.py -v`
Expected: PASS（2 passed）

- [ ] **Step 6: 提交**

```bash
cd skill && git add skills/pinchbench-report-generator/__init__.py skills/pinchbench-report-generator/models.py skills/pinchbench-report-generator/test_models.py
git commit -m "feat(report-gen): add data class skeleton"
```

## Task 2: 模型目录识别与 JSON 解析（result_collector.py）

**Files:**
- Create: `skills/pinchbench-report-generator/result_collector.py`
- Test: `skills/pinchbench-report-generator/test_result_collector.py`

按内容识别模型目录：目录下同时含 `*.json` 结果文件和 `*_transcripts/`。模型展示名优先取 JSON 的 `model` 字段。

- [ ] **Step 1: 写失败测试**

```python
"""目录扫描与 JSON 解析测试。"""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from result_collector import discover_model_dirs, parse_model_json


def _make_model_dir(base: Path, name: str, model_field: str, tasks: list):
    d = base / name
    d.mkdir(parents=True)
    (d / "0001_transcripts").mkdir()
    payload = {
        "model": model_field, "benchmark_version": "2.0.0",
        "run_id": "0001", "suite": "all", "tasks": tasks,
    }
    (d / f"0001_{name}.json").write_text(json.dumps(payload))
    return d


def _task(tid, cat, score, total=100, reqs=1):
    return {
        "task_id": tid, "status": "success", "timed_out": False,
        "execution_time": 1.0,
        "usage": {"input_tokens": total - 10, "output_tokens": 10,
                  "total_tokens": total, "request_count": reqs},
        "grading": {"mean": score, "runs": [
            {"breakdown": {"automated.x": score}, "notes": "n"}]},
        "frontmatter": {"category": cat, "grading_weights": {}},
    }


def test_discover_model_dirs(tmp_path):
    _make_model_dir(tmp_path, "xspark", "xsparkx2flash", [_task("task_a", "coding", 1.0)])
    _make_model_dir(tmp_path, "xglm", "xopglm5", [_task("task_a", "coding", 0.9)])
    (tmp_path / "not_a_model").mkdir()  # 无 json/transcripts，应被忽略
    dirs = discover_model_dirs([tmp_path])
    assert len(dirs) == 2
    assert {d.name for d in dirs} == {"xspark", "xglm"}


def test_discover_explicit_dirs(tmp_path):
    d1 = _make_model_dir(tmp_path, "xspark", "xsparkx2flash", [_task("task_a", "coding", 1.0)])
    _make_model_dir(tmp_path, "xglm", "xopglm5", [_task("task_a", "coding", 0.9)])
    dirs = discover_model_dirs([d1])  # 显式只传一个
    assert len(dirs) == 1
    assert dirs[0].name == "xspark"


def test_parse_model_json(tmp_path):
    d = _make_model_dir(tmp_path, "xspark", "xsparkx2flash",
                        [_task("task_a", "coding", 1.0, total=150, reqs=2)])
    m = parse_model_json(d)
    assert m.model == "xsparkx2flash"
    assert m.display_name == "xsparkx2flash"
    assert m.suite == "all"
    assert m.task_count == 1
    t = m.tasks[0]
    assert t.category == "coding"
    assert t.score == 1.0
    assert t.total_tokens == 150
    assert t.request_count == 2
    assert t.breakdown == {"automated.x": 1.0}
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd skill && python -m pytest skills/pinchbench-report-generator/test_result_collector.py -v`
Expected: FAIL（No module named 'result_collector'）

- [ ] **Step 3: 实现 result_collector.py**

```python
"""阶段1：模型目录扫描与结果 JSON 解析。"""
import json
from pathlib import Path
from typing import List

from models import ModelResult, TaskResult


def _is_model_dir(d: Path) -> bool:
    """目录同时含 *.json 结果文件和 *_transcripts/ 即视为模型目录。"""
    if not d.is_dir():
        return False
    has_json = any(d.glob("*.json"))
    has_transcripts = any(p.is_dir() and p.name.endswith("_transcripts")
                          for p in d.iterdir())
    return has_json and has_transcripts


def discover_model_dirs(inputs: List[Path]) -> List[Path]:
    """
    识别模型目录。
    - 输入本身是模型目录 → 直接收录
    - 输入是总目录 → 递归其直接子目录中的模型目录
    """
    found = []
    for inp in inputs:
        if _is_model_dir(inp):
            found.append(inp)
            continue
        for child in sorted(inp.iterdir()):
            if _is_model_dir(child):
                found.append(child)
    # 去重，保持顺序
    seen, uniq = set(), []
    for d in found:
        key = d.resolve()
        if key not in seen:
            seen.add(key)
            uniq.append(d)
    return uniq


def _find_result_json(model_dir: Path) -> Path:
    """选择结果 JSON：排除非结果文件，取第一个。"""
    candidates = [f for f in sorted(model_dir.glob("*.json"))]
    if not candidates:
        raise FileNotFoundError(f"模型目录无结果 JSON: {model_dir}")
    return candidates[0]


def parse_model_json(model_dir: Path) -> ModelResult:
    """解析单个模型目录的结果 JSON 为 ModelResult。"""
    json_path = _find_result_json(model_dir)
    data = json.loads(json_path.read_text())

    tasks = []
    for t in data.get("tasks", []):
        grading = t.get("grading", {})
        runs = grading.get("runs", [{}])
        run0 = runs[0] if runs else {}
        usage = t.get("usage", {})
        fm = t.get("frontmatter", {})
        tasks.append(TaskResult(
            task_id=t.get("task_id", ""),
            category=fm.get("category", "unknown"),
            status=t.get("status", "unknown"),
            timed_out=t.get("timed_out", False),
            execution_time=t.get("execution_time"),
            score=grading.get("mean", 0.0),
            breakdown=run0.get("breakdown", {}),
            notes=run0.get("notes", ""),
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            request_count=usage.get("request_count", 0),
        ))

    model_field = data.get("model", model_dir.name)
    return ModelResult(
        model=model_field,
        display_name=model_field,
        suite=data.get("suite", "unknown"),
        benchmark_version=data.get("benchmark_version", "unknown"),
        tasks=tasks,
    )


def collect_all(inputs: List[Path]) -> List[ModelResult]:
    """扫描所有输入路径，返回所有模型结果。"""
    return [parse_model_json(d) for d in discover_model_dirs(inputs)]
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd skill && python -m pytest skills/pinchbench-report-generator/test_result_collector.py -v`
Expected: PASS（3 passed）

- [ ] **Step 5: 用真实数据冒烟验证**

Run: `cd skill && python -c "from pathlib import Path; import sys; sys.path.insert(0,'skills/pinchbench-report-generator'); from result_collector import collect_all; ms=collect_all([Path('../astronclaw-result/all-suite/round-2')]); print(len(ms),'models:',[m.model for m in ms])"`
Expected: 输出 4 个模型（xopdeepseekv4pro/xopglm5/xopglm51/xsparkx2flash）

- [ ] **Step 6: 提交**

```bash
cd skill && git add skills/pinchbench-report-generator/result_collector.py skills/pinchbench-report-generator/test_result_collector.py
git commit -m "feat(report-gen): add model dir discovery and JSON parsing"
```

## Task 3: 统计指标计算（score_calculator.py）

**Files:**
- Create: `skills/pinchbench-report-generator/score_calculator.py`
- Test: `skills/pinchbench-report-generator/test_score_calculator.py`

- [ ] **Step 1: 写失败测试**

```python
"""统计指标计算测试。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from models import ModelResult, TaskResult
from score_calculator import (
    overall_score_rate, category_scores, count_high_tasks,
    count_low_tasks, token_efficiency, build_category_summary,
)


def _t(tid, cat, score, total=1000):
    return TaskResult(tid, cat, "success", False, 1.0, score, {}, "",
                      total - 10, 10, total, 1)


def _model(name, tasks):
    return ModelResult(name, name, "all", "2.0.0", tasks)


def test_overall_score_rate():
    m = _model("a", [_t("t1", "coding", 1.0), _t("t2", "research", 0.5)])
    assert abs(overall_score_rate(m) - 0.75) < 1e-9


def test_category_scores():
    m = _model("a", [_t("t1", "coding", 1.0), _t("t2", "coding", 0.8),
                     _t("t3", "research", 0.4)])
    cs = category_scores(m)
    assert abs(cs["coding"] - 0.9) < 1e-9
    assert abs(cs["research"] - 0.4) < 1e-9


def test_count_high_low_tasks():
    m = _model("a", [_t("t1", "c", 0.96), _t("t2", "c", 0.95),
                     _t("t3", "c", 0.5), _t("t4", "c", 0.3)])
    assert count_high_tasks(m) == 2     # >=0.95
    assert count_low_tasks(m) == 2      # <0.60


def test_token_efficiency():
    m = _model("a", [_t("t1", "c", 1.0, total=1000)])
    # 得分率 1.0 / 1000 tokens = 0.001 per token
    assert abs(token_efficiency(m) - (1.0 / 1000)) < 1e-12


def test_build_category_summary():
    m1 = _model("a", [_t("t1", "coding", 1.0), _t("t2", "research", 0.4)])
    m2 = _model("b", [_t("t1", "coding", 0.8), _t("t2", "research", 1.0)])
    summary = build_category_summary([m1, m2])
    # 每个类别一行，含每模型得分 + 最优模型
    coding = next(r for r in summary if r["category"] == "coding")
    assert coding["scores"]["a"] == 1.0
    assert coding["scores"]["b"] == 0.8
    assert coding["best_model"] == "a"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd skill && python -m pytest skills/pinchbench-report-generator/test_score_calculator.py -v`
Expected: FAIL（No module named 'score_calculator'）

- [ ] **Step 3: 实现 score_calculator.py**

```python
"""统计指标计算：得分率、分类别、排名、Token 效率。"""
from collections import defaultdict
from statistics import mean
from typing import Dict, List

from models import ModelResult

HIGH_THRESHOLD = 0.95   # ≥95% 优秀覆盖面
LOW_THRESHOLD = 0.60    # <60% 明显短板


def overall_score_rate(m: ModelResult) -> float:
    """总得分率 = 各任务得分均值。"""
    if not m.tasks:
        return 0.0
    return mean(t.score for t in m.tasks)


def category_scores(m: ModelResult) -> Dict[str, float]:
    """按 category 分组求均值。"""
    groups: Dict[str, List[float]] = defaultdict(list)
    for t in m.tasks:
        groups[t.category].append(t.score)
    return {cat: mean(scores) for cat, scores in groups.items()}


def count_high_tasks(m: ModelResult) -> int:
    """得分率 ≥ HIGH_THRESHOLD 的任务数。"""
    return sum(1 for t in m.tasks if t.score >= HIGH_THRESHOLD)


def count_low_tasks(m: ModelResult) -> int:
    """得分率 < LOW_THRESHOLD 的任务数。"""
    return sum(1 for t in m.tasks if t.score < LOW_THRESHOLD)


def token_efficiency(m: ModelResult) -> float:
    """每 token 得分 = 总得分率 / 总 token。"""
    total = m.total_tokens
    if total == 0:
        return 0.0
    return overall_score_rate(m) / total


def build_category_summary(models: List[ModelResult]) -> List[Dict]:
    """
    生成分类别汇总：每类别一行，含各模型得分和最优模型。

    Returns: [{"category": str, "scores": {model: float}, "best_model": str}]
    """
    all_cats = sorted({t.category for m in models for t in m.tasks})
    rows = []
    for cat in all_cats:
        scores = {}
        for m in models:
            cat_tasks = [t.score for t in m.tasks if t.category == cat]
            scores[m.model] = mean(cat_tasks) if cat_tasks else 0.0
        best = max(scores, key=scores.get) if scores else ""
        rows.append({"category": cat, "scores": scores, "best_model": best})
    return rows


def rank_models(models: List[ModelResult]) -> List[ModelResult]:
    """按总得分率降序排名。"""
    return sorted(models, key=overall_score_rate, reverse=True)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd skill && python -m pytest skills/pinchbench-report-generator/test_score_calculator.py -v`
Expected: PASS（5 passed）

- [ ] **Step 5: 提交**

```bash
cd skill && git add skills/pinchbench-report-generator/score_calculator.py skills/pinchbench-report-generator/test_score_calculator.py
git commit -m "feat(report-gen): add score and statistics calculations"
```

## Task 4: 低分任务筛选（task_filter.py）

**Files:**
- Create: `skills/pinchbench-report-generator/task_filter.py`
- Test: `skills/pinchbench-report-generator/test_task_filter.py`

筛选需 LLM 深度分析的任务。多模型：① 相对短板（对比模型中位数≥0.8 且目标落后≥0.2）② 全员低分（所有模型<0.4）。单模型回退：绝对阈值（目标<0.8）。

- [ ] **Step 1: 写失败测试**

```python
"""低分任务筛选测试。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from models import ModelResult, TaskResult
from task_filter import filter_tasks_to_analyze, FilterThresholds


def _t(tid, score):
    return TaskResult(tid, "cat", "success", False, 1.0, score, {}, "", 90, 10, 100, 1)


def _model(name, scores_by_task):
    tasks = [_t(tid, s) for tid, s in scores_by_task.items()]
    return ModelResult(name, name, "all", "2.0.0", tasks)


def test_relative_weakness():
    # 目标 spark 在 task_stock 落后：其他满分，spark 0分
    target = _model("spark", {"task_stock": 0.0, "task_ok": 1.0})
    o1 = _model("ds", {"task_stock": 1.0, "task_ok": 1.0})
    o2 = _model("glm", {"task_stock": 1.0, "task_ok": 1.0})
    picked = filter_tasks_to_analyze([target, o1, o2], target_model="spark")
    reasons = {p["task_id"]: p["reason"] for p in picked}
    assert reasons["task_stock"] == "relative_weakness"
    assert "task_ok" not in reasons


def test_all_low():
    # 所有模型在 task_hard 都 <0.4
    target = _model("spark", {"task_hard": 0.3, "task_ok": 1.0})
    o1 = _model("ds", {"task_hard": 0.35, "task_ok": 1.0})
    picked = filter_tasks_to_analyze([target, o1], target_model="spark")
    reasons = {p["task_id"]: p["reason"] for p in picked}
    assert reasons["task_hard"] == "all_low"


def test_no_pick_when_target_close():
    # 目标与对比差距 <0.2，不入选
    target = _model("spark", {"task_x": 0.9})
    o1 = _model("ds", {"task_x": 1.0})
    picked = filter_tasks_to_analyze([target, o1], target_model="spark")
    assert picked == []


def test_single_model_fallback():
    # 单模型：绝对阈值 <0.8
    target = _model("spark", {"task_low": 0.5, "task_ok": 0.9})
    picked = filter_tasks_to_analyze([target], target_model="spark")
    reasons = {p["task_id"]: p["reason"] for p in picked}
    assert reasons["task_low"] == "absolute_low"
    assert "task_ok" not in reasons


def test_custom_thresholds():
    target = _model("spark", {"task_x": 0.5})
    o1 = _model("ds", {"task_x": 0.6})
    th = FilterThresholds(all_low=0.7)  # 提高全员低分阈值
    picked = filter_tasks_to_analyze([target, o1], target_model="spark", thresholds=th)
    reasons = {p["task_id"]: p["reason"] for p in picked}
    assert reasons["task_x"] == "all_low"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd skill && python -m pytest skills/pinchbench-report-generator/test_task_filter.py -v`
Expected: FAIL（No module named 'task_filter'）

- [ ] **Step 3: 实现 task_filter.py**

```python
"""低分任务筛选：相对短板 + 全员低分 + 单模型绝对阈值回退。"""
from dataclasses import dataclass
from statistics import median
from typing import Dict, List, Optional

from models import ModelResult


@dataclass
class FilterThresholds:
    """筛选阈值，可通过 CLI 覆盖。"""
    relative_weakness_min_others: float = 0.8   # 对比模型中位数下限
    relative_weakness_gap: float = 0.2          # 目标落后幅度
    all_low: float = 0.4                         # 全员低分阈值
    absolute_low: float = 0.8                    # 单模型绝对阈值


def _score_map(m: ModelResult) -> Dict[str, float]:
    return {t.task_id: t.score for t in m.tasks}


def filter_tasks_to_analyze(
    models: List[ModelResult],
    target_model: str,
    thresholds: Optional[FilterThresholds] = None,
) -> List[Dict]:
    """
    返回待深度分析任务列表：[{"task_id": str, "reason": str}]
    reason ∈ {relative_weakness, all_low, absolute_low}
    """
    th = thresholds or FilterThresholds()
    target = next((m for m in models if m.model == target_model), None)
    if target is None:
        raise ValueError(f"目标模型不存在: {target_model}")

    others = [m for m in models if m.model != target_model]
    target_scores = _score_map(target)
    picked = []

    # 单模型回退：绝对阈值
    if not others:
        for tid, score in target_scores.items():
            if score < th.absolute_low:
                picked.append({"task_id": tid, "reason": "absolute_low"})
        return picked

    other_maps = [_score_map(m) for m in others]
    for tid, t_score in target_scores.items():
        other_scores = [om[tid] for om in other_maps if tid in om]
        if not other_scores:
            continue

        # ② 全员低分（含目标）
        if t_score < th.all_low and all(s < th.all_low for s in other_scores):
            picked.append({"task_id": tid, "reason": "all_low"})
            continue

        # ① 相对短板
        others_median = median(other_scores)
        if (others_median >= th.relative_weakness_min_others
                and (others_median - t_score) >= th.relative_weakness_gap):
            picked.append({"task_id": tid, "reason": "relative_weakness"})

    return picked
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd skill && python -m pytest skills/pinchbench-report-generator/test_task_filter.py -v`
Expected: PASS（5 passed）

- [ ] **Step 5: 提交**

```bash
cd skill && git add skills/pinchbench-report-generator/task_filter.py skills/pinchbench-report-generator/test_task_filter.py
git commit -m "feat(report-gen): add low-score task filtering"
```

## Task 5: collect 编排与 collected_data.json 序列化

**Files:**
- Create: `skills/pinchbench-report-generator/collect.py`
- Test: `skills/pinchbench-report-generator/test_collect.py`

整合 Task 2-4，产出阶段2 所需的 `collected_data.json`，并定位每个待分析任务的 transcript 路径与任务 md 路径。

- [ ] **Step 1: 写失败测试**

```python
"""collect 编排测试。"""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from collect import build_collected_data, resolve_transcript_path


def _make_model_dir(base, name, model_field, tasks):
    d = base / name
    d.mkdir(parents=True)
    td = d / "0001_transcripts"
    td.mkdir()
    for t in tasks:
        (td / f"{t['task_id']}.jsonl").write_text('{"type":"session"}\n')
    payload = {"model": model_field, "benchmark_version": "2.0.0",
               "run_id": "0001", "suite": "all", "tasks": tasks}
    (d / f"0001_{name}.json").write_text(json.dumps(payload))
    return d


def _task(tid, cat, score):
    return {"task_id": tid, "status": "success", "timed_out": False,
            "execution_time": 1.0,
            "usage": {"input_tokens": 90, "output_tokens": 10,
                      "total_tokens": 100, "request_count": 1},
            "grading": {"mean": score, "runs": [
                {"breakdown": {"automated.x": score}, "notes": "note"}]},
            "frontmatter": {"category": cat, "grading_weights": {}}}


def test_build_collected_data(tmp_path):
    _make_model_dir(tmp_path, "spark", "xsparkx2flash",
                    [_task("task_stock", "research", 0.0), _task("task_ok", "coding", 1.0)])
    _make_model_dir(tmp_path, "ds", "xopdeepseek",
                    [_task("task_stock", "research", 1.0), _task("task_ok", "coding", 1.0)])
    data = build_collected_data([tmp_path], target_model="xsparkx2flash",
                                tasks_root=tmp_path / "tasks")
    assert data["target_model"] == "xsparkx2flash"
    assert len(data["models"]) == 2
    assert data["is_single_model"] is False
    # task_stock 应被筛为相对短板
    analyze_ids = {a["task_id"] for a in data["tasks_to_analyze"]}
    assert "task_stock" in analyze_ids
    # transcript 路径已解析
    stock = next(a for a in data["tasks_to_analyze"] if a["task_id"] == "task_stock")
    assert stock["target_transcript"].endswith("task_stock.jsonl")


def test_resolve_transcript_path(tmp_path):
    d = _make_model_dir(tmp_path, "spark", "xsparkx2flash",
                        [_task("task_stock", "research", 0.0)])
    p = resolve_transcript_path(d, "task_stock")
    assert p is not None and p.name == "task_stock.jsonl"
    assert resolve_transcript_path(d, "task_missing") is None
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd skill && python -m pytest skills/pinchbench-report-generator/test_collect.py -v`
Expected: FAIL（No module named 'collect'）

- [ ] **Step 3: 实现 collect.py**

```python
"""阶段1 编排：整合收集、计算、筛选，产出 collected_data.json。"""
from pathlib import Path
from typing import Dict, List, Optional

from models import ModelResult
from result_collector import collect_all, discover_model_dirs
import score_calculator as sc
from task_filter import filter_tasks_to_analyze, FilterThresholds


def resolve_transcript_path(model_dir: Path, task_id: str) -> Optional[Path]:
    """在模型目录的 *_transcripts/ 下找 <task_id>.jsonl。"""
    for d in model_dir.iterdir():
        if d.is_dir() and d.name.endswith("_transcripts"):
            cand = d / f"{task_id}.jsonl"
            if cand.exists():
                return cand
    return None


def _model_dir_map(inputs: List[Path], models: List[ModelResult]) -> Dict[str, Path]:
    """模型 model 字段 → 其目录路径。"""
    dirs = discover_model_dirs(inputs)
    # 目录与 models 顺序一致（collect_all 同序）
    return {m.model: d for m, d in zip(models, dirs)}


def _model_summary(m: ModelResult) -> Dict:
    return {
        "model": m.model,
        "display_name": m.display_name,
        "suite": m.suite,
        "benchmark_version": m.benchmark_version,
        "score_rate": sc.overall_score_rate(m),
        "high_task_count": sc.count_high_tasks(m),
        "low_task_count": sc.count_low_tasks(m),
        "total_tokens": m.total_tokens,
        "total_requests": m.total_requests,
        "token_efficiency": sc.token_efficiency(m),
        "category_scores": sc.category_scores(m),
        "task_count": m.task_count,
    }


def _task_matrix(models: List[ModelResult]) -> List[Dict]:
    """对齐任务矩阵：每任务一行，含各模型得分/breakdown/notes。"""
    all_ids = []
    seen = set()
    for m in models:
        for t in m.tasks:
            if t.task_id not in seen:
                seen.add(t.task_id)
                all_ids.append((t.task_id, t.category))
    rows = []
    for tid, cat in all_ids:
        per_model = {}
        for m in models:
            t = next((x for x in m.tasks if x.task_id == tid), None)
            if t:
                per_model[m.model] = {
                    "score": t.score, "breakdown": t.breakdown,
                    "notes": t.notes, "total_tokens": t.total_tokens,
                    "request_count": t.request_count,
                    "timed_out": t.timed_out,
                }
        rows.append({"task_id": tid, "category": cat, "per_model": per_model})
    return rows


def build_collected_data(
    inputs: List[Path],
    target_model: str,
    tasks_root: Path,
    thresholds: Optional[FilterThresholds] = None,
) -> Dict:
    """构建阶段2 输入数据结构。"""
    models = collect_all(inputs)
    if not models:
        raise ValueError("未发现任何模型目录")

    # 若 target_model 未在结果中，默认取第一个
    if not any(m.model == target_model for m in models):
        target_model = models[0].model

    dir_map = _model_dir_map(inputs, models)
    picked = filter_tasks_to_analyze(models, target_model, thresholds)

    # 高分对比模型（用于对比 transcript）
    target = next(m for m in models if m.model == target_model)
    others = [m for m in models if m.model != target_model]

    tasks_to_analyze = []
    for p in picked:
        tid = p["task_id"]
        target_dir = dir_map[target_model]
        t_path = resolve_transcript_path(target_dir, tid)
        # 选得分最高的对比模型 transcript
        best_other = None
        if others:
            best = max(others,
                       key=lambda m: next((t.score for t in m.tasks if t.task_id == tid), 0.0))
            bo_path = resolve_transcript_path(dir_map[best.model], tid)
            if bo_path:
                best_other = {"model": best.model, "transcript": str(bo_path)}
        tasks_to_analyze.append({
            "task_id": tid,
            "reason": p["reason"],
            "target_transcript": str(t_path) if t_path else None,
            "best_other_transcript": best_other,
            "task_md": str(tasks_root / f"{tid}.md"),
        })

    return {
        "target_model": target_model,
        "is_single_model": len(models) == 1,
        "models": [_model_summary(m) for m in sc.rank_models(models)],
        "category_summary": sc.build_category_summary(models),
        "task_matrix": _task_matrix(models),
        "tasks_to_analyze": tasks_to_analyze,
    }
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd skill && python -m pytest skills/pinchbench-report-generator/test_collect.py -v`
Expected: PASS（2 passed）

- [ ] **Step 5: 提交**

```bash
cd skill && git add skills/pinchbench-report-generator/collect.py skills/pinchbench-report-generator/test_collect.py
git commit -m "feat(report-gen): add collect orchestration and data assembly"
```

## Task 6: 报告渲染器 - 表格渲染（report_renderer.py 第一部分）

**Files:**
- Create: `skills/pinchbench-report-generator/report_renderer.py`
- Test: `skills/pinchbench-report-generator/test_report_renderer.py`

先实现 Python 负责的纯数据表格（整体排名、分类别、各任务得分、Token），不依赖 LLM 分析。`analysis.json` 缺失时这些章节仍能渲染。

- [ ] **Step 1: 写失败测试**

```python
"""报告渲染测试。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from report_renderer import (
    render_ranking_table, render_category_table,
    render_token_table, fmt_pct,
)


def _collected():
    return {
        "target_model": "xspark",
        "is_single_model": False,
        "models": [
            {"model": "ds", "display_name": "DeepSeek", "score_rate": 0.972,
             "high_task_count": 16, "low_task_count": 0, "total_tokens": 3215180,
             "total_requests": 113, "token_efficiency": 3.02e-7,
             "category_scores": {"coding": 1.0, "research": 0.988}, "task_count": 21},
            {"model": "xspark", "display_name": "Spark", "score_rate": 0.833,
             "high_task_count": 10, "low_task_count": 3, "total_tokens": 7525595,
             "total_requests": 203, "token_efficiency": 1.11e-7,
             "category_scores": {"coding": 1.0, "research": 0.468}, "task_count": 21},
        ],
        "category_summary": [
            {"category": "coding", "scores": {"ds": 1.0, "xspark": 1.0}, "best_model": "ds"},
            {"category": "research", "scores": {"ds": 0.988, "xspark": 0.468}, "best_model": "ds"},
        ],
    }


def test_fmt_pct():
    assert fmt_pct(0.972) == "97.2%"
    assert fmt_pct(1.0) == "100%"


def test_render_ranking_table():
    out = render_ranking_table(_collected())
    assert "| 排名 | 模型 | 得分率 |" in out
    assert "DeepSeek" in out and "97.2%" in out
    assert "Spark" in out and "83.3%" in out
    # DeepSeek 排第一
    lines = [l for l in out.splitlines() if l.startswith("| 1 ")]
    assert "DeepSeek" in lines[0]


def test_render_category_table():
    out = render_category_table(_collected())
    assert "research" in out
    assert "46.8%" in out  # spark research
    assert "100%" in out   # coding


def test_render_token_table():
    out = render_token_table(_collected())
    assert "总Token" in out
    assert "7,525,595" in out  # spark tokens 带千分位
    assert "203" in out
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd skill && python -m pytest skills/pinchbench-report-generator/test_report_renderer.py -v`
Expected: FAIL（No module named 'report_renderer'）

- [ ] **Step 3: 实现 report_renderer.py 表格部分**

```python
"""阶段3：报告渲染。Python 负责所有数据表格，LLM 分析文字插入对应位置。"""
from typing import Dict, List


def fmt_pct(x: float) -> str:
    """0.972 → '97.2%'，整数省略小数。"""
    pct = x * 100
    if abs(pct - round(pct)) < 1e-9:
        return f"{int(round(pct))}%"
    return f"{pct:.1f}%"


def fmt_int(n: int) -> str:
    """带千分位。"""
    return f"{n:,}"


def _display(models: List[Dict], model_key: str) -> str:
    for m in models:
        if m["model"] == model_key:
            return m["display_name"]
    return model_key


def render_ranking_table(data: Dict) -> str:
    """一、整体排名。models 已按得分降序。"""
    models = data["models"]
    lines = [
        "| 排名 | 模型 | 得分率 | ≥95%任务数 | <60%任务数 |",
        "|------|------|--------|-----------|-----------|",
    ]
    for i, m in enumerate(models, 1):
        lines.append(
            f"| {i} | {m['display_name']} | **{fmt_pct(m['score_rate'])}** "
            f"| {m['high_task_count']}/{m['task_count']} | {m['low_task_count']} |"
        )
    return "\n".join(lines)


def render_category_table(data: Dict) -> str:
    """三、分类别得分对比。"""
    models = data["models"]
    header = "| 类别 | " + " | ".join(_display(models, m["model"]) for m in models) + " | 最优模型 |"
    sep = "|------|" + "|".join([":---:"] * len(models)) + "|------|"
    lines = [header, sep]
    for row in data["category_summary"]:
        cells = []
        for m in models:
            score = row["scores"].get(m["model"], 0.0)
            cells.append(fmt_pct(score))
        best = _display(models, row["best_model"])
        lines.append(f"| {row['category']} | " + " | ".join(cells) + f" | {best} |")
    return "\n".join(lines)


def render_token_table(data: Dict) -> str:
    """六、Token消耗与效率对比。"""
    models = data["models"]
    names = [_display(models, m["model"]) for m in models]
    header = "| 指标 | " + " | ".join(names) + " |"
    sep = "|------|" + "|".join([":---:"] * len(models)) + "|"
    rows = [header, sep]
    rows.append("| 总Token | " + " | ".join(fmt_int(m["total_tokens"]) for m in models) + " |")
    rows.append("| 总请求数 | " + " | ".join(str(m["total_requests"]) for m in models) + " |")
    rows.append("| 得分率 | " + " | ".join(fmt_pct(m["score_rate"]) for m in models) + " |")
    return "\n".join(rows)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd skill && python -m pytest skills/pinchbench-report-generator/test_report_renderer.py -v`
Expected: PASS（4 passed）

- [ ] **Step 5: 提交**

```bash
cd skill && git add skills/pinchbench-report-generator/report_renderer.py skills/pinchbench-report-generator/test_report_renderer.py
git commit -m "feat(report-gen): add table rendering"
```

## Task 7: 报告渲染器 - 任务详情表、深度分析章节与文档组装

**Files:**
- Modify: `skills/pinchbench-report-generator/report_renderer.py`
- Modify: `skills/pinchbench-report-generator/test_report_renderer.py`

加入各任务详细得分表、目标模型深度分析章节（消费 analysis.json）、以及整篇文档的单/多模型自适应组装。

- [ ] **Step 1: 追加失败测试到 test_report_renderer.py**

```python
# ---- 追加到 test_report_renderer.py 末尾 ----
from report_renderer import (
    render_task_detail_table, render_deep_analysis,
    render_report, build_filename,
)


def _collected_with_matrix():
    d = _collected()
    d["task_matrix"] = [
        {"task_id": "task_stock", "category": "research", "per_model": {
            "ds": {"score": 1.0, "notes": "ok", "breakdown": {}},
            "xspark": {"score": 0.0, "notes": "all tools failed", "breakdown": {}},
        }},
    ]
    return d


def _analysis():
    return {
        "task_analysis": [{
            "task_id": "task_stock",
            "filter_reason": "relative_weakness",
            "grading_criteria_cn": "需联网获取股价并写入文件",
            "target_model_breakdown": {
                "notes": "所有联网工具失败", "transcript_summary": "54次工具调用直至超时"},
            "comparison_models": [{"model": "ds", "score": 1.0, "why_succeeded": "用知识库回退"}],
            "root_cause": "缺乏联网失败回退策略",
        }],
        "target_model_weaknesses": [{
            "theme": "联网搜索失败后缺乏回退策略",
            "related_tasks": ["task_stock"],
            "evidence": "54次工具调用耗尽超时",
            "comparison": "其他模型基于知识库给出近似答案",
            "token_data": {"target": 7525595, "others_avg": 3200000},
        }],
        "improvement_suggestions": [
            {"priority": "P0", "direction": "联网失败回退", "expected_gain": "+4.8%",
             "explanation": "失败后用知识库近似答案"},
        ],
        "capability_mapping": {"task_stock": ["信息检索与综合", "自我纠错与反思"]},
    }


def test_render_task_detail_table():
    out = render_task_detail_table(_collected_with_matrix(), _analysis())
    assert "task_stock" in out
    assert "research" in out


def test_render_deep_analysis():
    out = render_deep_analysis(_collected_with_matrix(), _analysis())
    assert "联网搜索失败后缺乏回退策略" in out
    assert "需联网获取股价并写入文件" in out      # 中文评分标准
    assert "54次工具调用" in out                  # transcript 摘要
    assert "缺乏联网失败回退策略" in out          # 根本原因


def test_render_report_multi_model():
    out = render_report(_collected_with_matrix(), _analysis())
    assert "一、整体排名" in out
    assert "六、Token消耗与效率对比" in out
    assert "改进建议" in out


def test_render_report_single_model():
    d = _collected_with_matrix()
    d["is_single_model"] = True
    d["models"] = [d["models"][1]]  # 仅 spark
    out = render_report(d, _analysis())
    assert "一、整体排名" not in out          # 单模型跳过排名
    assert "六、Token消耗与效率对比" not in out
    assert "深度分析" in out                   # 仍有深度分析


def test_build_filename():
    assert build_filename(_collected_with_matrix()) == "comparison_2_models_report.md"
    single = _collected_with_matrix()
    single["is_single_model"] = True
    single["models"] = [single["models"][1]]
    assert build_filename(single) == "xspark_evaluation_report.md"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd skill && python -m pytest skills/pinchbench-report-generator/test_report_renderer.py -v`
Expected: FAIL（ImportError: cannot import name 'render_task_detail_table'）

- [ ] **Step 3: 追加实现到 report_renderer.py**

```python
# ---- 追加到 report_renderer.py 末尾 ----

def render_task_detail_table(data: Dict, analysis: Dict) -> str:
    """四、各任务详细得分。失分点优先用 LLM 分析，回退到 notes。"""
    models = data["models"]
    matrix = data.get("task_matrix", [])
    analysis_by_id = {a["task_id"]: a for a in analysis.get("task_analysis", [])}

    header = "| 任务 | 类别 | " + " | ".join(_display(models, m["model"]) for m in models) + " | 失分点分析 |"
    sep = "|------|------|" + "|".join([":---:"] * len(models)) + "|------|"
    lines = [header, sep]
    for row in matrix:
        tid = row["task_id"]
        cells = []
        for m in models:
            pm = row["per_model"].get(m["model"])
            cells.append(f"{pm['score']:.3g}" if pm else "N/A")
        a = analysis_by_id.get(tid)
        note = a["root_cause"] if a else _short_note(row, models)
        lines.append(f"| {tid} | {row['category']} | " + " | ".join(cells) + f" | {note} |")
    return "\n".join(lines)


def _short_note(row: Dict, models: List[Dict]) -> str:
    """从最低分模型的 notes 提取简短失分说明。"""
    items = [(k, v) for k, v in row["per_model"].items()]
    if not items:
        return "—"
    low = min(items, key=lambda kv: kv[1]["score"])
    note = (low[1].get("notes") or "").strip().replace("\n", " ")
    return note[:80] if note else "—"


def render_deep_analysis(data: Dict, analysis: Dict) -> str:
    """五、目标模型短板深度分析。"""
    target = data["target_model"]
    target_name = _display(data["models"], target)
    title = (f"## 五、{target_name} 短板深度分析"
             if not data["is_single_model"]
             else f"## 五、{target_name} 失分任务深度分析")
    parts = [title, ""]

    weaknesses = analysis.get("target_model_weaknesses", [])
    analysis_by_id = {a["task_id"]: a for a in analysis.get("task_analysis", [])}

    for i, w in enumerate(weaknesses, 1):
        parts.append(f"### 5.{i} {w['theme']}")
        parts.append("")
        parts.append(f"**相关任务**: {', '.join(w.get('related_tasks', []))}")
        parts.append("")
        # 每个相关任务的评分标准 + 失分明细 + 根本原因
        for tid in w.get("related_tasks", []):
            a = analysis_by_id.get(tid)
            if not a:
                continue
            parts.append(f"**任务 {tid} 评分标准（中文）**:")
            parts.append("")
            parts.append(a.get("grading_criteria_cn", ""))
            parts.append("")
            tb = a.get("target_model_breakdown", {})
            parts.append(f"**失分明细**: {tb.get('notes', '')}")
            parts.append("")
            parts.append(f"**过程分析**: {tb.get('transcript_summary', '')}")
            parts.append("")
            comps = a.get("comparison_models", [])
            if comps:
                comp_str = "；".join(
                    f"{c['model']}({c['score']:.3g})：{c['why_succeeded']}" for c in comps)
                parts.append(f"**对比模型表现**: {comp_str}")
                parts.append("")
            parts.append(f"**根本原因**: {a.get('root_cause', '')}")
            parts.append("")
        parts.append(f"**证据**: {w.get('evidence', '')}")
        parts.append("")
    return "\n".join(parts)


def render_improvements(analysis: Dict) -> str:
    """改进建议表（八、最终总结的一部分）。"""
    suggestions = analysis.get("improvement_suggestions", [])
    if not suggestions:
        return ""
    lines = ["| 优先级 | 改进方向 | 预期收益 | 说明 |",
             "|--------|---------|---------|------|"]
    for s in suggestions:
        lines.append(f"| {s['priority']} | {s['direction']} "
                     f"| {s['expected_gain']} | {s['explanation']} |")
    return "\n".join(lines)


def render_report(data: Dict, analysis: Dict) -> str:
    """组装完整报告，单/多模型自适应。"""
    models = data["models"]
    is_single = data["is_single_model"]
    suite = models[0].get("suite", "unknown") if models else "unknown"

    if is_single:
        title = f"# {_display(models, data['target_model'])} PinchBench 评测报告"
    else:
        title = f"# PinchBench {suite} suite {len(models)}模型评测对比报告"

    parts = [title, "", f"> 评测框架：PinchBench {suite} suite | 目标模型：{data['target_model']}", ""]

    if not is_single:
        parts += ["## 一、整体排名", "", render_ranking_table(data), ""]

    parts += ["## 三、分类别得分对比", "", render_category_table(data), ""]
    parts += ["## 四、各任务详细得分", "", render_task_detail_table(data, analysis), ""]
    parts += [render_deep_analysis(data, analysis), ""]

    if not is_single:
        parts += ["## 六、Token消耗与效率对比", "", render_token_table(data), ""]

    imp = render_improvements(analysis)
    if imp:
        parts += ["## 八、最终总结与改进建议", "", imp, ""]

    return "\n".join(parts)


def build_filename(data: Dict) -> str:
    """输出文件名：多模型 comparison_N_models_report.md / 单模型 <target>_evaluation_report.md。"""
    if data["is_single_model"]:
        return f"{data['target_model']}_evaluation_report.md"
    return f"comparison_{len(data['models'])}_models_report.md"
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd skill && python -m pytest skills/pinchbench-report-generator/test_report_renderer.py -v`
Expected: PASS（10 passed，含 Task 6 的 4 个）

- [ ] **Step 5: 提交**

```bash
cd skill && git add skills/pinchbench-report-generator/report_renderer.py skills/pinchbench-report-generator/test_report_renderer.py
git commit -m "feat(report-gen): add deep analysis sections and report assembly"
```

## Task 8: Agent能力对比表与分项排名（report_renderer.py 第三部分）

**Files:**
- Modify: `skills/pinchbench-report-generator/report_renderer.py`
- Modify: `skills/pinchbench-report-generator/test_report_renderer.py`

补齐 spec 第六节模板的"二、Agent核心能力对比"（按 LLM `capability_mapping` 把任务聚到能力维度，算各模型在该组任务的均分）和"七、分项排名"（综合 + 各类别第一名汇总），并接入 `render_report`。

- [ ] **Step 1: 追加失败测试到 test_report_renderer.py**

```python
# ---- 追加到 test_report_renderer.py 末尾 ----
from report_renderer import render_capability_table, render_subrankings


def test_render_capability_table():
    out = render_capability_table(_collected_with_matrix(), _analysis())
    assert "信息检索与综合" in out      # 来自 capability_mapping
    assert "task_stock" in out


def test_render_capability_table_empty_mapping():
    out = render_capability_table(_collected_with_matrix(), {"capability_mapping": {}})
    assert out == ""                      # 无归类返回空，render_report 跳过


def test_render_subrankings():
    out = render_subrankings(_collected_with_matrix())
    assert "综合得分率" in out
    assert "DeepSeek" in out               # 综合第一


def test_render_report_includes_capability_and_subrank():
    out = render_report(_collected_with_matrix(), _analysis())
    assert "二、Agent核心能力对比" in out
    assert "七、分项排名" in out
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd skill && python -m pytest skills/pinchbench-report-generator/test_report_renderer.py -k "capability or subranking or capability_and" -v`
Expected: FAIL（ImportError: cannot import name 'render_capability_table'）

- [ ] **Step 3: 追加实现到 report_renderer.py**

```python
# ---- 追加到 report_renderer.py 末尾 ----
from collections import defaultdict
from statistics import mean


def render_capability_table(data: Dict, analysis: Dict) -> str:
    """二、Agent核心能力对比。按 capability_mapping 把任务聚到能力维度。"""
    mapping = analysis.get("capability_mapping", {})
    if not mapping:
        return ""
    models = data["models"]
    matrix = {row["task_id"]: row for row in data.get("task_matrix", [])}

    cap_tasks = defaultdict(list)
    for tid, caps in mapping.items():
        for c in caps:
            cap_tasks[c].append(tid)

    header = ("| 考察点 | 对应任务 | "
              + " | ".join(_display(models, m["model"]) for m in models) + " |")
    sep = "|--------|---------|" + "|".join([":---:"] * len(models)) + "|"
    lines = [header, sep]
    for cap in sorted(cap_tasks):
        tids = cap_tasks[cap]
        cells = []
        for m in models:
            scores = []
            for tid in tids:
                pm = matrix.get(tid, {}).get("per_model", {}).get(m["model"])
                if pm:
                    scores.append(pm["score"])
            cells.append(fmt_pct(mean(scores)) if scores else "N/A")
        lines.append(f"| {cap} | {', '.join(tids)} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def render_subrankings(data: Dict) -> str:
    """七、分项排名。综合得分率 + 各类别第一名。"""
    models = data["models"]  # 已按总分降序
    lines = ["| 排名维度 | 第1名 | 第2名 |", "|---------|-------|-------|"]
    top2 = [_display(models, m["model"]) for m in models[:2]]
    while len(top2) < 2:
        top2.append("-")
    lines.append(f"| 综合得分率 | {top2[0]} | {top2[1]} |")
    for row in data.get("category_summary", []):
        best = _display(models, row["best_model"])
        lines.append(f"| {row['category']} | {best} | - |")
    return "\n".join(lines)
```

- [ ] **Step 4: 接入 render_report**

在 `render_report` 中找到：

```python
    if not is_single:
        parts += ["## 一、整体排名", "", render_ranking_table(data), ""]

    parts += ["## 三、分类别得分对比", "", render_category_table(data), ""]
```

替换为：

```python
    if not is_single:
        parts += ["## 一、整体排名", "", render_ranking_table(data), ""]
        cap = render_capability_table(data, analysis)
        if cap:
            parts += ["## 二、Agent核心能力对比", "", cap, ""]

    parts += ["## 三、分类别得分对比", "", render_category_table(data), ""]
```

再找到：

```python
    if not is_single:
        parts += ["## 六、Token消耗与效率对比", "", render_token_table(data), ""]
```

替换为：

```python
    if not is_single:
        parts += ["## 六、Token消耗与效率对比", "", render_token_table(data), ""]
        parts += ["## 七、分项排名", "", render_subrankings(data), ""]
```

- [ ] **Step 5: 运行全部渲染测试确认通过**

Run: `cd skill && python -m pytest skills/pinchbench-report-generator/test_report_renderer.py -v`
Expected: PASS（14 passed）

- [ ] **Step 6: 提交**

```bash
cd skill && git add skills/pinchbench-report-generator/report_renderer.py skills/pinchbench-report-generator/test_report_renderer.py
git commit -m "feat(report-gen): add capability comparison and subrankings sections"
```

## Task 9: CLI 入口（report_cli.py）

**Files:**
- Create: `skills/pinchbench-report-generator/report_cli.py`
- Test: `skills/pinchbench-report-generator/test_report_cli.py`

提供 `collect`（产出 collected_data.json）和 `render`（读 collected_data.json + analysis.json → md）两个子命令。阶段2 LLM 分析由上层 Skill agent 完成，不在 CLI。

- [ ] **Step 1: 写失败测试**

```python
"""CLI 测试。"""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from report_cli import cmd_collect, cmd_render


def _make_model_dir(base, name, model_field, tasks):
    d = base / name
    d.mkdir(parents=True)
    td = d / "0001_transcripts"
    td.mkdir()
    for t in tasks:
        (td / f"{t['task_id']}.jsonl").write_text('{"type":"session"}\n')
    payload = {"model": model_field, "benchmark_version": "2.0.0",
               "run_id": "0001", "suite": "all", "tasks": tasks}
    (d / f"0001_{name}.json").write_text(json.dumps(payload))
    return d


def _task(tid, cat, score):
    return {"task_id": tid, "status": "success", "timed_out": False,
            "execution_time": 1.0,
            "usage": {"input_tokens": 90, "output_tokens": 10,
                      "total_tokens": 100, "request_count": 1},
            "grading": {"mean": score, "runs": [
                {"breakdown": {"automated.x": score}, "notes": "n"}]},
            "frontmatter": {"category": cat, "grading_weights": {}}}


def test_cmd_collect(tmp_path):
    _make_model_dir(tmp_path, "spark", "xsparkx2flash",
                    [_task("task_stock", "research", 0.0)])
    _make_model_dir(tmp_path, "ds", "xopdeepseek",
                    [_task("task_stock", "research", 1.0)])
    out = tmp_path / "collected.json"
    cmd_collect(inputs=[str(tmp_path)], target_model="xsparkx2flash",
                tasks_root=str(tmp_path / "tasks"), output=str(out))
    assert out.exists()
    data = json.loads(out.read_text())
    assert data["target_model"] == "xsparkx2flash"


def test_cmd_render(tmp_path):
    collected = {
        "target_model": "xspark", "is_single_model": True,
        "models": [{"model": "xspark", "display_name": "Spark", "suite": "all",
                    "score_rate": 0.5, "high_task_count": 0, "low_task_count": 1,
                    "total_tokens": 100, "total_requests": 1, "token_efficiency": 0.005,
                    "category_scores": {"research": 0.5}, "task_count": 1}],
        "category_summary": [{"category": "research", "scores": {"xspark": 0.5},
                              "best_model": "xspark"}],
        "task_matrix": [{"task_id": "task_stock", "category": "research",
                         "per_model": {"xspark": {"score": 0.5, "notes": "n", "breakdown": {}}}}],
        "tasks_to_analyze": [],
    }
    analysis = {"task_analysis": [], "target_model_weaknesses": [],
                "improvement_suggestions": [], "capability_mapping": {}}
    cpath = tmp_path / "collected.json"
    apath = tmp_path / "analysis.json"
    cpath.write_text(json.dumps(collected))
    apath.write_text(json.dumps(analysis))
    out = tmp_path / "report.md"
    cmd_render(collected_data=str(cpath), analysis=str(apath), output=str(out))
    assert out.exists()
    assert "评测报告" in out.read_text()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd skill && python -m pytest skills/pinchbench-report-generator/test_report_cli.py -v`
Expected: FAIL（No module named 'report_cli'）

- [ ] **Step 3: 实现 report_cli.py**

```python
"""CLI 入口：collect / render 子命令。"""
import argparse
import json
from pathlib import Path
from typing import List, Optional

from collect import build_collected_data
from task_filter import FilterThresholds
from report_renderer import render_report, build_filename


def _parse_thresholds(s: Optional[str]) -> Optional[FilterThresholds]:
    """解析 'all_low=0.4,gap=0.2' 形式的阈值覆盖。"""
    if not s:
        return None
    th = FilterThresholds()
    mapping = {
        "relative_weakness_min_others": "relative_weakness_min_others",
        "min_others": "relative_weakness_min_others",
        "gap": "relative_weakness_gap",
        "all_low": "all_low",
        "absolute": "absolute_low",
    }
    for pair in s.split(","):
        k, _, v = pair.partition("=")
        attr = mapping.get(k.strip())
        if attr:
            setattr(th, attr, float(v))
    return th


def cmd_collect(inputs: List[str], target_model: str, tasks_root: str,
                output: str, thresholds: Optional[str] = None):
    """阶段1：收集数据写 collected_data.json。"""
    data = build_collected_data(
        [Path(p) for p in inputs], target_model, Path(tasks_root),
        _parse_thresholds(thresholds))
    Path(output).write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"collected_data 已写入: {output}")
    print(f"待深度分析任务数: {len(data['tasks_to_analyze'])}")


def cmd_render(collected_data: str, analysis: str, output: str):
    """阶段3：读 collected_data + analysis 渲染报告。"""
    data = json.loads(Path(collected_data).read_text())
    ana = json.loads(Path(analysis).read_text()) if Path(analysis).exists() else {}
    md = render_report(data, ana)
    out_path = Path(output)
    if out_path.is_dir():
        out_path = out_path / build_filename(data)
    out_path.write_text(md)
    print(f"报告已写入: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="PinchBench 评测报告生成器")
    sub = parser.add_subparsers(dest="command", required=True)

    pc = sub.add_parser("collect", help="阶段1：收集数据")
    pc.add_argument("inputs", nargs="+", help="评测结果目录（总目录或多个模型目录）")
    pc.add_argument("--target-model", default="xsparkx2flash")
    pc.add_argument("--tasks-root", default="tasks", help="任务 md 根目录")
    pc.add_argument("--output", default="collected_data.json")
    pc.add_argument("--thresholds", default=None, help="如 all_low=0.4,gap=0.2")

    pr = sub.add_parser("render", help="阶段3：渲染报告")
    pr.add_argument("--collected-data", required=True)
    pr.add_argument("--analysis", required=True)
    pr.add_argument("--output", required=True, help="输出文件或目录")

    args = parser.parse_args()
    if args.command == "collect":
        cmd_collect(args.inputs, args.target_model, args.tasks_root,
                    args.output, args.thresholds)
    elif args.command == "render":
        cmd_render(args.collected_data, args.analysis, args.output)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd skill && python -m pytest skills/pinchbench-report-generator/test_report_cli.py -v`
Expected: PASS（2 passed）

- [ ] **Step 5: 真实数据端到端冒烟（collect 阶段）**

Run: `cd skill && python skills/pinchbench-report-generator/report_cli.py collect ../astronclaw-result/all-suite/round-2 --target-model xsparkx2flash --tasks-root tasks --output /tmp/collected_smoke.json`
Expected: 打印"待深度分析任务数: N"（N>0），文件生成

- [ ] **Step 6: 提交**

```bash
cd skill && git add skills/pinchbench-report-generator/report_cli.py skills/pinchbench-report-generator/test_report_cli.py
git commit -m "feat(report-gen): add CLI with collect and render subcommands"
```

## Task 10: 能力维度静态资源与 SKILL.md（含阶段2 LLM 指引）

**Files:**
- Create: `skills/pinchbench-report-generator/agent-capability-dimensions.md`（复制）
- Create: `skills/pinchbench-report-generator/SKILL.md`

- [ ] **Step 1: 复制能力维度文档到 Skill**

```bash
cd skill && cp docs/agent-capability-dimensions.md skills/pinchbench-report-generator/agent-capability-dimensions.md
```

- [ ] **Step 2: 验证复制成功**

Run: `cd skill && head -5 skills/pinchbench-report-generator/agent-capability-dimensions.md`
Expected: 输出"# Agent 能力维度与子能力定义"

- [ ] **Step 3: 编写 SKILL.md**

写入以下内容（路径 `skills/pinchbench-report-generator/SKILL.md`）：

````markdown
---
name: pinchbench-report-generator
description: 分析 PinchBench 多模型评测结果，生成结构化对比报告。Use when 需要将一次或多次 PinchBench 评测的执行结果（含 transcripts）整理成评测报告、对比多个模型的得分与能力、或对某个目标模型做失分点深度分析时。读取评测结果目录，产出 Markdown 对比报告。
metadata:
  version: "1.0.0"
  author: astronclaw
---

# PinchBench 评测报告生成器

三阶段流水线：Python 收集统计 → LLM 深度分析 → Python 渲染报告。Python 保证数字准确，LLM 负责失分点语义分析。

## 何时使用

- PinchBench 在一个或多个模型上执行完毕，需生成评测对比报告
- 需要对某个目标模型（默认 xsparkx2flash）做详尽的优劣势分析
- 输入可以是总目录（自动发现所有模型）或多个具体模型目录

## 前置条件

- 已有 PinchBench 评测结果目录，每个模型目录含结果 JSON + `*_transcripts/`

## 三阶段工作流

### 阶段1：收集数据（Python）

```bash
python skills/pinchbench-report-generator/report_cli.py collect \
  <result_dir...> \
  --target-model xsparkx2flash \
  --tasks-root tasks \
  --output collected_data.json \
  [--thresholds all_low=0.4,gap=0.2,min_others=0.8,absolute=0.8]
```

产出 `collected_data.json`，含模型统计、任务矩阵、分类别汇总、`tasks_to_analyze`（待深度分析任务及其 transcript/任务md 路径与入选原因）。

### 阶段2：深度分析（LLM，由你执行）

读取 `collected_data.json` 后，对 `tasks_to_analyze` 中的每个任务：

1. 读 `target_transcript`（目标模型过程），必要时读 `best_other_transcript`（高分对比模型）做对照
2. 读 `task_md`（任务定义），提取 **Grading Criteria / Automated Checks / LLM Judge Rubric**，翻译成中文
3. 参考本目录 `agent-capability-dimensions.md`（20 个能力维度），为任务做能力归类
4. 结合 breakdown + notes + transcript 行为，分析目标模型失分点与对比模型为何得分

按入选原因区分分析角度：
- `relative_weakness`：目标模型独有短板，重点对比目标 vs 对比模型的行为差异
- `all_low`：全员低分，重点分析任务本身难度或环境问题
- `absolute_low`：单模型场景的绝对低分

产出 `analysis.json`，结构：

```json
{
  "capability_mapping": {"<task_id>": ["能力维度名", ...]},
  "task_analysis": [{
    "task_id": "...", "filter_reason": "relative_weakness|all_low|absolute_low",
    "grading_criteria_cn": "评分标准中文翻译",
    "target_model_breakdown": {"notes": "...", "transcript_summary": "关键行为摘要"},
    "comparison_models": [{"model": "...", "score": 1.0, "why_succeeded": "..."}],
    "root_cause": "根本原因"
  }],
  "target_model_weaknesses": [{
    "theme": "短板主题", "related_tasks": ["..."],
    "evidence": "证据", "comparison": "对比模型表现",
    "token_data": {"target": 0, "others_avg": 0}
  }],
  "improvement_suggestions": [{
    "priority": "P0|P1|P2", "direction": "...",
    "expected_gain": "+X.X%", "explanation": "..."
  }]
}
```

**Context 控制**：阶段1 已筛掉高分任务。transcript 大时只读关键片段（toolCall/toolResult/thinking），提取工具调用次数、失败模式、token 消耗，不全量灌入。

### 阶段3：渲染报告（Python）

```bash
python skills/pinchbench-report-generator/report_cli.py render \
  --collected-data collected_data.json \
  --analysis analysis.json \
  --output <result_dir 或 具体md路径>
```

`--output` 传目录时，文件名自适应：多模型 `comparison_<N>_models_report.md`，单模型 `<target>_evaluation_report.md`。

## 报告结构

参考 `astronclaw-result/core-suite/round-2/comparison_four_models_report.md`：
整体排名 → 分类别得分 → 各任务详细得分 → 目标模型短板深度分析 → Token效率 → 改进建议。单模型时跳过排名/Token对比章节。

## 设计说明

- Python 算所有表格数字，LLM 只产出分析文字章节，避免 LLM 拼表格算错
- `agent-capability-dimensions.md` 为 Skill 内置副本，不依赖外部 docs/ 路径
````

- [ ] **Step 4: 提交**

```bash
cd skill && git add skills/pinchbench-report-generator/agent-capability-dimensions.md skills/pinchbench-report-generator/SKILL.md
git commit -m "feat(report-gen): add capability dimensions resource and SKILL.md"
```

---

## Task 11: 集成测试（真实数据 + mock LLM 分析）

**Files:**
- Create: `skills/pinchbench-report-generator/test_integration.py`

用真实结果目录跑 collect → 构造 mock analysis → render，验证全链路与报告结构。

- [ ] **Step 1: 写集成测试**

```python
"""端到端集成测试：真实数据 collect + mock analysis + render。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from collect import build_collected_data
from report_renderer import render_report, build_filename

REAL_DIR = Path(__file__).resolve().parents[3] / "astronclaw-result" / "all-suite" / "round-2"
TASKS_ROOT = Path(__file__).resolve().parents[2] / "tasks"


@pytest.mark.skipif(not REAL_DIR.exists(), reason="真实评测数据不存在")
def test_full_pipeline_real_data():
    data = build_collected_data([REAL_DIR], target_model="xsparkx2flash",
                                tasks_root=TASKS_ROOT)
    # 至少识别到多个模型
    assert len(data["models"]) >= 2
    assert data["is_single_model"] is False
    # 目标模型存在
    assert any(m["model"] == data["target_model"] for m in data["models"])
    # 有待分析任务
    assert len(data["tasks_to_analyze"]) > 0
    # 每个待分析任务的 target_transcript 路径有效
    for a in data["tasks_to_analyze"]:
        if a["target_transcript"]:
            assert Path(a["target_transcript"]).exists()

    # mock 空 analysis 仍能渲染（表格部分）
    empty_analysis = {"task_analysis": [], "target_model_weaknesses": [],
                      "improvement_suggestions": [], "capability_mapping": {}}
    md = render_report(data, empty_analysis)
    assert "## 一、整体排名" in md
    assert "## 三、分类别得分对比" in md
    assert "## 四、各任务详细得分" in md
    assert build_filename(data).endswith("_models_report.md")
```

- [ ] **Step 2: 运行集成测试**

Run: `cd skill && python -m pytest skills/pinchbench-report-generator/test_integration.py -v`
Expected: PASS（1 passed；若真实数据缺失则 skipped）

- [ ] **Step 3: 运行全部测试确认无回归**

Run: `cd skill && python -m pytest skills/pinchbench-report-generator/ -v`
Expected: 所有测试 PASS

- [ ] **Step 4: 提交**

```bash
cd skill && git add skills/pinchbench-report-generator/test_integration.py
git commit -m "test(report-gen): add end-to-end integration test"
```

---

## 验收清单

完成全部任务后，应满足设计文档的所有要求：

- [ ] 三阶段流水线可独立运行（collect / LLM analyze / render）
- [ ] 模型目录按内容识别（*.json + *_transcripts/），展示名取 JSON model 字段
- [ ] 总目录自动发现 + 多目录显式指定均支持
- [ ] 低分任务筛选：相对短板（0.8/0.2）+ 全员低分（0.4）+ 单模型绝对回退（0.8），阈值可覆盖
- [ ] 单/多模型报告自适应（单模型跳过排名/Token对比章节）
- [ ] 目标模型深度分析含：评分标准中文、失分明细、transcript摘要、对比模型表现、根本原因
- [ ] 输出路径默认输入目录 + --output 可覆盖；文件名自适应
- [ ] agent-capability-dimensions.md 复制为 Skill 内置资源
- [ ] 所有单测 + 集成测试通过
