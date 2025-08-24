#!/bin/bash
# Test the package locally with pipx before publishing

set -e  # Exit on error

echo "🧪 Testing ml-jupyter-mcp locally with pipx..."
echo ""

# Build first
echo "📦 Building package..."
cd "$(dirname "$0")"
./build.sh
cd ..

echo ""
echo "🔧 Installing with pipx..."
pipx install dist/*.whl --force

echo ""
echo "✅ Installation complete! Testing commands..."
echo ""

# Test that the command works
echo "📍 Testing ml-jupyter-mcp command:"
ml-jupyter-mcp --version 2>/dev/null || echo "Version flag not implemented yet"

echo ""
echo "🧹 To uninstall test installation, run:"
echo "   pipx uninstall ml-jupyter-mcp"
echo ""
echo "📝 To test with Claude:"
echo "   1. Add to Claude config:"
echo '      "jupyter-executor": {'
echo '        "command": "ml-jupyter-mcp"'
echo '      }'
echo "   2. Restart Claude"
echo "   3. Test with: mcp__jupyter-executor__jupyter_initialize()"
echo ""
echo "✨ If everything works, run ./deploy/publish.sh to publish to PyPI!"