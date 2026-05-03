#!/bin/bash
set -euo pipefail

echo "Installing PyInstaller..."
pip install pyinstaller

echo "Building video_cut binary..."
pyinstaller --clean video_cut.spec

echo "✓ Build complete!"
echo "Binary: dist/video_cut"
