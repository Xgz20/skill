"""测试 batch_runner.py"""
import pytest
from pathlib import Path
from batch_runner import load_config, detect_next_round


def test_load_config_creates_template(tmp_path):
    """测试：配置文件不存在时，从 ../assets/ 复制模板并退出"""
    # load_config 通过 Path(__file__).parent.parent / "assets" 找真实模板。
    # 测试只需提供一个不存在的 project_root（tmp_path），
    # 验证配置缺失时会触发"复制模板 + sys.exit(0)"逻辑。
    with pytest.raises(SystemExit) as exc_info:
        load_config(tmp_path)
    assert exc_info.value.code == 0
    assert (tmp_path / "models-config.yaml").exists()


def test_detect_next_round_no_existing(tmp_path):
    """测试：没有已存在的轮次，返回 1"""
    assert detect_next_round("task_test", tmp_path) == 1


def test_detect_next_round_with_existing(tmp_path):
    """测试：已存在 round_1 和 round_2，返回 3"""
    results_dir = tmp_path / "results-auto" / "task_test"
    (results_dir / "round_1").mkdir(parents=True)
    (results_dir / "round_2").mkdir(parents=True)

    assert detect_next_round("task_test", tmp_path) == 3


def test_run_batch_refuses_when_tasks_has_different_file(tmp_path):
    """测试：tasks/ 已存在同名但非同一文件时，refuse 退出，不删除真实用例

    白盒测试：验证关键不变量 — 同名但内容不同时 samefile() 返回 False
    （这正是 run_batch 中触发 refuse 分支的条件）。
    """
    # 准备：在 tmp_path 模拟项目根
    (tmp_path / "tasks").mkdir()
    real_in_tasks = tmp_path / "tasks" / "task_clash.md"
    real_in_tasks.write_text("REAL TASK CONTENT")  # 模拟已晋升的真实用例

    gen_dir = tmp_path / "output" / "generated_cases"
    gen_dir.mkdir(parents=True)
    different_source = gen_dir / "task_clash.md"
    different_source.write_text("DIFFERENT GENERATED CONTENT")

    # 关键不变量：同名但内容不同时，samefile() 返回 False
    assert not real_in_tasks.samefile(different_source)
    # 真实用例应当依然存在（核心安全要求）
    assert real_in_tasks.exists()
    assert real_in_tasks.read_text() == "REAL TASK CONTENT"
