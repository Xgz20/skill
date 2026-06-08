"""低分任务筛选测试。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

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
