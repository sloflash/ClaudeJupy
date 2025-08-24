#!/bin/bash

# Jupyter MCP Test Cleanup Script
# Cleans up test environment, processes, and MCP registration

echo "🧹 Cleaning up Jupyter MCP test environment"
echo "==========================================="

# Function to kill processes safely
kill_process_by_name() {
    local process_name="$1"
    local pids=$(pgrep -f "$process_name" 2>/dev/null)
    
    if [ ! -z "$pids" ]; then
        echo "  Stopping $process_name processes..."
        for pid in $pids; do
            kill $pid 2>/dev/null || true
            sleep 0.5
            kill -9 $pid 2>/dev/null || true  # Force kill if still running
        done
    fi
}

# 1. Remove MCP registration
echo -e "\n📌 Removing MCP registration..."
if claude mcp list | grep -q "jupyter-executor"; then
    claude mcp remove jupyter-executor
    echo "  ✓ MCP server unregistered"
else
    echo "  ℹ️  MCP server was not registered"
fi

# 2. Stop kernel daemon
echo -e "\n🛑 Stopping kernel daemon..."
kill_process_by_name "kernel_daemon.py"
kill_process_by_name "jupyter_kernel"
kill_process_by_name "ipykernel_launcher"
echo "  ✓ Kernel processes stopped"

# 3. Clean up lock files
echo -e "\n🔒 Removing lock files..."
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
rm -f "$PROJECT_ROOT/.kernel_daemon.lock" 2>/dev/null
rm -f "$PROJECT_ROOT/.kernel_connection.json" 2>/dev/null
rm -f "$HOME/mcp_test_workspace/current/.kernel_daemon.lock" 2>/dev/null
rm -f "$HOME/mcp_test_workspace/current/.kernel_connection.json" 2>/dev/null
echo "  ✓ Lock files removed"

# 4. Archive test session (optional)
TEST_WORKSPACE="$HOME/mcp_test_workspace"
CURRENT_TEST="$TEST_WORKSPACE/current"

if [ -d "$CURRENT_TEST" ] && [ "$1" != "--no-archive" ]; then
    echo -e "\n📦 Archiving test session..."
    ARCHIVE_NAME="session_$(date +%Y%m%d_%H%M%S)"
    ARCHIVE_PATH="$TEST_WORKSPACE/archived/$ARCHIVE_NAME"
    
    mkdir -p "$TEST_WORKSPACE/archived"
    
    # Keep only last 5 archived sessions
    ARCHIVE_COUNT=$(ls -1 "$TEST_WORKSPACE/archived" 2>/dev/null | wc -l)
    if [ $ARCHIVE_COUNT -ge 5 ]; then
        OLDEST=$(ls -1t "$TEST_WORKSPACE/archived" | tail -1)
        rm -rf "$TEST_WORKSPACE/archived/$OLDEST"
        echo "  Removed old archive: $OLDEST"
    fi
    
    # Move current to archive
    mv "$CURRENT_TEST" "$ARCHIVE_PATH"
    echo "  ✓ Session archived to: $ARCHIVE_PATH"
    
    # Recreate empty current directory
    mkdir -p "$CURRENT_TEST"
fi

# 5. Check for orphaned processes
echo -e "\n🔍 Checking for orphaned processes..."
ORPHANED=$(ps aux | grep -E "(jupyter|kernel|ipython)" | grep -v grep | wc -l)
if [ $ORPHANED -gt 0 ]; then
    echo "  ⚠️  Warning: Found $ORPHANED potential orphaned processes"
    echo "  Run 'ps aux | grep jupyter' to investigate"
else
    echo "  ✓ No orphaned processes found"
fi

# 6. Verify cleanup
echo -e "\n✅ Cleanup verification:"
echo -n "  MCP removed: "
if ! claude mcp list | grep -q "jupyter-executor"; then
    echo "✓"
else
    echo "✗ (still registered)"
fi

echo -n "  Lock files: "
if [ ! -f "$PROJECT_ROOT/.kernel_daemon.lock" ] && [ ! -f "$CURRENT_TEST/.kernel_daemon.lock" ]; then
    echo "✓"
else
    echo "✗ (still exist)"
fi

echo -n "  Kernel processes: "
if [ $(pgrep -f "kernel_daemon" | wc -l) -eq 0 ]; then
    echo "✓"
else
    echo "✗ (still running)"
fi

echo -e "\n🎉 Cleanup complete!"

# Optional: Full reset
if [ "$1" == "--full-reset" ]; then
    echo -e "\n🔥 Performing full reset..."
    rm -rf "$TEST_WORKSPACE"
    echo "  ✓ Test workspace completely removed"
fi