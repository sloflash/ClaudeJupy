#!/bin/bash

# Test exact Claude usage patterns
# This validates the patterns documented in the README

echo "Testing Claude Usage Patterns"
echo "=============================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a Claude test
run_claude_test() {
    local test_name="$1"
    local test_input="$2"
    local expected_pattern="$3"
    
    echo -e "\n📝 Testing: $test_name"
    
    # Run the test
    OUTPUT=$(echo "$test_input" | claude 2>&1)
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -ne 0 ]; then
        echo -e "${RED}✗ Command failed${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
    
    # Check for expected pattern
    if echo "$OUTPUT" | grep -qi "$expected_pattern"; then
        echo -e "${GREEN}✓ Pattern found: $expected_pattern${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ Pattern not found: $expected_pattern${NC}"
        echo "Output preview: ${OUTPUT:0:200}..."
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Pattern 1: Always start with initialization
echo -e "\n### Pattern 1: Initialization First ###"
run_claude_test "Initialization Pattern" \
"Use jupyter-executor to:
1. Call jupyter_initialize(working_dir='.')
2. Get the session_id from the result
3. Print 'Initialized with session:' and the session_id" \
"session"

# Pattern 2: Execute code with rich feedback  
echo -e "\n### Pattern 2: Code Execution ###"
run_claude_test "Execution Pattern" \
"Use jupyter-executor to:
1. Initialize first
2. Execute this code: import pandas as pd; print('Pandas imported')
3. Show the output" \
"pandas"

# Pattern 3: ImportError → UV install → retry
echo -e "\n### Pattern 3: Error Recovery via UV ###"
TEST_INPUT='Use jupyter-executor to:
1. Initialize the environment
2. Try to import matplotlib: import matplotlib
3. If it fails with ImportError:
   - Use jupyter_ensure_dependencies(session_id, ["matplotlib"]) to install via UV
   - NEVER use pip install
   - Retry the import
4. Confirm success'

run_claude_test "UV Package Installation" "$TEST_INPUT" "matplotlib"

# Check that pip was NOT used
echo -e "\n🔍 Verifying UV-only approach..."
LAST_OUTPUT=$(echo "$TEST_INPUT" | claude 2>&1)
if echo "$LAST_OUTPUT" | grep -q "pip install" && ! echo "$LAST_OUTPUT" | grep -q "jupyter_ensure_dependencies"; then
    echo -e "${RED}✗ CRITICAL: pip was used instead of UV!${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
else
    echo -e "${GREEN}✓ UV-first principle maintained${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi

# Pattern 4: Get guidance when needed
echo -e "\n### Pattern 4: Guidance System ###"
run_claude_test "Guidance Pattern" \
"Use jupyter-executor to:
1. Initialize
2. Call jupyter_get_guidance('fix_error', context={'error_type': 'ModuleNotFoundError'})
3. Show the guidance" \
"jupyter_ensure_dependencies\|guidance\|fix"

# Pattern 5: Complete workflow
echo -e "\n### Pattern 5: Complete Workflow ###"
WORKFLOW_TEST='Use jupyter-executor following this exact pattern:
# 1. Always start with initialization
result = jupyter_initialize(working_dir=".")
session_id = result["session_id"]

# 2. Execute code with rich feedback
jupyter_execute_cell(session_id, "x = 42")

# 3. Show persistence
jupyter_execute_cell(session_id, "print(f\"x = {x}\")")

Print the final result'

run_claude_test "Complete Workflow" "$WORKFLOW_TEST" "42"

# Summary
echo -e "\n=============================="
echo "Test Summary"
echo "=============================="
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✅ All Claude pattern tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Some Claude pattern tests failed${NC}"
    exit 1
fi