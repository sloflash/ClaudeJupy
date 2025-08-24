"""
Response Formatter - Formats responses for optimal Claude understanding
"""

from typing import Dict, List, Any, Optional

class ResponseFormatter:
    def __init__(self):
        self.checklist_icons = {
            'completed': '✓',
            'pending': '○',
            'warning': '⚠',
            'error': '✗',
            'info': 'ℹ'
        }
    
    def format_execution_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format code execution response for Claude"""
        response = {
            'status': result.get('status', 'unknown'),
            'execution_count': result.get('execution_count', 0),
            'outputs': []
        }
        
        # Format outputs for clarity
        for output in result.get('outputs', []):
            if output['type'] == 'stream':
                response['outputs'].append({
                    'type': 'output',
                    'content': output['text']
                })
            elif output['type'] == 'execute_result':
                response['outputs'].append({
                    'type': 'result',
                    'content': output['data'].get('text/plain', '')
                })
            elif output['type'] == 'error':
                response['outputs'].append({
                    'type': 'error',
                    'name': output['ename'],
                    'message': output['evalue'],
                    'traceback': output.get('traceback', [])
                })
        
        # Add error handling guidance if error occurred
        if result.get('has_error'):
            response['error_guidance'] = self.format_error_guidance(result)
        
        # Add Claude checklist
        response['claude_checklist'] = self.create_execution_checklist(result)
        
        # Add next actions
        response['next_actions'] = self.suggest_next_actions(result)
        
        return response
    
    def format_error_guidance(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format error guidance for Claude"""
        error_suggestions = result.get('error_suggestions', [])
        
        # Find the error in outputs
        error_info = None
        for output in result.get('outputs', []):
            if output.get('type') == 'error':
                error_info = output
                break
        
        if not error_info:
            return {}
        
        guidance = {
            'error_type': error_info.get('ename', 'UnknownError'),
            'error_message': error_info.get('evalue', ''),
            'suggestions': error_suggestions,
            'should_fix': True
        }
        
        # Add specific fix commands based on error type
        if error_info.get('ename') == 'ModuleNotFoundError':
            module = self.extract_module_name(error_info.get('evalue', ''))
            guidance['fix_commands'] = [
                f"jupyter_ensure_dependencies(session_id, ['{module}'])"
            ]
            guidance['explanation'] = f"Package '{module}' is not installed. I'll install it using UV."
        
        return guidance
    
    def create_execution_checklist(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Create a checklist for Claude to track execution status"""
        checklist = {
            'completed': [],
            'pending': [],
            'warnings': []
        }
        
        # Check what was completed
        if result.get('status') == 'success' and not result.get('has_error'):
            checklist['completed'].append(f"{self.checklist_icons['completed']} Code executed successfully")
        
        if result.get('execution_count', 0) > 0:
            checklist['completed'].append(
                f"{self.checklist_icons['completed']} Execution #{result['execution_count']} completed"
            )
        
        # Check for errors
        if result.get('has_error'):
            checklist['warnings'].append(
                f"{self.checklist_icons['error']} Error occurred - needs fixing"
            )
            checklist['pending'].append(
                f"{self.checklist_icons['pending']} Fix error and retry execution"
            )
        
        # Add environment checks
        if result.get('environment'):
            env = result['environment']
            if env.get('using_uv'):
                checklist['completed'].append(
                    f"{self.checklist_icons['completed']} Using UV environment"
                )
            else:
                checklist['warnings'].append(
                    f"{self.checklist_icons['warning']} Not using UV environment"
                )
        
        return checklist
    
    def suggest_next_actions(self, result: Dict[str, Any]) -> List[Dict[str, str]]:
        """Suggest next actions for Claude based on execution result"""
        actions = []
        
        if result.get('has_error'):
            # Error occurred - suggest fixes
            for output in result.get('outputs', []):
                if output.get('type') == 'error':
                    if output.get('ename') == 'ModuleNotFoundError':
                        module = self.extract_module_name(output.get('evalue', ''))
                        actions.append({
                            'priority': 1,
                            'action': 'install_package',
                            'description': f"Install missing package '{module}'",
                            'tool': 'jupyter_ensure_dependencies',
                            'parameters': {'packages': [module]}
                        })
                    elif output.get('ename') == 'NameError':
                        actions.append({
                            'priority': 1,
                            'action': 'define_variable',
                            'description': "Define the missing variable or import",
                            'tool': 'jupyter_execute_cell'
                        })
        else:
            # Success - suggest continuation
            actions.append({
                'priority': 2,
                'action': 'continue',
                'description': "Continue with next code cell or task",
                'tool': 'jupyter_execute_cell'
            })
        
        return sorted(actions, key=lambda x: x['priority'])
    
    def format_environment_response(self, env_info: Dict[str, Any]) -> Dict[str, Any]:
        """Format environment detection response for Claude"""
        response = {
            'environments_found': len(env_info.get('environments', [])),
            'recommended': env_info.get('recommended'),
            'details': []
        }
        
        for env in env_info.get('environments', []):
            detail = {
                'type': env['type'],
                'path': env.get('path', 'N/A'),
                'python_version': env.get('python_version', 'unknown'),
                'is_active': env.get('python_executable') == env_info.get('current_python')
            }
            
            if env['type'] == 'uv':
                detail['badge'] = '🎯 UV (Recommended)'
            elif env['type'] == 'venv':
                detail['badge'] = '📦 Virtual Env'
            elif env['type'] == 'conda':
                detail['badge'] = '🐍 Conda'
            else:
                detail['badge'] = '💻 System'
            
            response['details'].append(detail)
        
        # Add setup guidance
        response['setup_guidance'] = self.create_setup_guidance(env_info)
        
        return response
    
    def create_setup_guidance(self, env_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create setup guidance based on environment detection"""
        guidance = {
            'steps': [],
            'commands': []
        }
        
        has_uv_env = any(e['type'] == 'uv' for e in env_info.get('environments', []))
        
        if not has_uv_env:
            guidance['steps'] = [
                "No UV environment detected",
                "Create UV environment for better dependency management",
                "Install required packages"
            ]
            guidance['commands'] = [
                "jupyter_setup_uv_environment(working_dir='.')",
                "jupyter_ensure_dependencies(session_id, ['jupyter', 'ipykernel'])"
            ]
        else:
            guidance['steps'] = [
                "UV environment detected",
                "Ensure dependencies are synced",
                "Start kernel with UV environment"
            ]
            guidance['commands'] = [
                "jupyter_validate_setup(working_dir='.')",
                "jupyter_start_kernel_uv(working_dir='.')"
            ]
        
        return guidance
    
    def format_validation_response(self, validation: Dict[str, Any]) -> Dict[str, Any]:
        """Format environment validation response"""
        response = {
            'is_valid': validation.get('is_valid', False),
            'checks': []
        }
        
        # Format checks with icons
        for check, status in validation.get('checks', {}).items():
            icon = self.checklist_icons['completed'] if status else self.checklist_icons['error']
            response['checks'].append(f"{icon} {check.replace('_', ' ').title()}: {'✅' if status else '❌'}")
        
        # Add issues and suggestions
        if validation.get('issues'):
            response['issues'] = validation['issues']
            response['fixes'] = validation.get('suggestions', [])
            
            # Create fix commands
            response['fix_commands'] = []
            for suggestion in validation.get('suggestions', []):
                if 'uv venv' in suggestion:
                    response['fix_commands'].append("jupyter_setup_uv_environment()")
                elif 'uv add' in suggestion:
                    response['fix_commands'].append("jupyter_ensure_dependencies()")
                elif 'uv sync' in suggestion:
                    response['fix_commands'].append("jupyter_sync_environment()")
        
        return response
    
    def extract_module_name(self, error_message: str) -> str:
        """Extract module name from error message"""
        import re
        match = re.search(r"No module named '([^']+)'", error_message)
        return match.group(1) if match else 'unknown'
    
    def format_namespace_response(self, namespace: Dict[str, Any]) -> Dict[str, Any]:
        """Format namespace inspection response"""
        response = {
            'variables': {},
            'modules': [],
            'functions': [],
            'classes': []
        }
        
        for name, info in namespace.items():
            obj_type = info.get('type', 'unknown')
            
            if obj_type == 'module':
                response['modules'].append(name)
            elif obj_type == 'function':
                response['functions'].append(name)
            elif obj_type == 'type':
                response['classes'].append(name)
            else:
                # Regular variable
                var_info = {'type': obj_type}
                if 'length' in info:
                    var_info['length'] = info['length']
                if 'shape' in info:
                    var_info['shape'] = info['shape']
                if 'dtype' in info:
                    var_info['dtype'] = info['dtype']
                response['variables'][name] = var_info
        
        # Add summary
        response['summary'] = {
            'total_variables': len(response['variables']),
            'total_modules': len(response['modules']),
            'total_functions': len(response['functions']),
            'total_classes': len(response['classes'])
        }
        
        return response