#!/bin/bash
# Build script for ml-jupyter-mcp package

set -e  # Exit on error

echo "🧹 Cleaning previous builds..."
rm -rf ../dist ../build ../src/*.egg-info

echo "📦 Building package..."
cd ..
python -m build

echo "✅ Build complete!"
echo "📁 Built packages:"
ls -la dist/

echo ""
echo "📊 Package contents:"
python -m zipfile -l dist/*.whl | head -20

echo ""
echo "✨ Ready to publish! Run ./deploy/publish.sh to upload to PyPI"