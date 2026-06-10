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


# ============ 维度F：capabilities_validity ============
from analyzers import analyze_capabilities_validity


def test_capabilities_all_standard():
    """全部为标准标签，数量合规 → 无问题"""
    frontmatter = {
        "capabilities": ["tool_usage", "information_retrieval", "output_format"]
    }
    result = analyze_capabilities_validity(frontmatter)
    assert result["has_issue"] is False
    assert result["details"]["invalid"] == []
    assert result["details"]["count"] == 3


def test_capabilities_invalid_tag():
    """包含业务特征词（非标准标签）→ 发现问题"""
    frontmatter = {
        "capabilities": ["tool_usage", "multi_market_analysis", "output_format"]
    }
    result = analyze_capabilities_validity(frontmatter)
    assert result["has_issue"] is True
    assert "multi_market_analysis" in result["details"]["invalid"]


def test_capabilities_too_few():
    """数量少于3个 → 发现问题"""
    frontmatter = {
        "capabilities": ["tool_usage", "output_format"]
    }
    result = analyze_capabilities_validity(frontmatter)
    assert result["has_issue"] is True
    assert result["details"]["count"] == 2


def test_capabilities_too_many():
    """数量多于5个 → 发现问题"""
    frontmatter = {
        "capabilities": [
            "tool_usage", "output_format", "information_retrieval",
            "data_extraction", "planning", "text_generation"
        ]
    }
    result = analyze_capabilities_validity(frontmatter)
    assert result["has_issue"] is True
    assert result["details"]["count"] == 6


def test_capabilities_missing():
    """缺少 capabilities 字段 → 发现问题"""
    frontmatter = {}
    result = analyze_capabilities_validity(frontmatter)
    assert result["has_issue"] is True


# ============ 维度G：difficulty_accuracy ============
from analyzers import analyze_difficulty_accuracy, _infer_difficulty_from_transcript


def _make_transcript(n_assistant: int, tool_names: list) -> list:
    """构造最小 transcript：n 条 assistant 消息，每条带一个 toolCall"""
    events = []
    tool_call_id = 0
    for i in range(n_assistant):
        content = [{"type": "text", "text": f"step {i}"}]
        if i < len(tool_names):
            content.append({
                "type": "toolCall",
                "id": f"call_{tool_call_id}",
                "name": tool_names[i],
                "arguments": {},
            })
            # 对应的 toolResult
            events.append({
                "type": "message",
                "message": {
                    "role": "toolResult",
                    "toolCallId": f"call_{tool_call_id}",
                    "toolName": tool_names[i],
                    "isError": False,
                    "content": "ok",
                },
            })
            tool_call_id += 1
        events.append({
            "type": "message",
            "message": {"role": "assistant", "content": content},
        })
    return events


def test_infer_difficulty_l1():
    """1步1工具 → L1"""
    transcript = _make_transcript(1, ["read_file"])
    result = _infer_difficulty_from_transcript(transcript)
    assert result["inferred_level"] == "L1"
    assert result["actual_steps"] == 1
    assert result["actual_tools"] == 1


def test_infer_difficulty_l2():
    """5步2工具 → L2"""
    transcript = _make_transcript(5, ["web_search", "write_file"])
    result = _infer_difficulty_from_transcript(transcript)
    assert result["inferred_level"] == "L2"


def test_infer_difficulty_l3():
    """10步4工具 → L3"""
    tools = ["web_search", "read_file", "write_file", "execute_command"]
    transcript = _make_transcript(10, tools)
    result = _infer_difficulty_from_transcript(transcript)
    assert result["inferred_level"] == "L3"


def test_infer_difficulty_l4():
    """30步 → L4"""
    transcript = _make_transcript(30, ["web_search"])
    result = _infer_difficulty_from_transcript(transcript)
    assert result["inferred_level"] == "L4"


def test_difficulty_accuracy_match():
    """声明与反推一致 → 无问题"""
    frontmatter = {"difficulty": "L2", "timeout_seconds": 180}
    # 5步2工具 → 反推 L2
    t = _make_transcript(5, ["web_search", "write_file"])
    results = [{"model": "a", "score": 0.7, "transcript": t}]
    result = analyze_difficulty_accuracy(frontmatter, results)
    assert result["has_issue"] is False
    assert result["details"]["inferred_difficulty"] == "L2"


def test_difficulty_accuracy_mismatch():
    """声明 L1 但反推 L3 → 发现问题"""
    frontmatter = {"difficulty": "L1", "timeout_seconds": 180}
    tools = ["web_search", "read_file", "write_file", "execute_command"]
    t = _make_transcript(10, tools)
    results = [{"model": "a", "score": 0.7, "transcript": t}]
    result = analyze_difficulty_accuracy(frontmatter, results)
    assert result["has_issue"] is True
    assert "L1" in result["summary"]
    assert "L3" in result["summary"]


def test_difficulty_timeout_mismatch():
    """难度 L3 但 timeout=60s（L1区间）→ 发现问题"""
    frontmatter = {"difficulty": "L3", "timeout_seconds": 60}
    tools = ["web_search", "read_file", "write_file", "execute_command"]
    t = _make_transcript(10, tools)
    results = [{"model": "a", "score": 0.7, "transcript": t}]
    result = analyze_difficulty_accuracy(frontmatter, results)
    assert result["has_issue"] is True
    assert "越界" in result["summary"]


def test_difficulty_no_transcripts():
    """无 transcript → 不报问题，优雅降级"""
    frontmatter = {"difficulty": "L2", "timeout_seconds": 180}
    results = [{"model": "a", "score": 0.5, "transcript": []}]
    result = analyze_difficulty_accuracy(frontmatter, results)
    assert result["has_issue"] is False

