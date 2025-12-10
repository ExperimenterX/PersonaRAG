# PersonaRAG Evaluation Script (Windows PowerShell)
# This script runs the evaluation suite on the PersonaRAG system

param(
    [Parameter(Position=0)]
    [ValidateSet("dense_only", "bm25_only", "hybrid", "hybrid_rerank", "all")]
    [string]$Mode = "hybrid_rerank"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PersonaRAG Evaluation Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$venvPath = "server\venv311"
$pythonExe = "$venvPath\Scripts\python.exe"

# Check if virtual environment exists
if (-not (Test-Path $venvPath)) {
    Write-Host "Error: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run setup.ps1 first:" -ForegroundColor Yellow
    Write-Host "  .\setup.ps1" -ForegroundColor White
    exit 1
}

# Change to server directory
Push-Location server

Write-Host "Running evaluation in mode: $Mode" -ForegroundColor Yellow
Write-Host ""

if ($Mode -eq "all") {
    Write-Host "This will run all 4 evaluation modes sequentially:" -ForegroundColor Cyan
    Write-Host "  1. dense_only" -ForegroundColor Gray
    Write-Host "  2. bm25_only" -ForegroundColor Gray
    Write-Host "  3. hybrid" -ForegroundColor Gray
    Write-Host "  4. hybrid_rerank" -ForegroundColor Gray
    Write-Host ""
    Write-Host "This may take several minutes..." -ForegroundColor Yellow
    Write-Host ""
}

& "..\$pythonExe" -m app.eval.run_eval --mode $Mode

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Evaluation completed successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Evaluation failed!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
}

Pop-Location
