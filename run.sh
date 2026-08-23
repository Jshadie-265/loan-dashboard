#!/usr/bin/env sh
set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
venv_python="$project_root/.venv/bin/python"
port="${1:-8501}"

if [ ! -x "$venv_python" ]; then
  echo "Creating Python virtual environment..."
  python3 -m venv "$project_root/.venv"
fi

echo "Installing application dependencies..."
"$venv_python" -m pip install --upgrade pip
"$venv_python" -m pip install -r "$project_root/requirements.txt"

echo "Starting Loan Manager at http://localhost:$port"
exec "$venv_python" -m streamlit run "$project_root/app.py" --server.port "$port"
