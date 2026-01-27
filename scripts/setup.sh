#!/bin/bash

# Doraemon Code Setup Script
# This script automates the installation of dependencies and environment setup.

set -e

echo "🚀 Initializing Doraemon Code environment..."

# 1. Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Python version: $PYTHON_VERSION"

# 2. Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# 3. Install/Update dependencies
echo "Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"

# 4. Initialize configuration directory
if [ ! -d ".doraemon" ]; then
    echo "Creating .doraemon directory..."
    mkdir -p .doraemon
fi

# 5. Create basic folders
mkdir -p materials drafts

echo "✅ Setup complete! You can now run Doraemon Code using 'dora start'."
echo "To activate the environment manually, run: source venv/bin/activate"
