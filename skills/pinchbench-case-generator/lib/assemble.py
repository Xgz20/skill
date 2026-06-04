"""Assemble PinchBench test cases from workflow output."""
from pathlib import Path
import re
from typing import Dict, Any
import yaml


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
    # Use yaml.dump with explicit settings for clean output
    yaml_text = yaml.dump(
        data,
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
