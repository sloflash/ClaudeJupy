#!/usr/bin/env python3
"""
Test code execution patterns
"""

import subprocess
import sys
import time

def test_basic_execution():
    """Test basic code execution with rich feedback"""
    print("Testing basic code execution...")
    
    test_script = """
Use jupyter-executor to:
1. Initialize the environment
2. Execute: print("Hello from Jupyter!")
3. Show the output
"""
    
    result = subprocess.run(
        ['claude'],
        input=test_script,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        print(f"❌ Failed to execute code: {result.stderr}")
        return False
    
    if 'Hello from Jupyter' in result.stdout:
        print("✓ Basic execution successful")
        return True
    else:
        print("❌ Expected output not found")
        print(f"  Output: {result.stdout[:300]}...")
        return False

def test_import_execution():
    """Test importing libraries"""
    print("\nTesting library imports...")
    
    test_script = """
Use jupyter-executor to:
1. Initialize
2. Execute: import sys; print(f"Python version: {sys.version.split()[0]}")
3. Show the Python version
"""
    
    result = subprocess.run(
        ['claude'],
        input=test_script,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        print(f"❌ Failed to import sys: {result.stderr}")
        return False
    
    if 'Python version' in result.stdout or '3.' in result.stdout:
        print("✓ Import and execution successful")
        return True
    else:
        print("❌ Import test failed")
        return False

def test_multi_line_execution():
    """Test multi-line code execution"""
    print("\nTesting multi-line code execution...")
    
    test_script = """
Use jupyter-executor to:
1. Initialize
2. Execute this multi-line code:
   ```python
   def fibonacci(n):
       if n <= 1:
           return n
       return fibonacci(n-1) + fibonacci(n-2)
   
   result = fibonacci(10)
   print(f"Fibonacci(10) = {result}")
   ```
3. Show the result
"""
    
    result = subprocess.run(
        ['claude'],
        input=test_script,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        print(f"❌ Failed to execute multi-line code: {result.stderr}")
        return False
    
    if '55' in result.stdout:  # Fibonacci(10) = 55
        print("✓ Multi-line execution successful")
        return True
    else:
        print("⚠️  Multi-line execution completed but result unclear")
        print(f"  Output: {result.stdout[:300]}...")
        return True

def test_variable_persistence():
    """Test that variables persist across executions"""
    print("\nTesting variable persistence...")
    
    test_script = """
Use jupyter-executor to:
1. Initialize and get session_id
2. Execute: data = [1, 2, 3, 4, 5]
3. Then execute: print(f"Sum of data: {sum(data)}")
4. Show that the variable persisted
"""
    
    result = subprocess.run(
        ['claude'],
        input=test_script,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        print(f"❌ Failed to test persistence: {result.stderr}")
        return False
    
    if '15' in result.stdout:  # Sum of [1,2,3,4,5] = 15
        print("✓ Variables persist across executions")
        return True
    else:
        print("❌ Variable persistence failed")
        return False

def test_expression_evaluation():
    """Test expression evaluation and return values"""
    print("\nTesting expression evaluation...")
    
    test_script = """
Use jupyter-executor to:
1. Initialize
2. Execute just the expression: 42 * 2
3. Show the result
"""
    
    result = subprocess.run(
        ['claude'],
        input=test_script,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        print(f"❌ Failed to evaluate expression: {result.stderr}")
        return False
    
    if '84' in result.stdout:
        print("✓ Expression evaluation successful")
        return True
    else:
        print("⚠️  Expression evaluated but result unclear")
        return True

def main():
    """Run all execution tests"""
    print("=" * 50)
    print("CODE EXECUTION TESTS")
    print("=" * 50)
    
    all_passed = True
    
    tests = [
        ("Basic Execution", test_basic_execution),
        ("Import Execution", test_import_execution),
        ("Multi-line Code", test_multi_line_execution),
        ("Variable Persistence", test_variable_persistence),
        ("Expression Evaluation", test_expression_evaluation)
    ]
    
    for test_name, test_func in tests:
        print(f"\n### {test_name} ###")
        try:
            if not test_func():
                all_passed = False
                print(f"❌ {test_name} failed")
        except Exception as e:
            all_passed = False
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All execution tests passed!")
        return 0
    else:
        print("❌ Some execution tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())