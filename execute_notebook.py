#!/usr/bin/env python3
"""
Execute the notebook cells programmatically
"""

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from pathlib import Path
import sys

def execute_notebook():
    notebook_path = Path('torch_attention_demo.ipynb')
    
    if not notebook_path.exists():
        print(f"❌ Notebook not found: {notebook_path}")
        return
    
    print(f"📓 Loading notebook: {notebook_path}")
    
    # Read the notebook
    with open(notebook_path, 'r') as f:
        nb = nbformat.read(f, as_version=4)
    
    # Create preprocessor with claude-jupy kernel
    ep = ExecutePreprocessor(
        timeout=60,
        kernel_name='claude-jupy',
        allow_errors=True
    )
    
    print("🚀 Executing notebook cells...")
    print(f"   Using kernel: {nb.metadata.get('kernelspec', {}).get('name', 'Not set')}")
    
    try:
        # Execute the notebook
        ep.preprocess(nb, {'metadata': {'path': '.'}})
        print("✅ Notebook executed successfully!")
        
        # Save the executed notebook
        output_path = Path('torch_attention_demo_executed.ipynb')
        with open(output_path, 'w') as f:
            nbformat.write(nb, f)
        print(f"💾 Saved executed notebook to: {output_path}")
        
        # Show outputs from first few cells
        print("\n📊 Sample outputs:")
        for i, cell in enumerate(nb.cells[:3]):
            if cell.cell_type == 'code' and hasattr(cell, 'outputs'):
                print(f"\nCell {i+1} outputs:")
                for output in cell.outputs:
                    if hasattr(output, 'text'):
                        print(f"  {output.text}")
                    elif hasattr(output, 'data') and 'text/plain' in output.data:
                        print(f"  {output.data['text/plain']}")
        
    except Exception as e:
        print(f"❌ Error executing notebook: {e}")
        
        # Check for errors in cells
        for i, cell in enumerate(nb.cells):
            if cell.cell_type == 'code' and hasattr(cell, 'outputs'):
                for output in cell.outputs:
                    if hasattr(output, 'ename'):
                        print(f"\n⚠️ Error in cell {i+1}:")
                        print(f"  {output.ename}: {output.evalue}")

if __name__ == "__main__":
    execute_notebook()