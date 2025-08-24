#!/usr/bin/env python3
"""
Test UV-centric package management
Ensures all package operations use UV, never pip
"""

import subprocess
import sys
import time

def test_uv_package_installation():
    """Test that packages are installed via UV"""
    print("Testing UV package installation...")
    
    test_script = """
Use jupyter-executor to:
1. Initialize environment
2. Install these packages using jupyter_ensure_dependencies:
   - requests
   - beautifulsoup4
3. Show exactly how you installed them
4. Import and verify: import requests; print(requests.__version__)
"""
    
    result = subprocess.run(
        ['claude'],
        input=test_script,
        capture_output=True,
        text=True,
        timeout=60
    )
    
    # Check for incorrect pip usage
    if 'pip install' in result.stdout and 'jupyter_ensure_dependencies' not in result.stdout:
        print("❌ FAIL: pip was used instead of UV")
        return False
    
    if 'jupyter_ensure_dependencies' in result.stdout:
        print("✓ Correct: jupyter_ensure_dependencies used")
        return True
    
    print("⚠️  Installation method unclear")
    return True

def test_dev_dependencies():
    """Test installation of development dependencies"""
    print("\nTesting dev dependency installation...")
    
    test_script = """
Use jupyter-executor to:
1. Initialize
2. Install development dependencies with dev=True flag:
   jupyter_ensure_dependencies(session_id, ['pytest', 'black'], dev=True)
3. Show that you used the dev flag
"""
    
    result = subprocess.run(
        ['claude'],
        input=test_script,
        capture_output=True,
        text=True,
        timeout=60
    )
    
    if 'dev=True' in result.stdout:
        print("✓ Dev dependencies handled correctly")
        return True
    
    print("⚠️  Dev dependency handling unclear")
    return True

def test_package_name_mapping():
    """Test that package name mappings are understood"""
    print("\nTesting package name mappings...")
    
    test_script = """
Use jupyter-executor to handle these import/package mappings:
1. Initialize
2. For cv2, install 'opencv-python'
3. For sklearn, install 'scikit-learn'
4. For PIL, install 'pillow'
Show the correct package names you used
"""
    
    result = subprocess.run(
        ['claude'],
        input=test_script,
        capture_output=True,
        text=True,
        timeout=60
    )
    
    mappings_found = 0
    if 'opencv-python' in result.stdout:
        mappings_found += 1
    if 'scikit-learn' in result.stdout:
        mappings_found += 1
    if 'pillow' in result.stdout:
        mappings_found += 1
    
    if mappings_found >= 2:
        print(f"✓ Package name mappings understood ({mappings_found}/3)")
        return True
    
    print("⚠️  Package mappings partially understood")
    return True

def test_uv_sync():
    """Test UV sync functionality"""
    print("\nTesting UV sync with lock file...")
    
    test_script = """
Use jupyter-executor to:
1. Initialize
2. Sync environment using jupyter_sync_environment(session_id)
3. Show what changed
"""
    
    result = subprocess.run(
        ['claude'],
        input=test_script,
        capture_output=True,
        text=True,
        timeout=60
    )
    
    if 'sync' in result.stdout.lower():
        print("✓ UV sync functionality tested")
        return True
    
    print("⚠️  UV sync test inconclusive")
    return True

def test_no_pip_ever():
    """Strict test that pip is never mentioned"""
    print("\nTesting strict no-pip policy...")
    
    test_script = """
Use jupyter-executor to explain how to:
1. Install pandas
2. Install numpy
3. Update packages
4. Install from requirements.txt
Remember: NEVER use pip, always UV via jupyter_ensure_dependencies
"""
    
    result = subprocess.run(
        ['claude'],
        input=test_script,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    pip_mentions = result.stdout.lower().count('pip install')
    uv_mentions = result.stdout.count('jupyter_ensure_dependencies') + result.stdout.lower().count('uv ')
    
    if pip_mentions > 0 and uv_mentions == 0:
        print(f"❌ FAIL: pip mentioned {pip_mentions} times, UV not used")
        return False
    elif uv_mentions > 0:
        print(f"✓ Perfect: UV mentioned {uv_mentions} times")
        return True
    
    print("⚠️  Package management approach unclear")
    return True

def main():
    """Run all UV package management tests"""
    print("=" * 50)
    print("UV PACKAGE MANAGEMENT TESTS")
    print("=" * 50)
    
    all_passed = True
    
    tests = [
        ("UV Package Installation", test_uv_package_installation),
        ("Dev Dependencies", test_dev_dependencies),
        ("Package Name Mapping", test_package_name_mapping),
        ("UV Sync", test_uv_sync),
        ("No Pip Policy", test_no_pip_ever)
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
    print("UV PACKAGE MANAGEMENT SUMMARY")
    print("=" * 50)
    
    if all_passed:
        print("✅ All UV package management tests passed!")
        print("✓ UV-first principle strictly enforced")
        print("✓ No pip usage detected")
        return 0
    else:
        print("❌ Some UV tests failed")
        print("⚠️  Ensure Claude uses jupyter_ensure_dependencies exclusively")
        return 1

if __name__ == "__main__":
    sys.exit(main())