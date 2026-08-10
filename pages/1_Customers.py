import streamlit as st
import pandas as pd

from db import get_connection, init_db, next_id

st.set_page_config(page_title="Customers", page_icon="🧑‍🤝‍🧑", layout="wide")
init_db()
conn = get_connection()

st.title("🧑‍🤝‍🧑 Customers")

with st.expander("➕ Add a new customer", expanded=False):
    with st.form("add_customer", clear_on_submit=True):
        c1, c2 = st.columns(2)
        full_name = c1.text_input("Full name *")
        phone = c2.text_input("Phone number")
        national_id = c1.text_input("National ID")
        occupation = c2.text_input("Occupation")
        address = st.text_input("Address")
        collateral = st.text_input("Collateral")
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add customer")

        if submitted:
            if not full_name.strip():
                st.error("Full name is required.")
            else:
                customer_id = next_id(conn, "customers", "customer_id", "CUST-")
                conn.execute(
                    """INSERT INTO customers (customer_id, full_name, phone, national_id,
                                               address, occupation, collateral, notes)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (customer_id, full_name.strip(), phone, national_id, address,
                     occupation, collateral, notes),
                )
                conn.commit()
                st.success(f"Added {full_name} as {customer_id}")
                st.rerun()

st.subheader("All customers")
df = pd.read_sql_query(
    "SELECT customer_id, full_name, phone, national_id, occupation, address, collateral, status, notes "
    "FROM customers ORDER BY full_name",
    conn,
)
if df.empty:
    st.info("No customers yet — add one above.")
else:
    search = st.text_input("Search by name")
    if search:
        df = df[df["full_name"].str.contains(search, case=False, na=False)]
    st.dataframe(df, use_container_width=True, hide_index=True)

conn.close()
