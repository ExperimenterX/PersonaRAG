#!/bin/bash
# PersonaRAG Evaluation Script (Linux/Mac)
# This script runs the evaluation suite on the PersonaRAG system

MODE="${1:-hybrid_rerank}"

# Validate mode
case "$MODE" in
    dense_only|bm25_only|hybrid|hybrid_rerank|all)
        ;;
    *)
        echo "Error: Invalid mode '$MODE'"
        echo "Valid modes: dense_only, bm25_only, hybrid, hybrid_rerank, all"
        echo ""
        echo "Usage: ./eval.sh [mode]"
        echo "Examples:"
        echo "  ./eval.sh                    # Run default mode (hybrid_rerank)"
        echo "  ./eval.sh dense_only         # Test dense retrieval only"
        echo "  ./eval.sh bm25_only          # Test BM25 retrieval only"
        echo "  ./eval.sh hybrid             # Test hybrid (no reranking)"
        echo "  ./eval.sh hybrid_rerank      # Test full pipeline"
        echo "  ./eval.sh all                # Run all modes for comparison"
        exit 1
        ;;
esac

echo "========================================"
echo "PersonaRAG Evaluation Script"
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

echo "Running evaluation in mode: $MODE"
echo ""

if [ "$MODE" = "all" ]; then
    echo "This will run all 4 evaluation modes sequentially:"
    echo "  1. dense_only"
    echo "  2. bm25_only"
    echo "  3. hybrid"
    echo "  4. hybrid_rerank"
    echo ""
    echo "This may take several minutes..."
    echo ""
fi

"../$PYTHON_EXE" -m app.eval.run_eval --mode "$MODE"

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "Evaluation completed successfully!"
    echo "========================================"
else
    echo ""
    echo "========================================"
    echo "Evaluation failed!"
    echo "========================================"
    exit 1
fi

cd ..
