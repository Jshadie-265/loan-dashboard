from datetime import date

import streamlit as st

from data_export import create_csv_backup, create_excel_export
from db import get_connection, init_db

init_db()
conn = get_connection()

st.title("🗃️ Backup & export")
st.caption("Download a portable Excel copy of your records or an archival CSV backup. You can also export directly from the Dashboard.")

counts = {
    "Customers": conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0],
    "Loans": conn.execute("SELECT COUNT(*) FROM loans").fetchone()[0],
    "Repayments": conn.execute("SELECT COUNT(*) FROM repayments").fetchone()[0],
    "Capital transactions": conn.execute("SELECT COUNT(*) FROM capital").fetchone()[0],
}
columns = st.columns(4)
for column, (label, count) in zip(columns, counts.items()):
    column.metric(label, count)

st.divider()

st.subheader("📊 Consolidated Excel export (.xlsx)")
st.write("Download all registers in a **single Excel workbook** with separate tabs for **Dashboard**, **Customers**, **Loans**, **Repayments**, and **Capital**.")


def get_excel_bytes() -> bytes:
    c = get_connection()
    try:
        return create_excel_export(c)
    finally:
        c.close()


st.download_button(
    "📥 Download consolidated Excel workbook (.xlsx)",
    data=get_excel_bytes,
    file_name=f"Loan_Manager_Export_{date.today().isoformat()}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    type="primary",
    key="backup_excel_download",
)

st.divider()

with st.expander("🗜️ Archival CSV backup (.zip)"):
    st.caption("Contains raw UTF-8 CSV files per register for database administration or migration.")

    def get_csv_zip_bytes() -> bytes:
        c = get_connection()
        try:
            return create_csv_backup(c)
        finally:
            c.close()

    st.download_button(
        "Download CSV archive (.zip)",
        data=get_csv_zip_bytes,
        file_name=f"loan-manager-backup-{date.today().isoformat()}.zip",
        mime="application/zip",
        key="backup_zip_download",
    )

st.info("💡 You can open the exported Excel workbook in Microsoft Excel or Google Sheets. Any edits made in the workbook can be re-imported seamlessly via the **Import data** page.")
conn.close()


