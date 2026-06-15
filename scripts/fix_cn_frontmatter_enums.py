#!/usr/bin/env python3
"""修复 tasks/cn/ 下的 frontmatter 枚举字段:把残留的英文 category/scene/capabilities 替换为中文映射值。

针对部分翻译 agent 未遵守"frontmatter 枚举翻译为中文"规则的批量修正。
仅替换 frontmatter,不动正文。
"""

import re
import sys
from pathlib import Path

CATEGORY_ZH = {
    "productivity": "生产力", "research": "调研", "writing": "写作",
    "coding": "编程", "analysis": "综合分析", "csv_analysis": "CSV 数据分析",
    "log_analysis": "日志分析", "meeting_analysis": "会议分析",
    "memory": "记忆", "skills": "技能", "integrations": "集成",
}
SCENE_ZH = {
    "finance_investment_research": "金融投研与企业价值评估",
    "deep_research_report": "深度搜索与专题研究报告",
    "science_tech_medical_qa": "科学技术、医学与计算问答",
    "data_retrieval_analysis": "数据库检索、表格整理与数据分析",
    "content_creation_multimedia": "内容创作、PPT、网页与多媒体生成",
    "enterprise_product_intel": "企业产品情报与业务信息助手",
    "skill_lifecycle": "Skill发现、创建、安装与调用",
    "local_env_scripting": "本地环境、命令执行与脚本任务",
}
CAPABILITY_ZH = {
    "instruction_following": "指令遵循与约束理解", "context_memory": "上下文记忆与状态管理",
    "output_format": "输出格式适配", "hallucination_resistance": "幻觉抑制",
    "tool_usage": "工具调用", "multimodal_perception": "多模态感知",
    "data_extraction": "数据提取与处理", "information_retrieval": "信息检索与综合",
    "multi_step_reasoning": "多步推理", "planning": "规划与任务分解",
    "domain_reasoning": "领域推理", "code_generation": "代码生成与理解",
    "service_integration": "外部服务集成", "text_generation": "自然语言生成",
    "self_correction": "自我纠错与反思", "uncertainty_handling": "不确定性处理",
    "safety_awareness": "安全与权限意识", "concurrency_management": "并发与优先级管理",
    "multi_agent": "多Agent协作", "adaptive_learning": "自适应学习",
}


def fix_frontmatter(fm_text: str) -> tuple[str, list[str]]:
    """对 frontmatter 文本逐行替换英文枚举值为中文映射。

    Returns: (修复后文本, 改动说明列表)
    """
    changes: list[str] = []
    lines = fm_text.split("\n")
    out_lines: list[str] = []
    in_caps = False  # capabilities 列表上下文标记

    for line in lines:
        # 1. category: <英文>  → category: <中文>
        m = re.match(r'^(\s*category\s*:\s*)([\'"]?)([a-z_]+)\2(\s*)$', line)
        if m and m.group(3) in CATEGORY_ZH:
            zh = CATEGORY_ZH[m.group(3)]
            line = f"{m.group(1)}{zh}{m.group(4)}"
            changes.append(f"category: {m.group(3)} → {zh}")
            in_caps = False
            out_lines.append(line)
            continue

        # 2. scene: <英文> → scene: <中文>
        m = re.match(r'^(\s*scene\s*:\s*)([\'"]?)([a-z_]+)\2(\s*)$', line)
        if m and m.group(3) in SCENE_ZH:
            zh = SCENE_ZH[m.group(3)]
            line = f"{m.group(1)}{zh}{m.group(4)}"
            changes.append(f"scene: {m.group(3)} → {zh}")
            in_caps = False
            out_lines.append(line)
            continue

        # 3. capabilities 上下文标记
        if re.match(r'^\s*capabilities\s*:\s*$', line):
            in_caps = True
            out_lines.append(line)
            continue

        # 4. capabilities 列表项: - <英文>  → - <中文>
        if in_caps:
            m = re.match(r'^(\s*-\s*)([\'"]?)([a-z_]+)\2(\s*)$', line)
            if m and m.group(3) in CAPABILITY_ZH:
                zh = CAPABILITY_ZH[m.group(3)]
                line = f"{m.group(1)}{zh}{m.group(4)}"
                changes.append(f"capability: {m.group(3)} → {zh}")
                out_lines.append(line)
                continue
            # 非列表项 → 退出 capabilities 上下文
            if not re.match(r'^\s*-\s+', line) and re.match(r'^\S', line):
                in_caps = False

        out_lines.append(line)

    return "\n".join(out_lines), changes


def fix_file(path: Path, dry_run: bool = False) -> list[str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r'^(---\s*\n)(.*?)(\n---\s*\n)', text, re.DOTALL)
    if not m:
        return []
    head, fm, tail = m.group(1), m.group(2), m.group(3)
    new_fm, changes = fix_frontmatter(fm)
    if not changes:
        return []
    new_text = head + new_fm + tail + text[m.end():]
    if not dry_run:
        path.write_text(new_text, encoding="utf-8")
    return changes


def main():
    cn_dir = Path(__file__).resolve().parent.parent / "tasks" / "cn"
    if not cn_dir.exists():
        sys.exit(f"目录不存在: {cn_dir}")

    dry_run = "--dry-run" in sys.argv
    files = sorted(cn_dir.glob("task_*.md"))
    fixed = 0
    total_changes = 0
    for f in files:
        changes = fix_file(f, dry_run=dry_run)
        if changes:
            fixed += 1
            total_changes += len(changes)
            print(f"{f.name}:")
            for c in changes:
                print(f"  - {c}")

    label = "[预览]" if dry_run else "[已修复]"
    print(f"\n{label} 处理 {len(files)} 个文件,改动 {fixed} 个,共 {total_changes} 处枚举替换")


if __name__ == "__main__":
    main()
