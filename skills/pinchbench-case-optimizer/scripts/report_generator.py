"""详细优化报告生成器。"""
from pathlib import Path
from typing import Dict, List


def format_model_overview(model_results: List[Dict]) -> str:
    """格式化模型表现总览表格。"""
    lines = [
        "| 模型 | 得分 | 用时 | 是否超时 | Token消耗 |",
        "|------|------|------|----------|-----------|",
    ]
    for r in model_results:
        tokens = r.get("usage", {}).get("total_tokens", "N/A")
        timed_out = "是" if r.get("timed_out") else "否"
        exec_time = r.get("execution_time")
        time_str = f"{exec_time:.1f}s" if exec_time is not None else "N/A"
        lines.append(
            f"| {r['model']} | {r['score']:.2f} | {time_str} | {timed_out} | {tokens} |"
        )
    return "\n".join(lines)


def _format_dimension(title: str, dim_key: str, analysis: Dict) -> str:
    """格式化单个维度的分析章节。"""
    dim = analysis.get(dim_key, {})
    has_issue = dim.get("has_issue", False)
    summary = dim.get("summary", "无数据")
    details = dim.get("details", {})

    status = "⚠️ 发现问题" if has_issue else "✅ 正常"

    section = f"## {title}\n\n"
    section += f"**状态**: {status}\n\n"
    section += f"**分析**: {summary}\n\n"

    if details:
        section += "**详细数据**:\n\n```\n"
        for k, v in details.items():
            section += f"{k}: {v}\n"
        section += "```\n\n"

    return section


def generate_report(
    report_path: Path,
    task_id: str,
    round_num: int,
    model_results: List[Dict],
    analysis: Dict,
    convergence: Dict,
    judge_model: str,
):
    """
    生成详细优化报告（详细分析版）。

    Args:
        report_path: 报告输出路径
        task_id: 用例 ID
        round_num: 优化轮次
        model_results: 模型评测结果
        analysis: 五维度分析结果
        convergence: 收敛检测结果
        judge_model: 裁判模型
    """
    report_path.parent.mkdir(parents=True, exist_ok=True)

    content = f"# 评测用例优化报告 - {task_id} (Round {round_num})\n\n"

    # 执行概览
    content += "## 执行概览\n\n"
    content += f"- **优化轮次**: Round {round_num}\n"
    content += f"- **参与模型**: {', '.join(r['model'] for r in model_results)}\n"
    content += f"- **裁判模型**: {judge_model}\n\n"

    # 模型表现总览
    content += "## 模型表现总览\n\n"
    content += format_model_overview(model_results) + "\n\n"

    # 七维度分析
    content += _format_dimension("维度A：Prompt清晰度分析", "prompt_clarity", analysis)
    content += _format_dimension("维度B：评分标准合理性", "grading_validity", analysis)
    content += _format_dimension("维度C：难度区分度", "difficulty", analysis)
    content += _format_dimension("维度D：超时设置", "timeout", analysis)
    content += _format_dimension("维度E：工具使用合理性", "tool_usage", analysis)
    content += _format_dimension("维度F：Capabilities 标注准确性", "capabilities_validity", analysis)
    content += _format_dimension("维度G：Difficulty 准确性", "difficulty_accuracy", analysis)

    # 收敛性判断
    content += "## 收敛性判断\n\n"
    content += f"- **本轮发现问题数**: {convergence['issue_count']}\n"
    if convergence["signals"]:
        content += f"- **收敛信号**: {'; '.join(convergence['signals'])}\n"
    content += f"- **建议**: {convergence['recommendation']}\n\n"

    report_path.write_text(content)
