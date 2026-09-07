"""
app.py — Loan Manager entry point and navigation router.

Run with:  streamlit run app.py
On first run, migrate your existing workbook first:  python import_excel.py Loan.xlsx
"""

import streamlit as st

from db import init_db
from ui_theme import apply_common_styles

# ---------------------------------------------------------------------------
# Global page config — set ONCE before anything else
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Loan Manager", page_icon="💰", layout="wide")
apply_common_styles()
init_db()

# ---------------------------------------------------------------------------
# Navigation — st.navigation replaces the pages/ directory auto-discovery.
# Each page gets an icon visible in the sidebar (and when collapsed).
# ---------------------------------------------------------------------------
pg = st.navigation(
    [
        st.Page("pages/0_Dashboard.py",      title="Dashboard",      icon="📊", default=True),
        st.Page("pages/1_Customers.py",      title="Customers",      icon="👥"),
        st.Page("pages/2_Loans.py",          title="Loans",          icon="📄"),
        st.Page("pages/3_Repayments.py",     title="Repayments",     icon="💵"),
        st.Page("pages/4_Capital.py",        title="Capital",        icon="🏦"),
        st.Page("pages/5_Import_Data.py",    title="Import Data",    icon="📥"),
        st.Page("pages/6_Backup_Export.py",  title="Backup & Export", icon="🗃️"),
    ],
    expanded=True,
)

pg.run()
