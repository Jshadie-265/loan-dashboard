import io

import streamlit as st

from import_excel import import_workbooks

st.title("📥 Import workbook data")
st.caption("Upload one or more Excel (.xlsx) workbooks to consolidate their records into this app. Existing records are updated with newly supplied information; conflicting IDs from other sources receive new IDs.")

uploaded_files = st.file_uploader("Choose Excel (.xlsx) workbooks", type=["xlsx"], accept_multiple_files=True)
if uploaded_files:
    st.info("The import adds and consolidates customers, capital, loans, and repayments. It does not delete data already in the app.")
    if st.button("Import and consolidate files", type="primary"):
        try:
            with st.spinner("Importing and consolidating workbook data…"):
                results = import_workbooks(io.BytesIO(file.getvalue()) for file in uploaded_files)
            st.success(f"Consolidation complete — {len(uploaded_files)} file(s) processed: " + ", ".join(f"{count} {name}" for name, count in results.items()) + ".")
        except ValueError as error:
            st.error(f"Validation error: {error}")
        except Exception as error:
            st.error(f"The workbook could not be imported: {error}. Confirm it is a valid Excel workbook and try again.")
