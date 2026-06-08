"""测试 analyzers.py"""
import pytest
from analyzers import analyze_difficulty, analyze_timeout


def test_analyze_difficulty_all_perfect():
    """测试：全部满分，区分度不足"""
    results = [
        {"model": "a", "score": 1.0},
        {"model": "b", "score": 1.0},
    ]
    analysis = analyze_difficulty(results)
    assert analysis["has_issue"] is True
    assert "全部满分" in analysis["summary"] or "区分度" in analysis["summary"] or "满分" in analysis["summary"]


def test_analyze_difficulty_all_zero():
    """测试：全部零分，难度过高"""
    results = [
        {"model": "a", "score": 0.0},
        {"model": "b", "score": 0.0},
    ]
    analysis = analyze_difficulty(results)
    assert analysis["has_issue"] is True


def test_analyze_difficulty_good_spread():
    """测试：良好分布，无问题"""
    results = [
        {"model": "a", "score": 0.3},
        {"model": "b", "score": 0.7},
    ]
    analysis = analyze_difficulty(results)
    assert analysis["has_issue"] is False


def test_analyze_timeout_with_timeout():
    """测试：存在超时"""
    results = [
        {"model": "a", "score": 0.5, "timed_out": True},
        {"model": "b", "score": 0.8, "timed_out": False},
    ]
    analysis = analyze_timeout(results)
    assert analysis["has_issue"] is True
    assert "a" in analysis["summary"]


def test_analyze_timeout_no_timeout():
    """测试：无超时"""
    results = [
        {"model": "a", "score": 0.5, "timed_out": False},
        {"model": "b", "score": 0.8, "timed_out": False},
    ]
    analysis = analyze_timeout(results)
    assert analysis["has_issue"] is False


from analyzers import analyze_tool_usage, extract_tool_calls


# OpenClaw 格式 mini-fixture：
# - call_1: read_file 成功
# - call_2: bad_tool 失败（details.status == "error"）
# - call_3: write_file 成功
OPENCLAW_TRANSCRIPT = [
    # 元数据事件，应被跳过
    {"type": "session", "id": "s1", "version": 3},
    {"type": "model_change", "id": "m1"},
    # 第一个 assistant 消息：发起 call_1
    {
        "type": "message",
        "id": "msg1",
        "message": {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "我来读取文件"},
                {"type": "toolCall", "id": "call_1", "name": "read_file", "arguments": {"path": "foo.txt"}},
            ],
        },
    },
    # call_1 的结果：成功
    {
        "type": "message",
        "id": "msg2",
        "message": {
            "role": "toolResult",
            "toolCallId": "call_1",
            "toolName": "read_file",
            "content": [{"type": "text", "text": "file content here"}],
            "isError": False,
        },
    },
    # 第二个 assistant 消息：发起 call_2
    {
        "type": "message",
        "id": "msg3",
        "message": {
            "role": "assistant",
            "content": [
                {"type": "toolCall", "id": "call_2", "name": "bad_tool", "arguments": {}},
            ],
        },
    },
    # call_2 的结果：失败（details.status == "error"）
    {
        "type": "message",
        "id": "msg4",
        "message": {
            "role": "toolResult",
            "toolCallId": "call_2",
            "toolName": "bad_tool",
            "content": [{"type": "text", "text": "tool not found"}],
            "isError": False,
            "details": {"status": "error", "error": "tool not found"},
        },
    },
    # 第三个 assistant 消息：发起 call_3
    {
        "type": "message",
        "id": "msg5",
        "message": {
            "role": "assistant",
            "content": [
                {"type": "toolCall", "id": "call_3", "name": "write_file", "arguments": {"path": "out.txt", "content": "hello"}},
            ],
        },
    },
    # call_3 的结果：成功
    {
        "type": "message",
        "id": "msg6",
        "message": {
            "role": "toolResult",
            "toolCallId": "call_3",
            "toolName": "write_file",
            "content": [{"type": "text", "text": "Successfully wrote 5 bytes to out.txt"}],
            "isError": False,
        },
    },
]


def test_extract_tool_calls():
    """测试：从 OpenClaw 格式 transcript 提取工具调用"""
    calls = extract_tool_calls(OPENCLAW_TRANSCRIPT)
    assert len(calls) == 3
    assert calls[0]["name"] == "read_file"
    assert calls[0]["success"] is True
    assert calls[1]["name"] == "bad_tool"
    assert calls[1]["success"] is False  # details.status == "error"
    assert calls[2]["name"] == "write_file"
    assert calls[2]["success"] is True


def test_analyze_tool_usage_high_failure():
    """测试：工具调用失败率高（2次失败 / 2次总计 = 100%，超过30%阈值）"""
    transcript = [
        {
            "type": "message",
            "id": "a1",
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "toolCall", "id": "t1", "name": "t1", "arguments": {}},
                    {"type": "toolCall", "id": "t2", "name": "t2", "arguments": {}},
                ],
            },
        },
        {
            "type": "message",
            "id": "r1",
            "message": {
                "role": "toolResult",
                "toolCallId": "t1",
                "toolName": "t1",
                "content": [{"type": "text", "text": "error occurred"}],
                "isError": False,
                "details": {"status": "error", "error": "failed"},
            },
        },
        {
            "type": "message",
            "id": "r2",
            "message": {
                "role": "toolResult",
                "toolCallId": "t2",
                "toolName": "t2",
                "content": [{"type": "text", "text": "another failure"}],
                "isError": True,
            },
        },
    ]
    model_results = [{"model": "a", "transcript": transcript}]
    analysis = analyze_tool_usage(model_results)
    assert analysis["has_issue"] is True


def test_analyze_tool_usage_no_issue():
    """测试：工具调用正常（1次成功 = 0%失败率，不触发has_issue）"""
    transcript = [
        {
            "type": "message",
            "id": "a1",
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "toolCall", "id": "t1", "name": "t1", "arguments": {}},
                ],
            },
        },
        {
            "type": "message",
            "id": "r1",
            "message": {
                "role": "toolResult",
                "toolCallId": "t1",
                "toolName": "t1",
                "content": [{"type": "text", "text": "success result"}],
                "isError": False,
            },
        },
    ]
    model_results = [{"model": "a", "transcript": transcript}]
    analysis = analyze_tool_usage(model_results)
    assert analysis["has_issue"] is False


def test_extract_tool_calls_from_real_transcript():
    """煙雾测试：用真实 PinchBench transcript 不抛异常，且能识别出工具调用"""
    import json
    from pathlib import Path
    real_path = Path("/Users/gzx/Project/GitHub/xgz/ai/evaluate/PinchBench/skill/results/0001_transcripts/task_0001_global_stock_market_five_day_summary.jsonl")
    if not real_path.exists():
        pytest.skip("真实样本不可用")
    transcript = []
    with open(real_path) as f:
        for line in f:
            line = line.strip()
            if line:
                transcript.append(json.loads(line))
    calls = extract_tool_calls(transcript)
    # 不验证具体数量（取决于样本），只验证不抛异常且返回 list
    assert isinstance(calls, list)
    # 如果识别到工具调用，验证字段结构
    for c in calls:
        assert "name" in c
        assert "success" in c
        assert isinstance(c["success"], bool)

