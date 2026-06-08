"""五维度分析器：分析评测结果，识别用例优化点。

维度：
- A. Prompt 清晰度（需 LLM 分析 transcript）
- B. 评分标准合理性（需 LLM 分析）
- C. 难度区分度（纯数据计算）
- D. 超时设置（纯数据计算）
- E. 工具使用合理性（transcript 解析）
"""
import statistics
from typing import Dict, List


def analyze_difficulty(model_results: List[Dict]) -> Dict:
    """
    维度C：难度区分度分析。

    优化触发条件：全部满分/全部0分，或方差过小。
    """
    scores = [r["score"] for r in model_results]

    if not scores:
        return {"has_issue": False, "summary": "无评测数据", "details": {}}

    mean_score = statistics.mean(scores)
    score_range = max(scores) - min(scores)
    variance = statistics.variance(scores) if len(scores) > 1 else 0.0

    has_issue = False
    issues = []

    # 全部满分
    if all(s >= 0.95 for s in scores):
        has_issue = True
        issues.append("所有模型接近满分，用例难度过低，缺乏区分度")
    # 全部零分
    if all(s <= 0.05 for s in scores):
        has_issue = True
        issues.append("所有模型接近零分，用例难度过高或存在缺陷")
    # 方差过小（多模型时）
    if len(scores) > 1 and score_range < 0.15:
        has_issue = True
        issues.append(f"分数极差仅 {score_range:.2f}，区分度不足")

    summary = "；".join(issues) if issues else "分数分布合理，有良好区分度"

    return {
        "has_issue": has_issue,
        "summary": summary,
        "details": {
            "scores": {r["model"]: r["score"] for r in model_results},
            "mean": round(mean_score, 3),
            "range": round(score_range, 3),
            "variance": round(variance, 3),
        },
    }


def analyze_timeout(model_results: List[Dict]) -> Dict:
    """
    维度D：超时设置分析。

    优化触发条件：任一模型因超时失败。
    """
    timed_out_models = [
        r["model"] for r in model_results if r.get("timed_out", False)
    ]

    has_issue = len(timed_out_models) > 0

    if has_issue:
        summary = (
            f"模型 {', '.join(timed_out_models)} 发生超时，"
            f"可能因 timeout 设置过短导致误判，建议增加 timeout"
        )
    else:
        summary = "无超时发生，timeout 设置合理"

    return {
        "has_issue": has_issue,
        "summary": summary,
        "details": {
            "timed_out_models": timed_out_models,
            "total_models": len(model_results),
        },
    }


def extract_tool_calls(transcript: List[Dict]) -> List[Dict]:
    """
    从 OpenClaw 格式 transcript 提取工具调用记录及成功状态。

    OpenClaw 格式说明：
    - 顶层每条记录含 type 字段（session/model_change/message 等）
    - 只有 type == "message" 的条目包含对话内容
    - 工具调用：role == "assistant"，content 数组含 {"type": "toolCall", "id", "name", "arguments"}
    - 工具结果：role == "toolResult"，含 toolCallId/toolName/isError/details 字段

    Args:
        transcript: OpenClaw 事件流列表（每项为顶层事件对象）

    Returns:
        工具调用列表，每项含 name/success/result
    """
    calls = []

    # 建立 toolCallId → toolResult 消息的映射
    tool_results: Dict = {}
    for event in transcript:
        # 只处理 message 类型事件
        if event.get("type") != "message":
            continue
        msg = event.get("message", {})
        if msg.get("role") == "toolResult":
            call_id = msg.get("toolCallId")
            if call_id:
                tool_results[call_id] = msg

    # 提取工具调用
    for event in transcript:
        if event.get("type") != "message":
            continue
        msg = event.get("message", {})
        if msg.get("role") != "assistant":
            continue
        content = msg.get("content", [])
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict) or block.get("type") != "toolCall":
                continue
            call_id = block.get("id")
            name = block.get("name", "unknown")

            result_msg = tool_results.get(call_id, {}) if call_id else {}
            # 成功判定：优先用结构化字段
            success = _is_tool_call_success(result_msg)

            # 提取结果文本用于展示
            result_text = _extract_tool_result_text(result_msg)

            calls.append({
                "name": name,
                "success": success,
                "result": result_text[:200],
            })

    return calls


def _is_tool_call_success(result_msg: Dict) -> bool:
    """判断工具调用是否成功。

    优先使用结构化字段（details.status / isError），
    仅在缺失时退化到文本匹配。
    """
    if not result_msg:
        # 没有对应的结果消息，视为未知，默认成功（可能是截断的 transcript）
        return True

    # 优先：isError 字段（布尔值）
    is_error = result_msg.get("isError")
    if is_error is True:
        return False

    # 次优：details.status 字段
    details = result_msg.get("details", {})
    if isinstance(details, dict):
        status = details.get("status", "")
        if status == "error":
            return False
        if status in ("success", "ok"):
            return True

    # 退化：文本匹配（兜底）
    result_text = _extract_tool_result_text(result_msg)
    if result_text and "error" in result_text.lower():
        return False

    return True


def _extract_tool_result_text(result_msg: Dict) -> str:
    """从 toolResult 消息中提取文本内容。"""
    if not result_msg:
        return ""
    content = result_msg.get("content", [])
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "\n".join(parts)
    return ""


def analyze_tool_usage(model_results: List[Dict]) -> Dict:
    """
    维度E：工具使用合理性分析。

    优化触发条件：工具调用失败率高，或缺少必要工具。
    """
    all_calls = []
    per_model_stats = {}

    for r in model_results:
        transcript = r.get("transcript", [])
        calls = extract_tool_calls(transcript)
        all_calls.extend(calls)

        if calls:
            failed = [c for c in calls if not c["success"]]
            per_model_stats[r["model"]] = {
                "total": len(calls),
                "failed": len(failed),
                "failure_rate": round(len(failed) / len(calls), 2),
            }

    if not all_calls:
        return {
            "has_issue": False,
            "summary": "无工具调用数据",
            "details": {},
        }

    total_failed = sum(1 for c in all_calls if not c["success"])
    overall_failure_rate = total_failed / len(all_calls)

    has_issue = overall_failure_rate > 0.3  # 失败率超30%视为问题

    if has_issue:
        summary = (
            f"工具调用整体失败率 {overall_failure_rate:.0%}，"
            f"可能存在工具能力 gap 或用例对工具要求不合理"
        )
    else:
        summary = f"工具调用失败率 {overall_failure_rate:.0%}，使用正常"

    return {
        "has_issue": has_issue,
        "summary": summary,
        "details": {
            "overall_failure_rate": round(overall_failure_rate, 2),
            "per_model": per_model_stats,
        },
    }


def prepare_llm_analysis_data(original_task: Dict, model_results: List[Dict]) -> Dict:
    """
    为 LLM 分析（维度 A/B）准备数据。

    维度 A（Prompt清晰度）和 B（评分标准）需要 LLM 来分析，
    此函数整理出 LLM 分析所需的结构化输入。

    Args:
        original_task: 原始用例数据（含 prompt、grading 等）
        model_results: 各模型评测结果

    Returns:
        结构化的 LLM 分析输入
    """
    return {
        "task_prompt": original_task.get("prompt", ""),
        "grading_criteria": original_task.get("grading", {}),
        "model_outputs": [
            {
                "model": r["model"],
                "score": r["score"],
                "transcript_summary": _summarize_transcript(r.get("transcript", [])),
            }
            for r in model_results
        ],
    }


def _summarize_transcript(transcript: List[Dict], max_messages: int = 20) -> List[Dict]:
    """提取 transcript 关键信息（用户指令 + 助手响应），截断长内容。

    适配 OpenClaw 事件流格式：跳过非 message 事件，
    从 obj["message"]["role"] 和 obj["message"]["content"] 取内容。
    """
    summary = []
    count = 0
    for event in transcript:
        if count >= max_messages:
            break
        # 只处理 message 类型事件，跳过元数据事件
        if event.get("type") != "message":
            continue
        msg = event.get("message", {})
        role = msg.get("role", "")
        content = msg.get("content", "")

        # content 可能是字符串或列表
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        parts.append(block.get("text", ""))
                    elif block.get("type") == "toolCall":
                        parts.append(f"[toolCall: {block.get('name', '?')}]")
            content_text = "\n".join(parts)[:500]
        else:
            content_text = str(content)[:500] if content else ""

        summary.append({"role": role, "content": content_text})
        count += 1
    return summary
