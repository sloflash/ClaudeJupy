#!/bin/bash

# Main test runner for Jupyter MCP
# Runs all test suites in sequence

set -e  # Exit on error

echo "🚀 Running Jupyter MCP End-to-End Tests"
echo "========================================"
echo "$(date)"
echo ""

# Get project root
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TEST_DIR="$PROJECT_ROOT/test"
TEST_WORKSPACE="$HOME/mcp_test_workspace/current"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test result tracking
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

# Function to run a test and track results
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -e "\n${YELLOW}Running: $test_name${NC}"
    echo "----------------------------------------"
    
    if eval "$test_command"; then
        echo -e "${GREEN}✓ $test_name passed${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ $test_name failed${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        FAILED_TESTS+=("$test_name")
    fi
}

# Setup test environment
echo "📦 Setting up test environment..."
if ! bash "$TEST_DIR/setup_test_env.sh"; then
    echo -e "${RED}Failed to setup test environment${NC}"
    exit 1
fi

# Change to test workspace
cd "$TEST_WORKSPACE"

# Core Tests
echo -e "\n${YELLOW}═══ CORE TESTS ═══${NC}"

# Test 1: MCP Installation
run_test "MCP Installation" "python '$TEST_DIR/core_tests/test_01_installation.py'"

# Test 2: Initialization Pattern
run_test "Initialization Pattern" "python '$TEST_DIR/core_tests/test_02_initialization.py'"

# Test 3: Code Execution
run_test "Code Execution" "python '$TEST_DIR/core_tests/test_03_execution.py'"

# Test 4: Error Recovery
run_test "Error Recovery" "python '$TEST_DIR/core_tests/test_04_error_recovery.py'"

# Integration Tests
echo -e "\n${YELLOW}═══ INTEGRATION TESTS ═══${NC}"

# Test 5: Claude Patterns
run_test "Claude Usage Patterns" "bash '$TEST_DIR/integration_tests/test_claude_patterns.sh'"

# Test 6: Module Import Flow
run_test "Module Import Flow" "bash '$TEST_DIR/integration_tests/test_module_import_flow.sh'"

# Test 7: Guidance System
run_test "Guidance System" "bash '$TEST_DIR/integration_tests/test_guidance_system.sh'"

# Workflow Tests
echo -e "\n${YELLOW}═══ WORKFLOW TESTS ═══${NC}"

# Test 8: Complete Workflow
run_test "Complete Workflow" "python '$TEST_DIR/workflows/test_complete_workflow.py'"

# Test 9: UV Package Management
run_test "UV Package Management" "python '$TEST_DIR/workflows/test_uv_package_mgmt.py'"

# Optional: Cursor Integration Tests
if [ "$1" == "--with-cursor" ]; then
    echo -e "\n${YELLOW}═══ CURSOR INTEGRATION ═══${NC}"
    
    # Open Cursor in test workspace
    echo "Opening Cursor IDE..."
    cursor "$TEST_WORKSPACE" &
    CURSOR_PID=$!
    sleep 5
    
    # Run Cursor-specific tests
    run_test "Cursor Claude Integration" "bash '$TEST_DIR/integration_tests/test_cursor_session.sh'"
    
    # Close Cursor
    echo "Closing Cursor..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        osascript -e 'quit app "Cursor"' 2>/dev/null || true
    else
        kill $CURSOR_PID 2>/dev/null || true
    fi
    sleep 2
fi

# Cleanup
echo -e "\n🧹 Running cleanup..."
bash "$TEST_DIR/cleanup.sh" --no-archive

# Test Summary
echo -e "\n${YELLOW}═══ TEST SUMMARY ═══${NC}"
echo "Total tests run: $((TESTS_PASSED + TESTS_FAILED))"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"

if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
    echo -e "\n${RED}Failed tests:${NC}"
    for test in "${FAILED_TESTS[@]}"; do
        echo "  - $test"
    done
fi

echo ""
echo "📋 Key validations performed:"
echo "  ✓ UV-centric package management (no pip!)"
echo "  ✓ Initialize → Execute → Error → Fix pattern"
echo "  ✓ Rich error feedback and guidance"
echo "  ✓ Clean module architecture"
echo "  ✓ MCP registration and cleanup"

# Exit with appropriate code
if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Some tests failed. Please review the output above.${NC}"
    exit 1
fi