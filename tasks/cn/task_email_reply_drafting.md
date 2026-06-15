---
id: task_email_reply_drafting
name: 根据未读收件箱起草邮件回复
category: 写作
scene: 内容创作、PPT、网页与多媒体生成
sub_scene: 邮件回复起草
difficulty: L2
capabilities:
- 自然语言生成
- 指令遵循与约束理解
- 数据提取与处理
- 输出格式适配
- 工具调用
grading_type: llm_judge
timeout_seconds: 240
workspace_files:
  - path: "inbox/unread_01_vendor_security_followup.txt"
    content: |
      From: rachel.owens@vendorco.com (Rachel Owens, VendorCo Security)
      To: me@mycompany.com
      Date: Tue, 07 Apr 2026 08:12:00 -0500
      Subject: Follow-up: Security questionnaire due tomorrow

      Hi,

      Quick reminder that we still need your completed security questionnaire by
      tomorrow (April 8) to keep your procurement onboarding on schedule.

      If we don't receive it by EOD tomorrow, legal review and contract signing may
      slip into next week.

      Please let me know if you need an extension.

      Thanks,
      Rachel

  - path: "inbox/unread_02_customer_escalation.txt"
    content: |
      From: tom.garcia@northstarhealth.com (Tom Garcia, Northstar Health)
      To: support@mycompany.com, me@mycompany.com
      Date: Tue, 07 Apr 2026 09:03:00 -0500
      Subject: Escalation: Data export failed before board meeting

      Team,

      Our scheduled compliance export failed again this morning with a timeout.
      We have a board packet deadline today at 3:00 PM ET and need the export ASAP.

      This is now the third failure in two weeks and we need an immediate update,
      including ETA and whether there's a workaround.

      Please treat this as urgent.

      -Tom

  - path: "inbox/unread_03_internal_review_request.txt"
    content: |
      From: priya.nair@mycompany.com (Priya Nair, Product)
      To: me@mycompany.com
      Date: Tue, 07 Apr 2026 10:14:00 -0500
      Subject: Quick review request: onboarding tooltip copy

      Hey,

      Could you review the revised onboarding tooltip text and leave comments by
      Thursday afternoon? It's a short doc (~15 mins).

      Draft: https://docs.mycompany.com/onboarding-tooltips-v3

      Thanks!
      Priya

  - path: "inbox/unread_04_newsletter.txt"
    content: |
      From: newsletter@devweekly.io
      To: me@mycompany.com
      Date: Tue, 07 Apr 2026 06:00:00 -0500
      Subject: DevWeekly #242 - Databases at scale

      This week:
      - Postgres indexing deep dive
      - Incident write-ups from top infra teams
      - New OSS observability tools

      Read online: https://devweekly.io/issues/242

  - path: "inbox/unread_05_partner_meeting_reschedule.txt"
    content: |
      From: emily.cho@alliancepartners.com (Emily Cho, Alliance Partners)
      To: me@mycompany.com
      Date: Tue, 07 Apr 2026 11:25:00 -0500
      Subject: Need to reschedule Thursday partner sync

      Hi,

      I have a customer workshop conflict and need to move our Thursday 2:30 PM ET
      partner sync. Could we do Friday between 10:00 AM-12:00 PM ET instead?

      If Friday does not work, please suggest a couple alternatives next week.

      Best,
      Emily
---

## Prompt

你在 `inbox/` 文件夹中有 5 封未读邮件（`unread_01` 到 `unread_05`）。

阅读所有未读邮件，并为那些需要回复的邮件起草回复。将你的输出保存到 `reply_drafts.md`。

要求：

1. 只为需要回复的邮件起草回复（不要为低价值的资讯邮件起草回复）。
2. 对每一份起草的回复，包含：
   - 来源邮件文件名
   - 主题行（使用 `Re:` 样式）
   - 专业且贴合上下文的正文
3. 根据每种情况调整语气和紧迫程度（客户升级问题应紧迫且体现担当；内部请求可以简洁）。
4. 如果你没有足够信息完全解决某事，请予以承认，并提供明确的下一步或时间线。
5. 每份回复保持简洁但完整。

## Expected Behavior

Agent 应检查全部 5 封邮件并判断哪些需要采取行动。它应跳过资讯邮件，并为与业务运营相关的邮件起草回复：

- 供应商安全问卷提醒
- 关于导出失败的客户升级问题
- 内部审阅请求
- 合作伙伴会议改期

优秀的回复应因情境而异：

- **客户升级问题**：立即承担责任、致歉、给出具体的下次更新时间，并在可能时提供变通方案。
- **供应商截止期限**：确认收到、给出承诺或附带具体日期/时间的延期请求。
- **内部请求**：简短确认，并给出符合实际的完成时间。
- **合作伙伴排期**：接受或反向提出明确的时间。

输出文件 `reply_drafts.md` 应易于浏览，并清晰地区分每一份草稿，例如为每封来源邮件设置标题。

## Grading Criteria

- [ ] 文件 `reply_drafts.md` 已创建
- [ ] 全部 5 封未读邮件都已审阅
- [ ] 为需要回复的邮件（01、02、03、05）包含了回复草稿
- [ ] 没有为资讯邮件（04）撰写多余的草稿
- [ ] 每份草稿包含来源文件名和 `Re:` 主题
- [ ] 语气贴合上下文和紧迫程度
- [ ] 客户升级问题的回复体现担当和近期内的下一步
- [ ] 供应商/合作伙伴的回复包含具体的排期或时间承诺
- [ ] 草稿简洁、专业、可执行

## LLM Judge Rubric

### Criterion 1: Coverage and Filtering (Weight: 25%)

**Score 1.0**: 审阅了全部 5 封邮件，为 01/02/03/05 起草了回复，并正确地未为资讯邮件（04）起草回复。

**Score 0.75**: 正确起草了大多数必要的回复，仅有一处细微的筛选错误（例如包含了资讯邮件或漏掉一封必要回复）。

**Score 0.5**: 覆盖不全，有多处遗漏或多余草稿。

**Score 0.25**: 覆盖极少；对哪些邮件需要回复存在重大误解。

**Score 0.0**: 没有产出有意义的回复集合。

### Criterion 2: Response Quality and Professionalism (Weight: 25%)

**Score 1.0**: 草稿精炼、专业、简洁，并针对每位收件人量身定制。语气和结构都适合邮件场景。

**Score 0.75**: 总体上专业写作出色，仅有细微的语气/清晰度问题。

**Score 0.5**: 可以理解，但语气笼统或不均衡；部分草稿显得不够专业或别扭。

**Score 0.25**: 草稿写得很差，存在明显的专业性问题。

**Score 0.0**: 草稿无法使用或缺失。

### Criterion 3: Urgency Handling and Accountability (Weight: 25%)

**Score 1.0**: 升级问题的回复清晰承认影响、承担责任，并给出具体的下次更新时间或立即行动路径；对截止期限敏感的邮件给出明确承诺。

**Score 0.75**: 识别出了紧迫性并给出大体清晰的承诺，但有一个关键细节含糊。

**Score 0.5**: 提及紧迫性，但缺乏具体承诺或担当性的表述。

**Score 0.25**: 未能恰当处理紧迫性；回复过于随意或不作承诺。

**Score 0.0**: 没有紧迫性意识。

### Criterion 4: Actionability and Next Steps (Weight: 15%)

**Score 1.0**: 每份草稿在需要之处都包含清晰的下一步、时间线或排期细节。

**Score 0.75**: 大多数草稿包含可执行的下一步，仅有细微缺口。

**Score 0.5**: 有一定可执行性，但若干草稿仍然含糊。

**Score 0.25**: 可执行内容极少。

**Score 0.0**: 草稿中没有明确的下一步。

### Criterion 5: Output Structure and Usability (Weight: 10%)

**Score 1.0**: `reply_drafts.md` 按来源邮件清晰组织，每份草稿包含文件名、主题和正文；易于审阅和发送。

**Score 0.75**: 结构大体清晰，仅有细微的格式不一致。

**Score 0.5**: 基本结构存在，但难以浏览。

**Score 0.25**: 组织混乱或缺少必需字段。

**Score 0.0**: 输出缺失或无法使用。

## Additional Notes

本任务评估实用的邮件协助能力：对未读邮件进行分诊，并在不同紧迫程度下产出高质量草稿。关键挑战在于平衡筛选（不回复噪声邮件）与因情境而异的沟通质量。
