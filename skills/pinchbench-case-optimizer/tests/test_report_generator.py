"""测试 report_generator.py"""
import pytest
from pathlib import Path
from report_generator import generate_report, format_model_overview


def test_format_model_overview():
    """测试：格式化模型表现总览表格"""
    model_results = [
        {"model": "xopglm5", "score": 0.30, "timed_out": False,
         "usage": {"total_tokens": 12000}, "execution_time": 108.5},
        {"model": "spark-x", "score": 0.85, "timed_out": True,
         "usage": {"total_tokens": 35000}, "execution_time": None},
    ]
    table = format_model_overview(model_results)
    assert "xopglm5" in table
    assert "0.30" in table
    assert "spark-x" in table
    assert "是" in table  # spark-x 超时
    assert "用时" in table  # 表头含用时列
    assert "108.5s" in table  # xopglm5 用时
    assert "N/A" in table  # spark-x 无用时数据


def test_generate_report_creates_file(tmp_path):
    """测试：生成报告文件"""
    analysis = {
        "prompt_clarity": {"has_issue": True, "summary": "存在歧义",
                           "details": {}},
        "grading_validity": {"has_issue": False, "summary": "评分合理",
                            "details": {}},
        "difficulty": {"has_issue": True, "summary": "区分度不足",
                      "details": {"scores": {}, "mean": 0.5}},
        "timeout": {"has_issue": False, "summary": "无超时", "details": {}},
        "tool_usage": {"has_issue": False, "summary": "正常", "details": {}},
    }
    model_results = [
        {"model": "a", "score": 0.5, "timed_out": False, "usage": {}},
    ]
    convergence = {
        "converged": False, "signals": [], "issue_count": 2,
        "recommendation": "建议继续优化",
    }

    report_path = tmp_path / "report.md"
    generate_report(
        report_path=report_path,
        task_id="task_test",
        round_num=1,
        model_results=model_results,
        analysis=analysis,
        convergence=convergence,
        judge_model="anthropic/claude-sonnet-4-6",
    )

    assert report_path.exists()
    content = report_path.read_text()
    assert "task_test" in content
    assert "维度A" in content
    assert "维度C" in content
    assert "存在歧义" in content
