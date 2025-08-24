# Claude Code Instructions for Jupyter Notebooks

## Default Workflow for Notebook Execution

When working with Jupyter notebooks in this project, **ALWAYS** follow this workflow:

### 1. Environment Setup
- **ALWAYS** tie notebooks to the `.venv` from this folder as the Jupyter kernel
- Verify the kernel connection is using the correct Python environment before executing any cells
- Use `jupyter_initialize(working_dir='.')` to set up the environment

### 2. Thoughtful Code Writing
**BE DELIBERATE AND CAREFUL:**
- **Plan before coding** - Think through your approach before writing
- **Write small chunks** - Keep cells to 5-10 lines of code maximum
- **One concept per cell** - Each cell should do ONE thing
- **Explain first** - Always explain what the code will do before executing
- **Validate outputs** - Check results before moving to next cell
- **Add print statements** - Verify intermediate results with clear output

### 3. Cell Execution Pattern
Follow this strict pattern for cell execution:
1. Explain what the cell will do
2. Write a small, focused cell (5-10 lines max)
3. Execute the cell using `jupyter_execute_cell` or `jupyter_add_cell` with `execute=true`
4. Wait 5 seconds using `sleep 5` command
5. Verify the output is correct
6. If error occurs, STOP and analyze before continuing
7. Repeat for this pattern until you are done

### 4. Important Rules
- **DO NOT** batch execute multiple cells at once
- **DO NOT** skip the 5-second wait between cell executions
- **ALWAYS** verify each cell execution completes successfully before proceeding
- **ALWAYS** use the `.venv` from the current project folder, not a global environment
- **STOP on errors** - Don't continue if something fails
- **Save checkpoints** - Save notebook state every 3 cells
- **Test incrementally** - Verify each piece works before building on it

### 5. Package Management
- **NEVER** use `pip install` directly
- **ALWAYS** use `jupyter_ensure_dependencies()` for package installation
- This maintains consistency with the UV package manager and `uv.lock` file

### 6. Error Handling & Rollback Strategy
If a cell execution fails:
1. **STOP IMMEDIATELY** - Don't continue with errors
2. Analyze the error message carefully
3. Save the current notebook state
4. Consider these approaches:
   - If it's a missing module, use `jupyter_ensure_dependencies()` to install it
   - Try a simpler approach
   - Break the problem into smaller pieces
   - Add more debugging output
   - Restart kernel if necessary using `jupyter_restart_kernel()`
5. Re-execute the cell with the fix
6. If still failing after 2 attempts, try a completely different approach

## Example Workflow

```python
# Step 1: Initialize
jupyter_initialize(working_dir='.')

# Step 2: Create notebook
jupyter_create_notebook('analysis.ipynb')

# Step 3: Add and execute first cell
jupyter_add_cell(
    notebook_path='analysis.ipynb',
    cell_type='code',
    content='import pandas as pd\nprint("Cell 1 executed")',
    execute=True,
    session_id='default'
)

# Step 4: Wait
sleep 5

# Step 5: Add and execute second cell
jupyter_add_cell(
    notebook_path='analysis.ipynb',
    cell_type='code',
    content='df = pd.DataFrame({"a": [1,2,3]})\nprint("Cell 2 executed")',
    execute=True,
    session_id='default'
)

# Step 6: Wait
sleep 5

# Continue pattern for remaining cells...
```

## MCP Tool Usage

This project uses the `jupyter-executor` MCP server. The available tools are:
- `jupyter_initialize` - Set up environment and kernel
- `jupyter_create_notebook` - Create new notebooks
- `jupyter_add_cell` - Add cells to notebooks
- `jupyter_execute_cell` - Execute code in the kernel
- `jupyter_ensure_dependencies` - Install packages via UV
- `jupyter_restart_kernel` - Restart the kernel if needed
- `jupyter_save_notebook` - Save notebook to disk

## Note
These instructions ensure consistent and reliable notebook execution with proper timing between cells, which is essential for operations that may have dependencies or need processing time.