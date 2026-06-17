"""评测结果收集器：读取 results-auto 下的评测结果和 transcripts。"""
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))
from path_resolver import extract_base_task_id, extract_optimization_round

ROUND_RE = re.compile(r"^round_(\d+)$")


def find_latest_round(task_results_base: Path) -> Optional[Path]:
    """
    找到 task_results_base 下最大轮次的目录。

    Args:
        task_results_base: 如 results-auto/task_xxx/

    Returns:
        最大轮次目录路径，无则返回 None
    """
    if not task_results_base.exists():
        return None

    round_dirs = []
    for d in task_results_base.iterdir():
        if d.is_dir():
            m = ROUND_RE.match(d.name)
            if m:
                round_dirs.append((int(m.group(1)), d))

    if not round_dirs:
        return None

    return max(round_dirs, key=lambda x: x[0])[1]


def collect_model_results(round_dir: Path) -> List[Dict]:
    """
    收集某轮评测中所有模型的结果。

    Args:
        round_dir: 如 results-auto/task_xxx/round_1/

    Returns:
        模型结果列表，每项包含 model/score/usage/timed_out/transcript_path
    """
    results = []

    for model_dir in round_dir.iterdir():
        if not model_dir.is_dir() or model_dir.name.endswith("_transcripts"):
            continue

        # 查找结果 JSON
        json_files = [f for f in model_dir.glob("*.json")]
        if not json_files:
            continue

        with open(json_files[0]) as f:
            data = json.load(f)

        # 提取任务结果（取第一个任务）
        task_data = data.get("tasks", [{}])[0]

        # 查找 transcript 文件（多轮场景取第一个匹配，可能是任意 run）
        # 用于 case-optimizer 的聚合分析，不依赖特定轮次
        transcript_dirs = list(model_dir.glob("*_transcripts"))
        transcript_path = None
        if transcript_dirs:
            jsonl_files = list(transcript_dirs[0].glob("*.jsonl"))
            if jsonl_files:
                transcript_path = jsonl_files[0]

        results.append({
            "model": model_dir.name,
            "score": task_data.get("grading", {}).get("mean", 0.0),
            "usage": task_data.get("usage", {}),
            "timed_out": task_data.get("timed_out", False),
            "status": task_data.get("status", "unknown"),
            "execution_time": task_data.get("execution_time", None),
            "transcript_path": transcript_path,
            "raw_task_data": task_data,
        })

    return results


def find_previous_round_results(task_id: str, project_root: Path) -> Optional[Path]:
    """
    找到用例家族中上一版本的最新评测结果，用于基线对比。

    Args:
        task_id: 当前用例 ID（如 task_xxx_r1）
        project_root: 项目根目录

    Returns:
        上一版本的最新轮次结果目录，原始用例返回 None
    """
    base = extract_base_task_id(task_id)
    current_round = extract_optimization_round(task_id)

    if current_round == 0:
        return None  # 原始用例，无基线

    prev_round = current_round - 1
    prev_id = base if prev_round == 0 else f"{base}_r{prev_round}"

    return find_latest_round(project_root / "results-auto" / prev_id)


def load_transcript(transcript_path: Optional[Path]) -> List[Dict]:
    """
    加载 transcript JSONL 文件。

    Args:
        transcript_path: JSONL 文件路径

    Returns:
        消息列表，每项为一条交互记录
    """
    if transcript_path is None or not transcript_path.exists():
        return []

    messages = []
    with open(transcript_path) as f:
        for line in f:
            line = line.strip()
            if line:
                messages.append(json.loads(line))

    return messages
