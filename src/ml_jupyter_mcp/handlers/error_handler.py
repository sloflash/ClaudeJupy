"""
Smart Error Handler - Parses errors and provides actionable suggestions for Claude
"""

import re
from typing import Dict, List, Any, Optional

class ErrorHandler:
    def __init__(self):
        # Map of error types to handlers
        self.error_handlers = {
            'ModuleNotFoundError': self.handle_module_not_found,
            'ImportError': self.handle_import_error,
            'FileNotFoundError': self.handle_file_not_found,
            'NameError': self.handle_name_error,
            'AttributeError': self.handle_attribute_error,
            'TypeError': self.handle_type_error,
            'ValueError': self.handle_value_error,
            'SyntaxError': self.handle_syntax_error,
            'IndentationError': self.handle_indentation_error,
            'KeyError': self.handle_key_error,
            'IndexError': self.handle_index_error,
            'MemoryError': self.handle_memory_error,
            'RuntimeError': self.handle_runtime_error
        }
        
        # Common import name to package name mapping
        self.package_map = {
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
            'mypy': 'mypy'
        }
    
    def parse_error(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Parse error information and generate suggestions"""
        error_type = error_info.get('ename', 'UnknownError')
        error_message = error_info.get('evalue', '')
        traceback = error_info.get('traceback', [])
        
        # Get specific handler or use generic
        handler = self.error_handlers.get(error_type, self.handle_generic_error)
        
        # Generate base analysis
        analysis = handler(error_message, traceback)
        
        # Add Claude-specific guidance
        analysis['claude_guidance'] = self.get_claude_guidance(error_type, analysis)
        
        # Add context from traceback
        analysis['error_location'] = self.extract_error_location(traceback)
        
        return analysis
    
    def handle_module_not_found(self, message: str, traceback: List[str]) -> Dict[str, Any]:
        """Handle ModuleNotFoundError"""
        # Extract module name from error message
        module_match = re.search(r"No module named '([^']+)'", message)
        module_name = module_match.group(1) if module_match else 'unknown'
        
        # Get package name
        package_name = self.package_map.get(module_name, module_name)
        
        return {
            'error_type': 'ModuleNotFoundError',
            'module': module_name,
            'package': package_name,
            'suggestions': [
                f"Install missing package: uv add {package_name}",
                f"Or if UV not available: pip install {package_name}",
                "Check if you're in the correct virtual environment",
                "Run 'uv sync' if package is already in uv.lock"
            ],
            'commands': [
                f"uv add {package_name}",
                "uv sync"
            ],
            'next_action': 'jupyter_ensure_dependencies'
        }
    
    def handle_import_error(self, message: str, traceback: List[str]) -> Dict[str, Any]:
        """Handle ImportError"""
        # Check for specific import patterns
        cannot_import = re.search(r"cannot import name '([^']+)'", message)
        
        if cannot_import:
            name = cannot_import.group(1)
            return {
                'error_type': 'ImportError',
                'import_name': name,
                'suggestions': [
                    f"Check if '{name}' exists in the module",
                    "Verify the import path is correct",
                    "The module might be installed but the specific function/class doesn't exist",
                    "Check the module's version - the API might have changed"
                ],
                'commands': [
                    "# Check installed version",
                    "import pkg_resources",
                    "pkg_resources.get_distribution('package_name').version"
                ]
            }
        
        return {
            'error_type': 'ImportError',
            'suggestions': [
                "Check if the module is properly installed",
                "Verify import statement syntax",
                "Run 'uv sync' to ensure all dependencies are installed"
            ],
            'commands': ["uv sync"]
        }
    
    def handle_file_not_found(self, message: str, traceback: List[str]) -> Dict[str, Any]:
        """Handle FileNotFoundError"""
        # Extract file path from error
        file_match = re.search(r"['\"]([^'\"]+)['\"]", message)
        file_path = file_match.group(1) if file_match else 'unknown'
        
        return {
            'error_type': 'FileNotFoundError',
            'file_path': file_path,
            'suggestions': [
                f"Check if file exists: {file_path}",
                "Verify the file path is correct",
                "Use absolute paths or check working directory",
                "Create the file if it should exist",
                f"Try: Path('{file_path}').exists() to check"
            ],
            'commands': [
                "import os",
                "os.getcwd()  # Check current directory",
                f"Path('{file_path}').exists()  # Check if file exists"
            ]
        }
    
    def handle_name_error(self, message: str, traceback: List[str]) -> Dict[str, Any]:
        """Handle NameError"""
        name_match = re.search(r"name '([^']+)' is not defined", message)
        name = name_match.group(1) if name_match else 'unknown'
        
        return {
            'error_type': 'NameError',
            'undefined_name': name,
            'suggestions': [
                f"Variable '{name}' is not defined",
                "Check for typos in the variable name",
                "Ensure the variable is defined before use",
                "Run previous cells if in a notebook",
                "Import required modules if it's a function/class"
            ],
            'commands': [
                f"# Define {name} before using it",
                f"{name} = ...  # Add appropriate value"
            ]
        }
    
    def handle_attribute_error(self, message: str, traceback: List[str]) -> Dict[str, Any]:
        """Handle AttributeError"""
        attr_match = re.search(r"'([^']+)' object has no attribute '([^']+)'", message)
        
        if attr_match:
            obj_type = attr_match.group(1)
            attr_name = attr_match.group(2)
            
            return {
                'error_type': 'AttributeError',
                'object_type': obj_type,
                'attribute': attr_name,
                'suggestions': [
                    f"'{obj_type}' objects don't have attribute '{attr_name}'",
                    "Check for typos in the attribute name",
                    f"Use dir() to see available attributes",
                    "The object might be None or of unexpected type"
                ],
                'commands': [
                    f"# Check available attributes",
                    f"dir(your_object)  # Replace with actual object",
                    f"type(your_object)  # Check object type"
                ]
            }
        
        return {
            'error_type': 'AttributeError',
            'suggestions': [
                "Object doesn't have the requested attribute",
                "Check object type and available methods"
            ]
        }
    
    def handle_type_error(self, message: str, traceback: List[str]) -> Dict[str, Any]:
        """Handle TypeError"""
        return {
            'error_type': 'TypeError',
            'suggestions': [
                "Check data types of variables",
                "Ensure function arguments are of correct type",
                "Convert data types if necessary",
                "Check function signature and required arguments"
            ],
            'commands': [
                "# Check variable types",
                "type(variable_name)",
                "# Convert if needed",
                "int(), str(), float(), list(), etc."
            ]
        }
    
    def handle_value_error(self, message: str, traceback: List[str]) -> Dict[str, Any]:
        """Handle ValueError"""
        return {
            'error_type': 'ValueError',
            'suggestions': [
                "Input value is invalid for the operation",
                "Check data format and ranges",
                "Validate input before processing",
                "Handle edge cases appropriately"
            ]
        }
    
    def handle_syntax_error(self, message: str, traceback: List[str]) -> Dict[str, Any]:
        """Handle SyntaxError"""
        return {
            'error_type': 'SyntaxError',
            'suggestions': [
                "Check for syntax errors in the code",
                "Look for missing colons, parentheses, or quotes",
                "Verify indentation is consistent",
                "Check for Python version compatibility"
            ]
        }
    
    def handle_indentation_error(self, message: str, traceback: List[str]) -> Dict[str, Any]:
        """Handle IndentationError"""
        return {
            'error_type': 'IndentationError',
            'suggestions': [
                "Fix indentation - use consistent spaces or tabs",
                "Python uses 4 spaces for indentation by convention",
                "Check that all code blocks are properly indented",
                "Don't mix tabs and spaces"
            ]
        }
    
    def handle_key_error(self, message: str, traceback: List[str]) -> Dict[str, Any]:
        """Handle KeyError"""
        key = message.strip("'\"")
        
        return {
            'error_type': 'KeyError',
            'missing_key': key,
            'suggestions': [
                f"Key '{key}' not found in dictionary",
                "Check available keys with .keys()",
                "Use .get() method for safe access",
                "Verify the key name and spelling"
            ],
            'commands': [
                "dict_name.keys()  # Check available keys",
                f"dict_name.get('{key}', default_value)  # Safe access"
            ]
        }
    
    def handle_index_error(self, message: str, traceback: List[str]) -> Dict[str, Any]:
        """Handle IndexError"""
        return {
            'error_type': 'IndexError',
            'suggestions': [
                "Index is out of range",
                "Check list/array length before accessing",
                "Use negative indices for reverse access",
                "Validate index bounds"
            ],
            'commands': [
                "len(list_name)  # Check length",
                "list_name[-1]  # Access last element"
            ]
        }
    
    def handle_memory_error(self, message: str, traceback: List[str]) -> Dict[str, Any]:
        """Handle MemoryError"""
        return {
            'error_type': 'MemoryError',
            'suggestions': [
                "System ran out of memory",
                "Process data in smaller chunks",
                "Use generators instead of lists",
                "Clear unnecessary variables",
                "Consider using data sampling"
            ],
            'commands': [
                "import gc",
                "gc.collect()  # Force garbage collection",
                "del large_variable  # Free memory"
            ]
        }
    
    def handle_runtime_error(self, message: str, traceback: List[str]) -> Dict[str, Any]:
        """Handle RuntimeError"""
        return {
            'error_type': 'RuntimeError',
            'suggestions': [
                "Runtime error occurred",
                "Check for infinite recursion",
                "Verify environment setup",
                "Check for threading issues"
            ]
        }
    
    def handle_generic_error(self, message: str, traceback: List[str]) -> Dict[str, Any]:
        """Handle generic/unknown errors"""
        return {
            'error_type': 'UnknownError',
            'suggestions': [
                "An unexpected error occurred",
                "Check the error message for details",
                "Review the traceback for error location",
                "Search for the error message online"
            ]
        }
    
    def extract_error_location(self, traceback: List[str]) -> Optional[Dict[str, Any]]:
        """Extract error location from traceback"""
        if not traceback:
            return None
        
        # Look for file and line information in traceback
        for line in reversed(traceback):
            file_match = re.search(r'File "([^"]+)", line (\d+)', line)
            if file_match:
                return {
                    'file': file_match.group(1),
                    'line': int(file_match.group(2))
                }
        
        return None
    
    def get_claude_guidance(self, error_type: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Get Claude-specific guidance for handling errors"""
        guidance = {
            'should_retry': False,
            'next_tool': None,
            'explanation_needed': False
        }
        
        if error_type == 'ModuleNotFoundError':
            guidance['should_retry'] = True
            guidance['next_tool'] = 'jupyter_ensure_dependencies'
            guidance['action'] = f"Use jupyter_ensure_dependencies to install {analysis.get('package', 'missing package')}"
        
        elif error_type == 'FileNotFoundError':
            guidance['explanation_needed'] = True
            guidance['action'] = "Check if file exists and verify path"
        
        elif error_type == 'NameError':
            guidance['should_retry'] = True
            guidance['action'] = "Define the variable or import required module"
        
        return guidance