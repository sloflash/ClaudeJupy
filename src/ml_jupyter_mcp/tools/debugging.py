"""
Debugging and Inspection Tools - Inspect variables, debug errors, and profile code
"""

from typing import Dict, Any, List, Optional

def register(mcp):
    """Register debugging tools with the MCP server"""
    
    @mcp.tool()
    def jupyter_inspect_namespace(session_id: str, filter_pattern: Optional[str] = None) -> Dict[str, Any]:
        """
        Inspect variables in the current kernel namespace.
        
        CLAUDE: Use to see what variables are defined and their types/values.
        
        Args:
            session_id: Session ID
            filter_pattern: Optional regex pattern to filter variable names
        
        Returns:
            Detailed information about variables in namespace
        """
        from ..daemon import DaemonClient
        from ..handlers import ResponseFormatter
        import re
        
        client = DaemonClient()
        formatter = ResponseFormatter()
        
        # Get namespace from daemon
        namespace = client.inspect_namespace()
        
        # Apply filter if provided
        if filter_pattern:
            try:
                pattern = re.compile(filter_pattern)
                namespace = {k: v for k, v in namespace.items() if pattern.match(k)}
            except re.error:
                return {
                    'status': 'error',
                    'error': f"Invalid regex pattern: {filter_pattern}"
                }
        
        # Format response
        result = formatter.format_namespace_response(namespace)
        
        # Add Claude tips based on namespace content
        tips = []
        if 'df' in namespace or 'data' in namespace:
            tips.append("DataFrames detected - use .describe() or .info() to explore")
        if 'model' in namespace:
            tips.append("Model object found - check if it's fitted before predictions")
        if len(namespace) == 0:
            tips.append("Namespace is empty - execute some code to define variables")
        
        result['claude_tips'] = tips
        return result
    
    @mcp.tool()
    def jupyter_inspect_variable(session_id: str, variable_name: str, detailed: bool = True) -> Dict[str, Any]:
        """
        Get detailed information about a specific variable.
        
        CLAUDE: Use to deeply inspect a variable's value, type, and attributes.
        
        Args:
            session_id: Session ID
            variable_name: Name of variable to inspect
            detailed: Whether to include detailed info (attributes, methods)
        
        Returns:
            Comprehensive variable information
        """
        from ..daemon import DaemonClient
        
        client = DaemonClient()
        
        # Build inspection code
        inspection_code = f"""
import json
import sys
import inspect

var_name = '{variable_name}'
result = {{'name': var_name}}

try:
    var = {variable_name}
    result['exists'] = True
    result['type'] = type(var).__name__
    result['module'] = type(var).__module__
    
    # Get string representation
    try:
        result['value'] = str(var)[:500]  # Limit to 500 chars
    except:
        result['value'] = '<unprintable>'
    
    # Get size/shape info
    if hasattr(var, '__len__'):
        result['length'] = len(var)
    if hasattr(var, 'shape'):
        result['shape'] = str(var.shape)
    if hasattr(var, 'dtype'):
        result['dtype'] = str(var.dtype)
    if hasattr(var, 'columns'):
        result['columns'] = list(var.columns)[:20]  # First 20 columns
    
    # Memory usage
    result['size_bytes'] = sys.getsizeof(var)
    
    if {str(detailed).lower()}:
        # Get attributes
        attrs = []
        for attr in dir(var):
            if not attr.startswith('_'):
                attrs.append(attr)
        result['attributes'] = attrs[:50]  # First 50 attributes
        
        # Get methods
        methods = []
        for name in dir(var):
            if not name.startswith('_') and callable(getattr(var, name)):
                methods.append(name)
        result['methods'] = methods[:30]  # First 30 methods
        
        # Get docstring
        if hasattr(var, '__doc__') and var.__doc__:
            result['docstring'] = var.__doc__[:500]
    
except NameError:
    result['exists'] = False
    result['error'] = f"Variable '{{var_name}}' is not defined"
except Exception as e:
    result['error'] = str(e)

print(json.dumps(result, indent=2))
"""
        
        # Execute inspection
        execution_result = client.execute_code(inspection_code)
        
        # Parse result from output
        for output in execution_result.get('outputs', []):
            if output.get('type') == 'stream' and output.get('name') == 'stdout':
                try:
                    import json
                    var_info = json.loads(output['text'])
                    
                    # Add Claude guidance
                    if var_info.get('type') == 'DataFrame':
                        var_info['claude_suggestions'] = [
                            f"{variable_name}.head() - View first rows",
                            f"{variable_name}.describe() - Statistical summary",
                            f"{variable_name}.info() - Data types and memory"
                        ]
                    elif var_info.get('type') in ['list', 'tuple', 'set']:
                        var_info['claude_suggestions'] = [
                            f"len({variable_name}) - Get length",
                            f"{variable_name}[:5] - View first 5 items"
                        ]
                    
                    return var_info
                except:
                    pass
        
        return {
            'status': 'error',
            'error': 'Could not inspect variable',
            'claude_tip': f"Check if '{variable_name}' is defined"
        }
    
    @mcp.tool()
    def jupyter_list_variables(session_id: str, var_type: Optional[str] = None) -> Dict[str, Any]:
        """
        List all variables in namespace, optionally filtered by type.
        
        CLAUDE: Quick way to see all defined variables.
        
        Args:
            session_id: Session ID
            var_type: Optional type filter (e.g., "DataFrame", "list", "function")
        
        Returns:
            List of variables with basic info
        """
        from ..daemon import DaemonClient
        
        client = DaemonClient()
        
        # Get namespace
        namespace = client.inspect_namespace()
        
        # Filter by type if specified
        if var_type:
            filtered = {}
            for name, info in namespace.items():
                if info.get('type', '').lower() == var_type.lower():
                    filtered[name] = info
            namespace = filtered
        
        # Format as list
        variables = []
        for name, info in namespace.items():
            var_summary = {
                'name': name,
                'type': info.get('type', 'unknown')
            }
            
            # Add size info if available
            if 'length' in info:
                var_summary['length'] = info['length']
            if 'shape' in info:
                var_summary['shape'] = info['shape']
            
            variables.append(var_summary)
        
        result = {
            'total_variables': len(variables),
            'variables': variables
        }
        
        if var_type:
            result['filter'] = f"Type = {var_type}"
        
        # Add tips
        if len(variables) == 0:
            result['claude_tip'] = "No variables found. Execute some code first."
        else:
            result['claude_tip'] = f"Found {len(variables)} variables. Use jupyter_inspect_variable() for details."
        
        return result
    
    @mcp.tool()
    def jupyter_debug_last_error(session_id: str) -> Dict[str, Any]:
        """
        Get detailed debugging information about the last error.
        
        CLAUDE: Use after an error occurs to understand what went wrong.
        
        Args:
            session_id: Session ID
        
        Returns:
            Comprehensive error analysis with fixes
        """
        from ..daemon import DaemonClient
        
        client = DaemonClient()
        
        # Execute code to get last exception info
        debug_code = """
import sys
import traceback
import json

result = {}

if hasattr(sys, 'last_type'):
    result['has_error'] = True
    result['type'] = sys.last_type.__name__
    result['value'] = str(sys.last_value)
    
    # Get traceback
    tb_lines = traceback.format_exception(sys.last_type, sys.last_value, sys.last_traceback)
    result['traceback'] = tb_lines
    
    # Get local variables at error point
    if sys.last_traceback:
        tb = sys.last_traceback
        while tb.tb_next:
            tb = tb.tb_next
        frame = tb.tb_frame
        
        locals_at_error = {}
        for k, v in frame.f_locals.items():
            if not k.startswith('_'):
                try:
                    locals_at_error[k] = {
                        'type': type(v).__name__,
                        'value': str(v)[:100]  # First 100 chars
                    }
                except:
                    locals_at_error[k] = {'type': 'unknown', 'value': '<unprintable>'}
        
        result['locals_at_error'] = locals_at_error
else:
    result['has_error'] = False
    result['message'] = "No error in history"

print(json.dumps(result, indent=2))
"""
        
        execution_result = client.execute_code(debug_code)
        
        # Parse result
        for output in execution_result.get('outputs', []):
            if output.get('type') == 'stream' and output.get('name') == 'stdout':
                try:
                    import json
                    debug_info = json.loads(output['text'])
                    
                    if debug_info.get('has_error'):
                        # Analyze error and add suggestions
                        from ..handlers import ErrorHandler
                        error_handler = ErrorHandler()
                        
                        error_data = {
                            'ename': debug_info.get('type'),
                            'evalue': debug_info.get('value'),
                            'traceback': debug_info.get('traceback', [])
                        }
                        
                        analysis = error_handler.parse_error(error_data)
                        debug_info['analysis'] = analysis
                        debug_info['claude_guidance'] = analysis.get('claude_guidance', {})
                    
                    return debug_info
                except:
                    pass
        
        return {
            'status': 'error',
            'message': 'Could not retrieve error information',
            'claude_tip': 'Execute code that produces an error first'
        }
    
    @mcp.tool()
    def jupyter_profile_code(session_id: str, code: str, sort_by: str = "cumulative") -> Dict[str, Any]:
        """
        Profile code execution to find performance bottlenecks.
        
        CLAUDE: Use to analyze code performance and find slow parts.
        
        Args:
            session_id: Session ID
            code: Code to profile
            sort_by: How to sort results ("cumulative", "time", "calls")
        
        Returns:
            Profiling results with timing information
        """
        from ..daemon import DaemonClient
        
        client = DaemonClient()
        
        # Wrap code in profiler
        profile_code = f"""
import cProfile
import pstats
import io
from contextlib import redirect_stdout

# Create profiler
profiler = cProfile.Profile()

# Profile the code
profiler.enable()
try:
    {code}
finally:
    profiler.disable()

# Get stats
s = io.StringIO()
ps = pstats.Stats(profiler, stream=s).sort_stats('{sort_by}')
ps.print_stats(20)  # Top 20 functions

print("=== PROFILING RESULTS ===")
print(s.getvalue())
"""
        
        # Execute profiled code
        result = client.execute_code(profile_code)
        
        # Extract profiling output
        profiling_output = ""
        for output in result.get('outputs', []):
            if output.get('type') == 'stream':
                profiling_output += output.get('text', '')
        
        return {
            'profiling_results': profiling_output,
            'sort_by': sort_by,
            'claude_tip': "Look for functions with high cumulative time or many calls"
        }