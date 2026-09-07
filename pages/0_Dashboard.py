"""Dashboard page — live business summary."""

import io
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from business_logic import format_mwk, get_dashboard_metrics, get_loans_df
from data_export import create_excel_export
from db import get_connection, init_db
from import_excel import import_workbooks

init_db()
conn = get_connection()

st.title("💰 Loan Manager")
st.caption("Live business summary — recalculated from the database on every load.")
if summary := st.session_state.pop("dashboard_import_summary", None):
    st.success(summary)

import_column, export_column = st.columns(2)
with import_column:
    with st.expander("📥 Import and consolidate Excel data"):
        uploaded_files = st.file_uploader("Choose one or more Excel (.xlsx) files", type=["xlsx"], accept_multiple_files=True, key="dashboard_import")
        if st.button("Import and consolidate files", type="primary", disabled=not uploaded_files):
            try:
                with st.spinner("Loading customers, loans, repayments, and capital…"):
                    results = import_workbooks(io.BytesIO(file.getvalue()) for file in uploaded_files)
                st.session_state["dashboard_import_summary"] = (
                    f"Consolidation complete — {len(uploaded_files)} file(s) processed: "
                    + ", ".join(f"{count} {name}" for name, count in results.items())
                    + "."
                )
                conn.close()
                st.rerun()
            except ValueError as error:
                st.error(f"Validation error: {error}")
            except Exception as error:
                st.error(f"The workbook could not be loaded: {error}. Confirm it is a valid Excel file and try again.")

with export_column:
    with st.expander("📤 Export consolidated workbook"):
        st.write("Download all registers in a **single Excel workbook (.xlsx)** with tabs for Dashboard, Customers, Loans, Repayments, and Capital.")

        def get_dash_excel() -> bytes:
            c = get_connection()
            try:
                return create_excel_export(c)
            finally:
                c.close()

        st.download_button(
            "📥 Download Excel workbook (.xlsx)",
            data=get_dash_excel,
            file_name=f"Loan_Manager_Export_{date.today().isoformat()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            key="dash_download_excel",
        )

metrics = get_dashboard_metrics(conn)
loans_df = get_loans_df(conn)

# --- KPI cards -----------------------------------------------------------
row1 = st.columns(3)
row1[0].metric("Total Capital", format_mwk(metrics["total_capital"]))
row1[1].metric("Money Loaned", format_mwk(metrics["total_loaned"]))
row1[2].metric("Available Cash", format_mwk(metrics["available_cash"]))

row2 = st.columns(3)
row2[0].metric("Outstanding Balance", format_mwk(metrics["outstanding_balance"]))
row2[1].metric("Interest Expected", format_mwk(metrics["total_interest_expected"]))
row2[2].metric("Profit Earned", format_mwk(metrics["profit_earned"]))

row3 = st.columns(3)
row3[0].metric("Active Loans", metrics["active_count"])
row3[1].metric("Paid Loans", metrics["paid_count"])
row3[2].metric("Overdue Loans", metrics["overdue_count"])

st.divider()

if loans_df.empty:
    st.info("No loans on file yet. Add a customer and issue a loan from the sidebar.")
else:
    # --- Charts ------------------------------------------------------------
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Loans by status")
        status_counts = loans_df["status"].value_counts().reset_index()
        status_counts.columns = ["status", "count"]
        fig = px.pie(
            status_counts, names="status", values="count", hole=0.5,
            color="status",
            color_discrete_map={"Active": "#146356", "Paid": "#8AA399", "Overdue": "#C0533E"},
        )
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), showlegend=True)
        st.plotly_chart(fig, width="stretch")

    with chart_col2:
        st.subheader("Exposure by borrower")
        exposure = (
            loans_df.groupby("borrower")["balance"].sum().sort_values(ascending=True).reset_index()
        )
        fig2 = px.bar(exposure, x="balance", y="borrower", orientation="h",
                       labels={"balance": "Outstanding balance (MWK)", "borrower": ""},
                       color_discrete_sequence=["#146356"])
        fig2.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig2, width="stretch")

    st.subheader("Disbursements over time")
    by_date = loans_df.groupby("date_taken")["principal"].sum().reset_index().sort_values("date_taken")
    by_date["cumulative"] = by_date["principal"].cumsum()
    fig3 = px.bar(by_date, x="date_taken", y="principal",
                  labels={"date_taken": "Date", "principal": "Principal issued (MWK)"},
                  color_discrete_sequence=["#146356"])
    st.plotly_chart(fig3, width="stretch")

    # --- Overdue aging -------------------------------------------------
    overdue = loans_df[loans_df["status"] == "Overdue"].copy()
    if not overdue.empty:
        st.subheader("⚠️ Overdue loans")
        overdue["due_date_parsed"] = pd.to_datetime(overdue["due_date"])
        overdue["days_overdue"] = (pd.Timestamp(date.today()) - overdue["due_date_parsed"]).dt.days
        overdue = overdue.sort_values("days_overdue", ascending=False)
        st.dataframe(
            overdue[["loan_id", "borrower", "due_date", "days_overdue", "balance"]].rename(
                columns={"loan_id": "Loan ID", "borrower": "Borrower", "due_date": "Due date",
                         "days_overdue": "Days overdue", "balance": "Balance (MWK)"}
            ),
            width="stretch", hide_index=True,
        )

conn.close()
