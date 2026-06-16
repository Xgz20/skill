#!/usr/bin/env python3
"""
生成低分（失分）任务清单 JSON —— 低分任务根因分析 Skill 的中间过程解析脚本（PinchBench 版）。

读取某模型的评测结果 JSON（如 0002_xsparkx2flash.json），筛出任意一轮 score 低于阈值的任务，
为每个任务汇总其根因分析所需的全部输入路径（任务文件、grading 详情、transcript.jsonl），
输出一份清单 JSON，供后续 workflow 并发分析使用。

用法:
  python3 generate_failed_tasks_manifest.py \
      --result-root /path/to/astronclaw-result/all-suite/round-3 \
      --model xsparkx2flash-530 \
      --threshold 60

默认输出到 <result-root>/report-workspace/_failed_tasks_<model>.json
可用 --output 显式指定输出文件，用 --tasks-dir 指定任务文件所在目录。
"""
import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any


def find_tasks_dir(explicit: str = None) -> Path:
    """定位任务文件根目录 skill/tasks。
    优先用 --tasks-dir；否则从脚本位置向上回溯查找仓库内的 skill/tasks 目录。
    找不到返回 None（清单里的 task_file 字段则留空，不影响 grading/transcript 分析）。
    """
    if explicit:
        p = Path(explicit)
        return p if p.exists() else None
    # 从脚本位置向上找 skill/tasks
    here = Path(__file__).resolve()
    for base in here.parents:
        cand = base / "skill" / "tasks"
        if cand.is_dir():
            return cand
    return None


def find_result_json(model_dir: Path) -> Path:
    """在模型目录下查找评测结果 JSON 文件（如 0002_xsparkx2flash.json）"""
    # 查找 *.json 文件（排除可能的其他辅助 json）
    json_files = list(model_dir.glob("*.json"))
    if not json_files:
        return None
    # 优先选择包含模型名的 json，否则取第一个
    model_name = model_dir.name.split('-')[0]  # xsparkx2flash-530 -> xsparkx2flash
    for jf in json_files:
        if model_name in jf.name:
            return jf
    return json_files[0]


def extract_failed_tasks(result_json: Path, threshold: float, tasks_dir: Path = None) -> List[Dict[str, Any]]:
    """从评测结果 JSON 中提取低分任务"""
    with open(result_json, encoding="utf-8") as f:
        data = json.load(f)

    model_dir = result_json.parent
    transcripts_dir = None
    # 查找 transcripts 目录（可能是 0002_transcripts 这样的格式）
    for d in model_dir.iterdir():
        if d.is_dir() and 'transcript' in d.name:
            transcripts_dir = d
            break

    bundles = []
    seen_tasks = set()  # 用于去重（同一个 task_id 在 JSON 中可能重复出现多轮）

    for task in data.get("tasks", []):
        tid = task["task_id"]

        # 去重：每个 task_id 只处理一次
        if tid in seen_tasks:
            continue

        grading = task.get("grading", {})
        runs = grading.get("runs", [])
        if not runs:
            continue

        # 检查是否有任意一轮低于阈值
        min_score = min(run.get("score", 1.0) for run in runs)
        if min_score >= threshold:
            continue

        seen_tasks.add(tid)

        # 任务文件路径
        task_file = ""
        if tasks_dir:
            task_md = tasks_dir / f"{tid}.md"
            if task_md.exists():
                task_file = str(task_md)

        # transcript 路径
        transcript_path = ""
        if transcripts_dir:
            transcript_jsonl = transcripts_dir / f"{tid}.jsonl"
            if transcript_jsonl.exists():
                transcript_path = str(transcript_jsonl)

        # 计算平均分
        avg_score = grading.get("mean", min_score)

        # 收集所有轮次的 grading 详情（用于分析多轮不稳定性）
        all_runs_detail = []
        for i, run in enumerate(runs, 1):
            all_runs_detail.append({
                "run": i,
                "score": run.get("score", 0.0),
                "breakdown": run.get("breakdown", {}),
                "notes": run.get("notes", "")
            })

        bundles.append({
            "task_id": tid,
            "score_pct": round(avg_score * 100, 1),
            "min_score_pct": round(min_score * 100, 1),
            "task_file": task_file,
            "grading_runs": all_runs_detail,  # 所有轮次的详情
            "transcript": transcript_path,
            "transcript_kb": round(Path(transcript_path).stat().st_size / 1024, 1)
                              if transcript_path and Path(transcript_path).exists() else 0,
            "category": task.get("category", ""),
        })

    return bundles


def main():
    parser = argparse.ArgumentParser(
        description="生成低分任务清单 JSON（低分任务根因分析 Skill 的中间过程解析脚本 - PinchBench 版）")
    parser.add_argument("--result-root", required=True,
                        help="评测结果根目录（其下含各模型子目录）")
    parser.add_argument("--model", required=True,
                        help="模型目录名，如 xsparkx2flash-530")
    parser.add_argument("--threshold", type=float, default=60,
                        help="低分阈值（百分制），任意一轮 score 低于此值的任务列入清单，默认 60")
    parser.add_argument("--workspace-dir", default=None,
                        help="输出工作区目录，默认 <result-root>/report-workspace")
    parser.add_argument("--output", default=None,
                        help="输出 JSON 路径，默认 <workspace-dir>/_failed_tasks_<model>.json")
    parser.add_argument("--tasks-dir", default=None,
                        help="任务文件所在目录，默认自动定位 skill/tasks")
    args = parser.parse_args()

    result_root = Path(args.result_root).resolve()
    model_dir = result_root / args.model

    if not model_dir.exists():
        sys.exit(f"错误: 模型目录不存在: {model_dir}")

    # 查找评测结果 JSON
    result_json = find_result_json(model_dir)
    if not result_json:
        sys.exit(f"错误: 在 {model_dir} 中找不到评测结果 JSON 文件")

    print(f"使用评测结果文件: {result_json.name}")

    # 工作区目录：默认 result-root / report-workspace
    workspace = Path(args.workspace_dir).resolve() if args.workspace_dir \
        else result_root / "report-workspace"
    out = Path(args.output).resolve() if args.output \
        else workspace / f"_failed_tasks_{args.model}.json"
    out.parent.mkdir(parents=True, exist_ok=True)

    tasks_dir = find_tasks_dir(args.tasks_dir)
    threshold = args.threshold / 100.0

    bundles = extract_failed_tasks(result_json, threshold, tasks_dir)
    bundles.sort(key=lambda b: b["min_score_pct"])

    # 计算统计信息
    with open(result_json, encoding="utf-8") as f:
        data = json.load(f)
    total_tasks = len(set(t["task_id"] for t in data.get("tasks", [])))

    with open(out, "w", encoding="utf-8") as f:
        json.dump(bundles, f, ensure_ascii=False, indent=2)

    print(f"\n模型: {args.model}")
    print(f"低分任务数（任意轮<{args.threshold}%）: {len(bundles)} / {total_tasks}")
    print(f"任务文件目录: {tasks_dir or '(未定位，task_file 留空)'}")
    print(f"清单已写入: {out}")
    print(f"\n按类别统计：")
    categories = {}
    for b in bundles:
        cat = b["category"] or "未分类"
        categories[cat] = categories.get(cat, 0) + 1
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

    # 末行输出清单路径，便于上层脚本/Skill 捕获
    print(f"\nMANIFEST_PATH={out}")


if __name__ == "__main__":
    main()
