"""测试 task_io.py"""
import pytest
from pathlib import Path
from task_io import load_task_markdown, get_output_path


def test_load_task_markdown(tmp_path):
    """测试：加载用例 markdown"""
    task_file = tmp_path / "task_test.md"
    task_file.write_text("""---
id: task_test
timeout: 60
---

## Prompt

分析数据
""")
    task = load_task_markdown(task_file)
    assert task["raw_content"].startswith("---")
    assert "分析数据" in task["raw_content"]
    assert task["frontmatter"]["timeout"] == 60


def test_get_output_path_from_generated_cases(tmp_path):
    """测试：源在 generated_cases，产物同目录"""
    source = tmp_path / "output" / "generated_cases" / "task_test.md"
    source.parent.mkdir(parents=True)
    source.write_text("# test")

    output = get_output_path(source, "task_test", 1)
    assert output == source.parent / "task_test_r1.md"


def test_get_output_path_chained(tmp_path):
    """测试：链式演进，_r1 产出 _r2（去除旧后缀）"""
    source = tmp_path / "task_test_r1.md"
    source.write_text("# test")

    # base_task_id=task_test, 新轮次=2
    output = get_output_path(source, "task_test", 2)
    assert output == source.parent / "task_test_r2.md"
