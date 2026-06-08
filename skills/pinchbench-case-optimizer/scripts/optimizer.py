#!/usr/bin/env python3
"""
PinchBench 评测用例优化器

职责：
1. 读取批量评测结果 + transcripts
2. 五维度分析（C/D/E自动 + A/B数据准备供LLM分析）
3. 家族识别与基线对比
4. 生成优化用例 + 详细报告
5. 收敛检测

CLI 用法（analyze 阶段）：
    python optimizer.py <task_id> [--results-dir DIR] [--dump-analysis]

完整端到端是两阶段 Python API（不是单个 CLI）：
    1. opt_data = run_optimization(task_input, results_dir)
       → 自动完成 C/D/E 维度，返回 LLM 待分析数据包
    2. （由上层 Skill agent 调用 LLM 完成 A/B 维度并生成优化用例内容）
    3. finalize_optimization(opt_data, full_analysis, optimized_content)
       → 写入优化用例 + 生成报告 + 收敛检测
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))
from path_resolver import (
    resolve_task_path,
    extract_base_task_id,
    extract_optimization_round,
)

from result_collector import (
    find_latest_round,
    collect_model_results,
    find_previous_round_results,
    load_transcript,
)
from analyzers import (
    analyze_difficulty,
    analyze_timeout,
    analyze_tool_usage,
    prepare_llm_analysis_data,
)
from convergence import check_convergence
from report_generator import generate_report
from task_io import load_task_markdown, get_output_path


def run_optimization(
    task_input: str,
    results_dir: Optional[str] = None,
) -> Dict:
    """
    执行用例优化分析，输出分析数据供 LLM 进一步处理。

    Args:
        task_input: 用例输入（task_id 或路径）
        results_dir: 评测结果目录（None 表示自动读取最新）

    Returns:
        优化分析数据包，含五维度分析、LLM输入、路径信息
    """
    # __file__ 是 skills/pinchbench-case-optimizer/scripts/optimizer.py
    # project_root 是 skill/（skills/ 的上一级）
    project_root = Path(__file__).parent.parent.parent.parent

    # 1. 加载源用例
    source = resolve_task_path(task_input, project_root)
    task_id = source.stem
    base_task_id = extract_base_task_id(task_id)
    optimization_round = extract_optimization_round(task_id)
    original_task = load_task_markdown(source)
    print(f"📋 源用例: {task_id} ({source})")

    # 2. 确定结果目录
    if results_dir is None:
        results_path = find_latest_round(
            project_root / "results-auto" / task_id
        )
        if results_path is None:
            print(f"❌ 未找到 {task_id} 的评测结果，请先运行 batch-runner")
            sys.exit(1)
    else:
        results_path = Path(results_dir)
        if not results_path.is_absolute():
            results_path = project_root / results_path

    print(f"📂 评测结果: {results_path}")

    # 3. 收集模型结果 + 加载 transcripts
    model_results = collect_model_results(results_path)
    for r in model_results:
        r["transcript"] = load_transcript(r.get("transcript_path"))

    print(f"📊 收集到 {len(model_results)} 个模型的结果")

    # 4. 加载基线（家族上一版本）
    prev_results_path = find_previous_round_results(task_id, project_root)
    prev_score_mean = None
    if prev_results_path:
        prev_results = collect_model_results(prev_results_path)
        if prev_results:
            prev_score_mean = sum(r["score"] for r in prev_results) / len(prev_results)
        print(f"📈 基线: {prev_results_path}（均分 {prev_score_mean:.3f}）")

    # 5. 五维度分析（C/D/E 自动）
    analysis = {
        # A/B 维度先占位，由 LLM 分析后填充
        "prompt_clarity": {
            "has_issue": None,
            "summary": "待LLM分析（见 llm_analysis_data）",
            "details": {},
        },
        "grading_validity": {
            "has_issue": None,
            "summary": "待LLM分析（见 llm_analysis_data）",
            "details": {},
        },
        "difficulty": analyze_difficulty(model_results),
        "timeout": analyze_timeout(model_results),
        "tool_usage": analyze_tool_usage(model_results),
    }

    # 6. 准备 LLM 分析数据（维度 A/B）
    llm_data = prepare_llm_analysis_data(
        {"prompt": original_task["body"],
         "grading": original_task["frontmatter"].get("grading", {})},
        model_results,
    )

    # 7. 当前轮均分
    current_score_mean = (
        sum(r["score"] for r in model_results) / len(model_results)
        if model_results else 0.0
    )

    # 8. 计算输出路径
    new_round = optimization_round + 1
    output_task_path = get_output_path(source, base_task_id, new_round)
    report_path = (
        project_root / "optimization-reports" / base_task_id
        / f"{base_task_id}_r{new_round}_report.md"
    )

    return {
        "task_id": task_id,
        "base_task_id": base_task_id,
        "optimization_round": optimization_round,
        "new_round": new_round,
        "source_path": source,
        "original_task": original_task,
        "model_results": model_results,
        "analysis": analysis,
        "llm_analysis_data": llm_data,
        "current_score_mean": current_score_mean,
        "prev_score_mean": prev_score_mean,
        "output_task_path": output_task_path,
        "report_path": report_path,
    }


def finalize_optimization(
    opt_data: Dict,
    analysis: Dict,
    optimized_task_content: str,
    judge_model: str = "anthropic/claude-sonnet-4-6",
) -> Dict:
    """
    完成优化：写入优化用例和报告，执行收敛检测。

    在 LLM 完成维度 A/B 分析并生成优化用例后调用。

    Args:
        opt_data: run_optimization 返回的数据包
        analysis: 完整的五维度分析（A/B 已由 LLM 填充）
        optimized_task_content: LLM 生成的优化用例完整内容
        judge_model: 裁判模型

    Returns:
        {output_task_path, report_path, convergence}
    """
    # 断言 A/B 已由 LLM 填充（has_issue 不能是 None）
    for dim in ("prompt_clarity", "grading_validity"):
        if analysis.get(dim, {}).get("has_issue") is None:
            raise ValueError(
                f"维度 {dim} 的 has_issue 仍为 None，"
                f"finalize 前必须先由 LLM 完成 A/B 维度分析"
            )

    from task_io import write_optimized_task

    # 1. 写入优化用例
    write_optimized_task(opt_data["output_task_path"], optimized_task_content)

    # 2. 收敛检测
    convergence = check_convergence(
        round_num=opt_data["new_round"],
        current_analysis=analysis,
        prev_score_mean=opt_data["prev_score_mean"],
        current_score_mean=opt_data["current_score_mean"],
    )

    # 3. 生成报告
    generate_report(
        report_path=opt_data["report_path"],
        task_id=opt_data["task_id"],
        round_num=opt_data["new_round"],
        model_results=opt_data["model_results"],
        analysis=analysis,
        convergence=convergence,
        judge_model=judge_model,
    )

    return {
        "output_task_path": opt_data["output_task_path"],
        "report_path": opt_data["report_path"],
        "convergence": convergence,
    }


def main():
    """命令行入口：输出分析数据为 JSON，供调用方处理。"""
    parser = argparse.ArgumentParser(description="PinchBench 评测用例优化器")
    parser.add_argument("task", help="用例输入（task_id 或文件路径）")
    parser.add_argument(
        "--results-dir",
        default=None,
        help="评测结果目录（默认自动读取最新轮次）",
    )
    parser.add_argument(
        "--dump-analysis",
        action="store_true",
        help="输出分析数据为 JSON（供 LLM 处理）",
    )

    args = parser.parse_args()
    opt_data = run_optimization(args.task, args.results_dir)

    if args.dump_analysis:
        # 序列化（排除不可序列化的 Path 和 transcript）
        dumpable = {
            "task_id": opt_data["task_id"],
            "base_task_id": opt_data["base_task_id"],
            "new_round": opt_data["new_round"],
            "analysis": opt_data["analysis"],
            "llm_analysis_data": opt_data["llm_analysis_data"],
            "current_score_mean": opt_data["current_score_mean"],
            "prev_score_mean": opt_data["prev_score_mean"],
            "output_task_path": str(opt_data["output_task_path"]),
            "report_path": str(opt_data["report_path"]),
        }
        print(json.dumps(dumpable, ensure_ascii=False, indent=2))
    else:
        print(f"\n✅ 分析完成")
        print(f"📝 优化用例将输出到: {opt_data['output_task_path']}")
        print(f"📊 报告将输出到: {opt_data['report_path']}")
        print(f"\n维度C（难度）: {opt_data['analysis']['difficulty']['summary']}")
        print(f"维度D（超时）: {opt_data['analysis']['timeout']['summary']}")
        print(f"维度E（工具）: {opt_data['analysis']['tool_usage']['summary']}")


if __name__ == "__main__":
    main()
