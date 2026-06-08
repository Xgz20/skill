#!/usr/bin/env python3
"""
PinchBench 批量评测执行器

职责：
1. 读取 models-config.yaml 配置
2. 临时复制用例到 tasks/ 目录
3. 串行执行多个模型的评测
4. 结果分目录存储
5. 清理临时文件
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional

# 导入共享工具（skills/shared/）
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))
from path_resolver import resolve_task_path

ROUND_RE = re.compile(r"^round_(\d+)$")


def load_config(project_root: Path) -> Dict:
    """
    加载或创建配置文件。

    如果配置文件不存在，从模板复制并提示用户填写后退出。
    """
    config_path = project_root / "models-config.yaml"
    # 模板在 ../assets/（scripts/ 上一级的 assets/ 目录）
    template_path = Path(__file__).parent.parent / "assets" / "models-config.yaml.example"

    if not config_path.exists():
        shutil.copy(template_path, config_path)
        print("✅ 已创建配置文件: models-config.yaml")
        print("⚠️  请编辑该文件，填写模型的 api_key 和 base_url")
        print(f"📝 配置文件路径: {config_path}")
        sys.exit(0)

    with open(config_path) as f:
        config = yaml.safe_load(f)

    # 验证配置结构
    if "judge" not in config or "models_under_test" not in config:
        print(f"❌ 配置文件格式错误: {config_path}")
        print("   必须包含 'judge' 和 'models_under_test' 字段")
        sys.exit(1)

    # 深度校验
    judge = config.get("judge")
    models = config.get("models_under_test")

    if not isinstance(judge, dict):
        print(f"❌ 配置文件错误: 'judge' 必须是非空对象")
        sys.exit(1)
    for field in ("model_id", "api_key", "base_url"):
        if not judge.get(field):
            print(f"❌ 配置文件错误: judge.{field} 缺失或为空")
            sys.exit(1)

    if not isinstance(models, list) or not models:
        print(f"❌ 配置文件错误: 'models_under_test' 必须是非空列表")
        sys.exit(1)
    for i, m in enumerate(models, 1):
        if not isinstance(m, dict):
            print(f"❌ 配置文件错误: models_under_test[{i}] 必须是对象")
            sys.exit(1)
        for field in ("model_id", "api_key", "base_url"):
            if not m.get(field):
                print(f"❌ 配置文件错误: models_under_test[{i}].{field} 缺失或为空")
                sys.exit(1)

    return config


def detect_next_round(task_id: str, project_root: Path) -> int:
    """
    自动检测下一个轮次号（同一 task_id 的多次评测）。

    扫描 results-auto/<task_id>/round_* 目录，返回最大 N + 1。
    """
    results_base = project_root / "results-auto" / task_id
    if not results_base.exists():
        return 1

    existing_rounds = []
    for d in results_base.iterdir():
        if d.is_dir():
            m = ROUND_RE.match(d.name)
            if m:
                existing_rounds.append(int(m.group(1)))

    return max(existing_rounds) + 1 if existing_rounds else 1


def build_command(
    model: Dict,
    judge: Dict,
    task_id: str,
    output_dir: Path,
    project_root: Path,
) -> List[str]:
    """
    组装 PinchBench 评测命令。

    Args:
        model: 被评测模型配置 {model_id, api_key, base_url}
        judge: 裁判模型配置 {model_id, api_key, base_url}
        task_id: 用例 ID（文件名不含 .md）
        output_dir: 结果输出目录
        project_root: 项目根目录

    Returns:
        命令参数列表（用于 subprocess.run）
    """
    run_script = project_root / "scripts" / "run.sh"

    return [
        str(run_script),
        "--model", model["model_id"],
        "--base-url", model["base_url"],
        "--api-key", model["api_key"],
        "--judge", judge["model_id"],
        "--suite", task_id,
        "--output-dir", str(output_dir),
        "--no-upload",
        "--verbose",
    ]


def run_batch(task_input: str, round_num: Optional[int] = None) -> Path:
    """
    批量执行多个模型的评测。

    Args:
        task_input: 用例输入（task_id 或路径）
        round_num: 指定轮次号（None 表示自动检测）

    Returns:
        结果输出目录（results-auto/<task_id>/round_<N>/）
    """
    # __file__ 是 skills/pinchbench-batch-runner/scripts/batch_runner.py
    # project_root 是 skill/（skills/ 的上一级）
    project_root = Path(__file__).parent.parent.parent.parent

    # 1. 加载配置
    config = load_config(project_root)
    judge = config["judge"]
    models = config["models_under_test"]

    # 2. 解析用例路径
    source = resolve_task_path(task_input, project_root)
    task_id = source.stem
    print(f"📋 用例: {task_id} ({source})")

    # 3. 轮次检测
    if round_num is None:
        round_num = detect_next_round(task_id, project_root)
    print(f"🔄 执行轮次: Round {round_num}")

    output_base = project_root / "results-auto" / task_id / f"round_{round_num}"
    output_base.mkdir(parents=True, exist_ok=True)

    # 4. 临时复制到 tasks/ + 注册到 manifest（PinchBench 框架限制）
    tasks_dir = project_root / "tasks"
    temp_in_tasks = tasks_dir / f"{task_id}.md"
    manifest_path = tasks_dir / "manifest.yaml"

    # 三种情况：
    # a) tasks/ 中已存在同名且是同一文件 → 源就在 tasks/ 里，不需要复制也不要删除
    # b) tasks/ 中已存在同名但不是同一文件 → 拒绝执行，避免覆盖已晋升的真实用例
    # c) tasks/ 中不存在同名 → 临时复制，执行后清理
    if temp_in_tasks.exists():
        if temp_in_tasks.samefile(source):
            need_temp_copy = False  # 情况 a
        else:
            print(
                f"❌ tasks/{task_id}.md 已存在且与待评测用例不是同一文件。\n"
                f"   待评测: {source}\n"
                f"   tasks/中: {temp_in_tasks}\n"
                f"   为避免覆盖已晋升的真实用例，请先重命名其中之一后重试。"
            )
            sys.exit(1)  # 情况 b：拒绝执行
    else:
        need_temp_copy = True  # 情况 c
        print(f"📄 临时复制用例到 {temp_in_tasks}")
        shutil.copy(source, temp_in_tasks)

        # 临时注册到 manifest.yaml（PinchBench 通过 manifest 加载任务）
        with open(manifest_path, "r") as f:
            manifest_backup = f.read()

        manifest_data = yaml.safe_load(manifest_backup)
        # 临时注册到 productivity category（批量评测的临时任务）
        if "categories" not in manifest_data:
            manifest_data["categories"] = {}
        if "productivity" not in manifest_data["categories"]:
            manifest_data["categories"]["productivity"] = []

        # 检查是否已在 manifest 中（避免重复注册）
        task_already_in_manifest = any(
            task_id in category_tasks
            for category_tasks in manifest_data["categories"].values()
        )

        if not task_already_in_manifest:
            manifest_data["categories"]["productivity"].append(task_id)
            with open(manifest_path, "w") as f:
                yaml.dump(manifest_data, f, default_flow_style=False, allow_unicode=True)
            print(f"📝 临时注册到 manifest (productivity category)")
        else:
            print(f"ℹ️  task_id 已在 manifest 中")
            manifest_backup = None  # 不需要还原

    try:
        # 5. 串行执行每个模型
        for i, model in enumerate(models, 1):
            model_id = model["model_id"]
            print(f"\n{'=' * 60}")
            print(f"▶ [{i}/{len(models)}] 评测模型: {model_id}")
            print(f"{'=' * 60}")

            output_dir = output_base / model_id
            output_dir.mkdir(parents=True, exist_ok=True)

            cmd = build_command(model, judge, task_id, output_dir, project_root)

            # 设置裁判模型环境变量
            env = {
                **os.environ,
                "ANTHROPIC_API_KEY": judge["api_key"],
                "ANTHROPIC_BASE_URL": judge["base_url"],
            }

            result = subprocess.run(
                cmd,
                env=env,
                capture_output=False,  # 实时输出到终端
                text=True,
            )

            if result.returncode != 0:
                print(f"⚠️  模型 {model_id} 评测失败（退出码 {result.returncode}）")
            else:
                print(f"✅ 模型 {model_id} 评测完成")

        # 6. 生成摘要文件
        summary_path = output_base / "batch-run-summary.md"
        write_summary(summary_path, task_id, round_num, models, output_base)
        print(f"\n📊 摘要文件: {summary_path}")

    finally:
        # 7. 清理临时文件和还原 manifest（仅清理我们自己创建的临时副本）
        if need_temp_copy:
            if temp_in_tasks.exists():
                print(f"🗑️  清理临时文件: {temp_in_tasks}")
                temp_in_tasks.unlink()

            # 还原 manifest（如果我们修改过）
            if 'manifest_backup' in locals() and manifest_backup is not None:
                with open(manifest_path, "w") as f:
                    f.write(manifest_backup)
                print(f"🔄 还原 manifest.yaml")

    print(f"\n✅ 批量评测完成")
    print(f"📂 结果目录: {output_base}")
    return output_base


def write_summary(
    summary_path: Path,
    task_id: str,
    round_num: int,
    models: List[Dict],
    output_base: Path,
):
    """生成批量执行摘要文件"""
    with open(summary_path, "w") as f:
        f.write(f"# 批量评测摘要 - {task_id} (Round {round_num})\n\n")
        f.write(f"**用例ID**: {task_id}\n")
        f.write(f"**评测轮次**: Round {round_num}\n")
        f.write(f"**参与模型数**: {len(models)}\n\n")
        f.write("## 模型列表\n\n")
        for model in models:
            model_id = model["model_id"]
            f.write(f"- `{model_id}`\n")
            f.write(f"  - 结果: `{output_base / model_id}/`\n")


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="PinchBench 批量评测执行器")
    parser.add_argument("task", help="用例输入（task_id 或文件路径）")
    parser.add_argument(
        "--round",
        type=int,
        default=None,
        help="指定轮次号（默认自动检测）",
    )

    args = parser.parse_args()
    run_batch(args.task, args.round)


if __name__ == "__main__":
    main()
