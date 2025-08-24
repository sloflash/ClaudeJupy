#!/usr/bin/env python3
"""
ML Jupyter MCP Server - UV-centric Jupyter kernel execution for Claude
Main server that registers all tools and starts the FastMCP server
"""

from fastmcp import FastMCP
import sys
from pathlib import Path

# Add src to path for imports
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

def create_server():
    """Create and configure the MCP server with all tools"""
    # Create the MCP server
    mcp = FastMCP("jupyter-executor")
    
    # Import and register all tool modules
    from .tools import execution, environment, notebook, debugging, guidance
    
    # Register each tool group
    execution.register(mcp)
    environment.register(mcp)
    notebook.register(mcp)
    debugging.register(mcp)
    guidance.register(mcp)
    
    # Add backward compatibility tools
    register_legacy_tools(mcp)
    
    return mcp

def register_legacy_tools(mcp):
    """Register legacy tools for backward compatibility"""
    
    @mcp.tool()
    def execute_code(code: str) -> str:
        """
        [LEGACY] Execute Python code in a persistent Jupyter kernel.
        
        CLAUDE: Consider using jupyter_initialize() then jupyter_execute_cell() instead.
        
        Args:
            code: Python code to execute
        
        Returns:
            Execution output as string
        """
        from .daemon import DaemonClient
        
        client = DaemonClient()
        
        # Ensure daemon is running
        port = client.start_daemon_if_needed()
        
        # Execute code
        result = client.execute_code(code)
        
        if result and result['status'] == 'success':
            output_lines = []
            
            for output in result['outputs']:
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
            
            return ''.join(output_lines) if output_lines else "Code executed successfully (no output)"
        else:
            return "Failed to execute code"
    
    @mcp.tool()
    def add_notebook_cell(notebook_path: str, cell_type: str, source: str) -> str:
        """
        [LEGACY] Add a cell to a Jupyter notebook and optionally execute it.
        
        CLAUDE: Consider using jupyter_add_cell() from the notebook tools instead.
        
        Args:
            notebook_path: Path to the notebook file
            cell_type: Type of cell - 'code' or 'markdown'
            source: Content of the cell
        
        Returns:
            Status message
        """
        from .tools.notebook import jupyter_add_cell
        
        # Use new tool with session
        result = jupyter_add_cell(
            notebook_path=notebook_path,
            cell_type=cell_type,
            content=source,
            position=None,
            execute=False,
            session_id=None
        )
        
        if result['status'] == 'success':
            return f"Successfully added {cell_type} cell to {notebook_path}"
        else:
            return f"Failed to add cell: {result.get('error', 'Unknown error')}"
    
    @mcp.tool()
    def kernel_status() -> str:
        """
        [LEGACY] Check the status of the Jupyter kernel daemon.
        
        CLAUDE: Consider using jupyter_kernel_status() instead.
        
        Returns:
            Kernel status message
        """
        from .daemon import DaemonClient
        
        client = DaemonClient()
        status = client.get_status()
        
        if status.get('kernel_running'):
            return f"Kernel daemon is running on port {status.get('port', 'unknown')}"
        else:
            return "Kernel daemon is not running"
    
    @mcp.tool()
    def shutdown_kernel() -> str:
        """
        [LEGACY] Shutdown the Jupyter kernel daemon.
        
        CLAUDE: Consider using jupyter_shutdown_kernel() instead.
        
        Returns:
            Shutdown status message
        """
        from .daemon import DaemonClient
        
        client = DaemonClient()
        client.shutdown()
        return "Kernel daemon shutdown requested"

def main():
    """Main entry point for the MCP server"""
    mcp = create_server()
    
    # Print startup message
    print("🚀 Jupyter MCP Server starting...")
    print("📦 UV-centric environment management enabled")
    print("🤖 Claude guidance system active")
    print("✨ Enhanced error handling and debugging tools available")
    print("")
    print("CLAUDE TIP: Always start with jupyter_initialize() to set up everything automatically!")
    print("")
    
    # Run the server
    mcp.run()

if __name__ == "__main__":
    main()