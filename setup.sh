#!/bin/bash
# PersonaRAG Setup Script (Linux/Mac)
# This script sets up the complete PersonaRAG environment

echo "========================================"
echo "PersonaRAG Setup Script"
echo "========================================"
echo ""

# Check if Python 3.11 is available
echo "[1/4] Checking Python 3.11..."
if ! command -v python3.11 &> /dev/null; then
    echo "Error: Python 3.11 not found. Please install Python 3.11"
    exit 1
fi

PYTHON_VERSION=$(python3.11 --version)
echo "Found: $PYTHON_VERSION"
echo ""

# Create Python virtual environment
echo "[2/4] Creating Python virtual environment (venv311)..."
VENV_PATH="server/venv311"
if [ -d "$VENV_PATH" ]; then
    echo "Virtual environment already exists. Skipping..."
else
    python3.11 -m venv "$VENV_PATH"
    if [ $? -eq 0 ]; then
        echo "Virtual environment created successfully!"
    else
        echo "Error: Failed to create virtual environment"
        exit 1
    fi
fi
echo ""

# Install Python dependencies
echo "[3/4] Installing Python dependencies..."
"$VENV_PATH/bin/python" -m pip install --upgrade pip
"$VENV_PATH/bin/pip" install -r server/requirements.txt
if [ $? -eq 0 ]; then
    echo "Python dependencies installed successfully!"
else
    echo "Error: Failed to install Python dependencies"
    exit 1
fi
echo ""

# Install Node.js dependencies and build frontend
echo "[4/4] Setting up frontend..."
cd client || exit 1

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Error: Node.js not found. Please install Node.js from https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node --version)
echo "Found Node.js: $NODE_VERSION"

# Install dependencies
echo "Installing Node.js dependencies..."
npm install
if [ $? -ne 0 ]; then
    echo "Error: Failed to install Node.js dependencies"
    exit 1
fi

# Build frontend
echo "Building frontend (dist)..."
npm run build
if [ $? -eq 0 ]; then
    echo "Frontend built successfully!"
else
    echo "Error: Failed to build frontend"
    exit 1
fi

cd ..
echo ""

# Success message
echo "========================================"
echo "Setup completed successfully!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Run: ./start.sh"
echo "   This will build the index and start the server"
echo ""
echo "2. Open: http://localhost:8000"
echo "   Access the PersonaRAG application"
echo ""
