#!/usr/bin/env python3
"""
FastMCP Server for Jupyter notebook execution with persistent kernel
This allows Claude Code to execute Python code in a persistent Jupyter environment
"""

from fastmcp import FastMCP
import sys
from pathlib import Path
import json

# Add the script directory to Python path so imports work
script_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(script_dir))

from notebook_client import start_daemon_if_needed, send_to_daemon, add_and_execute_cell

# Create the MCP server
mcp = FastMCP("jupyter-executor")

@mcp.tool()
def execute_code(code: str) -> str:
    """
    Execute Python code in a persistent Jupyter kernel.
    The kernel maintains state across executions within the same session.
    Uses the project's uv venv if available.
    """
    try:
        # Ensure daemon is running
        port = start_daemon_if_needed()
        
        # Execute code
        response = send_to_daemon({'action': 'execute', 'code': code}, port)
        
        if response and response['status'] == 'success':
            output_lines = []
            
            for output in response['outputs']:
                if output['type'] == 'stream':
                    output_lines.append(output['text'])
                elif output['type'] == 'execute_result':
                    if 'text/plain' in output['data']:
                        output_lines.append(output['data']['text/plain'])
                elif output['type'] == 'error':
                    output_lines.append(f"Error: {output['ename']}: {output['evalue']}")
                    for line in output.get('traceback', []):
                        output_lines.append(line)
                elif output['type'] == 'display_data':
                    if 'text/plain' in output['data']:
                        output_lines.append(output['data']['text/plain'])
            
            result = ''.join(output_lines) if output_lines else "Code executed successfully (no output)"
        else:
            result = "Failed to execute code"
        
        return result
        
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def add_notebook_cell(notebook_path: str, cell_type: str, source: str) -> str:
    """
    Add a cell to a Jupyter notebook and optionally execute it.
    
    Args:
        notebook_path: Path to the notebook file (will be created if doesn't exist)
        cell_type: Type of cell - 'code' or 'markdown'
        source: Content of the cell
    """
    try:
        success = add_and_execute_cell(notebook_path, cell_type, source)
        
        if success:
            return f"Successfully added {cell_type} cell to {notebook_path}"
        else:
            return f"Failed to add cell to {notebook_path}"
            
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def kernel_status() -> str:
    """
    Check the status of the Jupyter kernel daemon.
    """
    try:
        lock_file = script_dir / '.kernel_daemon.lock'
        
        if not lock_file.exists():
            return "Kernel daemon is not running"
        
        with open(lock_file, 'r') as f:
            info = json.load(f)
        
        # Try to ping the daemon
        response = send_to_daemon({'action': 'ping'}, info['port'])
        
        if response and response.get('status') == 'alive':
            return f"Kernel daemon is running on port {info['port']}"
        else:
            return "Kernel daemon lock file exists but daemon is not responding"
            
    except Exception as e:
        return f"Error checking status: {str(e)}"

@mcp.tool()
def shutdown_kernel() -> str:
    """
    Shutdown the Jupyter kernel daemon.
    """
    try:
        from notebook_client import shutdown_daemon
        shutdown_daemon()
        return "Kernel daemon shutdown requested"
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    """Main entry point for the MCP server"""
    mcp.run()

if __name__ == "__main__":
    main()