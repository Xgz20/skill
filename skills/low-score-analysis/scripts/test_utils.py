#!/usr/bin/env python3
"""
低分任务根因分析 Skill - utils.py 功能验证测试
验证数据精简、分批、断点续传等功能
"""
import json
import sys
from pathlib import Path

# 添加脚本路径
SKILL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_DIR / 'scripts'))

from utils import (
    simplify_task,
    split_into_batches,
    load_completed_tasks,
    save_batch_result,
    merge_all_batches,
    analyze_data_size,
    estimate_json_size
)


def test_data_simplification():
    """测试数据精简功能"""
    print("\n" + "="*60)
    print("测试 1: 数据精简")
    print("="*60)

    # 模拟完整任务数据
    full_task = {
        'task_id': 'task_example',
        'score_pct': 45.2,
        'min_score_pct': 3.0,
        'max_score_pct': 92.7,
        'category': 'csv-analysis',
        'grading_detail': {
            'grading_runs': [
                {
                    'run': 1,
                    'score': 0.927,
                    'breakdown': {
                        'automated.report_created': 1.0,
                        'automated.avg_payout_ranking': 1.0,
                        'llm_judge.calculation_accuracy': 0.75
                    },
                    'notes': 'Strong overall performance. Minor calculation issue.' * 10  # 长notes
                },
                {
                    'run': 2,
                    'score': 0.40,
                    'breakdown': {
                        'automated.report_created': 1.0,
                        'automated.avg_payout_ranking': 0.5
                    },
                    'notes': 'Calculations incorrect.'
                }
            ]
        },
        'task_file': '/path/to/task.md',
        'transcript': '/path/to/transcript.jsonl',
        'extra_field_1': 'not needed',
        'extra_field_2': [1, 2, 3]
    }

    # 精简前
    original_size = estimate_json_size(full_task)
    print(f"原始数据: {original_size} 字节")

    # 精简
    simplified = simplify_task(full_task)
    simplified_size = estimate_json_size(simplified)
    print(f"精简后: {simplified_size} 字节")
    print(f"减少: {(1 - simplified_size/original_size)*100:.1f}%")

    # 验证必要字段保留
    assert 'task_id' in simplified
    assert 'grading_detail' in simplified
    assert 'transcript' in simplified

    # 验证冗余字段删除
    assert 'min_score_pct' not in simplified
    assert 'extra_field_1' not in simplified

    # 验证 notes 截断
    assert len(simplified['grading_detail']['grading_runs'][0]['notes']) <= 500

    print("✅ 数据精简测试通过")
    return True


def test_batch_splitting():
    """测试分批功能"""
    print("\n" + "="*60)
    print("测试 2: 分批切分")
    print("="*60)

    # 模拟任务列表
    tasks = [{'task_id': f'task_{i}', 'score_pct': i} for i in range(37)]

    # 分批
    batches = split_into_batches(tasks, batch_size=10)

    print(f"总任务数: {len(tasks)}")
    print(f"批次数: {len(batches)}")
    print(f"各批大小: {[len(b) for b in batches]}")

    # 验证
    assert len(batches) == 4  # 37个任务，每批10个，应该是4批
    assert len(batches[0]) == 10
    assert len(batches[1]) == 10
    assert len(batches[2]) == 10
    assert len(batches[3]) == 7  # 最后一批7个

    # 验证没有任务丢失
    all_tasks_from_batches = []
    for batch in batches:
        all_tasks_from_batches.extend(batch)
    assert len(all_tasks_from_batches) == len(tasks)

    print("✅ 分批测试通过")
    return True


def test_completed_tasks_loading():
    """测试已完成任务加载"""
    print("\n" + "="*60)
    print("测试 3: 断点续传")
    print("="*60)

    # 创建临时目录
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        model = 'test_model'

        # 模拟批次结果
        batch1_data = {
            'task1': {'result_analysis': 'analysis1', 'root_cause_analysis': 'cause1'},
            'task2': {'result_analysis': 'analysis2', 'root_cause_analysis': 'cause2'}
        }
        batch2_data = {
            'task3': {'result_analysis': 'analysis3', 'root_cause_analysis': 'cause3'}
        }

        # 保存批次文件
        with open(workspace / f'analysis_{model}_batch1.json', 'w') as f:
            json.dump(batch1_data, f)
        with open(workspace / f'analysis_{model}_batch2.json', 'w') as f:
            json.dump(batch2_data, f)

        # 加载已完成任务
        completed = load_completed_tasks(workspace, model)

        print(f"已完成任务数: {len(completed)}")
        print(f"任务ID: {list(completed.keys())}")

        # 验证
        assert len(completed) == 3
        assert 'task1' in completed
        assert 'task2' in completed
        assert 'task3' in completed

        print("✅ 断点续传测试通过")
    return True


def test_batch_saving_and_merging():
    """测试批次保存和合并"""
    print("\n" + "="*60)
    print("测试 4: 增量保存与合并")
    print("="*60)

    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        model = 'test_model'

        # 模拟 Workflow 结果
        workflow_result1 = [
            {'task_id': 'task1', 'result_analysis': 'ra1', 'root_cause_analysis': 'rc1'},
            {'task_id': 'task2', 'result_analysis': 'ra2', 'root_cause_analysis': 'rc2'}
        ]
        workflow_result2 = [
            {'task_id': 'task3', 'result_analysis': 'ra3', 'root_cause_analysis': 'rc3'}
        ]

        # 保存批次1
        file1 = save_batch_result(workflow_result1, workspace, model, 1)
        print(f"批次1已保存: {file1.name}")
        assert file1.exists()

        # 保存批次2
        file2 = save_batch_result(workflow_result2, workspace, model, 2)
        print(f"批次2已保存: {file2.name}")
        assert file2.exists()

        # 合并所有批次
        final_file = merge_all_batches(workspace, model)
        print(f"最终文件: {final_file.name}")

        # 验证最终文件
        assert final_file.exists()
        with open(final_file, 'r') as f:
            final_data = json.load(f)

        assert len(final_data) == 3
        assert 'task1' in final_data
        assert 'task2' in final_data
        assert 'task3' in final_data

        print("✅ 保存与合并测试通过")
    return True


def test_size_analysis():
    """测试数据大小分析"""
    print("\n" + "="*60)
    print("测试 5: 数据大小分析")
    print("="*60)

    # 模拟任务数据
    tasks = [
        {
            'task_id': f'task_{i}',
            'score_pct': 50.0,
            'min_score_pct': 0.0,
            'max_score_pct': 100.0,
            'grading_detail': {
                'grading_runs': [
                    {
                        'run': 1,
                        'score': 0.5,
                        'breakdown': {'check1': 0.5, 'check2': 1.0},
                        'notes': 'Some notes here' * 20
                    }
                ]
            },
            'task_file': f'/path/to/task_{i}.md',
            'transcript': f'/path/to/transcript_{i}.jsonl'
        }
        for i in range(10)
    ]

    # 分析大小
    size_info = analyze_data_size(tasks)

    print(f"原始大小: {size_info['original_size_mb']:.3f} MB")
    print(f"精简后: {size_info['simplified_size_mb']:.3f} MB")
    print(f"减少: {size_info['reduction_pct']:.1f}%")

    # 验证确实减少了
    assert size_info['simplified_size'] < size_info['original_size']
    assert size_info['reduction_pct'] > 0

    print("✅ 大小分析测试通过")
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "🧪 开始测试 utils.py 功能".center(60, "="))

    tests = [
        ("数据精简", test_data_simplification),
        ("分批切分", test_batch_splitting),
        ("断点续传", test_completed_tasks_loading),
        ("保存与合并", test_batch_saving_and_merging),
        ("大小分析", test_size_analysis)
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            failed += 1
            print(f"\n❌ {name} 测试失败:")
            print(f"   {e}")

    print("\n" + "="*60)
    print("测试总结".center(60))
    print("="*60)
    print(f"✅ 通过: {passed}/{len(tests)}")
    if failed > 0:
        print(f"❌ 失败: {failed}/{len(tests)}")
    else:
        print("\n🎉 所有测试通过!")
    print("="*60)

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
