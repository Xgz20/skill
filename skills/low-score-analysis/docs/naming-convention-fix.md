# 分析文件命名规范修复

## 问题背景

在使用低分任务根因分析 Skill 时，如果评测结果的目录名与实际模型名不一致，会导致生成的分析文件无法被 `generate_eval_report.py` 正确识别，回填失败。

### 问题示例

```
评测结果目录: results-astronclaw-local/debug-001/
评测结果文件: 0009_xsparkx2flash.json
实际模型名:   xsparkx2flash (从 JSON 中读取)
目录名:       debug-001

使用 --model debug-001 运行 Skill 后:
生成的分析文件: analysis_debug-001.json  ← 包含目录名

回填 Excel 时:
已加载模型: xsparkx2flash
匹配文件名: analysis_debug-001.json 中查找 "xsparkx2flash"
结果: 无法匹配 → 回填失败 (0 条)
```

## 解决方案

### 1. README.md 增加注意事项

在 `README.md` 的"关键设计"部分后增加"⚠️ 重要注意事项"章节，详细说明：

- **问题根源**：目录名 vs 模型名不一致
- **判断方法**：如何查看实际模型名
- **解决方法**：
  1. 重命名文件（最简单）
  2. 使用显式模型绑定（MODEL=前缀）
  3. 直接使用模型名运行（推荐）
- **验证方法**：检查回填输出

### 2. 脚本输出增强

`generate_failed_tasks_manifest.py` 在末尾输出时增加：

1. **区分模型目录名和实际模型名**：
   ```
   模型目录: debug-001
   实际模型名: xsparkx2flash ⚠️  (与目录名不同)
   ```

2. **命名建议提示**：
   ```
   💡 提示：如需回填 Excel 报告，请确保分析文件名包含模型名 'xsparkx2flash'
      建议命名: analysis_xsparkx2flash.json
   ```

3. **冲突警告**（当目录名 ≠ 模型名时）：
   ```
   ⚠️  注意：当前使用目录名 'debug-001'，但实际模型名是 'xsparkx2flash'
   如果生成 analysis_debug-001.json，回填时将无法识别
   建议: 分析完成后重命名为 analysis_xsparkx2flash.json
   ```

### 3. SKILL.md 文档更新

- **第 1 步后**增加提示：脚本会显示实际模型名，注意命名差异
- **第 5 步**全面重写，增加：
  - ⚠️ 关键要求说明
  - 命名规范（正确/错误示例）
  - 如何查看实际模型名
  - 修复方法（重命名/显式绑定）
  - 回填示例（单模型/多模型）
  - 验证方法

## 技术实现

### 脚本改动（generate_failed_tasks_manifest.py）

```python
# 读取实际模型名
with open(result_json, encoding="utf-8") as f:
    data = json.load(f)
model_name = data.get("model", "")

# 输出区分
print(f"\n模型目录: {args.model}")
if model_name and model_name != args.model:
    print(f"实际模型名: {model_name} ⚠️  (与目录名不同)")

# 命名建议
if model_name:
    print(f"\n💡 提示：如需回填 Excel 报告，请确保分析文件名包含模型名 '{model_name}'")
    print(f"   建议命名: analysis_{model_name}.json")
    if model_name != args.model:
        print(f"   ⚠️  注意：当前使用目录名 '{args.model}'，但实际模型名是 '{model_name}'")
        print(f"   如果生成 analysis_{args.model}.json，回填时将无法识别")
        print(f"   建议: 分析完成后重命名为 analysis_{model_name}.json")
```

### 回填匹配逻辑（generate_eval_report.py）

```python
def _infer_model_from_filename(path: Path, model_ids: list[str]) -> str | None:
    """从分析文件名推断模型 id。
    
    在文件名（去扩展名）中查找作为子串出现的、最长的已加载模型 id。
    """
    stem = path.stem  # 如 analysis_xsparkx2flash
    matched = [m for m in model_ids if m and m in stem]
    if not matched:
        return None
    return max(matched, key=len)
```

**匹配逻辑**：
- 文件名必须**包含模型名作为子串**
- 例如：`analysis_xsparkx2flash.json` → 提取 `xsparkx2flash`
- 如果文件名是 `analysis_debug-001.json`，无法匹配模型名 `xsparkx2flash`

## 用户体验改进

### 改进前

```
模型: debug-001
低分任务数（任意轮<60.0%）: 1 / 2
清单已写入: .../report-workspace/_failed_tasks_debug-001.json

(用户不知道要用 xsparkx2flash 命名)

↓ 生成 analysis_debug-001.json

↓ 回填时

警告：分析文件为 task_id 字典格式，但无法从文件名 analysis_debug-001.json 
匹配到已加载模型 ['xsparkx2flash']，将忽略回填
已加载分析回填合计 0 条

(用户困惑：为什么回填失败？)
```

### 改进后

```
使用评测结果文件: 0009_xsparkx2flash.json

模型目录: debug-001
实际模型名: xsparkx2flash ⚠️  (与目录名不同)
低分任务数（任意轮<60.0%）: 1 / 2
清单已写入: .../report-workspace/_failed_tasks_debug-001.json

💡 提示：如需回填 Excel 报告，请确保分析文件名包含模型名 'xsparkx2flash'
   建议命名: analysis_xsparkx2flash.json
   ⚠️  注意：当前使用目录名 'debug-001'，但实际模型名是 'xsparkx2flash'
   如果生成 analysis_debug-001.json，回填时将无法识别
   建议: 分析完成后重命名为 analysis_xsparkx2flash.json

(用户清楚知道要重命名文件)

↓ mv analysis_debug-001.json analysis_xsparkx2flash.json

↓ 回填时

分析文件 analysis_xsparkx2flash.json 按 task_id 字典格式解析，回填到模型: xsparkx2flash
已加载分析回填合计 1 条（来自 1 个文件）  ✅ 成功
```

## 测试验证

```bash
# 测试脚本输出
python3 .claude/skills/low-score-analysis/scripts/generate_failed_tasks_manifest.py \
  --result-root results-astronclaw-local \
  --model debug-001 \
  --threshold 60

# 验证输出包含：
# ✅ "实际模型名: xsparkx2flash ⚠️  (与目录名不同)"
# ✅ "💡 提示：如需回填 Excel 报告，请确保分析文件名包含模型名 'xsparkx2flash'"
# ✅ "建议命名: analysis_xsparkx2flash.json"
```

## 影响范围

- ✅ 向后兼容：不影响现有功能
- ✅ 用户友好：主动提示潜在问题
- ✅ 文档完善：清晰的使用说明和故障排查
- ✅ 最佳实践：引导用户使用正确的命名规范

## 相关文件

- `skills/low-score-analysis/README.md` - 用户入口文档
- `skills/low-score-analysis/SKILL.md` - 完整使用说明
- `skills/low-score-analysis/scripts/generate_failed_tasks_manifest.py` - 清单生成脚本
- `scripts/generate_eval_report.py` - Excel 报告生成（含回填逻辑）
