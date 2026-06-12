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


# ---- 难度等级维度统计 ----

# 难度排序键：L1<L2<L3<L4<unknown，保证渲染顺序稳定
_DIFFICULTY_ORDER = {"L1": 1, "L2": 2, "L3": 3, "L4": 4, "unknown": 99}


def _difficulty_sort_key(d: str) -> int:
    return _DIFFICULTY_ORDER.get(d, 50)


def build_difficulty_summary(models: List[ModelResult]) -> List[Dict]:
    """
    按难度等级聚合各模型得分。任务编排以第一个模型为准（同一 suite 内任务集合一致）。

    Returns: [{
        "difficulty": "L1"|"L2"|...,
        "task_count": int,
        "scores": {model: mean_score},
        "totals": {model: sum_score},   # 累计分（report 用 "5.90/6" 形式展示）
        "best_model": model_key,
        "score_range": float,           # 得分率极差 = max - min
    }]
    """
    if not models:
        return []

    # 收集所有出现过的难度（以任意模型的任务列表为准——所有模型 suite 一致即可）
    diffs = sorted({t.difficulty for m in models for t in m.tasks},
                   key=_difficulty_sort_key)

    rows: List[Dict] = []
    for d in diffs:
        # 任务数取首个有该难度任务的模型计数（不同模型 suite 应一致）
        task_count = max((sum(1 for t in m.tasks if t.difficulty == d)
                          for m in models), default=0)
        if task_count == 0:
            continue

        scores: Dict[str, float] = {}
        totals: Dict[str, float] = {}
        for m in models:
            ds = [t.score for t in m.tasks if t.difficulty == d]
            scores[m.model] = mean(ds) if ds else 0.0
            totals[m.model] = sum(ds)

        best = max(scores, key=lambda k: (scores[k], _neg_key(k))) if scores else ""
        score_values = list(scores.values())
        rng = (max(score_values) - min(score_values)) if score_values else 0.0
        rows.append({
            "difficulty": d,
            "task_count": task_count,
            "scores": scores,
            "totals": totals,
            "best_model": best,
            "score_range": rng,
        })
    return rows


def highest_difficulty(rows: List[Dict]) -> str:
    """返回最高难度等级（用于 3.3 章节展开），跳过 unknown。"""
    real = [r for r in rows if r["difficulty"] != "unknown"]
    if not real:
        return ""
    # 取 _DIFFICULTY_ORDER 最大但不为 unknown 的
    return max(real, key=lambda r: _difficulty_sort_key(r["difficulty"]))["difficulty"]
