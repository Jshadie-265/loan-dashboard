import pandas as pd
import streamlit as st

from db import delete_customer, get_connection, init_db, next_id

st.set_page_config(page_title="Customers | Loan Manager", page_icon="👥", layout="wide")
init_db()
conn = get_connection()
st.title("👥 Customers")
st.caption("Register borrowers, update their details, or safely deactivate/remove unused records.")


def customer_fields(record=None, key_prefix="new"):
    record = record or {}
    left, right = st.columns(2)
    full_name = left.text_input("Full name *", value=record.get("full_name", ""), key=f"{key_prefix}_name")
    phone = right.text_input("Phone number", value=record.get("phone") or "", key=f"{key_prefix}_phone")
    national_id = left.text_input("National ID", value=record.get("national_id") or "", key=f"{key_prefix}_national_id")
    occupation = right.text_input("Occupation", value=record.get("occupation") or "", key=f"{key_prefix}_occupation")
    address = st.text_input("Address", value=record.get("address") or "", key=f"{key_prefix}_address")
    collateral = st.text_input("Collateral", value=record.get("collateral") or "", key=f"{key_prefix}_collateral")
    status = st.selectbox("Status", ["Active", "Inactive"], index=0 if record.get("status", "Active") == "Active" else 1, key=f"{key_prefix}_status")
    notes = st.text_area("Notes", value=record.get("notes") or "", key=f"{key_prefix}_notes")
    return full_name, phone, national_id, occupation, address, collateral, status, notes


add_tab, manage_tab = st.tabs(["Add customer", "Manage customers"])
with add_tab:
    with st.form("add_customer", clear_on_submit=True):
        values = customer_fields(key_prefix="add")
        if st.form_submit_button("Add customer", type="primary"):
            if not values[0].strip():
                st.error("Full name is required.")
            else:
                customer_id = next_id(conn, "customers", "customer_id", "CUST-")
                conn.execute("""INSERT INTO customers (customer_id, full_name, phone, national_id, occupation, address, collateral, status, notes)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", (customer_id, values[0].strip(), *values[1:]))
                conn.commit()
                st.success(f"Added {values[0].strip()} as {customer_id}.")
                st.rerun()

df = pd.read_sql_query("SELECT customer_id, full_name, phone, national_id, occupation, address, collateral, status, notes FROM customers ORDER BY full_name", conn)
with manage_tab:
    if df.empty:
        st.info("No customers yet — add one first.")
    else:
        selected_id = st.selectbox("Choose a customer", df["customer_id"], format_func=lambda value: f"{value} — {df.loc[df.customer_id == value, 'full_name'].iloc[0]}")
        record = df.loc[df.customer_id == selected_id].iloc[0].to_dict()
        with st.form("edit_customer"):
            values = customer_fields(record, key_prefix=f"edit_{selected_id}")
            if st.form_submit_button("Save changes", type="primary"):
                if not values[0].strip():
                    st.error("Full name is required.")
                else:
                    conn.execute("""UPDATE customers SET full_name=?, phone=?, national_id=?, occupation=?, address=?, collateral=?, status=?, notes=?
                                 WHERE customer_id=?""", (*values, selected_id))
                    conn.commit()
                    st.success("Customer updated.")
                    st.rerun()
        st.divider()
        st.caption("Delete is only available for a customer with no loan history, protecting your financial records.")
        confirm = st.checkbox("I understand this permanently removes the customer", key=f"delete_confirm_{selected_id}")
        if st.button("Delete customer", disabled=not confirm):
            deleted, message = delete_customer(conn, selected_id)
            (st.success if deleted else st.error)(message)
            if deleted:
                st.rerun()

st.subheader("Customer register")
if df.empty:
    st.info("No customer records to display.")
else:
    search = st.text_input("Search by name, phone, or national ID")
    view = df.copy()
    if search:
        view = view[view[["full_name", "phone", "national_id"]].fillna("").apply(lambda row: row.str.contains(search, case=False, regex=False).any(), axis=1)]
    st.dataframe(view, width="stretch", hide_index=True)

conn.close()
