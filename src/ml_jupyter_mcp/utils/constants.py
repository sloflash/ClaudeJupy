"""
Shared constants and configuration for Jupyter MCP Server
"""

# Default ports
DEFAULT_DAEMON_PORT = 9999

# Timeout values (in seconds)
DEFAULT_EXECUTION_TIMEOUT = 120
KERNEL_STARTUP_TIMEOUT = 30
DAEMON_STARTUP_TIMEOUT = 10

# File paths
LOCK_FILE_NAME = '.kernel_daemon.lock'
CONNECTION_FILE_NAME = '.kernel_connection.json'

# Package mappings for common import errors
IMPORT_TO_PACKAGE_MAP = {
    'cv2': 'opencv-python',
    'sklearn': 'scikit-learn',
    'PIL': 'pillow',
    'Image': 'pillow',
    'yaml': 'pyyaml',
    'dotenv': 'python-dotenv',
    'bs4': 'beautifulsoup4',
    'wx': 'wxpython',
    'OpenSSL': 'pyopenssl',
    'dateutil': 'python-dateutil',
    'tensorflow': 'tensorflow',
    'torch': 'pytorch',
    'torchvision': 'torchvision',
    'transformers': 'transformers',
    'openai': 'openai',
    'anthropic': 'anthropic',
    'fastapi': 'fastapi',
    'uvicorn': 'uvicorn',
    'pytest': 'pytest',
    'black': 'black',
    'isort': 'isort',
    'ruff': 'ruff',
    'mypy': 'mypy',
    'pandas': 'pandas',
    'numpy': 'numpy',
    'matplotlib': 'matplotlib',
    'seaborn': 'seaborn',
    'plotly': 'plotly',
    'scipy': 'scipy',
    'sympy': 'sympy',
    'networkx': 'networkx',
    'requests': 'requests',
    'flask': 'flask',
    'django': 'django',
    'sqlalchemy': 'sqlalchemy',
    'pymongo': 'pymongo',
    'redis': 'redis',
    'celery': 'celery',
    'boto3': 'boto3',
    'google': 'google-cloud',
    'azure': 'azure-storage-blob'
}

# Required Jupyter packages
REQUIRED_JUPYTER_PACKAGES = [
    'jupyter',
    'ipykernel',
    'nbformat',
    'jupyter_client'
]

# Development packages
DEV_PACKAGES = [
    'pytest',
    'black',
    'isort',
    'ruff',
    'mypy'
]

# Template descriptions
NOTEBOOK_TEMPLATES = {
    'default': 'Basic notebook with minimal structure',
    'data_analysis': 'Complete data analysis workflow template',
    'ml_experiment': 'Machine learning experiment with train/test/evaluate sections',
    'visualization': 'Data visualization focused template with plotting setup'
}

# Error messages for Claude
CLAUDE_ERROR_MESSAGES = {
    'no_uv': "UV is not installed. Ask the user to install it with: curl -LsSf https://astral.sh/uv/install.sh | sh",
    'no_venv': "No virtual environment found. Run jupyter_setup_uv_environment() to create one",
    'no_kernel': "Kernel is not running. Run jupyter_initialize() to start everything",
    'import_error': "Package not found. Use jupyter_ensure_dependencies() to install via UV",
    'file_error': "File not found. Check the path and working directory"
}

# Success messages for Claude
CLAUDE_SUCCESS_MESSAGES = {
    'env_ready': "Environment is ready! You can now execute code",
    'package_installed': "Package installed successfully via UV",
    'kernel_started': "Kernel daemon started and ready",
    'notebook_created': "Notebook created successfully"
}