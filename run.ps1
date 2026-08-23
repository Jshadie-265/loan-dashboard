param(
    [int]$Port = 8501
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating Python virtual environment..."
    python -m venv (Join-Path $projectRoot ".venv")
}

Write-Host "Installing application dependencies..."
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $projectRoot "requirements.txt")

Write-Host "Starting Loan Manager at http://localhost:$Port"
& $venvPython -m streamlit run (Join-Path $projectRoot "app.py") --server.port $Port
