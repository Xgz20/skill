"""用例文件读写工具。"""
import yaml
from pathlib import Path
from typing import Dict


def load_task_markdown(task_file: Path) -> Dict:
    """
    加载用例 markdown 文件，解析 frontmatter 和正文。

    Args:
        task_file: 用例文件路径

    Returns:
        {raw_content, frontmatter, body}
    """
    raw_content = task_file.read_text()

    frontmatter = {}
    body = raw_content

    # 解析 YAML frontmatter
    if raw_content.startswith("---"):
        parts = raw_content.split("---", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                frontmatter = {}
            body = parts[2]

    return {
        "raw_content": raw_content,
        "frontmatter": frontmatter,
        "body": body,
    }


def get_output_path(source: Path, base_task_id: str, new_round: int) -> Path:
    """
    计算优化产物的输出路径（与源用例同目录）。

    Args:
        source: 源用例文件路径
        base_task_id: 基础用例 ID（去除 _r 后缀）
        new_round: 新的优化轮次

    Returns:
        产物路径，如 <源目录>/<base_task_id>_r<N>.md
    """
    return source.parent / f"{base_task_id}_r{new_round}.md"


def write_optimized_task(
    output_path: Path,
    optimized_content: str,
):
    """写入优化后的用例文件。已存在时打印警告（不阻止覆盖）。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        print(f"⚠️  输出文件已存在，将覆盖: {output_path}")
    output_path.write_text(optimized_content)
