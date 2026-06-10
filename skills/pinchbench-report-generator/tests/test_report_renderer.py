"""报告渲染测试。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

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


def test_fmt_pct_edge_cases():
    assert fmt_pct(0.9999) == "100%"  # 边界：不输出 100.0%
    assert fmt_pct(0.995) == "99.5%"
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


# ---- 追加到 test_report_renderer.py 末尾 ----
from report_renderer import (
    render_task_detail_table, render_deep_analysis,
    render_report, build_filename, render_improvements,
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
    out = render_deep_analysis(_collected_with_matrix(), _analysis(), section_no=5)
    assert "联网搜索失败后缺乏回退策略" in out
    assert "需联网获取股价并写入文件" in out      # 中文评分标准
    assert "54次工具调用" in out                  # transcript 摘要
    assert "缺乏联网失败回退策略" in out          # 根本原因
    assert "## 五、" in out                       # 动态章节号
    assert "### 5.1 " in out                      # 子标题号


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


def test_table_cell_sanitizes_pipes():
    # 单元格含 | 时应被转义，不破坏表格列数
    data = _collected_with_matrix()
    data["task_matrix"][0]["per_model"]["xspark"]["notes"] = "a | b | c"
    analysis = {"task_analysis": []}  # 无 LLM 分析，走 _short_note 回退
    out = render_task_detail_table(data, analysis)
    # 原始裸 | 不应出现在 note 文本中（被替换为全角｜）
    assert "a ｜ b ｜ c" in out


def test_improvements_sanitizes_pipes():
    analysis = {"improvement_suggestions": [
        {"priority": "P0", "direction": "x | y", "expected_gain": "+1%", "explanation": "p | q"}]}
    out = render_improvements(analysis)
    assert "x ｜ y" in out
    assert "p ｜ q" in out


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


def test_capability_table_sanitizes_pipes():
    data = _collected_with_matrix()
    analysis = {"capability_mapping": {"task_stock": ["工具调用 | 错误恢复"]}}
    out = render_capability_table(data, analysis)
    assert "工具调用 ｜ 错误恢复" in out  # 竖线被转义为全角


# ---- 优势分析 + 动态编号 ----
from report_renderer import _cn_num


def _analysis_with_strength():
    a = _analysis()
    a["task_analysis"].append({
        "task_id": "task_research",
        "filter_reason": "relative_strength",
        "grading_criteria_cn": "需检索并综合多源信息",
        "target_model_breakdown": {
            "notes": "结构化报告完整", "transcript_summary": "并行检索+综合一次到位"},
        "comparison_models": [{"model": "ds", "score": 0.4, "why_succeeded": "对照仅给出片段未综合"}],
        "root_cause": "信息综合与结构化输出能力强",
    })
    a["target_model_strengths"] = [{
        "theme": "信息检索与综合输出领先",
        "related_tasks": ["task_research"],
        "evidence": "research 类目标 0.9 vs 对照中位 0.4",
        "comparison": "对照模型未做综合",
        "token_data": {"target": 100, "others_avg": 200},
    }]
    return a


def test_cn_num():
    assert _cn_num(1) == "一"
    assert _cn_num(5) == "五"
    assert _cn_num(9) == "九"
    assert _cn_num(10) == "十"
    assert _cn_num(12) == "十二"
    assert _cn_num(20) == "二十"


def test_render_deep_analysis_strength_mode():
    out = render_deep_analysis(_collected_with_matrix(), _analysis_with_strength(),
                               section_no=5, mode="strength")
    assert "优势深度分析" in out
    assert "信息检索与综合输出领先" in out
    assert "**得分亮点**" in out        # strength 模式字段措辞
    assert "**制胜原因**" in out
    assert "**对比模型差距**" in out


def test_render_report_with_strength_section():
    # 含 strengths：优势章节出现在短板之前，编号连续不跳号
    out = render_report(_collected_with_matrix(), _analysis_with_strength())
    assert "优势深度分析" in out
    assert "短板深度分析" in out
    # 优势(五) 在 短板(六) 之前
    assert out.index("优势深度分析") < out.index("短板深度分析")
    assert "五、" in out and "六、" in out
    # Token 章节顺延到七
    assert "七、Token消耗与效率对比" in out
    assert "八、分项排名" in out
    assert "九、最终总结与改进建议" in out


def test_render_report_without_strength_section():
    # 无 strengths：不出优势章节，短板回到五、Token 回到六（向后兼容旧 analysis）
    out = render_report(_collected_with_matrix(), _analysis())
    assert "优势深度分析" not in out
    assert "五、" in out and "短板深度分析" in out
    assert "六、Token消耗与效率对比" in out


def test_render_report_single_model_strength_title():
    d = _collected_with_matrix()
    d["is_single_model"] = True
    d["models"] = [d["models"][1]]
    out = render_report(d, _analysis_with_strength())
    assert "高分任务深度分析" in out      # 单模型优势标题措辞
    assert "整体排名" not in out
