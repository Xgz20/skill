---
id: task_daily_summary
name: 每日调研摘要生成
category: 生产力
scene: 企业产品情报与业务信息助手
sub_scene: 高管简报综合
difficulty: L2
capabilities:
- 信息检索与综合
- 数据提取与处理
- 自然语言生成
- 输出格式适配
- 多步推理
grading_type: llm_judge
timeout_seconds: 300
workspace_files:
  - path: "research/market_analysis.txt"
    content: |
      Market Analysis Report - February 15, 2026
      Analyst: Sarah Chen, Senior Market Strategist

      Key Market Movements:
      - S&P 500 closed at 5,842.31, up 1.2% on strong tech earnings
      - NASDAQ gained 1.8%, led by semiconductor stocks
      - Dow Jones rose 0.7% to 42,156.88
      - 10-year Treasury yield steady at 4.32%

      Sector Performance:
      - Technology: +2.1% (best performer)
      - Healthcare: +0.9%
      - Energy: -0.3% (only declining sector)
      - Financials: +0.6%

      Notable Company News:
      - TechCorp announced Q4 earnings beat, revenue up 23% YoY
      - GlobalPharma received FDA approval for new cancer treatment
      - AutoEV recalled 50,000 vehicles due to battery concerns
      - CloudServices acquired DataSecure for $2.3B

      Market Outlook:
      Analysts remain cautiously optimistic heading into March. The Fed's next meeting
      is expected to maintain current interest rates. Consumer spending data released
      today showed resilience despite inflation concerns.

  - path: "research/competitor_intelligence.txt"
    content: |
      Competitor Intelligence Brief - Daily Update
      Prepared by: Intelligence Team

      === COMPETITOR A (Nexus Technologies) ===
      - Launched new AI assistant product "NexusAI" targeting enterprise customers
      - Pricing: $99/user/month, undercutting our premium tier by 15%
      - Early reviews mention strong integration capabilities but limited customization
      - Hired 3 senior engineers from our ML team last month (ongoing retention concern)

      === COMPETITOR B (DataFlow Inc) ===
      - Announced Series D funding of $180M at $2.1B valuation
      - Planning expansion into European markets Q2 2026
      - New partnership with Microsoft for Azure integration
      - CEO quoted saying they aim to "dominate the mid-market segment"

      === COMPETITOR C (SwiftCloud) ===
      - Experiencing service outages (3rd incident this month)
      - Customer complaints increasing on social media
      - Opportunity: Their enterprise clients may be looking for alternatives
      - Our sales team should prioritize outreach to SwiftCloud's top 50 accounts

      === STRATEGIC RECOMMENDATIONS ===
      1. Accelerate enterprise AI features to counter Nexus launch
      2. Review pricing strategy for premium tier
      3. Strengthen employee retention programs
      4. Develop targeted campaign for SwiftCloud defectors

  - path: "research/customer_feedback.txt"
    content: |
      Customer Feedback Summary - Daily Digest
      Date: February 15, 2026
      Compiled by: Customer Success Team

      SUPPORT TICKETS (Last 24 hours):
      - Total: 247 tickets
      - Critical: 12 (down from 18 yesterday)
      - High Priority: 45
      - Medium/Low: 190

      TOP ISSUES:
      1. API rate limiting errors (34 tickets) - Engineering investigating
      2. Dashboard loading slowly (28 tickets) - Related to yesterday's update
      3. Export feature not working for large datasets (19 tickets) - Known issue, fix ETA Monday
      4. Mobile app crashes on Android 14 (15 tickets) - New issue, escalated to mobile team

      POSITIVE FEEDBACK HIGHLIGHTS:
      - "The new reporting feature saved our team 10 hours this week" - Enterprise client
      - "Best customer support I've experienced in SaaS" - NPS score 72 this month
      - 3 case studies approved by customers for marketing use
      - 15 new G2 reviews, average rating 4.6 stars

      CHURN RISK ALERTS:
      - MegaCorp (ARR $450K) - Evaluating competitors, exec meeting scheduled
      - TechStart (ARR $85K) - Missed renewal call, follow-up required
      - GlobalRetail (ARR $220K) - Budget cuts mentioned, may downgrade

      UPSELL OPPORTUNITIES:
      - FinanceHub (current ARR $120K) - Interested in enterprise tier
      - HealthTech (current ARR $95K) - Expanding team, needs more seats

  - path: "research/product_updates.txt"
    content: |
      Product & Engineering Daily Standup Notes
      Date: February 15, 2026
      Sprint: Phoenix-23 (Day 8 of 14)

      SHIPPED TODAY:
      ✓ Real-time collaboration feature (beta) - 500 users enrolled
      ✓ Performance improvements to dashboard (40% faster load times)
      ✓ Bug fix: CSV export encoding issues resolved
      ✓ Security patch: XSS vulnerability in comments section

      IN PROGRESS:
      → AI-powered insights feature (65% complete, on track for Feb 28)
      → Mobile app v3.0 redesign (80% complete, QA starting Monday)
      → API v2 migration tools (40% complete)
      → SOC 2 Type II audit preparation (documentation phase)

      BLOCKED:
      ⚠ Third-party payment integration - waiting on vendor API access
      ⚠ Enterprise SSO feature - Legal reviewing data processing agreement

      UPCOMING RELEASES (Next 2 weeks):
      - Feb 18: AI insights beta launch to 1000 users
      - Feb 21: Mobile app v3.0 public release
      - Feb 25: New pricing page and plan comparison tool
      - Feb 28: API v2 general availability

      TECHNICAL DEBT:
      - Scheduled database migration this weekend (Saturday 2am-6am EST)
      - Expected 30-minute downtime, customers notified

  - path: "research/industry_news.txt"
    content: |
      Industry News Roundup - February 15, 2026

      REGULATORY DEVELOPMENTS:
      - EU AI Act enforcement begins March 1, 2026
        * Companies must disclose AI-generated content
        * Fines up to 6% of global revenue for violations
        * Our compliance team confirms we're ready

      - California Consumer Privacy Act amendment proposed
        * Would require explicit consent for data sharing
        * Tech industry lobbying against stricter requirements

      INDUSTRY TRENDS:
      - Gartner Report: Enterprise AI spending to reach $280B by 2027
      - McKinsey Study: 67% of companies plan to increase SaaS budgets in 2026
      - Remote work tools market growing 18% annually

      NOTABLE FUNDING ROUNDS THIS WEEK:
      - AIStartup raised $500M Series E (largest AI funding this year)
      - WorkflowTool raised $75M Series B
      - SecurityFirst raised $120M Series C

      PARTNERSHIPS & ACQUISITIONS:
      - Salesforce + Anthropic: Expanded AI partnership announced
      - Google acquired DocuAI for $1.8B
      - Microsoft investing $2B in OpenAI competitors

      CONFERENCES & EVENTS:
      - TechCrunch Disrupt (Feb 20-22, San Francisco) - Our CEO speaking
      - SaaStr Annual (March 10-12, Phoenix) - We're a Gold Sponsor
      - Enterprise Connect (March 25-28, Orlando) - Booth #342
---

## Prompt

你是一名行政助理，正在准备每日简报。请审阅 research/ 文件夹中的所有文件，并将一份全面的每日摘要写入 daily_briefing.md。摘要应简洁，突出最需要高管关注的事项，并以清晰的章节组织。

## Expected Behavior

Agent 应当：

1. 发现并读取 `research/` 目录中的所有文件
2. 分析并综合来自多个来源的信息：
   - 市场分析数据
   - 竞争对手情报
   - 客户反馈
   - 产品更新
   - 行业新闻
3. 创建一份组织良好的每日简报，做到：
   - 以简短的执行摘要开篇（3-5 个关键要点）
   - 将信息组织为合乎逻辑的章节
   - 突出需要立即关注或决策的事项
   - 注明任何风险或机会
   - 保持摘要简洁（目标 500-800 字）
4. 将简报保存到 `daily_briefing.md`

本任务测试 Agent 以下能力：

- 探索并发现目录中的文件
- 阅读并理解多份文档
- 综合来自不同来源的信息
- 对关键信息进行优先级排序和突出
- 撰写专业的高管沟通材料

## Grading Criteria

- [ ] Agent 发现了 research/ 目录中的文件
- [ ] Agent 读取了全部 5 个调研文件
- [ ] 已创建文件 `daily_briefing.md`
- [ ] 摘要包含执行摘要章节
- [ ] 摘要涵盖市场/金融信息
- [ ] 摘要涵盖竞争对手情报
- [ ] 摘要涵盖客户反馈/风险
- [ ] 摘要涵盖产品更新
- [ ] 摘要涵盖行业新闻/监管事项
- [ ] 摘要识别出行动项或所需决策
- [ ] 文笔专业且适合高管阅读
- [ ] 摘要长度适当简洁（不冗长）

## LLM Judge Rubric

### Criterion 1: Information Coverage and Accuracy (Weight: 30%)

**Score 1.0**：摘要准确捕捉全部五份源文档的关键信息。包含市场走势、竞争对手威胁（尤其是 Nexus 发布和 SwiftCloud 机会）、客户风险（MegaCorp 流失风险）、产品里程碑（已发布功能、即将发布的版本）和监管事项（EU AI Act）。无重大遗漏或事实错误。

**Score 0.75**：摘要涵盖来自 4-5 个来源的大多数重要信息，仅有轻微遗漏。关键事项齐全，但部分次要细节缺失。

**Score 0.5**：摘要涵盖 3-4 个来源，但遗漏一份或多份文档中的重要事项。可能有轻微不准确。

**Score 0.25**：摘要仅涵盖 1-2 个来源，或有重大事实错误。严重遗漏关键信息。

**Score 0.0**：摘要缺失、不准确，或未能纳入调研文件。

### Criterion 2: Synthesis and Prioritization (Weight: 25%)

**Score 1.0**：跨来源综合出色。正确识别最高优先级事项：竞争对手产品发布威胁、MegaCorp 流失风险、EU AI Act 截止日期、SwiftCloud 机会。关联相关信息（例如竞争对手定价与我方留存）。紧急事项与信息性事项区分清晰。

**Score 0.75**：综合良好，识别出大多数优先事项。在优先级排序或关联相关信息方面有轻微问题。

**Score 0.5**：存在基本综合，但优先级排序较弱。重要事项可能被淹没，或与次要事项被等同对待。

**Score 0.25**：综合较差——大多只是罗列各来源的信息，缺乏有意义的整合或优先级排序。

**Score 0.0**：未尝试综合，或优先级完全错误。

### Criterion 3: Structure and Organization (Weight: 20%)

**Score 1.0**：组织专业，顶部有清晰的执行摘要、合乎逻辑的章节标题、易于浏览的格式。有效使用要点、加粗或其他格式。章节衔接流畅。行动项明确标出。

**Score 0.75**：组织良好，章节和执行摘要清晰。有轻微结构问题或格式不一致。

**Score 0.5**：存在基本结构，但组织可改进。可能缺少执行摘要或章节划分不清。

**Score 0.25**：组织较差，难以找到关键信息。杂乱或大段文字堆砌的格式。

**Score 0.0**：无可辨识的结构或组织。

### Criterion 4: Writing Quality and Tone (Weight: 15%)

**Score 1.0**：文笔专业，适合高管阅读。语言简洁、清晰、以行动为导向。无未加解释的术语。详略程度适合 C 级高管受众。语法和拼写完美。

**Score 0.75**：专业文笔良好，仅有轻微问题。语气总体恰当，偶有冗长或表述不清。

**Score 0.5**：文笔尚可，但语气可能不适合高管。可能过于随意、过于详细，或有明显语法/拼写问题。

**Score 0.25**：文笔较差。语气不专业、表达不清，或有多处错误。

**Score 0.0**：文笔难以理解或完全不恰当。

### Criterion 5: Conciseness and Length (Weight: 10%)

**Score 1.0**：摘要适当简洁（500-800 字），在不牺牲清晰度的前提下保持高信息密度。无冗余或填充内容。

**Score 0.75**：略超或略低于目标长度（400-500 或 800-1000 字），但仍有效。有轻微冗余。

**Score 0.5**：明显过长（1000-1500 字）或过短（200-400 字）。有些填充内容，或因过简而遗漏重要细节。

**Score 0.25**：显著过长（>1500 字）或过短（<200 字），难以有效使用。

**Score 0.0**：长度完全不恰当或内容缺失。

## Additional Notes

本任务测试一个常见的真实场景：AI 助理从多个来源收集信息并创建综合摘要。关键挑战包括：

1. **发现**：Agent 必须主动探索 research/ 目录，而非被告知确切读取哪些文件
2. **优先级排序**：并非所有信息同等重要——Agent 必须识别出最重要的内容
3. **综合**：跨来源关联信息（例如竞争对手定价影响留存）
4. **受众意识**：为高管撰写需要不同于技术文档的风格

预置数据有意包含：

- 时间敏感事项（EU AI Act 截止日期、竞争对手发布）
- 需要关注的风险事项（流失风险、召回新闻）
- 机会（SwiftCloud 流失客户、追加销售线索）
- 正面/负面消息的混合，以测试平衡报告能力
