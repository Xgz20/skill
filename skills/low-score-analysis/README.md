# 低分任务根因分析 Skill

为 PinchBench 评测产出**低分任务的根因分析**：对某个模型筛出得分低于阈值的任务，逐个用 LLM 结合评测判词和执行全过程找出失分的事实依据与根本原因，结果写入 JSON，可供评测报告脚本回填到 Excel。

## 目录结构

```
low-score-analysis/
├── SKILL.md                                    ← 完整使用说明（权威）
├── README.md                                   ← 本文件（项目入口）
├── docs/
│   └── data-simplification-explained.md        ← 数据精简原理说明
├── references/
│   └── workflow_template.js                    ← Workflow 脚本模板
└── scripts/
    ├── generate_failed_tasks_manifest.py       ← 生成低分任务清单
    ├── utils.py                                ← 数据精简、分批、断点续传等工具
    ├── test_utils.py                           ← utils.py 单元测试
    └── test_data_safety.py                     ← 数据精简安全性验证
```

## 快速开始

### 1. 在 Claude Code 中触发

```
/low-score-analysis
```

或自然语言：

```
分析 xsparkx2flash-530 模型的低分任务根因
```

Claude 会按 SKILL.md 中的流程自动执行：

1. 生成低分任务清单
2. 数据精简（减少 40-50% 体积，无信息损失）
3. 分批调用 Workflow（每批 ≤10 任务，避免参数传输瓶颈）
4. 增量保存 + 断点续传
5. 合并最终结果

### 2. 验证环境（可选）

```bash
python3 skills/low-score-analysis/scripts/test_utils.py
python3 skills/low-score-analysis/scripts/test_data_safety.py
```

## 关键设计

| 设计 | 解决的问题 |
|------|-----------|
| **必须数据精简** | 原始数据冗余字段过多（min/max_score_pct 等），传输易超限 |
| **强制外部分批** | Workflow `args` 参数有传输大小限制，单批 ≤10 任务最稳定 |
| **断点续传** | 失败重试不重复分析已完成任务 |
| **增量保存** | 每批次结果立即落盘，避免数据丢失 |
| **容错机制** | 单任务失败不影响其他任务（`filter(Boolean)`） |

## 安装（软链接到 .claude/skills）

源码在 `skill/skills/low-score-analysis/`，使用前软链到项目的 `.claude/skills/`：

```bash
mkdir -p .claude/skills
ln -snf ../../skill/skills/low-score-analysis .claude/skills/low-score-analysis
```

## 详细使用说明

完整流程、参数说明、故障排查请直接看 [SKILL.md](./SKILL.md)。
