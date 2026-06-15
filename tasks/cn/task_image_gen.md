---
id: task_image_gen
name: AI 图像生成
category: 技能
scene: 内容创作、PPT、网页与多媒体生成
sub_scene: AI 图像生成
difficulty: L1
capabilities:
- 工具调用
- 指令遵循与约束理解
- 多模态感知
- 输出格式适配
grading_type: hybrid
timeout_seconds: 120
workspace_files: []
---

## Prompt

生成一张图像：一个友好的机器人坐在温馨的咖啡馆里看书。将其保存为当前目录下的 "robot_cafe.png"。

## Expected Behavior

Agent 应当：

1. 使用 `generate_image` 工具（或等效的 AI 图像生成能力）创建一张与描述相符的图像
2. 提供一个能够捕捉关键要素的描述性提示词：机器人、咖啡馆场景、温馨氛围、看书
3. 将生成的图像保存为指定的文件名 "robot_cafe.png"
4. 确认生成成功并描述所创建的内容

本任务测试 Agent 的以下能力：

- 恰当地使用 AI 图像生成工具
- 根据自然语言描述编写有效的图像提示词
- 处理生成内容的文件输出操作
- 向用户清晰地传达结果

## Grading Criteria

- [ ] Agent 使用了图像生成工具
- [ ] 生成的提示词包含机器人（robot）
- [ ] 生成的提示词包含咖啡馆或 cafe 场景
- [ ] 生成的提示词包含看书或书（reading 或 book）
- [ ] 图像文件以正确的文件名保存
- [ ] Agent 确认了生成成功

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the AI image generation task.

    Args:
        transcript: Parsed JSONL transcript as list of dicts
        workspace_path: Path to the task's isolated workspace directory

    Returns:
        Dict mapping criterion names to scores (0.0 to 1.0)
    """
    from pathlib import Path

    scores = {
        "used_image_tool": 0.0,
        "prompt_has_robot": 0.0,
        "prompt_has_cafe": 0.0,
        "prompt_has_book": 0.0,
        "file_saved": 0.0,
        "confirmed_generation": 0.0,
    }

    generated_prompt = ""
    used_tool = False

    for event in transcript:
        if event.get("type") != "message":
            continue
        msg = event.get("message", {})

        if msg.get("role") == "assistant":
            for item in msg.get("content", []):
                if item.get("type") == "toolCall":
                    tool_name = item.get("name", "")
                    params = item.get("params", {})

                    # Check for image generation tool
                    if tool_name in ["generate_image", "generateImage", "image_generation"]:
                        used_tool = True
                        generated_prompt = params.get("prompt", "").lower()

                        # Check path parameter for correct filename
                        path = params.get("path", "")
                        if "robot_cafe.png" in path or path.endswith("robot_cafe.png"):
                            scores["file_saved"] = 1.0

                # Check text content for confirmation
                if item.get("type") == "text":
                    text = item.get("text", "").lower()
                    if any(phrase in text for phrase in [
                        "generated",
                        "created the image",
                        "image has been",
                        "successfully created",
                        "saved the image",
                        "here's the image",
                        "image is ready",
                    ]):
                        scores["confirmed_generation"] = 1.0

    scores["used_image_tool"] = 1.0 if used_tool else 0.0

    # Check prompt content
    if generated_prompt:
        if "robot" in generated_prompt:
            scores["prompt_has_robot"] = 1.0

        if any(term in generated_prompt for term in ["coffee", "cafe", "café", "cozy", "shop"]):
            scores["prompt_has_cafe"] = 1.0

        if any(term in generated_prompt for term in ["book", "reading", "read"]):
            scores["prompt_has_book"] = 1.0

    # Also check if file exists in workspace
    workspace = Path(workspace_path)
    if (workspace / "robot_cafe.png").exists():
        scores["file_saved"] = 1.0

    return scores
```

## LLM Judge Rubric

### Criterion 1: Image Quality and Relevance (Weight: 40%)

**Score 1.0**: 生成的图像清晰地描绘了一个机器人在咖啡馆场景中看书。场景给人温馨之感，所有要求的要素都存在且融合良好。
**Score 0.75**: 图像包含大多数要素（机器人、咖啡馆、书），但某个要素不够突出，或温馨氛围未被充分体现。
**Score 0.5**: 图像包含一个机器人和另一个要求的要素，但缺少场景的关键方面。
**Score 0.25**: 图像与要求仅有松散关联，缺少多个关键要素。
**Score 0.0**: 没有生成图像，或图像与要求完全无关。

### Criterion 2: Prompt Crafting (Weight: 30%)

**Score 1.0**: Agent 编写了一个有效、详细的提示词，捕捉了所有要素：友好的机器人、温馨的咖啡馆氛围、看书。可能包含有帮助的艺术性细节。
**Score 0.75**: 提示词包含所有主要要素，但可以更具描述性或更详细。
**Score 0.5**: 提示词捕捉了部分要素，但遗漏了要求中的重要细节。
**Score 0.25**: 提示词过于含糊或遗漏了多个关键要素。
**Score 0.0**: 没有提供提示词，或提示词完全跑题。

### Criterion 3: Task Execution (Weight: 30%)

**Score 1.0**: Agent 正确使用了图像生成工具，保存为正确的文件名，并清晰地传达了结果。
**Score 0.75**: Agent 完成了任务，但存在少量问题（例如文件名略有不同、确认信息极少）。
**Score 0.5**: Agent 生成了图像，但在保存或确认结果上存在问题。
**Score 0.25**: Agent 有尝试，但未能正确完成任务。
**Score 0.0**: Agent 没有尝试图像生成或完全失败。

## Additional Notes

- `generate_image` 工具通过 OpenRouter API 使用 AI 模型
- 支持的输出格式包括 PNG、JPG、JPEG、GIF 和 WEBP
- Agent 应当提供一个超越单纯复述用户请求的描述性提示词
- 鼓励在编写提示词时发挥创意，只要它忠于核心请求即可
- 本任务同时验证工具调用和创造性解读能力
