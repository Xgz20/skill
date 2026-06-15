---
id: task_polymarket_briefing
name: Polymarket + 新闻简报
category: 调研
scene: 金融投研与企业价值评估
sub_scene: 预测市场新闻简报
difficulty: L2
capabilities:
- 幻觉抑制
- 信息检索与综合
- 数据提取与处理
- 输出格式适配
- 自然语言生成
grading_type: hybrid
timeout_seconds: 180
workspace_files: []
---

# Polymarket + 新闻简报

## Prompt

获取 Polymarket（polymarket.com）当前热度最高的 3 个预测市场。对于每个市场，找到一条相关的近期新闻（过去 48 小时内），解释人们为何在该市场下注。

将结果保存为 `polymarket_briefing.md`，格式如下：

```
# Polymarket Briefing — {today's date}

## 1. {Market Question}
**Current odds:** Yes {X}% / No {Y}%
**Related news:** {1-2 sentence summary of a real news story that contextualizes this market}

## 2. {Market Question}
**Current odds:** Yes {X}% / No {Y}%
**Related news:** {1-2 sentence summary}

## 3. {Market Question}
**Current odds:** Yes {X}% / No {Y}%
**Related news:** {1-2 sentence summary}
```

只使用真实、当前活跃的市场。不要编造市场或赔率。

---

## Expected Behavior

Agent 应当：
1. 使用 Polymarket API（`https://gamma-api.polymarket.com/markets?active=true&order=volumeNum&ascending=false&limit=10`）或通过浏览 polymarket.com 获取热门/活跃市场
2. 按交易量选出最活跃/最热门的 3 个市场
3. 对于每个市场，搜索过去 48 小时内发布的一条相关新闻
4. 格式化并将输出保存到 `polymarket_briefing.md`

Agent 不得臆造市场数据。如果 API 不可用，应说明这一点并尝试备选方案（例如通过网络搜索 "polymarket trending markets today"）。

---

## Grading Criteria

- [ ] 工作区中创建了 `polymarket_briefing.md`
- [ ] 文件标题中包含今天的日期
- [ ] 恰好 3 个市场板块（若市场不可用，可少于 3 个并附说明）
- [ ] 每个市场都有问题、赔率（Yes/No 百分比）和相关新闻
- [ ] 赔率为百分比格式且总和约为 100%
- [ ] 相关新闻摘要为 1-3 句，且看起来符合事实
- [ ] 市场问题看起来是真实的预测市场话题
- [ ] 格式符合所要求的 markdown 结构

---

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    from pathlib import Path
    import re
    from datetime import date

    scores = {}
    workspace = Path(workspace_path)
    briefing_file = workspace / "polymarket_briefing.md"

    if not briefing_file.exists():
        return {
            "file_created": 0.0,
            "has_date_header": 0.0,
            "has_three_markets": 0.0,
            "has_odds": 0.0,
            "has_news_summaries": 0.0,
            "correct_format": 0.0,
        }

    scores["file_created"] = 1.0
    content = briefing_file.read_text()

    # Check date header
    year = date.today().strftime("%Y")
    has_date = year in content and "# Polymarket Briefing" in content
    scores["has_date_header"] = 1.0 if has_date else 0.0

    # Check for 3 market sections (## 1., ## 2., ## 3.)
    market_headers = re.findall(r'^## \d+\.', content, re.MULTILINE)
    count = len(market_headers)
    scores["has_three_markets"] = 1.0 if count >= 3 else (0.5 if count >= 2 else 0.0)

    # Check for odds pattern (XX% format)
    odds_matches = re.findall(r'\d{1,3}%', content)
    scores["has_odds"] = 1.0 if len(odds_matches) >= 6 else (0.5 if len(odds_matches) >= 3 else 0.0)

    # Check for related news sections with content
    news_sections = re.findall(r'\*\*Related news:\*\*\s*(.+)', content)
    valid_news = [n for n in news_sections if len(n.split()) >= 5]
    scores["has_news_summaries"] = 1.0 if len(valid_news) >= 3 else (0.5 if len(valid_news) >= 2 else 0.0)

    # Check overall format
    has_header = content.strip().startswith("# Polymarket Briefing")
    has_current_odds = "Current odds:" in content
    scores["correct_format"] = 1.0 if has_header and has_current_odds else 0.5

    return scores
```

---

## LLM Judge Rubric

```markdown
### Criterion 1: Data Authenticity (Weight: 45%)

**Score 1.0**：全部 3 个市场都是真实、当前活跃的 Polymarket 预测市场。赔率合理（总和接近 100%，没有缺乏上下文的极端值）。没有编造的市场或赔率。
**Score 0.75**：市场看起来真实，但赔率可能略有过时，或有一个市场无法核实。
**Score 0.5**：部分市场看起来合理，但有一个看似虚构，或赔率不合理（例如无论话题如何，每个市场都是 50/50）。
**Score 0.25**：多个市场看起来是编造的，或赔率显示出明显的幻觉模式（全部恰好 50%、不可能的值）。
**Score 0.0**：所有市场明显是幻觉，或 Agent 拒绝生成内容。

### Criterion 2: News Relevance (Weight: 35%)

**Score 1.0**：每条相关新闻都直接解释了该市场为何活跃。新闻合理且近期。新闻事件与预测市场问题之间联系清晰。
**Score 0.75**：新闻条目大多相关，仅有小的不匹配或新闻略旧。
**Score 0.5**：新闻条目与市场话题有些相关，但没有清晰解释当前的赔率或活跃度。
**Score 0.25**：新闻条目过于宽泛，或与具体市场问题仅有松散联系。
**Score 0.0**：没有新闻条目、新闻完全无关，或事件明显是编造的。

### Criterion 3: Format Compliance (Weight: 20%)

**Score 1.0**：文件完全符合所要求的格式：日期标题、3 个编号板块、加粗字段标签、百分比赔率、新闻摘要。
**Score 0.75**：有小的偏差（例如百分比格式略有不同、多余空白）。
**Score 0.5**：结构可辨认但偏差较大（例如缺少赔率、板块被合并）。
**Score 0.25**：内容存在但大多未格式化。
**Score 0.0**：文件为空或没有预测市场内容。
```

---

## Additional Notes

本任务测试 Agent 以下能力：
- 从实时 API 或网站访问并解析真实的金融/预测市场数据
- 将市场活跃度与当前新闻事件交叉印证
- 在压力下避免臆造数值数据（赔率）
- 将结构化数据检索与定性新闻摘要相结合

**Polymarket API 参考：**
- 按交易量排序的活跃市场：`https://gamma-api.polymarket.com/markets?active=true&order=volumeNum&ascending=false&limit=10`
- 公开市场数据无需认证

本任务反映了真实使用场景：Agent 将预测市场作为新闻重要性的信号进行监控（市场往往在主流报道之前就对新闻做出反应）。它专门挑战那些可能编造听起来合理的市场数据而非真正去获取数据的模型。

评分者对确切的日期格式应宽松，但对真实赔率（不全是 50/50 或整数）的存在以及市场与新闻之间的话题相关性应严格。
