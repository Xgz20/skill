"""端到端集成测试：真实数据 collect + mock analysis + render。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import pytest
from collect import build_collected_data
from report_renderer import render_report, build_filename

REAL_DIR = Path(__file__).resolve().parents[3] / "astronclaw-result" / "all-suite" / "round-2"
TASKS_ROOT = Path(__file__).resolve().parents[2] / "tasks"


@pytest.mark.skipif(not REAL_DIR.exists(), reason="真实评测数据不存在")
def test_full_pipeline_real_data():
    data = build_collected_data([REAL_DIR], target_model="xsparkx2flash",
                                tasks_root=TASKS_ROOT)
    # 至少识别到多个模型
    assert len(data["models"]) >= 2
    assert data["is_single_model"] is False
    # 目标模型存在
    assert any(m["model"] == data["target_model"] for m in data["models"])
    # 有待分析任务
    assert len(data["tasks_to_analyze"]) > 0
    # 每个待分析任务的 target_transcript 路径有效
    for a in data["tasks_to_analyze"]:
        if a["target_transcript"]:
            assert Path(a["target_transcript"]).exists()

    # mock 空 analysis 仍能渲染（表格部分）
    empty_analysis = {"task_analysis": [], "target_model_weaknesses": [],
                      "improvement_suggestions": [], "capability_mapping": {}}
    md = render_report(data, empty_analysis)
    assert "## 一、整体排名" in md
    assert "## 三、分类别得分对比" in md
    assert "## 四、各任务详细得分" in md
    assert build_filename(data).endswith("_models_report.md")
