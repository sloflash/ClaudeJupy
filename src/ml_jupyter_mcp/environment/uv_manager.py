"""
UV Environment Manager - Core UV operations for Jupyter environments
"""

import subprocess
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

class UVManager:
    def __init__(self, working_dir: Path = None):
        self.working_dir = Path(working_dir) if working_dir else Path.cwd()
        self.venv_path = self.working_dir / '.venv'
        self.uv_lock_path = self.working_dir / 'uv.lock'
        self.pyproject_path = self.working_dir / 'pyproject.toml'
        self.python_version_file = self.working_dir / '.python-version'
        
    def is_uv_available(self) -> bool:
        """Check if UV is installed and available"""
        try:
            result = subprocess.run(
                ['uv', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def detect_python_version(self) -> Optional[str]:
        """Detect required Python version from project files"""
        # Check .python-version file
        if self.python_version_file.exists():
            return self.python_version_file.read_text().strip()
        
        # Check pyproject.toml
        if self.pyproject_path.exists():
            try:
                import tomllib
            except ImportError:
                import tomli as tomllib
                
            with open(self.pyproject_path, 'rb') as f:
                data = tomllib.load(f)
                python_req = data.get('project', {}).get('requires-python', '')
                if python_req:
                    # Extract version from requirement string
                    # e.g., ">=3.11" -> "3.11"
                    import re
                    match = re.search(r'(\d+\.\d+)', python_req)
                    if match:
                        return match.group(1)
        
        # Default to current Python version
        return f"{sys.version_info.major}.{sys.version_info.minor}"
    
    def create_venv(self, python_version: str = None) -> Dict[str, Any]:
        """Create virtual environment using UV"""
        if not self.is_uv_available():
            return {
                'success': False,
                'error': 'UV is not installed',
                'suggestion': 'Install UV with: curl -LsSf https://astral.sh/uv/install.sh | sh'
            }
        
        if python_version is None:
            python_version = self.detect_python_version()
        
        try:
            # Create venv with UV
            cmd = ['uv', 'venv', str(self.venv_path)]
            if python_version:
                cmd.extend(['--python', python_version])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.working_dir)
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'venv_path': str(self.venv_path),
                    'python_version': python_version,
                    'message': f'Created virtual environment at {self.venv_path}'
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr,
                    'suggestion': 'Check Python version availability'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'suggestion': 'Check UV installation and permissions'
            }
    
    def sync_dependencies(self) -> Dict[str, Any]:
        """Sync dependencies from uv.lock"""
        if not self.uv_lock_path.exists():
            return {
                'success': False,
                'error': 'No uv.lock file found',
                'suggestion': 'Run "uv lock" to create lock file'
            }
        
        if not self.venv_path.exists():
            create_result = self.create_venv()
            if not create_result['success']:
                return create_result
        
        try:
            result = subprocess.run(
                ['uv', 'sync'],
                capture_output=True,
                text=True,
                cwd=str(self.working_dir)
            )
            
            if result.returncode == 0:
                # Parse installed packages
                packages = self.list_installed_packages()
                return {
                    'success': True,
                    'message': 'Dependencies synced successfully',
                    'packages_installed': packages
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr,
                    'suggestion': 'Check uv.lock file and network connection'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def add_package(self, package: str, dev: bool = False) -> Dict[str, Any]:
        """Add a package using UV"""
        if not self.is_uv_available():
            return {
                'success': False,
                'error': 'UV is not installed'
            }
        
        try:
            cmd = ['uv', 'add']
            if dev:
                cmd.append('--dev')
            cmd.append(package)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.working_dir)
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': f'Added {package} successfully',
                    'updated_files': ['pyproject.toml', 'uv.lock']
                }
            else:
                # Check if it's an import name vs package name issue
                if 'not found' in result.stderr.lower():
                    suggestion = self.suggest_package_name(package)
                    return {
                        'success': False,
                        'error': result.stderr,
                        'suggestion': suggestion
                    }
                return {
                    'success': False,
                    'error': result.stderr
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def suggest_package_name(self, import_name: str) -> str:
        """Suggest correct package name for common imports"""
        package_map = {
            'cv2': 'opencv-python',
            'sklearn': 'scikit-learn',
            'PIL': 'pillow',
            'yaml': 'pyyaml',
            'dotenv': 'python-dotenv',
            'bs4': 'beautifulsoup4',
            'wx': 'wxpython',
            'OpenSSL': 'pyopenssl',
            'dateutil': 'python-dateutil'
        }
        
        if import_name in package_map:
            return f"Try: uv add {package_map[import_name]}"
        return f"Check the correct package name for '{import_name}' on PyPI"
    
    def list_installed_packages(self) -> List[str]:
        """List installed packages in the virtual environment"""
        if not self.venv_path.exists():
            return []
        
        try:
            pip_path = self.venv_path / 'bin' / 'pip'
            if not pip_path.exists():
                pip_path = self.venv_path / 'Scripts' / 'pip.exe'
            
            result = subprocess.run(
                [str(pip_path), 'list', '--format=json'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                packages = json.loads(result.stdout)
                return [f"{p['name']}=={p['version']}" for p in packages]
        except:
            pass
        
        return []
    
    def validate_setup(self) -> Dict[str, Any]:
        """Validate the UV environment setup"""
        checks = {
            'uv_installed': self.is_uv_available(),
            'venv_exists': self.venv_path.exists(),
            'uv_lock_exists': self.uv_lock_path.exists(),
            'pyproject_exists': self.pyproject_path.exists(),
            'jupyter_installed': False,
            'ipykernel_installed': False
        }
        
        issues = []
        suggestions = []
        
        if not checks['uv_installed']:
            issues.append("UV is not installed")
            suggestions.append("Install UV: curl -LsSf https://astral.sh/uv/install.sh | sh")
        
        if not checks['venv_exists']:
            issues.append("No virtual environment found")
            suggestions.append("Create venv: uv venv")
        else:
            # Check for Jupyter packages
            packages = self.list_installed_packages()
            checks['jupyter_installed'] = any('jupyter' in p for p in packages)
            checks['ipykernel_installed'] = any('ipykernel' in p for p in packages)
            
            if not checks['jupyter_installed']:
                issues.append("Jupyter not installed in venv")
                suggestions.append("Install Jupyter: uv add jupyter")
            
            if not checks['ipykernel_installed']:
                issues.append("IPython kernel not installed")
                suggestions.append("Install kernel: uv add ipykernel")
        
        if not checks['uv_lock_exists'] and checks['pyproject_exists']:
            issues.append("No uv.lock file found")
            suggestions.append("Create lock file: uv lock")
        
        return {
            'checks': checks,
            'is_valid': len(issues) == 0,
            'issues': issues,
            'suggestions': suggestions
        }
    
    def ensure_jupyter_packages(self) -> Dict[str, Any]:
        """Ensure Jupyter and IPython kernel are installed"""
        required = ['jupyter', 'ipykernel', 'nbformat', 'jupyter_client']
        results = []
        
        for package in required:
            packages = self.list_installed_packages()
            if not any(package in p for p in packages):
                result = self.add_package(package)
                results.append({
                    'package': package,
                    'installed': result['success']
                })
        
        return {
            'success': all(r.get('installed', True) for r in results),
            'packages': results
        }
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get comprehensive environment information"""
        info = {
            'working_dir': str(self.working_dir),
            'uv_available': self.is_uv_available(),
            'venv_path': str(self.venv_path) if self.venv_path.exists() else None,
            'python_version': self.detect_python_version(),
            'uv_lock_exists': self.uv_lock_path.exists(),
            'pyproject_exists': self.pyproject_path.exists(),
            'installed_packages': []
        }
        
        if self.venv_path.exists():
            info['installed_packages'] = self.list_installed_packages()
            info['python_executable'] = str(self.venv_path / 'bin' / 'python')
            if not Path(info['python_executable']).exists():
                info['python_executable'] = str(self.venv_path / 'Scripts' / 'python.exe')
        
        return info