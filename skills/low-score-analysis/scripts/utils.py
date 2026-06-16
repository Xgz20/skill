#!/usr/bin/env python3
"""
低分任务根因分析 - 工具函数模块
提供数据精简、批次划分、结果合并等功能
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional


def simplify_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    精简任务数据，只保留 Workflow 必需的字段

    减少传输数据量，提高性能
    """
    simplified = {
        'task_id': task['task_id'],
        'score_pct': task['score_pct'],
        'category': task.get('category', ''),

        # 精简 grading_detail
        'grading_detail': {
            'grading_runs': [
                {
                    'run': r['run'],
                    'score': r['score'],
                    'breakdown': r['breakdown'],
                    # notes 截断到 500 字符避免过长
                    'notes': r.get('notes', '')[:500]
                }
                for r in task.get('grading_detail', {}).get('grading_runs', [])
            ]
        },

        # 保留必要路径
        'task_file': task.get('task_file', ''),
        'transcript': task.get('transcript', '')
    }

    return simplified


def split_into_batches(tasks: List[Dict], batch_size: int = 10) -> List[List[Dict]]:
    """
    将任务列表分割成小批次

    Args:
        tasks: 任务列表
        batch_size: 每批任务数量，默认10

    Returns:
        批次列表，每个批次是一个任务列表
    """
    batches = []
    for i in range(0, len(tasks), batch_size):
        batches.append(tasks[i:i+batch_size])
    return batches


def estimate_json_size(data: Any) -> int:
    """估算 JSON 数据序列化后的字节数"""
    return len(json.dumps(data, ensure_ascii=False))


def load_completed_tasks(workspace_dir: Path, model: str) -> Dict[str, Dict]:
    """
    加载已完成的任务分析结果（用于断点续传）

    Args:
        workspace_dir: 工作目录
        model: 模型名

    Returns:
        {task_id: {result_analysis, root_cause_analysis}}
    """
    completed = {}

    # 尝试加载最终结果文件
    final_file = workspace_dir / f'analysis_{model}.json'
    if final_file.exists():
        try:
            with open(final_file, 'r', encoding='utf-8') as f:
                completed.update(json.load(f))
        except Exception as e:
            print(f"⚠️  读取 {final_file.name} 失败: {e}")

    # 尝试加载各批次文件
    for batch_file in workspace_dir.glob(f'analysis_{model}_batch*.json'):
        try:
            with open(batch_file, 'r', encoding='utf-8') as f:
                batch_data = json.load(f)
                completed.update(batch_data)
        except Exception as e:
            print(f"⚠️  读取 {batch_file.name} 失败: {e}")

    return completed


def save_batch_result(
    results: List[Dict],
    workspace_dir: Path,
    model: str,
    batch_num: int
) -> Path:
    """
    保存单个批次的分析结果

    Args:
        results: Workflow 返回的结果列表
        workspace_dir: 工作目录
        model: 模型名
        batch_num: 批次编号

    Returns:
        保存的文件路径
    """
    # 转换为 {task_id: {result_analysis, root_cause_analysis}} 格式
    batch_data = {}
    for item in results:
        if item and 'task_id' in item:
            batch_data[item['task_id']] = {
                'result_analysis': item.get('result_analysis', ''),
                'root_cause_analysis': item.get('root_cause_analysis', '')
            }

    # 保存
    output_file = workspace_dir / f'analysis_{model}_batch{batch_num}.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(batch_data, f, indent=2, ensure_ascii=False)

    return output_file


def merge_all_batches(
    workspace_dir: Path,
    model: str,
    output_name: Optional[str] = None
) -> Path:
    """
    合并所有批次的分析结果到最终文件

    Args:
        workspace_dir: 工作目录
        model: 模型名
        output_name: 输出文件名(可选)，默认为 analysis_{model}.json

    Returns:
        最终文件路径
    """
    all_results = {}

    # 收集所有批次文件
    batch_files = sorted(workspace_dir.glob(f'analysis_{model}_batch*.json'))

    for batch_file in batch_files:
        try:
            with open(batch_file, 'r', encoding='utf-8') as f:
                batch_data = json.load(f)
                all_results.update(batch_data)
                print(f"  ✓ {batch_file.name}: {len(batch_data)} 个任务")
        except Exception as e:
            print(f"  ✗ {batch_file.name}: 读取失败 - {e}")

    # 保存最终结果
    if output_name is None:
        output_name = f'analysis_{model}.json'

    output_file = workspace_dir / output_name
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\n✓ 最终合并: {output_file.name}")
    print(f"  总任务数: {len(all_results)}")

    return output_file


def print_batch_summary(
    batch_num: int,
    total_batches: int,
    batch_tasks: List[Dict],
    succeeded: int,
    failed: int
):
    """打印批次执行摘要"""
    print(f"\n{'='*60}")
    print(f"批次 {batch_num}/{total_batches} 完成")
    print(f"{'='*60}")
    print(f"  任务: {[t['task_id'] for t in batch_tasks[:3]]}")
    if len(batch_tasks) > 3:
        print(f"       ... 还有 {len(batch_tasks)-3} 个")
    print(f"  成功: {succeeded}/{len(batch_tasks)}")
    if failed > 0:
        print(f"  失败: {failed}")
    print(f"{'='*60}\n")


def analyze_data_size(tasks: List[Dict]) -> Dict[str, Any]:
    """
    分析任务数据大小统计

    Returns:
        包含原始大小、精简后大小、减少比例等信息的字典
    """
    original_size = estimate_json_size(tasks)
    simplified = [simplify_task(t) for t in tasks]
    simplified_size = estimate_json_size(simplified)

    reduction = (1 - simplified_size / original_size) * 100 if original_size > 0 else 0

    return {
        'original_size': original_size,
        'simplified_size': simplified_size,
        'reduction_pct': reduction,
        'original_size_mb': original_size / 1024 / 1024,
        'simplified_size_mb': simplified_size / 1024 / 1024
    }
