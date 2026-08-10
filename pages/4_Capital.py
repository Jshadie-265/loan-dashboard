from datetime import date

import streamlit as st

from business_logic import format_mwk, get_capital_df
from db import get_connection, init_db, next_id

st.set_page_config(page_title="Capital", page_icon="🏦", layout="wide")
init_db()
conn = get_connection()

st.title("🏦 Capital")
st.caption("Business capital contributions and withdrawals.")

with st.expander("➕ Add a transaction", expanded=False):
    with st.form("add_capital", clear_on_submit=True):
        c1, c2 = st.columns(2)
        txn_date = c1.date_input("Date", value=date.today())
        txn_type = c2.selectbox("Type", ["Capital", "Withdrawal", "Expense", "Other"])
        description = st.text_input("Description")

        c3, c4 = st.columns(2)
        money_in = c3.number_input("Money in (MWK)", min_value=0.0, step=10000.0, format="%.2f")
        money_out = c4.number_input("Money out (MWK)", min_value=0.0, step=10000.0, format="%.2f")

        submitted = st.form_submit_button("Add transaction")
        if submitted:
            if money_in == 0 and money_out == 0:
                st.error("Enter an amount in either Money in or Money out.")
            else:
                transaction_id = next_id(conn, "capital", "transaction_id", "T", width=3)
                conn.execute(
                    """INSERT INTO capital (transaction_id, date, type, description, money_in, money_out)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (transaction_id, txn_date.isoformat(), txn_type, description, money_in, money_out),
                )
                conn.commit()
                st.success(f"Added {transaction_id}")
                st.rerun()

st.subheader("Capital ledger")
df = get_capital_df(conn)
if df.empty:
    st.info("No capital transactions yet.")
else:
    st.metric("Current cash position", format_mwk(df["running_balance"].iloc[-1]))
    st.dataframe(
        df.rename(columns={
            "transaction_id": "Transaction ID", "date": "Date", "type": "Type",
            "description": "Description", "money_in": "Money in", "money_out": "Money out",
            "running_balance": "Running balance",
        }),
        use_container_width=True, hide_index=True,
    )

conn.close()
