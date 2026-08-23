"""Business calculations shared by the Loan Manager pages."""

import calendar
from datetime import date
import sqlite3

import pandas as pd


PERIOD_OPTIONS = ["1 Week", "2 Weeks", "1 Month", "2 Months", "3 Months", "6 Months", "Custom"]


def compute_loan_terms(principal: float, rate: float) -> tuple[float, float]:
    """Calculate fixed interest and total due at the point a loan is issued."""
    interest = round(principal * rate, 2)
    return interest, round(principal + interest, 2)


def calculate_due_date(date_taken: date, period: str) -> date:
    """Apply the workbook's term convention: weeks are days; months are calendar months."""
    number, unit = period.split(maxsplit=1)
    quantity = int(number)
    if unit.lower().startswith("week"):
        from datetime import timedelta
        return date_taken + timedelta(days=quantity * 7)
    month_index = date_taken.month - 1 + quantity
    year = date_taken.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, min(date_taken.day, calendar.monthrange(year, month)[1]))


def get_loans_df(conn: sqlite3.Connection) -> pd.DataFrame:
    """Return loans with live balances and the workbook's Active/Paid/Overdue status."""
    df = pd.read_sql_query("""
        SELECT l.loan_id, l.customer_id, c.full_name AS borrower, l.date_taken, l.period,
               l.due_date, l.principal, l.rate, l.interest, l.total_due, l.bank, l.account,
               l.reference, l.notes, COALESCE(r.amount_paid, 0) AS amount_paid
        FROM loans l JOIN customers c ON c.customer_id = l.customer_id
        LEFT JOIN (SELECT loan_id, SUM(amount_paid) AS amount_paid FROM repayments GROUP BY loan_id) r
            ON r.loan_id = l.loan_id
        ORDER BY l.date_taken DESC, l.loan_id DESC
    """, conn)
    if df.empty:
        return df.assign(balance=pd.Series(dtype=float), status=pd.Series(dtype=str))
    df["balance"] = (df["total_due"] - df["amount_paid"]).round(2)
    df["status"] = "Active"
    df.loc[df["due_date"] < date.today().isoformat(), "status"] = "Overdue"
    df.loc[df["balance"] <= 0, "status"] = "Paid"
    return df


def get_capital_df(conn: sqlite3.Connection) -> pd.DataFrame:
    """Return the capital register, including its running balance."""
    df = pd.read_sql_query("SELECT transaction_id, date, type, description, money_in, money_out FROM capital ORDER BY date, transaction_id", conn)
    if df.empty:
        return df.assign(running_balance=pd.Series(dtype=float))
    df["running_balance"] = (df["money_in"] - df["money_out"]).cumsum().round(2)
    return df


def get_repayments_df(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query("""
        SELECT r.payment_id, r.loan_id, c.full_name AS borrower, r.payment_date, r.amount_paid,
               r.payment_method, r.reference, r.notes, r.recorded_by
        FROM repayments r JOIN loans l ON l.loan_id = r.loan_id
        JOIN customers c ON c.customer_id = l.customer_id
        ORDER BY r.payment_date DESC, r.payment_id DESC
    """, conn)


def get_dashboard_metrics(conn: sqlite3.Connection) -> dict:
    """Mirror the workbook's Profit Summary entirely from live records."""
    loans_df, capital_df = get_loans_df(conn), get_capital_df(conn)
    total_capital = float((capital_df["money_in"] - capital_df["money_out"]).sum()) if not capital_df.empty else 0.0
    total_loaned = float(loans_df["principal"].sum()) if not loans_df.empty else 0.0
    total_interest_expected = float(loans_df["interest"].sum()) if not loans_df.empty else 0.0
    total_collected = float(loans_df["amount_paid"].sum()) if not loans_df.empty else 0.0
    outstanding_balance = float(loans_df["balance"].sum()) if not loans_df.empty else 0.0
    return {"total_capital": total_capital, "total_loaned": total_loaned,
            "total_interest_expected": total_interest_expected,
            "profit_earned": float(loans_df.loc[loans_df["status"] == "Paid", "interest"].sum()) if not loans_df.empty else 0.0,
            "total_amount_due": float(loans_df["total_due"].sum()) if not loans_df.empty else 0.0,
            "total_collected": total_collected, "outstanding_balance": outstanding_balance,
            "available_cash": total_capital - total_loaned + total_collected,
            "active_count": int((loans_df["status"] == "Active").sum()) if not loans_df.empty else 0,
            "paid_count": int((loans_df["status"] == "Paid").sum()) if not loans_df.empty else 0,
            "overdue_count": int((loans_df["status"] == "Overdue").sum()) if not loans_df.empty else 0}


def format_mwk(amount: float) -> str:
    """Format amounts for the compact, whole-Kwacha dashboard and controls."""
    return f"MWK {amount:,.0f}"
