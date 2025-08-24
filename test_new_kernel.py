#!/usr/bin/env python3
"""
Test the new kernel manager approach
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from ml_jupyter_mcp.kernel import get_kernel_manager
import nbformat

def test_kernel_manager():
    print("🧪 Testing New Kernel Manager")
    print("=" * 50)
    
    # Get the kernel manager
    km = get_kernel_manager()
    
    # Start kernel
    print("\n1. Starting kernel...")
    result = km.start_kernel()
    print(f"   Status: {result['status']}")
    if 'connection_file' in result:
        print(f"   Connection file: {result['connection_file']}")
    
    # Execute some code
    print("\n2. Executing code...")
    code = """
import torch
print(f"PyTorch version: {torch.__version__}")
x = torch.tensor([1, 2, 3])
print(f"Tensor: {x}")
"""
    
    result = km.execute_code(code)
    print(f"   Status: {result['status']}")
    print(f"   Has error: {result.get('has_error', False)}")
    
    if result['outputs']:
        print("\n   Outputs:")
        for output in result['outputs']:
            if output['type'] == 'stream':
                print(f"   {output['text']}", end='')
            elif output['type'] == 'error':
                print(f"   ERROR: {output['ename']}: {output['evalue']}")
    
    # Get kernel info
    print("\n3. Kernel info:")
    info = km.get_kernel_info()
    print(f"   Status: {info['status']}")
    print(f"   Execution count: {info.get('execution_count', 0)}")
    
    # Now create a notebook that uses this kernel
    print("\n4. Creating notebook with kernel association...")
    nb = nbformat.v4.new_notebook()
    
    # Set the kernelspec to claude-jupy
    nb.metadata = {
        'kernelspec': {
            'display_name': 'Claude Jupy Environment',
            'language': 'python',
            'name': 'claude-jupy'
        },
        'language_info': {
            'name': 'python',
            'version': '3.11.0'
        }
    }
    
    # Add a test cell
    nb.cells = [
        nbformat.v4.new_markdown_cell("# Test Notebook with New Kernel System"),
        nbformat.v4.new_code_cell("import torch\nprint(f'PyTorch: {torch.__version__}')")
    ]
    
    # Save notebook
    notebook_path = Path('test_new_kernel.ipynb')
    with open(notebook_path, 'w') as f:
        nbformat.write(nb, f)
    
    print(f"   ✅ Created notebook: {notebook_path}")
    print(f"   Kernel: {nb.metadata['kernelspec']['name']}")
    
    # Shutdown kernel
    print("\n5. Shutting down kernel...")
    result = km.shutdown_kernel()
    print(f"   Status: {result['status']}")
    print(f"   Message: {result.get('message', '')}")
    
    print("\n" + "=" * 50)
    print("✅ Test complete!")
    print("\nThe notebook should now work properly in Jupyter")
    print("because we're using the standard Jupyter kernel system.")

if __name__ == "__main__":
    test_kernel_manager()