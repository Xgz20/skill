"""报告生成器数据类定义，统一各阶段类型契约。"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TaskResult:
    """单个任务在单个模型上的评测结果。"""
    task_id: str
    category: str
    status: str
    timed_out: bool
    execution_time: Optional[float]
    score: float                      # grading.mean
    breakdown: Dict[str, float]       # grading.runs[0].breakdown
    notes: str                        # grading.runs[0].notes
    input_tokens: int
    output_tokens: int
    total_tokens: int
    request_count: int
    difficulty: str = "unknown"       # L1/L2/L3/L4，缺失为 unknown


@dataclass
class ModelResult:
    """单个模型的完整评测结果。"""
    model: str                        # JSON 的 model 字段（内部 key）
    display_name: str                 # 展示名（默认同 model）
    suite: str
    benchmark_version: str
    tasks: List[TaskResult] = field(default_factory=list)

    @property
    def task_count(self) -> int:
        return len(self.tasks)

    @property
    def total_tokens(self) -> int:
        return sum(t.total_tokens for t in self.tasks)

    @property
    def total_requests(self) -> int:
        return sum(t.request_count for t in self.tasks)
