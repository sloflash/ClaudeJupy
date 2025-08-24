#!/usr/bin/env python3
"""
MCP Server for Jupyter notebook execution with persistent kernel
This allows Claude Code to execute Python code in a persistent Jupyter environment
"""

import json
import sys
import asyncio
from typing import Any, Dict, List
from pathlib import Path

# MCP SDK imports
try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
except ImportError:
    print("Error: MCP SDK not installed. Run: pip install mcp")
    sys.exit(1)

# Import our notebook client
from notebook_client import start_daemon_if_needed, send_to_daemon

class JupyterMCPServer:
    def __init__(self):
        self.server = Server("jupyter-executor")
        self.setup_tools()
        
    def setup_tools(self):
        """Register MCP tools"""
        
        @self.server.tool()
        async def execute_code(code: str) -> List[TextContent]:
            """
            Execute Python code in a persistent Jupyter kernel.
            The kernel maintains state across executions within the same session.
            Uses the project's uv venv if available.
            
            Args:
                code: Python code to execute
                
            Returns:
                Execution output and results
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
                
                return [TextContent(type="text", text=result)]
                
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        @self.server.tool()
        async def add_notebook_cell(notebook_path: str, cell_type: str, source: str) -> List[TextContent]:
            """
            Add a cell to a Jupyter notebook and optionally execute it.
            
            Args:
                notebook_path: Path to the notebook file (will be created if doesn't exist)
                cell_type: Type of cell - 'code' or 'markdown'
                source: Content of the cell
                
            Returns:
                Status message and any execution output
            """
            try:
                from notebook_client import add_and_execute_cell
                
                success = add_and_execute_cell(notebook_path, cell_type, source)
                
                if success:
                    return [TextContent(type="text", text=f"Successfully added {cell_type} cell to {notebook_path}")]
                else:
                    return [TextContent(type="text", text=f"Failed to add cell to {notebook_path}")]
                    
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        @self.server.tool()
        async def kernel_status() -> List[TextContent]:
            """
            Check the status of the Jupyter kernel daemon.
            
            Returns:
                Kernel status information
            """
            try:
                lock_file = Path('.kernel_daemon.lock')
                
                if not lock_file.exists():
                    return [TextContent(type="text", text="Kernel daemon is not running")]
                
                with open(lock_file, 'r') as f:
                    info = json.load(f)
                
                # Try to ping the daemon
                response = send_to_daemon({'action': 'ping'}, info['port'])
                
                if response and response.get('status') == 'alive':
                    return [TextContent(type="text", text=f"Kernel daemon is running on port {info['port']}")]
                else:
                    return [TextContent(type="text", text="Kernel daemon lock file exists but daemon is not responding")]
                    
            except Exception as e:
                return [TextContent(type="text", text=f"Error checking status: {str(e)}")]
        
        @self.server.tool()
        async def shutdown_kernel() -> List[TextContent]:
            """
            Shutdown the Jupyter kernel daemon.
            
            Returns:
                Shutdown status
            """
            try:
                from notebook_client import shutdown_daemon
                shutdown_daemon()
                return [TextContent(type="text", text="Kernel daemon shutdown requested")]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def run(self):
        """Run the MCP server"""
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

async def main():
    server = JupyterMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())