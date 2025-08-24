# Project Constraints

## Virtual Environment Requirements

### Always Use UV with .venv

**Constraint**: ALL Python projects MUST use `uv` for virtual environment management with `.venv` as the environment directory.

**Implementation**:
- Always create virtual environment using: `uv venv .venv`
- Always activate before running any Python code: `source .venv/bin/activate`
- Install dependencies using: `uv pip install <package>`
- The kernel daemon will automatically detect and use `.venv` if present

**Environment Setup Flow**:
```bash
# Initial setup (once per project)
uv venv .venv
source .venv/bin/activate
uv pip install jupyter ipykernel nbformat jupyter_client pytest

# Before any Python execution
source .venv/bin/activate
python script.py
```

**Enforcement**:
- Never use system Python for project code
- Always check for `.venv` existence before running Python
- Kernel daemon automatically uses `.venv` Python interpreter
- All tests must run within the virtual environment

## Core Constraints

### 1. File Management - Always Update Existing Files

**Constraint**: ALWAYS attempt to update existing files rather than creating new ones.

**Implementation**:
- Before creating any new file, search for existing files that serve the same purpose
- Update implementation in-place within existing files
- Append new functionality to existing modules rather than creating new ones
- Preserve existing code structure and organization

**File Update Priority**:
1. First: Check if the file already exists
2. If exists → Update the existing file
3. If not exists → Create once, then always reuse
4. Never create duplicate files with similar names (e.g., `script.py`, `script_v2.py`, `script_new.py`)

**Example Workflow**:
```
Request: "Add user authentication"
✓ Correct: Update existing auth.py or main.py
✗ Wrong: Create new auth_new.py or authentication.py
```

### 2. Test Execution - Always Run Tests After Code Changes

**Constraint**: EVERY code update MUST be followed by test execution.

**Implementation**:
- After any code modification → automatically run relevant tests
- Code changes are NOT considered complete until tests pass
- No manual "test later" workflow allowed
- USE SAME TEST file name for .ipynb

**Test Execution Flow**:
```
1. Update code
2. Save file
3. Run tests immediately (automated)
4. If tests pass → Continue to next task
5. If tests fail → Fix code → Run tests again (repeat until pass)
```

**Enforcement Rules**:
- Maximum 3 test-fix cycles before requiring human intervention
- Test execution is non-negotiable - cannot skip tests "just this once"
- Even small changes (single line fixes) require test validation

## Specific Implementation Rules

### For Python Projects
```python
# After any code update:
os.system("python -m pytest tests/")  # Must run automatically
# or
os.system("python test.py")  # Must run automatically
```

### For Jupyter Notebooks
```python
# After updating any cell:
1. Execute the updated cell
2. Run validation tests in next cell
3. Only proceed if tests pass
```

### For Web Projects
```bash
# After any code update:
npm test  # Must run automatically
# or
npm run test:unit && npm run test:integration  # Must run automatically
```

## Exceptions

### When File Creation is Acceptable
- Initial project setup (first time only)
- Creating test files for new features
- Configuration files that don't exist yet
- Documentation files

### When Test Skipping is Acceptable
- NEVER during implementation
- Only for documentation-only changes
- Only for comment-only changes (still recommended to run)

## Validation Checklist

Before considering any task complete, verify:

- [ ] Existing files were checked before creating new ones
- [ ] Implementation updated existing files where possible
- [ ] Tests were run after EVERY code change
- [ ] All tests are passing
- [ ] No duplicate files were created
- [ ] File naming remains consistent

## Error Handling

### If Unable to Update Existing File
```
1. Report why update isn't possible
2. Request permission to create new file
3. Document relationship to existing files
4. Ensure new file will be reused in future
```

### If Tests Fail
```
1. Do NOT proceed to next task
2. Fix the failing code
3. Re-run tests
4. Repeat until tests pass (max 3 attempts)
5. If still failing after 3 attempts, stop and report
```

## Monitoring and Compliance

Claude Code should track:
- Number of files updated vs created
- Test execution rate (should be 100%)
- Test pass rate after updates
- File reuse rate

## Example Constraint Violations to Avoid

❌ **Bad Practice**:
```
"I'll create a new script for this feature"
"Let me make a fresh notebook for testing"
"I'll test this later after implementing everything"
"Creating backup_v2.py since backup.py exists"
```

✅ **Good Practice**:
```
"Updating existing implementation in main.py"
"Adding new cells to existing notebook"
"Running tests now after code update"
"Modifying backup.py to add new functionality"
```

## Enforcement

These constraints are **mandatory** and should be treated as:
- Hard requirements, not suggestions
- Apply to ALL code changes, regardless of size
- Override convenience or speed considerations
- Essential for maintaining code quality and consistency

## Jupyter Kernel Persistence Tool - Deployment

### Tool Overview
A persistent Jupyter kernel execution system that maintains state across cell executions, designed as an MCP tool for Claude Code.

### Deployment Options

#### Option 1: Global Installation (Recommended)
**Quick deployment for all projects:**
```bash
# From the ClaudeJupy directory
./deploy_jupyter_tool.sh
```

This will:
1. Install to `~/claude-tools/jupyter/`
2. Create dedicated venv with dependencies
3. **Display exact MCP config JSON to add to Claude Code**

#### Option 2: Per-Project Installation
Copy files to specific project and configure locally (see INSTALLATION.md)

### Post-Deployment Configuration

**Add to Claude Code config:**
Location: `~/Library/Application Support/Claude/claude_desktop_config.json`

The deployment script will show the exact JSON to add, which includes:
- Path to tool's Python interpreter
- Path to MCP server script
- Tool name: `jupyter-executor`

### Available MCP Tools After Deployment

- `mcp__jupyter-executor__execute_code(code)` - Execute Python in persistent kernel
- `mcp__jupyter-executor__add_notebook_cell(notebook_path, cell_type, source)` - Add cells to notebooks  
- `mcp__jupyter-executor__kernel_status()` - Check kernel status
- `mcp__jupyter-executor__shutdown_kernel()` - Shutdown kernel

### Key Features

1. **Automatic .venv Detection**: Searches current and parent directories for `.venv`
2. **Package Auto-Installation**: First cell in new notebooks installs required packages
3. **State Persistence**: Variables and imports persist across cell executions
4. **UV Support**: Prefers `uv pip` for package installation in venv environments

### Testing After Deployment

```python
# Test in Claude Code
mcp__jupyter-executor__execute_code("x = 42; print(x)")
mcp__jupyter-executor__execute_code("print(f'x is still {x}')")  # Should work!
```

### File Structure
```
~/claude-tools/jupyter/
├── .venv/                    # Tool's dedicated venv
├── mcp_jupyter_server.py     # MCP interface
├── kernel_daemon.py          # Persistent kernel manager
└── notebook_client.py        # Notebook cell handler
```

### Updating the Tool
Re-run `./deploy_jupyter_tool.sh` to update to latest version