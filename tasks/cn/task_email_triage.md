---
id: task_email_triage
name: 邮件收件箱分类
category: 生产力
scene: 数据库检索、表格整理与数据分析
sub_scene: 邮件分类
difficulty: L2
capabilities:
- 指令遵循与约束理解
- 数据提取与处理
- 多步推理
- 输出格式适配
- 自然语言生成
grading_type: hybrid
timeout_seconds: 240
grading_weights:
  automated: 0.4
  llm_judge: 0.6
workspace_files:
  - path: "inbox/email_01.txt"
    content: |
      From: cto@mycompany.com (David Park, CTO)
      To: me@mycompany.com
      Date: Mon, 17 Feb 2026 08:02:00 -0500
      Subject: URGENT: Production database outage - all hands needed

      Our primary production database cluster went down at 7:45am EST. Customer-facing
      services are returning 500 errors. SRE team is engaged but we need all backend
      engineers on the war room bridge call immediately.

      War room link: https://meet.mycompany.com/war-room-prod
      Incident channel: #incident-db-20260217

      This is a P0 incident. Drop everything else until this is resolved.

      -David

  - path: "inbox/email_02.txt"
    content: |
      From: sarah.marketing@mycompany.com (Sarah Liu, Marketing Director)
      To: me@mycompany.com
      Date: Mon, 17 Feb 2026 09:15:00 -0500
      Subject: Blog post review needed by EOD Wednesday

      Hi,

      We have a new blog post about our Q4 product updates that needs a technical
      accuracy review. It's about 1,200 words. Could you take a look and flag anything
      that's incorrect or misleading? No rush - end of day Wednesday works.

      Draft link: https://docs.mycompany.com/blog-q4-review

      Thanks!
      Sarah

  - path: "inbox/email_03.txt"
    content: |
      From: noreply@github.com
      To: me@mycompany.com
      Date: Mon, 17 Feb 2026 07:30:00 -0500
      Subject: [mycompany/api-gateway] Pull request #482: Dependency updates (Dependabot)

      Dependabot has opened a pull request to update the following dependencies:

      - express: 4.18.2 → 4.19.0 (minor)
      - lodash: 4.17.21 → 4.17.22 (patch)
      - @types/node: 20.10.0 → 20.11.0 (minor)

      All CI checks are passing. No breaking changes detected.

      View pull request: https://github.com/mycompany/api-gateway/pull/482

  - path: "inbox/email_04.txt"
    content: |
      From: jenna.hr@mycompany.com (Jenna Walsh, HR)
      To: all-staff@mycompany.com
      Date: Fri, 14 Feb 2026 16:00:00 -0500
      Subject: Reminder: Benefits enrollment deadline is Feb 28

      Hi everyone,

      Just a friendly reminder that the annual benefits enrollment window closes on
      February 28, 2026. If you haven't reviewed your selections, please log into
      the HR portal and make any changes before the deadline.

      Key items:
      - Health insurance plan selection
      - 401(k) contribution changes
      - FSA/HSA elections
      - Life insurance beneficiary updates

      Portal link: https://hr.mycompany.com/benefits

      If you have questions, reach out to the HR team.

      Thanks,
      Jenna

  - path: "inbox/email_05.txt"
    content: |
      From: mike.chen@bigclient.com (Mike Chen, VP Engineering)
      To: me@mycompany.com
      Date: Mon, 17 Feb 2026 08:45:00 -0500
      Subject: Re: API integration timeline

      Hi,

      Following up on our call last week. Our board approved the integration project
      and we'd like to move forward. We need to finalize the API contract and get
      staging credentials set up ASAP so our team can start development.

      Can we schedule a 30-minute call this week? Tuesday or Thursday afternoon works
      best for us. This is a $2M annual contract so we want to keep momentum.

      Also, our security team will need to complete a vendor assessment. Could you
      send over your SOC 2 report and data processing agreement?

      Best,
      Mike Chen
      VP Engineering, BigClient Inc.

  - path: "inbox/email_06.txt"
    content: |
      From: noreply@linkedin.com
      To: me@mycompany.com
      Date: Sun, 16 Feb 2026 14:22:00 -0500
      Subject: You have 3 new connection requests

      You have new connection requests from:
      - Alex Turner, Software Engineer at TechCorp
      - Maria Santos, Product Manager at StartupXYZ
      - Kevin Park, Recruiter at TopTalent Agency

      View and respond to your invitations:
      https://linkedin.com/notifications

  - path: "inbox/email_07.txt"
    content: |
      From: team-lead@mycompany.com (Rachel Green, Engineering Manager)
      To: me@mycompany.com
      Date: Mon, 17 Feb 2026 09:30:00 -0500
      Subject: Performance review self-assessment due Friday

      Hi,

      Quick reminder that your annual performance review self-assessment is due this
      Friday, Feb 21. Please fill out the form I shared last week covering:

      1. Key accomplishments from the past year
      2. Areas for growth
      3. Goals for the next review period
      4. Any feedback on team processes

      Form link: https://hr.mycompany.com/perf-review/2026

      Let me know if you have any questions. I'll be scheduling our 1:1 review
      meeting for the following week.

      Rachel

  - path: "inbox/email_08.txt"
    content: |
      From: security@mycompany.com (Security Team)
      To: engineering@mycompany.com
      Date: Mon, 17 Feb 2026 07:00:00 -0500
      Subject: IMPORTANT: Mandatory password rotation by Feb 19

      As part of our quarterly security compliance, all engineering team members
      must rotate their passwords and SSH keys by Wednesday, February 19, 2026.

      Required actions:
      1. Change your SSO password via https://sso.mycompany.com/reset
      2. Rotate your SSH keys on all company repositories
      3. Update any personal access tokens older than 90 days
      4. Confirm completion by replying to this email

      Failure to comply by the deadline may result in temporary account lockout.

      Security Team

  - path: "inbox/email_09.txt"
    content: |
      From: newsletter@techdigest.io
      To: me@mycompany.com
      Date: Mon, 17 Feb 2026 06:00:00 -0500
      Subject: TechDigest Weekly: AI agents are reshaping software development

      This week in tech:

      → AI coding agents now write 40% of code at top tech companies
      → New study shows remote engineers are 15% more productive
      → Rust adoption surges in cloud-native development
      → OpenAI announces GPT-5 release date
      → Kubernetes 1.32 brings major networking improvements

      Read the full digest: https://techdigest.io/weekly/2026-02-17

      Unsubscribe: https://techdigest.io/unsubscribe

  - path: "inbox/email_10.txt"
    content: |
      From: alice.wong@mycompany.com (Alice Wong, Senior Engineer)
      To: me@mycompany.com
      Date: Mon, 17 Feb 2026 09:50:00 -0500
      Subject: Code review request - auth service refactor

      Hey,

      I just pushed a pretty significant refactor of the auth service to handle
      the new OAuth2 PKCE flow. It's about 800 lines changed across 12 files.
      I'd really appreciate your review since you wrote the original auth module.

      PR link: https://github.com/mycompany/auth-service/pull/156

      The key changes:
      - Replaced implicit flow with PKCE
      - Added token rotation logic
      - New middleware for session validation
      - Updated all integration tests

      I'd like to merge by Thursday if possible since it blocks the mobile app release.
      Let me know if you need more context on any of the changes.

      Thanks,
      Alice

  - path: "inbox/email_11.txt"
    content: |
      From: deals@saastools.com
      To: me@mycompany.com
      Date: Sat, 15 Feb 2026 10:00:00 -0500
      Subject: 🔥 Flash Sale: 60% off all annual plans - 48 hours only!

      LIMITED TIME OFFER!

      Upgrade your development workflow with SaaSTools Pro:
      ✅ Advanced CI/CD pipelines
      ✅ Real-time monitoring
      ✅ Unlimited team members

      Regular price: $299/year
      FLASH SALE: $119/year

      Use code FLASH60 at checkout.

      This offer expires Monday at midnight!

      Shop now: https://saastools.com/pricing

  - path: "inbox/email_12.txt"
    content: |
      From: cfo@mycompany.com (Linda Zhao, CFO)
      To: engineering-leads@mycompany.com
      Date: Mon, 17 Feb 2026 08:30:00 -0500
      Subject: Q1 budget reconciliation - action needed by Thursday

      Hi team leads,

      Finance is closing out Q1 budget projections and we need each team to review
      and confirm their spending against allocated budgets. Specifically:

      1. Verify cloud infrastructure costs (AWS/GCP) for Jan-Feb
      2. Flag any anticipated overruns for March
      3. Submit any pending purchase requests before the March 1 cutoff

      Please fill out the budget tracker: https://docs.mycompany.com/q1-budget

      Need responses by end of day Thursday, Feb 20. If your team is trending
      over budget, let's schedule a quick sync to discuss.

      Thanks,
      Linda

  - path: "inbox/email_13.txt"
    content: |
      From: automated-alerts@monitoring.mycompany.com
      To: oncall@mycompany.com, me@mycompany.com
      Date: Mon, 17 Feb 2026 07:48:00 -0500
      Subject: [ALERT] API latency exceeding threshold - p99 > 2000ms

      MONITORING ALERT

      Service: api-gateway
      Metric: p99 latency
      Current value: 3,247ms (threshold: 2,000ms)
      Duration: 3 minutes
      Status: FIRING

      Affected endpoints:
      - POST /api/v1/transactions (p99: 4,102ms)
      - GET /api/v1/accounts (p99: 2,891ms)
      - POST /api/v1/auth/token (p99: 3,415ms)

      Dashboard: https://grafana.mycompany.com/d/api-latency
      Runbook: https://wiki.mycompany.com/runbooks/api-latency

      This alert correlates with the ongoing database incident (INC-20260217-001).
---

## Prompt

你正在协助分类一个堆积的邮件收件箱。这些邮件已放置在你工作区的 `inbox/` 文件夹下（文件名为 `email_01.txt` 到 `email_13.txt`）。阅读全部 13 封邮件，并创建一份分类报告保存为 `triage_report.md`。对每封邮件，分配：

1. **Priority**：P0（放下一切处理）、P1（今日处理）、P2（本周处理）、P3（方便时处理）、P4（无需处理 / 归档）
2. **Category**：以下之一："incident"、"client"、"internal-request"、"administrative"、"code-review"、"automated"、"newsletter"、"spam"
3. **Recommended action**：用 1-2 句简要描述应当采取的行动

报告中的邮件按优先级排序（最紧急的在前）。在顶部包含一段简要的 summary 部分，突出最关键的事项，并给出当日工作计划建议。

## Expected Behavior

Agent 应：

1. 发现并阅读 `inbox/` 目录下全部 13 封邮件文件
2. 对每封邮件分析其紧急程度、发件人重要性、截止时间和内容
3. 在分配优先级时考虑以下因素：
   - 生产事故为 P0
   - 高价值客户沟通为 P1
   - 安全合规截止事项为 P1-P2
   - 带截止时间的同事代码评审为 P2
   - 带截止时间的行政事项为 P2
   - Newsletter 与社交通知为 P3-P4
   - 垃圾/促销邮件为 P4
4. 正确归类每封邮件
5. 为每封邮件提供具体可执行的建议
6. 创建按优先级排序、结构化、易于浏览的报告
7. 包含顶部摘要与建议的当日计划
8. 将报告保存为 `triage_report.md`

本任务考察 Agent 的能力：

- 处理一批异构输入
- 运用判断对信息进行分类与排序
- 识别上下文线索（例如监控告警与数据库故障相关）
- 区分紧急、重要与低价值事项
- 产出结构化、可执行的输出

## Grading Criteria

- [ ] Agent 发现并读取了 inbox/ 中全部 13 封邮件
- [ ] 创建了 `triage_report.md` 文件
- [ ] 报告中包含全部 13 封邮件
- [ ] 每封邮件均分配了优先级（P0-P4）
- [ ] 每封邮件均分配了类别
- [ ] 每封邮件均给出了推荐操作
- [ ] 生产故障邮件（01）被分类为 P0
- [ ] 监控告警（13）与故障关联或归在同组
- [ ] 客户邮件（05）被分类为高优先级（P0 或 P1）
- [ ] 垃圾/促销邮件（11）被分类为 P4
- [ ] 报告按优先级排序（最紧急的在前）
- [ ] 报告顶部存在摘要部分

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the email triage task based on structural correctness and key priority assignments.

    Args:
        transcript: Parsed JSONL transcript as list of dicts
        workspace_path: Path to the task's isolated workspace directory

    Returns:
        Dict mapping criterion names to scores (0.0 to 1.0)
    """
    from pathlib import Path
    import re

    scores = {}
    workspace = Path(workspace_path)

    # Check if triage_report.md exists
    report_file = workspace / "triage_report.md"

    if not report_file.exists():
        return {
            "file_created": 0.0,
            "all_emails_covered": 0.0,
            "priorities_assigned": 0.0,
            "categories_assigned": 0.0,
            "actions_assigned": 0.0,
            "outage_is_p0": 0.0,
            "alert_linked_to_outage": 0.0,
            "client_is_high_priority": 0.0,
            "spam_is_low_priority": 0.0,
            "sorted_by_priority": 0.0,
            "has_summary_section": 0.0,
        }

    scores["file_created"] = 1.0
    content = report_file.read_text()
    content_lower = content.lower()

    # Check all 13 emails are covered.
    # Look for references to email subjects or senders as indicators.
    email_indicators = [
        r"(production database outage|war room|p0 incident|david park)",
        r"(blog post review|sarah.?liu|marketing|q4 product)",
        r"(dependabot|pull request #?482|dependency update)",
        r"(benefits enrollment|jenna walsh|feb(ruary)?\s*28)",
        r"(bigclient|mike chen|\$2m|api integration timeline)",
        r"(linkedin|connection request)",
        r"(performance review|self.?assessment|rachel green)",
        r"(password rotation|ssh key|security compliance|feb(ruary)?\s*19)",
        r"(techdigest|newsletter|weekly.*ai agent)",
        r"(auth service refactor|alice wong|oauth2?\s*pkce|pr.*#?156)",
        r"(flash sale|saastools|60%\s*off|spam)",
        r"(budget reconciliation|linda zhao|cfo|q1 budget)",
        r"(api latency|monitoring alert|\[alert\]|p99.*2000)",
    ]

    found_emails = 0
    for pattern in email_indicators:
        if re.search(pattern, content_lower):
            found_emails += 1

    scores["all_emails_covered"] = found_emails / 13.0

    # Check priorities are assigned (look for P0-P4 labels)
    priority_matches = re.findall(r'\bP[0-4]\b', content, re.IGNORECASE)
    if len(priority_matches) >= 13:
        scores["priorities_assigned"] = 1.0
    elif len(priority_matches) >= 10:
        scores["priorities_assigned"] = 0.75
    elif len(priority_matches) >= 6:
        scores["priorities_assigned"] = 0.5
    elif len(priority_matches) >= 1:
        scores["priorities_assigned"] = 0.25
    else:
        scores["priorities_assigned"] = 0.0

    # Check categories are assigned
    category_keywords = [
        "incident", "client", "internal", "administrative", "admin",
        "code.?review", "automated", "newsletter", "spam", "promotional",
    ]
    categories_found = sum(
        1 for kw in category_keywords
        if re.search(kw, content_lower)
    )
    if categories_found >= 6:
        scores["categories_assigned"] = 1.0
    elif categories_found >= 4:
        scores["categories_assigned"] = 0.75
    elif categories_found >= 2:
        scores["categories_assigned"] = 0.5
    else:
        scores["categories_assigned"] = 0.0

    # Check recommended actions exist (look for action-oriented language near each email)
    action_patterns = [
        r"(action|respond|reply|review|schedule|join|ignore|archive|complete|submit|fill|approve|merge|delete|unsubscribe|forward|delegate|attend|read|dismiss)",
    ]
    action_count = len(re.findall(action_patterns[0], content_lower))
    if action_count >= 13:
        scores["actions_assigned"] = 1.0
    elif action_count >= 8:
        scores["actions_assigned"] = 0.75
    elif action_count >= 4:
        scores["actions_assigned"] = 0.5
    else:
        scores["actions_assigned"] = 0.25

    # Check production outage (email 01) is P0
    # Look for P0 near the outage-related content
    outage_section = ""
    # Try to find the section about the outage
    outage_matches = list(re.finditer(
        r'(production database outage|david park|war room|cto)',
        content_lower
    ))
    if outage_matches:
        # Get surrounding context (500 chars around first match)
        start = max(0, outage_matches[0].start() - 200)
        end = min(len(content_lower), outage_matches[0].end() + 300)
        outage_section = content_lower[start:end]

    if re.search(r'\bp0\b', outage_section, re.IGNORECASE):
        scores["outage_is_p0"] = 1.0
    elif re.search(r'\bp1\b', outage_section, re.IGNORECASE):
        scores["outage_is_p0"] = 0.5
    else:
        scores["outage_is_p0"] = 0.0

    # Check monitoring alert (email 13) is linked to the outage
    alert_section = ""
    alert_matches = list(re.finditer(
        r'(api latency|monitoring alert|\balert\b.*threshold|p99)',
        content_lower
    ))
    if alert_matches:
        start = max(0, alert_matches[0].start() - 200)
        end = min(len(content_lower), alert_matches[0].end() + 500)
        alert_section = content_lower[start:end]

    if re.search(r'(relat|correlat|connect|linked|same.*incident|outage|database|incident)', alert_section):
        scores["alert_linked_to_outage"] = 1.0
    elif re.search(r'\bp0\b', alert_section, re.IGNORECASE):
        scores["alert_linked_to_outage"] = 0.75
    else:
        scores["alert_linked_to_outage"] = 0.0

    # Check client email (email 05, BigClient) is high priority
    client_section = ""
    client_matches = list(re.finditer(
        r'(bigclient|mike chen|\$2m|api integration)',
        content_lower
    ))
    if client_matches:
        start = max(0, client_matches[0].start() - 200)
        end = min(len(content_lower), client_matches[0].end() + 300)
        client_section = content_lower[start:end]

    if re.search(r'\bp[01]\b', client_section, re.IGNORECASE):
        scores["client_is_high_priority"] = 1.0
    elif re.search(r'\bp2\b', client_section, re.IGNORECASE):
        scores["client_is_high_priority"] = 0.5
    else:
        scores["client_is_high_priority"] = 0.0

    # Check spam/promotional email (email 11) is P4
    spam_section = ""
    spam_matches = list(re.finditer(
        r'(flash sale|saastools|60%.*off)',
        content_lower
    ))
    if spam_matches:
        start = max(0, spam_matches[0].start() - 200)
        end = min(len(content_lower), spam_matches[0].end() + 300)
        spam_section = content_lower[start:end]

    if re.search(r'\bp4\b', spam_section, re.IGNORECASE):
        scores["spam_is_low_priority"] = 1.0
    elif re.search(r'\bp3\b', spam_section, re.IGNORECASE):
        scores["spam_is_low_priority"] = 0.75
    else:
        scores["spam_is_low_priority"] = 0.0

    # Check report is sorted by priority (P0 items should appear before P4 items)
    p0_positions = [m.start() for m in re.finditer(r'\bP0\b', content, re.IGNORECASE)]
    p4_positions = [m.start() for m in re.finditer(r'\bP4\b', content, re.IGNORECASE)]

    if p0_positions and p4_positions:
        if max(p0_positions) < min(p4_positions):
            scores["sorted_by_priority"] = 1.0
        elif min(p0_positions) < min(p4_positions):
            scores["sorted_by_priority"] = 0.5
        else:
            scores["sorted_by_priority"] = 0.0
    elif p0_positions or p4_positions:
        scores["sorted_by_priority"] = 0.25
    else:
        scores["sorted_by_priority"] = 0.0

    # Check for summary section at top
    # Summary should appear in the first 20% of the document
    first_chunk = content_lower[:max(len(content_lower) // 5, 200)]
    if re.search(r'(summary|overview|highlights|critical items|day plan|top priorities)', first_chunk):
        scores["has_summary_section"] = 1.0
    elif re.search(r'(summary|overview|highlights)', content_lower):
        scores["has_summary_section"] = 0.5
    else:
        scores["has_summary_section"] = 0.0

    return scores
```

## LLM Judge Rubric

### Criterion 1: Priority Assignment Accuracy (Weight: 30%)

**Score 1.0**：所有优先级分配正确。生产故障（邮件 01）及相关联的监控告警（邮件 13）为 P0。BigClient 跟进（邮件 05）为 P0 或 P1。安全密码轮换（邮件 08）鉴于其 2 天截止期为 P1 或 P2。auth 服务代码评审（邮件 10）鉴于其阻塞发布为 P2。预算核对（邮件 12）为 P2。绩效评审（邮件 07）和博客评审（邮件 02）为 P2-P3。福利提醒（邮件 04）为 P2-P3。Dependabot PR（邮件 03）为 P3。LinkedIn（邮件 06）、newsletter（邮件 09）和促销垃圾邮件（邮件 11）为 P3-P4。无明显错排。

**Score 0.75**：大多数优先级合理，有 1-2 处轻微错排（例如代码评审评得过低或过高）。所有关键事项（故障、客户、安全）均正确识别为高优先级。

**Score 0.5**：若干优先级分配存疑。可能忽视客户邮件或安全截止期的紧迫性。明显的能答对（故障 = P0，垃圾 = P4），但在中间优先级上有困难。

**Score 0.25**：明显错排。可能未能将生产故障识别为最高优先级，或将低价值事项排得过高。优先级方案显得随意。

**Score 0.0**：未分配优先级，或优先级完全错误（例如垃圾邮件排得比生产事故还高）。

### Criterion 2: Categorization Quality (Weight: 15%)

**Score 1.0**：所有邮件正确归类。识别出：incident（邮件 01、13）、client（邮件 05）、internal-request（邮件 02、07、08、10、12）、automated（邮件 03）、newsletter（邮件 09）、spam（邮件 11）、administrative（邮件 04、07）。类别一致且有意义。

**Score 0.75**：大多数类别正确，有 1-2 处轻微误分类。类别来自一个合理的分类体系。

**Score 0.5**：部分类别正确，但若干邮件误分类。可能使用不一致或过于宽泛的类别。

**Score 0.25**：归类糟糕。许多邮件误分类，或类别无意义。

**Score 0.0**：未分配类别或完全错误。

### Criterion 3: Action Recommendations (Weight: 25%)

**Score 1.0**：建议具体、可执行且恰当。例如：对故障建议"立即加入作战室通话"；对客户邮件建议"回复 Mike Chen 提议周二/周四的时间，让客户经理介入，准备 SOC 2 文档"；对垃圾邮件建议"归档/删除"；对代码评审建议"周三前评审 PR #156，重点关注 PKCE 流程更改"。建议体现出对上下文的理解（例如告警与故障相关、代码评审阻塞移动端发布）。

**Score 0.75**：大多数建议良好且可执行。存在轻微问题，例如在 1-2 项上过于含糊或遗漏了上下文关联。

**Score 0.5**：建议存在，但是泛泛而谈（"回复这封邮件"）而非具体。遗漏了关键上下文，如 200 万美元合同价值或代码评审的阻塞发布性质。

**Score 0.25**：建议过于含糊无法实用，或对若干邮件不恰当。

**Score 0.0**：未提供建议或完全无用。

### Criterion 4: Contextual Awareness and Connections (Weight: 15%)

**Score 1.0**：展现出强的上下文推理。明确将监控告警（邮件 13）与生产故障（邮件 01）关联。认识到 BigClient 关系的 200 万美元价值。指出 auth 代码评审阻塞移动端发布。理解安全截止期仅剩 2 天。可能指出故障会影响 BigClient 关系。

**Score 0.75**：建立了大多数关键关联。将告警关联到故障。识别出大多数时间敏感事项及其影响。

**Score 0.5**：建立了 1-2 处关联但遗漏其他。孤立地处理每封邮件而未看到关系。

**Score 0.25**：上下文意识极弱。独立处理每封邮件，无交叉引用。

**Score 0.0**：未建立任何上下文关联。

### Criterion 5: Report Structure and Usability (Weight: 15%)

**Score 1.0**：报告结构良好且可立即执行。顶部有清晰的摘要/当日计划。邮件按优先级组织。使用一致的格式（标题、项目符号、表格）。易于快速浏览。一个忙碌的人扫一眼即可确切知道首先该做什么。

**Score 0.75**：结构良好，存在轻微格式问题。有摘要。总体易于浏览。

**Score 0.5**：有基本结构但可以组织得更好。可能缺少摘要或格式不一致。需要更多精力来提取关键信息。

**Score 0.25**：结构糟糕。难以浏览。无清晰组织或摘要。

**Score 0.0**：输出无结构或无法理解。

## Additional Notes

本任务考察一个实际的、日常的 AI 助手场景：处理一批混合优先级的积压邮件并产出可执行的分类计划。关键挑战包括：

1. **批量处理（Volume processing）**：Agent 必须处理 13 封多样化邮件而不遗漏任何一封
2. **判断决策（Judgment calls）**：优先级分配需要对紧急程度、重要性和截止期进行细致推理
3. **上下文关联（Context linking）**：监控告警（邮件 13）明确提到与数据库事故的关联——优秀的 Agent 应将二者联系起来
4. **干系人意识（Stakeholder awareness）**：认识到一封 200 万美元客户邮件和 CTO 升级与一份 newsletter 分量不同
5. **可执行性（Actionability）**：建议应具体到足以真正执行，而非泛泛的套话

该邮件集合有意包含：

- 一个带相关联告警的明确 P0 事故（考察关联能力）
- 一封高价值客户沟通（考察业务判断）
- 时间敏感的合规事项（考察截止期意识）
- 带下游依赖的同事请求（考察影响评估）
- 低价值噪音：newsletter、社交通知、垃圾邮件（考察过滤能力）
- 截止期各异的行政事项（考察优先级划分的精细度）
