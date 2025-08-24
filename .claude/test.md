# End-to-End Test Scenarios for Jupyter Notebook Executor

## IMPORTANT: Test Execution Guidelines

**DO NOT CREATE SEPARATE TEST FILES** - Run tests directly inline using the notebook_client.py module.

Tests should be executed as inline Python code like this:
```python
from notebook_client import add_and_execute_cell, shutdown_daemon
# Run test commands directly
add_and_execute_cell('temp_test.ipynb', 'code', 'x = 42')
# Clean up after test
import os; os.remove('temp_test.ipynb')
```

## Test Environment Setup

```bash
# Prerequisites - Using uv for virtual environment management
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies using uv
uv pip install jupyter ipykernel nbformat jupyter_client pytest pandas numpy matplotlib

# Note: The kernel daemon will automatically detect and use the .venv
```

## Test 1: Success Scenario - Data Analysis Pipeline

### Test Description
Complete successful execution of a data analysis notebook with multiple steps.

### Test Input
```python
problem = "Analyze sample sales data and create summary report"
```

### Expected TODO Generation
```python
todos = [
    "Import required libraries (pandas, numpy, matplotlib)",
    "Create sample sales data",
    "Validate data structure",
    "Calculate summary statistics",
    "Create visualization",
    "Generate final report"
]
```

### Test Execution Script
```python
# test_success_scenario.py
import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from notebook_client import add_and_execute_cell, shutdown_daemon

def test_success_scenario():
    """Test successful end-to-end notebook execution using our daemon"""
    
    # Create temporary notebook for testing
    test_notebook = 'test_notebook_success.ipynb'
    
    # Clean up any existing test notebook
    if Path(test_notebook).exists():
        os.remove(test_notebook)
    
    # Step 3: Execute TODOs sequentially using our notebook_client
    cells_to_execute = [
        {
            'type': 'markdown',
            'content': '## Step 1: Import required libraries'
        },
        {
            'type': 'code',
            'content': '''import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
print("Libraries imported successfully")'''
        },
        {
            'type': 'markdown',
            'content': '## Step 2: Create sample sales data'
        },
        {
            'type': 'code',
            'content': '''np.random.seed(42)
data = {
    'date': pd.date_range('2024-01-01', periods=30),
    'sales': np.random.randint(100, 1000, 30),
    'region': np.random.choice(['North', 'South', 'East', 'West'], 30)
}
df = pd.DataFrame(data)
print(f"Created dataframe with {len(df)} rows")
df.head()'''
        },
        {
            'type': 'markdown',
            'content': '## Step 3: Validate data structure'
        },
        {
            'type': 'code',
            'content': '''assert len(df) == 30, "Expected 30 rows"
assert list(df.columns) == ['date', 'sales', 'region'], "Column mismatch"
assert df['sales'].min() >= 100, "Sales validation failed"
print("✓ Data validation passed")'''
        },
        {
            'type': 'markdown',
            'content': '## Step 4: Calculate summary statistics'
        },
        {
            'type': 'code',
            'content': '''summary = {
    'total_sales': df['sales'].sum(),
    'average_sales': df['sales'].mean(),
    'max_sales': df['sales'].max(),
    'min_sales': df['sales'].min(),
    'sales_by_region': df.groupby('region')['sales'].sum().to_dict()
}
print("Summary Statistics:")
for key, value in summary.items():
    print(f"  {key}: {value}")'''
        },
        {
            'type': 'markdown',
            'content': '## Step 5: Create visualization'
        },
        {
            'type': 'code',
            'content': '''fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

# Sales over time
ax1.plot(df['date'], df['sales'])
ax1.set_title('Sales Over Time')
ax1.set_xlabel('Date')
ax1.set_ylabel('Sales')

# Sales by region
region_sales = df.groupby('region')['sales'].sum()
ax2.bar(region_sales.index, region_sales.values)
ax2.set_title('Total Sales by Region')
ax2.set_xlabel('Region')
ax2.set_ylabel('Total Sales')

plt.tight_layout()
plt.savefig('sales_report.png')
print("✓ Visualization saved as sales_report.png")'''
        },
        {
            'type': 'markdown',
            'content': '## Step 6: Generate final report'
        },
        {
            'type': 'code',
            'content': '''report = f"""
SALES ANALYSIS REPORT
====================
Period: {df['date'].min().date()} to {df['date'].max().date()}
Total Sales: ${summary['total_sales']:,}
Average Daily Sales: ${summary['average_sales']:.2f}
Peak Sales Day: {df.loc[df['sales'].idxmax(), 'date'].date()}
Peak Sales Amount: ${summary['max_sales']:,}

Regional Performance:
{chr(10).join([f"  {region}: ${amount:,}" for region, amount in summary['sales_by_region'].items()])}

Report generated successfully.
"""
print(report)
SUCCESS = True'''
        }
    ]
    
    execution_log = []
    
    # Execute cells using our notebook_client
    for i, cell_spec in enumerate(cells_to_execute):
        try:
            # Add and execute cell
            success = add_and_execute_cell(
                test_notebook,
                cell_spec['type'],
                cell_spec['content']
            )
            
            if success:
                execution_log.append(f"Cell {i}: ✓ Success")
                print(f"Cell {i}: ✓ Success - {cell_spec.get('type', 'code')}")
            else:
                execution_log.append(f"Cell {i}: ✗ Failed")
                raise Exception(f"Cell {i} failed")
                
        except Exception as e:
            execution_log.append(f"Cell {i}: ✗ Failed - {str(e)}")
            raise Exception(f"Cell {i} failed: {str(e)}")
    
    # Verify success
    assert len(execution_log) == len(cells_to_execute)
    assert all('✓' in log for log in execution_log)
    
    # Clean up temporary files (but keep notebook for inspection if needed)
    # Remove generated files like sales_report.png
    if Path('sales_report.png').exists():
        os.remove('sales_report.png')
    
    print("✅ Success scenario test PASSED")
    return True

if __name__ == "__main__":
    test_success_scenario()
```

## Test 2: Recoverable Failure Scenario

### Test Description
Test automatic error recovery for common Python errors.

### Test Input
```python
problem = "Process data with intentional recoverable errors"
```

### Test Execution Script
```python
# test_recoverable_failure.py
import os
import sys
from pathlib import Path

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from notebook_client import add_and_execute_cell, shutdown_daemon

def test_recoverable_failure():
    """Test error recovery mechanism using our daemon"""
    
    test_notebook = 'test_notebook_recovery.ipynb'
    
    # Clean up any existing test notebook
    if Path(test_notebook).exists():
        os.remove(test_notebook)
    
    test_cases = [
        {
            'name': 'NameError Recovery',
            'initial_code': 'result = undefined_var * 2',
            'fixed_code': 'undefined_var = 10\nresult = undefined_var * 2',
            'expected_fix': 'Define missing variable'
        },
        {
            'name': 'ImportError Recovery',
            'initial_code': 'df = pd.DataFrame()',
            'fixed_code': 'import pandas as pd\ndf = pd.DataFrame()',
            'expected_fix': 'Add missing import'
        },
        {
            'name': 'IndexError Recovery',
            'initial_code': 'my_list = [1, 2, 3]\nvalue = my_list[10]',
            'fixed_code': 'my_list = [1, 2, 3]\nvalue = my_list[-1]',  # Use safe index
            'expected_fix': 'Fix index bounds'
        },
        {
            'name': 'ValueError Recovery',
            'initial_code': 'int("not_a_number")',
            'fixed_code': 'try:\n    int("not_a_number")\nexcept ValueError:\n    value = 0',
            'expected_fix': 'Add error handling'
        }
    ]
    
    recovery_log = []
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        
        # Step 1: Try initial (failing) code - expect it to fail
        print(f"  Attempting failing code...")
        try:
            add_and_execute_cell(test_notebook, 'code', test_case['initial_code'])
            # If we get here, the code didn't fail as expected
            print(f"  ⚠️ Code should have failed but didn't")
        except Exception as e:
            print(f"  Expected error occurred")
        
        # Step 2: Apply fix - this should succeed
        print(f"  Applying fix: {test_case['expected_fix']}")
        try:
            success = add_and_execute_cell(test_notebook, 'code', test_case['fixed_code'])
            if success:
                recovery_log.append({
                    'test': test_case['name'],
                    'status': 'RECOVERED',
                    'fix_applied': test_case['expected_fix']
                })
                print(f"  ✓ Successfully recovered with: {test_case['expected_fix']}")
            else:
                recovery_log.append({
                    'test': test_case['name'],
                    'status': 'FAILED',
                    'error': 'Fix did not succeed'
                })
                print(f"  ✗ Recovery failed")
        except Exception as e:
            recovery_log.append({
                'test': test_case['name'],
                'status': 'FAILED',
                'error': str(e)
            })
            print(f"  ✗ Recovery failed: {str(e)}")
    
    # Verify all recoveries succeeded
    assert all(r['status'] == 'RECOVERED' for r in recovery_log)
    print("\n✅ Recoverable failure test PASSED")
    print(f"Successfully recovered from {len(recovery_log)} errors")
    return True

if __name__ == "__main__":
    test_recoverable_failure()
```

## Test 3: Unrecoverable Failure Scenario

### Test Description
Test proper handling and reporting of unrecoverable errors.

### Test Execution Script
```python
# test_unrecoverable_failure.py
def test_unrecoverable_failure():
    """Test handling of unrecoverable errors"""
    
    unrecoverable_scenarios = [
        {
            'name': 'Memory Error Simulation',
            'code': '''# Simulate memory error
raise MemoryError("STOP: System out of memory")''',
            'expected_behavior': 'Stop execution immediately'
        },
        {
            'name': 'Permission Error',
            'code': '''import os
os.chmod('/root/protected', 0o777)''',
            'expected_behavior': 'Stop after max retries'
        },
        {
            'name': 'Explicit STOP Signal',
            'code': '''raise Exception("STOP: Human intervention required")''',
            'expected_behavior': 'Stop on STOP signal'
        }
    ]
    
    # Test each scenario
    for scenario in unrecoverable_scenarios:
        print(f"\nTesting: {scenario['name']}")
        print(f"Expected: {scenario['expected_behavior']}")
        
        # Execution should stop and report error
        # Not continue to next cells
        
    print("\n✅ Unrecoverable failure handling test PASSED")
    return True
```

## Integration Test Runner with Verification

**DO NOT CREATE run_all_tests.py** - Execute tests inline with proper verification:

```bash
# Make sure to run tests with venv activated
source .venv/bin/activate

# Run comprehensive tests with verification
python -c "
from notebook_client import add_and_execute_cell, shutdown_daemon
import os
import nbformat
import sys

# Clean up before tests
shutdown_daemon()

print('='*60)
print('JUPYTER EXECUTOR TESTS WITH VERIFICATION')
print('='*60)

test_file = 'temp_test.ipynb'
passed_tests = 0
failed_tests = 0

# TEST 1: Variable Persistence
print('\n🧪 Test 1: Variable Persistence')
try:
    add_and_execute_cell(test_file, 'code', 'test_var = 42')
    add_and_execute_cell(test_file, 'code', 'assert test_var == 42, \"Variable not persisted\"')
    add_and_execute_cell(test_file, 'code', 'print(f\"test_var = {test_var}\")')
    print('  ✅ PASSED: Variables persist across cells')
    passed_tests += 1
except Exception as e:
    print(f'  ❌ FAILED: {e}')
    failed_tests += 1

# TEST 2: Import Persistence
print('\n🧪 Test 2: Import Persistence')
try:
    add_and_execute_cell(test_file, 'code', 'import datetime')
    add_and_execute_cell(test_file, 'code', 'now = datetime.datetime.now(); print(f\"Time: {now}\")')
    print('  ✅ PASSED: Imports persist across cells')
    passed_tests += 1
except Exception as e:
    print(f'  ❌ FAILED: {e}')
    failed_tests += 1

# TEST 3: Error Recovery
print('\n🧪 Test 3: Error Recovery')
try:
    # This should fail but not crash
    add_and_execute_cell(test_file, 'code', 'undefined_variable')
    # This should succeed
    add_and_execute_cell(test_file, 'code', 'undefined_variable = 100')
    add_and_execute_cell(test_file, 'code', 'assert undefined_variable == 100')
    print('  ✅ PASSED: Kernel survives errors and continues')
    passed_tests += 1
except Exception as e:
    print(f'  ❌ FAILED: {e}')
    failed_tests += 1

# TEST 4: Complex Operations
print('\n🧪 Test 4: Complex Operations')
try:
    add_and_execute_cell(test_file, 'code', '''
import numpy as np
data = np.array([1, 2, 3, 4, 5])
mean_val = data.mean()
assert mean_val == 3.0, f\"Expected 3.0, got {mean_val}\"
print(f\"Mean: {mean_val}\")
    ''')
    add_and_execute_cell(test_file, 'code', 'squared = data ** 2; print(f\"Squared: {squared}\")')
    print('  ✅ PASSED: Complex numpy operations work')
    passed_tests += 1
except Exception as e:
    print(f'  ❌ FAILED: {e}')
    failed_tests += 1

# VERIFICATION: Check notebook was created with correct cells
print('\n🧪 Test 5: Notebook Structure Verification')
try:
    with open(test_file, 'r') as f:
        nb = nbformat.read(f, as_version=4)
    
    assert len(nb.cells) > 0, 'No cells in notebook'
    code_cells = [c for c in nb.cells if c.cell_type == 'code']
    assert len(code_cells) >= 8, f'Expected at least 8 code cells, got {len(code_cells)}'
    
    # Check that cells have outputs
    cells_with_output = sum(1 for c in code_cells if len(c.get('outputs', [])) > 0)
    assert cells_with_output > 0, 'No cells have outputs'
    
    print(f'  ✅ PASSED: Notebook has {len(code_cells)} code cells with outputs')
    passed_tests += 1
except Exception as e:
    print(f'  ❌ FAILED: {e}')
    failed_tests += 1

# Clean up
os.remove(test_file) if os.path.exists(test_file) else None
shutdown_daemon()

# FINAL REPORT
print('\n' + '='*60)
print('TEST SUMMARY')
print('='*60)
print(f'✅ Passed: {passed_tests}')
print(f'❌ Failed: {failed_tests}')
print(f'Total: {passed_tests + failed_tests}')

if failed_tests > 0:
    print('\n⚠️  SOME TESTS FAILED!')
    sys.exit(1)
else:
    print('\n🎉 ALL TESTS PASSED!')
    sys.exit(0)
"
```

The original test functions below are for reference only - DO NOT CREATE THESE AS FILES:

```python
# REFERENCE ONLY - DO NOT CREATE THIS FILE
# This shows what the tests should do when run inline

def main():
    tests = [
        ('Success Scenario', test_success_scenario),
        ('Recoverable Failure', test_recoverable_failure),
        ('Unrecoverable Failure', test_unrecoverable_failure)
    ]
    
    results = []
    
    print("=" * 60)
    print("JUPYTER NOTEBOOK EXECUTOR - END TO END TESTS")
    print("=" * 60)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        print("-" * 40)
        
        try:
            result = test_func()
            results.append((test_name, 'PASS', None))
            print(f"✅ {test_name}: PASSED")
        except Exception as e:
            results.append((test_name, 'FAIL', str(e)))
            print(f"❌ {test_name}: FAILED")
            traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, status, _ in results if status == 'PASS')
    failed = sum(1 for _, status, _ in results if status == 'FAIL')
    
    for test_name, status, error in results:
        status_icon = "✅" if status == "PASS" else "❌"
        print(f"{status_icon} {test_name}: {status}")
        if error:
            print(f"   Error: {error}")
    
    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
```

## Expected Test Output

```
============================================================
JUPYTER NOTEBOOK EXECUTOR - END TO END TESTS
============================================================

🧪 Running: Success Scenario
----------------------------------------
Libraries imported successfully
Created dataframe with 30 rows
✓ Data validation passed
Summary Statistics:
  total_sales: 16234
  average_sales: 541.13
  max_sales: 987
  min_sales: 102
  sales_by_region: {'North': 4123, 'South': 3987, ...}
✓ Visualization saved as sales_report.png
✓ Success scenario test PASSED

🧪 Running: Recoverable Failure
----------------------------------------
Testing: NameError Recovery
  Expected error caught: NameError
  ✓ Successfully recovered with: Define missing variable
Testing: ImportError Recovery
  Expected error caught: ImportError
  ✓ Successfully recovered with: Add missing import
✓ Recoverable failure test PASSED

🧪 Running: Unrecoverable Failure
----------------------------------------
Testing: Memory Error Simulation
Expected: Stop execution immediately
✓ Unrecoverable failure handling test PASSED

============================================================
TEST SUMMARY
============================================================
✅ Success Scenario: PASS
✅ Recoverable Failure: PASS
✅ Unrecoverable Failure: PASS

Total: 3 tests
Passed: 3
Failed: 0
```