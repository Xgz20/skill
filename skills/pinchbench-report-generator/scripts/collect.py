"""阶段1 编排：整合收集、计算、筛选，产出 collected_data.json。"""
import warnings
from pathlib import Path
from typing import Dict, List, Optional

from models import ModelResult
from result_collector import collect_all, discover_model_dirs
import score_calculator as sc
from task_filter import filter_tasks_to_analyze, filter_strength_tasks, FilterThresholds


def resolve_transcript_path(model_dir: Path, task_id: str) -> Optional[Path]:
    """在模型目录的 *_transcripts/ 下找 <task_id>.jsonl。"""
    for d in model_dir.iterdir():
        if d.is_dir() and d.name.endswith("_transcripts"):
            cand = d / f"{task_id}.jsonl"
            if cand.exists():
                return cand
    return None


def _model_dir_map(inputs: List[Path], models: List[ModelResult]) -> Dict[str, Path]:
    """模型 model 字段 → 其目录路径。

    依赖 collect_all 与 discover_model_dirs 同序遍历（collect_all 实现为
    [parse_model_json(d) for d in discover_model_dirs(inputs)]）。断言长度一致以防未来漂移。
    """
    dirs = discover_model_dirs(inputs)
    assert len(dirs) == len(models), (
        f"目录数({len(dirs)})与模型数({len(models)})不一致，顺序映射不可靠")
    return {m.model: d for m, d in zip(models, dirs)}


def _model_summary(m: ModelResult) -> Dict:
    return {
        "model": m.model,
        "display_name": m.display_name,
        "suite": m.suite,
        "benchmark_version": m.benchmark_version,
        "score_rate": sc.overall_score_rate(m),
        "high_task_count": sc.count_high_tasks(m),
        "low_task_count": sc.count_low_tasks(m),
        "total_tokens": m.total_tokens,
        "total_requests": m.total_requests,
        "token_efficiency": sc.token_efficiency(m),
        "category_scores": sc.category_scores(m),
        "task_count": m.task_count,
    }


def _task_matrix(models: List[ModelResult]) -> List[Dict]:
    """对齐任务矩阵：每任务一行，含各模型得分/breakdown/notes。"""
    all_ids = []
    seen = set()
    for m in models:
        for t in m.tasks:
            if t.task_id not in seen:
                seen.add(t.task_id)
                all_ids.append((t.task_id, t.category))
    rows = []
    for tid, cat in all_ids:
        per_model = {}
        for m in models:
            t = next((x for x in m.tasks if x.task_id == tid), None)
            if t:
                per_model[m.model] = {
                    "score": t.score, "breakdown": t.breakdown,
                    "notes": t.notes, "total_tokens": t.total_tokens,
                    "request_count": t.request_count,
                    "timed_out": t.timed_out,
                }
        rows.append({"task_id": tid, "category": cat, "per_model": per_model})
    return rows


def build_collected_data(
    inputs: List[Path],
    target_model: str,
    tasks_root: Path,
    thresholds: Optional[FilterThresholds] = None,
) -> Dict:
    """构建阶段2 输入数据结构。"""
    models = collect_all(inputs)
    if not models:
        raise ValueError("未发现任何模型目录")

    # 若 target_model 未在结果中，默认取第一个并告警
    if not any(m.model == target_model for m in models):
        warnings.warn(
            f"目标模型 '{target_model}' 不在结果中，回退到 '{models[0].model}'")
        target_model = models[0].model

    dir_map = _model_dir_map(inputs, models)
    picked = filter_tasks_to_analyze(models, target_model, thresholds)
    picked_strengths = filter_strength_tasks(models, target_model, thresholds)

    # 高分对比模型（用于对比 transcript）
    others = [m for m in models if m.model != target_model]

    def _best_other_transcript(tid: str) -> Optional[Dict]:
        """选得分最高的对比模型 transcript（短板/优势均用最强对手对照）。"""
        if not others:
            return None
        best = max(others,
                   key=lambda m: next((t.score for t in m.tasks if t.task_id == tid), 0.0))
        bo_path = resolve_transcript_path(dir_map[best.model], tid)
        if bo_path:
            return {"model": best.model, "transcript": str(bo_path)}
        return None

    def _build_analyze_entry(p: Dict) -> Dict:
        """把筛选结果项转为阶段2 输入项（解析 transcript / task_md 路径）。"""
        tid = p["task_id"]
        t_path = resolve_transcript_path(dir_map[target_model], tid)
        return {
            "task_id": tid,
            "reason": p["reason"],
            "target_transcript": str(t_path) if t_path else None,
            "best_other_transcript": _best_other_transcript(tid),
            "task_md": str(tasks_root / f"{tid}.md"),
        }

    tasks_to_analyze = [_build_analyze_entry(p) for p in picked]
    strengths_to_analyze = [_build_analyze_entry(p) for p in picked_strengths]

    return {
        "target_model": target_model,
        "is_single_model": len(models) == 1,
        "models": [_model_summary(m) for m in sc.rank_models(models)],
        "category_summary": sc.build_category_summary(models),
        "task_matrix": _task_matrix(models),
        "tasks_to_analyze": tasks_to_analyze,
        "strengths_to_analyze": strengths_to_analyze,
    }
