#!/bin/bash
# End-to-end test: invoke workflow and verify output

set -e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="$SKILL_DIR/../../output/generated_cases"

echo "=== E2E Test: Generate a test case from Query ==="

# Clean previous test output
rm -f "$OUTPUT_DIR"/task_9998_*.md

# Test Query (English)
TEST_QUERY="Look up the current price of Apple stock (AAPL) and save it to a file."
TEST_LANG="en"

echo "Query: $TEST_QUERY"
echo "Language: $TEST_LANG"

# Mock: In real execution, this would invoke the workflow via Claude Code
# For testing, we simulate the workflow output and call assemble.py directly

python3 << EOF
import sys
from pathlib import Path
sys.path.insert(0, str(Path("$SKILL_DIR") / "lib"))

from assemble import assign_next_sequence, assemble_case_file

# Mock workflow output
workflow_result = {
    "frontmatter": {
        "name": "Stock Price Lookup",
        "category": "research",
        "scene": "finance_investment_research",
        "sub_scene": "realtime_quote_lookup",
        "source": "astronclaw",
        "grading_type": "hybrid",
        "timeout_seconds": 180,
        "capabilities": ["tool_use", "realtime_data_retrieval", "file_creation"],
        "workspace_files": []
    },
    "sections": {
        "prompt": "$TEST_QUERY",
        "expected_behavior": "Agent should use web search to find current AAPL price and save to file.",
        "grading_criteria": ["File created", "Contains AAPL ticker", "Contains price"],
        "automated_checks": "def grade(transcript, workspace):\\n    return {'file_created': 1.0}",
        "llm_judge_rubric": "### Accuracy\\n**Score 1.0**: Perfect"
    },
    "metadata": {
        "task_name_suggestion": "stock_price_lookup_test",
        "language": "$TEST_LANG"
    }
}

# Assign sequence
seq = assign_next_sequence(
    Path("$OUTPUT_DIR"),
    Path("$SKILL_DIR/../../tasks")
)
case_id = f"task_{seq:04d}_stock_price_lookup_test"

# Assemble and write
md_content = assemble_case_file(workflow_result, case_id)
output_file = Path("$OUTPUT_DIR") / f"{case_id}.md"
output_file.parent.mkdir(parents=True, exist_ok=True)
output_file.write_text(md_content)

print(f"✓ Generated: {output_file}")
print(f"✓ Sequence assigned: {seq}")
EOF

# Verify output file exists
if [ -f "$OUTPUT_DIR"/task_*_stock_price_lookup_test.md ]; then
    echo "✓ Output file created"
else
    echo "✗ Output file missing"
    exit 1
fi

# Verify file contains expected content
GENERATED_FILE=$(ls "$OUTPUT_DIR"/task_*_stock_price_lookup_test.md)
if grep -q "source: astronclaw" "$GENERATED_FILE" && \
   grep -q "scene: finance_investment_research" "$GENERATED_FILE" && \
   grep -q "## Prompt" "$GENERATED_FILE" && \
   grep -q "## Expected Behavior" "$GENERATED_FILE"; then
    echo "✓ File format correct"
else
    echo "✗ File format validation failed"
    exit 1
fi

echo "=== E2E Test PASSED ==="
