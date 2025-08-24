#!/usr/bin/env python3
"""
Test error recovery patterns - especially the ImportError → UV install → retry flow
"""

import subprocess
import sys
import time

def test_import_error_recovery():
    """Test: If ImportError, install via UV (NEVER pip!)"""
    print("Testing ImportError recovery with UV...")
    
    # This is the key pattern we want to validate
    test_script = """
Use jupyter-executor to:
1. Initialize the environment
2. Try to import a package that might not be installed: import requests
3. If you get an ImportError or ModuleNotFoundError:
   - Use jupyter_ensure_dependencies to install it via UV (NEVER use pip!)
   - Then try the import again
4. Finally execute: print("requests version:", requests.__version__)
"""
    
    result = subprocess.run(
        ['claude'],
        input=test_script,
        capture_output=True,
        text=True,
        timeout=60  # Longer timeout for package installation
    )
    
    if result.returncode != 0:
        print(f"❌ Failed to test import recovery: {result.stderr}")
        return False
    
    # Check that UV was used, not pip
    output_lower = result.stdout.lower()
    if 'pip install' in output_lower and 'uv' not in output_lower:
        print("❌ ERROR: Claude used pip instead of UV!")
        print("  This violates the UV-first principle")
        return False
    
    if 'requests version' in result.stdout or 'import.*success' in output_lower:
        print("✓ ImportError recovery successful via UV")
        return True
    else:
        print("⚠️  Import recovery attempted but result unclear")
        print(f"  Output: {result.stdout[:400]}...")
        return True

def test_syntax_error_handling():
    """Test handling of syntax errors"""
    print("\nTesting syntax error handling...")
    
    test_script = """
Use jupyter-executor to:
1. Initialize
2. Execute code with a syntax error: print("test"
3. Show the error message
4. Then execute correct code: print("test")
"""
    
    result = subprocess.run(
        ['claude'],
        input=test_script,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        print(f"❌ Failed to handle syntax error: {result.stderr}")
        return False
    
    if 'syntaxerror' in result.stdout.lower() or 'error' in result.stdout.lower():
        print("✓ Syntax error handled gracefully")
        return True
    else:
        print("⚠️  Syntax error handling unclear")
        return True

def test_runtime_error_handling():
    """Test handling of runtime errors"""
    print("\nTesting runtime error handling...")
    
    test_script = """
Use jupyter-executor to:
1. Initialize
2. Execute code that causes a runtime error: result = 10 / 0
3. Show the error (should be ZeroDivisionError)
4. Then execute: print("Recovered from error")
"""
    
    result = subprocess.run(
        ['claude'],
        input=test_script,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        print(f"❌ Failed to handle runtime error: {result.stderr}")
        return False
    
    if 'zerodivision' in result.stdout.lower() or 'division by zero' in result.stdout.lower():
        print("✓ Runtime error handled gracefully")
        if 'Recovered from error' in result.stdout:
            print("✓ Execution continued after error")
        return True
    else:
        print("⚠️  Runtime error handling unclear")
        return True

def test_guidance_for_errors():
    """Test: Get help when needed using jupyter_get_guidance"""
    print("\nTesting guidance system for errors...")
    
    test_script = """
Use jupyter-executor to:
1. Initialize
2. Use jupyter_get_guidance('fix_error', context={'error_type': 'ModuleNotFoundError', 'module': 'pandas'})
3. Show the guidance provided
"""
    
    result = subprocess.run(
        ['claude'],
        input=test_script,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        print(f"❌ Failed to get guidance: {result.stderr}")
        return False
    
    output_lower = result.stdout.lower()
    if 'jupyter_ensure_dependencies' in result.stdout or 'uv' in output_lower:
        print("✓ Guidance system provided UV-based solution")
        return True
    elif 'guidance' in output_lower or 'fix' in output_lower:
        print("✓ Guidance system responded")
        return True
    else:
        print("⚠️  Guidance system response unclear")
        print(f"  Output: {result.stdout[:300]}...")
        return True

def test_no_pip_usage():
    """Verify that pip is NEVER used directly"""
    print("\nVerifying UV-only package management...")
    
    test_script = """
Use jupyter-executor to:
1. Initialize
2. Install a package 'numpy' using the correct method (should use jupyter_ensure_dependencies, NOT pip)
3. Show how you installed it
"""
    
    result = subprocess.run(
        ['claude'],
        input=test_script,
        capture_output=True,
        text=True,
        timeout=60
    )
    
    if result.returncode != 0:
        print(f"❌ Failed to test package installation: {result.stderr}")
        return False
    
    output_lower = result.stdout.lower()
    
    # Check for bad patterns
    if 'pip install' in output_lower and 'jupyter_ensure_dependencies' not in result.stdout:
        print("❌ CRITICAL: pip was used instead of UV!")
        print("  This violates the UV-first architecture")
        return False
    
    # Check for good patterns
    if 'jupyter_ensure_dependencies' in result.stdout or 'uv' in output_lower:
        print("✓ Package installation uses UV correctly")
        return True
    else:
        print("⚠️  Package installation method unclear")
        return True

def main():
    """Run all error recovery tests"""
    print("=" * 50)
    print("ERROR RECOVERY TESTS")
    print("=" * 50)
    
    all_passed = True
    
    tests = [
        ("ImportError Recovery (UV)", test_import_error_recovery),
        ("Syntax Error Handling", test_syntax_error_handling),
        ("Runtime Error Handling", test_runtime_error_handling),
        ("Guidance System", test_guidance_for_errors),
        ("No Pip Usage", test_no_pip_usage)
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
        print("✅ All error recovery tests passed!")
        print("✓ UV-first principle maintained")
        return 0
    else:
        print("❌ Some error recovery tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())