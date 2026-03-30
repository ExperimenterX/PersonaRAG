# PersonaRAG Benchmark Evaluation Script (Windows PowerShell)
# Runs external benchmark evaluation and saves artifacts into server\output by default.

param(
    [Parameter(Position=0)]
    [ValidateSet("hotpotqa", "nq", "triviaqa", "multireqa", "custom")]
    [string]$Benchmark = "hotpotqa",

    [Parameter(Position=1)]
    [ValidateSet("dense_only", "bm25_only", "hybrid", "hybrid_rerank", "all")]
    [string]$Mode = "all",

    [int]$Limit = 1000,
    [string]$Split = "validation",
    [string]$DatasetName = "",
    [string]$DatasetConfig = "",
    [string]$InputFile = "",
    [string]$OutputDir = "server\output",
    [int]$PrintExamples = 3
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PersonaRAG Benchmark Evaluation Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Benchmark: $Benchmark" -ForegroundColor Yellow
Write-Host "Mode:      $Mode" -ForegroundColor Yellow
Write-Host "Limit:     $Limit" -ForegroundColor Yellow
Write-Host "Split:     $Split" -ForegroundColor Yellow

$resolvedOutputDir = if ([System.IO.Path]::IsPathRooted($OutputDir)) {
    $OutputDir
} else {
    Join-Path (Get-Location) $OutputDir
}

Write-Host "Output:    $resolvedOutputDir" -ForegroundColor Yellow
Write-Host ""

$pythonExe = "server\venv311\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Host "Error: Python executable not found at $pythonExe" -ForegroundColor Red
    Write-Host "Please run setup first to create venv311." -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path $resolvedOutputDir)) {
    New-Item -ItemType Directory -Path $resolvedOutputDir -Force | Out-Null
}

$env:PYTHONIOENCODING = "utf-8"

$argsList = @(
    "-m", "app.eval.run_benchmark_eval",
    "--benchmark", $Benchmark,
    "--mode", $Mode,
    "--limit", $Limit,
    "--split", $Split,
    "--output-dir", $resolvedOutputDir,
    "--print-examples", $PrintExamples
)

if ($DatasetName -ne "") {
    $argsList += @("--dataset-name", $DatasetName)
}
if ($DatasetConfig -ne "") {
    $argsList += @("--dataset-config", $DatasetConfig)
}
if ($InputFile -ne "") {
    $argsList += @("--input-file", $InputFile)
}

Push-Location server
& "..\$pythonExe" @argsList
$exitCode = $LASTEXITCODE
Pop-Location

if ($exitCode -eq 0) {
    Write-Host "" 
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Benchmark evaluation completed!" -ForegroundColor Green
    Write-Host "Artifacts saved under: $resolvedOutputDir" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Benchmark evaluation failed!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
}

exit $exitCode
