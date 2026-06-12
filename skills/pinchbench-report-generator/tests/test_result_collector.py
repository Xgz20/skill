"""目录扫描与 JSON 解析测试。"""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

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


def _task(tid, cat, score, total=100, reqs=1, difficulty=None):
    fm = {"category": cat, "grading_weights": {}}
    if difficulty is not None:
        fm["difficulty"] = difficulty
    return {
        "task_id": tid, "status": "success", "timed_out": False,
        "execution_time": 1.0,
        "usage": {"input_tokens": total - 10, "output_tokens": 10,
                  "total_tokens": total, "request_count": reqs},
        "grading": {"mean": score, "runs": [
            {"breakdown": {"automated.x": score}, "notes": "n"}]},
        "frontmatter": fm,
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
    # frontmatter 无 difficulty 时默认为 unknown
    assert t.difficulty == "unknown"


def test_parse_model_json_with_difficulty(tmp_path):
    # round-3 起 frontmatter 含 difficulty 字段
    d = _make_model_dir(tmp_path, "xds", "xopdeepseek", [
        _task("task_a", "coding", 1.0, difficulty="L1"),
        _task("task_b", "research", 0.8, difficulty="L3"),
    ])
    m = parse_model_json(d)
    assert m.tasks[0].difficulty == "L1"
    assert m.tasks[1].difficulty == "L3"
