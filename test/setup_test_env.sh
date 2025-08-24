#!/bin/bash

# Jupyter MCP Test Environment Setup
# This script sets up a clean test environment for end-to-end testing

set -e  # Exit on error

echo "🚀 Setting up Jupyter MCP test environment"
echo "=========================================="

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "📁 Project root: $PROJECT_ROOT"

# Create test workspace
TEST_WORKSPACE="$HOME/mcp_test_workspace"
CURRENT_TEST="$TEST_WORKSPACE/current"

echo -e "\n📦 Creating test workspace..."
mkdir -p "$CURRENT_TEST"
cd "$CURRENT_TEST"

# Clean any existing test files
rm -rf .venv uv.lock pyproject.toml .kernel_daemon.lock

# Create a test pyproject.toml
echo -e "\n📝 Creating test pyproject.toml..."
cat > pyproject.toml << 'EOF'
[project]
name = "test-project"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []

[tool.uv]
dev-dependencies = [
    "pytest",
    "pandas",
    "numpy"
]
EOF

# Remove any existing MCP registration
echo -e "\n🧹 Cleaning existing MCP registration..."
claude mcp remove jupyter-executor 2>/dev/null || true

# Add the MCP server locally
echo -e "\n📌 Adding MCP server to Claude..."
# Using the new src structure
if [ -f "$PROJECT_ROOT/src/ml_jupyter_mcp/server.py" ]; then
    # New modular structure
    echo "Using new modular structure from src/"
    cd "$PROJECT_ROOT"
    
    # Install the package in development mode first
    echo "Installing package in development mode..."
    uv pip install -e . 2>/dev/null || pip install -e .
    
    # Add to Claude using the installed command (force update if exists)
    claude mcp remove jupyter-executor 2>/dev/null || true
    claude mcp add jupyter-executor "ml-jupyter-mcp"
    
elif [ -f "$PROJECT_ROOT/mcp_jupyter_server_fast.py" ]; then
    # Legacy structure
    echo "Using legacy structure"
    claude mcp add jupyter-executor "python" "$PROJECT_ROOT/mcp_jupyter_server_fast.py"
else
    echo "❌ Error: Could not find MCP server files!"
    exit 1
fi

# Verify MCP installation
echo -e "\n✅ Verifying MCP installation..."
if claude mcp list | grep -q "jupyter-executor"; then
    echo "✓ MCP server registered successfully"
else
    echo "❌ Error: MCP server not found in claude mcp list"
    exit 1
fi

# Create test fixtures
echo -e "\n📁 Creating test fixtures..."
cd "$CURRENT_TEST"
mkdir -p fixtures

# Create sample test code
cat > fixtures/basic_math.py << 'EOF'
# Basic math operations for testing
x = 42
y = 13
result = x + y
print(f"Result: {result}")
EOF

cat > fixtures/import_test.py << 'EOF'
# Test import and error recovery
try:
    import pandas as pd
    print("Pandas imported successfully")
except ImportError:
    print("Pandas not found - needs installation")
EOF

cat > fixtures/error_test.py << 'EOF'
# Test error handling
def divide(a, b):
    return a / b

# This should cause ZeroDivisionError
result = divide(10, 0)
EOF

# Create test tracking file
echo -e "\n📊 Setting up test tracking..."
cat > test_status.json << EOF
{
  "setup_time": "$(date -u +"%Y-%m-%d %H:%M:%S UTC")",
  "project_root": "$PROJECT_ROOT",
  "test_workspace": "$TEST_WORKSPACE",
  "mcp_registered": true,
  "status": "ready"
}
EOF

echo -e "\n✨ Test environment setup complete!"
echo "📍 Test workspace: $CURRENT_TEST"
echo "🔧 MCP server: jupyter-executor"
echo ""
echo "Next steps:"
echo "  1. Run tests: ./test/run_tests.sh"
echo "  2. Check MCP: claude mcp list"
echo "  3. Test manually: echo 'use jupyter-executor to calculate 2+2' | claude"