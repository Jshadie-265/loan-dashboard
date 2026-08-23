"""Portable, read-only exports for a Loan Manager database."""

import csv
import io
import sqlite3
import zipfile
from datetime import datetime, timezone


EXPORT_TABLES = ("customers", "loans", "repayments", "capital")


def create_csv_backup(conn: sqlite3.Connection) -> bytes:
    """Return a ZIP containing one UTF-8 CSV file per editable register."""
    buffer = io.BytesIO()
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "README.txt",
            "Loan Manager data export\n\n"
            f"Created: {created_at}\n"
            "Contains the source records for Customers, Loans, Repayments, and Capital.\n"
            "Keep this archive somewhere safe as a portable backup.\n",
        )
        for table in EXPORT_TABLES:
            rows = conn.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()
            output = io.StringIO(newline="")
            writer = csv.writer(output)
            writer.writerow([column[0] for column in conn.execute(f"SELECT * FROM {table} LIMIT 0").description])
            writer.writerows([tuple(row) for row in rows])
            archive.writestr(f"{table}.csv", output.getvalue().encode("utf-8-sig"))
    return buffer.getvalue()
