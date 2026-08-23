from datetime import date

import pandas as pd
import streamlit as st

from business_logic import format_mwk, get_loans_df, get_repayments_df
from db import get_connection, init_db, next_id

st.set_page_config(page_title="Repayments | Loan Manager", page_icon="💵", layout="wide")
init_db()
conn = get_connection()
st.title("💵 Repayments")
st.caption("Record, correct, or remove payments. The app prevents repayments exceeding the loan's total due.")


def payment_fields(loans, record=None, key_prefix="new"):
    record = record or {}
    loan_ids = loans.loan_id.tolist()
    current_id = record.get("loan_id", loan_ids[0])
    loan_id = st.selectbox("Loan", loan_ids, index=loan_ids.index(current_id) if current_id in loan_ids else 0,
                           format_func=lambda value: f"{value} — {loans.loc[loans.loan_id == value, 'borrower'].iloc[0]} (balance {format_mwk(float(loans.loc[loans.loan_id == value, 'balance'].iloc[0]))})",
                           key=f"{key_prefix}_loan")
    left, right = st.columns(2)
    payment_date = left.date_input("Payment date", value=pd.to_datetime(record.get("payment_date", date.today())).date(), key=f"{key_prefix}_date")
    amount = right.number_input("Amount paid (MWK)", min_value=0.0, value=float(record.get("amount_paid", 0.0)), step=1000.0, format="%.2f", key=f"{key_prefix}_amount")
    left, right = st.columns(2)
    method = left.selectbox("Payment method", ["Cash", "Bank Transfer", "Mobile Money", "Other"], index=["Cash", "Bank Transfer", "Mobile Money", "Other"].index(record.get("payment_method", "Cash")) if record.get("payment_method") in ["Cash", "Bank Transfer", "Mobile Money", "Other"] else 3, key=f"{key_prefix}_method")
    reference = right.text_input("Reference", value=record.get("reference") or "", key=f"{key_prefix}_reference")
    left, right = st.columns(2)
    recorded_by = left.text_input("Recorded by", value=record.get("recorded_by") or "", key=f"{key_prefix}_recorded_by")
    notes = right.text_input("Notes", value=record.get("notes") or "", key=f"{key_prefix}_notes")
    return loan_id, payment_date, amount, method, reference, notes, recorded_by


loans_df = get_loans_df(conn)
add_tab, manage_tab = st.tabs(["Record repayment", "Manage repayments"])
with add_tab:
    open_loans = loans_df[loans_df.balance > 0] if not loans_df.empty else loans_df
    if open_loans.empty:
        st.info("There are no outstanding loans to record a payment against.")
    else:
        with st.form("add_payment", clear_on_submit=True):
            values = payment_fields(open_loans, key_prefix="add")
            if st.form_submit_button("Record repayment", type="primary"):
                balance = float(open_loans.loc[open_loans.loan_id == values[0], "balance"].iloc[0])
                if values[2] <= 0:
                    st.error("Amount must be greater than zero.")
                elif values[2] > balance:
                    st.error(f"Amount cannot exceed the remaining balance of {format_mwk(balance)}.")
                else:
                    payment_id = next_id(conn, "repayments", "payment_id", "PMT-")
                    conn.execute("""INSERT INTO repayments (payment_id, loan_id, payment_date, amount_paid, payment_method, reference, notes, recorded_by)
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", (payment_id, values[0], values[1].isoformat(), *values[2:]))
                    conn.commit()
                    st.success(f"Recorded {format_mwk(values[2])} against {values[0]}.")
                    st.rerun()

payments_df = get_repayments_df(conn)
with manage_tab:
    if payments_df.empty:
        st.info("No repayments yet.")
    else:
        selected_id = st.selectbox("Choose a repayment", payments_df.payment_id, format_func=lambda value: f"{value} — {payments_df.loc[payments_df.payment_id == value, 'borrower'].iloc[0]} ({format_mwk(float(payments_df.loc[payments_df.payment_id == value, 'amount_paid'].iloc[0]))})")
        record = payments_df.loc[payments_df.payment_id == selected_id].iloc[0].to_dict()
        with st.form("edit_payment"):
            values = payment_fields(loans_df, record, key_prefix=f"edit_{selected_id}")
            if st.form_submit_button("Save changes", type="primary"):
                selected_balance = float(loans_df.loc[loans_df.loan_id == values[0], "balance"].iloc[0])
                original_credit = float(record["amount_paid"]) if values[0] == record["loan_id"] else 0.0
                allowed = selected_balance + original_credit
                if values[2] <= 0:
                    st.error("Amount must be greater than zero.")
                elif values[2] > allowed:
                    st.error(f"Amount cannot exceed {format_mwk(allowed)} after existing repayments.")
                else:
                    conn.execute("""UPDATE repayments SET loan_id=?, payment_date=?, amount_paid=?, payment_method=?, reference=?, notes=?, recorded_by=? WHERE payment_id=?""",
                                 (values[0], values[1].isoformat(), *values[2:], selected_id))
                    conn.commit()
                    st.success("Repayment updated.")
                    st.rerun()
        st.divider()
        confirm = st.checkbox("I understand this permanently removes the repayment", key=f"delete_confirm_{selected_id}")
        if st.button("Delete repayment", disabled=not confirm):
            conn.execute("DELETE FROM repayments WHERE payment_id=?", (selected_id,))
            conn.commit()
            st.success("Repayment deleted.")
            st.rerun()

st.subheader("Payment history")
if payments_df.empty:
    st.info("No repayments recorded yet.")
else:
    st.dataframe(payments_df, width="stretch", hide_index=True)

conn.close()
