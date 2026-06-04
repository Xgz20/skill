"""Integration test: generated cases can be loaded by PinchBench."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from lib_tasks import TaskLoader
from assemble import assemble_case_file


class TestRoundTripParsing(unittest.TestCase):
    def test_generated_case_loads_successfully(self):
        """Assemble a case and verify lib_tasks.py can load it."""
        workflow_result = {
            "frontmatter": {
                "name": "Test Case",
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
                "prompt": "Test prompt",
                "expected_behavior": "Agent should do X",
                "grading_criteria": ["Criterion 1", "Criterion 2"],
                "automated_checks": "def grade(transcript, workspace):\n    return {'test': 1.0}",
                "llm_judge_rubric": "### Accuracy\n**Score 1.0**: Perfect"
            },
            "metadata": {
                "task_name_suggestion": "test_case",
                "language": "en"
            }
        }

        case_id = "task_9999_test_case"
        md_content = assemble_case_file(workflow_result, case_id)

        # Write to temp file
        with tempfile.TemporaryDirectory() as tmp:
            task_dir = Path(tmp) / "tasks"
            task_dir.mkdir()
            task_file = task_dir / f"{case_id}.md"
            task_file.write_text(md_content)

            # Load with TaskLoader
            loader = TaskLoader(task_dir)
            task = loader.load_task(task_file)

            # Verify fields
            self.assertEqual(task.task_id, case_id)
            self.assertEqual(task.name, "Test Case")
            self.assertEqual(task.category, "research")
            self.assertEqual(task.grading_type, "hybrid")
            self.assertIn("tool_use", task.frontmatter["capabilities"])
            self.assertEqual(task.frontmatter["source"], "astronclaw")
            self.assertEqual(task.frontmatter["scene"], "finance_investment_research")
            self.assertIn("Test prompt", task.prompt)
            self.assertIn("Criterion 1", task.grading_criteria)
            self.assertIsNotNone(task.automated_checks)
            self.assertIsNotNone(task.llm_judge_rubric)
