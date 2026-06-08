"""数据类契约测试。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from models import TaskResult, ModelResult


def test_task_result_fields():
    t = TaskResult(
        task_id="task_stock",
        category="research",
        status="success",
        timed_out=False,
        execution_time=12.5,
        score=0.0,
        breakdown={"automated.file_created": 0.0},
        notes="failed",
        input_tokens=100,
        output_tokens=50,
        total_tokens=150,
        request_count=3,
    )
    assert t.task_id == "task_stock"
    assert t.score == 0.0
    assert t.total_tokens == 150


def test_model_result_aggregates():
    tasks = [
        TaskResult("task_a", "coding", "success", False, 1.0, 1.0, {}, "", 10, 5, 15, 1),
        TaskResult("task_b", "research", "success", False, 1.0, 0.5, {}, "", 20, 10, 30, 2),
    ]
    m = ModelResult(model="xspark", display_name="Spark", suite="all",
                    benchmark_version="2.0.0", tasks=tasks)
    assert m.total_tokens == 45
    assert m.total_requests == 3
    assert m.task_count == 2
