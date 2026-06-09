"""Test suite for assemble.py — case assembly and sequence allocation."""
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from assemble import assign_next_sequence, render_frontmatter, assemble_case_file


class TestSequenceAssignment(unittest.TestCase):
    def test_empty_dirs_return_0001(self):
        """No existing tasks → sequence 1."""
        with tempfile.TemporaryDirectory() as tmp:
            generated = Path(tmp) / "generated"
            tasks = Path(tmp) / "tasks"
            generated.mkdir()
            tasks.mkdir()

            seq = assign_next_sequence(generated, tasks)
            self.assertEqual(seq, 1)

    def test_finds_max_from_both_dirs(self):
        """Should scan both generated_cases and tasks for max sequence."""
        with tempfile.TemporaryDirectory() as tmp:
            generated = Path(tmp) / "generated"
            tasks = Path(tmp) / "tasks"
            generated.mkdir()
            tasks.mkdir()

            (generated / "task_0003_example.md").touch()
            (tasks / "task_0007_another.md").touch()

            seq = assign_next_sequence(generated, tasks)
            self.assertEqual(seq, 8)  # 7 + 1


class TestFrontmatterRendering(unittest.TestCase):
    def test_renders_basic_fields(self):
        data = {
            "id": "task_0001_example",
            "name": "Example Task",
            "category": "research",
            "grading_type": "automated",
            "timeout_seconds": 180,
            "workspace_files": []
        }
        yaml_text = render_frontmatter(data)

        self.assertIn("id: task_0001_example", yaml_text)
        self.assertIn("name: Example Task", yaml_text)
        self.assertIn("workspace_files: []", yaml_text)

    def test_renders_yaml_array_format(self):
        data = {
            "id": "task_0001_test",
            "name": "Test",
            "category": "coding",
            "capabilities": [
                "instruction_following",
                "tool_use",
                "multi_step_reasoning"
            ],
            "grading_type": "hybrid",
            "timeout_seconds": 120,
            "workspace_files": []
        }
        yaml_text = render_frontmatter(data)

        # 验证 YAML 数组格式（标准YAML格式，无缩进）
        self.assertIn("capabilities:", yaml_text)
        self.assertIn("- instruction_following", yaml_text)
        self.assertIn("- tool_use", yaml_text)


class TestCaseAssembly(unittest.TestCase):
    def test_assembles_complete_md_file(self):
        workflow_result = {
            "frontmatter": {
                "name": "Stock Lookup",
                "category": "research",
                "scene": "finance_investment_research",
                "sub_scene": "realtime_quote",
                "source": "astronclaw",
                "grading_type": "hybrid",
                "timeout_seconds": 180,
                "capabilities": ["tool_use", "data_retrieval"],
                "workspace_files": []
            },
            "sections": {
                "prompt": "Query stock price",
                "expected_behavior": "Agent should use web search",
                "grading_criteria": [
                    "File created",
                    "Contains price"
                ],
                "automated_checks": "def grade(transcript, workspace):\n    return {}",
                "llm_judge_rubric": "### Accuracy\n**Score 1.0**: Perfect"
            },
            "metadata": {
                "task_name_suggestion": "stock_price_lookup",
                "language": "en"
            }
        }

        case_id = "task_0001_stock_price_lookup"
        md_content = assemble_case_file(workflow_result, case_id)

        # 验证结构
        self.assertIn("---", md_content)
        self.assertIn("id: task_0001_stock_price_lookup", md_content)
        self.assertIn("## Prompt", md_content)
        self.assertIn("## Expected Behavior", md_content)
        self.assertIn("## Grading Criteria", md_content)
        self.assertIn("- [ ] File created", md_content)
        self.assertIn("## Automated Checks", md_content)
        self.assertIn("```python", md_content)
        self.assertIn("## LLM Judge Rubric", md_content)
