from datetime import date

import pandas as pd
import streamlit as st

from business_logic import PERIOD_OPTIONS, calculate_due_date, compute_loan_terms, format_mwk, get_loans_df
from db import delete_loan, get_connection, init_db, next_id

st.set_page_config(page_title="Loans | Loan Manager", page_icon="📄", layout="wide")
init_db()
conn = get_connection()
st.title("📄 Loans")
st.caption("Issue loans using the workbook's terms, then edit or remove records with linked payments handled safely.")
customers = pd.read_sql_query("SELECT customer_id, full_name, status FROM customers ORDER BY full_name", conn)


def loan_fields(record=None, key_prefix="new"):
    record = record or {}
    active_customers = customers[customers.status == "Active"]
    eligible = active_customers.copy()
    if record.get("customer_id") and record["customer_id"] not in eligible.customer_id.tolist():
        eligible = pd.concat([eligible, customers[customers.customer_id == record["customer_id"]]])
    customer_ids = eligible["customer_id"].tolist()
    current_customer = record.get("customer_id", customer_ids[0])
    borrower_id = st.selectbox("Borrower", customer_ids, index=customer_ids.index(current_customer) if current_customer in customer_ids else 0,
                               format_func=lambda value: eligible.loc[eligible.customer_id == value, "full_name"].iloc[0], key=f"{key_prefix}_borrower")
    left, right = st.columns(2)
    date_taken = left.date_input("Date taken", value=pd.to_datetime(record.get("date_taken", date.today())).date(), key=f"{key_prefix}_date")
    current_period = record.get("period", "1 Month")
    period = right.selectbox("Loan period", PERIOD_OPTIONS, index=PERIOD_OPTIONS.index(current_period) if current_period in PERIOD_OPTIONS else PERIOD_OPTIONS.index("Custom"), key=f"{key_prefix}_period")
    calculated_due = calculate_due_date(date_taken, period) if period != "Custom" else pd.to_datetime(record.get("due_date", date_taken)).date()
    due_date = st.date_input("Due date", value=calculated_due, disabled=period != "Custom", key=f"{key_prefix}_due")
    left, right = st.columns(2)
    principal = left.number_input("Principal (MWK)", min_value=0.0, value=float(record.get("principal", 0.0)), step=10000.0, format="%.2f", key=f"{key_prefix}_principal")
    rate_pct = right.number_input("Interest rate (%)", min_value=0.0, value=float(record.get("rate", 0.0)) * 100, step=1.0, format="%.2f", key=f"{key_prefix}_rate")
    interest, total_due = compute_loan_terms(principal, rate_pct / 100)
    st.info(f"Fixed interest: **{format_mwk(interest)}** · Total due: **{format_mwk(total_due)}**")
    left, right = st.columns(2)
    bank = left.text_input("Bank", value=record.get("bank") or "", key=f"{key_prefix}_bank")
    account = right.text_input("Account number", value=record.get("account") or "", key=f"{key_prefix}_account")
    reference = st.text_input("Reference", value=record.get("reference") or "", key=f"{key_prefix}_reference")
    notes = st.text_area("Notes", value=record.get("notes") or "", key=f"{key_prefix}_notes")
    return borrower_id, date_taken, period, due_date, principal, rate_pct / 100, interest, total_due, bank, account, reference, notes


if customers.empty:
    st.warning("Add a customer before issuing a loan.")
else:
    add_tab, manage_tab = st.tabs(["Issue loan", "Manage loans"])
    with add_tab:
        if customers[customers.status == "Active"].empty:
            st.warning("Activate a customer before issuing a loan.")
        else:
            with st.form("add_loan"):
                values = loan_fields(key_prefix="add")
                if st.form_submit_button("Issue loan", type="primary"):
                    if values[4] <= 0:
                        st.error("Principal must be greater than zero.")
                    elif values[3] < values[1]:
                        st.error("Due date cannot be earlier than the issue date.")
                    else:
                        loan_id = next_id(conn, "loans", "loan_id", "L")
                        conn.execute("""INSERT INTO loans (loan_id, customer_id, date_taken, period, due_date, principal, rate, interest, total_due, bank, account, reference, notes)
                                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (loan_id, values[0], values[1].isoformat(), values[2], values[3].isoformat(), *values[4:]))
                        conn.commit()
                        st.success(f"Issued {loan_id} for {format_mwk(values[4])}.")
                        st.rerun()
    loans_df = get_loans_df(conn)
    with manage_tab:
        if loans_df.empty:
            st.info("No loans yet.")
        else:
            selected_id = st.selectbox("Choose a loan", loans_df.loan_id, format_func=lambda value: f"{value} — {loans_df.loc[loans_df.loan_id == value, 'borrower'].iloc[0]}")
            record = loans_df.loc[loans_df.loan_id == selected_id].iloc[0].to_dict()
            paid = float(record["amount_paid"])
            with st.form("edit_loan"):
                values = loan_fields(record, key_prefix=f"edit_{selected_id}")
                if st.form_submit_button("Save changes", type="primary"):
                    if values[4] <= 0 or values[3] < values[1]:
                        st.error("Enter a positive principal and a valid due date.")
                    elif values[7] < paid:
                        st.error(f"Total due cannot be lower than existing repayments ({format_mwk(paid)}).")
                    else:
                        conn.execute("""UPDATE loans SET customer_id=?, date_taken=?, period=?, due_date=?, principal=?, rate=?, interest=?, total_due=?, bank=?, account=?, reference=?, notes=? WHERE loan_id=?""",
                                     (values[0], values[1].isoformat(), values[2], values[3].isoformat(), *values[4:], selected_id))
                        conn.commit()
                        st.success("Loan updated.")
                        st.rerun()
            payment_count = conn.execute("SELECT COUNT(*) FROM repayments WHERE loan_id=?", (selected_id,)).fetchone()[0]
            st.divider()
            st.warning(f"Deleting this loan also deletes its {payment_count} linked repayment(s).")
            confirm = st.checkbox("I understand this permanently removes the loan history", key=f"delete_confirm_{selected_id}")
            if st.button("Delete loan", disabled=not confirm):
                delete_loan(conn, selected_id)
                st.success("Loan and linked repayments deleted.")
                st.rerun()

st.subheader("Loan register")
loans_df = get_loans_df(conn)
if loans_df.empty:
    st.info("No loans on file.")
else:
    left, right = st.columns([1, 2])
    statuses = left.multiselect("Status", ["Active", "Paid", "Overdue"], default=["Active", "Paid", "Overdue"])
    borrowers = right.multiselect("Borrower", sorted(loans_df.borrower.unique()))
    view = loans_df[loans_df.status.isin(statuses)]
    if borrowers:
        view = view[view.borrower.isin(borrowers)]
    st.dataframe(view, width="stretch", hide_index=True)

conn.close()
