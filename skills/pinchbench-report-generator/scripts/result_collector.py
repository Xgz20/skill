"""阶段1：模型目录扫描与结果 JSON 解析。"""
import json
from pathlib import Path
from typing import List

from models import ModelResult, TaskResult


def _is_model_dir(d: Path) -> bool:
    """目录同时含 *.json 结果文件和 *_transcripts/ 即视为模型目录。"""
    if not d.is_dir():
        return False
    has_json = any(d.glob("*.json"))
    has_transcripts = any(p.is_dir() and p.name.endswith("_transcripts")
                          for p in d.iterdir())
    return has_json and has_transcripts


def discover_model_dirs(inputs: List[Path]) -> List[Path]:
    """
    识别模型目录。
    - 输入本身是模型目录 → 直接收录
    - 输入是总目录 → 递归其直接子目录中的模型目录

    注意：仅扫描输入目录的直接子目录，不递归更深层。
    """
    found = []
    for inp in inputs:
        if _is_model_dir(inp):
            found.append(inp)
            continue
        for child in sorted(inp.iterdir()):
            if _is_model_dir(child):
                found.append(child)
    # 去重，保持顺序
    seen, uniq = set(), []
    for d in found:
        key = d.resolve()
        if key not in seen:
            seen.add(key)
            uniq.append(d)
    return uniq


def _find_result_json(model_dir: Path) -> Path:
    """返回模型目录下的结果 JSON。

    取字典序第一个 *.json。依赖命名约定（如 0001_<model>.json），
    每个模型目录预期只有一个结果 JSON。
    """
    candidates = sorted(model_dir.glob("*.json"))
    if not candidates:
        raise FileNotFoundError(f"模型目录无结果 JSON: {model_dir}")
    return candidates[0]


def parse_model_json(model_dir: Path) -> ModelResult:
    """解析单个模型目录的结果 JSON 为 ModelResult。"""
    json_path = _find_result_json(model_dir)
    try:
        data = json.loads(json_path.read_text())
    except json.JSONDecodeError as e:
        raise ValueError(f"结果 JSON 解析失败: {json_path}") from e

    tasks = []
    for t in data.get("tasks", []):
        grading = t.get("grading", {})
        runs = grading.get("runs", [{}])
        # 仅取第一次 run，与 grading.mean 对应
        run0 = runs[0] if runs else {}
        usage = t.get("usage", {})
        fm = t.get("frontmatter", {})
        tasks.append(TaskResult(
            task_id=t.get("task_id", ""),
            category=fm.get("category", "unknown"),
            status=t.get("status", "unknown"),
            timed_out=t.get("timed_out", False),
            execution_time=t.get("execution_time"),
            score=grading.get("mean", 0.0),
            breakdown=run0.get("breakdown", {}),
            notes=run0.get("notes", ""),
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            request_count=usage.get("request_count", 0),
            difficulty=fm.get("difficulty") or "unknown",
        ))

    model_field = data.get("model", model_dir.name)
    return ModelResult(
        model=model_field,
        display_name=model_field,
        suite=data.get("suite", "unknown"),
        benchmark_version=data.get("benchmark_version", "unknown"),
        tasks=tasks,
    )


def collect_all(inputs: List[Path]) -> List[ModelResult]:
    """扫描所有输入路径，返回所有模型结果。"""
    return [parse_model_json(d) for d in discover_model_dirs(inputs)]
