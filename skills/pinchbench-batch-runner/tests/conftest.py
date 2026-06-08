"""pytest fixture: 把 scripts/ 加入 sys.path，让测试可以直接 import 模块。"""
import sys
from pathlib import Path

# 把 ../scripts/ 和 ../../shared/ 加入 sys.path
TESTS_DIR = Path(__file__).parent
sys.path.insert(0, str(TESTS_DIR.parent / "scripts"))
sys.path.insert(0, str(TESTS_DIR.parent.parent / "shared"))
