"""统计指标计算测试。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

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
