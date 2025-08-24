#!/bin/bash
# Publish ml-jupyter-mcp to PyPI

set -e  # Exit on error

# Load environment variables
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/.env"

echo "🚀 Publishing ml-jupyter-mcp to PyPI..."
echo ""

# Check for token
if [ -z "$PYPI_API_TOKEN" ]; then
    echo "❌ Error: PYPI_API_TOKEN not found in .env file"
    exit 1
fi

# Build first
echo "📦 Building package..."
cd "$SCRIPT_DIR"
./build.sh
cd ..

echo ""
echo "📤 Uploading to PyPI..."
python -m twine upload dist/* \
    --username __token__ \
    --password "$PYPI_API_TOKEN" \
    --verbose

echo ""
echo "✅ Published successfully!"
echo ""
echo "🎉 Users can now install with:"
echo "   pipx install ml-jupyter-mcp"
echo "   pip install ml-jupyter-mcp"
echo "   uv tool install ml-jupyter-mcp"
echo ""
echo "📊 View on PyPI: https://pypi.org/project/ml-jupyter-mcp/"
echo ""
echo "📝 To update Claude config for users:"
echo '   "jupyter-executor": {'
echo '     "command": "pipx run ml-jupyter-mcp"'
echo '   }'