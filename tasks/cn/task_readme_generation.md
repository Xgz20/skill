---
id: task_readme_generation
name: README 生成
category: 写作
scene: 内容创作、PPT、网页与多媒体生成
sub_scene: README 文档生成
difficulty: L2
capabilities:
- 数据提取与处理
- 自然语言生成
- 指令遵循与约束理解
- 输出格式适配
- 幻觉抑制
grading_type: llm_judge
timeout_seconds: 180
workspace_files:
  - path: "src/index.ts"
    content: |
      import express from 'express';
      import { config } from './config';
      import { authRouter } from './routes/auth';
      import { tasksRouter } from './routes/tasks';
      import { webhookRouter } from './routes/webhooks';
      import { connectDb } from './db';
      import { logger } from './utils/logger';

      const app = express();

      app.use(express.json());
      app.use('/api/auth', authRouter);
      app.use('/api/tasks', tasksRouter);
      app.use('/api/webhooks', webhookRouter);

      app.get('/health', (_req, res) => res.json({ status: 'ok' }));

      async function main() {
        await connectDb();
        app.listen(config.port, () => {
          logger.info(`TaskFlow API listening on port ${config.port}`);
        });
      }

      main().catch((err) => {
        logger.error('Failed to start server', err);
        process.exit(1);
      });
  - path: "src/config.ts"
    content: |
      import dotenv from 'dotenv';
      dotenv.config();

      export const config = {
        port: parseInt(process.env.PORT || '3000', 10),
        databaseUrl: process.env.DATABASE_URL || 'postgresql://localhost:5432/taskflow',
        jwtSecret: process.env.JWT_SECRET || 'change-me',
        redisUrl: process.env.REDIS_URL || 'redis://localhost:6379',
        webhookSecret: process.env.WEBHOOK_SECRET || '',
      };
  - path: "src/routes/auth.ts"
    content: |
      import { Router } from 'express';
      import bcrypt from 'bcrypt';
      import jwt from 'jsonwebtoken';
      import { db } from '../db';
      import { config } from '../config';

      export const authRouter = Router();

      authRouter.post('/register', async (req, res) => {
        const { email, password, name } = req.body;
        const hash = await bcrypt.hash(password, 12);
        const user = await db.user.create({ data: { email, password: hash, name } });
        res.status(201).json({ id: user.id, email: user.email });
      });

      authRouter.post('/login', async (req, res) => {
        const { email, password } = req.body;
        const user = await db.user.findUnique({ where: { email } });
        if (!user || !(await bcrypt.compare(password, user.password))) {
          return res.status(401).json({ error: 'Invalid credentials' });
        }
        const token = jwt.sign({ sub: user.id }, config.jwtSecret, { expiresIn: '7d' });
        res.json({ token });
      });
  - path: "src/routes/tasks.ts"
    content: |
      import { Router } from 'express';
      import { db } from '../db';
      import { authenticate } from '../middleware/auth';

      export const tasksRouter = Router();
      tasksRouter.use(authenticate);

      tasksRouter.get('/', async (req, res) => {
        const tasks = await db.task.findMany({ where: { userId: req.userId } });
        res.json(tasks);
      });

      tasksRouter.post('/', async (req, res) => {
        const { title, description, dueDate } = req.body;
        const task = await db.task.create({
          data: { title, description, dueDate: new Date(dueDate), userId: req.userId },
        });
        res.status(201).json(task);
      });

      tasksRouter.patch('/:id', async (req, res) => {
        const task = await db.task.update({
          where: { id: req.params.id, userId: req.userId },
          data: req.body,
        });
        res.json(task);
      });

      tasksRouter.delete('/:id', async (req, res) => {
        await db.task.delete({ where: { id: req.params.id, userId: req.userId } });
        res.status(204).send();
      });
  - path: "src/routes/webhooks.ts"
    content: |
      import { Router } from 'express';
      import crypto from 'crypto';
      import { config } from '../config';
      import { db } from '../db';

      export const webhookRouter = Router();

      webhookRouter.post('/task-complete', async (req, res) => {
        const signature = req.headers['x-webhook-signature'] as string;
        const payload = JSON.stringify(req.body);
        const expected = crypto.createHmac('sha256', config.webhookSecret).update(payload).digest('hex');
        if (signature !== expected) {
          return res.status(403).json({ error: 'Invalid signature' });
        }
        const { taskId, completedAt } = req.body;
        await db.task.update({ where: { id: taskId }, data: { completedAt: new Date(completedAt), status: 'done' } });
        res.json({ ok: true });
      });
  - path: "package.json"
    content: |
      {
        "name": "taskflow-api",
        "version": "1.2.0",
        "description": "Task management REST API",
        "main": "dist/index.js",
        "scripts": {
          "dev": "ts-node-dev --respawn src/index.ts",
          "build": "tsc",
          "start": "node dist/index.js",
          "test": "jest",
          "lint": "eslint src/",
          "db:migrate": "prisma migrate dev",
          "db:seed": "ts-node prisma/seed.ts"
        },
        "dependencies": {
          "express": "^4.18.2",
          "bcrypt": "^5.1.1",
          "jsonwebtoken": "^9.0.2",
          "ioredis": "^5.3.2",
          "dotenv": "^16.3.1",
          "@prisma/client": "^5.7.0"
        },
        "devDependencies": {
          "typescript": "^5.3.3",
          "ts-node-dev": "^2.0.0",
          "jest": "^29.7.0",
          "@types/express": "^4.17.21",
          "eslint": "^8.56.0",
          "prisma": "^5.7.0"
        },
        "license": "MIT"
      }
  - path: "prisma/schema.prisma"
    content: |
      generator client {
        provider = "prisma-client-js"
      }

      datasource db {
        provider = "postgresql"
        url      = env("DATABASE_URL")
      }

      model User {
        id        String   @id @default(uuid())
        email     String   @unique
        password  String
        name      String
        tasks     Task[]
        createdAt DateTime @default(now())
      }

      model Task {
        id          String    @id @default(uuid())
        title       String
        description String?
        status      String    @default("pending")
        dueDate     DateTime?
        completedAt DateTime?
        user        User      @relation(fields: [userId], references: [id])
        userId      String
        createdAt   DateTime  @default(now())
        updatedAt   DateTime  @updatedAt
      }
  - path: ".env.example"
    content: |
      PORT=3000
      DATABASE_URL=postgresql://user:password@localhost:5432/taskflow
      JWT_SECRET=your-secret-key
      REDIS_URL=redis://localhost:6379
      WEBHOOK_SECRET=your-webhook-secret
---

# README Generation

## Prompt

检查本工作区中的源代码——这是一个小型的 TypeScript REST API 项目。为该项目生成一份完整的 `README.md`。

README 应包含：

1. **项目标题与描述** — 项目的作用。
2. **技术栈** — 使用的语言、框架和关键库。
3. **快速开始** — 先决条件、安装步骤以及如何在本地运行项目（包括数据库设置）。
4. **环境变量** — 解释 `.env.example` 中每个变量的表格或列表。
5. **API 端点** — 用 HTTP 方法和简要描述记录可用路由。
6. **可用脚本** — 解释每个 npm 脚本的作用。
7. **许可证** — 基于 `package.json` 中的内容。

将输出保存为工作区根目录的 `README.md`。

## Expected Behavior

Agent 应当阅读源文件以理解项目结构，然后生成一份组织良好的 README，准确反映代码库。

Agent 应发现并包含的关键细节：

- 项目名为 "TaskFlow API"（来自 package.json 的 name/description 和 logger 输出）。
- 技术栈：TypeScript、Express、Prisma（PostgreSQL）、Redis、JWT 认证、bcrypt。
- 路由：`/api/auth`（注册、登录）、`/api/tasks`（CRUD）、`/api/webhooks`（task-complete）、`/health`。
- 环境变量：PORT、DATABASE_URL、JWT_SECRET、REDIS_URL、WEBHOOK_SECRET。
- 脚本：dev、build、start、test、lint、db:migrate、db:seed。
- 许可证：MIT。

README 应结构良好，标题清晰，命令使用代码块，信息准确且来自实际源代码（而非臆造功能）。

## Grading Criteria

- [ ] 创建了文件 `README.md`
- [ ] 包含项目名和准确描述
- [ ] 列出了正确的技术栈
- [ ] 提供快速开始/安装说明
- [ ] 记录了 `.env.example` 中的环境变量
- [ ] 用 HTTP 方法记录了 API 端点
- [ ] 解释了可用的 npm 脚本
- [ ] 提及许可证
- [ ] 内容准确且源自实际源代码

## LLM Judge Rubric

### Criterion 1: Accuracy and Faithfulness (Weight: 30%)

**Score 1.0**：README 中的所有信息都来自实际源代码。技术栈、端点、环境变量和脚本都正确，没有臆造的功能或库。

**Score 0.75**：大体准确，但有一处小的不准确或假定的细节不在源代码中。

**Score 0.5**：总体正确但包含明显的不准确或编造的细节。

**Score 0.25**：多处重大不准确或臆造功能。

**Score 0.0**：大部分内容是编造的，不反映实际代码库。

### Criterion 2: Completeness (Weight: 25%)

**Score 1.0**：覆盖所有必需板块：标题/描述、技术栈、快速开始、环境变量、API 端点、脚本和许可证。没有重大板块缺失。

**Score 0.75**：覆盖大多数板块，有一处小的遗漏。

**Score 0.5**：缺少两个或更多板块，或多个板块表述浅显。

**Score 0.25**：覆盖最少；大多数必需板块缺失。

**Score 0.0**：没有有意义的 README 内容。

### Criterion 3: API Documentation Quality (Weight: 20%)

**Score 1.0**：所有路由都用 HTTP 方法、路径和简要描述记录。认证路由（注册、登录）、任务 CRUD 路由、webhook 端点和健康检查都涵盖。

**Score 0.75**：大多数路由有记录，有小的缺口（例如缺少健康检查或一个 CRUD 操作）。

**Score 0.5**：路由记录部分；多个端点缺失或方法不正确。

**Score 0.25**：API 文档最少。

**Score 0.0**：没有 API 文档。

### Criterion 4: Structure and Readability (Weight: 15%)

**Score 1.0**：组织良好，标题清晰，格式一致，恰当使用命令和环境变量的代码块，对新开发者来说易于跟随。

**Score 0.75**：结构良好，有小的格式不一致。

**Score 0.5**：可读但组织混乱或格式不一致。

**Score 0.25**：难以跟随或结构混乱。

**Score 0.0**：不可读或无结构。

### Criterion 5: Getting Started Quality (Weight: 10%)

**Score 1.0**：清晰的逐步设置说明，包括先决条件（Node.js、PostgreSQL、Redis）、安装依赖、设置环境变量、运行迁移和启动服务器。

**Score 0.75**：良好的设置说明，有一处小的缺口。

**Score 0.5**：基本说明但缺少关键步骤（例如数据库迁移或 Redis）。

**Score 0.25**：设置说明最少或不清晰。

**Score 0.0**：没有设置说明。

## Additional Notes

- 本任务评估 Agent 能否分析代码库并产出准确、结构良好的文档。
- 工作区包含足够的文件来完整记录项目而无需猜测——优秀答案会引用实际的代码模式（例如用 Prisma 做 ORM、用 bcrypt 做密码哈希），而非做出通用假设。
- Agent 不应编造代码中不存在的端点、功能或依赖。
