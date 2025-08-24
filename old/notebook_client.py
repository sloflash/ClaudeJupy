#!/usr/bin/env python3
"""
Client for interacting with the kernel daemon to add and execute notebook cells
"""

import nbformat
import json
import socket
import sys
import subprocess
import time
from pathlib import Path

def start_daemon_if_needed():
    """Start the daemon if it's not running"""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    lock_file = script_dir / '.kernel_daemon.lock'
    
    if lock_file.exists():
        try:
            with open(lock_file, 'r') as f:
                info = json.load(f)
            
            # Try to ping the daemon
            try:
                response = send_to_daemon({'action': 'ping'}, info['port'])
                if response and response.get('status') == 'alive':
                    print("✅ Daemon is already running")
                    return info['port']
            except:
                pass
        except:
            pass
    
    # Start daemon in background with absolute path
    print("Starting kernel daemon...")
    daemon_path = script_dir / 'kernel_daemon.py'
    subprocess.Popen([sys.executable, str(daemon_path)], 
                     cwd=str(script_dir),
                     stdout=subprocess.DEVNULL, 
                     stderr=subprocess.DEVNULL)
    
    # Wait for daemon to start
    for _ in range(10):
        time.sleep(0.5)
        if lock_file.exists():
            try:
                with open(lock_file, 'r') as f:
                    info = json.load(f)
                return info['port']
            except:
                pass
    
    raise RuntimeError("Failed to start daemon")

def send_to_daemon(request, port=9999):
    """Send request to daemon and get response"""
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', port))
        
        # Send request
        message = json.dumps(request).encode() + b'\n\n'
        client_socket.send(message)
        
        # Receive response
        data = b''
        while True:
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            data += chunk
            if b'\n\n' in data:
                break
        
        client_socket.close()
        return json.loads(data.decode().strip())
    except Exception as e:
        print(f"Error communicating with daemon: {e}")
        return None

def convert_outputs(outputs):
    """Convert daemon outputs to nbformat outputs"""
    nb_outputs = []
    for output in outputs:
        if output['type'] == 'stream':
            nb_outputs.append(nbformat.v4.new_output(
                'stream',
                name=output['name'],
                text=output['text']
            ))
        elif output['type'] == 'execute_result':
            nb_outputs.append(nbformat.v4.new_output(
                'execute_result',
                data=output['data'],
                execution_count=output['execution_count']
            ))
        elif output['type'] == 'error':
            nb_outputs.append(nbformat.v4.new_output(
                'error',
                ename=output['ename'],
                evalue=output['evalue'],
                traceback=output['traceback']
            ))
        elif output['type'] == 'display_data':
            nb_outputs.append(nbformat.v4.new_output(
                'display_data',
                data=output['data']
            ))
    return nb_outputs

def add_and_execute_cell(notebook_path, cell_type, source):
    """Add a cell to notebook and execute it using the daemon"""
    
    # Ensure daemon is running
    port = start_daemon_if_needed()
    
    # Read or create notebook
    notebook_path = Path(notebook_path)
    is_new_notebook = not notebook_path.exists()
    
    if notebook_path.exists():
        with open(notebook_path, 'r') as f:
            nb = nbformat.read(f, as_version=4)
    else:
        nb = nbformat.v4.new_notebook()
        
        # Add package installation cell as first cell for new notebooks
        setup_code = """# Setup cell - Ensure Jupyter kernel packages are installed
# This cell prepares the environment for Jupyter notebook execution

import subprocess
import sys
import os
from pathlib import Path

print("🔍 Detecting environment...")

# Check if we're in a uv venv
venv_path = os.environ.get('VIRTUAL_ENV')
if venv_path:
    print(f"✅ Using virtual environment: {venv_path}")
    
    # For uv venv, use uv pip to install packages
    packages = ['jupyter', 'ipykernel', 'nbformat', 'jupyter_client']
    
    for package in packages:
        try:
            __import__(package)
            print(f"  ✓ {package} already installed")
        except ImportError:
            print(f"  📦 Installing {package} with uv pip...")
            try:
                # Try uv pip first (preferred for uv environments)
                subprocess.check_call(["uv", "pip", "install", package], 
                                    capture_output=True, text=True)
                print(f"  ✓ {package} installed via uv")
            except:
                # Fallback to regular pip
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"  ✓ {package} installed via pip")
else:
    print("⚠️  No virtual environment detected")
    print("💡 Recommended: Create a uv venv first with:")
    print("    uv venv .venv")
    print("    source .venv/bin/activate")
    
    # Still try to install packages
    packages = ['jupyter', 'ipykernel', 'nbformat', 'jupyter_client']
    for package in packages:
        try:
            __import__(package)
            print(f"  ✓ {package} already installed globally")
        except ImportError:
            print(f"  📦 Installing {package} globally...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", package])
            print(f"  ✓ {package} installed")

print("\\n✅ Jupyter kernel ready!")
print("🔄 Kernel persists across cell executions")
print("📝 Notebook remains open for continuous editing")
print("💾 All variables and imports are preserved between cells")"""
        
        # Execute setup code via daemon
        setup_response = send_to_daemon({'action': 'execute', 'code': setup_code}, port)
        
        setup_cell = nbformat.v4.new_code_cell(setup_code)
        setup_cell.execution_count = 1
        
        if setup_response and setup_response['status'] == 'success':
            setup_cell.outputs = convert_outputs(setup_response['outputs'])
            print("✅ Added setup cell to new notebook")
        
        nb.cells.append(setup_cell)
    
    # Create new cell
    if cell_type == 'code':
        # Execute code via daemon
        response = send_to_daemon({'action': 'execute', 'code': source}, port)
        
        if response and response['status'] == 'success':
            outputs = convert_outputs(response['outputs'])
            
            # Create cell with outputs
            new_cell = nbformat.v4.new_code_cell(source)
            # Correct execution count (accounting for any existing code cells)
            new_cell.execution_count = len([c for c in nb.cells if c.cell_type == 'code']) + 1
            new_cell.outputs = outputs
            
            # Print output for user feedback
            for output in response['outputs']:
                if output['type'] == 'stream':
                    print(output['text'], end='')
                elif output['type'] == 'error':
                    print(f"❌ Error: {output['ename']}: {output['evalue']}")
                elif output['type'] == 'execute_result':
                    if 'text/plain' in output['data']:
                        print(output['data']['text/plain'])
        else:
            print("❌ Failed to execute code")
            new_cell = nbformat.v4.new_code_cell(source)
    else:
        new_cell = nbformat.v4.new_markdown_cell(source)
    
    nb.cells.append(new_cell)
    
    # Save notebook
    with open(notebook_path, 'w') as f:
        nbformat.write(nb, f)
    
    print(f"✅ Added {cell_type} cell to {notebook_path}")
    return True

def shutdown_daemon():
    """Shutdown the daemon"""
    script_dir = Path(__file__).parent.absolute()
    lock_file = script_dir / '.kernel_daemon.lock'
    
    if not lock_file.exists():
        print("No daemon running")
        return
    
    try:
        with open(lock_file, 'r') as f:
            info = json.load(f)
        
        response = send_to_daemon({'action': 'shutdown'}, info['port'])
        if response:
            print("✅ Daemon shutdown requested")
        else:
            print("❌ Failed to shutdown daemon")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python notebook_client.py <notebook_path> <cell_type> <source_code>")
        print("  python notebook_client.py --shutdown")
        sys.exit(1)
    
    if sys.argv[1] == '--shutdown':
        shutdown_daemon()
    else:
        if len(sys.argv) < 4:
            print("Error: Missing arguments")
            sys.exit(1)
        
        notebook = sys.argv[1]
        cell_type = sys.argv[2]
        # Join all remaining arguments as the source code
        source = ' '.join(sys.argv[3:])
        # Replace literal \n with actual newlines
        source = source.replace('\\n', '\n')
        
        add_and_execute_cell(notebook, cell_type, source)