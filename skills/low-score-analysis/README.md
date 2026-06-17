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

### 2. 直接运行脚本

**单模型目录模式**（推荐，workspace 在模型目录内）：
```bash
python3 scripts/generate_failed_tasks_manifest.py \
  --result-root /path/to/results/model-dir
```

**多模型根目录模式**（workspace 在根目录，与所有模型目录平级）：
```bash
python3 scripts/generate_failed_tasks_manifest.py \
  --result-root /path/to/results \
  --model model-dir-name
```

脚本会自动检测：
- 如果 `--result-root` 本身包含评测结果 JSON → 单模型模式
- 如果 `--result-root` 是多个模型的父目录 → 多模型模式

### 3. 验证环境（可选）

```bash
python3 skills/low-score-analysis/scripts/test_utils.py
python3 skills/low-score-analysis/scripts/test_data_safety.py
```

## 关键设计

| 设计 | 解决的问题 |
|------|-----------|
| **智能目录识别** | 自动判断单模型/多模型模式，workspace 位置符合直觉 |
| **必须数据精简** | 原始数据冗余字段过多（min/max_score_pct 等），传输易超限 |
| **强制外部分批** | Workflow `args` 参数有传输大小限制，单批 ≤10 任务最稳定 |
| **断点续传** | 失败重试不重复分析已完成任务 |
| **增量保存** | 每批次结果立即落盘，避免数据丢失 |
| **容错机制** | 单任务失败不影响其他任务（`filter(Boolean)`） |

### 目录结构

**单模型模式**（直接指定模型目录）：
```
model-dir/
  ├── 0001_model.json
  ├── 0001_transcripts/
  └── report-workspace/           ← workspace 在模型目录内
      ├── _failed_tasks_model.json
      ├── analysis_model.json
      └── output/
          └── report_xxx.xlsx
```

**多模型模式**（指定根目录 + 模型名）：
```
results-root/
  ├── model-1/
  │   ├── 0001_model1.json
  │   └── 0001_transcripts/
  ├── model-2/
  │   ├── 0002_model2.json
  │   └── 0002_transcripts/
  └── report-workspace/           ← workspace 与所有模型平级
      ├── _failed_tasks_model1.json
      ├── _failed_tasks_model2.json
      ├── analysis_model1.json
      ├── analysis_model2.json
      └── output/
          └── report_xxx.xlsx
```

## ⚠️ 重要注意事项

### 分析文件命名规范

生成的分析文件名**必须包含模型名**（而非目录名），才能被 `generate_eval_report.py` 正确识别回填到 Excel。

**常见问题**：
- 使用 `--model debug-001` 时，脚本生成 `analysis_debug-001.json`（目录名）
- 但模型名可能是 `xsparkx2flash`（从 `0009_xsparkx2flash.json` 推断）
- 导致报告脚本无法匹配，回填失败

**判断标准**：
```bash
# 查看模型名（从评测结果 JSON 中）
python3 -c "import json; print(json.load(open('path/to/0009_xxx.json'))['model'])"
# 输出：xsparkx2flash  ← 这是真正的模型名
```

**解决方法**：

1. **重命名分析文件**（最简单）：
   ```bash
   cd report-workspace
   mv analysis_<目录名>.json analysis_<模型名>.json
   mv analysis_<目录名>_batch_*.json analysis_<模型名>_batch_*.json
   ```
   
   示例：
   ```bash
   mv analysis_debug-001.json analysis_xsparkx2flash.json
   ```

2. **使用显式模型绑定**（一次性处理）：
   ```bash
   python3 scripts/generate_eval_report.py \
     -d <result-dir> \
     --analysis MODEL=<模型名>:path/to/analysis_<目录名>.json
   ```
   
   示例：
   ```bash
   --analysis MODEL=xsparkx2flash:report-workspace/analysis_debug-001.json
   ```

3. **直接使用模型名运行**（推荐，从源头避免）：
   ```bash
   # 不要用目录名
   ❌ python3 scripts/generate_failed_tasks_manifest.py --model debug-001
   
   # 而是用模型名（从 JSON 文件中读取）
   ✅ python3 scripts/generate_failed_tasks_manifest.py --model xsparkx2flash
   ```

**验证回填成功**：
```bash
# 查看脚本输出，应该有这行：
# "已加载分析回填合计 N 条（来自 1 个文件）"  ← N > 0 表示成功

# 如果看到警告：
# "警告：分析文件为 task_id 字典格式，但无法从文件名 xxx 匹配到已加载模型"
# 说明文件名不匹配，需要重命名
```

## 安装（软链接到 .claude/skills）

源码在 `skill/skills/low-score-analysis/`，使用前软链到项目的 `.claude/skills/`：

```bash
mkdir -p .claude/skills
ln -snf ../../skill/skills/low-score-analysis .claude/skills/low-score-analysis
```

## 详细使用说明

完整流程、参数说明、故障排查请直接看 [SKILL.md](./SKILL.md)。
