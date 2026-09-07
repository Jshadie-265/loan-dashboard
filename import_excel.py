"""Import and consolidate one or more Loan.xlsx workbooks into SQLite.

Imports are safe to repeat. Identical records with the same source ID are
skipped or updated, while conflicting IDs from another workbook receive a new
local ID so that neither file's data is lost. Repayments are remapped to their
imported loan when a loan ID conflict occurs.
"""

import sys
from datetime import date, datetime
from pathlib import Path
from typing import BinaryIO, Iterable

import openpyxl
from openpyxl.utils.datetime import from_excel

from business_logic import calculate_due_date, compute_loan_terms
from db import get_connection, init_db, next_id


def to_date(value) -> str | None:
    """Parse dates robustly from datetime, date, Excel serial numbers, or formatted strings."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (int, float)) and 10000 < value < 100000:
        try:
            return from_excel(value).date().isoformat()
        except Exception:
            pass
    val_str = str(value).strip()
    if not val_str:
        return None
    # 1. ISO format (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
    try:
        return datetime.fromisoformat(val_str).date().isoformat()
    except (ValueError, TypeError):
        pass
    # 2. Common regional date formats (DD/MM/YYYY is standard in Malawi / UK)
    for fmt in ("%d/%m/%Y", "%d/%m/%Y %H:%M:%S", "%d-%m-%Y", "%d.%m.%Y", "%Y/%m/%d", "%m/%d/%Y", "%m-%d-%Y"):
        try:
            return datetime.strptime(val_str, fmt).date().isoformat()
        except (ValueError, TypeError):
            pass
    try:
        import pandas as pd
        ts = pd.to_datetime(val_str, dayfirst=True)
        if pd.notna(ts):
            return ts.date().isoformat()
    except Exception:
        pass
    return None


def text(value) -> str:
    return str(value or "").strip()


def same_text(left, right) -> bool:
    return text(left).casefold() == text(right).casefold()


def get_sheet(workbook, candidates: tuple[str, ...]):
    """Find a worksheet matching candidates case-insensitively and whitespace-trimmed."""
    if not workbook:
        return None
    clean_map = {s.strip().casefold(): s for s in workbook.sheetnames}
    for candidate in candidates:
        cand_key = candidate.strip().casefold()
        if cand_key in clean_map:
            return workbook[clean_map[cand_key]]
    return None


def source_id(value_sheet, formula_sheet, row: int, prefix: str, col: int = 1) -> str:
    """Return a saved ID or recreate the workbook's generated row-based ID."""
    if value_sheet is None:
        return ""
    value = text(value_sheet.cell(row, col).value)
    if value:
        return value
    formula = formula_sheet.cell(row, col).value if formula_sheet else None
    if isinstance(formula, str) and formula.startswith("="):
        return f"{prefix}{row - 3:03d}"
    return ""


CUSTOMER_ALIASES = {
    "id": ["customer id", "customer_id", "id", "code"],
    "full_name": ["full name", "full_name", "customer name", "borrower", "name"],
    "phone": ["phone number", "phone", "mobile", "telephone", "contact"],
    "national_id": ["national id", "national_id", "nid", "id number"],
    "address": ["address", "location"],
    "occupation": ["occupation", "job", "profession"],
    "collateral": ["collateral", "security"],
    "status": ["status", "stastus"],
    "notes": ["notes", "note", "remarks", "comment"],
}
DEFAULT_CUSTOMER_COLS = {
    "id": 1, "full_name": 2, "phone": 3, "national_id": 4, "address": 5,
    "occupation": 6, "collateral": 7, "status": 8, "notes": 9,
}

LOAN_ALIASES = {
    "id": ["loan id", "loan_id", "id"],
    "borrower": ["borrower", "customer", "client", "full name", "name"],
    "date_taken": ["date taken", "date_taken", "taken", "issued", "issue date", "date"],
    "period": ["loan period", "period", "term", "duration"],
    "due_date": ["due date", "due_date", "due"],
    "principal": ["principal", "amount", "loan amount"],
    "rate": ["rate", "interest rate", "rate (%)", "interest_rate"],
    "interest": ["interest (mwk)", "interest", "fixed interest"],
    "total_due": ["total due", "total_due", "total amount due", "total"],
    "bank": ["bank"],
    "account": ["account", "account number", "acct"],
    "reference": ["reference", "ref"],
    "notes": ["notes", "note", "remarks", "comment"],
}
DEFAULT_LOAN_COLS = {
    "id": 1, "borrower": 2, "date_taken": 3, "period": 4, "due_date": 5,
    "principal": 6, "rate": 7, "interest": 8, "total_due": 9,
    "bank": 13, "account": 14, "reference": 15, "notes": 16,
}

REPAYMENT_ALIASES = {
    "id": ["payment id", "payment_id", "id"],
    "loan_id": ["loan id", "loan_id", "loan"],
    "borrower": ["borrower", "customer", "name"],
    "payment_date": ["payment date", "payment_date", "date", "paid on"],
    "amount_paid": ["amount paid", "amount_paid", "amount", "paid"],
    "payment_method": ["payment method", "payment_method", "method"],
    "reference": ["reference", "ref"],
    "notes": ["notes", "note", "remarks", "comment"],
    "recorded_by": ["recorded by", "recorded_by", "agent", "user"],
}
DEFAULT_REPAYMENT_COLS = {
    "id": 1, "loan_id": 2, "borrower": 3, "payment_date": 4, "amount_paid": 5,
    "payment_method": 6, "reference": 7, "notes": 8, "recorded_by": 9,
}

CAPITAL_ALIASES = {
    "id": ["transaction id", "transaction_id", "id"],
    "date": ["date", "transaction date"],
    "type": ["type", "transaction type"],
    "description": ["description", "desc", "details"],
    "money_in": ["money in", "money_in", "in", "deposit"],
    "money_out": ["money out", "money_out", "out", "withdrawal"],
}
DEFAULT_CAPITAL_COLS = {
    "id": 1, "date": 2, "type": 3, "description": 4, "money_in": 5, "money_out": 6,
}


def detect_sheet_headers(ws, expected_aliases: dict[str, list[str]], default_cols: dict[str, int]) -> tuple[int, dict[str, int]]:
    """Scan top rows to detect header row and dynamically map column names."""
    max_scan = min(10, ws.max_row)
    best_row = None
    best_mapping = {}
    max_matches = 0

    max_col = getattr(ws, "max_column", None) or 25
    for r in range(1, max_scan + 1):
        has_numeric = False
        row_cells = {}
        for c in range(1, max_col + 1):
            val = ws.cell(r, c).value
            if val is not None and val != "":
                if isinstance(val, (int, float, datetime, date)):
                    has_numeric = True
                    break
                s = str(val).strip()
                if s.replace(".", "", 1).isdigit() and len(s) > 0:
                    has_numeric = True
                    break
                row_cells[c] = s.casefold()
        if has_numeric or not row_cells:
            continue

        current_mapping = {}
        for field, aliases in expected_aliases.items():
            for c, cell_val in row_cells.items():
                for alias in aliases:
                    if alias == cell_val or cell_val.startswith(alias) or cell_val.endswith(alias):
                        current_mapping[field] = c
                        break
                if field in current_mapping:
                    break

        if len(current_mapping) > max_matches:
            max_matches = len(current_mapping)
            best_row = r
            best_mapping = current_mapping

    final_mapping = dict(default_cols)
    if best_row is not None and max_matches >= 3:
        final_mapping.update(best_mapping)
        data_start_row = best_row + 1
    else:
        data_start_row = 4
        if ws.max_row < 4:
            data_start_row = 1
            for r in range(1, ws.max_row + 1):
                if any(ws.cell(r, c).value is not None for c in range(1, max_col + 1)):
                    data_start_row = r
                    break

    return data_start_row, final_mapping


def find_customer_id(conn, full_name: str, national_id: str | None = None) -> str | None:
    """Find a borrower by national ID when present, otherwise by their name."""
    if text(national_id):
        row = conn.execute("SELECT customer_id FROM customers WHERE lower(COALESCE(national_id, '')) = lower(?)", (text(national_id),)).fetchone()
        if row:
            return row["customer_id"]
    row = conn.execute("SELECT customer_id FROM customers WHERE lower(full_name) = lower(?)", (text(full_name),)).fetchone()
    if row:
        return row["customer_id"]
    return None


def get_or_create_customer(conn, full_name: str, national_id: str | None = None) -> str:
    customer_id = find_customer_id(conn, full_name, national_id)
    if customer_id:
        return customer_id
    customer_id = next_id(conn, "customers", "customer_id", "CUST-")
    conn.execute("INSERT INTO customers (customer_id, full_name, national_id) VALUES (?, ?, ?)", (customer_id, text(full_name), text(national_id) or None))
    return customer_id


def import_customers(conn, ws, formula_ws=None) -> int:
    inserted = 0
    start_row, cols = detect_sheet_headers(ws, CUSTOMER_ALIASES, DEFAULT_CUSTOMER_COLS)
    for row in range(start_row, ws.max_row + 1):
        full_name = text(ws.cell(row, cols["full_name"]).value)
        national_id = text(ws.cell(row, cols["national_id"]).value) or None
        if not full_name:
            continue
        phone = text(ws.cell(row, cols["phone"]).value) or None
        address = text(ws.cell(row, cols["address"]).value) or None
        occupation = text(ws.cell(row, cols["occupation"]).value) or None
        collateral = text(ws.cell(row, cols["collateral"]).value) or None
        status = text(ws.cell(row, cols["status"]).value or "Active").title()
        status = status if status in {"Active", "Inactive"} else "Active"
        notes = text(ws.cell(row, cols["notes"]).value) or None

        cust_id = find_customer_id(conn, full_name, national_id)
        if cust_id:
            # Consolidate: update empty fields with any newly supplied details
            conn.execute(
                """UPDATE customers SET
                    phone = COALESCE(phone, ?),
                    national_id = COALESCE(national_id, ?),
                    address = COALESCE(address, ?),
                    occupation = COALESCE(occupation, ?),
                    collateral = COALESCE(collateral, ?),
                    notes = COALESCE(notes, ?)
                WHERE customer_id=?""",
                (phone, national_id, address, occupation, collateral, notes, cust_id),
            )
            continue

        requested_id = source_id(ws, formula_ws, row, "C", col=cols["id"]) or next_id(conn, "customers", "customer_id", "CUST-")
        existing_by_id = conn.execute("SELECT customer_id FROM customers WHERE customer_id=?", (requested_id,)).fetchone()
        customer_id = requested_id if existing_by_id is None else next_id(conn, "customers", "customer_id", "CUST-")

        conn.execute(
            """INSERT INTO customers (customer_id, full_name, phone, national_id, address, occupation, collateral, status, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (customer_id, full_name, phone, national_id, address, occupation, collateral, status, notes),
        )
        inserted += 1
    return inserted


def capital_record_matches(row, txn_date, txn_type, description, money_in, money_out) -> bool:
    return (
        row is not None
        and row["date"] == txn_date
        and same_text(row["type"], txn_type)
        and same_text(row["description"], description)
        and abs(float(row["money_in"]) - money_in) < 0.01
        and abs(float(row["money_out"]) - money_out) < 0.01
    )


def find_matching_capital(conn, txn_date, txn_type, description, money_in, money_out):
    for row in conn.execute("SELECT * FROM capital"):
        if capital_record_matches(row, txn_date, txn_type, description, money_in, money_out):
            return row["transaction_id"]
    return None


def import_capital(conn, ws, formula_ws=None) -> int:
    inserted = 0
    start_row, cols = detect_sheet_headers(ws, CAPITAL_ALIASES, DEFAULT_CAPITAL_COLS)
    for row in range(start_row, ws.max_row + 1):
        txn_date = to_date(ws.cell(row, cols["date"]).value)
        raw_in = ws.cell(row, cols["money_in"]).value
        raw_out = ws.cell(row, cols["money_out"]).value
        try:
            money_in = float(raw_in or 0)
        except (ValueError, TypeError):
            money_in = 0.0
        try:
            money_out = float(raw_out or 0)
        except (ValueError, TypeError):
            money_out = 0.0
        if not txn_date or (money_in <= 0 and money_out <= 0):
            continue
        if money_in > 0 and money_out > 0:
            money_out = 0.0
        txn_type = text(ws.cell(row, cols["type"]).value or "Capital")
        description = text(ws.cell(row, cols["description"]).value) or None

        requested_id = source_id(ws, formula_ws, row, "T", col=cols["id"]) or next_id(conn, "capital", "transaction_id", "T")
        existing = conn.execute("SELECT * FROM capital WHERE transaction_id=?", (requested_id,)).fetchone()
        if existing:
            if (existing["date"] == txn_date and abs(float(existing["money_in"]) - money_in) < 0.01
                    and abs(float(existing["money_out"]) - money_out) < 0.01):
                continue
            if find_matching_capital(conn, txn_date, txn_type, description, money_in, money_out):
                continue
            transaction_id = next_id(conn, "capital", "transaction_id", "T")
        else:
            if find_matching_capital(conn, txn_date, txn_type, description, money_in, money_out):
                continue
            transaction_id = requested_id

        conn.execute(
            "INSERT INTO capital (transaction_id, date, type, description, money_in, money_out) VALUES (?, ?, ?, ?, ?, ?)",
            (transaction_id, txn_date, txn_type, description, money_in, money_out),
        )
        inserted += 1
    return inserted


def find_matching_loan(conn, customer_id, issued, principal, reference=None):
    """Find a loan by customer and issue date/principal, or by customer and reference."""
    row = conn.execute(
        "SELECT loan_id FROM loans WHERE customer_id=? AND date_taken=? AND abs(principal - ?) < 0.01",
        (customer_id, issued, principal),
    ).fetchone()
    if row:
        return row["loan_id"]
    if reference:
        row = conn.execute("SELECT loan_id FROM loans WHERE customer_id=? AND reference=?", (customer_id, reference)).fetchone()
        if row:
            return row["loan_id"]
    return None


def import_loans(conn, ws, formula_ws=None) -> tuple[int, dict[str, str]]:
    """Import loans and return source-to-local IDs for repayment reconciliation."""
    inserted, loan_ids = 0, {}
    start_row, cols = detect_sheet_headers(ws, LOAN_ALIASES, DEFAULT_LOAN_COLS)

    for row in range(start_row, ws.max_row + 1):
        borrower = text(ws.cell(row, cols["borrower"]).value)
        issued = to_date(ws.cell(row, cols["date_taken"]).value)
        try:
            principal = float(ws.cell(row, cols["principal"]).value or 0)
        except (ValueError, TypeError):
            principal = 0.0
        if not borrower or not issued or principal <= 0:
            continue

        source_loan_id = source_id(ws, formula_ws, row, "L", col=cols["id"])
        period = text(ws.cell(row, cols["period"]).value or "Custom")
        due_date = to_date(ws.cell(row, cols["due_date"]).value)
        if not due_date and period != "Custom":
            try:
                due_date = calculate_due_date(date.fromisoformat(issued), period).isoformat()
            except ValueError:
                due_date = issued
        due_date = due_date or issued

        try:
            rate = float(ws.cell(row, cols["rate"]).value or 0)
        except (ValueError, TypeError):
            rate = 0.0
        if rate > 1.0:
            rate = rate / 100.0

        calculated_interest, calculated_total = compute_loan_terms(principal, rate)
        try:
            interest = float(ws.cell(row, cols["interest"]).value or calculated_interest)
        except (ValueError, TypeError):
            interest = calculated_interest
        try:
            total_due = float(ws.cell(row, cols["total_due"]).value or calculated_total)
        except (ValueError, TypeError):
            total_due = calculated_total

        bank = ws.cell(row, cols["bank"]).value
        account = ws.cell(row, cols["account"]).value
        reference = ws.cell(row, cols["reference"]).value
        notes = ws.cell(row, cols["notes"]).value

        customer_id = get_or_create_customer(conn, borrower)
        requested_id = source_loan_id or next_id(conn, "loans", "loan_id", "L")
        existing = conn.execute("SELECT * FROM loans WHERE loan_id=?", (requested_id,)).fetchone() if requested_id else None

        if existing is not None:
            is_same_borrower = existing["customer_id"] == customer_id
            is_same_ref = bool(reference and same_text(reference, existing["reference"]))
            is_same_terms = existing["date_taken"] == issued and abs(float(existing["principal"]) - principal) < 0.01

            if is_same_borrower or is_same_ref or is_same_terms:
                conn.execute(
                    """UPDATE loans SET
                        customer_id=?, date_taken=?, period=?, due_date=?,
                        principal=?, rate=?, interest=?, total_due=?,
                        bank=COALESCE(?, bank), account=COALESCE(?, account),
                        reference=COALESCE(?, reference), notes=COALESCE(?, notes)
                    WHERE loan_id=?""",
                    (customer_id, issued, period, due_date, principal, rate, interest, total_due,
                     bank or None, str(account) if account is not None else None, reference or None, notes or None, requested_id),
                )
                loan_ids[source_loan_id or requested_id] = requested_id
                continue
            else:
                matching_id = find_matching_loan(conn, customer_id, issued, principal, reference)
                if matching_id:
                    loan_ids[source_loan_id or requested_id] = matching_id
                    continue
                loan_id = next_id(conn, "loans", "loan_id", "L")
        else:
            matching_id = find_matching_loan(conn, customer_id, issued, principal, reference)
            if matching_id:
                loan_ids[source_loan_id or requested_id] = matching_id
                continue
            loan_id = requested_id or next_id(conn, "loans", "loan_id", "L")

        conn.execute(
            """INSERT INTO loans (loan_id, customer_id, date_taken, period, due_date, principal, rate, interest, total_due, bank, account, reference, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (loan_id, customer_id, issued, period, due_date, principal, rate, interest, total_due, bank,
             str(account) if account is not None else None, reference, notes),
        )
        loan_ids[source_loan_id or requested_id] = loan_id
        inserted += 1

    return inserted, loan_ids


def import_repayments(conn, ws, loan_ids: dict[str, str], formula_ws=None) -> int:
    inserted = 0
    start_row, cols = detect_sheet_headers(ws, REPAYMENT_ALIASES, DEFAULT_REPAYMENT_COLS)

    for row in range(start_row, ws.max_row + 1):
        source_loan_id = text(ws.cell(row, cols["loan_id"]).value)
        paid_on = to_date(ws.cell(row, cols["payment_date"]).value)
        try:
            amount = float(ws.cell(row, cols["amount_paid"]).value or 0)
        except (ValueError, TypeError):
            amount = 0.0

        if not source_loan_id or not paid_on or amount <= 0:
            continue

        loan_id = loan_ids.get(source_loan_id, source_loan_id)
        if not conn.execute("SELECT 1 FROM loans WHERE loan_id=?", (loan_id,)).fetchone():
            continue

        source_payment_id = source_id(ws, formula_ws, row, "P", col=cols["id"])
        requested_id = source_payment_id or next_id(conn, "repayments", "payment_id", "PMT-")

        payment_method = text(ws.cell(row, cols["payment_method"]).value) or "Cash"
        reference = ws.cell(row, cols["reference"]).value
        notes = ws.cell(row, cols["notes"]).value
        recorded_by = ws.cell(row, cols["recorded_by"]).value

        existing = conn.execute("SELECT * FROM repayments WHERE payment_id=?", (requested_id,)).fetchone()
        if existing is not None:
            if existing["loan_id"] == loan_id:
                conn.execute(
                    """UPDATE repayments SET
                        payment_date=?, amount_paid=?, payment_method=?, reference=?, notes=?, recorded_by=?
                    WHERE payment_id=?""",
                    (paid_on, amount, payment_method, reference or existing["reference"],
                     notes or existing["notes"], recorded_by or existing["recorded_by"], requested_id),
                )
                continue
            else:
                payment_id = next_id(conn, "repayments", "payment_id", "PMT-")
        else:
            existing_match = conn.execute(
                """SELECT payment_id FROM repayments
                   WHERE loan_id=? AND payment_date=? AND abs(amount_paid - ?) < 0.01""",
                (loan_id, paid_on, amount),
            ).fetchone()
            if existing_match:
                continue
            payment_id = requested_id

        conn.execute(
            """INSERT INTO repayments (payment_id, loan_id, payment_date, amount_paid, payment_method, reference, notes, recorded_by)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (payment_id, loan_id, paid_on, amount, payment_method, reference, notes, recorded_by),
        )
        inserted += 1

    return inserted


def import_workbook(source: str | Path | BinaryIO, db_path: str | Path | None = None) -> dict[str, int]:
    """Import a compatible workbook and consolidate it with the current database."""
    init_db(db_path)
    if hasattr(source, "seek"):
        source.seek(0)
    workbook = openpyxl.load_workbook(source, data_only=True)
    formula_workbook = None
    try:
        if hasattr(source, "seek"):
            source.seek(0)
        formula_workbook = openpyxl.load_workbook(source, data_only=False)
    except Exception:
        pass

    cap_ws = get_sheet(workbook, ("Capital", "Capital Register", "Capital Ledger"))
    loans_ws = get_sheet(workbook, ("Loans", "Loan Register", "Loan Portfolio"))
    rep_ws = get_sheet(workbook, ("Repayments", "Repayments Register", "Payment History"))
    cust_ws = get_sheet(workbook, ("Customers", "Customer Register", "Borrowers"))

    missing = []
    if cap_ws is None:
        missing.append("Capital")
    if loans_ws is None:
        missing.append("Loans")
    if rep_ws is None:
        missing.append("Repayments")
    if missing:
        raise ValueError(f"Workbook is missing required sheet(s): {', '.join(sorted(missing))}")

    formula_cust = get_sheet(formula_workbook, ("Customers", "Customer Register", "Borrowers")) if formula_workbook else None
    formula_cap = get_sheet(formula_workbook, ("Capital", "Capital Register", "Capital Ledger")) if formula_workbook else None
    formula_loans = get_sheet(formula_workbook, ("Loans", "Loan Register", "Loan Portfolio")) if formula_workbook else None
    formula_rep = get_sheet(formula_workbook, ("Repayments", "Repayments Register", "Payment History")) if formula_workbook else None

    conn = get_connection(db_path)
    try:
        with conn:
            customers = import_customers(conn, cust_ws, formula_cust) if cust_ws is not None else 0
            capital = import_capital(conn, cap_ws, formula_cap)
            loans, loan_ids = import_loans(conn, loans_ws, formula_loans)
            repayments = import_repayments(conn, rep_ws, loan_ids, formula_rep)
        return {"customers": customers, "capital": capital, "loans": loans, "repayments": repayments}
    finally:
        conn.close()


def import_workbooks(sources: Iterable[str | Path | BinaryIO], db_path: str | Path | None = None) -> dict[str, int]:
    """Import several workbooks in sequence and return one consolidated summary."""
    totals = {"customers": 0, "capital": 0, "loans": 0, "repayments": 0}
    for source in sources:
        results = import_workbook(source, db_path=db_path)
        for name, count in results.items():
            totals[name] += count
    return totals


def main(xlsx_path: str) -> None:
    results = import_workbook(xlsx_path)
    print("Import complete: " + ", ".join(f"{count} {name}" for name, count in results.items()))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python import_excel.py path/to/Loan.xlsx")
        raise SystemExit(1)
    main(sys.argv[1])
