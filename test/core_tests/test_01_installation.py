#!/usr/bin/env python3
"""
Test MCP Installation and Registration
"""

import subprocess
import sys
import json
from pathlib import Path

def test_mcp_registration():
    """Test that MCP server is properly registered with Claude"""
    print("Testing MCP registration...")
    
    # Need to run from project root to see the MCP registration
    project_root = Path(__file__).parent.parent.parent
    
    # Check if jupyter-executor is registered
    result = subprocess.run(
        ['claude', 'mcp', 'list'],
        capture_output=True,
        text=True,
        cwd=str(project_root)
    )
    
    if result.returncode != 0:
        print(f"❌ Failed to run 'claude mcp list': {result.stderr}")
        return False
    
    if 'jupyter-executor' not in result.stdout:
        print("❌ jupyter-executor not found in MCP list")
        print(f"Output: {result.stdout}")
        return False
    
    print("✓ MCP server is registered")
    
    # Test basic MCP invocation
    print("\nTesting basic MCP invocation...")
    test_command = "Use jupyter-executor to calculate 2+2 and show the result"
    
    result = subprocess.run(
        ['claude'],
        input=test_command,
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(project_root)
    )
    
    if result.returncode != 0:
        print(f"❌ Claude command failed: {result.stderr}")
        return False
    
    # Check if we got a reasonable response
    if '4' in result.stdout or 'four' in result.stdout.lower():
        print("✓ Basic calculation worked")
    else:
        print("⚠️  Unexpected response (but command succeeded)")
        print(f"Response: {result.stdout[:200]}...")
    
    return True

def test_project_structure():
    """Test that the project structure is correct"""
    print("\nTesting project structure...")
    
    project_root = Path(__file__).parent.parent.parent
    
    # Check for key files
    required_files = [
        'pyproject.toml',
        'README.md'
    ]
    
    # Check for either old or new structure
    has_old_structure = (project_root / 'mcp_jupyter_server_fast.py').exists()
    has_new_structure = (project_root / 'src' / 'ml_jupyter_mcp').exists()
    
    if not (has_old_structure or has_new_structure):
        print("❌ Neither old nor new MCP server structure found")
        return False
    
    if has_new_structure:
        print("✓ Using new modular structure (src/ml_jupyter_mcp/)")
    else:
        print("✓ Using legacy structure (mcp_jupyter_server_fast.py)")
    
    for file in required_files:
        file_path = project_root / file
        if not file_path.exists():
            print(f"❌ Missing required file: {file}")
            return False
        print(f"✓ Found {file}")
    
    # Check pyproject.toml has correct configuration
    with open(project_root / 'pyproject.toml', 'r') as f:
        content = f.read()
        if 'ml-jupyter-mcp' in content:
            print("✓ pyproject.toml configured correctly")
        else:
            print("⚠️  pyproject.toml may need updates")
    
    return True

def test_dependencies():
    """Test that required dependencies are available"""
    print("\nTesting dependencies...")
    
    required_packages = [
        'fastmcp',
        'jupyter',
        'ipykernel',
        'nbformat',
        'jupyter_client'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package} is installed")
        except ImportError:
            missing.append(package)
            print(f"❌ {package} is not installed")
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("Install with: uv pip install " + ' '.join(missing))
        return False
    
    return True

def main():
    """Run all installation tests"""
    print("=" * 50)
    print("MCP INSTALLATION TESTS")
    print("=" * 50)
    
    all_passed = True
    
    # Run tests
    tests = [
        ("MCP Registration", test_mcp_registration),
        ("Project Structure", test_project_structure),
        ("Dependencies", test_dependencies)
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
    
    # Summary
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All installation tests passed!")
        return 0
    else:
        print("❌ Some installation tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())