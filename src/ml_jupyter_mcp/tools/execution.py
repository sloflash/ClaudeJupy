"""
Code Execution Tools - Execute Python code in persistent Jupyter kernel
"""

from typing import Dict, Any, Optional

def register(mcp):
    """Register execution tools with the MCP server"""
    
    @mcp.tool()
    def jupyter_execute_cell(session_id: str, code: str, timeout: int = 120) -> Dict[str, Any]:
        """
        Execute Python code in the persistent Jupyter kernel.
        
        CLAUDE: Main tool for running Python code. The kernel maintains state across executions.
        
        Args:
            session_id: Session ID from jupyter_initialize()
            code: Python code to execute
            timeout: Execution timeout in seconds
        
        Returns:
            Execution results with outputs, errors, and suggestions
        """
        from ..daemon import DaemonClient
        from ..handlers import ErrorHandler, ResponseFormatter
        
        client = DaemonClient()
        error_handler = ErrorHandler()
        formatter = ResponseFormatter()
        
        # Execute code
        result = client.execute_code(code)
        
        # Process any errors
        if result.get('has_error'):
            for output in result.get('outputs', []):
                if output.get('type') == 'error':
                    error_analysis = error_handler.parse_error(output)
                    result['error_analysis'] = error_analysis
                    result['claude_should'] = error_analysis.get('claude_guidance', {})
                    break
        
        # Format response for Claude
        formatted = formatter.format_execution_response(result)
        
        # Add execution tips
        if result.get('status') == 'success' and not result.get('has_error'):
            formatted['claude_tip'] = "Code executed successfully. Variables are preserved for next execution."
        elif result.get('has_error'):
            formatted['claude_tip'] = "Error occurred. Check error_guidance for fixes."
        
        return formatted
    
    @mcp.tool()
    def jupyter_execute_magic(session_id: str, magic_command: str) -> Dict[str, Any]:
        """
        Execute IPython magic commands.
        
        CLAUDE: Use for special IPython commands like %timeit, %who, %pwd, etc.
        
        Args:
            session_id: Session ID
            magic_command: Magic command (e.g., "%timeit sum(range(100))")
        
        Returns:
            Magic command output
        """
        # Ensure magic command starts with %
        if not magic_command.startswith('%'):
            magic_command = '%' + magic_command
        
        return jupyter_execute_cell(session_id, magic_command)
    
    @mcp.tool()
    def jupyter_run_file(session_id: str, file_path: str) -> Dict[str, Any]:
        """
        Execute a Python file in the kernel.
        
        CLAUDE: Use to run existing Python scripts in the Jupyter environment.
        
        Args:
            session_id: Session ID
            file_path: Path to Python file to execute
        
        Returns:
            Execution results
        """
        from pathlib import Path
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {
                'status': 'error',
                'error': f"File not found: {file_path}",
                'claude_should': f"Check if file exists at {file_path}"
            }
        
        if not file_path.suffix == '.py':
            return {
                'status': 'error',
                'error': "File must be a Python file (.py)",
                'claude_should': "Only Python files can be executed"
            }
        
        # Read file content
        try:
            code = file_path.read_text()
            # Execute with special comment indicating file source
            full_code = f"# Executing file: {file_path}\n{code}"
            return jupyter_execute_cell(session_id, full_code)
        except Exception as e:
            return {
                'status': 'error',
                'error': f"Could not read file: {str(e)}"
            }
    
    @mcp.tool()
    def jupyter_execute_notebook(session_id: str, notebook_path: str, stop_on_error: bool = True) -> Dict[str, Any]:
        """
        Execute all code cells in a notebook sequentially.
        
        CLAUDE: Use to run an entire notebook programmatically.
        
        Args:
            session_id: Session ID
            notebook_path: Path to .ipynb file
            stop_on_error: Whether to stop execution on first error
        
        Returns:
            Execution summary with results from each cell
        """
        import nbformat
        from pathlib import Path
        
        notebook_path = Path(notebook_path)
        
        if not notebook_path.exists():
            return {
                'status': 'error',
                'error': f"Notebook not found: {notebook_path}"
            }
        
        # Read notebook
        try:
            with open(notebook_path, 'r') as f:
                nb = nbformat.read(f, as_version=4)
        except Exception as e:
            return {
                'status': 'error',
                'error': f"Could not read notebook: {str(e)}"
            }
        
        results = {
            'notebook': str(notebook_path),
            'total_cells': len(nb.cells),
            'executed_cells': [],
            'errors': [],
            'stopped_early': False
        }
        
        # Execute each code cell
        for i, cell in enumerate(nb.cells):
            if cell.cell_type != 'code':
                continue
            
            cell_result = jupyter_execute_cell(session_id, cell.source)
            
            results['executed_cells'].append({
                'cell_index': i,
                'status': cell_result.get('status'),
                'has_error': cell_result.get('has_error', False)
            })
            
            if cell_result.get('has_error'):
                results['errors'].append({
                    'cell_index': i,
                    'error': cell_result.get('error_guidance', {})
                })
                
                if stop_on_error:
                    results['stopped_early'] = True
                    results['claude_tip'] = f"Execution stopped at cell {i} due to error"
                    break
        
        results['summary'] = {
            'cells_executed': len(results['executed_cells']),
            'cells_with_errors': len(results['errors']),
            'success': len(results['errors']) == 0
        }
        
        return results