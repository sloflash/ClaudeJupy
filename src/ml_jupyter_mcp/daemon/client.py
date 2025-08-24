"""
Client for communicating with the kernel - now using SimpleKernelManager
"""

from typing import Dict, Any
from ..kernel import get_kernel_manager

class DaemonClient:
    """
    Compatibility wrapper that now uses SimpleKernelManager instead of daemon.
    This maintains the same interface for backward compatibility.
    """
    
    def __init__(self):
        # Use the new SimpleKernelManager instead of daemon
        self.kernel_manager = get_kernel_manager()
        
    def start_daemon_if_needed(self) -> int:
        """Start the kernel if it's not running - now using SimpleKernelManager"""
        result = self.kernel_manager.start_kernel()
        if result['status'] in ['started', 'already_running']:
            return 9999  # Return dummy port for compatibility
        else:
            raise Exception(f"Failed to start kernel: {result.get('error', 'Unknown error')}")
    
    def execute_code(self, code: str) -> Dict[str, Any]:
        """Execute code using the kernel manager"""
        # Ensure kernel is started
        self.start_daemon_if_needed()
        
        # Execute code using the new kernel manager
        return self.kernel_manager.execute_code(code)
    
    def inspect_namespace(self) -> Dict[str, Any]:
        """Get namespace information - simplified version"""
        # Execute code to inspect namespace
        code = """
import json
import sys
namespace_info = {}
for name, obj in list(globals().items()):
    if not name.startswith('_'):
        try:
            obj_type = type(obj).__name__
            obj_info = {'type': obj_type}
            
            # Add size info for common types
            if hasattr(obj, '__len__'):
                obj_info['length'] = len(obj)
            if hasattr(obj, 'shape'):
                obj_info['shape'] = str(obj.shape)
            if hasattr(obj, 'dtype'):
                obj_info['dtype'] = str(obj.dtype)
                
            namespace_info[name] = obj_info
        except:
            pass
print(json.dumps(namespace_info))
"""
        result = self.execute_code(code)
        
        # Parse namespace info from output
        for output in result.get('outputs', []):
            if output.get('type') == 'stream' and output.get('name') == 'stdout':
                try:
                    import json
                    return json.loads(output['text'])
                except:
                    pass
        
        return {}
    
    def get_status(self) -> Dict[str, Any]:
        """Get kernel status"""
        return self.kernel_manager.get_kernel_info()
    
    def shutdown(self):
        """Shutdown the kernel"""
        result = self.kernel_manager.shutdown_kernel()
        if result['status'] == 'success':
            print("✅ Kernel shutdown successfully")
        else:
            print(f"❌ {result.get('message', 'Failed to shutdown kernel')}")