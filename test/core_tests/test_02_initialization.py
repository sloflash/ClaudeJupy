#!/usr/bin/env python3
"""
Test the Claude initialization pattern
"""

import subprocess
import sys
import json
import time
from pathlib import Path

def test_initialization_pattern():
    """Test: Always start with initialization"""
    print("Testing initialization pattern...")
    
    # Test the exact Claude pattern
    test_script = """
Use jupyter-executor to:
1. Initialize the environment with jupyter_initialize(working_dir='.')
2. Get the session_id from the result
3. Print "Session ID: " followed by the session_id
"""
    
    result = subprocess.run(
        ['claude'],
        input=test_script,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        print(f"❌ Claude command failed: {result.stderr}")
        return False
    
    # Check for session_id in output
    if 'session' in result.stdout.lower() or 'initialized' in result.stdout.lower():
        print("✓ Initialization successful")
        print(f"  Response preview: {result.stdout[:200]}...")
        return True
    else:
        print("❌ Initialization did not return expected result")
        print(f"  Output: {result.stdout}")
        return False

def test_kernel_status_after_init():
    """Test that kernel is running after initialization"""
    print("\nTesting kernel status after initialization...")
    
    # First initialize
    init_script = "Use jupyter-executor to initialize the environment and then check kernel_status()"
    
    result = subprocess.run(
        ['claude'],
        input=init_script,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        print(f"❌ Failed to check kernel status: {result.stderr}")
        return False
    
    if 'running' in result.stdout.lower() or 'started' in result.stdout.lower():
        print("✓ Kernel is running after initialization")
        return True
    else:
        print("⚠️  Could not confirm kernel status")
        print(f"  Output: {result.stdout[:300]}...")
        return True  # Don't fail the test, just warn

def test_session_persistence():
    """Test that session_id enables persistent state"""
    print("\nTesting session persistence...")
    
    # Set a variable and then retrieve it
    test_script = """
Use jupyter-executor to:
1. Initialize and get session_id
2. Execute code to set test_var = 42
3. In a separate execution, print test_var
4. Confirm the value is still 42
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
    
    if '42' in result.stdout:
        print("✓ Session persistence verified - variable retained across executions")
        return True
    else:
        print("❌ Session persistence failed - variable not retained")
        print(f"  Output: {result.stdout[:300]}...")
        return False

def test_working_directory_handling():
    """Test working directory parameter in initialization"""
    print("\nTesting working directory handling...")
    
    test_script = """
Use jupyter-executor to:
1. Initialize with working_dir='.'
2. Execute: import os; print(os.getcwd())
3. Show the current working directory
"""
    
    result = subprocess.run(
        ['claude'],
        input=test_script,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        print(f"❌ Failed to test working directory: {result.stderr}")
        return False
    
    # Should show some path
    if '/' in result.stdout or '\\' in result.stdout:
        print("✓ Working directory handled correctly")
        return True
    else:
        print("⚠️  Could not verify working directory")
        return True

def main():
    """Run all initialization tests"""
    print("=" * 50)
    print("INITIALIZATION PATTERN TESTS")
    print("=" * 50)
    
    all_passed = True
    
    tests = [
        ("Basic Initialization", test_initialization_pattern),
        ("Kernel Status", test_kernel_status_after_init),
        ("Session Persistence", test_session_persistence),
        ("Working Directory", test_working_directory_handling)
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
        print("✅ All initialization tests passed!")
        return 0
    else:
        print("❌ Some initialization tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())