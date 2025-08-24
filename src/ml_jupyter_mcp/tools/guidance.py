"""
Claude Guidance Tools - Help Claude use the MCP server effectively
"""

from typing import Dict, Any, List, Optional

def register(mcp):
    """Register guidance tools with the MCP server"""
    
    @mcp.tool()
    def jupyter_get_guidance(action: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get context-aware guidance for Claude on how to use Jupyter tools effectively.
        
        CLAUDE: Use this tool when you're unsure about the next step or need help with:
        - Setting up a new environment
        - Fixing errors
        - Understanding tool usage
        - Following best practices
        
        Args:
            action: What you're trying to do (e.g., "create_notebook", "fix_error", "setup_environment")
            context: Optional context about current state (e.g., error info, environment status)
        
        Returns:
            Detailed guidance with step-by-step instructions
        """
        guidance_map = {
            'setup_environment': get_setup_guidance,
            'fix_error': get_error_fix_guidance,
            'create_notebook': get_notebook_creation_guidance,
            'execute_code': get_execution_guidance,
            'install_package': get_package_installation_guidance,
            'manage_kernel': get_kernel_management_guidance
        }
        
        handler = guidance_map.get(action, get_general_guidance)
        return handler(context or {})
    
    @mcp.tool()
    def jupyter_what_next(session_id: str, goal: Optional[str] = None) -> Dict[str, Any]:
        """
        Suggest what Claude should do next based on current state.
        
        CLAUDE: Use this when you've completed a task and need to know what to do next.
        
        Args:
            session_id: Current session ID
            goal: Optional description of what the user wants to achieve
        
        Returns:
            Prioritized list of next actions with specific tool recommendations
        """
        from ..daemon import DaemonClient
        from ..handlers import ResponseFormatter
        
        client = DaemonClient()
        formatter = ResponseFormatter()
        
        # Get current state
        status = client.get_status()
        namespace = client.inspect_namespace() if status.get('kernel_running') else {}
        
        recommendations = []
        
        # Check kernel status
        if not status.get('kernel_running'):
            recommendations.append({
                'priority': 1,
                'action': 'Start kernel',
                'reason': 'No kernel is running',
                'tool': 'jupyter_initialize',
                'command': "jupyter_initialize(working_dir='.')"
            })
        
        # Check for common data science patterns
        if 'df' in namespace:
            df_info = namespace.get('df', {})
            if df_info.get('type') == 'DataFrame':
                recommendations.append({
                    'priority': 2,
                    'action': 'Explore DataFrame',
                    'reason': f"DataFrame 'df' detected with shape {df_info.get('shape', 'unknown')}",
                    'tool': 'jupyter_execute_cell',
                    'command': "jupyter_execute_cell(session_id, 'df.describe()')"
                })
        
        # Check for models
        if 'model' in namespace:
            recommendations.append({
                'priority': 2,
                'action': 'Evaluate model',
                'reason': 'Model object detected',
                'tool': 'jupyter_execute_cell',
                'command': "jupyter_execute_cell(session_id, 'model.score(X_test, y_test)')"
            })
        
        # Default recommendations
        if not recommendations:
            recommendations.append({
                'priority': 3,
                'action': 'Import common libraries',
                'reason': 'Start with standard imports',
                'tool': 'jupyter_execute_cell',
                'command': "jupyter_execute_cell(session_id, 'import pandas as pd\\nimport numpy as np\\nimport matplotlib.pyplot as plt')"
            })
        
        return {
            'current_state': {
                'kernel_running': status.get('kernel_running', False),
                'execution_count': status.get('execution_count', 0),
                'variables_defined': list(namespace.keys())[:10],  # First 10 variables
                'environment': status.get('environment', {})
            },
            'recommendations': sorted(recommendations, key=lambda x: x['priority']),
            'tips': [
                "Always check environment before starting",
                "Use UV for package management",
                "Save notebooks regularly"
            ]
        }

def get_setup_guidance(context: Dict[str, Any]) -> Dict[str, Any]:
    """Get guidance for environment setup"""
    return {
        'workflow': [
            {
                'step': 1,
                'action': 'Check for UV installation',
                'command': "jupyter_detect_uv_environment(working_dir='.')",
                'why': "UV provides better dependency management than pip"
            },
            {
                'step': 2,
                'action': 'Initialize environment',
                'command': "jupyter_initialize(working_dir='.')",
                'why': "Automatically sets up venv, installs dependencies, and starts kernel"
            },
            {
                'step': 3,
                'action': 'Validate setup',
                'command': "jupyter_validate_setup(working_dir='.')",
                'why': "Ensures everything is properly configured"
            }
        ],
        'best_practices': [
            "ALWAYS use UV for Python package management",
            "NEVER use pip install directly - use jupyter_ensure_dependencies",
            "Check for .python-version file to use correct Python version",
            "Run uv sync after pulling changes with updated uv.lock"
        ],
        'common_issues': [
            {
                'issue': "No .venv found",
                'fix': "Run jupyter_setup_uv_environment() to create it"
            },
            {
                'issue': "Package not found",
                'fix': "Use jupyter_ensure_dependencies() to install via UV"
            }
        ]
    }

def get_error_fix_guidance(context: Dict[str, Any]) -> Dict[str, Any]:
    """Get guidance for fixing errors"""
    error_type = context.get('error_type', 'unknown')
    
    guidance = {
        'general_steps': [
            "Read the error message carefully",
            "Check the traceback for error location",
            "Use suggestions provided in error response"
        ]
    }
    
    if error_type == 'ModuleNotFoundError':
        module = context.get('module', 'unknown')
        guidance['specific_fix'] = {
            'error': f"Module '{module}' not found",
            'steps': [
                f"Install module: jupyter_ensure_dependencies(session_id, ['{module}'])",
                "If that fails, check if import name differs from package name",
                "Common: cv2→opencv-python, sklearn→scikit-learn"
            ]
        }
    elif error_type == 'FileNotFoundError':
        guidance['specific_fix'] = {
            'error': "File not found",
            'steps': [
                "Check current working directory: os.getcwd()",
                "Use absolute paths or verify relative path",
                "Create file if it should exist"
            ]
        }
    
    return guidance

def get_notebook_creation_guidance(context: Dict[str, Any]) -> Dict[str, Any]:
    """Get guidance for creating notebooks"""
    return {
        'workflow': [
            {
                'step': 1,
                'action': 'Initialize environment first',
                'command': "jupyter_initialize(working_dir='.')"
            },
            {
                'step': 2,
                'action': 'Create notebook with template',
                'command': "jupyter_create_notebook('analysis.ipynb', template='data_analysis')"
            },
            {
                'step': 3,
                'action': 'Add cells with proper structure',
                'commands': [
                    "# Markdown cell for documentation",
                    "jupyter_add_cell(notebook_id, 'markdown', '# Data Analysis')",
                    "# Code cell for imports",
                    "jupyter_add_cell(notebook_id, 'code', 'import pandas as pd')"
                ]
            }
        ],
        'cell_organization': [
            "Start with markdown cell explaining purpose",
            "Group imports in first code cell",
            "Separate data loading, processing, and visualization",
            "Add markdown cells between sections for documentation"
        ]
    }

def get_execution_guidance(context: Dict[str, Any]) -> Dict[str, Any]:
    """Get guidance for code execution"""
    return {
        'pre_execution_checks': [
            "Ensure kernel is running",
            "Check all required packages are installed",
            "Verify working directory is correct"
        ],
        'execution_tips': [
            "Break long code into multiple cells",
            "Use print() for intermediate results",
            "Handle errors gracefully with try/except",
            "Save important results to variables"
        ],
        'post_execution': [
            "Check for errors in output",
            "Validate results make sense",
            "Save notebook if results are good"
        ]
    }

def get_package_installation_guidance(context: Dict[str, Any]) -> Dict[str, Any]:
    """Get guidance for package installation"""
    return {
        'rules': [
            "ALWAYS use UV for package management",
            "NEVER use pip install directly",
            "Add packages to pyproject.toml for reproducibility"
        ],
        'workflow': [
            {
                'step': 1,
                'action': 'Use jupyter_ensure_dependencies',
                'command': "jupyter_ensure_dependencies(session_id, ['package_name'])",
                'why': "Maintains uv.lock consistency"
            },
            {
                'step': 2,
                'action': 'For development dependencies',
                'command': "jupyter_ensure_dependencies(session_id, ['pytest'], dev=True)",
                'why': "Separates dev dependencies from production"
            }
        ],
        'package_name_mapping': {
            'cv2': 'opencv-python',
            'sklearn': 'scikit-learn',
            'PIL': 'pillow',
            'yaml': 'pyyaml'
        }
    }

def get_kernel_management_guidance(context: Dict[str, Any]) -> Dict[str, Any]:
    """Get guidance for kernel management"""
    return {
        'lifecycle': [
            "Start: jupyter_initialize() - handles everything automatically",
            "Check: jupyter_kernel_status() - verify kernel is running",
            "Restart: jupyter_restart_kernel() - if kernel becomes unresponsive",
            "Shutdown: jupyter_shutdown_kernel() - clean shutdown when done"
        ],
        'troubleshooting': [
            {
                'issue': "Kernel won't start",
                'fixes': [
                    "Check if .venv exists",
                    "Verify jupyter and ipykernel are installed",
                    "Check for port conflicts on 9999"
                ]
            },
            {
                'issue': "Kernel dies unexpectedly",
                'fixes': [
                    "Check for memory issues",
                    "Look for infinite loops",
                    "Restart with jupyter_restart_kernel()"
                ]
            }
        ]
    }

def get_general_guidance(context: Dict[str, Any]) -> Dict[str, Any]:
    """Get general guidance"""
    return {
        'golden_rules': [
            "ALWAYS use jupyter_initialize() first in any project",
            "NEVER use pip - always use UV via jupyter_ensure_dependencies",
            "CHECK environment with jupyter_detect_uv_environment() if unsure",
            "SAVE work regularly with jupyter_save_notebook()"
        ],
        'typical_workflow': [
            "1. Initialize: jupyter_initialize()",
            "2. Execute code: jupyter_execute_cell()",
            "3. If error: jupyter_ensure_dependencies() for missing packages",
            "4. Continue execution",
            "5. Save results: jupyter_save_notebook()"
        ],
        'help': "Use jupyter_get_guidance() with specific action for detailed help"
    }