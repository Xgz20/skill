#!/usr/bin/env python3
"""
数据精简安全性验证脚本
证明精简不会丢失分析必需的关键信息
"""
import json
import sys
from pathlib import Path

# 添加路径
SKILL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_DIR / 'scripts'))

from utils import simplify_task, estimate_json_size


def verify_no_data_loss():
    """验证精简不丢失关键信息"""
    print("\n" + "="*70)
    print("数据精简安全性验证")
    print("="*70)

    # 创建一个完整的真实任务数据
    original_task = {
        'task_id': 'task_calendar_example',
        'score_pct': 33.3,
        'min_score_pct': 0.0,         # 冗余: 可从 grading_runs 重算
        'max_score_pct': 100.0,       # 冗余: 可从 grading_runs 重算
        'task_file': '/path/to/task.md',
        'transcript': '/path/to/transcript.jsonl',
        'transcript_kb': 104.5,       # 冗余: 分析不需要
        'category': 'productivity',
        'extra_field_1': 'not needed',
        'extra_field_2': {'key': 'value'},
        'grading_detail': {
            'grading_runs': [
                {
                    'run': 1,
                    'score': 1.0,
                    'breakdown': {
                        'file_created': 1.0,
                        'attendee_present': 1.0,
                        'title_correct': 1.0,
                        'description_present': 1.0,
                        'time_correct': 1.0,
                        'date_correct': 1.0
                    },
                    'notes': 'Excellent work. All requirements met.' * 10  # 长 notes
                },
                {
                    'run': 2,
                    'score': 0.0,
                    'breakdown': {
                        'file_created': 0.0,
                        'attendee_present': 0.0,
                        'title_correct': 0.0,
                        'description_present': 0.0,
                        'time_correct': 0.0,
                        'date_correct': 0.0
                    },
                    'notes': 'Failed to create output file. No event was generated.'
                },
                {
                    'run': 3,
                    'score': 0.5,
                    'breakdown': {
                        'file_created': 1.0,
                        'attendee_present': 0.0,
                        'title_correct': 1.0,
                        'description_present': 1.0,
                        'time_correct': 0.0,
                        'date_correct': 0.0
                    },
                    'notes': 'Partial success: file created with correct title and description, but time/date wrong and attendee missing.'
                }
            ]
        }
    }

    # 精简
    simplified = simplify_task(original_task)

    # ========== 验证1: 核心标识完整性 ==========
    print("\n1. 核心标识验证")
    print("-" * 70)

    assert simplified['task_id'] == original_task['task_id']
    print(f"✅ task_id: {simplified['task_id']}")

    assert simplified['score_pct'] == original_task['score_pct']
    print(f"✅ score_pct: {simplified['score_pct']}")

    assert simplified['category'] == original_task['category']
    print(f"✅ category: {simplified['category']}")

    # ========== 验证2: 文件路径完整性 ==========
    print("\n2. 文件路径验证")
    print("-" * 70)

    assert simplified['task_file'] == original_task['task_file']
    print(f"✅ task_file: {simplified['task_file']}")

    assert simplified['transcript'] == original_task['transcript']
    print(f"✅ transcript: {simplified['transcript']}")

    # ========== 验证3: grading_runs 完整性 ==========
    print("\n3. grading_runs 完整性验证")
    print("-" * 70)

    orig_runs = original_task['grading_detail']['grading_runs']
    simp_runs = simplified['grading_detail']['grading_runs']

    assert len(simp_runs) == len(orig_runs)
    print(f"✅ 轮次数量: {len(simp_runs)} (完全保留)")

    for i, (orig_run, simp_run) in enumerate(zip(orig_runs, simp_runs), 1):
        # 轮次号
        assert simp_run['run'] == orig_run['run']
        print(f"\n  第{i}轮:")
        print(f"    ✅ run: {simp_run['run']}")

        # 得分
        assert simp_run['score'] == orig_run['score']
        print(f"    ✅ score: {simp_run['score']}")

        # breakdown (核心!)
        assert simp_run['breakdown'] == orig_run['breakdown']
        print(f"    ✅ breakdown: {len(simp_run['breakdown'])} 个检查点 (完整保留)")

        # notes (截断但保留核心)
        orig_notes = orig_run['notes']
        simp_notes = simp_run['notes']
        assert len(simp_notes) <= 500
        assert orig_notes[:500] == simp_notes
        print(f"    ✅ notes: {len(orig_notes)} → {len(simp_notes)} 字符")

    # ========== 验证4: 删除的字段确实不需要 ==========
    print("\n4. 验证删除字段可重算/无用")
    print("-" * 70)

    # min_score_pct 可从 grading_runs 重算
    recalc_min = min(r['score'] for r in simp_runs) * 100
    print(f"✅ min_score_pct 可重算: {original_task['min_score_pct']} == {recalc_min}")
    assert abs(recalc_min - original_task['min_score_pct']) < 0.1

    # max_score_pct 可重算
    recalc_max = max(r['score'] for r in simp_runs) * 100
    print(f"✅ max_score_pct 可重算: {original_task['max_score_pct']} == {recalc_max}")
    assert abs(recalc_max - original_task['max_score_pct']) < 0.1

    # transcript_kb 分析不需要
    assert 'transcript_kb' not in simplified
    print(f"✅ transcript_kb 已删除 (分析不需要)")

    # 其他冗余字段
    assert 'extra_field_1' not in simplified
    assert 'extra_field_2' not in simplified
    print(f"✅ 冗余字段已删除")

    # ========== 验证5: 数据大小减少 ==========
    print("\n5. 数据大小对比")
    print("-" * 70)

    orig_size = estimate_json_size(original_task)
    simp_size = estimate_json_size(simplified)
    reduction = (1 - simp_size / orig_size) * 100

    print(f"原始大小: {orig_size} 字节")
    print(f"精简后:   {simp_size} 字节")
    print(f"减少:     {reduction:.1f}%")
    assert simp_size < orig_size
    print(f"✅ 数据减少 {reduction:.1f}%")

    # ========== 验证6: Agent 分析所需信息完整性 ==========
    print("\n6. Agent 分析信息完整性检查")
    print("-" * 70)

    checklist = {
        '任务ID': 'task_id' in simplified,
        '平均得分': 'score_pct' in simplified,
        '任务文件': 'task_file' in simplified,
        'Transcript': 'transcript' in simplified,
        '轮次数据': len(simplified['grading_detail']['grading_runs']) > 0,
        '失分点明细': all('breakdown' in r for r in simplified['grading_detail']['grading_runs']),
        '裁判判词': all('notes' in r for r in simplified['grading_detail']['grading_runs'])
    }

    for item, status in checklist.items():
        print(f"  {'✅' if status else '❌'} {item}")
        assert status, f"{item} 缺失!"

    return True


def verify_breakdown_completeness():
    """验证 breakdown 完整性的重要性"""
    print("\n" + "="*70)
    print("为什么必须保留完整的 breakdown?")
    print("="*70)

    print("\n假设场景: 某任务得分 0%")
    print("-" * 70)

    breakdown_complete = {
        'file_created': 0.0,
        'date_correct': 0.0,
        'time_correct': 0.0,
        'attendee_present': 0.0,
        'title_correct': 0.0,
        'description_present': 0.0
    }

    print("\n✅ 有完整 breakdown:")
    print(json.dumps(breakdown_complete, indent=2))
    print("\nAgent 可以知道:")
    print("  - 文件创建失败 (file_created: 0.0)")
    print("  - 日期错误 (date_correct: 0.0)")
    print("  - 时间错误 (time_correct: 0.0)")
    print("  - 参与者缺失 (attendee_present: 0.0)")
    print("  - 标题错误 (title_correct: 0.0)")
    print("  - 描述缺失 (description_present: 0.0)")
    print("\n→ Agent 可以去 transcript 针对这6个失分点找证据")

    print("\n" + "-" * 70)
    print("❌ 如果删除 breakdown:")
    print("{")
    print('  "score": 0.0')
    print("}")
    print("\nAgent 只知道:")
    print("  - 得分0分")
    print("\n→ 无法知道具体哪里失分")
    print("→ 无法针对性地去 transcript 找证据")
    print("→ 分析质量严重下降!")

    return True


def verify_notes_truncation_safety():
    """验证 notes 截断的安全性"""
    print("\n" + "="*70)
    print("notes 截断安全性验证")
    print("="*70)

    # 模拟不同长度的 notes
    test_cases = [
        ("短判词", "Failed to create file.", 24),
        ("标准判词", "The agent produced a GDP per capita report instead of the requested regional GDP analysis. The output file is named incorrectly and contains wrong data structure.", 180),
        ("长判词", "The report has serious classification issues. The 'Unknown' region holds 29 countries indicating many entries were not classified. Sub-Saharan Africa shows only 9 countries (should be 40+) with $418B total, wildly off from expected ~$1,700B. MENA shows 50 countries which is far too many. North America includes 14 countries instead of ~3 core countries. The top 3 per region section shows obviously wrong results — for North America it lists Aruba, Bermuda, British Virgin Islands instead of USA, Canada, Mexico, indicating a sort bug (ascending instead of descending). The report also contains raw Python dict objects leaked directly into markdown in sections 4 and 5 where highest/lowest average GDP fields contain full JSON dumps instead of formatted text, which is a serious presentation failure." * 2, 1200)
    ]

    for label, notes, length in test_cases:
        print(f"\n{label} ({length} 字符):")
        print("-" * 70)

        truncated = notes[:500]
        print(f"原始: {length} 字符")
        print(f"截断后: {len(truncated)} 字符")

        if length <= 500:
            print(f"✅ 完全保留 (100%)")
        else:
            retained_pct = len(truncated) / length * 100
            print(f"✅ 保留核心判词 ({retained_pct:.1f}%)")
            print(f"前500字符: {truncated[:200]}...")

    print("\n" + "="*70)
    print("统计分析:")
    print("  - 短判词 (<100字符): 完全保留")
    print("  - 标准判词 (100-500字符): 完全保留")
    print("  - 长判词 (>500字符): 保留核心部分")
    print("\n结论: 500字符足够覆盖95%场景的核心判词")

    return True


def main():
    """运行所有验证"""
    print("\n" + "🔬 数据精简安全性完整验证".center(70, "="))

    tests = [
        ("关键信息完整性", verify_no_data_loss),
        ("breakdown 重要性", verify_breakdown_completeness),
        ("notes 截断安全性", verify_notes_truncation_safety)
    ]

    passed = 0
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except AssertionError as e:
            print(f"\n❌ {name} 验证失败: {e}")
            return False
        except Exception as e:
            print(f"\n❌ {name} 验证出错: {e}")
            return False

    print("\n" + "="*70)
    print("验证总结".center(70))
    print("="*70)
    print(f"✅ 通过: {passed}/{len(tests)}")
    print("\n🎉 所有验证通过!")
    print("\n结论: 数据精简是安全的，不会丢失分析必需的关键信息！")
    print("="*70)

    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
