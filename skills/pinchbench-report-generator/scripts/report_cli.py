"""CLI 入口：collect / render 子命令。"""
import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from collect import build_collected_data
from task_filter import FilterThresholds
from report_renderer import render_report, build_filename


def _parse_thresholds(s: Optional[str]) -> Optional[FilterThresholds]:
    """解析 'all_low=0.4,gap=0.2' 形式的阈值覆盖。"""
    if not s:
        return None
    th = FilterThresholds()
    mapping = {
        "relative_weakness_min_others": "relative_weakness_min_others",
        "min_others": "relative_weakness_min_others",
        "gap": "relative_weakness_gap",
        "all_low": "all_low",
        "absolute": "absolute_low",
        "strength_min": "relative_strength_min",
        "strength_gap": "relative_strength_gap",
        "absolute_high": "absolute_high",
        "strength_top_n": "strength_top_n",
    }
    int_attrs = {"strength_top_n"}
    for pair in s.split(","):
        k, _, v = pair.partition("=")
        k = k.strip()
        if not v:
            print(f"警告：忽略无效阈值对 '{pair}'", file=sys.stderr)
            continue
        attr = mapping.get(k)
        if attr:
            caster = int if attr in int_attrs else float
            try:
                setattr(th, attr, caster(v))
            except ValueError:
                print(f"错误：阈值 '{k}' 需要数值，收到 '{v}'", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"警告：未知阈值键 '{k}'，可用: min_others, gap, all_low, absolute, "
                  f"strength_min, strength_gap, absolute_high, strength_top_n", file=sys.stderr)
    return th


def cmd_collect(inputs: List[str], target_model: str, tasks_root: str,
                output: str, thresholds: Optional[str] = None):
    """阶段1：收集数据写 collected_data.json。"""
    try:
        data = build_collected_data(
            [Path(p) for p in inputs], target_model, Path(tasks_root),
            _parse_thresholds(thresholds))
    except (ValueError, FileNotFoundError, OSError) as e:
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(1)

    try:
        Path(output).write_text(json.dumps(data, ensure_ascii=False, indent=2))
    except (TypeError, OSError) as e:
        print(f"错误：无法写入数据到 {output}: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"collected_data 已写入: {output}")
    print(f"待深度分析任务数: {len(data['tasks_to_analyze'])}")
    print(f"待深度分析优势任务数: {len(data.get('strengths_to_analyze', []))}")


def cmd_render(collected_data: str, analysis: str, output: str):
    """阶段3：读 collected_data + analysis 渲染报告。"""
    try:
        data = json.loads(Path(collected_data).read_text())
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"错误：无法读取 collected_data {collected_data}: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        ana = json.loads(Path(analysis).read_text()) if Path(analysis).exists() else {}
    except json.JSONDecodeError as e:
        print(f"错误：analysis JSON 格式错误 {analysis}: {e}", file=sys.stderr)
        sys.exit(1)

    md = render_report(data, ana)
    out_path = Path(output)
    if out_path.is_dir():
        out_path = out_path / build_filename(data)

    try:
        out_path.write_text(md)
    except OSError as e:
        print(f"错误：无法写入报告到 {out_path}: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"报告已写入: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="PinchBench 评测报告生成器")
    sub = parser.add_subparsers(dest="command", required=True)

    pc = sub.add_parser("collect", help="阶段1：收集数据")
    pc.add_argument("inputs", nargs="+", help="评测结果目录（总目录或多个模型目录）")
    pc.add_argument("--target-model", default="xsparkx2flash")
    pc.add_argument("--tasks-root", default="tasks", help="任务 md 根目录")
    pc.add_argument("--output", default="collected_data.json")
    pc.add_argument("--thresholds", default=None,
                    help="如 all_low=0.4,gap=0.2,strength_min=0.8,strength_top_n=12")

    pr = sub.add_parser("render", help="阶段3：渲染报告")
    pr.add_argument("--collected-data", required=True)
    pr.add_argument("--analysis", required=True)
    pr.add_argument("--output", required=True, help="输出文件或目录")

    args = parser.parse_args()
    if args.command == "collect":
        cmd_collect(args.inputs, args.target_model, args.tasks_root,
                    args.output, args.thresholds)
    elif args.command == "render":
        cmd_render(args.collected_data, args.analysis, args.output)


if __name__ == "__main__":
    main()
