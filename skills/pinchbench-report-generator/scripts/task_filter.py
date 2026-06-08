"""低分任务筛选：相对短板 + 全员低分 + 单模型绝对阈值回退。"""
from dataclasses import dataclass
from statistics import median
from typing import Dict, List, Optional

from models import ModelResult


@dataclass
class FilterThresholds:
    """筛选阈值，可通过 CLI 覆盖。"""
    relative_weakness_min_others: float = 0.8   # 对比模型中位数下限
    relative_weakness_gap: float = 0.2          # 目标落后幅度
    all_low: float = 0.4                         # 全员低分阈值
    absolute_low: float = 0.8                    # 单模型绝对阈值


def _score_map(m: ModelResult) -> Dict[str, float]:
    return {t.task_id: t.score for t in m.tasks}


def filter_tasks_to_analyze(
    models: List[ModelResult],
    target_model: str,
    thresholds: Optional[FilterThresholds] = None,
) -> List[Dict]:
    """
    返回待深度分析任务列表：[{"task_id": str, "reason": str}]
    reason ∈ {relative_weakness, all_low, absolute_low}
    """
    th = thresholds or FilterThresholds()
    target = next((m for m in models if m.model == target_model), None)
    if target is None:
        raise ValueError(f"目标模型不存在: {target_model}")

    others = [m for m in models if m.model != target_model]
    target_scores = _score_map(target)
    picked = []

    # 单模型回退：绝对阈值
    if not others:
        for tid, score in target_scores.items():
            if score < th.absolute_low:
                picked.append({"task_id": tid, "reason": "absolute_low"})
        return picked

    other_maps = [_score_map(m) for m in others]
    for tid, t_score in target_scores.items():
        other_scores = [om[tid] for om in other_maps if tid in om]
        if not other_scores:
            continue

        # 全员低分优先：task 对所有模型都困难，不属于个性短板
        if t_score < th.all_low and all(s < th.all_low for s in other_scores):
            picked.append({"task_id": tid, "reason": "all_low"})
            continue

        # 相对短板：目标明显落后于对比模型
        others_median = median(other_scores)
        if (others_median >= th.relative_weakness_min_others
                and (others_median - t_score) >= th.relative_weakness_gap):
            picked.append({"task_id": tid, "reason": "relative_weakness"})

    return picked
