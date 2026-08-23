from datetime import date

import streamlit as st

from data_export import create_csv_backup
from db import get_connection, init_db


st.set_page_config(page_title="Backup & export | Loan Manager", page_icon="🗃️", layout="wide")
init_db()
conn = get_connection()

st.title("🗃️ Backup & export")
st.caption("Download a portable copy of your current changes before major edits or at the end of each business day. You can also export directly from the Dashboard.")

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
st.subheader("Export current changes")
st.write("First prepare the export, then press the download button. Visiting this page never starts a download.")
if st.button("Prepare export", type="primary"):
    st.session_state["prepared_backup"] = create_csv_backup(conn)

if backup := st.session_state.get("prepared_backup"):
    st.download_button(
        "Download prepared backup (.zip)",
        data=backup,
        file_name=f"loan-manager-backup-{date.today().isoformat()}.zip",
        mime="application/zip",
    )

st.info("To move the complete app to another computer, install the repository there and keep this backup together with your original Loan.xlsx file.")
conn.close()
