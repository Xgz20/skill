"""统计指标计算测试。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from models import ModelResult, TaskResult
from score_calculator import (
    overall_score_rate, category_scores, count_high_tasks,
    count_low_tasks, token_efficiency, build_category_summary,
    build_difficulty_summary, highest_difficulty,
)


def _t(tid, cat, score, total=1000, difficulty="unknown"):
    return TaskResult(tid, cat, "success", False, 1.0, score, {}, "",
                      total - 10, 10, total, 1, difficulty)


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


def test_token_efficiency_zero_tokens():
    # 空任务模型 total_tokens=0，应安全返回 0.0 而非除零
    assert token_efficiency(_model("a", [])) == 0.0


def test_build_category_summary_empty():
    # 无模型时返回空列表
    assert build_category_summary([]) == []


def test_build_category_summary_tie_deterministic():
    # 平局时按字母序取最小，保证可复现
    m_b = _model("b", [_t("t1", "coding", 1.0)])
    m_a = _model("a", [_t("t1", "coding", 1.0)])
    summary = build_category_summary([m_b, m_a])  # 注意传入顺序 b 在前
    coding = next(r for r in summary if r["category"] == "coding")
    assert coding["best_model"] == "a"  # 字母序最小，不受传入顺序影响


# ---- 按难度等级聚合 ----

def test_build_difficulty_summary_basic():
    # 两个模型 × L1×2 + L2×1 + L3×1
    m1 = _model("a", [
        _t("t1", "c", 1.0, difficulty="L1"),
        _t("t2", "c", 0.8, difficulty="L1"),
        _t("t3", "c", 0.5, difficulty="L2"),
        _t("t4", "c", 0.2, difficulty="L3"),
    ])
    m2 = _model("b", [
        _t("t1", "c", 0.9, difficulty="L1"),
        _t("t2", "c", 0.9, difficulty="L1"),
        _t("t3", "c", 1.0, difficulty="L2"),
        _t("t4", "c", 1.0, difficulty="L3"),
    ])
    rows = build_difficulty_summary([m1, m2])
    # 顺序按 L1, L2, L3
    assert [r["difficulty"] for r in rows] == ["L1", "L2", "L3"]

    l1 = rows[0]
    assert l1["task_count"] == 2
    assert abs(l1["scores"]["a"] - 0.9) < 1e-9     # (1.0+0.8)/2
    assert abs(l1["scores"]["b"] - 0.9) < 1e-9
    assert abs(l1["totals"]["a"] - 1.8) < 1e-9
    # 平局取字母序最小
    assert l1["best_model"] == "a"
    assert abs(l1["score_range"]) < 1e-9

    l3 = rows[2]
    assert l3["task_count"] == 1
    assert l3["best_model"] == "b"
    assert abs(l3["score_range"] - 0.8) < 1e-9     # 1.0 - 0.2


def test_build_difficulty_summary_unknown_last():
    # unknown 任务排在最后
    m = _model("a", [
        _t("t1", "c", 1.0, difficulty="L2"),
        _t("t2", "c", 0.5, difficulty="unknown"),
    ])
    rows = build_difficulty_summary([m])
    assert [r["difficulty"] for r in rows] == ["L2", "unknown"]


def test_highest_difficulty_skips_unknown():
    rows = build_difficulty_summary([_model("a", [
        _t("t1", "c", 1.0, difficulty="L1"),
        _t("t2", "c", 1.0, difficulty="L3"),
        _t("t3", "c", 1.0, difficulty="unknown"),
    ])])
    assert highest_difficulty(rows) == "L3"


def test_highest_difficulty_empty_or_all_unknown():
    assert highest_difficulty([]) == ""
    rows = build_difficulty_summary([_model("a", [
        _t("t1", "c", 1.0, difficulty="unknown"),
    ])])
    assert highest_difficulty(rows) == ""


def test_build_difficulty_summary_empty():
    assert build_difficulty_summary([]) == []
