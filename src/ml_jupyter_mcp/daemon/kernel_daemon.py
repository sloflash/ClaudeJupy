#!/usr/bin/env python3
"""
Enhanced Kernel daemon with UV-first approach and rich error handling
"""

import jupyter_client
import json
import socket
import threading
import sys
import os
import signal
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

class KernelDaemon:
    def __init__(self, port: int = 9999):
        self.port = port
        self.kernel_manager = None
        self.kernel_client = None
        self.socket_server = None
        self.running = False
        self.script_dir = Path(__file__).parent.parent.parent.absolute()
        self.lock_file = self.script_dir / '.kernel_daemon.lock'
        self.connection_file = self.script_dir / '.kernel_connection.json'
        self.execution_count = 0
        self.namespace_cache = {}
        
    def detect_uv_environment(self) -> Optional[Path]:
        """Detect UV-managed virtual environment"""
        cwd = Path.cwd()
        
        # Search for .venv in current and parent directories
        for path in [cwd] + list(cwd.parents):
            potential_venv = path / '.venv'
            if potential_venv.exists():
                return potential_venv
        
        return None
        
    def start_kernel(self):
        """Start the Jupyter kernel with UV environment if available"""
        print("Starting Jupyter kernel...")
        
        venv_path = self.detect_uv_environment()
        
        if venv_path:
            # Use UV venv Python
            python_path = venv_path / 'bin' / 'python'
            if not python_path.exists():
                # Windows path
                python_path = venv_path / 'Scripts' / 'python.exe'
            
            if python_path.exists():
                print(f"✅ Using UV venv Python: {python_path}")
                # Set up environment for venv
                kernel_env = os.environ.copy()
                kernel_env['VIRTUAL_ENV'] = str(venv_path)
                kernel_env['PATH'] = f"{venv_path / 'bin'}:{kernel_env.get('PATH', '')}"
                
                # Start kernel with venv Python
                self.kernel_manager = jupyter_client.KernelManager(kernel_name='python3')
                self.kernel_manager.kernel_cmd = [
                    str(python_path), '-m', 'ipykernel_launcher',
                    '-f', '{connection_file}'
                ]
                self.kernel_manager.env = kernel_env
            else:
                print("⚠️ .venv exists but Python not found, using system Python")
                self.kernel_manager = jupyter_client.KernelManager(kernel_name='python3')
        else:
            print("⚠️ No UV environment found, using system Python")
            print("💡 Recommended: Create a UV environment with 'uv venv'")
            self.kernel_manager = jupyter_client.KernelManager(kernel_name='python3')
        
        self.kernel_manager.start_kernel()
        self.kernel_client = self.kernel_manager.client()
        self.kernel_client.start_channels()
        self.kernel_client.wait_for_ready()
        
        # Save connection info
        with open(self.connection_file, 'w') as f:
            json.dump({
                'connection_file': self.kernel_manager.connection_file,
                'port': self.port,
                'venv_path': str(venv_path) if venv_path else None,
                'python_version': sys.version
            }, f)
        
        print(f"✅ Kernel started and ready on port {self.port}")
        
    def execute_code(self, code: str) -> Dict[str, Any]:
        """Execute code in the kernel with enhanced error handling"""
        self.execution_count += 1
        msg_id = self.kernel_client.execute(code)
        
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
            except:
                break
        
        # Add execution metadata
        result = {
            'outputs': outputs,
            'execution_count': self.execution_count,
            'has_error': error_info is not None
        }
        
        # Add error suggestions if error occurred
        if error_info:
            result['error_suggestions'] = self.get_error_suggestions(error_info)
        
        return result
    
    def get_error_suggestions(self, error_info: Dict) -> List[str]:
        """Generate suggestions for common errors"""
        suggestions = []
        ename = error_info['ename']
        evalue = error_info['evalue']
        
        if ename == 'ModuleNotFoundError':
            module_name = evalue.split("'")[1] if "'" in evalue else ""
            if module_name:
                suggestions.append(f"Install missing module with: uv add {module_name}")
                suggestions.append(f"Or if UV not available: pip install {module_name}")
        elif ename == 'ImportError':
            suggestions.append("Check if the module is installed in your environment")
            suggestions.append("Try: uv sync to sync dependencies")
        elif ename == 'FileNotFoundError':
            suggestions.append("Check if the file path is correct")
            suggestions.append("Use absolute paths or verify working directory")
        elif ename == 'NameError':
            suggestions.append("Variable or function not defined")
            suggestions.append("Check for typos or run previous cells first")
        
        return suggestions
    
    def inspect_namespace(self) -> Dict[str, Any]:
        """Inspect current kernel namespace"""
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
        for output in result['outputs']:
            if output['type'] == 'stream' and output['name'] == 'stdout':
                try:
                    return json.loads(output['text'])
                except:
                    pass
        
        return {}
    
    def handle_client(self, client_socket):
        """Handle client requests with enhanced responses"""
        try:
            # Receive data
            data = b''
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                data += chunk
                if b'\n\n' in data:
                    break
            
            request = json.loads(data.decode())
            action = request.get('action')
            
            if action == 'execute':
                result = self.execute_code(request['code'])
                response = {
                    'status': 'success',
                    'outputs': result['outputs'],
                    'execution_count': result['execution_count'],
                    'has_error': result['has_error']
                }
                if 'error_suggestions' in result:
                    response['error_suggestions'] = result['error_suggestions']
                    
            elif action == 'inspect':
                namespace = self.inspect_namespace()
                response = {
                    'status': 'success',
                    'namespace': namespace
                }
                
            elif action == 'ping':
                response = {
                    'status': 'alive',
                    'kernel_active': self.kernel_manager is not None,
                    'execution_count': self.execution_count
                }
                
            elif action == 'shutdown':
                response = {'status': 'shutting_down'}
                self.running = False
                
            elif action == 'status':
                venv_path = self.detect_uv_environment()
                response = {
                    'status': 'success',
                    'kernel_running': self.kernel_manager is not None,
                    'port': self.port,
                    'execution_count': self.execution_count,
                    'environment': {
                        'venv_path': str(venv_path) if venv_path else None,
                        'python_version': sys.version,
                        'using_uv': venv_path is not None
                    }
                }
                
            else:
                response = {'status': 'error', 'message': f'Unknown action: {action}'}
            
            # Send response
            client_socket.send(json.dumps(response).encode() + b'\n\n')
            
        except Exception as e:
            error_response = {
                'status': 'error',
                'message': str(e),
                'type': type(e).__name__
            }
            client_socket.send(json.dumps(error_response).encode() + b'\n\n')
        finally:
            client_socket.close()
    
    def start_server(self):
        """Start the socket server"""
        self.socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_server.bind(('localhost', self.port))
        self.socket_server.listen(5)
        self.running = True
        
        # Write lock file with enhanced info
        with open(self.lock_file, 'w') as f:
            json.dump({
                'pid': os.getpid(),
                'port': self.port,
                'started_at': time.time(),
                'venv_detected': self.detect_uv_environment() is not None
            }, f)
        
        print(f"✅ Daemon listening on port {self.port}")
        
        while self.running:
            try:
                self.socket_server.settimeout(1.0)
                client_socket, addr = self.socket_server.accept()
                # Handle each client in a new thread
                thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                thread.start()
            except socket.timeout:
                continue
            except:
                break
    
    def cleanup(self):
        """Clean up resources"""
        print("Shutting down daemon...")
        self.running = False
        
        if self.kernel_manager:
            self.kernel_manager.shutdown_kernel()
            
        if self.socket_server:
            self.socket_server.close()
            
        if self.lock_file.exists():
            self.lock_file.unlink()
            
        if self.connection_file.exists():
            self.connection_file.unlink()
            
        print("✅ Daemon shut down")
    
    def run(self):
        """Main daemon loop"""
        # Set up signal handlers
        signal.signal(signal.SIGINT, lambda s, f: self.cleanup())
        signal.signal(signal.SIGTERM, lambda s, f: self.cleanup())
        
        try:
            self.start_kernel()
            self.start_server()
        finally:
            self.cleanup()

def is_daemon_running():
    """Check if daemon is already running"""
    script_dir = Path(__file__).parent.parent.parent.absolute()
    lock_file = script_dir / '.kernel_daemon.lock'
    
    if not lock_file.exists():
        return False
    
    try:
        with open(lock_file, 'r') as f:
            info = json.load(f)
        
        # Check if process is still running
        try:
            os.kill(info['pid'], 0)
            return True
        except OSError:
            # Process is dead, clean up lock file
            lock_file.unlink()
            return False
    except:
        return False

if __name__ == '__main__':
    if is_daemon_running():
        print("❌ Daemon is already running")
        sys.exit(1)
    
    daemon = KernelDaemon()
    daemon.run()