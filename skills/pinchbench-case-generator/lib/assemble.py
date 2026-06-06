"""Assemble PinchBench test cases from workflow output.

提供两类能力：
1. 库函数：assign_next_sequence / render_frontmatter / assemble_case_file
   （供 tests 和其他脚本调用，行为保持向后兼容）
2. CLI 入口：python assemble.py <workflow_result.json>
   读取 workflow 返回的 result JSON，分配序号、组装 md、输出到项目根
   output/generated_cases/，并在质检发现严重问题时生成 *_REPORT.md
"""
from pathlib import Path
import json
import re
import sys
from typing import Dict, Any, Optional
import yaml


# 组装到 frontmatter 时的字段顺序（id 置顶，对齐官方用例风格）
_FRONTMATTER_ORDER = [
    "id", "name", "category", "scene", "sub_scene", "source", "difficulty",
    "grading_type", "timeout_seconds", "grading_weights",
    "capabilities", "workspace_files",
]


def find_project_root(start: Optional[Path] = None) -> Path:
    """向上查找 PinchBench 项目根目录。

    项目根的唯一标志：同时存在 scripts/lib_grading.py 与 tasks/ 目录。
    这样无论 assemble.py 是从 skills/ 还是 .claude/skills/ 副本运行，
    都能正确定位到项目根（即 skill/ 目录），避免输出到错误位置。

    Args:
        start: 起始查找路径，默认为本文件所在目录

    Returns:
        项目根 Path

    Raises:
        RuntimeError: 向上到文件系统根仍未找到标志时
    """
    cur = (start or Path(__file__).resolve()).resolve()
    for candidate in [cur, *cur.parents]:
        if (candidate / "scripts" / "lib_grading.py").exists() and (candidate / "tasks").is_dir():
            return candidate
    raise RuntimeError(
        "无法定位 PinchBench 项目根（需同时存在 scripts/lib_grading.py 和 tasks/）"
    )


def assign_next_sequence(generated_dir: Path, tasks_dir: Path) -> int:
    """
    Scan both generated_cases/ and tasks/ for task_NNNN_* files,
    return next available sequence number.

    Args:
        generated_dir: Path to output/generated_cases/
        tasks_dir: Path to tasks/

    Returns:
        Next sequence number (1 if no files found)
    """
    pattern = re.compile(r'task_(\d{4})_')
    max_seq = 0

    for directory in [generated_dir, tasks_dir]:
        if not directory.exists():
            continue
        for f in directory.glob("task_*.md"):
            match = pattern.match(f.name)
            if match:
                seq = int(match.group(1))
                max_seq = max(max_seq, seq)

    return max_seq + 1


def render_frontmatter(data: Dict[str, Any]) -> str:
    """
    Render frontmatter dict to YAML format.

    Args:
        data: Frontmatter dictionary

    Returns:
        YAML text without --- delimiters
    """
    # 按既定顺序重排字段（未列出的保持原序追加在后）
    ordered: Dict[str, Any] = {}
    for key in _FRONTMATTER_ORDER:
        if key in data:
            ordered[key] = data[key]
    for key, value in data.items():
        if key not in ordered:
            ordered[key] = value

    # Use yaml.dump with explicit settings for clean output
    yaml_text = yaml.dump(
        ordered,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        indent=2
    )
    return yaml_text.strip()


def assemble_case_file(workflow_result: Dict[str, Any], case_id: str) -> str:
    """
    Assemble workflow result into PinchBench .md format.

    Args:
        workflow_result: Output from case-generation-pipeline workflow
        case_id: Full task ID with sequence (e.g. task_0001_example)

    Returns:
        Complete markdown file content
    """
    frontmatter = workflow_result["frontmatter"].copy()
    frontmatter["id"] = case_id
    sections = workflow_result["sections"]

    # Render frontmatter
    fm_yaml = render_frontmatter(frontmatter)

    # Build markdown sections
    parts = [
        "---",
        fm_yaml,
        "---",
        "",
        "## Prompt",
        "",
        sections["prompt"],
        "",
        "## Expected Behavior",
        "",
        sections["expected_behavior"],
        "",
        "## Grading Criteria",
        ""
    ]

    # Add grading criteria checklist
    for criterion in sections["grading_criteria"]:
        parts.append(f"- [ ] {criterion}")
    parts.append("")

    # Add automated checks if present
    if sections.get("automated_checks"):
        parts.extend([
            "## Automated Checks",
            "",
            "```python",
            sections["automated_checks"],
            "```",
            ""
        ])

    # Add LLM judge rubric if present
    if sections.get("llm_judge_rubric"):
        parts.extend([
            "## LLM Judge Rubric",
            "",
            sections["llm_judge_rubric"],
            ""
        ])

    return "\n".join(parts)


def needs_report(quality_report: Dict[str, Any]) -> bool:
    """质检结果是否达到需要生成报告的程度（存在严重问题或被标记 needs_review）。"""
    if not quality_report:
        return False
    if quality_report.get("needs_review"):
        return True
    for critique in quality_report.get("critiques", []):
        if critique.get("severity") == "critical":
            return True
    return False


def render_report(workflow_result: Dict[str, Any], case_id: str) -> str:
    """生成用例质量报告 markdown（*_REPORT.md），便于后续分析优化。"""
    fm = workflow_result["frontmatter"]
    meta = workflow_result.get("metadata", {})
    quality = meta.get("quality_report", {})
    critiques = quality.get("critiques", [])

    sev_icon = {"critical": "🔴 严重", "moderate": "🟡 中等", "minor": "🟢 轻微"}
    lines = [
        f"# 用例质量报告: {case_id}",
        "",
        f"- **用例名称**: {fm.get('name', '')}",
        f"- **场景**: {fm.get('scene', '')} / {fm.get('sub_scene', '')}",
        f"- **难度等级**: {fm.get('difficulty', 'N/A')}",
        f"- **评分类型**: {fm.get('grading_type', '')}",
    ]
    if fm.get("grading_weights"):
        gw = fm["grading_weights"]
        lines.append(
            f"- **评分权重**: automated={gw.get('automated')}, llm_judge={gw.get('llm_judge')}"
        )
    lines += [
        f"- **草稿质量评分**: {quality.get('best_draft_score', 'N/A')}/10",
        f"- **需要人工审核**: {'是' if quality.get('needs_review') else '否'}",
    ]
    if quality.get("review_reason"):
        lines.append(f"- **审核原因**: {quality['review_reason']}")
    lines += ["", "## 质检发现的问题", ""]

    if not critiques:
        lines.append("（无质检问题记录）")
    else:
        for c in critiques:
            label = sev_icon.get(c.get("severity"), c.get("severity", ""))
            lines.append(f"### [{c.get('key', '')}] {label}")
            lines.append("")
            for issue in c.get("issues", []):
                lines.append(f"- {issue}")
            lines.append("")

    lines += [
        "## 后续步骤",
        "",
        "1. 根据上述问题修订 Prompt、Expected Behavior 或评分逻辑",
        "2. 重点核对标记为「严重」的项",
        "3. 修订后可删除本报告或保留作变更记录",
        "4. 审核通过后迁移到 tasks/ 并更新 manifest.yaml",
        "",
    ]
    return "\n".join(lines)


def main(argv: list) -> int:
    """CLI 入口：从 workflow result JSON 组装用例并输出到项目根 output/generated_cases/。"""
    if len(argv) < 2:
        print("用法: python assemble.py <workflow_result.json>", file=sys.stderr)
        print("  JSON 可为 workflow 完整输出（含 result 键）或直接的 result 对象", file=sys.stderr)
        return 2

    result_path = Path(argv[1])
    if not result_path.exists():
        print(f"错误: 找不到结果文件 {result_path}", file=sys.stderr)
        return 1

    data = json.loads(result_path.read_text(encoding="utf-8"))
    # 兼容两种格式：{ "result": {...} } 或直接 {...}
    workflow_result = data["result"] if isinstance(data, dict) and "result" in data else data

    project_root = find_project_root()
    output_dir = project_root / "output" / "generated_cases"
    tasks_dir = project_root / "tasks"
    output_dir.mkdir(parents=True, exist_ok=True)

    seq = assign_next_sequence(output_dir, tasks_dir)
    task_name = workflow_result.get("metadata", {}).get("task_name_suggestion", "generated_case")
    case_id = f"task_{seq:04d}_{task_name}"

    # 组装并写入用例文件
    md_content = assemble_case_file(workflow_result, case_id)
    case_file = output_dir / f"{case_id}.md"
    case_file.write_text(md_content, encoding="utf-8")

    print(f"✅ 用例已生成: {case_file}")
    print(f"   ID: {case_id}")
    print(f"   名称: {workflow_result['frontmatter'].get('name', '')}")
    print(f"   评分类型: {workflow_result['frontmatter'].get('grading_type', '')}")
    gw = workflow_result["frontmatter"].get("grading_weights")
    if gw:
        print(f"   评分权重: automated={gw.get('automated')}, llm_judge={gw.get('llm_judge')}")

    # 质检不通过时生成报告
    quality = workflow_result.get("metadata", {}).get("quality_report", {})
    if needs_report(quality):
        report_content = render_report(workflow_result, case_id)
        report_file = output_dir / f"{case_id}_REPORT.md"
        report_file.write_text(report_content, encoding="utf-8")
        print(f"⚠️  发现质量问题，已生成报告: {report_file}")
    else:
        print("✅ 质检通过，无需生成报告")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
