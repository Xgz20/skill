"""统一路径解析工具，支持 task_id 或文件路径输入。"""
from pathlib import Path
from typing import Union


def resolve_task_path(task_input: str, project_root: Path) -> Path:
    """
    解析用例路径，支持三种输入形式：
    1. 纯 task_id：在 tasks/ 和 output/generated_cases/ 中查找
    2. 相对路径：相对于项目根目录解析
    3. 绝对路径：直接使用

    Args:
        task_input: 用户输入（task_id 或路径）
        project_root: 项目根目录

    Returns:
        用例文件的绝对路径

    Raises:
        FileNotFoundError: 如果用例文件不存在
    """
    # 如果不包含路径分隔符且不以 .md 结尾，视为 task_id
    if "/" not in task_input and not task_input.endswith(".md"):
        # 优先在 tasks/ 中查找
        for base_dir in ["tasks", "output/generated_cases"]:
            candidate = project_root / base_dir / f"{task_input}.md"
            if candidate.exists():
                return candidate
        raise FileNotFoundError(
            f"未找到用例 {task_input}，已搜索: tasks/, output/generated_cases/"
        )

    # 否则视为路径
    path = Path(task_input)
    if not path.is_absolute():
        path = project_root / path

    if not path.exists():
        raise FileNotFoundError(f"用例文件不存在: {path}")

    return path


def extract_base_task_id(task_id: str) -> str:
    """
    从 task_id 中提取 base_task_id（去除 _r<N> 后缀）。

    Examples:
        task_csv_iris_summary → task_csv_iris_summary
        task_csv_iris_summary_r2 → task_csv_iris_summary
    """
    import re
    return re.sub(r'_r\d+$', '', task_id)


def extract_optimization_round(task_id: str) -> int:
    """
    从 task_id 中提取优化轮次。

    Examples:
        task_csv_iris_summary → 0
        task_csv_iris_summary_r2 → 2
    """
    import re
    match = re.match(r'^.+_r(\d+)$', task_id)
    return int(match.group(1)) if match else 0
