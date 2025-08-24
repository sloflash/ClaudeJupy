"""
Simple Kernel Manager using Jupyter's native system
No daemon, no custom socket server - just standard Jupyter kernel management
"""

import jupyter_client
from jupyter_client import KernelManager
from pathlib import Path
from typing import Dict, Any, Optional
import json
import os

class SimpleKernelManager:
    """Manages a single Jupyter kernel using the standard Jupyter approach"""
    
    def __init__(self):
        self.kernel_manager: Optional[KernelManager] = None
        self.kernel_client = None
        self.execution_count = 0
        
        # Store kernel info in project directory
        self.kernel_info_file = Path.cwd() / '.mcp_kernel_info.json'
        
    def start_kernel(self) -> Dict[str, Any]:
        """Start a kernel using the claude-jupy kernelspec"""
        
        if self.kernel_manager and self.kernel_manager.is_alive():
            return {
                'status': 'already_running',
                'connection_file': self.kernel_manager.connection_file
            }
        
        try:
            # Use the registered claude-jupy kernelspec
            self.kernel_manager = KernelManager(kernel_name='claude-jupy')
            
            # Start the kernel
            self.kernel_manager.start_kernel()
            
            # Create a client
            self.kernel_client = self.kernel_manager.client()
            self.kernel_client.start_channels()
            self.kernel_client.wait_for_ready(timeout=10)
            
            # Save kernel info for reuse
            kernel_info = {
                'connection_file': self.kernel_manager.connection_file,
                'kernel_id': self.kernel_manager.kernel_id if hasattr(self.kernel_manager, 'kernel_id') else None
            }
            
            with open(self.kernel_info_file, 'w') as f:
                json.dump(kernel_info, f)
            
            return {
                'status': 'started',
                'connection_file': self.kernel_manager.connection_file,
                'message': 'Kernel started successfully'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'message': 'Failed to start kernel'
            }
    
    def execute_code(self, code: str) -> Dict[str, Any]:
        """Execute code in the kernel"""
        
        if not self.kernel_manager or not self.kernel_manager.is_alive():
            # Try to start kernel
            start_result = self.start_kernel()
            if start_result['status'] == 'error':
                return start_result
        
        self.execution_count += 1
        
        # Execute the code
        msg_id = self.kernel_client.execute(code, store_history=True)
        
        # Collect outputs
        outputs = []
        error_info = None
        
        while True:
            try:
                msg = self.kernel_client.get_iopub_msg(timeout=10)
                msg_type = msg['header']['msg_type']
                content = msg['content']
                
                if msg_type == 'stream':
                    outputs.append({
                        'type': 'stream',
                        'name': content['name'],
                        'text': content['text']
                    })
                elif msg_type == 'execute_result':
                    outputs.append({
                        'type': 'execute_result',
                        'data': content['data'],
                        'execution_count': content['execution_count']
                    })
                elif msg_type == 'error':
                    error_info = {
                        'type': 'error',
                        'ename': content['ename'],
                        'evalue': content['evalue'],
                        'traceback': content['traceback']
                    }
                    outputs.append(error_info)
                elif msg_type == 'display_data':
                    outputs.append({
                        'type': 'display_data',
                        'data': content['data']
                    })
                elif msg_type == 'status' and content['execution_state'] == 'idle':
                    break
            except Exception:
                break
        
        return {
            'status': 'success',
            'outputs': outputs,
            'execution_count': self.execution_count,
            'has_error': error_info is not None
        }
    
    def shutdown_kernel(self) -> Dict[str, Any]:
        """Shutdown the kernel"""
        
        if self.kernel_manager and self.kernel_manager.is_alive():
            try:
                self.kernel_manager.shutdown_kernel(now=True)
                
                # Clean up kernel info file
                if self.kernel_info_file.exists():
                    self.kernel_info_file.unlink()
                
                return {
                    'status': 'success',
                    'message': 'Kernel shut down successfully'
                }
            except Exception as e:
                return {
                    'status': 'error',
                    'error': str(e),
                    'message': 'Failed to shutdown kernel'
                }
        else:
            return {
                'status': 'not_running',
                'message': 'No kernel running'
            }
    
    def get_kernel_info(self) -> Dict[str, Any]:
        """Get information about the current kernel"""
        
        if self.kernel_manager and self.kernel_manager.is_alive():
            return {
                'status': 'running',
                'connection_file': self.kernel_manager.connection_file,
                'execution_count': self.execution_count
            }
        else:
            return {
                'status': 'not_running',
                'message': 'No kernel running'
            }

# Global instance for MCP tools to use
_kernel_manager = None

def get_kernel_manager() -> SimpleKernelManager:
    """Get or create the global kernel manager instance"""
    global _kernel_manager
    if _kernel_manager is None:
        _kernel_manager = SimpleKernelManager()
    return _kernel_manager