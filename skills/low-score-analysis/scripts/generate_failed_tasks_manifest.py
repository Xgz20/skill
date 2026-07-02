#!/usr/bin/env python3
"""
生成低分（失分）任务清单 JSON —— 低分任务根因分析 Skill 的中间过程解析脚本（PinchBench 版）。

读取某模型的评测结果 JSON（如 0002_xsparkx2flash.json），按「主口径 + 高波动专项」双通道
选取任务：主口径取三轮平均分 < 阈值的低分任务；高波动专项取平均分≥阈值但极差(max-min)≥波动阈值
的不稳定任务。为每个任务汇总其根因分析所需的全部输入路径（任务文件、grading 详情、transcript.jsonl），
并用 low_score_type 字段标注归属，输出一份清单 JSON，供后续 workflow 并发分析使用。

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


def extract_failed_tasks(result_json: Path, threshold: float, tasks_dir: Path = None,
                         variance_threshold: float = 0.50) -> List[Dict[str, Any]]:
    """从评测结果 JSON 中提取需分析的任务。

    采用「主口径 + 高波动专项」双通道选取：
      - 主口径（low）：三轮平均分 < threshold，即真正拉低模型得分的低分任务；
      - 高波动专项（high_variance）：平均分 ≥ threshold 但极差(max-min) ≥ variance_threshold，
        即"某轮偶发塌陷、整体尚可"的稳定性缺陷（如 [100,0,100]）。
    两通道并集送入分析；每个任务用 low_score_type 字段标注归属，供报告分章。
    """
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

        # 计算均分 / 极差
        scores = [run.get("score", 1.0) for run in runs]
        min_score = min(scores)
        max_score = max(scores)
        avg_score = grading.get("mean")
        if avg_score is None:
            avg_score = sum(scores) / len(scores)
        score_range = max_score - min_score

        # 双通道选取：主口径(均分<阈值) 或 高波动专项(均分≥阈值但极差≥波动阈值)
        is_low = avg_score < threshold
        # 减 1e-9 避免浮点误差把恰好等于阈值的极差（如 0.95-0.45）判为略小于阈值而漏选
        is_high_var = (not is_low) and (score_range >= variance_threshold - 1e-9)
        if not (is_low or is_high_var):
            continue
        low_score_type = "low" if is_low else "high_variance"

        seen_tasks.add(tid)

        # 任务文件路径
        task_file = ""
        if tasks_dir:
            task_md = tasks_dir / f"{tid}.md"
            if task_md.exists():
                task_file = str(task_md)

        # transcript 路径（多轮场景枚举所有 run，单轮回退旧命名）
        transcript_paths = []
        transcript_total_kb = 0.0
        if transcripts_dir:
            # 先尝试多轮命名 {tid}_run{N}.jsonl
            runs_per_task = len(runs)
            found_multi = False
            for i in range(runs_per_task):
                transcript_jsonl = transcripts_dir / f"{tid}_run{i + 1}.jsonl"
                if transcript_jsonl.exists():
                    transcript_paths.append(str(transcript_jsonl))
                    transcript_total_kb += transcript_jsonl.stat().st_size / 1024
                    found_multi = True
            # 回退旧单轮命名
            if not found_multi:
                transcript_jsonl = transcripts_dir / f"{tid}.jsonl"
                if transcript_jsonl.exists():
                    transcript_paths.append(str(transcript_jsonl))
                    transcript_total_kb += transcript_jsonl.stat().st_size / 1024

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
            "low_score_type": low_score_type,  # "low"=均分<阈值主口径 / "high_variance"=高波动专项
            "score_pct": round(avg_score * 100, 1),  # 三轮平均分（主口径依据）
            "min_score_pct": round(min_score * 100, 1),
            "max_score_pct": round(max_score * 100, 1),
            "score_range_pct": round(score_range * 100, 1),  # 极差 max-min，衡量稳定性
            "task_file": task_file,
            "grading_detail": {
                "grading_runs": all_runs_detail,  # 嵌套结构：与 simplify_task / workflow_template.js 对齐
            },
            # 兼容字段：多轮时 transcript=首轮，transcripts=全部轮次列表
            "transcript": transcript_paths[0] if transcript_paths else "",
            "transcripts": transcript_paths,  # 按 run1..runN 顺序，单轮场景为单元素
            "transcript_kb": round(transcript_total_kb, 1),
            "category": task.get("category", ""),
        })

    return bundles


def main():
    parser = argparse.ArgumentParser(
        description="生成低分任务清单 JSON（低分任务根因分析 Skill 的中间过程解析脚本 - PinchBench 版）",
        epilog="""
使用示例：
  # 多模型根目录模式（需要指定 --model）
  python3 generate_failed_tasks_manifest.py \\
    --result-root /path/to/results \\
    --model xsparkx2flash-530

  # 单模型目录模式（直接指定模型目录，--model 可省略）
  python3 generate_failed_tasks_manifest.py \\
    --result-root /path/to/results/xsparkx2flash-530
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--result-root", required=True,
                        help="评测结果根目录（可以是包含多个模型子目录的根目录，也可以直接是某个模型目录）")
    parser.add_argument("--model", default=None,
                        help="模型目录名（可选）。多模型根目录模式时必须指定；单模型目录模式时可省略")
    parser.add_argument("--threshold", type=float, default=60,
                        help="低分阈值（百分制），三轮平均分低于此值的任务列入「低分主口径」，默认 60")
    parser.add_argument("--variance-threshold", type=float, default=50,
                        help="高波动阈值（百分制），均分≥阈值但极差(max-min)≥此值的任务列入「高波动专项」，默认 50")
    parser.add_argument("--workspace-dir", default=None,
                        help="输出工作区目录（可选）。未指定时，多模型模式默认 <result-root>/report-workspace，单模型模式默认 <model-dir>/report-workspace")
    parser.add_argument("--output", default=None,
                        help="输出 JSON 路径，默认 <workspace-dir>/_failed_tasks_<model>.json")
    parser.add_argument("--tasks-dir", default=None,
                        help="任务文件所在目录，默认自动定位 skill/tasks")
    args = parser.parse_args()

    result_root = Path(args.result_root).resolve()

    # 智能判断：如果 result_root 本身就包含评测结果 JSON，说明用户直接指定了模型目录
    # 这种情况下，workspace 应该在模型目录内，而不是在父目录
    result_json_in_root = find_result_json(result_root)
    if result_json_in_root:
        # 场景：用户直接指定模型目录
        # 例如：--result-root /path/to/results/debug-001
        # 此时 result_root 本身就是模型目录
        model_dir = result_root
        # workspace 默认在模型目录内（除非用户显式指定 --workspace-dir）
        default_workspace = result_root / "report-workspace"
        print(f"检测到单模型目录模式: {result_root.name}")
        print(f"忽略 --model 参数（如果提供）")
    else:
        # 场景：多模型根目录
        # 例如：--result-root /path/to/results，--model debug-001
        # 此时 model_dir = result_root / model
        model_dir = result_root / args.model
        if not model_dir.exists():
            sys.exit(f"错误: 模型目录不存在: {model_dir}")
        # workspace 默认在根目录下（与所有模型目录平级）
        default_workspace = result_root / "report-workspace"
        print(f"检测到多模型根目录模式")

    # 查找评测结果 JSON
    result_json = find_result_json(model_dir)
    if not result_json:
        sys.exit(f"错误: 在 {model_dir} 中找不到评测结果 JSON 文件")

    print(f"使用评测结果文件: {result_json.name}")

    # 工作区目录：显式指定 > 自动判断的默认位置
    workspace = Path(args.workspace_dir).resolve() if args.workspace_dir else default_workspace

    # 输出文件名：优先使用实际模型名，回退到目录名
    with open(result_json, encoding="utf-8") as f_temp:
        data_temp = json.load(f_temp)
    model_name_for_file = data_temp.get("model", "") or args.model or model_dir.name

    out = Path(args.output).resolve() if args.output \
        else workspace / f"_failed_tasks_{model_name_for_file}.json"
    out.parent.mkdir(parents=True, exist_ok=True)

    tasks_dir = find_tasks_dir(args.tasks_dir)
    threshold = args.threshold / 100.0
    variance_threshold = args.variance_threshold / 100.0

    bundles = extract_failed_tasks(result_json, threshold, tasks_dir, variance_threshold)
    # 主口径任务在前、高波动专项在后；组内按均分升序
    bundles.sort(key=lambda b: (0 if b["low_score_type"] == "low" else 1, b["score_pct"]))

    # 计算统计信息
    with open(result_json, encoding="utf-8") as f:
        data = json.load(f)
    total_tasks = len(set(t["task_id"] for t in data.get("tasks", [])))
    model_name = data.get("model", "")  # 从 JSON 中读取真实模型名

    with open(out, "w", encoding="utf-8") as f:
        json.dump(bundles, f, ensure_ascii=False, indent=2)

    # 输出统计信息
    print(f"\n模型目录: {model_dir}")
    print(f"实际模型名: {model_name}")
    if args.model and model_name != args.model:
        print(f"  ⚠️  注意：--model 参数 '{args.model}' 与实际模型名不同")
    print(f"工作区目录: {workspace}")
    n_low = sum(1 for b in bundles if b["low_score_type"] == "low")
    n_var = sum(1 for b in bundles if b["low_score_type"] == "high_variance")
    print(f"低分任务数（均分<{args.threshold}%，主口径）: {n_low} / {total_tasks}")
    print(f"高波动任务数（均分≥{args.threshold}% 但极差≥{args.variance_threshold}%，稳定性专项）: {n_var}")
    print(f"合计送分析: {len(bundles)}")
    print(f"任务文件目录: {tasks_dir or '(未定位，task_file 留空)'}")
    print(f"清单已写入: {out}")
    print(f"\n按类别统计（主口径低分任务）：")
    categories = {}
    for b in bundles:
        if b["low_score_type"] != "low":
            continue
        cat = b["category"] or "未分类"
        categories[cat] = categories.get(cat, 0) + 1
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

    # 末行输出清单路径，便于上层脚本/Skill 捕获
    print(f"\nMANIFEST_PATH={out}")

    # 💡 提示正确的分析文件命名（用于后续回填 Excel）
    if model_name:
        print(f"\n💡 提示：如需回填 Excel 报告，请确保分析文件名包含模型名 '{model_name}'")
        print(f"   建议命名: analysis_{model_name}.json")
        print(f"   分析文件将保存到: {workspace / f'analysis_{model_name}.json'}")


if __name__ == "__main__":
    main()
