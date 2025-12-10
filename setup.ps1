# PersonaRAG Setup Script (Windows PowerShell)
# This script sets up the complete PersonaRAG environment

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PersonaRAG Setup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python 3.11 is available
Write-Host "[1/4] Checking Python 3.11..." -ForegroundColor Yellow
$pythonCmd = Get-Command py -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "Error: 'py' command not found. Please install Python 3.11" -ForegroundColor Red
    exit 1
}

$pythonVersion = py -3.11 --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Python 3.11 not found. Please install Python 3.11" -ForegroundColor Red
    exit 1
}
Write-Host "Found: $pythonVersion" -ForegroundColor Green
Write-Host ""

# Create Python virtual environment
Write-Host "[2/4] Creating Python virtual environment (venv311)..." -ForegroundColor Yellow
$venvPath = "server\venv311"
if (Test-Path $venvPath) {
    Write-Host "Virtual environment already exists. Skipping..." -ForegroundColor Gray
} else {
    py -3.11 -m venv $venvPath
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Virtual environment created successfully!" -ForegroundColor Green
    } else {
        Write-Host "Error: Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
}
Write-Host ""

# Install Python dependencies
Write-Host "[3/4] Installing Python dependencies..." -ForegroundColor Yellow
& "$venvPath\Scripts\python.exe" -m pip install --upgrade pip
& "$venvPath\Scripts\pip.exe" install -r server\requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "Python dependencies installed successfully!" -ForegroundColor Green
} else {
    Write-Host "Error: Failed to install Python dependencies" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Install Node.js dependencies and build frontend
Write-Host "[4/4] Setting up frontend..." -ForegroundColor Yellow
Push-Location client

# Check if Node.js is installed
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeCmd) {
    Write-Host "Error: Node.js not found. Please install Node.js from https://nodejs.org/" -ForegroundColor Red
    Pop-Location
    exit 1
}

$nodeVersion = node --version
Write-Host "Found Node.js: $nodeVersion" -ForegroundColor Green

# Install dependencies
Write-Host "Installing Node.js dependencies..." -ForegroundColor Yellow
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to install Node.js dependencies" -ForegroundColor Red
    Pop-Location
    exit 1
}

# Build frontend
Write-Host "Building frontend (dist)..." -ForegroundColor Yellow
npm run build
if ($LASTEXITCODE -eq 0) {
    Write-Host "Frontend built successfully!" -ForegroundColor Green
} else {
    Write-Host "Error: Failed to build frontend" -ForegroundColor Red
    Pop-Location
    exit 1
}

Pop-Location
Write-Host ""

# Success message
Write-Host "========================================" -ForegroundColor Green
Write-Host "Setup completed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Run: .\start.ps1" -ForegroundColor White
Write-Host "   This will build the index and start the server" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Open: http://localhost:8000" -ForegroundColor White
Write-Host "   Access the PersonaRAG application" -ForegroundColor Gray
Write-Host ""
