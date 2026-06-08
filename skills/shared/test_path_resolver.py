"""测试路径解析器。"""
import pytest
from pathlib import Path
from path_resolver import (
    resolve_task_path,
    extract_base_task_id,
    extract_optimization_round,
)


def test_resolve_task_path_with_task_id(tmp_path):
    """测试：纯 task_id 输入"""
    # 准备：创建测试文件
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    test_file = tasks_dir / "task_test.md"
    test_file.write_text("# Test")

    # 执行
    result = resolve_task_path("task_test", tmp_path)

    # 验证
    assert result == test_file


def test_resolve_task_path_fallback_to_generated_cases(tmp_path):
    """测试：回退到 output/generated_cases/"""
    # 准备
    gen_dir = tmp_path / "output" / "generated_cases"
    gen_dir.mkdir(parents=True)
    test_file = gen_dir / "task_test.md"
    test_file.write_text("# Test")

    # 执行
    result = resolve_task_path("task_test", tmp_path)

    # 验证
    assert result == test_file


def test_resolve_task_path_not_found(tmp_path):
    """测试：用例不存在"""
    with pytest.raises(FileNotFoundError, match="未找到用例"):
        resolve_task_path("task_nonexistent", tmp_path)


def test_extract_base_task_id():
    """测试：提取 base_task_id"""
    assert extract_base_task_id("task_xxx") == "task_xxx"
    assert extract_base_task_id("task_xxx_r1") == "task_xxx"
    assert extract_base_task_id("task_xxx_r10") == "task_xxx"


def test_extract_optimization_round():
    """测试：提取优化轮次"""
    assert extract_optimization_round("task_xxx") == 0
    assert extract_optimization_round("task_xxx_r1") == 1
    assert extract_optimization_round("task_xxx_r10") == 10
