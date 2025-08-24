#!/usr/bin/env python3
"""
Kernel daemon that maintains a persistent Jupyter kernel
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

class KernelDaemon:
    def __init__(self, port=9999):
        self.port = port
        self.kernel_manager = None
        self.kernel_client = None
        self.socket_server = None
        self.running = False
        # Use absolute paths in the script directory
        self.script_dir = Path(__file__).parent.absolute()
        self.lock_file = self.script_dir / '.kernel_daemon.lock'
        self.connection_file = self.script_dir / '.kernel_connection.json'
        
    def start_kernel(self):
        """Start the Jupyter kernel"""
        print("Starting Jupyter kernel...")
        
        # Check for uv venv in current directory or parent directories
        cwd = Path.cwd()
        venv_path = None
        
        # Search for .venv in current and parent directories
        for path in [cwd] + list(cwd.parents):
            potential_venv = path / '.venv'
            if potential_venv.exists():
                venv_path = potential_venv
                break
        
        if venv_path:
            # Use uv venv Python
            python_path = venv_path / 'bin' / 'python'
            if not python_path.exists():
                # Windows path
                python_path = venv_path / 'Scripts' / 'python.exe'
            
            if python_path.exists():
                print(f"Using uv venv Python: {python_path}")
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
                print("Using system Python")
                self.kernel_manager = jupyter_client.KernelManager(kernel_name='python3')
        else:
            print("No venv found, using system Python")
            self.kernel_manager = jupyter_client.KernelManager(kernel_name='python3')
        
        self.kernel_manager.start_kernel()
        self.kernel_client = self.kernel_manager.client()
        self.kernel_client.start_channels()
        self.kernel_client.wait_for_ready()
        
        # Save connection info
        with open(self.connection_file, 'w') as f:
            json.dump({
                'connection_file': self.kernel_manager.connection_file,
                'port': self.port
            }, f)
        
        print(f"✅ Kernel started and ready on port {self.port}")
        
    def execute_code(self, code):
        """Execute code in the kernel and return outputs"""
        msg_id = self.kernel_client.execute(code)
        
        outputs = []
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
                    outputs.append({
                        'type': 'error',
                        'ename': content['ename'],
                        'evalue': content['evalue'],
                        'traceback': content['traceback']
                    })
                elif msg_type == 'display_data':
                    outputs.append({
                        'type': 'display_data',
                        'data': content['data']
                    })
                elif msg_type == 'status' and content['execution_state'] == 'idle':
                    break
            except:
                break
                
        return outputs
    
    def handle_client(self, client_socket):
        """Handle client requests"""
        try:
            # Receive data
            data = b''
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                data += chunk
                if b'\n\n' in data:  # Double newline as message terminator
                    break
            
            request = json.loads(data.decode())
            
            if request['action'] == 'execute':
                outputs = self.execute_code(request['code'])
                response = {'status': 'success', 'outputs': outputs}
            elif request['action'] == 'ping':
                response = {'status': 'alive'}
            elif request['action'] == 'shutdown':
                response = {'status': 'shutting_down'}
                self.running = False
            else:
                response = {'status': 'error', 'message': 'Unknown action'}
            
            # Send response
            client_socket.send(json.dumps(response).encode() + b'\n\n')
            
        except Exception as e:
            error_response = {'status': 'error', 'message': str(e)}
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
        
        # Write lock file with PID
        with open(self.lock_file, 'w') as f:
            json.dump({'pid': os.getpid(), 'port': self.port}, f)
        
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
    script_dir = Path(__file__).parent.absolute()
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