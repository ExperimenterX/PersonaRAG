# PersonaRAG Start Script (Windows PowerShell)
# This script builds the index and starts the server

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PersonaRAG Start Script" -ForegroundColor Cyan
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

Write-Host "[1/2] Building FAISS index..." -ForegroundColor Yellow
Write-Host "This may take a minute on first run..." -ForegroundColor Gray
& "..\$pythonExe" -m app.indexing.build_index
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to build index" -ForegroundColor Red
    Pop-Location
    exit 1
}
Write-Host "Index built successfully!" -ForegroundColor Green
Write-Host ""

Write-Host "[2/2] Starting FastAPI server..." -ForegroundColor Yellow
Write-Host "Server will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host ""

& "..\$pythonExe" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Pop-Location
