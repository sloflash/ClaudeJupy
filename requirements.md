# Jupyter Notebook Step-by-Step Execution Tool Requirements

## Overview
This tool enables Claude Code to execute Python code incrementally in Jupyter notebooks, with automatic error recovery and step-by-step validation.

## Core Requirements

### 1. Environment Setup
- **Virtual Environment**: Use existing `uv` virtual environment located in the project
- **Jupyter Integration**: Connect to Jupyter kernel using the uv venv Python interpreter
- **Kernel Management**: Maintain single kernel session per notebook for state persistence

### 2. Notebook Creation
When given a new problem or idea:
- Create a new `.ipynb` notebook file in `notebooks/` directory
- Naming convention: `{timestamp}_{problem_description}.ipynb`
- Initialize with problem statement as markdown cell

### 3. Task Planning
Before implementation:
- Generate a structured TODO list for the problem
- Each TODO represents one notebook cell
- TODOs should be:
  - Atomic (single responsibility per cell)
  - Sequential (dependencies respected)
  - Testable (clear success criteria)

### 4. Step-by-Step Execution

#### 4.1 Cell Implementation
- Implement cells in ascending order (top to bottom)
- Each cell should correspond to one TODO item
- Add markdown documentation before code cells explaining the step

#### 4.2 Execution Flow
```
For each TODO:
  1. Write cell code
  2. Execute cell
  3. Check execution result:
     - If SUCCESS → proceed to next TODO
     - If ERROR (recoverable) → fix and retry (max 3 attempts)
     - If ERROR (unrecoverable) → stop execution and report
```

#### 4.3 Error Handling
**Recoverable Errors:**
- NameError (undefined variable) → define variable
- ImportError → add import statement
- IndexError → adjust indexing logic
- ValueError (with clear message) → fix input validation
- FileNotFoundError → create file or adjust path

**Unrecoverable Errors:**
- System errors (out of memory, permission denied)
- Network errors after 3 retries
- Logical errors requiring human intervention
- Errors explicitly marked as "STOP" in exception message

### 5. State Management
- Preserve kernel state between cells
- Variables defined in earlier cells available in later cells
- Import statements persist throughout notebook

### 6. Output Handling
- Capture and display all cell outputs
- Log execution time for each cell
- Maintain execution history with timestamps

### 7. Success Criteria
A notebook execution is considered successful when:
- All TODOs are completed
- All cells execute without unrecoverable errors
- Final validation cell (if defined) passes

## Technical Implementation

### Required Dependencies
```python
jupyter
ipykernel
nbformat
nbconvert
jupyter_client
```

### File Structure
```
project/
├── requirements.md          # This file
├── test.md                 # Test specifications
├── notebooks/              # Generated notebooks
├── .venv/                  # uv virtual environment
└── jupyter_executor.py     # Main execution script
```

## Constraints

1. **Execution Timeout**: Each cell has max 30 seconds execution time
2. **Memory Limit**: Monitor memory usage, stop if >80% system memory
3. **Retry Limit**: Maximum 3 retries per recoverable error
4. **Notebook Size**: Maximum 100 cells per notebook
5. **Output Size**: Truncate outputs larger than 1MB

## User Commands

Claude Code should respond to these commands:

- `new notebook <problem>` - Create new notebook for problem
- `continue notebook` - Resume from last successful cell
- `fix and retry` - Fix current error and retry execution
- `skip cell` - Mark current cell as skipped and continue
- `show status` - Display current execution progress

## Error Reporting Format

When execution stops, report:
```
❌ Execution stopped at cell {number}
TODO: {todo_description}
Error Type: {error_class}
Error Message: {error_message}
Attempted Fixes: {fix_count}
Suggestion: {suggested_action}
```

## Example Usage

User: "Create a notebook to analyze CSV data and create visualizations"

Claude Code will:
1. Create new notebook: `2024_01_15_csv_analysis.ipynb`
2. Generate TODOs:
   - Import required libraries
   - Load CSV file
   - Explore data structure
   - Clean data
   - Create summary statistics
   - Generate visualizations
   - Save results
3. Implement and execute each cell sequentially
4. Handle any errors encountered
5. Report completion or blocking errors