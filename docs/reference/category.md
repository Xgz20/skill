## 评测集分类（Category）

全量评测集中的任务按 `category` 字段归类，权威分类定义见 `tasks/manifest.yaml`，共 11 类。以下为中英文对照表（按 manifest 中的顺序排列），并附各分类的任务数量与说明。

| 英文 | 中文 |
| --- | --- |
| productivity | 生产力 |
| research | 调研 |
| writing | 写作 |
| coding | 编程 |
| analysis | 综合分析 |
| csv_analysis | CSV 数据分析 |
| log_analysis | 日志分析 |
| meeting_analysis | 会议分析 |
| memory | 记忆 |
| skills | 技能 |
| integrations | 集成 |

### 分类说明与任务数量

| 英文 | 中文 | 任务数 | 说明 |
| --- | --- | --- | --- |
| productivity | 生产力 | 8 | 日常办公与效率类任务，如待办整理、信息归纳 |
| research | 调研 | 12 | 专题调研与资料检索，如股票、行业研究 |
| writing | 写作 | 6 | 内容创作，如博客、文案撰写 |
| coding | 编程 | 14 | 代码编写、脚本与本地命令执行类任务 |
| analysis | 综合分析 | 12 | 通用数据/文本分析与摘要 |
| csv_analysis | CSV 数据分析 | 26 | 针对 CSV 表格的检索、聚合与交叉分析 |
| log_analysis | 日志分析 | 30 | 服务器/应用日志的解析、分组与异常排查 |
| meeting_analysis | 会议分析 | 28 | 会议纪要解析，如投票统计、行动项与建议提取 |
| memory | 记忆 | 2 | 跨会话记忆的存取与应用 |
| skills | 技能 | 6 | Skill 的发现、创建、安装与调用 |
| integrations | 集成 | 3 | 第三方服务集成，如邮件、Google Workspace |

> 注：任务数量统计自各任务文件 frontmatter 中的 `category` 字段（不含 `tasks/TASK_TEMPLATE.md` 模板）。
