"""低分任务筛选测试。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from models import ModelResult, TaskResult
from task_filter import filter_tasks_to_analyze, filter_strength_tasks, FilterThresholds


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


def test_all_low_takes_precedence_over_relative():
    # 同时满足全员低分(<0.4)和相对短板(others中位数>=0.8且差距>=0.2)时，
    # all_low 优先（验证 continue 语义）。
    # 构造：target=0.1，两个 other=1.0,0.0 → 中位数0.5... 需要 others 都<0.4 才算 all_low
    # 用 target=0.1, others 都<0.4 但中位数不可能>=0.8，故 all_low 与 relative 天然互斥。
    # 改为验证：all_low 命中时不会被误标为 relative。
    target = _model("spark", {"task_h": 0.1})
    o1 = _model("ds", {"task_h": 0.2})
    o2 = _model("glm", {"task_h": 0.3})
    picked = filter_tasks_to_analyze([target, o1, o2], target_model="spark")
    reasons = {p["task_id"]: p["reason"] for p in picked}
    assert reasons["task_h"] == "all_low"


# ---- 优势筛选（与短板对称） ----

def test_relative_strength():
    # 目标 spark 在 task_win 领先：spark 1.0，其他 0.4 中位
    target = _model("spark", {"task_win": 1.0, "task_mid": 0.7})
    o1 = _model("ds", {"task_win": 0.4, "task_mid": 0.7})
    o2 = _model("glm", {"task_win": 0.4, "task_mid": 0.7})
    picked = filter_strength_tasks([target, o1, o2], target_model="spark")
    reasons = {p["task_id"]: p["reason"] for p in picked}
    assert reasons["task_win"] == "relative_strength"
    assert "task_mid" not in reasons          # 与对照持平，不入选


def test_relative_strength_requires_high_target():
    # 领先幅度够(0.3)但目标本身未达 strength_min(0.8)，不入选
    target = _model("spark", {"task_x": 0.7})
    o1 = _model("ds", {"task_x": 0.4})
    picked = filter_strength_tasks([target, o1], target_model="spark")
    assert picked == []


def test_absolute_high_single_model():
    # 单模型：得分 >=0.9 入选
    target = _model("spark", {"task_great": 0.95, "task_mid": 0.7})
    picked = filter_strength_tasks([target], target_model="spark")
    reasons = {p["task_id"]: p["reason"] for p in picked}
    assert reasons["task_great"] == "absolute_high"
    assert "task_mid" not in reasons


def test_strength_top_n_limit_and_order():
    # 构造 5 个不同领先幅度的优势任务，top_n=3 应保留领先幅度最大的 3 个
    target = _model("spark", {f"t{i}": 0.8 + i * 0.04 for i in range(5)})  # 0.80..0.96
    o1 = _model("ds", {f"t{i}": 0.4 for i in range(5)})                    # 全 0.4
    th = FilterThresholds(strength_top_n=3)
    picked = filter_strength_tasks([target, o1], target_model="spark", thresholds=th)
    assert len(picked) == 3
    ids = [p["task_id"] for p in picked]
    assert ids == ["t4", "t3", "t2"]          # 按 lead 降序
    # lead 单调递减
    leads = [p["lead"] for p in picked]
    assert leads == sorted(leads, reverse=True)


def test_strength_custom_thresholds():
    # 放宽 gap 到 0.1，原本差 0.15 的任务可入选
    target = _model("spark", {"task_x": 0.9})
    o1 = _model("ds", {"task_x": 0.75})
    th = FilterThresholds(relative_strength_gap=0.1)
    picked = filter_strength_tasks([target, o1], target_model="spark", thresholds=th)
    assert {p["task_id"] for p in picked} == {"task_x"}
