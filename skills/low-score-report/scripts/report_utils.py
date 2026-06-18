#!/usr/bin/env python3
"""
生成低分任务根因共性分析报告的辅助工具

功能：
1. 读取 analysis_<model>.json 和 _failed_tasks_<model>.json
2. 统计根因分类、层次归属
3. 提供深度根因分析的辅助函数（从 transcript 提取代码片段）
4. 从 summary.json 提取评测元信息（任务总数、模型显示名）
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict


def load_analysis_data(workspace_dir: str, model: str) -> Dict[str, Any]:
    """加载分析结果"""
    analysis_file = os.path.join(workspace_dir, f'analysis_{model}.json')
    with open(analysis_file, 'r') as f:
        return json.load(f)


def load_failed_tasks(workspace_dir: str, model: str) -> List[Dict]:
    """加载低分任务清单"""
    tasks_file = os.path.join(workspace_dir, f'_failed_tasks_{model}.json')
    with open(tasks_file, 'r') as f:
        return json.load(f)


def load_summary(result_dir: str) -> Optional[Dict]:
    """
    从评测结果目录加载 summary.json
    返回: summary 数据，如果文件不存在返回 None
    """
    summary_path = os.path.join(result_dir, 'summary.json')
    if not os.path.exists(summary_path):
        return None

    with open(summary_path, 'r') as f:
        return json.load(f)


def extract_eval_metadata(result_dir: str) -> Dict[str, Any]:
    """
    从 summary.json 提取评测元信息

    返回:
        {
            'task_count': int,  # 实际评测任务数
            'model_display_name': str,  # 模型显示名（如 'Spark'）
            'model_id': str  # 模型标识（如 'xsparkx2flash-530'）
        }
    """
    summary = load_summary(result_dir)

    metadata = {
        'task_count': 0,
        'model_display_name': '',
        'model_id': ''
    }

    if summary:
        metadata['task_count'] = len(summary.get('tasks', []))
        metadata['model_id'] = summary.get('model', '')

        # 从 model ID 提取显示名
        # 例如: xsparkx2flash-530 -> Spark
        model_id = metadata['model_id']
        if 'spark' in model_id.lower():
            metadata['model_display_name'] = 'Spark'
        elif 'opus' in model_id.lower():
            metadata['model_display_name'] = 'Opus'
        elif 'sonnet' in model_id.lower():
            metadata['model_display_name'] = 'Sonnet'
        elif 'haiku' in model_id.lower():
            metadata['model_display_name'] = 'Haiku'
        elif 'claude' in model_id.lower():
            metadata['model_display_name'] = 'Claude'
        else:
            # 默认用 model_id 本身
            metadata['model_display_name'] = model_id

    return metadata


def format_round_description(
    round_name: str,
    task_count: int,
    special_config: Optional[str] = None
) -> str:
    """
    生成评测轮次描述

    Args:
        round_name: 轮次名称，如 'round-4'
        task_count: 实际任务数
        special_config: 特殊配置说明，如 "超时时间相对 round-3 放大 4 倍"

    Returns:
        格式化的轮次描述字符串
    """
    base = f"{round_name}（all-suite {task_count} 个评测任务，每任务 3 轮"

    if special_config:
        return f"{base}，{special_config}）"
    else:
        return f"{base}）"


def normalize_terminology(text: str) -> str:
    """
    统一术语：将 provider 相关术语替换为"推理服务"

    Args:
        text: 原始文本

    Returns:
        替换后的文本
    """
    replacements = {
        'provider idle timeout': '推理服务空闲超时',
        'provider 无响应': '推理服务无响应',
        'provider响应': '推理服务响应',
        'provider': '推理服务',
        'Provider': '推理服务',
        'PROVIDER': '推理服务'
    }

    result = text
    for old, new in replacements.items():
        result = result.replace(old, new)

    return result


def classify_root_causes(analysis_data: Dict) -> Dict[str, List[str]]:
    """
    根据 root_cause_analysis 文本自动分类
    返回: {根因类型: [task_id列表]}
    """
    categories = {
        '产物未落盘/写入失败': [],
        '稳定性问题': [],
        '环境限制': [],
        '超时/无响应中断': [],
        '裁判端问题': [],
        '代码错误': [],
        '工具调用格式错误': [],
        '数据计算错误': [],
        '任务理解偏离/串扰': [],
        '幻觉/编造数据': []
    }

    for task_id, data in analysis_data.items():
        rc = data.get('root_cause_analysis', '')

        # 关键词匹配（按优先级）
        if '工具调用格式' in rc or '伪<tool_call>' in rc or '伪 tool_call' in rc:
            categories['工具调用格式错误'].append(task_id)
        elif '产物未落盘' in rc or '未创建文件' in rc or '写入失败' in rc:
            categories['产物未落盘/写入失败'].append(task_id)
        elif '稳定性' in rc or '波动' in rc or '不一致' in rc:
            categories['稳定性问题'].append(task_id)
        elif '环境' in rc or '工具不可用' in rc or '联网' in rc:
            categories['环境限制'].append(task_id)
        elif '超时' in rc or '无响应' in rc or 'timeout' in rc.lower():
            categories['超时/无响应中断'].append(task_id)
        elif '裁判' in rc or 'judge' in rc.lower():
            categories['裁判端问题'].append(task_id)
        elif '代码' in rc and ('错误' in rc or 'bug' in rc):
            categories['代码错误'].append(task_id)
        elif '计算' in rc or '数据错误' in rc:
            categories['数据计算错误'].append(task_id)
        elif '串题' in rc or '理解偏离' in rc or '推理偏离' in rc:
            categories['任务理解偏离/串扰'].append(task_id)
        elif '幻觉' in rc or '编造' in rc:
            categories['幻觉/编造数据'].append(task_id)

    return categories


def extract_layer_attribution(task_data: Dict) -> str:
    """
    从任务数据或分析结果中提取层归属
    返回: L1a-底层推理 / L1b-长程执行 / L3-环境/基础设施 / L4-评测系统
    """
    # 如果任务数据里有 layer 字段，直接返回
    if 'layer' in task_data:
        layer = task_data['layer']
        # 统一格式
        if layer.startswith('L1a') or 'L1a' in layer:
            return 'L1a-底层推理'
        elif layer.startswith('L1b') or 'L1b' in layer:
            return 'L1b-长程执行'
        elif layer.startswith('L1 ') or layer == 'L1 LLM底层能力':
            return 'L1a-底层推理'
        elif layer.startswith('L2 ') or layer == 'L2 Agent工程能力':
            return 'L1b-长程执行'  # 根据重分类
        elif layer.startswith('L3 '):
            return 'L3-环境/基础设施'
        elif layer.startswith('L4 '):
            return 'L4-评测系统'

    # 否则从 root_cause_analysis 推断
    rc = task_data.get('root_cause_analysis', '')
    if 'L1a' in rc or '底层能力' in rc or '底层推理' in rc:
        return 'L1a-底层推理'
    elif 'L1b' in rc or 'agentic' in rc or '长程执行' in rc:
        return 'L1b-长程执行'
    elif 'L3' in rc or '环境' in rc or '基础设施' in rc:
        return 'L3-环境/基础设施'
    elif 'L4' in rc or '裁判' in rc or '评测系统' in rc:
        return 'L4-评测系统'

    return '未分类'


def read_transcript(transcript_path: str) -> List[Dict]:
    """读取 transcript.jsonl"""
    events = []
    if not os.path.exists(transcript_path):
        return events

    with open(transcript_path, 'r') as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))
    return events


def extract_code_executions(transcript_path: str) -> List[Dict]:
    """
    从 transcript 中提取所有代码执行记录
    返回: [{tool_use: {...}, tool_result: {...}}]
    """
    events = read_transcript(transcript_path)
    executions = []

    # 找到所有 exec 工具调用及其结果
    pending_exec = {}

    for event in events:
        if event.get('type') == 'message':
            content = event.get('message', {}).get('content', [])
            for item in content:
                if item.get('type') == 'tool_use' and item.get('name') == 'exec':
                    exec_id = item.get('id')
                    pending_exec[exec_id] = {'tool_use': item, 'tool_result': None}

                elif item.get('type') == 'tool_result':
                    exec_id = item.get('tool_use_id')
                    if exec_id in pending_exec:
                        pending_exec[exec_id]['tool_result'] = item

    return list(pending_exec.values())


def analyze_key_error(code: str, error_msg: str) -> str:
    """
    分析 KeyError 的具体原因
    """
    analysis = []

    # 提取 KeyError 的键名
    key_match = re.search(r"KeyError: ['\"]([^'\"]+)['\"]", error_msg)
    if key_match:
        missing_key = key_match.group(1)
        analysis.append(f"缺失的键: `{missing_key}`")

        # 检查代码中是否有字典访问
        dict_access = re.findall(rf'\w+\[[\'"]({missing_key})[\'"]\]', code)
        if dict_access:
            analysis.append(f"代码中尝试访问不存在的字典键，可能是数据结构理解错误或键名拼写错误")

        # 检查日期解析
        if re.search(r'strptime|strftime', code):
            analysis.append("涉及日期解析，可能是日期格式字符串与实际格式不匹配")

    return '; '.join(analysis) if analysis else "KeyError原因需进一步分析"


def format_task_table(tasks: List[Dict], analysis_data: Dict) -> str:
    """
    生成任务详表的 Markdown
    tasks: 任务列表（含 task_id, score_pct等）
    """
    lines = ['', '**该类任务详表**：', '', '| 任务 ID | 得分 | 归属层 |', '|---------|------|--------|']

    for task in tasks:
        task_id = task['task_id']
        score = task.get('score_pct', 0)

        # 从分析结果获取层归属
        task_analysis = analysis_data.get(task_id, {})
        layer = extract_layer_attribution(task_analysis)

        lines.append(f'| {task_id} | {score:.1f}% | {layer} |')

    lines.append('')
    return '\n'.join(lines)


def generate_report_header(
    model_display_name: str,
    model_id: str,
    round_desc: str,
    num_failed: int,
    num_zero: int,
    data_sources: str = None
) -> str:
    """
    生成报告头部

    Args:
        model_display_name: 模型显示名，如 'Spark'
        model_id: 模型ID，如 'xsparkx2flash-530'
        round_desc: 轮次描述，如 'round-4（all-suite 147 个评测任务，每任务 3 轮）'
        num_failed: 低分任务数
        num_zero: 0分任务数
        data_sources: 数据来源说明（可选）
    """
    if not data_sources:
        data_sources = f"`analysis_{model_id}.json`（{num_failed} 任务逐任务结果分析与根因分析）与 `_failed_tasks_{model_id}.json`（评分明细、三轮得分、transcript 路径）"

    return f"""# AstronClaw PinchBench {model_display_name} 模型低分任务根因分析报告

**被测模型**：{model_id}

**评测轮次**：{round_desc}

**分析样本**：{num_failed} 个低分任务（含 {num_zero} 个 0 分任务）

**数据来源**：{data_sources}
"""


if __name__ == '__main__':
    # 测试工具函数
    result_dir = '/Users/gzx/Project/GitHub/xgz/ai/evaluate/PinchBench/astronclaw-result/all-suite/round-4/xsparkx2flash-530'
    workspace = os.path.join(result_dir, '../report-workspace')
    model = 'xsparkx2flash-530'

    print("提取评测元信息...")
    metadata = extract_eval_metadata(result_dir)
    print(f"  任务数: {metadata['task_count']}")
    print(f"  模型显示名: {metadata['model_display_name']}")
    print(f"  模型ID: {metadata['model_id']}")

    print("\n生成轮次描述...")
    round_desc = format_round_description('round-4', metadata['task_count'], '超时时间相对 round-3 放大 4 倍')
    print(f"  {round_desc}")

    print("\n加载分析数据...")
    analysis = load_analysis_data(workspace, model)
    print(f"  共 {len(analysis)} 个任务")

    print("\n根因分类:")
    categories = classify_root_causes(analysis)
    for cat, tasks in categories.items():
        if tasks:
            print(f"  {cat}: {len(tasks)} 个")
