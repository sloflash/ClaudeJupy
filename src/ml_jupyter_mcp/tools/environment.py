"""
Environment Management Tools - UV-first environment operations
"""

from pathlib import Path
from typing import Dict, Any, List, Optional

def register(mcp):
    """Register environment tools with the MCP server"""
    
    @mcp.tool()
    def jupyter_initialize(working_dir: str = ".") -> Dict[str, Any]:
        """
        One-command initialization that sets up everything automatically.
        
        CLAUDE: ALWAYS call this first when starting any Jupyter task!
        
        This tool will:
        1. Detect or create UV environment
        2. Sync dependencies from uv.lock
        3. Install Jupyter packages if missing
        4. Start kernel daemon
        5. Return session_id for subsequent calls
        
        Args:
            working_dir: Project directory (default: current directory)
        
        Returns:
            Complete setup status with session_id
        """
        from ..environment import UVManager, EnvironmentDetector
        from ..daemon import DaemonClient
        from ..handlers import ResponseFormatter
        
        working_path = Path(working_dir).absolute()
        uv_manager = UVManager(working_path)
        detector = EnvironmentDetector(working_path)
        client = DaemonClient()
        formatter = ResponseFormatter()
        
        result = {
            'steps_completed': [],
            'warnings': [],
            'errors': []
        }
        
        # Step 1: Detect environment
        env_info = detector.detect_all_environments()
        result['environment_scan'] = {
            'environments_found': len(env_info['environments']),
            'recommended': env_info['recommended']
        }
        
        # Step 2: Check/create UV environment
        if not uv_manager.venv_path.exists():
            result['steps_completed'].append("No .venv found - creating new environment")
            create_result = uv_manager.create_venv()
            if not create_result['success']:
                result['errors'].append(create_result['error'])
                return result
            result['steps_completed'].append("Created .venv with UV")
        else:
            result['steps_completed'].append("Found existing .venv")
        
        # Step 3: Sync dependencies if uv.lock exists
        if uv_manager.uv_lock_path.exists():
            sync_result = uv_manager.sync_dependencies()
            if sync_result['success']:
                result['steps_completed'].append("Synced dependencies from uv.lock")
            else:
                result['warnings'].append("Could not sync uv.lock: " + sync_result.get('error', ''))
        
        # Step 4: Ensure Jupyter packages
        jupyter_result = uv_manager.ensure_jupyter_packages()
        if jupyter_result['success']:
            result['steps_completed'].append("Jupyter packages installed")
        
        # Step 5: Start kernel daemon
        try:
            port = client.start_daemon_if_needed()
            result['kernel_started'] = True
            result['session_id'] = f"session_{port}"
            result['steps_completed'].append(f"Kernel daemon started on port {port}")
        except Exception as e:
            result['errors'].append(f"Failed to start kernel: {str(e)}")
            return result
        
        # Final status
        result['ready'] = len(result['errors']) == 0
        result['claude_instructions'] = [
            f"Environment is ready! Use session_id '{result.get('session_id')}' for all subsequent calls",
            "You can now execute code with jupyter_execute_cell()"
        ]
        
        return formatter.format_environment_response(result)
    
    @mcp.tool()
    def jupyter_detect_uv_environment(working_dir: str = ".") -> Dict[str, Any]:
        """
        Detect UV project structure and environment status.
        
        CLAUDE: Use this to understand the project's Python environment setup.
        
        Args:
            working_dir: Directory to check
        
        Returns:
            Detailed environment information including UV status
        """
        from ..environment import UVManager, EnvironmentDetector
        from ..handlers import ResponseFormatter
        
        working_path = Path(working_dir).absolute()
        uv_manager = UVManager(working_path)
        detector = EnvironmentDetector(working_path)
        formatter = ResponseFormatter()
        
        # Get comprehensive info
        uv_info = uv_manager.get_environment_info()
        all_envs = detector.detect_all_environments()
        
        result = {
            'uv_available': uv_info['uv_available'],
            'working_dir': str(working_path),
            'python_version': uv_info['python_version'],
            'venv_status': {
                'exists': uv_info['venv_path'] is not None,
                'path': uv_info['venv_path'],
                'needs_creation': uv_info['venv_path'] is None
            },
            'uv_lock': {
                'exists': uv_info['uv_lock_exists'],
                'path': str(working_path / 'uv.lock') if uv_info['uv_lock_exists'] else None
            },
            'pyproject': {
                'exists': uv_info['pyproject_exists'],
                'path': str(working_path / 'pyproject.toml') if uv_info['pyproject_exists'] else None
            },
            'all_environments': all_envs['environments'],
            'recommended_action': 'use_existing' if uv_info['venv_path'] else 'create_new',
            'claude_next_steps': []
        }
        
        # Add Claude-specific guidance
        if not uv_info['venv_path']:
            result['claude_next_steps'] = [
                "Run jupyter_setup_uv_environment() to create .venv",
                "Or run jupyter_initialize() to do everything automatically"
            ]
        elif not uv_info['uv_lock_exists']:
            result['claude_next_steps'] = [
                "No uv.lock found - dependencies may not be reproducible",
                "Consider running 'uv lock' to create lock file"
            ]
        else:
            result['claude_next_steps'] = [
                "Environment looks good!",
                "Run jupyter_initialize() to start working"
            ]
        
        return result
    
    @mcp.tool()
    def jupyter_setup_uv_environment(working_dir: str = ".", python_version: Optional[str] = None) -> Dict[str, Any]:
        """
        Create and setup UV-managed virtual environment.
        
        CLAUDE: Use this when no .venv exists and you need to create one.
        
        Args:
            working_dir: Project directory
            python_version: Python version to use (e.g., "3.11"). Auto-detects if not specified.
        
        Returns:
            Setup status and next steps
        """
        from ..environment import UVManager
        
        working_path = Path(working_dir).absolute()
        uv_manager = UVManager(working_path)
        
        # Create venv
        result = uv_manager.create_venv(python_version)
        
        if result['success']:
            # Sync dependencies if lock file exists
            if uv_manager.uv_lock_path.exists():
                sync_result = uv_manager.sync_dependencies()
                result['sync_result'] = sync_result
            
            # Ensure Jupyter packages
            jupyter_result = uv_manager.ensure_jupyter_packages()
            result['jupyter_setup'] = jupyter_result
            
            result['claude_next'] = "Run jupyter_initialize() to start the kernel"
        
        return result
    
    @mcp.tool()
    def jupyter_ensure_dependencies(session_id: str, packages: List[str], dev: bool = False) -> Dict[str, Any]:
        """
        Install packages using UV (never use pip directly!).
        
        CLAUDE: ALWAYS use this instead of pip install. It maintains uv.lock consistency.
        
        Args:
            session_id: Current session ID
            packages: List of package names to install
            dev: Whether these are development dependencies
        
        Returns:
            Installation status for each package
        """
        from ..environment import UVManager
        from ..daemon import DaemonClient
        
        uv_manager = UVManager()
        results = {
            'installed': [],
            'failed': [],
            'already_installed': []
        }
        
        # Check current packages
        current_packages = uv_manager.list_installed_packages()
        
        for package in packages:
            # Check if already installed
            if any(package.lower() in p.lower() for p in current_packages):
                results['already_installed'].append(package)
                continue
            
            # Install with UV
            install_result = uv_manager.add_package(package, dev=dev)
            
            if install_result['success']:
                results['installed'].append(package)
            else:
                results['failed'].append({
                    'package': package,
                    'error': install_result.get('error', 'Unknown error'),
                    'suggestion': install_result.get('suggestion', '')
                })
        
        # Restart kernel if packages were installed
        if results['installed']:
            results['kernel_restart'] = "Kernel restart may be required for new packages"
            results['claude_action'] = "Consider running jupyter_restart_kernel() if imports fail"
        
        return results
    
    @mcp.tool()
    def jupyter_sync_environment(session_id: str, upgrade: bool = False) -> Dict[str, Any]:
        """
        Sync virtual environment with uv.lock file.
        
        CLAUDE: Use this after pulling changes that updated uv.lock.
        
        Args:
            session_id: Current session ID
            upgrade: Whether to upgrade packages to latest versions
        
        Returns:
            Sync status and changes made
        """
        from ..environment import UVManager
        
        uv_manager = UVManager()
        
        # Get current state
        before_packages = set(uv_manager.list_installed_packages())
        
        # Sync with UV
        result = uv_manager.sync_dependencies()
        
        if result['success']:
            # Compare packages
            after_packages = set(uv_manager.list_installed_packages())
            
            result['changes'] = {
                'added': list(after_packages - before_packages),
                'removed': list(before_packages - after_packages),
                'total_packages': len(after_packages)
            }
            
            if result['changes']['added'] or result['changes']['removed']:
                result['kernel_restart_required'] = True
                result['claude_action'] = "Run jupyter_restart_kernel() to use updated packages"
        
        return result
    
    @mcp.tool()
    def jupyter_validate_setup(working_dir: str = ".") -> Dict[str, Any]:
        """
        Validate that UV environment is properly configured.
        
        CLAUDE: Use this to check environment health before starting work.
        
        Args:
            working_dir: Project directory to validate
        
        Returns:
            Validation results with specific issues and fixes
        """
        from ..environment import UVManager
        from ..handlers import ResponseFormatter
        
        working_path = Path(working_dir).absolute()
        uv_manager = UVManager(working_path)
        formatter = ResponseFormatter()
        
        validation = uv_manager.validate_setup()
        
        # Format response for Claude
        result = formatter.format_validation_response(validation)
        
        # Add specific Claude instructions
        if not validation['is_valid']:
            result['claude_fix_commands'] = []
            for issue in validation['issues']:
                if 'UV is not installed' in issue:
                    result['claude_fix_commands'].append(
                        "UV needs to be installed on the system. User should run: curl -LsSf https://astral.sh/uv/install.sh | sh"
                    )
                elif 'No virtual environment' in issue:
                    result['claude_fix_commands'].append(
                        "jupyter_setup_uv_environment()"
                    )
                elif 'Jupyter not installed' in issue:
                    result['claude_fix_commands'].append(
                        "jupyter_ensure_dependencies(session_id, ['jupyter'])"
                    )
        
        return result