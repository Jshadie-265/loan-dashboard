from datetime import date, timedelta

import pandas as pd
import streamlit as st

from business_logic import compute_loan_terms, format_mwk, get_loans_df
from db import get_connection, init_db, next_id

st.set_page_config(page_title="Loans", page_icon="📄", layout="wide")
init_db()
conn = get_connection()

st.title("📄 Loans")

PERIOD_DAYS = {"2 Weeks": 14, "1 Month": 30, "3 Months": 90}

customers = pd.read_sql_query("SELECT customer_id, full_name FROM customers ORDER BY full_name", conn)

with st.expander("➕ Issue a new loan", expanded=customers.empty):
    if customers.empty:
        st.warning("Add a customer first, on the Customers page.")
    else:
        c1, c2 = st.columns(2)
        borrower_name = c1.selectbox("Borrower", customers["full_name"])
        date_taken = c2.date_input("Date taken", value=date.today())

        c3, c4 = st.columns(2)
        period = c3.selectbox("Period", list(PERIOD_DAYS.keys()) + ["Custom"])
        if period == "Custom":
            due_date = c4.date_input("Due date", value=date_taken + timedelta(days=30))
        else:
            due_date = date_taken + timedelta(days=PERIOD_DAYS[period])
            c4.date_input("Due date (auto)", value=due_date, disabled=True)

        c5, c6 = st.columns(2)
        principal = c5.number_input("Principal (MWK)", min_value=0.0, step=10000.0, format="%.2f")
        rate_pct = c6.number_input("Interest rate (%)", min_value=0.0, step=1.0, format="%.1f")
        rate = rate_pct / 100

        interest, total_due = compute_loan_terms(principal, rate)
        st.caption(f"Interest: **{format_mwk(interest)}**  •  Total due: **{format_mwk(total_due)}**")

        c7, c8 = st.columns(2)
        bank = c7.text_input("Bank")
        account = c8.text_input("Account number")
        reference = st.text_input("Reference")
        notes = st.text_area("Notes")

        if st.button("Issue loan", type="primary"):
            if principal <= 0:
                st.error("Principal must be greater than zero.")
            else:
                customer_id = customers.loc[customers["full_name"] == borrower_name, "customer_id"].iloc[0]
                loan_id = next_id(conn, "loans", "loan_id", "L", width=3)
                conn.execute(
                    """INSERT INTO loans (loan_id, customer_id, date_taken, period, due_date,
                                           principal, rate, interest, total_due, bank, account,
                                           reference, notes)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (loan_id, customer_id, date_taken.isoformat(), period, due_date.isoformat(),
                     principal, rate, interest, total_due, bank, account, reference, notes),
                )
                conn.commit()
                st.success(f"Issued {loan_id} to {borrower_name} for {format_mwk(principal)}")
                st.rerun()

st.subheader("Loan register")
df = get_loans_df(conn)
if df.empty:
    st.info("No loans yet.")
else:
    f1, f2 = st.columns([1, 2])
    status_filter = f1.multiselect("Status", ["Active", "Paid", "Overdue"], default=["Active", "Paid", "Overdue"])
    borrower_filter = f2.multiselect("Borrower", sorted(df["borrower"].unique()))

    view = df[df["status"].isin(status_filter)]
    if borrower_filter:
        view = view[view["borrower"].isin(borrower_filter)]

    display = view[["loan_id", "borrower", "date_taken", "due_date", "principal",
                     "rate", "interest", "total_due", "amount_paid", "balance", "status"]].rename(
        columns={"loan_id": "Loan ID", "borrower": "Borrower", "date_taken": "Date taken",
                 "due_date": "Due date", "principal": "Principal", "rate": "Rate",
                 "interest": "Interest", "total_due": "Total due", "amount_paid": "Paid",
                 "balance": "Balance", "status": "Status"}
    )
    st.dataframe(display, use_container_width=True, hide_index=True)

conn.close()
