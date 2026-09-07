"""build.py — One-step build pipeline for Loan Manager installer.

Usage:  python build.py

Steps:
  1. Generate application icon   (assets/app_icon.ico)
  2. Bundle with PyInstaller      (dist/LoanManager/)
  3. Compile Inno Setup installer (dist_installer/LoanManager_Setup.exe)
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
PYINSTALLER = ROOT / ".venv" / "Scripts" / "pyinstaller.exe"
ISCC = Path(os.environ.get(
    "ISCC_PATH",
    r"C:\Users\moses\AppData\Local\Programs\Inno Setup 6\ISCC.exe",
))

SPEC_FILE = ROOT / "LoanManager.spec"
ISS_FILE = ROOT / "installer.iss"
DIST_DIR = ROOT / "dist" / "LoanManager"
INSTALLER_DIR = ROOT / "dist_installer"
ICON_SCRIPT = ROOT / "assets" / "generate_icon.py"
ICON_FILE = ROOT / "assets" / "app_icon.ico"


def _run(cmd: list[str | Path], label: str) -> None:
    """Run a subprocess, printing a status banner."""
    print()
    print("=" * 60)
    print(f"  {label}")
    print("=" * 60)
    result = subprocess.run(
        [str(c) for c in cmd],
        cwd=str(ROOT),
    )
    if result.returncode != 0:
        print(f"\nERROR: {label} failed (exit code {result.returncode})")
        sys.exit(result.returncode)


def step_icon() -> None:
    """Generate the application icon."""
    if ICON_FILE.exists():
        print(f"Icon already exists: {ICON_FILE}")
        return
    python = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
    _run([python, str(ICON_SCRIPT)], "Step 1/3 : Generate Icon")


def step_pyinstaller() -> None:
    """Run PyInstaller to create the one-directory bundle."""
    # Clean previous build artifacts
    for d in [ROOT / "build", DIST_DIR]:
        if d.exists():
            shutil.rmtree(d)

    pyinstaller = str(PYINSTALLER) if PYINSTALLER.exists() else "pyinstaller"
    _run(
        [pyinstaller, "--noconfirm", str(SPEC_FILE)],
        "Step 2/3 : PyInstaller Bundle",
    )

    exe = DIST_DIR / "LoanManager.exe"
    if not exe.exists():
        print(f"\nERROR: Expected output not found: {exe}")
        sys.exit(1)
    print(f"\nPyInstaller output ready: {DIST_DIR}")


def step_inno_setup() -> None:
    """Compile the Inno Setup installer."""
    if not ISCC.exists():
        print(f"\nWARNING: Inno Setup compiler not found at {ISCC}")
        print("Skipping installer compilation.  You can install Inno Setup 6 and re-run,")
        print("or set the ISCC_PATH environment variable.")
        return

    INSTALLER_DIR.mkdir(parents=True, exist_ok=True)
    _run([str(ISCC), str(ISS_FILE)], "Step 3/3 : Inno Setup Installer")

    setup_exe = INSTALLER_DIR / "LoanManager_Setup.exe"
    if setup_exe.exists():
        size_mb = setup_exe.stat().st_size / (1024 * 1024)
        print(f"\nInstaller ready: {setup_exe}  ({size_mb:.1f} MB)")
    else:
        print(f"\nWARNING: Expected installer not found: {setup_exe}")


def main() -> None:
    print("Loan Manager — Build Pipeline")
    print(f"Project root: {ROOT}")

    step_icon()
    step_pyinstaller()
    step_inno_setup()

    print()
    print("=" * 60)
    print("  BUILD COMPLETE")
    print("=" * 60)
    setup = INSTALLER_DIR / "LoanManager_Setup.exe"
    if setup.exists():
        print(f"  Installer: {setup}")
    print(f"  Portable:  {DIST_DIR / 'LoanManager.exe'}")
    print()


if __name__ == "__main__":
    main()
