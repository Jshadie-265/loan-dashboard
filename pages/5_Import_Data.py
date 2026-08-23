import io

import streamlit as st

from import_excel import import_workbooks

st.set_page_config(page_title="Import data | Loan Manager", page_icon="📥", layout="wide")
st.title("📥 Import workbook data")
st.caption("Choose several Loan.xlsx files to consolidate their records into this app. Re-importing the same file skips matching source records; conflicting IDs from different files are kept using new local IDs.")

uploaded_files = st.file_uploader("Choose Loan.xlsx files", type=["xlsx"], accept_multiple_files=True)
if uploaded_files:
    st.info("The import adds and consolidates customers, capital, loans, and repayments. It does not delete data already in the app.")
    if st.button("Import and consolidate files", type="primary"):
        try:
            with st.spinner("Importing workbook data…"):
                results = import_workbooks(io.BytesIO(file.getvalue()) for file in uploaded_files)
            st.success(f"Consolidation complete — {len(uploaded_files)} file(s) processed: " + ", ".join(f"{count} {name}" for name, count in results.items()) + ".")
        except ValueError as error:
            st.error(str(error))
        except Exception:
            st.error("The workbook could not be imported. Confirm it is a valid Loan.xlsx file and try again.")
