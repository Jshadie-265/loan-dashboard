# Loan Manager

A local Streamlit application for managing the customer, loan, repayment, and capital registers from `Loan.xlsx`. It stores data in SQLite and calculates the dashboard live, so balances, status, and profit summaries stay consistent.

## Run from a fresh GitHub clone

Requires Python 3.10 or newer.

```bash
git clone <your-repository-url>
cd loan_app
python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source .venv/bin/activate
```

Then install and start the application:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

For a simpler launch after cloning, use one of the included helpers. Each creates a virtual environment and installs the required packages automatically:

```powershell
# Windows (double-click run.bat, or run it in Command Prompt)
run.bat
```

```powershell
# Windows PowerShell alternative
.\run.ps1
```

```bash
# macOS / Linux
chmod +x run.sh
./run.sh
```

The app opens at `http://localhost:8501`. A blank `loan_app.db` is created automatically on first launch; it is intentionally excluded from Git so each user keeps their own data.

## Bring in the original workbook

After starting the app, choose **Import data** in the sidebar and upload one or more `Loan.xlsx` files. The importer consolidates them: repeat imports skip matching source records, while conflicting IDs in another workbook are assigned new local IDs so those records are retained.

For daily use, the Dashboard also has **Import and consolidate Excel data** and **Export current changes** controls. An export is only downloaded after explicitly preparing it and pressing its download button. It contains the current customers, loans, repayments, and capital registers in a ZIP of CSV files.

You can also import from the command line:

```bash
python import_excel.py path/to/Loan.xlsx
```

## What it does

- **Customers:** add, search, edit, set active/inactive, and safely delete customers with no loan history.
- **Loans:** issue loans with calendar-based weekly/monthly terms, fixed interest, live balance/status, filters, editing, and confirmed deletion.
- **Repayments:** add, edit, and delete payments; overpayments are blocked.
- **Capital:** add, edit, and delete money-in/money-out transactions with a running balance.
- **Backup & export:** download all editable registers as a portable ZIP of CSV files.
- **Dashboard:** mirrors the workbook’s performance summary with real-time KPIs, status counts, charts, and overdue aging.

## Data safeguards

Deleting a loan also deletes its linked repayments after an explicit confirmation. Customers with loan history cannot be removed; set them to **Inactive** instead. All other deletion controls require confirmation.

## Project layout

```text
app.py                 Dashboard
pages/                 Customer, loan, repayment, capital, and import screens
db.py                  SQLite schema and safe deletion helpers
business_logic.py      Shared calculations and live status logic
import_excel.py        Workbook import command and in-app importer
data_export.py         Portable CSV backup generator
run.bat / run.ps1 / run.sh  One-command launch helpers
```
