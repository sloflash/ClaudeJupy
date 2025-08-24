"""
Environment Detector - Detects and analyzes Python environments
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

class EnvironmentDetector:
    def __init__(self, working_dir: Path = None):
        self.working_dir = Path(working_dir) if working_dir else Path.cwd()
        
    def detect_all_environments(self) -> Dict[str, Any]:
        """Detect all available Python environments"""
        environments = []
        
        # Check for UV venv
        uv_env = self.detect_uv_venv()
        if uv_env:
            environments.append(uv_env)
        
        # Check for standard venv
        standard_venv = self.detect_standard_venv()
        if standard_venv and standard_venv['path'] != uv_env.get('path'):
            environments.append(standard_venv)
        
        # Check for conda environments
        conda_envs = self.detect_conda_environments()
        environments.extend(conda_envs)
        
        # Check system Python
        system_python = self.detect_system_python()
        if system_python:
            environments.append(system_python)
        
        # Determine recommended environment
        recommended = self.get_recommended_environment(environments)
        
        return {
            'environments': environments,
            'recommended': recommended,
            'current_python': sys.executable,
            'current_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        }
    
    def detect_uv_venv(self) -> Optional[Dict[str, Any]]:
        """Detect UV-managed virtual environment"""
        venv_path = self.working_dir / '.venv'
        
        if not venv_path.exists():
            # Check parent directories
            for parent in self.working_dir.parents:
                potential_venv = parent / '.venv'
                if potential_venv.exists():
                    venv_path = potential_venv
                    break
            else:
                return None
        
        python_path = venv_path / 'bin' / 'python'
        if not python_path.exists():
            python_path = venv_path / 'Scripts' / 'python.exe'
        
        if not python_path.exists():
            return None
        
        # Check if it's UV-managed
        is_uv = (venv_path.parent / 'uv.lock').exists()
        
        # Get Python version
        try:
            result = subprocess.run(
                [str(python_path), '--version'],
                capture_output=True,
                text=True
            )
            version = result.stdout.strip().split()[-1] if result.returncode == 0 else 'unknown'
        except:
            version = 'unknown'
        
        return {
            'type': 'uv' if is_uv else 'venv',
            'path': str(venv_path),
            'python_executable': str(python_path),
            'python_version': version,
            'is_uv_managed': is_uv,
            'priority': 1  # Highest priority
        }
    
    def detect_standard_venv(self) -> Optional[Dict[str, Any]]:
        """Detect standard Python virtual environments"""
        # Common venv names
        venv_names = ['venv', 'env', '.env', 'virtualenv']
        
        for name in venv_names:
            venv_path = self.working_dir / name
            if venv_path.exists() and venv_path.is_dir():
                python_path = venv_path / 'bin' / 'python'
                if not python_path.exists():
                    python_path = venv_path / 'Scripts' / 'python.exe'
                
                if python_path.exists():
                    try:
                        result = subprocess.run(
                            [str(python_path), '--version'],
                            capture_output=True,
                            text=True
                        )
                        version = result.stdout.strip().split()[-1] if result.returncode == 0 else 'unknown'
                    except:
                        version = 'unknown'
                    
                    return {
                        'type': 'venv',
                        'path': str(venv_path),
                        'python_executable': str(python_path),
                        'python_version': version,
                        'is_uv_managed': False,
                        'priority': 2
                    }
        
        return None
    
    def detect_conda_environments(self) -> List[Dict[str, Any]]:
        """Detect conda environments"""
        environments = []
        
        try:
            # Check if conda is available
            result = subprocess.run(
                ['conda', 'env', 'list', '--json'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for env_path in data.get('envs', []):
                    env_name = Path(env_path).name
                    python_path = Path(env_path) / 'bin' / 'python'
                    if not python_path.exists():
                        python_path = Path(env_path) / 'python.exe'
                    
                    if python_path.exists():
                        try:
                            version_result = subprocess.run(
                                [str(python_path), '--version'],
                                capture_output=True,
                                text=True
                            )
                            version = version_result.stdout.strip().split()[-1]
                        except:
                            version = 'unknown'
                        
                        environments.append({
                            'type': 'conda',
                            'name': env_name,
                            'path': env_path,
                            'python_executable': str(python_path),
                            'python_version': version,
                            'is_uv_managed': False,
                            'priority': 3
                        })
        except:
            pass
        
        return environments
    
    def detect_system_python(self) -> Dict[str, Any]:
        """Detect system Python"""
        # Try to find system Python
        python_commands = ['python3', 'python']
        
        for cmd in python_commands:
            try:
                result = subprocess.run(
                    ['which', cmd],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    python_path = result.stdout.strip()
                    
                    # Get version
                    version_result = subprocess.run(
                        [python_path, '--version'],
                        capture_output=True,
                        text=True
                    )
                    version = version_result.stdout.strip().split()[-1]
                    
                    return {
                        'type': 'system',
                        'path': os.path.dirname(python_path),
                        'python_executable': python_path,
                        'python_version': version,
                        'is_uv_managed': False,
                        'priority': 4  # Lowest priority
                    }
            except:
                continue
        
        # Fallback to current Python
        return {
            'type': 'system',
            'path': os.path.dirname(sys.executable),
            'python_executable': sys.executable,
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'is_uv_managed': False,
            'priority': 4
        }
    
    def get_recommended_environment(self, environments: List[Dict[str, Any]]) -> Optional[str]:
        """Determine the recommended environment based on priority"""
        if not environments:
            return None
        
        # Sort by priority (lower number = higher priority)
        sorted_envs = sorted(environments, key=lambda x: x.get('priority', 999))
        
        if sorted_envs:
            recommended = sorted_envs[0]
            if recommended['type'] == 'uv':
                return f"UV-managed venv at {recommended['path']}"
            elif recommended['type'] == 'venv':
                return f"Virtual environment at {recommended['path']}"
            elif recommended['type'] == 'conda':
                return f"Conda environment '{recommended['name']}'"
            else:
                return "System Python (consider creating a virtual environment)"
        
        return None
    
    def check_package_installed(self, package_name: str, python_path: str) -> bool:
        """Check if a package is installed in a specific Python environment"""
        try:
            result = subprocess.run(
                [python_path, '-c', f'import {package_name}'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def get_installed_packages(self, python_path: str) -> List[str]:
        """Get list of installed packages in an environment"""
        try:
            result = subprocess.run(
                [python_path, '-m', 'pip', 'list', '--format=json'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                packages = json.loads(result.stdout)
                return [f"{p['name']}=={p['version']}" for p in packages]
        except:
            pass
        
        return []