"""Loan Manager — Desktop launcher for the packaged application.

This is the entrypoint that PyInstaller compiles.  It:
1. Creates (or reuses) a persistent database in %APPDATA%/LoanManager/.
   On the very first launch the database is empty — only the schema is
   initialised via ``init_db()``.  No sample data is bundled.
2. Finds an available local port (starting at 8501).
3. Launches the default web browser once the Streamlit server is healthy.
4. Starts Streamlit in the *main* thread (required for signal handling).
"""

from __future__ import annotations

import ctypes
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def _is_frozen() -> bool:
    """Return True when running inside a PyInstaller bundle."""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def _bundle_dir() -> Path:
    """Return the directory that contains the bundled application files."""
    if _is_frozen():
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent


def _app_data_dir() -> Path:
    """Return (and create) the persistent user data directory."""
    base = Path(os.environ.get("APPDATA", Path.home()))
    data_dir = base / "LoanManager"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


# ---------------------------------------------------------------------------
# Database bootstrap — empty on first run
# ---------------------------------------------------------------------------

def _setup_database() -> Path:
    """Ensure the user's database exists.  Creates an *empty* one on first run."""
    db_path = _app_data_dir() / "loan_app.db"
    os.environ["LOAN_APP_DB"] = str(db_path)

    # Import *after* setting the env var so db.py picks it up
    # noinspection PyPep8Naming
    from db import init_db  # noqa: E402

    init_db(db_path)
    return db_path


# ---------------------------------------------------------------------------
# Networking
# ---------------------------------------------------------------------------

def _find_free_port(start: int = 8501, attempts: int = 100) -> int:
    """Return the first available TCP port starting from *start*."""
    for port in range(start, start + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("Could not find a free port")


# ---------------------------------------------------------------------------
# Browser auto-open
# ---------------------------------------------------------------------------

def _open_browser_when_ready(port: int, timeout: float = 30.0) -> None:
    """Poll the local Streamlit server and open the browser once it responds."""
    url = f"http://localhost:{port}"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(url, timeout=2)
            # Use subprocess so it works reliably on Windows
            subprocess.Popen(["cmd", "/c", "start", "", url],
                             creationflags=subprocess.CREATE_NO_WINDOW)
            return
        except Exception:
            time.sleep(0.5)
    # If we never got a response, give up silently.


# ---------------------------------------------------------------------------
# Console banner
# ---------------------------------------------------------------------------

def _set_console_title(title: str) -> None:
    try:
        ctypes.windll.kernel32.SetConsoleTitleW(title)  # type: ignore[attr-defined]
    except Exception:
        pass


def _print_banner(port: int) -> None:
    _set_console_title("Loan Manager")
    print()
    print("=" * 52)
    print("   💰  Loan Manager")
    print("=" * 52)
    print(f"   Running at  http://localhost:{port}")
    print()
    print("   Your browser will open automatically.")
    print("   To stop the server, close this window")
    print("   or press  Ctrl+C.")
    print("=" * 52)
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # 1. Setup paths — make bundled files discoverable
    bundle = _bundle_dir()
    os.chdir(bundle)

    # Add bundle dir to sys.path so Python finds app modules
    if str(bundle) not in sys.path:
        sys.path.insert(0, str(bundle))

    # 2. Database
    db_path = _setup_database()
    print(f"Database: {db_path}")

    # 3. Networking
    port = _find_free_port()
    _print_banner(port)

    # 4. Browser auto-open (background thread — no signal issues)
    t = threading.Thread(target=_open_browser_when_ready, args=(port,), daemon=True)
    t.start()

    # 5. Start Streamlit in the main thread
    app_script = str(bundle / "app.py")
    sys.argv = [
        "streamlit", "run", app_script,
        "--server.port", str(port),
        "--server.headless", "true",
        "--server.address", "localhost",
        "--browser.gatherUsageStats", "false",
        "--global.developmentMode", "false",
        "--client.toolbarMode", "viewer",
    ]

    from streamlit.web.cli import main as st_main
    st_main()


if __name__ == "__main__":
    main()
