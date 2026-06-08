"""统计指标计算：得分率、分类别、排名、Token 效率。"""
from collections import defaultdict
from statistics import mean
from typing import Dict, List

from models import ModelResult

HIGH_THRESHOLD = 0.95   # ≥95% 优秀覆盖面
LOW_THRESHOLD = 0.60    # <60% 明显短板


def _neg_key(name: str):
    """用于平局时按字母序取最小：返回可反向比较的键。"""
    # max 取 (score, _neg_key) 最大；字母序越小的名字应排在前，
    # 故对每个字符取负序，等价于让字母序小的 _neg_key 更大。
    return tuple(-ord(c) for c in name)


def overall_score_rate(m: ModelResult) -> float:
    """总得分率 = 各任务得分均值。"""
    if not m.tasks:
        return 0.0
    return mean(t.score for t in m.tasks)


def category_scores(m: ModelResult) -> Dict[str, float]:
    """按 category 分组求均值。"""
    groups: Dict[str, List[float]] = defaultdict(list)
    for t in m.tasks:
        groups[t.category].append(t.score)
    return {cat: mean(scores) for cat, scores in groups.items()}


def count_high_tasks(m: ModelResult) -> int:
    """得分率 ≥ HIGH_THRESHOLD 的任务数。"""
    return sum(1 for t in m.tasks if t.score >= HIGH_THRESHOLD)


def count_low_tasks(m: ModelResult) -> int:
    """得分率 < LOW_THRESHOLD 的任务数。"""
    return sum(1 for t in m.tasks if t.score < LOW_THRESHOLD)


def token_efficiency(m: ModelResult) -> float:
    """每 token 得分 = 总得分率 / 总 token。"""
    total = m.total_tokens
    if total == 0:
        return 0.0
    return overall_score_rate(m) / total


def build_category_summary(models: List[ModelResult]) -> List[Dict]:
    """
    生成分类别汇总：每类别一行，含各模型得分和最优模型。

    Returns: [{"category": str, "scores": {model: float}, "best_model": str}]
    """
    all_cats = sorted({t.category for m in models for t in m.tasks})
    rows = []
    for cat in all_cats:
        scores = {}
        for m in models:
            cat_tasks = [t.score for t in m.tasks if t.category == cat]
            scores[m.model] = mean(cat_tasks) if cat_tasks else 0.0
        # 平局时按模型名字母序取最小，保证报告可复现
        best = max(scores, key=lambda k: (scores[k], _neg_key(k))) if scores else ""
        rows.append({"category": cat, "scores": scores, "best_model": best})
    return rows


def rank_models(models: List[ModelResult]) -> List[ModelResult]:
    """按总得分率降序排名。"""
    return sorted(models, key=overall_score_rate, reverse=True)
