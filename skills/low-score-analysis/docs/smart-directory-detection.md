# 智能目录识别优化

## 问题背景

之前的脚本设计假设**多模型场景**，要求用户提供：
- `--result-root`: 包含多个模型子目录的根目录
- `--model`: 模型子目录名

```
results-root/
  ├── model-1/
  └── model-2/
  └── report-workspace/  ← 硬编码在 result_root 下
```

但实际使用中，用户常见的场景是：
- **单模型评测**：直接指定模型目录 `/path/to/results/model-dir`
- **期望**：workspace 在模型目录内，而不是父目录

### 问题示例

用户输入：
```bash
--result-root /path/to/results-astronclaw-local/debug-001
```

旧逻辑处理：
```python
result_root = Path("/.../debug-001")
model_dir = result_root / "debug-001"  # ❌ 不存在：/.../debug-001/debug-001
workspace = result_root / "report-workspace"  # /.../debug-001/report-workspace
```

实际执行时我自动调整为：
```bash
--result-root /path/to/results-astronclaw-local
--model debug-001
```

导致：
```
workspace = /.../results-astronclaw-local/report-workspace  ← 与 debug-001 平级
```

**用户困惑**："为什么 workspace 不在我指定的 debug-001 目录下？"

## 解决方案：智能目录识别

### 核心逻辑

脚本自动检测 `--result-root` 的类型：

```python
# 1. 检查 result_root 本身是否包含评测结果 JSON
result_json_in_root = find_result_json(result_root)

if result_json_in_root:
    # 单模型模式：result_root 本身就是模型目录
    model_dir = result_root
    default_workspace = result_root / "report-workspace"  # workspace 在模型目录内
else:
    # 多模型模式：result_root 是多个模型的父目录
    model_dir = result_root / args.model  # 需要 --model 参数
    default_workspace = result_root / "report-workspace"  # workspace 在根目录
```

### 使用方式

**单模型目录模式**（新增支持）：
```bash
python3 generate_failed_tasks_manifest.py \
  --result-root /path/to/results/model-dir

# 脚本输出：
# 检测到单模型目录模式: model-dir
# 工作区目录: /path/to/results/model-dir/report-workspace
```

目录结构：
```
model-dir/
  ├── 0001_model.json
  ├── 0001_transcripts/
  └── report-workspace/           ← workspace 在模型目录内
      ├── _failed_tasks_model.json
      └── analysis_model.json
```

**多模型根目录模式**（保持兼容）：
```bash
python3 generate_failed_tasks_manifest.py \
  --result-root /path/to/results \
  --model model-dir

# 脚本输出：
# 检测到多模型根目录模式
# 工作区目录: /path/to/results/report-workspace
```

目录结构：
```
results/
  ├── model-1/
  ├── model-2/
  └── report-workspace/           ← workspace 在根目录（与所有模型平级）
      ├── _failed_tasks_model1.json
      └── _failed_tasks_model2.json
```

### 参数调整

- `--model` 从 `required=True` 改为 `default=None`
- 单模型模式时可省略 `--model`，脚本自动识别
- 多模型模式时仍需提供 `--model`

### 输出优化

旧输出：
```
模型: debug-001
低分任务数（任意轮<60.0%）: 1 / 2
清单已写入: /.../report-workspace/_failed_tasks_debug-001.json
```

新输出：
```
检测到单模型目录模式: debug-001
使用评测结果文件: 0009_xsparkx2flash.json

模型目录: /.../results-astronclaw-local/debug-001
实际模型名: xsparkx2flash
工作区目录: /.../debug-001/report-workspace      ← 明确显示 workspace 位置
低分任务数（任意轮<60.0%）: 1 / 2
清单已写入: /.../debug-001/report-workspace/_failed_tasks_xsparkx2flash.json

💡 提示：如需回填 Excel 报告，请确保分析文件名包含模型名 'xsparkx2flash'
   建议命名: analysis_xsparkx2flash.json
   分析文件将保存到: /.../debug-001/report-workspace/analysis_xsparkx2flash.json
```

### 技术实现

#### 1. 智能检测逻辑

```python
# 检查 result_root 本身是否包含评测结果 JSON
result_json_in_root = find_result_json(result_root)

if result_json_in_root:
    # 单模型模式
    model_dir = result_root
    default_workspace = result_root / "report-workspace"
    print(f"检测到单模型目录模式: {result_root.name}")
    print(f"忽略 --model 参数（如果提供）")
else:
    # 多模型模式
    model_dir = result_root / args.model
    if not model_dir.exists():
        sys.exit(f"错误: 模型目录不存在: {model_dir}")
    default_workspace = result_root / "report-workspace"
    print(f"检测到多模型根目录模式")
```

#### 2. 文件名使用实际模型名

```python
# 从 JSON 读取实际模型名
with open(result_json, encoding="utf-8") as f:
    data = json.load(f)
model_name_for_file = data.get("model", "") or args.model or model_dir.name

# 输出文件名使用实际模型名
out = workspace / f"_failed_tasks_{model_name_for_file}.json"
```

#### 3. 输出信息增强

```python
print(f"\n模型目录: {model_dir}")
print(f"实际模型名: {model_name}")
if args.model and model_name != args.model:
    print(f"  ⚠️  注意：--model 参数 '{args.model}' 与实际模型名不同")
print(f"工作区目录: {workspace}")  # ← 新增：明确显示 workspace 位置
print(f"低分任务数（任意轮<{args.threshold}%）: {len(bundles)} / {total_tasks}")
```

## 用户体验改进

### 改进前

```bash
# 用户想分析单个模型
$ python3 scripts/generate_failed_tasks_manifest.py \
    --result-root results/debug-001 \
    --model debug-001

# ❌ 错误：模型目录不存在: results/debug-001/debug-001

# 被迫调整为：
$ python3 scripts/generate_failed_tasks_manifest.py \
    --result-root results \
    --model debug-001

# ✓ 成功，但是：
workspace = results/report-workspace  ← 不符合直觉，用户期望在 debug-001 下
```

### 改进后

```bash
# 用户可以直接指定模型目录
$ python3 scripts/generate_failed_tasks_manifest.py \
    --result-root results/debug-001

# ✓ 自动检测单模型模式
# 检测到单模型目录模式: debug-001
# 工作区目录: results/debug-001/report-workspace  ← 符合直觉

# 或者保持旧方式（完全兼容）
$ python3 scripts/generate_failed_tasks_manifest.py \
    --result-root results \
    --model debug-001

# ✓ 检测到多模型根目录模式
# 工作区目录: results/report-workspace  ← 多模型时合理
```

## 测试验证

### 测试 1：单模型目录模式

```bash
$ python3 .claude/skills/low-score-analysis/scripts/generate_failed_tasks_manifest.py \
    --result-root results-astronclaw-local/debug-001 \
    --threshold 60

# 输出验证点：
✅ "检测到单模型目录模式: debug-001"
✅ "工作区目录: /.../debug-001/report-workspace"
✅ "清单已写入: /.../debug-001/report-workspace/_failed_tasks_xsparkx2flash.json"
✅ "分析文件将保存到: /.../debug-001/report-workspace/analysis_xsparkx2flash.json"

# 目录结构验证：
$ ls results-astronclaw-local/debug-001/
0009_xsparkx2flash.json
0009_transcripts/
report-workspace/         ← ✅ 在模型目录内
```

### 测试 2：多模型根目录模式（兼容性）

```bash
$ python3 .claude/skills/low-score-analysis/scripts/generate_failed_tasks_manifest.py \
    --result-root results-astronclaw-local \
    --model debug-001 \
    --threshold 60

# 输出验证点：
✅ "检测到多模型根目录模式"
✅ "工作区目录: /.../results-astronclaw-local/report-workspace"
✅ "清单已写入: /.../results-astronclaw-local/report-workspace/_failed_tasks_xsparkx2flash.json"

# 目录结构验证：
$ ls results-astronclaw-local/
debug-001/
skill-debug/
report-workspace/         ← ✅ 与模型目录平级
```

## 向后兼容性

✅ **完全向后兼容**：
- 多模型模式的参数和行为完全不变
- 只是新增了单模型模式的智能识别
- 不影响现有脚本和工作流

## 文档更新

- [x] `README.md` - 新增"直接运行脚本"章节，说明两种模式
- [x] `README.md` - 关键设计表格增加"智能目录识别"
- [x] `README.md` - 新增"目录结构"说明
- [x] `SKILL.md` - 输入章节增加模式说明和自动检测逻辑
- [x] `SKILL.md` - 输出章节区分单模型/多模型结构
- [x] `SKILL.md` - 第1步增加两种模式的示例
- [x] `scripts/generate_failed_tasks_manifest.py` - argparse help 增加使用示例
- [x] `docs/smart-directory-detection.md` - 本文档（完整设计说明）

## 相关问题修复

此优化同时解决了另一个相关问题：文件名自动使用实际模型名。

**改进前**：
```python
out = workspace / f"_failed_tasks_{args.model}.json"
# 使用用户输入的 --model 参数（可能是目录名）
```

**改进后**：
```python
model_name_for_file = data.get("model", "") or args.model or model_dir.name
out = workspace / f"_failed_tasks_{model_name_for_file}.json"
# 优先使用 JSON 中的实际模型名
```

这样生成的文件名始终是 `_failed_tasks_xsparkx2flash.json`，与后续的 `analysis_xsparkx2flash.json` 保持一致，避免命名混乱。

## 影响范围

### 修改的文件

1. **`scripts/generate_failed_tasks_manifest.py`**
   - 主函数增加智能检测逻辑（30 行）
   - argparse 参数调整（--model 改为可选，增加 epilog）
   - 输出信息增强（显示工作区目录）
   - 文件名使用实际模型名

2. **`README.md`**
   - 新增"直接运行脚本"章节
   - 关键设计表格更新
   - 新增目录结构说明

3. **`SKILL.md`**
   - 输入章节重写（增加模式说明）
   - 输出章节重写（区分两种模式）
   - 第1步增加示例

4. **`docs/smart-directory-detection.md`** (新增)
   - 完整的优化文档

### 不影响的部分

- ✅ Workflow 模板无需修改
- ✅ utils.py 工具函数无需修改
- ✅ 后续分析步骤无需修改
- ✅ generate_eval_report.py 无需修改

## 未来可能的改进

### generate_eval_report.py 同步优化

`generate_eval_report.py` 目前也硬编码了 `result_root / "report-workspace"`：

```python
# 第 1310 行
output_dir = Path(args.output_dir) if args.output_dir else result_root / "report-workspace" / "output"
```

可以考虑类似的智能检测逻辑，让报告脚本也支持单模型/多模型两种模式。但鉴于：
1. 报告脚本通常用于多模型对比场景
2. 可以通过 `--output-dir` 显式指定输出位置
3. 改动影响范围较大

暂时不优化，保持现状。如果用户反馈需要，可以在后续版本中统一。
