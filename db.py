"""
db.py — SQLite connection and schema for the loan management app.

This replaces Loan.xlsx as the system of record. Four tables map onto the
four data sheets from the original workbook (Customers, Loans, Repayments,
Capital). "Profit Summery" and "Dashboard" are not tables — they were pure
calculation sheets in Excel, and here that logic lives in business_logic.py
instead, computed on the fly from the four tables below.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "loan_app.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    full_name   TEXT NOT NULL,
    phone       TEXT,
    national_id TEXT,
    address     TEXT,
    occupation  TEXT,
    collateral  TEXT,
    status      TEXT DEFAULT 'Active',
    notes       TEXT,
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS loans (
    loan_id     TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    date_taken  TEXT NOT NULL,
    period      TEXT,
    due_date    TEXT NOT NULL,
    principal   REAL NOT NULL,
    rate        REAL NOT NULL,      -- decimal, e.g. 0.3 = 30%
    interest    REAL NOT NULL,      -- principal * rate, fixed at issue time
    total_due   REAL NOT NULL,      -- principal + interest, fixed at issue time
    bank        TEXT,
    account     TEXT,
    reference   TEXT,
    notes       TEXT,
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS repayments (
    payment_id     TEXT PRIMARY KEY,
    loan_id        TEXT NOT NULL REFERENCES loans(loan_id),
    payment_date   TEXT NOT NULL,
    amount_paid    REAL NOT NULL,
    payment_method TEXT,
    reference      TEXT,
    notes          TEXT,
    recorded_by    TEXT,
    created_at     TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS capital (
    transaction_id TEXT PRIMARY KEY,
    date           TEXT NOT NULL,
    type           TEXT NOT NULL,   -- 'Capital' (in) or 'Withdrawal' (out), free text
    description    TEXT,
    money_in       REAL DEFAULT 0,
    money_out      REAL DEFAULT 0,
    created_at     TEXT DEFAULT (datetime('now'))
);
"""


def get_connection() -> sqlite3.Connection:
    """Open a connection with foreign keys enforced and row access by column name."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they don't exist yet. Safe to call every app startup."""
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def next_id(conn: sqlite3.Connection, table: str, id_col: str, prefix: str, width: int = 3) -> str:
    """
    Generate the next sequential ID for a table, e.g. next_id(conn, 'loans', 'loan_id', 'L')
    looks at existing IDs like 'L001'..'L009' and returns 'L010'.
    Falls back to 1 if the table is empty or IDs don't match the prefix pattern.
    """
    cur = conn.execute(f"SELECT {id_col} FROM {table} WHERE {id_col} LIKE ?", (f"{prefix}%",))
    max_n = 0
    for (val,) in cur.fetchall():
        suffix = val[len(prefix):]
        if suffix.isdigit():
            max_n = max(max_n, int(suffix))
    return f"{prefix}{max_n + 1:0{width}d}"


if __name__ == "__main__":
    init_db()
    print(f"Database ready at {DB_PATH}")
