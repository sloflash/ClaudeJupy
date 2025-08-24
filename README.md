# ML Jupyter MCP - UV-Centric Persistent Jupyter Kernel for Claude

Execute Python code with persistent state across Claude conversations using MCP (Model Context Protocol).

## ✨ Features

- 🔄 **Persistent State** - Variables and imports persist across executions
- 📓 **Notebook Support** - Create and manage Jupyter notebooks
- 🐍 **Virtual Environment Detection** - Automatically uses project's `.venv`
- 🚀 **Easy Installation** - One-line setup with Claude MCP

## 📦 Installation

### Quick Install (Recommended)

```bash
# Install from PyPI
pipx install ml-jupyter-mcp

# Add to Claude Code
claude mcp add jupyter-executor ml-jupyter-mcp
```

That's it! The MCP server is now available in all your Claude sessions.

### Alternative: Install with UV

```bash
# Install with UV tool
uv tool install ml-jupyter-mcp

# Add to Claude Code  
claude mcp add jupyter-executor "uvx ml-jupyter-mcp"
```

### Alternative: Clone and Install Locally

```bash
# Clone the repository
git clone https://github.com/mayankketkar/ml-jupyter-mcp.git
cd ml-jupyter-mcp

# Create virtual environment
uv venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e .

# Add to Claude Code
claude mcp add jupyter-executor "$(pwd)/.venv/bin/python -m ml_jupyter_mcp.server"
```

## 🎯 Usage

Once installed, you can use these MCP tools in any Claude conversation:

### Execute Python Code

```python
# In Claude, use:
mcp__jupyter-executor__execute_code("x = 42; print(f'x = {x}')")

# Later in the same conversation:
mcp__jupyter-executor__execute_code("print(f'x is still {x}')")  # x persists!
```

### Create Jupyter Notebooks

```python
# Add code cells to notebooks
mcp__jupyter-executor__add_notebook_cell("analysis.ipynb", "code", "import pandas as pd")
```

### Check Kernel Status

```python
# Check if kernel is running
mcp__jupyter-executor__kernel_status()
```

### Shutdown Kernel

```python
# Clean shutdown when done
mcp__jupyter-executor__shutdown_kernel()
```

## 🛠️ How It Works

1. **Kernel Daemon** - Maintains a persistent Jupyter kernel in the background
2. **MCP Server** - Provides tools that Claude can invoke
3. **State Persistence** - All variables, imports, and definitions persist across tool calls
4. **Auto-detection** - Automatically finds and uses your project's `.venv` if available

## 📝 Example Workflow

```python
# Start a data analysis session
mcp__jupyter-executor__execute_code("""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load your data
df = pd.read_csv('data.csv')
print(f"Loaded {len(df)} rows")
""")

# Continue analysis in next message
mcp__jupyter-executor__execute_code("""
# df is still available!
summary = df.describe()
print(summary)
""")

# Create a notebook with your analysis
mcp__jupyter-executor__add_notebook_cell("analysis.ipynb", "code", """
# Data Analysis
df.groupby('category').mean().plot(kind='bar')
plt.title('Average by Category')
plt.show()
""")
```

## 🔧 Configuration

The tool automatically:
- Detects and uses `.venv` in your project directory
- Installs required packages on first notebook creation
- Manages kernel lifecycle automatically

## 📋 Requirements

- Python 3.8+
- Claude Code CLI (`claude` command)

## 🐛 Troubleshooting

### MCP tools not showing up?
```bash
# Check if server is connected
claude mcp list

# Should show:
# jupyter-executor: ... - ✓ Connected
```

### Kernel not starting?
```bash
# Remove and re-add the server
claude mcp remove jupyter-executor
claude mcp add jupyter-executor "uvx ml-jupyter-mcp"
```

### Port 9999 already in use?
The kernel daemon uses port 9999. If it's in use, the tool will handle it automatically.

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - feel free to use in your projects!

## 🙏 Acknowledgments

Built for the Claude Code community to enable persistent Python execution across conversations.

---

**Pro Tip:** After installation, try asking Claude: "Use jupyter-executor to calculate fibonacci numbers and keep them in memory for later use!"