---
id: task_skill_search
name: 文件中的查找与替换
category: 技能
scene: 本地环境、命令执行与脚本任务
sub_scene: 配置文件查找替换
difficulty: L2
capabilities:
- 指令遵循与约束理解
- 工具调用
- 输出格式适配
- 自然语言生成
grading_type: automated
timeout_seconds: 180
workspace_files:
  - path: "config/settings.json"
    content: |
      {
        "database": {
          "host": "localhost",
          "port": 5432,
          "name": "myapp_dev",
          "user": "devuser",
          "password": "dev_password_123"
        },
        "api": {
          "endpoint": "http://localhost:3000",
          "timeout": 30
        },
        "logging": {
          "level": "debug",
          "file": "/var/log/myapp/dev.log"
        }
      }
  - path: "config/database.yml"
    content: |
      development:
        adapter: postgresql
        host: localhost
        port: 5432
        database: myapp_dev
        username: devuser
        password: dev_password_123

      test:
        adapter: postgresql
        host: localhost
        port: 5432
        database: myapp_test
        username: devuser
        password: dev_password_123
---

## Prompt

我需要为生产环境部署更新我的配置文件。请对 `config/` 目录下的所有配置文件做出以下修改：

1. 将所有的 `localhost` 改为 `prod-db.example.com`
2. 将数据库名从 `myapp_dev` 改为 `myapp_prod`（并将 `myapp_test` 改为 `myapp_prod`）
3. 将日志级别从 `debug` 改为 `warn`（在 settings.json 中）
4. 将 API 端点从 `http://localhost:3000` 更新为 `https://api.example.com`

列出你对每个文件所做的修改。

## Expected Behavior

Agent 应当：

1. 读取 `config/` 目录下的配置文件
2. 识别出所有需要修改的位置
3. 在每个文件中进行相应的替换
4. 总结所做的修改

本任务测试 Agent 的以下能力：

- 阅读并理解配置文件格式（JSON、YAML）
- 执行有针对性的查找替换操作
- 跨多个文件工作
- 清晰地传达所做的修改

## Grading Criteria

- [ ] Agent 读取了配置文件
- [ ] Agent 将 localhost 替换为 prod-db.example.com
- [ ] Agent 适当地更新了数据库名
- [ ] Agent 将日志级别改为 warn
- [ ] Agent 将 API 端点更新为 https
- [ ] Agent 总结了所做的修改

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    """
    Grade the search and replace task.

    Args:
        transcript: Parsed JSONL transcript as list of dicts
        workspace_path: Path to the task's isolated workspace directory

    Returns:
        Dict mapping criterion names to scores (0.0 to 1.0)
    """
    from pathlib import Path
    import json

    scores = {}
    workspace = Path(workspace_path)

    # Check settings.json
    settings_file = workspace / "config" / "settings.json"
    if settings_file.exists():
        content = settings_file.read_text()
        scores["settings_host_updated"] = 1.0 if "prod-db.example.com" in content and "localhost" not in content.replace("api.example.com", "") else 0.0
        scores["settings_db_updated"] = 1.0 if "myapp_prod" in content and "myapp_dev" not in content else 0.0
        scores["settings_loglevel_updated"] = 1.0 if '"warn"' in content.lower() and '"debug"' not in content.lower() else 0.0
        scores["settings_api_updated"] = 1.0 if "https://api.example.com" in content else 0.0
    else:
        scores["settings_host_updated"] = 0.0
        scores["settings_db_updated"] = 0.0
        scores["settings_loglevel_updated"] = 0.0
        scores["settings_api_updated"] = 0.0

    # Check database.yml
    db_file = workspace / "config" / "database.yml"
    if db_file.exists():
        content = db_file.read_text()
        scores["yaml_host_updated"] = 1.0 if "prod-db.example.com" in content and "localhost" not in content else 0.0
        scores["yaml_db_updated"] = 1.0 if "myapp_prod" in content and "myapp_dev" not in content and "myapp_test" not in content else 0.0
    else:
        scores["yaml_host_updated"] = 0.0
        scores["yaml_db_updated"] = 0.0

    return scores
```

## Additional Notes

- 本任务测试 DevOps/部署场景中常见的实用文件操作技能
- Agent 应当注意保持文件格式（合法的 JSON、合法的 YAML）
- 需要对多个文件进行一致的修改
- Agent 应当清晰地传达做了哪些修改
