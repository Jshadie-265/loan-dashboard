from datetime import date

import pandas as pd
import streamlit as st

from business_logic import format_mwk, get_capital_df
from db import get_connection, init_db, next_id

st.set_page_config(page_title="Capital | Loan Manager", page_icon="🏦", layout="wide")
init_db()
conn = get_connection()
st.title("🏦 Capital")
st.caption("Maintain the capital register from the workbook. Each transaction is a single money-in or money-out movement.")


def capital_fields(record=None, key_prefix="new"):
    record = record or {}
    left, right = st.columns(2)
    txn_date = left.date_input("Date", value=pd.to_datetime(record.get("date", date.today())).date(), key=f"{key_prefix}_date")
    txn_type = right.selectbox("Type", ["Capital", "Withdrawal", "Expense", "Other"], index=["Capital", "Withdrawal", "Expense", "Other"].index(record.get("type", "Capital")) if record.get("type") in ["Capital", "Withdrawal", "Expense", "Other"] else 3, key=f"{key_prefix}_type")
    direction = st.radio("Direction", ["Money in", "Money out"], horizontal=True, index=0 if float(record.get("money_in", 0) or 0) > 0 else 1, key=f"{key_prefix}_direction")
    default_amount = float(record.get("money_in", 0) or record.get("money_out", 0) or 0)
    amount = st.number_input("Amount (MWK)", min_value=0.0, value=default_amount, step=10000.0, format="%.2f", key=f"{key_prefix}_amount")
    description = st.text_area("Description", value=record.get("description") or "", key=f"{key_prefix}_description")
    return txn_date, txn_type, direction, amount, description


add_tab, manage_tab = st.tabs(["Add transaction", "Manage transactions"])
with add_tab:
    with st.form("add_capital", clear_on_submit=True):
        values = capital_fields(key_prefix="add")
        if st.form_submit_button("Add transaction", type="primary"):
            if values[3] <= 0:
                st.error("Amount must be greater than zero.")
            else:
                transaction_id = next_id(conn, "capital", "transaction_id", "T")
                money_in, money_out = (values[3], 0.0) if values[2] == "Money in" else (0.0, values[3])
                conn.execute("INSERT INTO capital (transaction_id, date, type, description, money_in, money_out) VALUES (?, ?, ?, ?, ?, ?)",
                             (transaction_id, values[0].isoformat(), values[1], values[4], money_in, money_out))
                conn.commit()
                st.success(f"Added {transaction_id}.")
                st.rerun()

df = get_capital_df(conn)
with manage_tab:
    if df.empty:
        st.info("No capital transactions yet.")
    else:
        selected_id = st.selectbox("Choose a transaction", df.transaction_id, format_func=lambda value: f"{value} — {df.loc[df.transaction_id == value, 'description'].iloc[0] or 'No description'}")
        record = df.loc[df.transaction_id == selected_id].iloc[0].to_dict()
        with st.form("edit_capital"):
            values = capital_fields(record, key_prefix=f"edit_{selected_id}")
            if st.form_submit_button("Save changes", type="primary"):
                if values[3] <= 0:
                    st.error("Amount must be greater than zero.")
                else:
                    money_in, money_out = (values[3], 0.0) if values[2] == "Money in" else (0.0, values[3])
                    conn.execute("UPDATE capital SET date=?, type=?, description=?, money_in=?, money_out=? WHERE transaction_id=?",
                                 (values[0].isoformat(), values[1], values[4], money_in, money_out, selected_id))
                    conn.commit()
                    st.success("Transaction updated.")
                    st.rerun()
        st.divider()
        confirm = st.checkbox("I understand this permanently removes the transaction", key=f"delete_confirm_{selected_id}")
        if st.button("Delete transaction", disabled=not confirm):
            conn.execute("DELETE FROM capital WHERE transaction_id=?", (selected_id,))
            conn.commit()
            st.success("Transaction deleted.")
            st.rerun()

st.subheader("Capital ledger")
if df.empty:
    st.info("No capital transactions on file.")
else:
    st.metric("Current capital position", format_mwk(float(df.running_balance.iloc[-1])))
    st.dataframe(df, width="stretch", hide_index=True)

conn.close()
