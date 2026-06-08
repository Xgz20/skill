"""收敛检测：判断多轮优化是否应停止（混合方式）。"""
from typing import Dict, List, Optional


def count_issues(analysis: Dict) -> int:
    """统计五维度中有问题的维度数量。"""
    return sum(
        1 for dim in analysis.values()
        if isinstance(dim, dict) and dim.get("has_issue", False)
    )


def check_convergence(
    round_num: int,
    current_analysis: Dict,
    prev_score_mean: Optional[float] = None,
    current_score_mean: Optional[float] = None,
    max_rounds: int = 5,
) -> Dict:
    """
    收敛检测：给出停止建议，最终由用户决定。

    检测信号：
    1. 无新问题发现
    2. 与上轮对比改进幅度 < 0.05
    3. 达到最大轮次限制

    Args:
        round_num: 当前优化轮次
        current_analysis: 五维度分析结果
        prev_score_mean: 上一轮平均分（用于对比）
        current_score_mean: 当前轮平均分
        max_rounds: 最大轮次限制

    Returns:
        {converged, signals, issue_count, recommendation}
    """
    signals: List[str] = []

    # 信号1：无新问题
    issue_count = count_issues(current_analysis)
    if issue_count == 0:
        signals.append("无新问题发现")

    # 信号2：与上轮对比改进幅度
    if prev_score_mean is not None and current_score_mean is not None:
        improvement = current_score_mean - prev_score_mean
        if abs(improvement) < 0.05:
            signals.append(f"分数提升{improvement:+.3f}，趋于收敛")

    # 信号3：最大轮次
    if round_num >= max_rounds:
        signals.append(f"达到最大轮次限制（{max_rounds}）")

    converged = len(signals) > 0

    return {
        "converged": converged,
        "signals": signals,
        "issue_count": issue_count,
        "recommendation": "建议停止" if converged else "建议继续优化",
    }
