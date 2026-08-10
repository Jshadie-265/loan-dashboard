"""
business_logic.py — the calculation layer.

This is the Python equivalent of the "Profit Summery" sheet in the original
workbook. Nothing here is stored redundantly in the database — balance and
status are always derived fresh from loans + repayments, so they can never
drift out of sync the way a hand-maintained Excel "Status" column could.
"""

from datetime import date, datetime
import pandas as pd
import sqlite3


def compute_loan_terms(principal: float, rate: float) -> tuple[float, float]:
    """Mirrors Loans!H (Interest) and Loans!I (Total Due): interest = principal * rate."""
    interest = round(principal * rate, 2)
    total_due = round(principal + interest, 2)
    return interest, total_due


def _today_str() -> str:
    return date.today().isoformat()


def get_loans_df(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    All loans joined with their borrower and computed amount_paid / balance / status.
    status logic mirrors the workbook's intent: Paid once balance hits zero,
    Overdue if the due date has passed with a balance remaining, else Active.
    """
    query = """
        SELECT
            l.loan_id, l.customer_id, c.full_name AS borrower,
            l.date_taken, l.period, l.due_date,
            l.principal, l.rate, l.interest, l.total_due,
            l.bank, l.account, l.reference, l.notes,
            COALESCE(r.amount_paid, 0) AS amount_paid
        FROM loans l
        JOIN customers c ON l.customer_id = c.customer_id
        LEFT JOIN (
            SELECT loan_id, SUM(amount_paid) AS amount_paid
            FROM repayments GROUP BY loan_id
        ) r ON l.loan_id = r.loan_id
        ORDER BY l.date_taken DESC, l.loan_id DESC
    """
    df = pd.read_sql_query(query, conn)
    if df.empty:
        df["balance"] = []
        df["status"] = []
        return df

    df["balance"] = (df["total_due"] - df["amount_paid"]).round(2)
    today = _today_str()

    def status_for(row):
        if row["balance"] <= 0:
            return "Paid"
        if row["due_date"] < today:
            return "Overdue"
        return "Active"

    df["status"] = df.apply(status_for, axis=1)
    return df


def get_capital_df(conn: sqlite3.Connection) -> pd.DataFrame:
    """Capital ledger with a running balance, mirroring Capital!G (Running Balance)."""
    query = """
        SELECT transaction_id, date, type, description, money_in, money_out
        FROM capital
        ORDER BY date ASC, transaction_id ASC
    """
    df = pd.read_sql_query(query, conn)
    if df.empty:
        df["running_balance"] = []
        return df
    df["running_balance"] = (df["money_in"] - df["money_out"]).cumsum().round(2)
    return df


def get_repayments_df(conn: sqlite3.Connection) -> pd.DataFrame:
    query = """
        SELECT r.payment_id, r.loan_id, c.full_name AS borrower, r.payment_date,
               r.amount_paid, r.payment_method, r.reference, r.notes, r.recorded_by
        FROM repayments r
        JOIN loans l ON r.loan_id = l.loan_id
        JOIN customers c ON l.customer_id = c.customer_id
        ORDER BY r.payment_date DESC, r.payment_id DESC
    """
    return pd.read_sql_query(query, conn)


def get_dashboard_metrics(conn: sqlite3.Connection) -> dict:
    """
    The Python equivalent of every cell in the 'Profit Summery' sheet.
    Comments show which original cell/formula each value replaces.
    """
    loans_df = get_loans_df(conn)
    capital_df = get_capital_df(conn)

    total_capital = float(capital_df["money_in"].sum() - capital_df["money_out"].sum()) if not capital_df.empty else 0.0  # B4
    total_loaned = float(loans_df["principal"].sum()) if not loans_df.empty else 0.0                                      # B5
    total_interest_expected = float(loans_df["interest"].sum()) if not loans_df.empty else 0.0                            # B6
    profit_earned = float(loans_df.loc[loans_df["status"] == "Paid", "interest"].sum()) if not loans_df.empty else 0.0    # B7
    total_amount_due = float(loans_df["total_due"].sum()) if not loans_df.empty else 0.0                                  # B8
    total_collected = float(loans_df["amount_paid"].sum()) if not loans_df.empty else 0.0                                 # B9
    outstanding_balance = float(loans_df["balance"].sum()) if not loans_df.empty else 0.0                                 # B10
    available_cash = total_capital - total_loaned + total_collected                                                       # B11

    active_count = int((loans_df["status"] == "Active").sum()) if not loans_df.empty else 0    # B12
    paid_count = int((loans_df["status"] == "Paid").sum()) if not loans_df.empty else 0         # B13
    overdue_count = int((loans_df["status"] == "Overdue").sum()) if not loans_df.empty else 0   # B14

    return {
        "total_capital": total_capital,
        "total_loaned": total_loaned,
        "total_interest_expected": total_interest_expected,
        "profit_earned": profit_earned,
        "total_amount_due": total_amount_due,
        "total_collected": total_collected,
        "outstanding_balance": outstanding_balance,
        "available_cash": available_cash,
        "active_count": active_count,
        "paid_count": paid_count,
        "overdue_count": overdue_count,
    }


def format_mwk(amount: float) -> str:
    return f"MWK {amount:,.0f}"
