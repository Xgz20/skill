"""测试 result_collector.py"""
import json
import pytest
from pathlib import Path
from result_collector import (
    find_latest_round,
    collect_model_results,
    find_previous_round_results,
)


def test_find_latest_round_returns_max(tmp_path):
    """测试：返回最大轮次目录"""
    base = tmp_path / "task_test"
    (base / "round_1").mkdir(parents=True)
    (base / "round_2").mkdir(parents=True)
    (base / "round_3").mkdir(parents=True)

    result = find_latest_round(base)
    assert result == base / "round_3"


def test_find_latest_round_none_when_empty(tmp_path):
    """测试：无轮次目录时返回 None"""
    base = tmp_path / "task_test"
    base.mkdir()
    assert find_latest_round(base) is None


def test_collect_model_results(tmp_path):
    """测试：收集模型结果"""
    round_dir = tmp_path / "round_1"
    model_dir = round_dir / "xopglm5"
    model_dir.mkdir(parents=True)

    # 创建结果 JSON
    result_data = {
        "tasks": [{
            "task_id": "task_test",
            "grading": {"mean": 0.75},
            "usage": {"total_tokens": 12000},
            "timed_out": False,
            "execution_time": 108.58,
        }]
    }
    (model_dir / "0001_xopglm5.json").write_text(json.dumps(result_data))

    results = collect_model_results(round_dir)
    assert len(results) == 1
    assert results[0]["model"] == "xopglm5"
    assert results[0]["score"] == 0.75
    assert results[0]["timed_out"] is False
    assert results[0]["execution_time"] == 108.58


def test_find_previous_round_results_original_returns_none(tmp_path):
    """测试：原始用例（round 0）无基线"""
    result = find_previous_round_results("task_test", tmp_path)
    assert result is None


def test_find_previous_round_results_r1_finds_base(tmp_path):
    """测试：_r1 找到原始用例的结果作为基线"""
    base_results = tmp_path / "results-auto" / "task_test" / "round_1"
    base_results.mkdir(parents=True)

    result = find_previous_round_results("task_test_r1", tmp_path)
    assert result == base_results
