"""阶段3：报告渲染。Python 负责所有数据表格，LLM 分析文字插入对应位置。"""
from collections import defaultdict
from statistics import mean
from typing import Dict, List


def fmt_pct(x: float) -> str:
    """0.972 → '97.2%'，整数省略小数。"""
    pct = round(x * 100, 1)
    if pct == round(pct):
        return f"{int(pct)}%"
    return f"{pct:.1f}%"


def fmt_int(n: int) -> str:
    """带千分位。"""
    return f"{n:,}"


def _display(models: List[Dict], model_key: str) -> str:
    for m in models:
        if m["model"] == model_key:
            return m["display_name"]
    return model_key


def _sanitize_cell(s: str) -> str:
    """转义表格单元格中的竖线，避免破坏 Markdown 表格列结构。"""
    return str(s).replace("|", "｜")


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
        lines.append(f"| {tid} | {row['category']} | " + " | ".join(cells) + f" | {_sanitize_cell(note)} |")
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
        lines.append(f"| {_sanitize_cell(s['priority'])} | {_sanitize_cell(s['direction'])} "
                     f"| {_sanitize_cell(s['expected_gain'])} | {_sanitize_cell(s['explanation'])} |")
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
        cap = render_capability_table(data, analysis)
        if cap:
            parts += ["## 二、Agent核心能力对比", "", cap, ""]

    parts += ["## 三、分类别得分对比", "", render_category_table(data), ""]
    parts += ["## 四、各任务详细得分", "", render_task_detail_table(data, analysis), ""]
    parts += [render_deep_analysis(data, analysis).rstrip("\n"), ""]

    if not is_single:
        parts += ["## 六、Token消耗与效率对比", "", render_token_table(data), ""]
        parts += ["## 七、分项排名", "", render_subrankings(data), ""]

    imp = render_improvements(analysis)
    if imp:
        parts += ["## 八、最终总结与改进建议", "", imp, ""]

    return "\n".join(parts)


def build_filename(data: Dict) -> str:
    """输出文件名：多模型 comparison_N_models_report.md / 单模型 <target>_evaluation_report.md。"""
    if data["is_single_model"]:
        return f"{data['target_model']}_evaluation_report.md"
    return f"comparison_{len(data['models'])}_models_report.md"


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
        lines.append(f"| {_sanitize_cell(cap)} | {_sanitize_cell(', '.join(tids))} | " + " | ".join(cells) + " |")
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
        lines.append(f"| {_sanitize_cell(row['category'])} | {best} | - |")
    return "\n".join(lines)
