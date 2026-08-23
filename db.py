"""SQLite storage and safe record operations for the Loan Manager."""

import os
import sqlite3
from pathlib import Path
from typing import Optional


DB_PATH = Path(os.environ.get("LOAN_APP_DB", Path(__file__).parent / "loan_app.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    full_name   TEXT NOT NULL CHECK (length(trim(full_name)) > 0),
    phone       TEXT,
    national_id TEXT,
    address     TEXT,
    occupation  TEXT,
    collateral  TEXT,
    status      TEXT NOT NULL DEFAULT 'Active' CHECK (status IN ('Active', 'Inactive')),
    notes       TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS loans (
    loan_id     TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    date_taken  TEXT NOT NULL,
    period      TEXT,
    due_date    TEXT NOT NULL,
    principal   REAL NOT NULL CHECK (principal > 0),
    rate        REAL NOT NULL CHECK (rate >= 0),
    interest    REAL NOT NULL CHECK (interest >= 0),
    total_due   REAL NOT NULL CHECK (total_due >= principal),
    bank        TEXT,
    account     TEXT,
    reference   TEXT,
    notes       TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS repayments (
    payment_id     TEXT PRIMARY KEY,
    loan_id        TEXT NOT NULL REFERENCES loans(loan_id),
    payment_date   TEXT NOT NULL,
    amount_paid    REAL NOT NULL CHECK (amount_paid > 0),
    payment_method TEXT,
    reference      TEXT,
    notes          TEXT,
    recorded_by    TEXT,
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS capital (
    transaction_id TEXT PRIMARY KEY,
    date           TEXT NOT NULL,
    type           TEXT NOT NULL,
    description    TEXT,
    money_in       REAL NOT NULL DEFAULT 0 CHECK (money_in >= 0),
    money_out      REAL NOT NULL DEFAULT 0 CHECK (money_out >= 0),
    created_at     TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (money_in > 0 OR money_out > 0),
    CHECK (NOT (money_in > 0 AND money_out > 0))
);

CREATE INDEX IF NOT EXISTS idx_loans_customer ON loans(customer_id);
CREATE INDEX IF NOT EXISTS idx_repayments_loan ON repayments(loan_id);
CREATE INDEX IF NOT EXISTS idx_loans_due_date ON loans(due_date);
CREATE INDEX IF NOT EXISTS idx_capital_date ON capital(date);
"""


def get_connection(db_path: Optional[Path | str] = None) -> sqlite3.Connection:
    """Open a foreign-key-enforced database connection with named row access."""
    path = Path(db_path) if db_path else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[Path | str] = None) -> None:
    """Create the database and indexes if they do not already exist."""
    conn = get_connection(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def next_id(conn: sqlite3.Connection, table: str, id_col: str, prefix: str, width: int = 3) -> str:
    """Return the next readable sequential ID, such as ``L014``."""
    allowed = {("customers", "customer_id"), ("loans", "loan_id"), ("repayments", "payment_id"), ("capital", "transaction_id")}
    if (table, id_col) not in allowed:
        raise ValueError("Unsupported table or ID column")
    rows = conn.execute(f"SELECT {id_col} FROM {table} WHERE {id_col} LIKE ?", (f"{prefix}%",))
    max_number = 0
    for (value,) in rows.fetchall():
        suffix = value[len(prefix):]
        if suffix.isdigit():
            max_number = max(max_number, int(suffix))
    return f"{prefix}{max_number + 1:0{width}d}"


def delete_customer(conn: sqlite3.Connection, customer_id: str) -> tuple[bool, str]:
    """Delete a customer only when no loan history would be orphaned."""
    loan_count = conn.execute("SELECT COUNT(*) FROM loans WHERE customer_id = ?", (customer_id,)).fetchone()[0]
    if loan_count:
        return False, "This customer has loan history. Mark them inactive instead."
    conn.execute("DELETE FROM customers WHERE customer_id = ?", (customer_id,))
    conn.commit()
    return True, "Customer deleted."


def delete_loan(conn: sqlite3.Connection, loan_id: str) -> int:
    """Delete a loan and its linked payment records as one deliberate operation."""
    payment_count = conn.execute("SELECT COUNT(*) FROM repayments WHERE loan_id = ?", (loan_id,)).fetchone()[0]
    with conn:
        conn.execute("DELETE FROM repayments WHERE loan_id = ?", (loan_id,))
        conn.execute("DELETE FROM loans WHERE loan_id = ?", (loan_id,))
    return payment_count


if __name__ == "__main__":
    init_db()
    print(f"Database ready at {DB_PATH}")
