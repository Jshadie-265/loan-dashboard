"""
import_excel.py — one-time migration from Loan.xlsx into loan_app.db.

Run this once to bring your existing Capital, Loans, and Repayments data
into the new database:

    python import_excel.py path/to/Loan.xlsx

The Customers sheet in the original workbook was empty, so customer records
are created here from the unique borrower names found in the Loans sheet
(one CUST-### per distinct name). If you re-run this against a workbook
that already has real Customers rows, it will match by full name instead
of creating duplicates.

Safe to re-run: it skips any transaction/loan/payment ID already present
in the database rather than inserting it twice.
"""

import sys
from datetime import datetime
from pathlib import Path

import openpyxl

from db import get_connection, init_db, next_id


def _iter_rows(ws, header_row: int, id_col: int):
    """Yield data rows starting after header_row, stopping at the first row whose id_col is empty."""
    row = header_row + 1
    while True:
        val = ws.cell(row=row, column=id_col).value
        if val is None:
            break
        yield row
        row += 1


def _to_date_str(value) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    return str(value)


def import_capital(conn, ws):
    inserted = 0
    for row in _iter_rows(ws, header_row=3, id_col=1):
        transaction_id = ws.cell(row=row, column=1).value
        existing = conn.execute(
            "SELECT 1 FROM capital WHERE transaction_id = ?", (transaction_id,)
        ).fetchone()
        if existing:
            continue
        conn.execute(
            """INSERT INTO capital (transaction_id, date, type, description, money_in, money_out)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                transaction_id,
                _to_date_str(ws.cell(row=row, column=2).value),
                ws.cell(row=row, column=3).value,
                ws.cell(row=row, column=4).value,
                ws.cell(row=row, column=5).value or 0,
                ws.cell(row=row, column=6).value or 0,
            ),
        )
        inserted += 1
    conn.commit()
    return inserted


def get_or_create_customer(conn, full_name: str) -> str:
    row = conn.execute(
        "SELECT customer_id FROM customers WHERE full_name = ?", (full_name,)
    ).fetchone()
    if row:
        return row["customer_id"]
    customer_id = next_id(conn, "customers", "customer_id", "CUST-")
    conn.execute(
        "INSERT INTO customers (customer_id, full_name, status) VALUES (?, ?, 'Active')",
        (customer_id, full_name),
    )
    return customer_id


def import_loans(conn, ws):
    inserted = 0
    for row in _iter_rows(ws, header_row=3, id_col=1):
        loan_id = ws.cell(row=row, column=1).value
        existing = conn.execute("SELECT 1 FROM loans WHERE loan_id = ?", (loan_id,)).fetchone()
        if existing:
            continue

        borrower = ws.cell(row=row, column=2).value
        customer_id = get_or_create_customer(conn, borrower)

        principal = ws.cell(row=row, column=6).value or 0
        rate = ws.cell(row=row, column=7).value or 0
        interest = ws.cell(row=row, column=8).value or (principal * rate)
        total_due = ws.cell(row=row, column=9).value or (principal + interest)

        conn.execute(
            """INSERT INTO loans (loan_id, customer_id, date_taken, period, due_date,
                                   principal, rate, interest, total_due, bank, account,
                                   reference, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                loan_id,
                customer_id,
                _to_date_str(ws.cell(row=row, column=3).value),
                ws.cell(row=row, column=4).value,
                _to_date_str(ws.cell(row=row, column=5).value),
                principal,
                rate,
                interest,
                total_due,
                ws.cell(row=row, column=13).value,
                str(ws.cell(row=row, column=14).value) if ws.cell(row=row, column=14).value else None,
                ws.cell(row=row, column=15).value,
                ws.cell(row=row, column=16).value,
            ),
        )
        inserted += 1
    conn.commit()
    return inserted


def import_repayments(conn, ws):
    inserted = 0
    for row in _iter_rows(ws, header_row=3, id_col=1):
        payment_id = ws.cell(row=row, column=1).value
        existing = conn.execute(
            "SELECT 1 FROM repayments WHERE payment_id = ?", (payment_id,)
        ).fetchone()
        if existing:
            continue
        loan_id = ws.cell(row=row, column=2).value
        loan_exists = conn.execute("SELECT 1 FROM loans WHERE loan_id = ?", (loan_id,)).fetchone()
        if not loan_exists:
            print(f"  Skipping payment {payment_id}: loan {loan_id} not found")
            continue
        conn.execute(
            """INSERT INTO repayments (payment_id, loan_id, payment_date, amount_paid,
                                        payment_method, reference, notes, recorded_by)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                payment_id,
                loan_id,
                _to_date_str(ws.cell(row=row, column=4).value),
                ws.cell(row=row, column=5).value or 0,
                ws.cell(row=row, column=6).value,
                ws.cell(row=row, column=7).value,
                ws.cell(row=row, column=8).value,
                ws.cell(row=row, column=9).value,
            ),
        )
        inserted += 1
    conn.commit()
    return inserted


def main(xlsx_path: str):
    path = Path(xlsx_path)
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    init_db()
    conn = get_connection()
    wb = openpyxl.load_workbook(path, data_only=True)

    n_capital = import_capital(conn, wb["Capital"])
    print(f"Capital transactions imported: {n_capital}")

    n_loans = import_loans(conn, wb["Loans"])
    print(f"Loans imported: {n_loans}")

    n_repay = import_repayments(conn, wb["Repayments"])
    print(f"Repayments imported: {n_repay}")

    n_customers = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    print(f"Customers on file: {n_customers}")

    conn.close()
    print("\nDone. Run `streamlit run app.py` to view the dashboard.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python import_excel.py path/to/Loan.xlsx")
        sys.exit(1)
    main(sys.argv[1])
