"""集成测试：模拟评测结果，验证多模块端到端协作。"""
import json
from pathlib import Path

# sys.path 在 conftest.py 中统一处理（scripts/ 和 ../shared/）


def _make_mock_results(project_root: Path, task_id: str, round_num: int, scores: dict):
    """在 project_root 下创建模拟评测结果目录结构。"""
    round_dir = project_root / "results-auto" / task_id / f"round_{round_num}"
    for model, score in scores.items():
        model_dir = round_dir / model
        model_dir.mkdir(parents=True)
        result = {
            "tasks": [{
                "task_id": task_id,
                "grading": {"mean": score},
                "usage": {"total_tokens": 10000},
                "timed_out": False,
                "status": "completed",
            }]
        }
        (model_dir / f"0001_{model}.json").write_text(json.dumps(result))
    return round_dir


def test_collect_and_analyze_all_perfect(tmp_path):
    """端到端：收集结果 → 难度分析（全满分应触发区分度问题）"""
    from result_collector import collect_model_results, find_latest_round
    from analyzers import analyze_difficulty

    _make_mock_results(tmp_path, "task_test", 1,
                       {"model_a": 1.0, "model_b": 1.0})

    results_dir = find_latest_round(tmp_path / "results-auto" / "task_test")
    assert results_dir is not None

    model_results = collect_model_results(results_dir)
    assert len(model_results) == 2

    difficulty = analyze_difficulty(model_results)
    assert difficulty["has_issue"] is True  # 全部满分→区分度不足


def test_collect_and_analyze_good_spread(tmp_path):
    """端到端：分数有区分度时不报问题"""
    from result_collector import collect_model_results, find_latest_round
    from analyzers import analyze_difficulty

    _make_mock_results(tmp_path, "task_test", 1,
                       {"model_a": 0.3, "model_b": 0.8})

    results_dir = find_latest_round(tmp_path / "results-auto" / "task_test")
    model_results = collect_model_results(results_dir)
    difficulty = analyze_difficulty(model_results)
    assert difficulty["has_issue"] is False


def test_chained_family_baseline(tmp_path):
    """链式演进：家族基线识别"""
    from result_collector import find_previous_round_results

    # 创建原始用例的结果
    base_results = tmp_path / "results-auto" / "task_test" / "round_1"
    base_results.mkdir(parents=True)

    # _r1 应找到原始用例结果作为基线
    prev = find_previous_round_results("task_test_r1", tmp_path)
    assert prev == base_results

    # 原始用例无基线
    prev_none = find_previous_round_results("task_test", tmp_path)
    assert prev_none is None
