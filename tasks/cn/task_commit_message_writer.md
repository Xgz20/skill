---
id: task_commit_message_writer
name: 提交信息撰写器
category: 写作
scene: 本地环境、命令执行与脚本任务
sub_scene: 提交信息生成
difficulty: L2
capabilities:
- 指令遵循与约束理解
- 数据提取与处理
- 自然语言生成
- 输出格式适配
- 多步推理
grading_type: llm_judge
timeout_seconds: 120
workspace_files:
  - path: "change.diff"
    content: |
      diff --git a/src/auth/session.ts b/src/auth/session.ts
      index 3a1c4e8..b7f2d91 100644
      --- a/src/auth/session.ts
      +++ b/src/auth/session.ts
      @@ -12,8 +12,10 @@ import { Redis } from 'ioredis';
       
       const SESSION_TTL = 3600; // 1 hour
       
      -export async function createSession(userId: string): Promise<string> {
      +export async function createSession(userId: string, rememberMe: boolean = false): Promise<string> {
         const token = crypto.randomUUID();
      +  const ttl = rememberMe ? SESSION_TTL * 24 * 30 : SESSION_TTL;
      +
         const session: Session = {
           userId,
           token,
      @@ -21,7 +23,7 @@ export async function createSession(userId: string): Promise<string> {
           isActive: true,
         };
       
      -  await redis.set(`session:${token}`, JSON.stringify(session), 'EX', SESSION_TTL);
      +  await redis.set(`session:${token}`, JSON.stringify(session), 'EX', ttl);
         await redis.sAdd(`user_sessions:${userId}`, token);
       
         return token;
      @@ -45,3 +47,15 @@ export async function destroySession(token: string): Promise<void> {
         await redis.sRem(`user_sessions:${session.userId}`, token);
         await redis.del(`session:${token}`);
       }
      +
      +export async function refreshSession(token: string): Promise<boolean> {
      +  const raw = await redis.get(`session:${token}`);
      +  if (!raw) return false;
      +
      +  const session: Session = JSON.parse(raw);
      +  const remaining = await redis.ttl(`session:${token}`);
      +  const originalTtl = remaining > SESSION_TTL ? SESSION_TTL * 24 * 30 : SESSION_TTL;
      +
      +  await redis.expire(`session:${token}`, originalTtl);
      +  return true;
      +}
      diff --git a/src/auth/session.test.ts b/src/auth/session.test.ts
      index 8e21f3a..c4d9b72 100644
      --- a/src/auth/session.test.ts
      +++ b/src/auth/session.test.ts
      @@ -22,6 +22,28 @@ describe('createSession', () => {
           expect(parsed.isActive).toBe(true);
         });
       
      +  it('should create a session with extended TTL when rememberMe is true', async () => {
      +    const token = await createSession('user-1', true);
      +    const ttl = await redis.ttl(`session:${token}`);
      +    expect(ttl).toBeGreaterThan(SESSION_TTL);
      +  });
      +});
      +
      +describe('refreshSession', () => {
      +  it('should reset TTL for an active session', async () => {
      +    const token = await createSession('user-1');
      +    // wait a tick so TTL decreases
      +    await new Promise(r => setTimeout(r, 50));
      +    const result = await refreshSession(token);
      +    expect(result).toBe(true);
      +    const ttl = await redis.ttl(`session:${token}`);
      +    expect(ttl).toBeGreaterThan(SESSION_TTL - 5);
      +  });
      +
      +  it('should return false for a nonexistent session', async () => {
      +    const result = await refreshSession('nonexistent-token');
      +    expect(result).toBe(false);
      +  });
       });
       
       describe('destroySession', () => {
---

# Commit Message Writer

## Prompt

阅读 `change.diff` 中的统一格式 diff。为这些改动撰写一条规范、符合约定的提交信息，并保存到 `commit_message.txt`。

要求：

1. 遵循 Conventional Commits 格式：`type(scope): description`
2. 第一行（主题行）必须不超过 72 个字符。
3. 包含正文（用空行隔开），解释这次改动**为什么**要做，而不仅仅是改了什么。
4. 不要在提交信息中包含原始 diff。
5. 信息应为纯文本，不带任何 markdown 格式。

## Expected Behavior

Agent 应阅读 diff 并识别出：

- 在会话创建中新增了 `rememberMe` 选项，带有更长的 TTL。
- 新增了 `refreshSession` 函数用于重置会话 TTL。
- 为这两项改动都添加了相应的测试。

一条优秀的提交信息将会：

- 使用合适的类型（如 `feat`）和作用域（如 `auth` 或 `session`）。
- 有一个简洁的主题行，概括该特性（例如 "add remember-me and session refresh support"）。
- 包含一段正文，解释动机：为选择启用的用户提供持久化会话，以及延长活跃会话的能力。
- 在正文中提及测试覆盖，但不过度展开细节。

## Grading Criteria

- [ ] 创建了文件 `commit_message.txt`
- [ ] 使用 Conventional Commits 格式（`type(scope): description`）
- [ ] 主题行不超过 72 个字符
- [ ] 包含用空行分隔的正文
- [ ] 正文解释了动机/原因，而不只是复述 diff
- [ ] 准确概括了 diff 中的所有改动
- [ ] 输出中没有原始 diff 内容或 markdown 格式

## LLM Judge Rubric

### Criterion 1: Format Compliance (Weight: 25%)

**Score 1.0**：精确遵循 Conventional Commits——正确的类型、可选的作用域、祈使语气的主题行且不超过 72 字符、正文前有空行。

**Score 0.75**：格式基本正确，仅有一处小问题（例如略微超过 72 字符，或缺少作用域）。

**Score 0.5**：可识别为提交信息格式，但在显著方面偏离了 Conventional Commits。

**Score 0.25**：有主题和正文，但没有约定式结构。

**Score 0.0**：不是可识别的提交信息格式。

### Criterion 2: Subject Line Quality (Weight: 25%)

**Score 1.0**：简洁、祈使语气，准确抓住了主要改动（remember-me 会话和/或会话刷新）。不堆砌不必要的细节。

**Score 0.75**：概括良好，但措辞有小问题或范围略宽/略窄。

**Score 0.5**：可以理解，但概括含糊或部分不准确。

**Score 0.25**：有误导性或过于笼统（例如 "update session code"）。

**Score 0.0**：缺少主题行或完全不准确。

### Criterion 3: Body Quality — Motivation and Context (Weight: 30%)

**Score 1.0**：正文清楚解释了改动的原因（例如用户需要持久化会话、会话应可刷新），覆盖了两项特性，并在不过度展开细节的情况下提及了测试新增。

**Score 0.75**：正文提供了良好的背景，但有小缺口（例如遗漏了两项特性之一，或未提及测试）。

**Score 0.5**：有正文，但大多是复述 diff 做了什么，而非为什么。

**Score 0.25**：正文极简，几乎没有在主题行之外增加内容。

**Score 0.0**：没有正文，或正文包含原始 diff／无关内容。

### Criterion 4: Accuracy and Completeness (Weight: 20%)

**Score 1.0**：信息准确反映了所有改动：`rememberMe` 参数、更长的 TTL、新的 `refreshSession` 函数以及相关测试。没有编造细节。

**Score 0.75**：准确抓住了大部分改动，仅有一处小遗漏。

**Score 0.5**：抓住了大致意思，但遗漏了重要改动或包含不准确之处。

**Score 0.25**：有重大不准确，或遗漏了大部分改动。

**Score 0.0**：未反映实际的 diff 内容。

## Additional Notes

- 本任务评估 Agent 能否阅读代码 diff 并产出一条清晰、结构良好、遵循行业约定的提交信息。
- 该 diff 有意设计为多方面的（新参数、新函数、测试），以测试 Agent 是否能将改动综合成一段连贯的叙述，而不是机械罗列。
