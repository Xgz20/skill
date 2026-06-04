#!/usr/bin/env python3
"""PinchBench 评测结果分析脚本，输出 Excel 报告。

支持两种模式：
1. 单文件模式（-i）：分析单个评测结果 JSON，输出「概览 + 明细」两个 Sheet。
2. 目录模式（-d）：递归扫描目录下所有 `0xxx_<modelid>.json` 格式的结果文件，
   汇总输出「对比 + 明细」两个 Sheet。
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
except ImportError:
    sys.exit("需要 openpyxl 库，请执行: pip install openpyxl")


# 形如 0004_xopdeepseekv4pro.json：0 开头 + 下划线 + 模型 id + .json
RESULT_FILE_PATTERN = re.compile(r"^0\w*_.+\.json$")

HEADER_FONT_WHITE = Font(bold=True, color="FFFFFF")
HEADER_FILL = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
CENTER = Alignment(horizontal="center")


def find_latest_result(results_dir: Path) -> Path:
    json_files = sorted(results_dir.glob("*.json"), key=lambda f: f.stat().st_mtime)
    if not json_files:
        sys.exit(f"未找到结果文件: {results_dir}")
    return json_files[-1]


def find_result_files(root: Path) -> list[Path]:
    """递归查找目录下所有符合命名规则的结果文件。"""
    return sorted(
        p for p in root.rglob("*.json") if RESULT_FILE_PATTERN.match(p.name)
    )


def load_result(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def style_header_row(ws, row: int, ncols: int):
    for col_idx in range(1, ncols + 1):
        cell = ws.cell(row=row, column=col_idx)
        cell.font = HEADER_FONT_WHITE
        cell.fill = HEADER_FILL
        cell.alignment = CENTER


# --------------------------------------------------------------------------- #
# 单文件模式
# --------------------------------------------------------------------------- #
def write_overview_sheet(wb: openpyxl.Workbook, data: dict):
    ws = wb.active
    ws.title = "概览"

    category_scores = data["category_scores"]
    total_score = sum(v["score"] for v in category_scores.values())
    total_max = sum(v["max_score"] for v in category_scores.values())
    overall_pct = (total_score / total_max * 100) if total_max > 0 else 0

    ws.append(["总分", f"{overall_pct:.1f}%", f"({total_score:.1f} / {total_max:.1f})"])
    ws["A1"].font = Font(bold=True)
    ws.append([])

    headers = ["类别", "得分", "满分", "得分率", "任务数"]
    ws.append(headers)
    style_header_row(ws, 3, len(headers))

    for category, scores in category_scores.items():
        ws.append([
            category,
            round(scores["score"], 3),
            round(scores["max_score"], 1),
            f"{scores['pct']:.1f}%",
            scores["task_count"],
        ])

    for col in range(1, 6):
        ws.column_dimensions[get_column_letter(col)].width = 16


def write_detail_sheet(wb: openpyxl.Workbook, data: dict):
    ws = wb.create_sheet("明细")

    headers = [
        "category", "task", "score",
        "input_tokens", "output_tokens",
        "cache_read_tokens", "cache_write_tokens",
        "total_tokens", "request_count",
    ]
    ws.append(headers)
    style_header_row(ws, 1, len(headers))

    for task in data["tasks"]:
        usage = task.get("usage", {})
        ws.append([
            task.get("category", ""),
            task.get("task_id", ""),
            task.get("grading", {}).get("mean", 0),
            usage.get("input_tokens", 0),
            usage.get("output_tokens", 0),
            usage.get("cache_read_tokens", 0),
            usage.get("cache_write_tokens", 0),
            usage.get("total_tokens", 0),
            usage.get("request_count", 0),
        ])

    for col in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col)].width = 18


def build_single_report(data: dict) -> openpyxl.Workbook:
    wb = openpyxl.Workbook()
    write_overview_sheet(wb, data)
    write_detail_sheet(wb, data)
    return wb


# --------------------------------------------------------------------------- #
# 目录模式
# --------------------------------------------------------------------------- #
def fmt_timestamp(ts) -> str:
    try:
        return datetime.fromtimestamp(float(ts)).strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError, OSError):
        return ""


def write_compare_sheet(wb, results: list[tuple[Path, Path, dict]], categories: list[str]):
    """对比 Sheet：每个文件一行，含模型/suite/总分率/各类别得分率/总 tokens 等。"""
    ws = wb.active
    ws.title = "对比"

    headers = ["文件", "模型", "suite", "run_id", "总分率", "总分/满分", "任务数"]
    headers += categories
    headers += ["total_tokens", "total_requests", "总耗时(s)", "时间"]
    ws.append(headers)
    style_header_row(ws, 1, len(headers))

    for rel_path, _abs_path, data in results:
        cat_scores = data.get("category_scores", {})
        total_score = sum(v["score"] for v in cat_scores.values())
        total_max = sum(v["max_score"] for v in cat_scores.values())
        overall_pct = (total_score / total_max * 100) if total_max > 0 else 0
        task_count = sum(v.get("task_count", 0) for v in cat_scores.values())

        eff = data.get("efficiency", {})

        row = [
            str(rel_path),
            data.get("model", ""),
            data.get("suite", ""),
            data.get("run_id", ""),
            f"{overall_pct:.1f}%",
            f"{total_score:.2f} / {total_max:.1f}",
            task_count,
        ]
        for cat in categories:
            if cat in cat_scores:
                row.append(f"{cat_scores[cat]['pct']:.1f}%")
            else:
                row.append("-")
        row += [
            eff.get("total_tokens", ""),
            eff.get("total_requests", ""),
            eff.get("total_execution_time_seconds", ""),
            fmt_timestamp(data.get("timestamp")),
        ]
        ws.append(row)

    # 列宽：文件列宽一些，其余适中
    ws.column_dimensions["A"].width = 50
    for col in range(2, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col)].width = 16
    ws.freeze_panes = "B2"


def write_all_detail_sheet(wb, results: list[tuple[Path, Path, dict]]):
    """全量明细 Sheet：所有文件的任务展平，前置 model/run_id/文件 列。"""
    ws = wb.create_sheet("明细")

    headers = [
        "model", "run_id", "suite", "category", "task", "score",
        "input_tokens", "output_tokens",
        "cache_read_tokens", "cache_write_tokens",
        "total_tokens", "request_count", "文件",
    ]
    ws.append(headers)
    style_header_row(ws, 1, len(headers))

    for rel_path, _abs_path, data in results:
        model = data.get("model", "")
        run_id = data.get("run_id", "")
        suite = data.get("suite", "")
        for task in data.get("tasks", []):
            usage = task.get("usage", {})
            ws.append([
                model,
                run_id,
                suite,
                task.get("category", ""),
                task.get("task_id", ""),
                task.get("grading", {}).get("mean", 0),
                usage.get("input_tokens", 0),
                usage.get("output_tokens", 0),
                usage.get("cache_read_tokens", 0),
                usage.get("cache_write_tokens", 0),
                usage.get("total_tokens", 0),
                usage.get("request_count", 0),
                str(rel_path),
            ])

    for col in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col)].width = 16
    ws.column_dimensions[get_column_letter(len(headers))].width = 50
    ws.freeze_panes = "A2"


def build_dir_report(results: list[tuple[Path, Path, dict]]) -> openpyxl.Workbook:
    # 收集所有出现过的类别，保持稳定顺序（按首次出现）
    categories: list[str] = []
    for _rel, _abs, data in results:
        for cat in data.get("category_scores", {}):
            if cat not in categories:
                categories.append(cat)

    wb = openpyxl.Workbook()
    write_compare_sheet(wb, results, categories)
    write_all_detail_sheet(wb, results)
    return wb


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #
def run_single(input_path: Path, output_dir: Path):
    if not input_path.exists():
        sys.exit(f"文件不存在: {input_path}")

    data = load_result(input_path)
    wb = build_single_report(data)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"analysis_{input_path.stem}_{timestamp}.xlsx"
    wb.save(output_path)
    print(f"分析完成: {output_path}")


def run_dir(dir_paths: list[Path], output_dir: Path):
    all_files = []
    for dir_path in dir_paths:
        if not dir_path.exists():
            print(f"警告：目录不存在，跳过: {dir_path}", file=sys.stderr)
            continue
        if not dir_path.is_dir():
            print(f"警告：不是目录，跳过: {dir_path}", file=sys.stderr)
            continue
        files = find_result_files(dir_path)
        if not files:
            print(f"警告：未找到符合命名规则的文件: {dir_path}", file=sys.stderr)
            continue
        print(f"在 {dir_path} 下找到 {len(files)} 个待分析文件:")
        for path in files:
            print(f"  - {path}")
        all_files.extend(files)

    if not all_files:
        sys.exit("所有目录下均未找到符合命名规则（0xxx_<模型id>.json）的结果文件")

    # 去重（可能多个目录有重复文件）
    all_files = sorted(set(all_files))
    print(f"\n合并后共 {len(all_files)} 个文件待分析\n")

    results: list[tuple[Path, Path, dict]] = []
    # 使用第一个有效目录作为相对路径基准；若需展示绝对路径，可改为直接用 path
    base_dir = dir_paths[0] if len(dir_paths) == 1 else None

    for path in all_files:
        try:
            data = load_result(path)
        except (json.JSONDecodeError, OSError) as e:
            print(f"跳过（解析失败）: {path} -> {e}", file=sys.stderr)
            continue
        # 尝试相对路径，失败则用绝对路径
        if base_dir:
            try:
                rel = path.relative_to(base_dir)
            except ValueError:
                rel = path
        else:
            rel = path
        results.append((rel, path, data))

    if not results:
        sys.exit("没有可解析的结果文件")

    wb = build_dir_report(results)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # 多目录时用 "multi"，单目录时用目录名
    dir_name = dir_paths[0].name if len(dir_paths) == 1 else "multi"
    output_path = output_dir / f"analysis_dir_{dir_name}_{timestamp}.xlsx"
    wb.save(output_path)
    print(f"分析完成（共 {len(results)} 个文件）: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="PinchBench 评测结果分析")
    parser.add_argument("-i", "--input", type=str, default=None, help="输入的评测结果 JSON 文件路径")
    parser.add_argument(
        "-d", "--dir", type=str, nargs='+', default=None,
        help="递归扫描一个或多个目录下所有 0xxx_<模型id>.json 文件，汇总分析",
    )
    parser.add_argument("-o", "--output-dir", type=str, default=None, help="输出目录，默认为 ./output")
    args = parser.parse_args()

    if args.input and args.dir:
        sys.exit("-i 与 -d 不能同时使用")

    output_dir = Path(args.output_dir) if args.output_dir else Path.cwd() / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.dir:
        run_dir([Path(d) for d in args.dir], output_dir)
        return

    results_dir = Path(__file__).resolve().parent.parent / "results"
    input_path = Path(args.input) if args.input else find_latest_result(results_dir)
    run_single(input_path, output_dir)


if __name__ == "__main__":
    main()
