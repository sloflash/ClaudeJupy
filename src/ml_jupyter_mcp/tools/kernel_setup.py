"""
Kernel setup utilities for ensuring proper Jupyter kernel registration
"""

import subprocess
import json
from pathlib import Path
import sys

def ensure_kernel_registered():
    """Ensure the claude-jupy kernel is registered with Jupyter"""
    
    # Check if kernel already exists
    try:
        result = subprocess.run(['jupyter', 'kernelspec', 'list'], 
                              capture_output=True, text=True)
        if 'claude-jupy' in result.stdout:
            return True  # Already registered
    except:
        pass
    
    # Find the project venv
    venv_path = Path.cwd() / '.venv'
    if not venv_path.exists():
        # Try parent directories
        for parent in Path.cwd().parents:
            potential_venv = parent / '.venv'
            if potential_venv.exists():
                venv_path = potential_venv
                break
    
    if not venv_path.exists():
        print("Warning: No .venv found, cannot register kernel")
        return False
    
    # Create kernel spec
    python_path = venv_path / 'bin' / 'python'
    if not python_path.exists():
        python_path = venv_path / 'Scripts' / 'python.exe'  # Windows
    
    kernel_spec = {
        "argv": [
            str(python_path),
            "-Xfrozen_modules=off",
            "-m",
            "ipykernel_launcher",
            "-f",
            "{connection_file}"
        ],
        "display_name": "Claude Jupy Environment",
        "language": "python",
        "metadata": {
            "debugger": True
        }
    }
    
    # Install kernel spec
    try:
        # Create temp directory for kernel spec
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            kernel_json_path = Path(tmpdir) / 'kernel.json'
            with open(kernel_json_path, 'w') as f:
                json.dump(kernel_spec, f, indent=2)
            
            # Install the kernel spec
            subprocess.run([
                sys.executable, '-m', 'jupyter', 'kernelspec', 'install',
                tmpdir,
                '--name', 'claude-jupy',
                '--user'
            ], check=True)
            
            print("✅ Registered claude-jupy kernel with Jupyter")
            return True
            
    except Exception as e:
        print(f"❌ Failed to register kernel: {e}")
        return False