# Jupyter MCP End-to-End Test Suite

## Overview

This test suite validates the complete functionality of the UV-first Jupyter MCP server, including Claude integration, error recovery, and the exact usage patterns Claude should follow.

## Claude Usage Pattern Tests

This test suite validates the exact patterns Claude should use:

```python
# 1. Always start with initialization
result = jupyter_initialize(working_dir='.')
session_id = result['session_id']

# 2. Execute code with rich feedback
jupyter_execute_cell(session_id, "import pandas as pd")

# 3. If ImportError, install via UV (NEVER pip!)
jupyter_ensure_dependencies(session_id, ['pandas'])

# 4. Get help when needed
jupyter_get_guidance('fix_error', context={'error_type': 'ModuleNotFoundError'})
```

## Quick Start

1. **Setup test environment:**
   ```bash
   ./test/setup_test_env.sh
   ```

2. **Run all tests:**
   ```bash
   ./test/run_tests.sh
   ```

3. **Run with Cursor integration:**
   ```bash
   ./test/run_tests.sh --with-cursor
   ```

4. **Cleanup:**
   ```bash
   ./test/cleanup.sh
   ```

## Test Structure

```
test/
├── setup_test_env.sh         # Setup test environment and MCP
├── run_tests.sh             # Main test runner
├── cleanup.sh               # Cleanup script
│
├── core_tests/              # Core functionality tests
│   ├── test_01_installation.py
│   ├── test_02_initialization.py
│   ├── test_03_execution.py
│   └── test_04_error_recovery.py
│
├── integration_tests/       # Claude CLI integration
│   ├── test_claude_patterns.sh
│   ├── test_module_import_flow.sh
│   └── test_guidance_system.sh
│
├── workflows/               # Real-world scenarios
│   ├── test_complete_workflow.py
│   ├── test_uv_package_mgmt.py
│   └── test_deployment.py
│
└── test_workspace/          # Managed test workspace
    └── current/            # Active test directory
```

## Test Coverage

### Core Tests
- ✅ MCP installation and registration
- ✅ UV environment detection and creation
- ✅ Kernel daemon lifecycle
- ✅ Code execution with persistence
- ✅ Error handling and recovery

### Integration Tests
- ✅ Claude CLI tool invocation
- ✅ Import error → UV install → retry flow
- ✅ Guidance system functionality
- ✅ Multi-turn conversations

### Workflow Tests
- ✅ Complete initialization → execution → error → fix flow
- ✅ UV-centric package management (no pip!)
- ✅ Data science workflow
- ✅ Deployment validation

## Key Validations

1. **UV-Centric Approach**
   - All package management uses UV
   - Never uses pip directly
   - Maintains uv.lock consistency

2. **Session Management**
   - All operations use session_id
   - State persists across calls
   - Clean kernel lifecycle

3. **Rich Error Handling**
   - Errors include fix suggestions
   - Auto-recovery for common issues
   - Guidance tools provide help

4. **Claude Integration**
   - MCP tools work via Claude CLI
   - Proper tool registration
   - Clean uninstall

## Running Specific Tests

### Test MCP Installation Only
```bash
python test/core_tests/test_01_installation.py
```

### Test Claude Patterns Only
```bash
bash test/integration_tests/test_claude_patterns.sh
```

### Test Complete Workflow
```bash
python test/workflows/test_complete_workflow.py
```

## Debugging

If tests fail, check:

1. **MCP Registration:**
   ```bash
   claude mcp list
   ```

2. **Kernel Status:**
   ```bash
   cat .kernel_daemon.lock
   ps aux | grep kernel_daemon
   ```

3. **Test Logs:**
   ```bash
   cat test/test_workspace/current/test.log
   ```

## Expected Test Duration

- Quick tests: ~5 minutes
- Full test suite: ~10-15 minutes
- With Cursor integration: ~20 minutes

## Success Criteria

All tests should pass with:
- ✅ No orphaned processes
- ✅ Clean MCP registration/deregistration
- ✅ No port conflicts
- ✅ Workspace is reusable
- ✅ UV handles all package management