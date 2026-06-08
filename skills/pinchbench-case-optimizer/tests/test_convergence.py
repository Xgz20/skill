"""测试 convergence.py"""
import pytest
from convergence import check_convergence, count_issues


def test_count_issues():
    """测试：统计问题数量"""
    analysis = {
        "prompt_clarity": {"has_issue": True},
        "grading_validity": {"has_issue": False},
        "difficulty": {"has_issue": True},
        "timeout": {"has_issue": False},
        "tool_usage": {"has_issue": False},
    }
    assert count_issues(analysis) == 2


def test_check_convergence_no_issues():
    """测试：无问题时建议停止"""
    analysis = {
        "prompt_clarity": {"has_issue": False},
        "grading_validity": {"has_issue": False},
        "difficulty": {"has_issue": False},
        "timeout": {"has_issue": False},
        "tool_usage": {"has_issue": False},
    }
    result = check_convergence(1, analysis)
    assert result["converged"] is True
    assert "无新问题发现" in result["signals"]


def test_check_convergence_max_rounds():
    """测试：达到最大轮次"""
    analysis = {
        "prompt_clarity": {"has_issue": True},
        "grading_validity": {"has_issue": False},
        "difficulty": {"has_issue": False},
        "timeout": {"has_issue": False},
        "tool_usage": {"has_issue": False},
    }
    result = check_convergence(5, analysis)
    assert result["converged"] is True
    assert any("最大轮次" in s for s in result["signals"])


def test_check_convergence_has_issues_continue():
    """测试：有问题且未达最大轮次，建议继续"""
    analysis = {
        "prompt_clarity": {"has_issue": True},
        "grading_validity": {"has_issue": False},
        "difficulty": {"has_issue": False},
        "timeout": {"has_issue": False},
        "tool_usage": {"has_issue": False},
    }
    result = check_convergence(2, analysis)
    assert result["converged"] is False
    assert result["recommendation"] == "建议继续优化"
