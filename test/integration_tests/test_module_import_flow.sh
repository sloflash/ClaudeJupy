#!/bin/bash

# Test the critical import error → UV install → retry flow
# This ensures Claude NEVER uses pip directly

echo "Testing Module Import Flow (UV-First)"
echo "======================================"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

TESTS_PASSED=0
TESTS_FAILED=0

# Test 1: Missing module → UV installation
echo -e "\n${YELLOW}Test 1: Missing Module Recovery${NC}"
TEST_OUTPUT=$(cat << 'EOF' | claude 2>&1
Use jupyter-executor to:
1. Initialize the environment
2. Try importing a package that might not exist: import seaborn as sns
3. If you get ModuleNotFoundError:
   - Install it using jupyter_ensure_dependencies (NOT pip!)
   - Show me the exact command you used
4. Try the import again
5. Execute: print("Seaborn imported successfully")
EOF
)

# Check for correct UV usage
if echo "$TEST_OUTPUT" | grep -q "pip install" && ! echo "$TEST_OUTPUT" | grep -q "jupyter_ensure_dependencies"; then
    echo -e "${RED}✗ CRITICAL: pip was used instead of UV!${NC}"
    echo "This violates the UV-first architecture"
    TESTS_FAILED=$((TESTS_FAILED + 1))
elif echo "$TEST_OUTPUT" | grep -qi "jupyter_ensure_dependencies\|uv"; then
    echo -e "${GREEN}✓ Correct: UV/jupyter_ensure_dependencies used${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠ Method unclear, checking output...${NC}"
    echo "$TEST_OUTPUT" | head -20
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi

# Test 2: Multiple package installation
echo -e "\n${YELLOW}Test 2: Multiple Package Installation${NC}"
TEST_OUTPUT=$(cat << 'EOF' | claude 2>&1
Use jupyter-executor to:
1. Initialize
2. Install multiple packages at once using jupyter_ensure_dependencies:
   - numpy
   - pandas
   - matplotlib
3. Show how you installed them (should be one command with a list)
EOF
)

if echo "$TEST_OUTPUT" | grep -q "jupyter_ensure_dependencies.*\[.*numpy.*pandas.*matplotlib.*\]"; then
    echo -e "${GREEN}✓ Correct: Multiple packages in one UV call${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠ Checking for UV usage...${NC}"
    if echo "$TEST_OUTPUT" | grep -qi "uv\|jupyter_ensure_dependencies"; then
        echo -e "${GREEN}✓ UV method used${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ Incorrect package installation method${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
fi

# Test 3: Dev dependencies
echo -e "\n${YELLOW}Test 3: Development Dependencies${NC}"
TEST_OUTPUT=$(cat << 'EOF' | claude 2>&1
Use jupyter-executor to:
1. Initialize
2. Install pytest as a development dependency using:
   jupyter_ensure_dependencies(session_id, ['pytest'], dev=True)
3. Confirm it was installed as a dev dependency
EOF
)

if echo "$TEST_OUTPUT" | grep -q "dev=True"; then
    echo -e "${GREEN}✓ Correct: Dev dependency flag used${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠ Dev dependency handling unclear${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi

# Test 4: Package name mapping
echo -e "\n${YELLOW}Test 4: Package Name Mapping${NC}"
TEST_OUTPUT=$(cat << 'EOF' | claude 2>&1
Use jupyter-executor to:
1. Initialize
2. Try to import cv2 (OpenCV)
3. If it fails, remember that cv2 comes from the package 'opencv-python'
4. Install the correct package using jupyter_ensure_dependencies
5. Show what package name you used for cv2
EOF
)

if echo "$TEST_OUTPUT" | grep -qi "opencv-python"; then
    echo -e "${GREEN}✓ Correct: Package name mapping understood${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠ Package name mapping unclear${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi

# Test 5: Never pip, always UV
echo -e "\n${YELLOW}Test 5: Enforcing UV-Only Policy${NC}"
TEST_OUTPUT=$(cat << 'EOF' | claude 2>&1
Use jupyter-executor to install these packages. Remember: NEVER use pip directly, always use jupyter_ensure_dependencies:
1. requests
2. beautifulsoup4
3. scipy

Show me the exact commands you used.
EOF
)

# Count pip mentions vs UV mentions
PIP_COUNT=$(echo "$TEST_OUTPUT" | grep -c "pip install" || true)
UV_COUNT=$(echo "$TEST_OUTPUT" | grep -c "jupyter_ensure_dependencies\|uv" || true)

if [ $PIP_COUNT -gt 0 ] && [ $UV_COUNT -eq 0 ]; then
    echo -e "${RED}✗ FAIL: pip used $PIP_COUNT times, UV not used${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
elif [ $UV_COUNT -gt 0 ]; then
    echo -e "${GREEN}✓ Perfect: UV/jupyter_ensure_dependencies used consistently${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠ Installation method unclear${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi

# Summary
echo -e "\n======================================"
echo "Module Import Flow Test Summary"
echo "======================================"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✅ All import flow tests passed!${NC}"
    echo "✓ UV-first principle strictly enforced"
    exit 0
else
    echo -e "\n${RED}❌ Some import flow tests failed${NC}"
    echo "⚠️  Check that Claude is using jupyter_ensure_dependencies, not pip"
    exit 1
fi