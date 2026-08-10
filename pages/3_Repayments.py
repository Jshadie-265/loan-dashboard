from datetime import date

import streamlit as st

from business_logic import format_mwk, get_loans_df, get_repayments_df
from db import get_connection, init_db, next_id

st.set_page_config(page_title="Repayments", page_icon="💵", layout="wide")
init_db()
conn = get_connection()

st.title("💵 Repayments")

loans_df = get_loans_df(conn)
unpaid = loans_df[loans_df["status"] != "Paid"] if not loans_df.empty else loans_df

with st.expander("➕ Record a repayment", expanded=not unpaid.empty):
    if unpaid.empty:
        st.info("No outstanding loans to record a payment against.")
    else:
        unpaid = unpaid.copy()
        unpaid["label"] = unpaid.apply(
            lambda r: f"{r['loan_id']} — {r['borrower']} (balance {format_mwk(r['balance'])})", axis=1
        )
        choice = st.selectbox("Loan", unpaid["label"])
        selected = unpaid[unpaid["label"] == choice].iloc[0]

        c1, c2 = st.columns(2)
        payment_date = c1.date_input("Payment date", value=date.today())
        amount = c2.number_input(
            "Amount paid (MWK)", min_value=0.0, max_value=float(selected["balance"]),
            step=1000.0, format="%.2f",
        )
        c3, c4 = st.columns(2)
        method = c3.selectbox("Payment method", ["Cash", "Bank Transfer", "Mobile Money", "Other"])
        reference = c4.text_input("Reference")
        c5, c6 = st.columns(2)
        recorded_by = c5.text_input("Recorded by")
        notes = c6.text_input("Notes")

        if st.button("Record repayment", type="primary"):
            if amount <= 0:
                st.error("Amount must be greater than zero.")
            else:
                payment_id = next_id(conn, "repayments", "payment_id", "PMT-")
                conn.execute(
                    """INSERT INTO repayments (payment_id, loan_id, payment_date, amount_paid,
                                                payment_method, reference, notes, recorded_by)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (payment_id, selected["loan_id"], payment_date.isoformat(), amount,
                     method, reference, notes, recorded_by),
                )
                conn.commit()
                st.success(f"Recorded {format_mwk(amount)} against {selected['loan_id']}")
                st.rerun()

st.subheader("Payment history")
df = get_repayments_df(conn)
if df.empty:
    st.info("No repayments recorded yet.")
else:
    st.dataframe(
        df.rename(columns={
            "payment_id": "Payment ID", "loan_id": "Loan ID", "borrower": "Borrower",
            "payment_date": "Date", "amount_paid": "Amount", "payment_method": "Method",
            "reference": "Reference", "notes": "Notes", "recorded_by": "Recorded by",
        }),
        use_container_width=True, hide_index=True,
    )

conn.close()
