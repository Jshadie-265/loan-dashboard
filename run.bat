@echo off
setlocal

set "PROJECT_ROOT=%~dp0"
set "VENV_PYTHON=%PROJECT_ROOT%.venv\Scripts\python.exe"
set "PORT=%~1"
if "%PORT%"=="" set "PORT=8501"

if not exist "%VENV_PYTHON%" (
    echo Creating Python virtual environment...
    python -m venv "%PROJECT_ROOT%.venv"
)

echo Installing application dependencies...
"%VENV_PYTHON%" -m pip install --upgrade pip
"%VENV_PYTHON%" -m pip install -r "%PROJECT_ROOT%requirements.txt"

echo Starting Loan Manager at http://localhost:%PORT%
"%VENV_PYTHON%" -m streamlit run "%PROJECT_ROOT%app.py" --server.port %PORT%
