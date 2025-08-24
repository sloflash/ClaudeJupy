"""
Client for communicating with the kernel daemon
"""

import json
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

class DaemonClient:
    def __init__(self):
        self.script_dir = Path(__file__).parent.parent.parent.absolute()
        self.lock_file = self.script_dir / '.kernel_daemon.lock'
        self.port = None
        
    def start_daemon_if_needed(self) -> int:
        """Start the daemon if it's not running"""
        if self.lock_file.exists():
            try:
                with open(self.lock_file, 'r') as f:
                    info = json.load(f)
                
                # Try to ping the daemon
                try:
                    response = self.send_to_daemon({'action': 'ping'}, info['port'])
                    if response and response.get('status') == 'alive':
                        print("✅ Daemon is already running")
                        self.port = info['port']
                        return info['port']
                except:
                    pass
            except:
                pass
        
        # Start daemon in background
        print("Starting kernel daemon...")
        daemon_path = Path(__file__).parent / 'kernel_daemon.py'
        subprocess.Popen(
            [sys.executable, str(daemon_path)],
            cwd=str(self.script_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Wait for daemon to start
        for _ in range(10):
            time.sleep(0.5)
            if self.lock_file.exists():
                try:
                    with open(self.lock_file, 'r') as f:
                        info = json.load(f)
                    self.port = info['port']
                    return info['port']
                except:
                    pass
        
        raise RuntimeError("Failed to start daemon")
    
    def send_to_daemon(self, request: Dict[str, Any], port: int = None) -> Optional[Dict[str, Any]]:
        """Send request to daemon and get response"""
        if port is None:
            port = self.port or 9999
            
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
    
    def execute_code(self, code: str) -> Dict[str, Any]:
        """Execute code via daemon"""
        port = self.start_daemon_if_needed()
        response = self.send_to_daemon({'action': 'execute', 'code': code}, port)
        
        if response and response.get('status') == 'success':
            return {
                'status': 'success',
                'outputs': response.get('outputs', []),
                'execution_count': response.get('execution_count', 0),
                'has_error': response.get('has_error', False),
                'error_suggestions': response.get('error_suggestions', [])
            }
        else:
            return {
                'status': 'error',
                'message': 'Failed to execute code',
                'outputs': []
            }
    
    def inspect_namespace(self) -> Dict[str, Any]:
        """Get namespace information from daemon"""
        port = self.start_daemon_if_needed()
        response = self.send_to_daemon({'action': 'inspect'}, port)
        
        if response and response.get('status') == 'success':
            return response.get('namespace', {})
        return {}
    
    def get_status(self) -> Dict[str, Any]:
        """Get daemon status"""
        if not self.lock_file.exists():
            return {'status': 'not_running'}
        
        try:
            with open(self.lock_file, 'r') as f:
                info = json.load(f)
            
            response = self.send_to_daemon({'action': 'status'}, info['port'])
            if response:
                return response
        except:
            pass
        
        return {'status': 'error', 'message': 'Could not get daemon status'}
    
    def shutdown(self):
        """Shutdown the daemon"""
        if not self.lock_file.exists():
            print("No daemon running")
            return
        
        try:
            with open(self.lock_file, 'r') as f:
                info = json.load(f)
            
            response = self.send_to_daemon({'action': 'shutdown'}, info['port'])
            if response:
                print("✅ Daemon shutdown requested")
            else:
                print("❌ Failed to shutdown daemon")
        except Exception as e:
            print(f"Error: {e}")