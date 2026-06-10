"""collect 编排测试。"""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

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
    # 优势任务字段存在（task_ok 全员 1.0 持平，不构成相对优势）
    assert "strengths_to_analyze" in data


def test_build_collected_data_captures_strength(tmp_path):
    # 目标在 task_win 领先：spark 1.0 vs ds 0.4 → relative_strength
    _make_model_dir(tmp_path, "spark", "xsparkx2flash",
                    [_task("task_win", "research", 1.0), _task("task_ok", "coding", 0.7)])
    _make_model_dir(tmp_path, "ds", "xopdeepseek",
                    [_task("task_win", "research", 0.4), _task("task_ok", "coding", 0.7)])
    data = build_collected_data([tmp_path], target_model="xsparkx2flash",
                                tasks_root=tmp_path / "tasks")
    strength_ids = {s["task_id"]: s for s in data["strengths_to_analyze"]}
    assert "task_win" in strength_ids
    assert strength_ids["task_win"]["reason"] == "relative_strength"
    # 对照 transcript 指向得分最高的对手
    bo = strength_ids["task_win"]["best_other_transcript"]
    assert bo is not None and bo["transcript"].endswith("task_win.jsonl")


def test_resolve_transcript_path(tmp_path):
    d = _make_model_dir(tmp_path, "spark", "xsparkx2flash",
                        [_task("task_stock", "research", 0.0)])
    p = resolve_transcript_path(d, "task_stock")
    assert p is not None and p.name == "task_stock.jsonl"
    assert resolve_transcript_path(d, "task_missing") is None


def test_build_collected_data_single_model(tmp_path):
    _make_model_dir(tmp_path, "spark", "xsparkx2flash",
                    [_task("task_low", "research", 0.5), _task("task_ok", "coding", 0.9)])
    data = build_collected_data([tmp_path], target_model="xsparkx2flash",
                                tasks_root=tmp_path / "tasks")
    assert data["is_single_model"] is True
    # 单模型时所有 best_other_transcript 为 None
    assert all(a["best_other_transcript"] is None for a in data["tasks_to_analyze"])
    # task_matrix 每行 per_model 只含一个 key
    assert all(len(row["per_model"]) == 1 for row in data["task_matrix"])
    # 绝对阈值 <0.8：task_low(0.5) 入选，task_ok(0.9) 不入选
    ids = {a["task_id"]: a["reason"] for a in data["tasks_to_analyze"]}
    assert ids.get("task_low") == "absolute_low"
    assert "task_ok" not in ids
