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


_CN_DIGITS = "零一二三四五六七八九"


def _cn_num(n: int) -> str:
    """阿拉伯数字转中文章节序号（1→一，10→十，12→十二）。仅支持 1-99，够用。"""
    if n < 10:
        return _CN_DIGITS[n]
    tens, ones = divmod(n, 10)
    head = ("" if tens == 1 else _CN_DIGITS[tens]) + "十"
    return head + (_CN_DIGITS[ones] if ones else "")


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


def render_deep_analysis(data: Dict, analysis: Dict, section_no: int, mode: str = "weakness") -> str:
    """目标模型深度分析章节。mode='weakness' 短板 / 'strength' 优势。

    两种模式共用 task_analysis（按 filter_reason 区分），主题列表分别取
    target_model_weaknesses / target_model_strengths，字段措辞按 mode 切换。
    """
    target = data["target_model"]
    target_name = _display(data["models"], target)
    cn = _cn_num(section_no)

    if mode == "strength":
        title = (f"## {cn}、{target_name} 优势深度分析"
                 if not data["is_single_model"]
                 else f"## {cn}、{target_name} 高分任务深度分析")
        themes = analysis.get("target_model_strengths", [])
        labels = {"detail": "得分亮点", "comp": "对比模型差距", "cause": "制胜原因"}
    else:
        title = (f"## {cn}、{target_name} 短板深度分析"
                 if not data["is_single_model"]
                 else f"## {cn}、{target_name} 失分任务深度分析")
        themes = analysis.get("target_model_weaknesses", [])
        labels = {"detail": "失分明细", "comp": "对比模型表现", "cause": "根本原因"}

    parts = [title, ""]
    analysis_by_id = {a["task_id"]: a for a in analysis.get("task_analysis", [])}

    for i, w in enumerate(themes, 1):
        parts.append(f"### {section_no}.{i} {w['theme']}")
        parts.append("")
        parts.append(f"**相关任务**: {', '.join(w.get('related_tasks', []))}")
        parts.append("")
        # 每个相关任务的评分标准 + 明细 + 原因
        for tid in w.get("related_tasks", []):
            a = analysis_by_id.get(tid)
            if not a:
                continue
            parts.append(f"**任务 {tid} 评分标准（中文）**:")
            parts.append("")
            parts.append(a.get("grading_criteria_cn", ""))
            parts.append("")
            tb = a.get("target_model_breakdown", {})
            parts.append(f"**{labels['detail']}**: {tb.get('notes', '')}")
            parts.append("")
            parts.append(f"**过程分析**: {tb.get('transcript_summary', '')}")
            parts.append("")
            comps = a.get("comparison_models", [])
            if comps:
                comp_str = "；".join(
                    f"{c['model']}({c['score']:.3g})：{c['why_succeeded']}" for c in comps)
                parts.append(f"**{labels['comp']}**: {comp_str}")
                parts.append("")
            parts.append(f"**{labels['cause']}**: {a.get('root_cause', '')}")
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
    """组装完整报告，单/多模型自适应。章节号按实际出现的章节动态生成。"""
    models = data["models"]
    is_single = data["is_single_model"]
    suite = models[0].get("suite", "unknown") if models else "unknown"

    if is_single:
        title = f"# {_display(models, data['target_model'])} PinchBench 评测报告"
    else:
        title = f"# PinchBench {suite} suite {len(models)}模型评测对比报告"

    parts = [title, "", f"> 评测框架：PinchBench {suite} suite | 目标模型：{data['target_model']}", ""]

    sec = 0  # 动态章节计数器

    def add_section(heading: str, body: str):
        nonlocal sec
        sec += 1
        parts.extend([f"## {_cn_num(sec)}、{heading}", "", body, ""])

    if not is_single:
        add_section("整体排名", render_ranking_table(data))
        cap = render_capability_table(data, analysis)
        if cap:
            add_section("Agent核心能力对比", cap)

    # 难度等级维度分析（多模型放在排名/能力对比之后；单模型放在最前的数据章节）
    if data.get("difficulty_summary"):
        sec += 1
        diff_md = render_difficulty_section(data, analysis, sec)
        if diff_md:
            parts.append(diff_md)
            parts.append("")
        else:
            sec -= 1  # 渲染为空（极端情况），让出该编号

    add_section("分类别得分对比", render_category_table(data))
    add_section("各任务详细得分", render_task_detail_table(data, analysis))

    # 优势深度分析（仅当 LLM 产出了 strengths 时出现，标题号已含在内）
    if analysis.get("target_model_strengths"):
        sec += 1
        parts.append(render_deep_analysis(data, analysis, sec, mode="strength").rstrip("\n"))
        parts.append("")

    # 短板深度分析
    sec += 1
    parts.append(render_deep_analysis(data, analysis, sec, mode="weakness").rstrip("\n"))
    parts.append("")

    if not is_single:
        add_section("Token消耗与效率对比", render_token_table(data))
        add_section("分项排名", render_subrankings(data))

    imp = render_improvements(analysis)
    if imp:
        add_section("最终总结与改进建议", imp)

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


# ---- 难度等级维度章节（3.1 - 3.5） ----

# 难度分级标准（量化参考与典型场景）；与 task md 的 difficulty 字段对应
_DIFFICULTY_STANDARD = [
    ("L1", "单步执行，单工具调用", "1-3 步，1 个工具", "文件读取、简单查询、单文件生成"),
    ("L2", "多步推理，工具组合", "4-10 步，2-3 个工具", "数据分析、日志提取、多文件操作"),
    ("L3", "复杂规划，跨领域", "10-30 步，多工具链", "代码重构、深度研究、跨文件一致性"),
    ("L4", "长程任务，跨系统/多Agent", "30+ 步，跨会话", "端到端项目、多Agent协作"),
]


def render_difficulty_standard(data: Dict, section_no: int) -> str:
    """{section_no}.1 难度分级标准 + 实际数据中的难度分布。"""
    rows = data.get("difficulty_summary", [])
    lines = [
        f"### {section_no}.1 难度分级标准",
        "",
        "PinchBench 采用 L1-L4 四级难度体系，综合评估任务的**预估执行步数**与"
        "**预估涉及工具数**，取两者较高者对应的等级：",
        "",
        "| 等级 | 定义 | 量化参考 | 典型场景 |",
        "|------|------|----------|----------|",
    ]
    for lvl, defn, scale, scenes in _DIFFICULTY_STANDARD:
        lines.append(f"| **{lvl}** | {defn} | {scale} | {scenes} |")
    if rows:
        dist = "，".join(
            f"**{r['difficulty']}×{r['task_count']}**" for r in rows
            if r["difficulty"] != "unknown"
        )
        if dist:
            lines.append("")
            lines.append(f"本次评测难度分布：{dist}。")
        unknown = next((r for r in rows if r["difficulty"] == "unknown"), None)
        if unknown:
            lines.append(
                f"\n> 注：另有 {unknown['task_count']} 个任务未配置 difficulty 字段，"
                f"在难度对比表中以 unknown 行展示。")
    return "\n".join(lines)


def render_difficulty_compare_table(data: Dict, section_no: int) -> str:
    """{section_no}.2 各模型按难度等级的得分率对比表。"""
    rows = data.get("difficulty_summary", [])
    if not rows:
        return ""
    models = data["models"]
    header = ("| 难度 | 任务数 | "
              + " | ".join(_display(models, m["model"]) for m in models)
              + " | 得分率极差 |")
    sep = "|:----:|:------:|" + "|".join([":---:"] * len(models)) + "|:----------:|"
    lines = [f"### {section_no}.2 各模型按难度等级的得分率对比", "", header, sep]

    for r in rows:
        d = r["difficulty"]
        # 找到该难度下得分最高者，对应单元格加粗
        max_score = max(r["scores"].values()) if r["scores"] else 0.0
        cells = []
        for m in models:
            s = r["scores"].get(m["model"], 0.0)
            tot = r["totals"].get(m["model"], 0.0)
            txt = f"{fmt_pct(s)} ({tot:.2f}/{r['task_count']})"
            cells.append(f"**{txt}**" if s == max_score and r["task_count"] > 0 else txt)
        rng = fmt_pct(r["score_range"])
        # 极差较大时(>=0.2)加粗，提醒区分度
        rng_disp = f"**{rng}**" if r["score_range"] >= 0.2 else rng
        lines.append(f"| **{d}** | {r['task_count']} | " + " | ".join(cells)
                     + f" | {rng_disp} |")
    return "\n".join(lines)


def render_difficulty_top_detail(data: Dict, section_no: int) -> str:
    """{section_no}.3 最高难度等级的逐项任务得分明细。"""
    rows = data.get("difficulty_summary", [])
    if not rows:
        return ""
    from score_calculator import highest_difficulty
    top = highest_difficulty(rows)
    if not top:
        return ""

    matrix = data.get("task_matrix", [])
    top_tasks = [row for row in matrix if row.get("difficulty") == top]
    if not top_tasks:
        return ""

    models = data["models"]
    header = ("| 任务 | 类别 | "
              + " | ".join(_display(models, m["model"]) for m in models) + " |")
    sep = "|------|------|" + "|".join([":---:"] * len(models)) + "|"
    lines = [f"### {section_no}.3 {top} 任务逐项得分明细（{len(top_tasks)} 个任务）",
             "", header, sep]
    for row in top_tasks:
        # 行内最高分加粗，便于读者一眼识别该任务的最优模型
        scores = [row["per_model"].get(m["model"], {}).get("score", 0.0)
                  for m in models]
        mx = max(scores) if scores else 0.0
        cells = []
        for s in scores:
            cells.append(f"**{fmt_pct(s)}**" if s == mx and mx > 0 else fmt_pct(s))
        lines.append(f"| {row['task_id']} | {row['category']} | "
                     + " | ".join(cells) + " |")
    return "\n".join(lines)


def render_difficulty_section(data: Dict, analysis: Dict, section_no: int) -> str:
    """难度等级维度分析章节。

    Python 渲染 N.1/N.2/N.3 数据章节；N.4 典型失分点 / N.5 结论与建议
    取自 analysis.difficulty_analysis（LLM 产出），缺省时跳过。
    """
    rows = data.get("difficulty_summary", [])
    if not rows:
        return ""
    # 多模型才有对比意义；单模型时只展示标准 + 自身按难度得分
    if data.get("is_single_model"):
        # 单模型场景：仍保留章节，但只渲染标准与各等级自身得分
        cn = _cn_num(section_no)
        parts = [f"## {cn}、难度等级维度分析", ""]
        parts.append(render_difficulty_standard(data, section_no))
        parts.append("")
        cmp_table = render_difficulty_compare_table(data, section_no)
        if cmp_table:
            parts.append(cmp_table)
            parts.append("")
        return "\n".join(parts).rstrip("\n")

    cn = _cn_num(section_no)
    parts = [f"## {cn}、难度等级维度分析", ""]

    parts.append(render_difficulty_standard(data, section_no))
    parts.append("")

    cmp_table = render_difficulty_compare_table(data, section_no)
    if cmp_table:
        parts.append(cmp_table)
        parts.append("")

    da = analysis.get("difficulty_analysis", {}) if analysis else {}

    # N.2 章节核心发现（LLM 产出，紧跟对比表）
    findings = da.get("compare_findings", "")
    if findings:
        parts.append("**核心发现**：")
        parts.append("")
        parts.append(findings)
        parts.append("")

    detail = render_difficulty_top_detail(data, section_no)
    if detail:
        parts.append(detail)
        parts.append("")
        # N.3 章节分析（LLM 产出，紧跟逐项明细）
        top_analysis = da.get("top_difficulty_analysis", "")
        if top_analysis:
            parts.append("**分析**：")
            parts.append("")
            parts.append(top_analysis)
            parts.append("")

    # N.4 L1/L2 典型失分点（LLM 产出）
    low_loss = da.get("lower_difficulty_loss_points", "")
    if low_loss:
        parts.append(f"### {section_no}.4 低难度任务典型失分点")
        parts.append("")
        parts.append(low_loss)
        parts.append("")

    # N.5 结论与建议（LLM 产出）
    conclusion = da.get("conclusion", "")
    if conclusion:
        parts.append(f"### {section_no}.5 难度维度结论与建议")
        parts.append("")
        parts.append(conclusion)
        parts.append("")

    return "\n".join(parts).rstrip("\n")
