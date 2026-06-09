#!/usr/bin/env python3
"""PinchBench 评测结果分析脚本，输出 Excel 报告。

支持两种模式：
1. 单文件模式（-i）：分析单个评测结果 JSON，输出「概览 + 明细」两个 Sheet。
2. 目录模式（-d）：递归扫描目录下所有 `0xxx_<modelid>.json` 格式的结果文件，
   汇总输出「对比 + 明细」两个 Sheet。
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
except ImportError:
    sys.exit("需要 openpyxl 库，请执行: pip install openpyxl")


# 形如 0004_xopdeepseekv4pro.json：0 开头 + 下划线 + 模型 id + .json
RESULT_FILE_PATTERN = re.compile(r"^0\w*_.+\.json$")

HEADER_FONT_WHITE = Font(bold=True, color="FFFFFF")
HEADER_FILL = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
CENTER = Alignment(horizontal="center")


def find_latest_result(results_dir: Path) -> Path:
    json_files = sorted(results_dir.glob("*.json"), key=lambda f: f.stat().st_mtime)
    if not json_files:
        sys.exit(f"未找到结果文件: {results_dir}")
    return json_files[-1]


def find_result_files(root: Path) -> list[Path]:
    """递归查找目录下所有符合命名规则的结果文件。"""
    return sorted(
        p for p in root.rglob("*.json") if RESULT_FILE_PATTERN.match(p.name)
    )


# 历史评测 JSON 没有 scene/sub_scene/difficulty/capabilities 字段，
# 需要从当前 tasks/*.md 的 frontmatter 实时补齐。下面是支撑函数。
_TASKS_DIR_CACHE: list[Path | None] = [None]   # 项目 tasks 目录(单值缓存)
_FM_CACHE: dict[str, dict] = {}                 # task_id -> frontmatter 缓存


def _find_tasks_dir(start: Path | None = None) -> Path | None:
    """向上查找 PinchBench 项目根的 tasks/ 目录。

    项目根标志：同时存在 scripts/lib_grading.py 与 tasks/ 目录
    （与 assemble.py 的 find_project_root 一致）。

    Returns:
        tasks 目录 Path，找不到则 None（聚合时优雅降级）
    """
    if _TASKS_DIR_CACHE[0] is not None:
        return _TASKS_DIR_CACHE[0]
    cur = (start or Path(__file__).resolve()).resolve()
    for cand in [cur, *cur.parents]:
        if (cand / "scripts" / "lib_grading.py").exists() and (cand / "tasks").is_dir():
            _TASKS_DIR_CACHE[0] = cand / "tasks"
            return _TASKS_DIR_CACHE[0]
    return None


def _read_task_frontmatter(task_id: str) -> dict:
    """从 tasks/{task_id}.md 读取 frontmatter (仅 YAML 头)，结果缓存。"""
    if task_id in _FM_CACHE:
        return _FM_CACHE[task_id]
    tasks_dir = _find_tasks_dir()
    fm: dict = {}
    if tasks_dir is not None:
        f = tasks_dir / f"{task_id}.md"
        if f.exists():
            try:
                import yaml
                text = f.read_text(encoding="utf-8")
                m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
                if m:
                    parsed = yaml.safe_load(m.group(1))
                    if isinstance(parsed, dict):
                        fm = parsed
            except Exception:
                fm = {}
    _FM_CACHE[task_id] = fm
    return fm


_NEW_FIELDS = ("scene", "sub_scene", "difficulty", "capabilities")


def enrich_tasks_from_frontmatter(tasks: list[dict]) -> list[dict]:
    """对历史评测 JSON 兼容：当 task.frontmatter 缺新字段时，从 tasks/*.md 补齐。

    策略：**只补缺失，不覆盖已有**。这样：
    - 历史 JSON（缺新字段）→ 从 tasks/ 补齐，可参与新维度统计
    - 新评测 JSON（已含新字段）→ 保持原样，不被当前 tasks/ 改写
    - tasks/ 找不到对应文件 → 字段保持缺失，聚合时归入 UNKNOWN（不崩溃）

    in-place 修改并返回 tasks。
    """
    for task in tasks:
        fm = task.get("frontmatter")
        if not isinstance(fm, dict):
            fm = {}
            task["frontmatter"] = fm
        # 全部 4 个新字段都已存在 → 跳过文件读取
        if all(fm.get(k) for k in _NEW_FIELDS):
            continue
        tid = task.get("task_id")
        if not tid:
            continue
        latest_fm = _read_task_frontmatter(tid)
        for k in _NEW_FIELDS:
            if not fm.get(k) and latest_fm.get(k):
                fm[k] = latest_fm[k]
    return tasks


def load_result(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def style_header_row(ws, row: int, ncols: int):
    for col_idx in range(1, ncols + 1):
        cell = ws.cell(row=row, column=col_idx)
        cell.font = HEADER_FONT_WHITE
        cell.fill = HEADER_FILL
        cell.alignment = CENTER


# 难度等级展示顺序（L1→L4，未知值排末尾）
_DIFFICULTY_ORDER = ["L1", "L2", "L3", "L4"]


def compute_difficulty_scores(tasks: list[dict]) -> dict:
    """按 difficulty 维度聚合得分。

    口径与 benchmark.py 的 _compute_category_scores 一致：
    每个 task 满分 1.0，得分取 grading.mean，按 difficulty 分组累加。
    difficulty 从 task 的 frontmatter 读取（结果 JSON 已完整保留 frontmatter）。

    Args:
        tasks: 结果 JSON 中的 data["tasks"] 列表

    Returns:
        {difficulty: {score, max_score, pct, task_count}}，按 L1→L4 排序
    """
    raw: dict[str, dict] = {}
    for task in tasks:
        fm = task.get("frontmatter", {}) or {}
        difficulty = fm.get("difficulty") or "UNKNOWN"
        mean_score = float(task.get("grading", {}).get("mean", 0.0))
        max_score = 1.0  # 与 category 口径一致：每个 task 满分 1.0

        if difficulty not in raw:
            raw[difficulty] = {"score": 0.0, "max_score": 0.0, "task_count": 0}
        raw[difficulty]["score"] += mean_score
        raw[difficulty]["max_score"] += max_score
        raw[difficulty]["task_count"] += 1

    # 排序：已知等级按 L1→L4，其余（如 UNKNOWN）按字母序追加在后
    ordered_keys = [d for d in _DIFFICULTY_ORDER if d in raw]
    ordered_keys += sorted(k for k in raw if k not in ordered_keys)

    result: dict[str, dict] = {}
    for d in ordered_keys:
        v = raw[d]
        pct = (v["score"] / v["max_score"] * 100) if v["max_score"] > 0 else 0
        result[d] = {
            "score": round(v["score"], 6),
            "max_score": round(v["max_score"], 6),
            "pct": round(pct, 1),
            "task_count": int(v["task_count"]),
        }
    return result


# 8 大场景展示顺序
_SCENE_ORDER = [
    "finance_investment_research", "deep_research_report", "science_tech_medical_qa",
    "data_retrieval_analysis", "content_creation_multimedia", "enterprise_product_intel",
    "skill_lifecycle", "local_env_scripting",
]

# 20 个标准能力标签（与 agent-capability-dimensions.md 一致）
_CAPABILITY_TAGS = [
    "instruction_following", "context_memory", "output_format", "hallucination_resistance",
    "tool_usage", "multimodal_perception", "data_extraction", "information_retrieval",
    "multi_step_reasoning", "planning", "domain_reasoning", "code_generation",
    "service_integration", "text_generation", "self_correction", "uncertainty_handling",
    "safety_awareness", "concurrency_management", "multi_agent", "adaptive_learning",
]


def compute_scene_scores(tasks: list[dict]) -> dict:
    """按 scene 维度聚合得分。

    口径与 difficulty/category 一致：每 task 满分 1.0，得分取 grading.mean。
    scene 从 task 的 frontmatter 读取。

    Returns:
        {scene: {score, max_score, pct, task_count}}，按 _SCENE_ORDER 排序
    """
    raw: dict[str, dict] = {}
    for task in tasks:
        fm = task.get("frontmatter", {}) or {}
        scene = fm.get("scene") or "UNKNOWN"
        mean_score = float(task.get("grading", {}).get("mean", 0.0))
        if scene not in raw:
            raw[scene] = {"score": 0.0, "max_score": 0.0, "task_count": 0}
        raw[scene]["score"] += mean_score
        raw[scene]["max_score"] += 1.0
        raw[scene]["task_count"] += 1

    ordered = [s for s in _SCENE_ORDER if s in raw]
    ordered += sorted(k for k in raw if k not in ordered)
    result: dict[str, dict] = {}
    for s in ordered:
        v = raw[s]
        pct = (v["score"] / v["max_score"] * 100) if v["max_score"] > 0 else 0
        result[s] = {
            "score": round(v["score"], 6),
            "max_score": round(v["max_score"], 6),
            "pct": round(pct, 1),
            "task_count": int(v["task_count"]),
        }
    return result


def compute_capability_scores(tasks: list[dict]) -> dict:
    """按 capabilities 维度聚合得分（多标签：每任务得分贡献到其所有 capabilities）。

    口径：每 task 满分 1.0，得分取 grading.mean。
    一个 task 标了 N 个 capabilities，则该任务对每个 capability 都贡献 1 次（score=mean，max=1）。
    所以一个 capability 的 task_count 表示"涉及该能力的任务数"，得分率为这些任务的均值。

    Returns:
        {capability: {score, max_score, pct, task_count}}，按 20 标准标签顺序排序
    """
    raw: dict[str, dict] = {}
    for task in tasks:
        fm = task.get("frontmatter", {}) or {}
        caps = fm.get("capabilities") or []
        if not isinstance(caps, list):
            continue
        mean_score = float(task.get("grading", {}).get("mean", 0.0))
        for cap in caps:
            if cap not in raw:
                raw[cap] = {"score": 0.0, "max_score": 0.0, "task_count": 0}
            raw[cap]["score"] += mean_score
            raw[cap]["max_score"] += 1.0
            raw[cap]["task_count"] += 1

    # 按 20 标准标签顺序输出，未标准标签排末尾
    ordered = [c for c in _CAPABILITY_TAGS if c in raw]
    ordered += sorted(k for k in raw if k not in ordered)
    result: dict[str, dict] = {}
    for c in ordered:
        v = raw[c]
        pct = (v["score"] / v["max_score"] * 100) if v["max_score"] > 0 else 0
        result[c] = {
            "score": round(v["score"], 6),
            "max_score": round(v["max_score"], 6),
            "pct": round(pct, 1),
            "task_count": int(v["task_count"]),
        }
    return result


# --------------------------------------------------------------------------- #
# 单文件模式
# --------------------------------------------------------------------------- #
def write_overview_sheet(wb: openpyxl.Workbook, data: dict):
    ws = wb.active
    ws.title = "概览"

    category_scores = data["category_scores"]
    total_score = sum(v["score"] for v in category_scores.values())
    total_max = sum(v["max_score"] for v in category_scores.values())
    overall_pct = (total_score / total_max * 100) if total_max > 0 else 0

    ws.append(["总分", f"{overall_pct:.1f}%", f"({total_score:.1f} / {total_max:.1f})"])
    ws["A1"].font = Font(bold=True)
    ws.append([])

    headers = ["类别", "得分", "满分", "得分率", "任务数"]
    ws.append(headers)
    style_header_row(ws, 3, len(headers))

    for category, scores in category_scores.items():
        ws.append([
            category,
            round(scores["score"], 3),
            round(scores["max_score"], 1),
            f"{scores['pct']:.1f}%",
            scores["task_count"],
        ])

    for col in range(1, 6):
        ws.column_dimensions[get_column_letter(col)].width = 16

    # 难度等级分布（从 tasks 的 frontmatter 聚合，与 category 同口径）
    difficulty_scores = compute_difficulty_scores(data.get("tasks", []))
    if difficulty_scores:
        ws.append([])
        title_row = ws.max_row + 1
        ws.append(["难度等级维度"])
        ws.cell(row=title_row, column=1).font = Font(bold=True)

        diff_header_row = ws.max_row + 1
        ws.append(["难度", "得分", "满分", "得分率", "任务数"])
        style_header_row(ws, diff_header_row, 5)

        for level, scores in difficulty_scores.items():
            ws.append([
                level,
                round(scores["score"], 3),
                round(scores["max_score"], 1),
                f"{scores['pct']:.1f}%",
                scores["task_count"],
            ])

    # 场景维度分布
    scene_scores = compute_scene_scores(data.get("tasks", []))
    if scene_scores:
        ws.append([])
        title_row = ws.max_row + 1
        ws.append(["场景维度"])
        ws.cell(row=title_row, column=1).font = Font(bold=True)

        scene_header_row = ws.max_row + 1
        ws.append(["场景", "得分", "满分", "得分率", "任务数"])
        style_header_row(ws, scene_header_row, 5)

        for scene, scores in scene_scores.items():
            ws.append([
                scene,
                round(scores["score"], 3),
                round(scores["max_score"], 1),
                f"{scores['pct']:.1f}%",
                scores["task_count"],
            ])

    # 能力维度分布（多标签：每任务贡献到所有 capabilities）
    cap_scores = compute_capability_scores(data.get("tasks", []))
    if cap_scores:
        ws.append([])
        title_row = ws.max_row + 1
        ws.append(["能力维度（capabilities，多标签聚合）"])
        ws.cell(row=title_row, column=1).font = Font(bold=True)

        cap_header_row = ws.max_row + 1
        ws.append(["能力维度", "得分", "满分", "得分率", "涉及任务数"])
        style_header_row(ws, cap_header_row, 5)

        for cap, scores in cap_scores.items():
            ws.append([
                cap,
                round(scores["score"], 3),
                round(scores["max_score"], 1),
                f"{scores['pct']:.1f}%",
                scores["task_count"],
            ])


def write_detail_sheet(wb: openpyxl.Workbook, data: dict):
    ws = wb.create_sheet("明细")

    headers = [
        "category", "scene", "sub_scene", "difficulty", "task", "score",
        "capabilities",
        "input_tokens", "output_tokens",
        "cache_read_tokens", "cache_write_tokens",
        "total_tokens", "request_count",
    ]
    ws.append(headers)
    style_header_row(ws, 1, len(headers))

    for task in data["tasks"]:
        usage = task.get("usage", {})
        fm = task.get("frontmatter", {}) or {}
        caps = fm.get("capabilities") or []
        caps_str = "\n".join(caps) if isinstance(caps, list) else str(caps)
        ws.append([
            task.get("category", ""),
            fm.get("scene", ""),
            fm.get("sub_scene", ""),
            fm.get("difficulty", ""),
            task.get("task_id", ""),
            task.get("grading", {}).get("mean", 0),
            caps_str,
            usage.get("input_tokens", 0),
            usage.get("output_tokens", 0),
            usage.get("cache_read_tokens", 0),
            usage.get("cache_write_tokens", 0),
            usage.get("total_tokens", 0),
            usage.get("request_count", 0),
        ])

    for col in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col)].width = 18
    # capabilities 列加宽并启用换行
    ws.column_dimensions[get_column_letter(7)].width = 24
    for row_idx in range(2, ws.max_row + 1):
        ws.cell(row=row_idx, column=7).alignment = Alignment(wrap_text=True, vertical="top")


def build_single_report(data: dict) -> openpyxl.Workbook:
    # 历史 JSON 缺新字段 → 从当前 tasks/*.md 补齐 (不覆盖已有)
    enrich_tasks_from_frontmatter(data.get("tasks", []))
    wb = openpyxl.Workbook()
    write_overview_sheet(wb, data)
    write_detail_sheet(wb, data)
    return wb


# --------------------------------------------------------------------------- #
# 目录模式
# --------------------------------------------------------------------------- #
def fmt_timestamp(ts) -> str:
    try:
        return datetime.fromtimestamp(float(ts)).strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError, OSError):
        return ""


def write_compare_sheet(wb, results: list[tuple[Path, Path, dict]], categories: list[str]):
    """对比 Sheet：每个文件一行，含模型/suite/总分率/各类别得分率/总 tokens 等。"""
    ws = wb.active
    ws.title = "对比"

    headers = ["文件", "模型", "suite", "run_id", "总分率", "总分/满分", "任务数"]
    headers += categories
    headers += [f"难度{d}" for d in _DIFFICULTY_ORDER]
    headers += [f"场景:{s}" for s in _SCENE_ORDER]
    headers += ["total_tokens", "total_requests", "总耗时(s)", "时间"]
    ws.append(headers)
    style_header_row(ws, 1, len(headers))

    for rel_path, _abs_path, data in results:
        cat_scores = data.get("category_scores", {})
        total_score = sum(v["score"] for v in cat_scores.values())
        total_max = sum(v["max_score"] for v in cat_scores.values())
        overall_pct = (total_score / total_max * 100) if total_max > 0 else 0
        task_count = sum(v.get("task_count", 0) for v in cat_scores.values())

        eff = data.get("efficiency", {})

        row = [
            str(rel_path),
            data.get("model", ""),
            data.get("suite", ""),
            data.get("run_id", ""),
            f"{overall_pct:.1f}%",
            f"{total_score:.2f} / {total_max:.1f}",
            task_count,
        ]
        for cat in categories:
            if cat in cat_scores:
                row.append(f"{cat_scores[cat]['pct']:.1f}%")
            else:
                row.append("-")
        # 难度维度得分率（从该结果文件的 tasks 聚合）
        diff_scores = compute_difficulty_scores(data.get("tasks", []))
        for level in _DIFFICULTY_ORDER:
            if level in diff_scores:
                row.append(f"{diff_scores[level]['pct']:.1f}%")
            else:
                row.append("-")
        # 场景维度得分率
        scene_scores = compute_scene_scores(data.get("tasks", []))
        for scene in _SCENE_ORDER:
            if scene in scene_scores:
                row.append(f"{scene_scores[scene]['pct']:.1f}%")
            else:
                row.append("-")
        row += [
            eff.get("total_tokens", ""),
            eff.get("total_requests", ""),
            eff.get("total_execution_time_seconds", ""),
            fmt_timestamp(data.get("timestamp")),
        ]
        ws.append(row)

    # 列宽：文件列宽一些，其余适中
    ws.column_dimensions["A"].width = 50
    for col in range(2, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col)].width = 16
    ws.freeze_panes = "B2"


def write_capability_compare_sheet(wb, results: list[tuple[Path, Path, dict]]):
    """能力维度对比 Sheet：每个模型一行，列出 20 个能力维度的得分率。"""
    ws = wb.create_sheet("能力维度对比")

    headers = ["文件", "模型", "suite", "run_id"]
    headers += _CAPABILITY_TAGS
    ws.append(headers)
    style_header_row(ws, 1, len(headers))

    for rel_path, _abs_path, data in results:
        cap_scores = compute_capability_scores(data.get("tasks", []))
        row = [
            str(rel_path),
            data.get("model", ""),
            data.get("suite", ""),
            data.get("run_id", ""),
        ]
        for cap in _CAPABILITY_TAGS:
            if cap in cap_scores:
                # 显示 得分率 (涉及任务数)
                pct = cap_scores[cap]["pct"]
                cnt = cap_scores[cap]["task_count"]
                row.append(f"{pct:.1f}% ({cnt})")
            else:
                row.append("-")
        ws.append(row)

    ws.column_dimensions["A"].width = 50
    ws.column_dimensions["B"].width = 20
    for col in range(3, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col)].width = 18
    ws.freeze_panes = "E2"


def write_all_detail_sheet(wb, results: list[tuple[Path, Path, dict]]):
    """全量明细 Sheet：所有文件的任务展平，前置 model/run_id/文件 列。"""
    ws = wb.create_sheet("明细")

    headers = [
        "model", "run_id", "suite", "category", "scene", "sub_scene",
        "difficulty", "task", "score", "capabilities",
        "input_tokens", "output_tokens",
        "cache_read_tokens", "cache_write_tokens",
        "total_tokens", "request_count", "文件",
    ]
    ws.append(headers)
    style_header_row(ws, 1, len(headers))

    for rel_path, _abs_path, data in results:
        model = data.get("model", "")
        run_id = data.get("run_id", "")
        suite = data.get("suite", "")
        for task in data.get("tasks", []):
            usage = task.get("usage", {})
            fm = task.get("frontmatter", {}) or {}
            caps = fm.get("capabilities") or []
            caps_str = "\n".join(caps) if isinstance(caps, list) else str(caps)
            ws.append([
                model,
                run_id,
                suite,
                task.get("category", ""),
                fm.get("scene", ""),
                fm.get("sub_scene", ""),
                fm.get("difficulty", ""),
                task.get("task_id", ""),
                task.get("grading", {}).get("mean", 0),
                caps_str,
                usage.get("input_tokens", 0),
                usage.get("output_tokens", 0),
                usage.get("cache_read_tokens", 0),
                usage.get("cache_write_tokens", 0),
                usage.get("total_tokens", 0),
                usage.get("request_count", 0),
                str(rel_path),
            ])

    for col in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col)].width = 16
    # capabilities 列加宽并启用换行
    cap_col = headers.index("capabilities") + 1
    ws.column_dimensions[get_column_letter(cap_col)].width = 24
    for row_idx in range(2, ws.max_row + 1):
        ws.cell(row=row_idx, column=cap_col).alignment = Alignment(wrap_text=True, vertical="top")
    ws.column_dimensions[get_column_letter(len(headers))].width = 50
    ws.freeze_panes = "A2"


def build_dir_report(results: list[tuple[Path, Path, dict]]) -> openpyxl.Workbook:
    # 历史 JSON 缺新字段 → 从当前 tasks/*.md 补齐 (不覆盖已有, 全局缓存仅读一次)
    for _rel, _abs, data in results:
        enrich_tasks_from_frontmatter(data.get("tasks", []))

    # 收集所有出现过的类别，保持稳定顺序（按首次出现）
    categories: list[str] = []
    for _rel, _abs, data in results:
        for cat in data.get("category_scores", {}):
            if cat not in categories:
                categories.append(cat)

    wb = openpyxl.Workbook()
    write_compare_sheet(wb, results, categories)
    write_capability_compare_sheet(wb, results)
    write_all_detail_sheet(wb, results)
    return wb


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #
def run_single(input_path: Path, output_dir: Path):
    if not input_path.exists():
        sys.exit(f"文件不存在: {input_path}")

    data = load_result(input_path)
    wb = build_single_report(data)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"analysis_{input_path.stem}_{timestamp}.xlsx"
    wb.save(output_path)
    print(f"分析完成: {output_path}")


def run_dir(dir_paths: list[Path], output_dir: Path):
    all_files = []
    for dir_path in dir_paths:
        if not dir_path.exists():
            print(f"警告：目录不存在，跳过: {dir_path}", file=sys.stderr)
            continue
        if not dir_path.is_dir():
            print(f"警告：不是目录，跳过: {dir_path}", file=sys.stderr)
            continue
        files = find_result_files(dir_path)
        if not files:
            print(f"警告：未找到符合命名规则的文件: {dir_path}", file=sys.stderr)
            continue
        print(f"在 {dir_path} 下找到 {len(files)} 个待分析文件:")
        for path in files:
            print(f"  - {path}")
        all_files.extend(files)

    if not all_files:
        sys.exit("所有目录下均未找到符合命名规则（0xxx_<模型id>.json）的结果文件")

    # 去重（可能多个目录有重复文件）
    all_files = sorted(set(all_files))
    print(f"\n合并后共 {len(all_files)} 个文件待分析\n")

    results: list[tuple[Path, Path, dict]] = []
    # 使用第一个有效目录作为相对路径基准；若需展示绝对路径，可改为直接用 path
    base_dir = dir_paths[0] if len(dir_paths) == 1 else None

    for path in all_files:
        try:
            data = load_result(path)
        except (json.JSONDecodeError, OSError) as e:
            print(f"跳过（解析失败）: {path} -> {e}", file=sys.stderr)
            continue
        # 尝试相对路径，失败则用绝对路径
        if base_dir:
            try:
                rel = path.relative_to(base_dir)
            except ValueError:
                rel = path
        else:
            rel = path
        results.append((rel, path, data))

    if not results:
        sys.exit("没有可解析的结果文件")

    wb = build_dir_report(results)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # 多目录时用 "multi"，单目录时用目录名
    dir_name = dir_paths[0].name if len(dir_paths) == 1 else "multi"
    output_path = output_dir / f"analysis_dir_{dir_name}_{timestamp}.xlsx"
    wb.save(output_path)
    print(f"分析完成（共 {len(results)} 个文件）: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="PinchBench 评测结果分析")
    parser.add_argument("-i", "--input", type=str, default=None, help="输入的评测结果 JSON 文件路径")
    parser.add_argument(
        "-d", "--dir", type=str, nargs='+', default=None,
        help="递归扫描一个或多个目录下所有 0xxx_<模型id>.json 文件，汇总分析",
    )
    parser.add_argument("-o", "--output-dir", type=str, default=None, help="输出目录，默认为 ./output")
    args = parser.parse_args()

    if args.input and args.dir:
        sys.exit("-i 与 -d 不能同时使用")

    output_dir = Path(args.output_dir) if args.output_dir else Path.cwd() / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.dir:
        run_dir([Path(d) for d in args.dir], output_dir)
        return

    results_dir = Path(__file__).resolve().parent.parent / "results"
    input_path = Path(args.input) if args.input else find_latest_result(results_dir)
    run_single(input_path, output_dir)


if __name__ == "__main__":
    main()
