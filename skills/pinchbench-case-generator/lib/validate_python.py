#!/usr/bin/env python3
"""确定性 Python 语法验证器（供 case-generation workflow 的验证子 Agent 调用）。

设计目标：真实编译验证（py_compile）+ 绝不污染项目根目录。

- 代码从 stdin 读取（子 Agent 用 heredoc 管道传入，不在项目根创建文件）
- 临时文件写入系统临时目录（tempfile.TemporaryDirectory，通常在 /tmp）
- with 块退出时自动删除整个临时目录（含编译产生的 __pycache__/.pyc），
  无论验证成功、失败还是异常都保证清理
- 结果以 JSON 输出到 stdout：{"valid": bool, "error": str}

用法：
    echo "<code>" | python validate_python.py
    python validate_python.py < some_code.py
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def validate(code: str, timeout: float = 10.0) -> dict:
    """用 py_compile 在隔离的临时目录中验证 Python 代码语法。

    Args:
        code: 待验证的 Python 源码
        timeout: 编译子进程超时（秒）

    Returns:
        {"valid": bool, "error": str}
        error 为编译器 stderr（valid=True 时为空串）
    """
    if not code.strip():
        return {"valid": False, "error": "empty code"}

    # 临时目录位于系统临时区（不在项目根），with 退出时连同 .pyc 一并删除
    with tempfile.TemporaryDirectory(prefix="pinchbench_pyvalidate_") as td:
        target = Path(td) / "grade_check.py"
        target.write_text(code, encoding="utf-8")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(target)],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return {"valid": False, "error": f"py_compile timed out after {timeout}s"}

        if result.returncode == 0:
            return {"valid": True, "error": ""}

        # py_compile 的语法错误写到 stderr；清洗临时路径避免泄露到结果里
        err = (result.stderr or result.stdout or "compile failed").strip()
        err = err.replace(str(target), "grade_check.py").replace(td, "<tmp>")
        return {"valid": False, "error": err}


def main() -> int:
    code = sys.stdin.read()
    print(json.dumps(validate(code), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
