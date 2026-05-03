#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Building video_cut binary with Docker..."
echo "Container: debian:bookworm with Python 3.12"

docker run --rm \
  -v "$SCRIPT_DIR:/workspace" \
  -w /workspace \
  debian:bookworm \
  bash -c '
set -euo pipefail

echo "=== Installing build dependencies ==="
apt-get update
apt-get install -y --no-install-recommends \
  curl \
  git \
  ca-certificates \
  build-essential \
  libssl-dev \
  libffi-dev \
  zlib1g-dev \
  libbz2-dev \
  libreadline-dev \
  libsqlite3-dev

echo "=== Installing Python 3.12 via pyenv ==="
git clone --depth=1 https://github.com/pyenv/pyenv.git ~/.pyenv || true
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"

# Install Python 3.12 if not present
if ! pyenv versions | grep -q 3.12; then
  pyenv install 3.12.0
fi
pyenv local 3.12.0

echo "=== Installing Python packages ==="
pip install --upgrade pip setuptools wheel
pip install pyinstaller

echo "=== Installing video_cut and dependencies ==="
pip install -e /workspace

echo "=== Running PyInstaller ==="
cd /workspace
pyinstaller --clean video_cut.spec

echo "=== Build complete ==="
ls -lh dist/video_cut
'

echo "✓ Docker build complete!"
echo "Binary: dist/video_cut"
