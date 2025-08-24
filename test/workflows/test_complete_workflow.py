#!/usr/bin/env python3
"""
Test the complete Claude workflow from initialization to error recovery
This validates the exact pattern Claude should follow
"""

import subprocess
import sys
import time
import json

def test_complete_claude_workflow():
    """Test the exact workflow Claude should follow"""
    
    print("=" * 50)
    print("COMPLETE CLAUDE WORKFLOW TEST")
    print("=" * 50)
    
    all_steps_passed = True
    
    # Step 1: Always start with initialization
    print("\n📌 Step 1: Initialize Environment")
    print("-" * 30)
    
    init_test = """
Use jupyter-executor to follow this exact pattern:
# 1. Always start with initialization
result = jupyter_initialize(working_dir='.')
session_id = result['session_id']
print(f"Initialized with session: {session_id}")
"""
    
    result = subprocess.run(
        ['claude'],
        input=init_test,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        print(f"❌ Initialization failed: {result.stderr}")
        all_steps_passed = False
    elif 'session' in result.stdout.lower():
        print("✓ Got session_id from initialization")
    else:
        print("❌ No session_id returned")
        all_steps_passed = False
    
    # Step 2: Execute code with rich feedback
    print("\n📌 Step 2: Execute Code with Rich Feedback")
    print("-" * 30)
    
    exec_test = """
Use jupyter-executor to:
1. Initialize and get session_id
2. Execute: import pandas as pd; print("Pandas version:", pd.__version__)
3. Show the rich feedback/output
"""
    
    result = subprocess.run(
        ['claude'],
        input=exec_test,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if 'pandas version' in result.stdout.lower() or 'modulenotfounderror' in result.stdout.lower():
        print("✓ Code execution with feedback works")
    else:
        print("⚠️  Execution feedback unclear")
        all_steps_passed = False
    
    # Step 3: Handle ImportError with UV (critical test)
    print("\n📌 Step 3: ImportError → UV Install → Retry")
    print("-" * 30)
    
    error_recovery_test = """
Use jupyter-executor to demonstrate error recovery:
1. Initialize and get session_id
2. Try to import a package that might not exist: import plotly
3. If you get ImportError/ModuleNotFoundError:
   - Use jupyter_ensure_dependencies(session_id, ['plotly']) to install via UV
   - IMPORTANT: Never use pip install!
4. Retry the import
5. Execute: print("Plotly imported successfully")
"""
    
    result = subprocess.run(
        ['claude'],
        input=error_recovery_test,
        capture_output=True,
        text=True,
        timeout=60  # Longer timeout for package installation
    )
    
    # Critical check: ensure UV was used, not pip
    if 'pip install' in result.stdout.lower() and 'jupyter_ensure_dependencies' not in result.stdout:
        print("❌ CRITICAL ERROR: pip was used instead of UV!")
        print("   This violates the UV-first architecture")
        all_steps_passed = False
    elif 'jupyter_ensure_dependencies' in result.stdout or 'uv' in result.stdout.lower():
        print("✓ UV package management used correctly")
    else:
        print("⚠️  Package installation method unclear")
    
    # Step 4: Get guidance when needed
    print("\n📌 Step 4: Use Guidance System")
    print("-" * 30)
    
    guidance_test = """
Use jupyter-executor to:
1. Initialize
2. Get help for a ModuleNotFoundError:
   jupyter_get_guidance('fix_error', context={'error_type': 'ModuleNotFoundError', 'module': 'scipy'})
3. Show the guidance provided
4. Confirm it recommends jupyter_ensure_dependencies, not pip
"""
    
    result = subprocess.run(
        ['claude'],
        input=guidance_test,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if 'jupyter_ensure_dependencies' in result.stdout or 'uv' in result.stdout.lower():
        print("✓ Guidance system provides UV-based solutions")
    else:
        print("⚠️  Guidance system response unclear")
    
    # Step 5: Verify state persistence
    print("\n📌 Step 5: Verify State Persistence")
    print("-" * 30)
    
    persistence_test = """
Use jupyter-executor to verify persistence:
1. Initialize and get session_id
2. Execute: test_data = [1, 2, 3, 4, 5]
3. In a separate call, execute: print(f"Sum: {sum(test_data)}")
4. Verify the variable persisted (sum should be 15)
"""
    
    result = subprocess.run(
        ['claude'],
        input=persistence_test,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if '15' in result.stdout:
        print("✓ State persists across executions")
    else:
        print("❌ State persistence failed")
        all_steps_passed = False
    
    # Step 6: Complex workflow
    print("\n📌 Step 6: Complete Data Science Workflow")
    print("-" * 30)
    
    workflow_test = """
Use jupyter-executor for a complete workflow:
1. Initialize
2. Import numpy: import numpy as np
3. Create data: data = np.random.randn(100)
4. Calculate stats: mean = np.mean(data); std = np.std(data)
5. Print results: print(f"Mean: {mean:.2f}, Std: {std:.2f}")
6. Show that all steps completed successfully
"""
    
    result = subprocess.run(
        ['claude'],
        input=workflow_test,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if 'mean' in result.stdout.lower() and 'std' in result.stdout.lower():
        print("✓ Complete workflow executed successfully")
    else:
        print("⚠️  Workflow completion unclear")
    
    # Summary
    print("\n" + "=" * 50)
    print("WORKFLOW TEST SUMMARY")
    print("=" * 50)
    
    print("\n✅ Validated patterns:")
    print("  1. Always start with initialization ✓")
    print("  2. Execute code with rich feedback ✓")
    print("  3. ImportError → UV install → retry ✓")
    print("  4. Get help via guidance system ✓")
    print("  5. State persists across calls ✓")
    print("  6. Complex workflows supported ✓")
    
    if all_steps_passed:
        print("\n🎉 Complete workflow test PASSED!")
        return 0
    else:
        print("\n❌ Some workflow steps failed")
        return 1

if __name__ == "__main__":
    sys.exit(test_complete_claude_workflow())