# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Loan Manager.

Bundles the Streamlit application into a one-directory distribution.
Run:  pyinstaller LoanManager.spec
"""

import os
import importlib

from PyInstaller.building.api import COLLECT, EXE, PYZ
from PyInstaller.building.build_main import Analysis
from PyInstaller.utils.hooks import collect_data_files, copy_metadata

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = os.path.abspath(".")
ASSETS = os.path.join(ROOT, "assets")
ICON = os.path.join(ASSETS, "app_icon.ico")

# ---------------------------------------------------------------------------
# Data files from third-party packages
# ---------------------------------------------------------------------------
datas = []
datas += collect_data_files("streamlit")
datas += copy_metadata("streamlit")
datas += collect_data_files("altair")
datas += copy_metadata("altair")
datas += collect_data_files("plotly")
datas += copy_metadata("plotly")
datas += collect_data_files("pydeck")
datas += copy_metadata("pydeck")
datas += collect_data_files("pandas")
datas += copy_metadata("pandas")
datas += copy_metadata("packaging")

# ---------------------------------------------------------------------------
# Application files — bundled into the root of _MEIPASS
# ---------------------------------------------------------------------------
datas += [
    (os.path.join(ROOT, "app.py"), "."),
    (os.path.join(ROOT, "business_logic.py"), "."),
    (os.path.join(ROOT, "data_export.py"), "."),
    (os.path.join(ROOT, "db.py"), "."),
    (os.path.join(ROOT, "import_excel.py"), "."),
    (os.path.join(ROOT, "ui_theme.py"), "."),
    (os.path.join(ROOT, "pages"), "pages"),
    (os.path.join(ROOT, ".streamlit"), ".streamlit"),
]

# ---------------------------------------------------------------------------
# Hidden imports that PyInstaller cannot detect by analysis alone
# ---------------------------------------------------------------------------
hiddenimports = [
    "ui_theme",
    "streamlit",
    "streamlit.web.cli",
    "streamlit.web.bootstrap",
    "streamlit.runtime.scriptrunner",
    "streamlit.runtime.scriptrunner.script_runner",
    "altair",
    "plotly",
    "plotly.express",
    "plotly.graph_objects",
    "pydeck",
    "pandas",
    "openpyxl",
    "uvicorn",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "starlette",
    "watchdog",
    "watchdog.observers",
    "PIL",
    "PIL._tkinter_finder",
    "pyarrow",
]

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
a = Analysis(
    [os.path.join(ROOT, "launcher.py")],
    pathex=[ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "IPython", "notebook", "tkinter"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="LoanManager",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    icon=ICON if os.path.exists(ICON) else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="LoanManager",
)
