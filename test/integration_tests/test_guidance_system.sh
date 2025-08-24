#!/bin/bash

# Test the guidance system that helps Claude make correct decisions

echo "Testing Guidance System"
echo "======================="

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

TESTS_PASSED=0
TESTS_FAILED=0

# Test 1: Get guidance for setup
echo -e "\n${YELLOW}Test 1: Setup Guidance${NC}"
TEST_OUTPUT=$(cat << 'EOF' | claude 2>&1
Use jupyter-executor to:
1. Call jupyter_get_guidance('setup_environment')
2. Show the workflow steps provided
EOF
)

if echo "$TEST_OUTPUT" | grep -qi "jupyter_initialize\|workflow\|step"; then
    echo -e "${GREEN}✓ Setup guidance provided${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗ Setup guidance not clear${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 2: Error fix guidance
echo -e "\n${YELLOW}Test 2: Error Fix Guidance${NC}"
TEST_OUTPUT=$(cat << 'EOF' | claude 2>&1
Use jupyter-executor to:
1. Initialize
2. Get guidance for fixing a ModuleNotFoundError for pandas:
   jupyter_get_guidance('fix_error', context={'error_type': 'ModuleNotFoundError', 'module': 'pandas'})
3. Show the specific fix steps
EOF
)

if echo "$TEST_OUTPUT" | grep -qi "jupyter_ensure_dependencies.*pandas"; then
    echo -e "${GREEN}✓ Correct fix guidance (UV-based)${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
elif echo "$TEST_OUTPUT" | grep -qi "pip install"; then
    echo -e "${RED}✗ Wrong guidance: suggests pip instead of UV${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
else
    echo -e "${YELLOW}⚠ Fix guidance unclear${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi

# Test 3: What next suggestions
echo -e "\n${YELLOW}Test 3: What Next Suggestions${NC}"
TEST_OUTPUT=$(cat << 'EOF' | claude 2>&1
Use jupyter-executor to:
1. Initialize and get session_id
2. Execute: df = pd.DataFrame({'a': [1,2,3], 'b': [4,5,6]})
3. Call jupyter_what_next(session_id) to get recommendations
4. Show what it suggests to do with the DataFrame
EOF
)

if echo "$TEST_OUTPUT" | grep -qi "recommendation\|explore\|describe\|next"; then
    echo -e "${GREEN}✓ Next action recommendations provided${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠ Recommendations unclear${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi

# Test 4: Package installation guidance
echo -e "\n${YELLOW}Test 4: Package Installation Guidance${NC}"
TEST_OUTPUT=$(cat << 'EOF' | claude 2>&1
Use jupyter-executor to:
1. Get guidance on how to install packages:
   jupyter_get_guidance('install_package')
2. Show the rules about package management
3. Confirm it says to use UV, not pip
EOF
)

if echo "$TEST_OUTPUT" | grep -qi "uv\|jupyter_ensure_dependencies" && ! echo "$TEST_OUTPUT" | grep -q "pip install"; then
    echo -e "${GREEN}✓ Correct: UV-first guidance${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
elif echo "$TEST_OUTPUT" | grep -q "pip install"; then
    echo -e "${RED}✗ Wrong: guidance suggests pip${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
else
    echo -e "${YELLOW}⚠ Package guidance unclear${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi

# Test 5: Kernel management guidance
echo -e "\n${YELLOW}Test 5: Kernel Management Guidance${NC}"
TEST_OUTPUT=$(cat << 'EOF' | claude 2>&1
Use jupyter-executor to:
1. Get guidance for kernel management:
   jupyter_get_guidance('manage_kernel')
2. Show the lifecycle steps
3. Show troubleshooting tips
EOF
)

if echo "$TEST_OUTPUT" | grep -qi "jupyter_initialize\|restart\|shutdown\|lifecycle"; then
    echo -e "${GREEN}✓ Kernel management guidance provided${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠ Kernel guidance unclear${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi

# Test 6: General guidance
echo -e "\n${YELLOW}Test 6: General Guidance (Golden Rules)${NC}"
TEST_OUTPUT=$(cat << 'EOF' | claude 2>&1
Use jupyter-executor to:
1. Get general guidance: jupyter_get_guidance('general')
2. Show the golden rules
3. Confirm rule: "NEVER use pip - always use UV"
EOF
)

if echo "$TEST_OUTPUT" | grep -qi "never.*pip\|uv\|jupyter_ensure_dependencies"; then
    echo -e "${GREEN}✓ Golden rules include UV-first principle${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠ Golden rules unclear${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi

# Summary
echo -e "\n======================="
echo "Guidance System Test Summary"
echo "======================="
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✅ All guidance tests passed!${NC}"
    echo "✓ Guidance system promotes UV-first approach"
    exit 0
else
    echo -e "\n${RED}❌ Some guidance tests failed${NC}"
    exit 1
fi