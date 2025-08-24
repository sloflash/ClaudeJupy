"""
Notebook Management Tools - Create, edit, and manage Jupyter notebooks
"""

import nbformat
from pathlib import Path
from typing import Dict, Any, List, Optional

def register(mcp):
    """Register notebook tools with the MCP server"""
    
    @mcp.tool()
    def jupyter_create_notebook(
        filename: str,
        session_id: Optional[str] = None,
        template: str = "default",
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new Jupyter notebook with optional template.
        
        CLAUDE: Use to create structured notebooks for analysis or reports.
        
        Args:
            filename: Path for the notebook (must end with .ipynb)
            session_id: Optional session to attach kernel
            template: Template type ("default", "data_analysis", "ml_experiment", "visualization")
            title: Optional title for the notebook
        
        Returns:
            Notebook creation status
        """
        notebook_path = Path(filename)
        
        # Ensure .ipynb extension
        if not notebook_path.suffix == '.ipynb':
            notebook_path = notebook_path.with_suffix('.ipynb')
        
        # Create notebook
        nb = nbformat.v4.new_notebook()
        
        # Add metadata
        nb.metadata = {
            'kernelspec': {
                'display_name': 'Python 3',
                'language': 'python',
                'name': 'python3'
            },
            'language_info': {
                'name': 'python',
                'version': '3.11.0'
            }
        }
        
        # Apply template
        if template == "data_analysis":
            cells = create_data_analysis_template(title or "Data Analysis")
        elif template == "ml_experiment":
            cells = create_ml_experiment_template(title or "Machine Learning Experiment")
        elif template == "visualization":
            cells = create_visualization_template(title or "Data Visualization")
        else:
            cells = create_default_template(title or "Jupyter Notebook")
        
        nb.cells = cells
        
        # Save notebook
        try:
            with open(notebook_path, 'w') as f:
                nbformat.write(nb, f)
            
            return {
                'status': 'success',
                'notebook_path': str(notebook_path),
                'cells_created': len(cells),
                'template_used': template,
                'claude_next': f"Use jupyter_add_cell() to add more cells to {notebook_path}"
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'claude_tip': "Check file permissions and path validity"
            }
    
    @mcp.tool()
    def jupyter_add_cell(
        notebook_path: str,
        cell_type: str,
        content: str,
        position: Optional[int] = None,
        execute: bool = False,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a cell to an existing notebook.
        
        CLAUDE: Use to incrementally build notebooks.
        
        Args:
            notebook_path: Path to notebook
            cell_type: "code" or "markdown"
            content: Cell content
            position: Position to insert (None = append)
            execute: Whether to execute code cell immediately
            session_id: Session ID if executing
        
        Returns:
            Cell addition status
        """
        notebook_path = Path(notebook_path)
        
        if not notebook_path.exists():
            return {
                'status': 'error',
                'error': f"Notebook not found: {notebook_path}",
                'claude_tip': "Create notebook first with jupyter_create_notebook()"
            }
        
        # Read notebook
        try:
            with open(notebook_path, 'r') as f:
                nb = nbformat.read(f, as_version=4)
        except Exception as e:
            return {
                'status': 'error',
                'error': f"Could not read notebook: {str(e)}"
            }
        
        # Create new cell
        if cell_type == 'code':
            new_cell = nbformat.v4.new_code_cell(content)
            
            # Execute if requested
            if execute and session_id:
                from ..daemon import DaemonClient
                client = DaemonClient()
                result = client.execute_code(content)
                
                # Add outputs to cell
                outputs = []
                for output in result.get('outputs', []):
                    if output['type'] == 'stream':
                        outputs.append(nbformat.v4.new_output(
                            'stream',
                            name=output['name'],
                            text=output['text']
                        ))
                    elif output['type'] == 'execute_result':
                        outputs.append(nbformat.v4.new_output(
                            'execute_result',
                            data=output['data'],
                            execution_count=output.get('execution_count', 1)
                        ))
                    elif output['type'] == 'error':
                        outputs.append(nbformat.v4.new_output(
                            'error',
                            ename=output['ename'],
                            evalue=output['evalue'],
                            traceback=output['traceback']
                        ))
                
                new_cell.outputs = outputs
                new_cell.execution_count = result.get('execution_count', 1)
                
        elif cell_type == 'markdown':
            new_cell = nbformat.v4.new_markdown_cell(content)
        else:
            return {
                'status': 'error',
                'error': f"Invalid cell type: {cell_type}",
                'claude_tip': "Use 'code' or 'markdown'"
            }
        
        # Insert cell
        if position is None:
            nb.cells.append(new_cell)
        else:
            nb.cells.insert(position, new_cell)
        
        # Save notebook
        try:
            with open(notebook_path, 'w') as f:
                nbformat.write(nb, f)
            
            result = {
                'status': 'success',
                'cell_type': cell_type,
                'position': position if position is not None else len(nb.cells) - 1,
                'total_cells': len(nb.cells)
            }
            
            if execute:
                result['executed'] = True
                result['has_error'] = any(o.get('type') == 'error' for o in result.get('outputs', []))
            
            return result
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f"Could not save notebook: {str(e)}"
            }
    
    @mcp.tool()
    def jupyter_update_cell(
        notebook_path: str,
        cell_index: int,
        content: str,
        execute: bool = False,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update content of an existing cell.
        
        CLAUDE: Use to modify cells in a notebook.
        
        Args:
            notebook_path: Path to notebook
            cell_index: Index of cell to update (0-based)
            content: New cell content
            execute: Whether to execute if code cell
            session_id: Session ID if executing
        
        Returns:
            Update status
        """
        notebook_path = Path(notebook_path)
        
        if not notebook_path.exists():
            return {
                'status': 'error',
                'error': f"Notebook not found: {notebook_path}"
            }
        
        # Read notebook
        try:
            with open(notebook_path, 'r') as f:
                nb = nbformat.read(f, as_version=4)
        except Exception as e:
            return {
                'status': 'error',
                'error': f"Could not read notebook: {str(e)}"
            }
        
        # Check cell index
        if cell_index >= len(nb.cells):
            return {
                'status': 'error',
                'error': f"Cell index {cell_index} out of range (notebook has {len(nb.cells)} cells)",
                'claude_tip': "Use jupyter_get_notebook_info() to see cell count"
            }
        
        # Update cell
        cell = nb.cells[cell_index]
        old_content = cell.source
        cell.source = content
        
        # Execute if requested and it's a code cell
        if execute and cell.cell_type == 'code' and session_id:
            from ..daemon import DaemonClient
            client = DaemonClient()
            result = client.execute_code(content)
            
            # Update outputs
            outputs = []
            for output in result.get('outputs', []):
                if output['type'] == 'stream':
                    outputs.append(nbformat.v4.new_output(
                        'stream',
                        name=output['name'],
                        text=output['text']
                    ))
                elif output['type'] == 'execute_result':
                    outputs.append(nbformat.v4.new_output(
                        'execute_result',
                        data=output['data'],
                        execution_count=output.get('execution_count', 1)
                    ))
                elif output['type'] == 'error':
                    outputs.append(nbformat.v4.new_output(
                        'error',
                        ename=output['ename'],
                        evalue=output['evalue'],
                        traceback=output['traceback']
                    ))
            
            cell.outputs = outputs
            cell.execution_count = result.get('execution_count', 1)
        
        # Save notebook
        try:
            with open(notebook_path, 'w') as f:
                nbformat.write(nb, f)
            
            return {
                'status': 'success',
                'cell_index': cell_index,
                'cell_type': cell.cell_type,
                'old_content_preview': old_content[:100] if old_content else "",
                'executed': execute and cell.cell_type == 'code'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f"Could not save notebook: {str(e)}"
            }
    
    @mcp.tool()
    def jupyter_get_notebook_info(notebook_path: str) -> Dict[str, Any]:
        """
        Get information about a notebook.
        
        CLAUDE: Use to understand notebook structure before editing.
        
        Args:
            notebook_path: Path to notebook
        
        Returns:
            Notebook metadata and cell information
        """
        notebook_path = Path(notebook_path)
        
        if not notebook_path.exists():
            return {
                'status': 'error',
                'error': f"Notebook not found: {notebook_path}"
            }
        
        # Read notebook
        try:
            with open(notebook_path, 'r') as f:
                nb = nbformat.read(f, as_version=4)
        except Exception as e:
            return {
                'status': 'error',
                'error': f"Could not read notebook: {str(e)}"
            }
        
        # Analyze cells
        cells_info = []
        code_cells = 0
        markdown_cells = 0
        
        for i, cell in enumerate(nb.cells):
            cell_info = {
                'index': i,
                'type': cell.cell_type,
                'content_preview': cell.source[:100] if cell.source else "",
                'lines': len(cell.source.split('\n')) if cell.source else 0
            }
            
            if cell.cell_type == 'code':
                code_cells += 1
                cell_info['has_output'] = len(cell.outputs) > 0 if hasattr(cell, 'outputs') else False
                cell_info['execution_count'] = cell.execution_count if hasattr(cell, 'execution_count') else None
            else:
                markdown_cells += 1
            
            cells_info.append(cell_info)
        
        return {
            'notebook_path': str(notebook_path),
            'total_cells': len(nb.cells),
            'code_cells': code_cells,
            'markdown_cells': markdown_cells,
            'cells': cells_info,
            'metadata': nb.metadata,
            'claude_tip': f"Notebook has {len(nb.cells)} cells. Use cell indices 0-{len(nb.cells)-1} for operations."
        }
    
    @mcp.tool()
    def jupyter_save_notebook(session_id: str, notebook_path: str) -> Dict[str, Any]:
        """
        Save the current session state to a notebook.
        
        CLAUDE: Use to save your work session as a notebook.
        
        Args:
            session_id: Current session ID
            notebook_path: Path to save notebook
        
        Returns:
            Save status
        """
        # This would need implementation to track executed cells in session
        # For now, return a placeholder
        return {
            'status': 'info',
            'message': "Session saving not yet implemented",
            'claude_tip': "Use jupyter_create_notebook() and jupyter_add_cell() to build notebooks"
        }

def create_default_template(title: str) -> List:
    """Create default notebook template"""
    return [
        nbformat.v4.new_markdown_cell(f"# {title}\n\nCreated with Jupyter MCP Server"),
        nbformat.v4.new_code_cell("# Import libraries\nimport pandas as pd\nimport numpy as np"),
    ]

def create_data_analysis_template(title: str) -> List:
    """Create data analysis notebook template"""
    return [
        nbformat.v4.new_markdown_cell(f"# {title}\n\n## Overview\nData analysis notebook created with Jupyter MCP Server"),
        nbformat.v4.new_markdown_cell("## 1. Setup and Imports"),
        nbformat.v4.new_code_cell("import pandas as pd\nimport numpy as np\nimport matplotlib.pyplot as plt\nimport seaborn as sns\n\n# Set style\nsns.set_style('whitegrid')\nplt.rcParams['figure.figsize'] = (10, 6)"),
        nbformat.v4.new_markdown_cell("## 2. Load Data"),
        nbformat.v4.new_code_cell("# Load your data here\n# df = pd.read_csv('data.csv')"),
        nbformat.v4.new_markdown_cell("## 3. Data Exploration"),
        nbformat.v4.new_code_cell("# Basic info\n# df.info()\n# df.describe()"),
        nbformat.v4.new_markdown_cell("## 4. Data Cleaning"),
        nbformat.v4.new_code_cell("# Handle missing values, outliers, etc."),
        nbformat.v4.new_markdown_cell("## 5. Analysis"),
        nbformat.v4.new_code_cell("# Perform your analysis"),
        nbformat.v4.new_markdown_cell("## 6. Visualization"),
        nbformat.v4.new_code_cell("# Create visualizations"),
        nbformat.v4.new_markdown_cell("## 7. Conclusions"),
    ]

def create_ml_experiment_template(title: str) -> List:
    """Create ML experiment notebook template"""
    return [
        nbformat.v4.new_markdown_cell(f"# {title}\n\n## Machine Learning Experiment"),
        nbformat.v4.new_markdown_cell("## 1. Imports and Setup"),
        nbformat.v4.new_code_cell("import pandas as pd\nimport numpy as np\nfrom sklearn.model_selection import train_test_split\nfrom sklearn.preprocessing import StandardScaler\nfrom sklearn.metrics import classification_report, confusion_matrix\nimport matplotlib.pyplot as plt\nimport seaborn as sns"),
        nbformat.v4.new_markdown_cell("## 2. Load and Prepare Data"),
        nbformat.v4.new_code_cell("# Load data\n# df = pd.read_csv('data.csv')"),
        nbformat.v4.new_markdown_cell("## 3. Feature Engineering"),
        nbformat.v4.new_code_cell("# Create features"),
        nbformat.v4.new_markdown_cell("## 4. Train/Test Split"),
        nbformat.v4.new_code_cell("# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)"),
        nbformat.v4.new_markdown_cell("## 5. Model Training"),
        nbformat.v4.new_code_cell("# Train your model"),
        nbformat.v4.new_markdown_cell("## 6. Evaluation"),
        nbformat.v4.new_code_cell("# Evaluate model performance"),
        nbformat.v4.new_markdown_cell("## 7. Results and Next Steps"),
    ]

def create_visualization_template(title: str) -> List:
    """Create visualization notebook template"""
    return [
        nbformat.v4.new_markdown_cell(f"# {title}\n\n## Data Visualization"),
        nbformat.v4.new_markdown_cell("## Setup"),
        nbformat.v4.new_code_cell("import pandas as pd\nimport numpy as np\nimport matplotlib.pyplot as plt\nimport seaborn as sns\nimport plotly.express as px\n\n# Configure visualization settings\nsns.set_theme(style='whitegrid')\nplt.rcParams['figure.figsize'] = (12, 8)"),
        nbformat.v4.new_markdown_cell("## Load Data"),
        nbformat.v4.new_code_cell("# df = pd.read_csv('data.csv')"),
        nbformat.v4.new_markdown_cell("## Statistical Plots"),
        nbformat.v4.new_code_cell("# Distribution plots, correlations, etc."),
        nbformat.v4.new_markdown_cell("## Time Series Plots"),
        nbformat.v4.new_code_cell("# If applicable"),
        nbformat.v4.new_markdown_cell("## Interactive Visualizations"),
        nbformat.v4.new_code_cell("# Using plotly or similar"),
    ]