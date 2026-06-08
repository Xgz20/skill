"""CLI 测试。"""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from report_cli import cmd_collect, cmd_render


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
                {"breakdown": {"automated.x": score}, "notes": "n"}]},
            "frontmatter": {"category": cat, "grading_weights": {}}}


def test_cmd_collect(tmp_path):
    _make_model_dir(tmp_path, "spark", "xsparkx2flash",
                    [_task("task_stock", "research", 0.0)])
    _make_model_dir(tmp_path, "ds", "xopdeepseek",
                    [_task("task_stock", "research", 1.0)])
    out = tmp_path / "collected.json"
    cmd_collect(inputs=[str(tmp_path)], target_model="xsparkx2flash",
                tasks_root=str(tmp_path / "tasks"), output=str(out))
    assert out.exists()
    data = json.loads(out.read_text())
    assert data["target_model"] == "xsparkx2flash"


def test_cmd_render(tmp_path):
    collected = {
        "target_model": "xspark", "is_single_model": True,
        "models": [{"model": "xspark", "display_name": "Spark", "suite": "all",
                    "score_rate": 0.5, "high_task_count": 0, "low_task_count": 1,
                    "total_tokens": 100, "total_requests": 1, "token_efficiency": 0.005,
                    "category_scores": {"research": 0.5}, "task_count": 1}],
        "category_summary": [{"category": "research", "scores": {"xspark": 0.5},
                              "best_model": "xspark"}],
        "task_matrix": [{"task_id": "task_stock", "category": "research",
                         "per_model": {"xspark": {"score": 0.5, "notes": "n", "breakdown": {}}}}],
        "tasks_to_analyze": [],
    }
    analysis = {"task_analysis": [], "target_model_weaknesses": [],
                "improvement_suggestions": [], "capability_mapping": {}}
    cpath = tmp_path / "collected.json"
    apath = tmp_path / "analysis.json"
    cpath.write_text(json.dumps(collected))
    apath.write_text(json.dumps(analysis))
    out = tmp_path / "report.md"
    cmd_render(collected_data=str(cpath), analysis=str(apath), output=str(out))
    assert out.exists()
    assert "评测报告" in out.read_text()
