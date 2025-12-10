#!/bin/bash
# PersonaRAG Start Script (Linux/Mac)
# This script builds the index and starts the server

echo "========================================"
echo "PersonaRAG Start Script"
echo "========================================"
echo ""

VENV_PATH="server/venv311"
PYTHON_EXE="$VENV_PATH/bin/python"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Error: Virtual environment not found!"
    echo "Please run setup.sh first:"
    echo "  ./setup.sh"
    exit 1
fi

# Change to server directory
cd server || exit 1

echo "[1/2] Building FAISS index..."
echo "This may take a minute on first run..."
"../$PYTHON_EXE" -m app.indexing.build_index
if [ $? -ne 0 ]; then
    echo "Error: Failed to build index"
    exit 1
fi
echo "Index built successfully!"
echo ""

echo "[2/2] Starting FastAPI server..."
echo "Server will be available at: http://localhost:8000"
echo "Press Ctrl+C to stop the server"
echo ""

"../$PYTHON_EXE" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

cd ..
